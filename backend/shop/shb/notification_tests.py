"""Ordinary transaction notices preserve source identity across worker retries."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path
from threading import Barrier
from unittest.mock import patch
import uuid

from django.db import DatabaseError, connections, transaction
from django.test import TransactionTestCase, override_settings
from django.utils import timezone

from . import review_tests, offer_tests


@override_settings(SHB_SYNTHETIC_FIXTURE=True)
class NotificationTests(TransactionTestCase):
    client_class = review_tests.RequestReviewTests.client_class
    post = review_tests.RequestReviewTests.post
    challenge = review_tests.RequestReviewTests.challenge
    authenticated = review_tests.RequestReviewTests.authenticated
    customer_submit = review_tests.RequestReviewTests.customer_submit
    submit = review_tests.RequestReviewTests.submit
    issue = offer_tests.OfferTests.issue
    offer = offer_tests.OfferTests.offer
    customer_review = offer_tests.OfferTests.customer_review
    accept_offer = offer_tests.OfferTests.accept_offer
    pay = offer_tests.OfferTests.pay

    def setUp(self):
        review_tests.RequestReviewTests.setUp(self)
        context=override_settings(LOCAL_CHECKOUT_ARCHIVE_ROOT=self.directory.name)
        context.enable();self.addCleanup(context.disable)

    def test_stored_asic_request_has_one_retryable_customer_acknowledgement(self):
        from shop.worker.services import execute_once
        self.assertTrue(execute_once(), 'A stored request must leave durable acknowledgement work.')
        from .models import TransactionNotice, TransactionNoticeCapture
        notice=TransactionNotice.objects.get(event='request-received')
        self.assertEqual(notice.payload['recipient'],'buyer@synthetic.invalid')
        self.assertEqual(notice.payload['body']['reference'],str(self.row.pk))
        self.assertEqual(TransactionNoticeCapture.objects.count(),1)
        self.assertFalse(execute_once())

    def test_request_retry_does_not_queue_second_notice_or_change_recipient_authority(self):
        from .models import TransactionNotice
        with override_settings(**self.customer_settings):
            self.assertEqual(self.customer_submit(request_id=str(self.row.request_id)).status_code,200)
        notice=TransactionNotice.objects.get()
        self.assertEqual(notice.payload['recipient_scope'],'this-transaction-only')
        self.assertIs(notice.payload['named_identity_verified'],False)
        self.assertEqual(TransactionNotice.objects.count(),1)

    def test_question_and_decline_notices_freeze_the_exact_review_message(self):
        from .models import TransactionNotice, DiscountReservation
        self.assertEqual(self.submit().status_code,201)
        self.assertEqual(self.submit().status_code,200)
        message='SLL cannot support this requested project scope.'
        self.assertEqual(self.submit(request_id=str(uuid.uuid4()),expected_review_version=1,
            decision='declined',message=message).status_code,201)
        self.assertEqual(TransactionNotice.objects.count(),3)
        self.assertEqual(TransactionNotice.objects.get(event='request-question').payload['body']['message'],self.value['message'])
        self.assertEqual(TransactionNotice.objects.get(event='request-declined').payload['body']['message'],message)
        self.assertEqual(DiscountReservation.objects.get().state,'released')

    def test_offer_and_customer_purchase_notices_keep_one_order_reference_and_no_balance(self):
        from .models import TransactionNotice, PaidOrder, DiscountReservation
        self.assertEqual(self.issue().status_code,201)
        response=self.accept_offer();self.assertEqual(response.status_code,302)
        self.assertEqual(self.pay(response['Location']).status_code,200)
        self.assertEqual(self.pay(response['Location']).status_code,200)
        self.assertEqual(TransactionNotice.objects.count(),3)
        offer=TransactionNotice.objects.get(event='offer-issued')
        self.assertEqual(offer.payload['body']['path'],'/purchase/shb/offer/'+str(self.offer().pk)+'/')
        notice=TransactionNotice.objects.get(event='purchase-confirmed');order=PaidOrder.objects.get()
        self.assertEqual(notice.payload['body']['reference'],order.payload['order_reference'])
        self.assertEqual(notice.payload['body']['hours_purchased'],50)
        self.assertEqual(DiscountReservation.objects.get().state,'consumed')
        self.assertNotIn('remaining_hours',notice.payload['body'])
        self.assertNotIn('assistance',notice.payload['body'])

    def test_customer_withdrawal_queues_its_committed_closing_once(self):
        from .models import TransactionNotice
        self.assertEqual(self.issue().status_code,201)
        path='/purchase/shb/offer/'+str(self.offer().pk)+'/'
        value={'action':'withdraw','request_id':str(uuid.uuid4())}
        with override_settings(**self.customer_settings):
            self.assertEqual(self.client.post(path,value,secure=True).status_code,200)
            self.assertEqual(self.client.post(path,value,secure=True).status_code,200)
        self.assertEqual(TransactionNotice.objects.filter(event='request-closed').count(),1)

    def test_archive_failure_retains_notice_and_lease_then_retry_reuses_same_capture(self):
        from shop.adapters.evidence_archive import PreparedArchive, ArchiveError
        from . import transaction_mail as mail
        from .models import TransactionNoticeDelivery as Delivery, TransactionNoticeCapture as Capture
        claimed=mail.claim(lease_seconds=1)
        with PreparedArchive(Path(self.directory.name)) as archive:
            with patch.object(PreparedArchive,'publish',side_effect=ArchiveError('unavailable')):
                with self.assertRaises(ArchiveError):mail.capture(claimed,archive)
            self.assertFalse(Capture.objects.exists())
            Delivery.objects.filter(pk=claimed.notice_id).update(lease_until=timezone.now()-timedelta(seconds=1))
            next_claim=mail.claim()
            self.assertFalse(mail.capture(claimed,archive))
            self.assertTrue(mail.capture(next_claim,archive))
            self.assertTrue(mail.capture(next_claim,archive))
            self.assertTrue(mail.complete(next_claim,archive))
        self.assertEqual(Capture.objects.count(),1)
        self.assertEqual(Delivery.objects.get().state,'captured')

    def test_capture_commit_before_worker_loss_is_recoverable_without_duplicate_notice(self):
        from shop.adapters.evidence_archive import PreparedArchive
        from . import transaction_mail as mail
        from .models import TransactionNoticeDelivery as Delivery, TransactionNoticeCapture as Capture
        claimed=mail.claim(lease_seconds=1)
        with PreparedArchive(Path(self.directory.name)) as archive:
            self.assertTrue(mail.capture(claimed,archive))
        Delivery.objects.filter(pk=claimed.notice_id).update(lease_until=timezone.now()-timedelta(seconds=1))
        from shop.worker.services import execute_once
        self.assertTrue(execute_once())
        self.assertEqual(Capture.objects.count(),1)
        self.assertEqual(Delivery.objects.get().state,'captured')

    def test_current_invitation_expiry_does_not_drop_already_stored_notice(self):
        from .models import Invitation, TransactionNoticeCapture
        Invitation.objects.filter(pk=self.invitation.pk).update(revoked_at=timezone.now())
        from shop.worker.services import execute_once
        self.assertTrue(execute_once())
        self.assertEqual(TransactionNoticeCapture.objects.count(),1)

    def test_parallel_claim_has_one_owner_and_exhaustion_is_bounded(self):
        from . import transaction_mail as mail
        from .models import TransactionNoticeDelivery as Delivery
        barrier=Barrier(2)
        def take(_):
            try:barrier.wait(timeout=5);return mail.claim(lease_seconds=1,max_attempts=1)
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:claims=list(pool.map(take,range(2)))
        self.assertEqual(sum(claim is not None for claim in claims),1)
        Delivery.objects.update(lease_until=timezone.now()-timedelta(seconds=1))
        self.assertIsNone(mail.claim(max_attempts=1))
        self.assertEqual(Delivery.objects.get().state,'held')

    def test_notice_body_recipient_source_and_capture_cannot_be_rewritten(self):
        from .models import TransactionNotice
        notice=TransactionNotice.objects.get()
        with self.assertRaises(DatabaseError),transaction.atomic():
            TransactionNotice.objects.filter(pk=notice.pk).update(payload=dict(notice.payload,recipient='other@synthetic.invalid'))

    def test_customer_notice_archive_failure_does_not_erase_paid_order_or_redeem_again(self):
        from shop.adapters.evidence_archive import PreparedArchive, ArchiveError
        from . import transaction_mail as mail
        from .models import TransactionNotice, TransactionNoticeDelivery as Delivery, PaidOrder, DiscountReservation
        self.assertEqual(self.issue().status_code,201)
        response=self.accept_offer();self.assertEqual(self.pay(response['Location']).status_code,200)
        with PreparedArchive(Path(self.directory.name)) as archive:
            for _ in range(3):
                claimed=mail.claim(lease_seconds=1)
                if TransactionNotice.objects.get(pk=claimed.notice_id).event=='purchase-confirmed':break
                self.assertTrue(mail.capture(claimed,archive));self.assertTrue(mail.complete(claimed,archive))
            else:self.fail('Purchase notice was not queued')
            with patch.object(PreparedArchive,'publish',side_effect=ArchiveError('mail evidence unavailable')):
                with self.assertRaises(ArchiveError):mail.capture(claimed,archive)
        order=PaidOrder.objects.get()
        self.assertEqual(DiscountReservation.objects.get().consumed_order_id,order.pk)
        Delivery.objects.filter(pk=claimed.notice_id).update(lease_until=timezone.now()-timedelta(seconds=1))
        self.assertTrue(mail.execute_once())
        self.assertEqual(PaidOrder.objects.count(),1)
        self.assertEqual(DiscountReservation.objects.get().consumed_order_id,order.pk)

    def test_sql_source_commit_cannot_omit_required_request_notice(self):
        from .models import SupportRequest
        with patch('shop.shb.transaction_mail.queue',return_value=None):
            with override_settings(**self.customer_settings),self.assertRaisesMessage(DatabaseError,'queue its ordinary notice atomically'):
                self.customer_submit(discount_code='')
        self.assertEqual(SupportRequest.objects.count(),1)

    def test_shb_09_approve_clarify_decline_withdraw_each_notices_state_and_no_paid_order(self):
        """SHB-09: each ASIC transition emits the correct customer notice,
        updates state as expected, keeps DiscountReservation in the right
        state, and leaves PaidOrder.objects.count() == 0 until an accepted
        verified payment.

        Pairs with:
        - test_stored_asic_request_has_one_retryable_customer_acknowledgement
          (submission -> request-received notice)
        - test_question_and_decline_notices_freeze_the_exact_review_message
          (clarify -> request-question notice; decline -> request-declined;
          reservation released on decline)
        - test_customer_withdrawal_queues_its_committed_closing_once
          (withdraw -> request-closed notice, idempotent)
        - test_offer_and_customer_purchase_notices_keep_one_order_reference_and_no_balance
          (approve+issue -> offer-issued notice; pay -> purchase-confirmed)

        This tags the composite as SHB-09 and chains clarify -> approve ->
        issue -> withdraw on a single request, with a separate decline
        branch, asserting PaidOrder.objects.count() == 0 at every
        pre-payment point."""
        from .models import DiscountReservation, PaidOrder, SupportRequest, TransactionNotice
        # (A) Starting from the submitted state, PaidOrder is zero.
        self.assertEqual(PaidOrder.objects.count(), 0, 'submitted state must have no PaidOrder')
        self.assertTrue(TransactionNotice.objects.filter(event='request-received').exists())
        # (B) Clarify (needs_information) -> state 'needs_information', notice emitted.
        self.assertEqual(self.submit().status_code, 201)
        self.assertEqual(SupportRequest.objects.get().state, 'needs_information')
        self.assertTrue(TransactionNotice.objects.filter(event='request-question').exists())
        self.assertEqual(DiscountReservation.objects.get().state, 'reserved')
        self.assertEqual(PaidOrder.objects.count(), 0, 'needs_information must have no PaidOrder')
        # (C) Approve (ready_for_commercial_review from needs_information) ->
        # state 'under_review', no PaidOrder.
        self.assertEqual(self.submit(request_id=str(uuid.uuid4()), expected_review_version=1,
            decision='ready_for_commercial_review',
            message='Ready for commercial review').status_code, 201)
        self.assertEqual(SupportRequest.objects.get().state, 'under_review')
        self.assertEqual(DiscountReservation.objects.get().state, 'reserved')
        self.assertEqual(PaidOrder.objects.count(), 0, 'under_review must have no PaidOrder')
        # (D) Issue offer, then customer withdraws -> request-closed notice.
        issue_value = {'request_id': str(uuid.uuid4()), 'expected_review_version': 2,
            'scope_sha256': self.row.sha256,
            'prerequisites': 'Customer provides authorized tool access separately.',
            'exclusions': 'No tape-out or sign-off commitment.'}
        self.assertEqual(self.post('quotation-requests/' + str(self.row.quotation_id) +
            '/shb-offers/', issue_value).status_code, 201)
        self.assertTrue(TransactionNotice.objects.filter(event='offer-issued').exists())
        self.assertEqual(PaidOrder.objects.count(), 0, 'offer_issued must have no PaidOrder')
        path = '/purchase/shb/offer/' + str(self.offer().pk) + '/'
        with override_settings(**self.customer_settings):
            self.assertEqual(self.client.post(path, {'action': 'withdraw',
                'request_id': str(uuid.uuid4())}, secure=True).status_code, 200)
        self.assertEqual(TransactionNotice.objects.filter(event='request-closed').count(), 1)
        self.assertEqual(PaidOrder.objects.count(), 0,
            'withdrawn offer must have no PaidOrder (completion requires accepted verified payment)')
        # (E) Separately, assert decline-from-needs_information releases the hold
        # using a fresh second request (independent of the chain above).
        with override_settings(**self.customer_settings):
            self.assertEqual(self.customer_submit(discount_code='').status_code, 200)
        second = SupportRequest.objects.exclude(pk=self.row.pk).get()
        from shop.access.models import StaffQuotationGrant
        StaffQuotationGrant.objects.create(user=self.user, quotation=second.quotation,
            business_scope_version=second.revision)
        route = 'quotation-requests/' + str(second.quotation_id) + '/shb-reviews/'
        decline_value = {'request_id': str(uuid.uuid4()), 'expected_review_version': 0,
            'scope_sha256': second.sha256, 'decision': 'declined',
            'message': 'The requested scope cannot be supported.'}
        self.assertEqual(self.post(route, decline_value).status_code, 201)
        self.assertEqual(SupportRequest.objects.get(pk=second.pk).state, 'declined')
        self.assertTrue(TransactionNotice.objects.filter(event='request-declined').exists())
        self.assertEqual(PaidOrder.objects.count(), 0,
            'declined request must have no PaidOrder')
