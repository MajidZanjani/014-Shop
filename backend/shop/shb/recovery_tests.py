"""Owned PostgreSQL recovery/replay components; no actual restore qualification."""
from pathlib import Path
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone as utc_timezone
from hashlib import sha256
import json
from unittest.mock import patch
import uuid

from django.apps import apps
from django.db import connection, transaction
from django.test import TransactionTestCase, override_settings
from django.utils import timezone

from shop.access.models import AccessEpoch, LocalAccessRecoveryOperation
from shop.access.recovery import AccessRecoveryError, local_recovery_operation
from . import revision_tests
from .errors import ShbError


@override_settings(SHB_SYNTHETIC_FIXTURE=True)
class RecoveryTests(TransactionTestCase):
    client_class = revision_tests.RevisionTests.client_class
    setUp = revision_tests.RevisionTests.setUp
    post = revision_tests.RevisionTests.post
    challenge = revision_tests.RevisionTests.challenge
    authenticated = revision_tests.RevisionTests.authenticated
    customer_submit = revision_tests.RevisionTests.customer_submit
    submit = revision_tests.RevisionTests.submit
    issue = revision_tests.RevisionTests.issue
    offer = revision_tests.RevisionTests.offer
    customer_review = revision_tests.RevisionTests.customer_review
    accept_offer = revision_tests.RevisionTests.accept_offer
    pay = revision_tests.RevisionTests.pay
    withdraw = revision_tests.RevisionTests.withdraw
    revised = revision_tests.RevisionTests.revised

    def operation(self, action='quarantine', *, request_id=None, basis=None):
        return local_recovery_operation(action=action, request_id=request_id or uuid.uuid4(),
            expected_database=connection.settings_dict['NAME'], basis_reset=basis)

    def inspect(self):
        from .recovery import inspect_local_shb_recovery
        return inspect_local_shb_recovery()

    def state(self):
        from shop.access.models import LocalEffectAdmission
        models = [*apps.get_app_config('shb').get_models(), AccessEpoch, LocalAccessRecoveryOperation, LocalEffectAdmission]
        return {model._meta.label: sha256(json.dumps(list(model.objects.order_by(model._meta.pk.name).values()),
            sort_keys=True, default=str).encode()).hexdigest() for model in models}

    @contextmanager
    def corrupt_owned_fixture(self, table, *triggers):
        # This test owns this newly created disposable database and its tables.
        # Simulate an incomplete restore without weakening application guards.
        with transaction.atomic():
            with connection.cursor() as cursor:
                for trigger in triggers:
                    cursor.execute('ALTER TABLE public.' + table + ' DISABLE TRIGGER ' + trigger)
                # Transactional DDL rolls back to enabled triggers on an error.
                yield
                for trigger in triggers:
                    cursor.execute('ALTER TABLE public.' + table + ' ENABLE TRIGGER ' + trigger)

    def refuse_release(self):
        reset = uuid.uuid4()
        self.operation(request_id=reset)
        before = self.state()
        with self.assertRaisesMessage(AccessRecoveryError, 'shb_recovery_evidence_required'):
            self.operation('release', basis=reset)
        self.assertEqual(self.state(), before)

    def test_release_refuses_missing_ordinary_capture_archive_without_clearing_hold(self):
        from . import transaction_mail
        from .models import TransactionNoticeCapture
        self.assertTrue(transaction_mail.execute_once())
        capture = TransactionNoticeCapture.objects.get()
        (Path(self.directory.name) / ('blob-' + capture.sha256)).unlink()
        reset = uuid.uuid4()
        self.operation(request_id=reset)
        epoch = AccessEpoch.objects.get().value
        with self.assertRaisesMessage(AccessRecoveryError, 'shb_recovery_evidence_required'):
            self.operation('release', basis=reset)
        self.assertTrue(AccessEpoch.objects.get().quarantined)
        self.assertEqual(AccessEpoch.objects.get().value, epoch)
        self.assertEqual(LocalAccessRecoveryOperation.objects.count(), 1)

    def test_assessment_is_read_only_and_never_attests_post_backup_completeness(self):
        from shop.adapters.evidence_archive import PreparedArchive
        self.operation()
        before = self.state()
        files = {path.name:sha256(path.read_bytes()).hexdigest() for path in Path(self.directory.name).iterdir()}
        with patch.object(PreparedArchive, 'publish', side_effect=AssertionError('assessment must not publish')):
            result = self.inspect()
            self.assertEqual(self.inspect(), result)
        self.assertTrue(result['persisted_state_valid'])
        for flag in ('post_backup_completeness_established','actual_recovery_qualified','retry_authorized','reopening_authorized'):
            self.assertIs(result[flag], False)
        self.assertEqual(result['counts']['transaction_notices'], 1)
        self.assertEqual(result['counts']['transaction_captures'], 0)
        self.assertEqual(self.state(), before)
        self.assertEqual({path.name:sha256(path.read_bytes()).hexdigest() for path in Path(self.directory.name).iterdir()}, files)
        self.assertNotIn('buyer@synthetic.invalid', json.dumps(result))
        self.assertNotIn(self.code, json.dumps(result))

    def test_inspection_requires_quarantine_and_complete_effect_drain(self):
        from shop.access.effects import _begin, _finish
        with self.assertRaises(ShbError): self.inspect()
        effect = _begin('worker-run')
        reset = uuid.uuid4(); self.operation(request_id=reset)
        with self.assertRaises(ShbError): self.inspect()
        with self.assertRaisesMessage(AccessRecoveryError, 'recovery_effects_unfinished'):
            self.operation('release', basis=reset)
        _finish(effect, 'returned')
        self.assertTrue(self.inspect()['persisted_state_valid'])

    def test_missing_delivery_blocks_release_instead_of_inventing_a_new_notice(self):
        from .models import TransactionNoticeDelivery
        with self.corrupt_owned_fixture('shb_transactionnoticedelivery','shb_transaction_delivery_guard'):
            TransactionNoticeDelivery.objects.all().delete()
        self.refuse_release()
        self.assertEqual(TransactionNoticeDelivery.objects.count(), 0)

    def test_self_consistent_notice_hash_cannot_change_its_source_recipient(self):
        from .models import TransactionNotice
        from . import catalog
        notice = TransactionNotice.objects.get()
        changed = dict(notice.payload, recipient='other@synthetic.invalid')
        with self.corrupt_owned_fixture('shb_transactionnotice','shb_transaction_notice_guard'):
            TransactionNotice.objects.filter(pk=notice.pk).update(payload=changed, sha256=catalog.digest(changed))
        self.refuse_release()

    def test_applied_request_closing_requires_original_archived_intent(self):
        self.withdraw()
        (Path(self.directory.name) / ('blob-' + self.closure.sha256)).unlink()
        self.refuse_release()

    def test_interrupted_closing_replays_its_intent_after_revocation_without_reclaiming_coupon(self):
        from shop.adapters.evidence_archive import PreparedArchive, ArchiveError
        from shop.worker.services import execute_once
        from .models import DiscountReservation, Invitation, RequestClosure, TransactionNotice
        self.assertEqual(self.issue().status_code, 201)
        published = PreparedArchive.publish
        def interrupt(archive, key, raw):
            if json.loads(raw).get('kind') == 'shb-request-closure': raise ArchiveError('owned fixture interruption')
            return published(archive, key, raw)
        with override_settings(**self.customer_settings), patch.object(PreparedArchive,'publish',new=interrupt):
            response = self.client.post('/purchase/shb/offer/'+str(self.offer().pk)+'/',
                {'action':'withdraw','request_id':str(uuid.uuid4())}, secure=True)
        self.assertEqual(response.status_code, 503)
        close = RequestClosure.objects.get()
        self.assertIsNone(close.applied_at)
        self.assertEqual(DiscountReservation.objects.get().state, 'reserved')
        expiry = self.discount.expires_at; offer_expiry = self.offer().expires_at
        Invitation.objects.filter(pk=self.invitation.pk).update(revoked_at=timezone.now())
        reset=uuid.uuid4(); self.operation(request_id=reset)
        self.assertEqual(self.inspect()['counts']['pending_request_closures'], 1)
        self.operation('release', basis=reset)
        for _ in range(12):
            if not execute_once(): break
        else: self.fail('Owned worker did not drain bounded fixture work')
        close.refresh_from_db()
        self.assertIsNotNone(close.applied_at)
        hold=DiscountReservation.objects.get()
        self.assertEqual(hold.state,'released'); self.assertEqual(hold.release_lifecycle_id,close.pk)
        self.assertEqual(hold.discount.expires_at,expiry); self.assertEqual(self.offer().expires_at,offer_expiry)
        self.assertEqual(TransactionNotice.objects.filter(event='request-closed').count(),1)
        self.assertEqual(RequestClosure.objects.count(),1)

    def test_committed_capture_before_process_loss_resumes_same_envelope_and_proof(self):
        from shop.adapters.evidence_archive import PreparedArchive
        from shop.worker.services import execute_once
        from . import transaction_mail as mail
        from .models import TransactionNoticeCapture as Capture, TransactionNoticeDelivery as Delivery
        claim=mail.claim(lease_seconds=1)
        with PreparedArchive(Path(self.directory.name)) as archive:
            self.assertTrue(mail.capture(claim,archive))
        original=Capture.objects.get(); delivery=Delivery.objects.get()
        Delivery.objects.filter(pk=delivery.pk).update(lease_until=timezone.now()-timedelta(seconds=1))
        reset=uuid.uuid4();self.operation(request_id=reset)
        self.assertEqual(self.inspect()['counts']['transaction_captures'],1)
        self.operation('release',basis=reset)
        self.assertTrue(execute_once());self.assertFalse(execute_once())
        self.assertEqual(Capture.objects.count(),1);self.assertEqual(Capture.objects.get().pk,original.pk)
        self.assertEqual(Delivery.objects.get().state,'captured')
        self.assertFalse(Capture.objects.get().payload['actual_email_sent'])

    def test_original_month_end_clocks_revocation_and_coupon_outcomes_survive_selected_restore(self):
        from .invitations import issue_fixture
        from .models import Invitation, DiscountReservation
        for created in (datetime(2023,8,31,6,tzinfo=utc_timezone.utc),datetime(2024,8,31,6,tzinfo=utc_timezone.utc)):
            issue_fixture(customer=self.customer,issuer=self.issuer,company_name=self.invitation.company_name,created_at=created)
        Invitation.objects.filter(pk=self.invitation.pk).update(revoked_at=timezone.now())
        before_invites=list(Invitation.objects.order_by('pk').values())
        expiry=self.discount.expires_at;hold=DiscountReservation.objects.get()
        reset=uuid.uuid4()
        with override_settings(LOCAL_RESTORE_ID=reset):
            self.operation(request_id=reset)
            self.assertTrue(self.inspect()['persisted_state_valid'])
            result=self.operation('release',basis=reset)
            self.assertFalse(result['startup_recovery_pending'])
            self.assertEqual(list(Invitation.objects.order_by('pk').values()),before_invites)
            self.assertEqual(DiscountReservation.objects.get().snapshot,hold.snapshot)
            self.assertEqual(DiscountReservation.objects.get().state,'reserved')
            self.assertEqual(DiscountReservation.objects.get().discount.expires_at,expiry)
            self.credential.refresh_from_db();self.assertFalse(self.credential.enabled)
            with override_settings(**self.customer_settings):
                self.assertEqual(self.client.get('/purchase/simple/',secure=True).status_code,403)

    def test_missing_material_revision_link_blocks_release_without_recreating_it(self):
        from .models import RequestReplacement
        self.withdraw();self.assertEqual(self.revised().status_code,200)
        with self.corrupt_owned_fixture('shb_requestreplacement','shb_request_replacement_guard'):
            RequestReplacement.objects.all().delete()
        self.refuse_release()
        self.assertEqual(RequestReplacement.objects.count(),0)

    def test_missing_discount_reservation_cannot_silently_erase_captured_concession(self):
        from .models import DiscountReservation
        with self.corrupt_owned_fixture('shb_discountreservation','shb_discount_reservation_guard','shb_discount_release_guard'):
            DiscountReservation.objects.all().delete()
        self.refuse_release()

    def test_uncertain_payment_stays_lookup_only_and_reconciliation_keeps_original_order(self):
        from shop.adapters.evidence_archive import PreparedArchive
        from shop.catalog import checkout_payment as payment
        from shop.catalog.models import SyntheticCheckoutAcceptance
        from shop.payments.models import SyntheticBankOperation, SyntheticPaymentAttempt
        from .models import DiscountReservation, PaidOrder
        self.assertEqual(self.issue().status_code,201)
        response=self.accept_offer();self.assertEqual(response.status_code,302)
        original=payment.pay
        with patch('shop.catalog.checkout_payment.pay',side_effect=lambda *a,**k:original(*a,fault='after_commit',**k)):
            self.assertEqual(self.pay(response['Location']).status_code,409)
        accepted=SyntheticCheckoutAcceptance.objects.get()
        self.assertEqual(SyntheticPaymentAttempt.objects.get().state,'uncertain')
        reset=uuid.uuid4();self.operation(request_id=reset)
        report=self.inspect()
        self.assertEqual(report['counts']['uncertain_payments'],1)
        self.assertFalse(report['retry_authorized'])
        self.assertEqual(SyntheticBankOperation.objects.count(),1)
        self.operation('release',basis=reset)
        self.assertEqual(SyntheticPaymentAttempt.objects.get().state,'uncertain')
        self.assertEqual(DiscountReservation.objects.get().state,'reserved')
        with PreparedArchive(Path(self.directory.name)) as archive:
            payment.reconcile(self.customer,accepted.checkout_id,archive)
            payment.reconcile(self.customer,accepted.checkout_id,archive)
        self.assertEqual(SyntheticBankOperation.objects.count(),1)
        self.assertEqual(PaidOrder.objects.get().payload['order_reference'],str(accepted.pk))
        self.assertEqual(DiscountReservation.objects.get().state,'consumed')

    def test_exhausted_notice_remains_held_across_local_release(self):
        from . import transaction_mail
        from .models import TransactionNoticeDelivery,TransactionNoticeCapture
        claim=transaction_mail.claim(lease_seconds=1,max_attempts=1)
        TransactionNoticeDelivery.objects.filter(pk=claim.notice_id).update(lease_until=timezone.now()-timedelta(seconds=1))
        self.assertIsNone(transaction_mail.claim(max_attempts=1))
        reset=uuid.uuid4();self.operation(request_id=reset)
        self.assertEqual(self.inspect()['counts']['held_transaction_notices'],1)
        self.operation('release',basis=reset)
        self.assertFalse(transaction_mail.execute_once())
        self.assertEqual(TransactionNoticeDelivery.objects.get().state,'held')
        self.assertFalse(TransactionNoticeCapture.objects.exists())

    def test_paid_material_revision_and_captured_notices_keep_original_order_reference_on_replay(self):
        from shop.access.models import StaffQuotationGrant
        from shop.payments.models import SyntheticBankOperation
        from shop.worker.services import execute_once
        from .models import (RequestReplacement, PaidOrder, DiscountReservation,
            PurchaseNoticeCapture, TransactionNotice, TransactionNoticeCapture)
        self.withdraw();self.assertEqual(self.revised(discount_code=self.code).status_code,200)
        self.row=RequestReplacement.objects.select_related('request__quotation').get().request
        StaffQuotationGrant.objects.create(user=self.user,quotation=self.row.quotation,business_scope_version=2)
        self.route='quotation-requests/'+str(self.row.quotation_id)+'/shb-reviews/'
        self.value.update(scope_sha256=self.row.sha256,request_id=str(uuid.uuid4()),expected_review_version=0)
        del self.issue_value
        self.assertEqual(self.issue().status_code,201)
        response=self.accept_offer();self.assertEqual(response.status_code,302)
        self.assertEqual(self.pay(response['Location']).status_code,200)
        for _ in range(15):
            if not execute_once(): break
        else: self.fail('Owned worker did not drain bounded fixture work')
        order=PaidOrder.objects.get();capture_ids=set(TransactionNoticeCapture.objects.values_list('pk',flat=True))
        reference=order.payload['order_reference'];hold=DiscountReservation.objects.get(state='consumed')
        reset=uuid.uuid4();self.operation(request_id=reset)
        result=self.inspect()
        self.assertEqual(result['counts']['request_replacements'],1)
        self.assertEqual(result['counts']['paid_orders'],1)
        self.assertEqual(result['counts']['transaction_captures'],6)
        self.operation('release',basis=reset)
        self.assertFalse(execute_once())
        self.assertEqual(PaidOrder.objects.get().payload['order_reference'],reference)
        self.assertEqual(PaidOrder.objects.get().payload['purchase']['hours_purchased'],75)
        self.assertEqual(SyntheticBankOperation.objects.count(),1)
        self.assertEqual(TransactionNotice.objects.get(event='purchase-confirmed').payload['body']['reference'],reference)
        self.assertEqual(set(TransactionNoticeCapture.objects.values_list('pk',flat=True)),capture_ids)
        self.assertEqual(PurchaseNoticeCapture.objects.count(),1)
        self.assertEqual(DiscountReservation.objects.get(state='consumed').consumed_order_id,hold.consumed_order_id)

    def test_shb_28_restore_replay_preserves_invitation_expiry_order_reference_and_coupon_state(self):
        """SHB-28: a selected restore/replay within the existing recovery
        qualification preserves invitation expires_at + revoked_at, the
        PaidOrder.order_reference and the DiscountReservation state --
        staff never count a replay as a new purchase.

        Pairs with test_original_month_end_clocks_revocation_and_coupon_outcomes_survive_selected_restore
        (invitation clocks + coupon state through selected restore) and
        test_paid_material_revision_and_captured_notices_keep_original_order_reference_on_replay
        (order_reference preserved under revision/replay). This tags the
        composite invariant as SHB-28."""
        from .models import DiscountReservation, Invitation, PaidOrder
        from shop.payments.models import SyntheticBankOperation
        from shop.worker.services import execute_once
        # Issue offer, accept, pay -> one PaidOrder with reference.
        self.assertEqual(self.issue().status_code, 201)
        response = self.accept_offer(); self.assertEqual(response.status_code, 302)
        self.assertEqual(self.pay(response['Location']).status_code, 200)
        for _ in range(15):
            if not execute_once(): break
        order = PaidOrder.objects.get()
        reference = order.payload['order_reference']
        hours = order.payload['purchase']['hours_purchased']
        hold = DiscountReservation.objects.get(state='consumed')
        before_invitation = Invitation.objects.get(pk=self.invitation.pk)
        bank_ops_before = SyntheticBankOperation.objects.count()
        # Quarantine + inspect + release cycle (selected restore basis).
        reset = uuid.uuid4()
        self.operation(request_id=reset)
        result = self.inspect()
        self.assertEqual(result['counts']['paid_orders'], 1,
            'inspect confirms exactly one PaidOrder before release')
        self.operation('release', basis=reset)
        # (1) Invitation clocks preserved byte-identical.
        after_invitation = Invitation.objects.get(pk=self.invitation.pk)
        self.assertEqual(after_invitation.expires_at, before_invitation.expires_at,
            'restore must preserve original invitation expires_at')
        self.assertEqual(after_invitation.revoked_at, before_invitation.revoked_at,
            'restore must preserve original invitation revoked_at')
        self.assertEqual(after_invitation.token_digest, before_invitation.token_digest,
            'restore must preserve the original token_digest')
        # (2) PaidOrder.order_reference and hours preserved; no new order.
        self.assertEqual(PaidOrder.objects.count(), 1,
            'replay must not create a second PaidOrder')
        self.assertEqual(PaidOrder.objects.get().payload['order_reference'], reference,
            'replay preserves the original order_reference so staff see no new purchase')
        self.assertEqual(PaidOrder.objects.get().payload['purchase']['hours_purchased'], hours)
        # (3) DiscountReservation state preserved.
        self.assertEqual(DiscountReservation.objects.get().state, 'consumed')
        self.assertEqual(DiscountReservation.objects.get().consumed_order_id, hold.consumed_order_id)
        # (4) No duplicate bank operation from the restore.
        self.assertEqual(SyntheticBankOperation.objects.count(), bank_ops_before,
            'restore must not replay a bank operation')
