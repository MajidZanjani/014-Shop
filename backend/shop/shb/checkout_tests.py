"""Invitation-scoped SHB checkout on PostgreSQL; no real contracts or money."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path
import json
import tempfile
from threading import Barrier
from unittest.mock import patch
import uuid

from django.contrib.auth import get_user_model
from django.db import DatabaseError, connections, transaction
from django.test import TransactionTestCase, override_settings
from django.utils import timezone

from . import catalog
from .tests import ShopClient, form_data


@override_settings(SHB_SYNTHETIC_FIXTURE=True)
class CheckoutTests(TransactionTestCase):
    client_class = ShopClient

    def setUp(self):
        from .invitations import issue_fixture
        self.customer = get_user_model().objects.create_user(username='shb-checkout-customer')
        self.issuer = get_user_model().objects.create_user(username='shb-checkout-issuer', is_staff=True)
        self.invitation, self.token = issue_fixture(customer=self.customer, issuer=self.issuer,
            company_name='Synthetic Company Limited', project_reference='SLL fixture')
        self.client.get('/invite/' + self.token, secure=True)
        self.directory = tempfile.TemporaryDirectory(prefix='shb-checkout-')
        self.addCleanup(self.directory.cleanup)
        self.settings_context = override_settings(LOCAL_CHECKOUT_ARCHIVE_ROOT=self.directory.name)
        self.settings_context.enable(); self.addCleanup(self.settings_context.disable)
        self.data = form_data(quantity='3', action='review', accept_terms='', privacy_acknowledged='')

    def review(self, client=None, **changes):
        data = dict(self.data, **changes)
        response = (client or self.client).post('/purchase/simple/', data, secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context.get('review_digest'), 'FPGA review must expose an exact signed review')
        return data, response.context['review_digest']

    def checkout(self, data=None, token=None, client=None):
        if data is None: data, token = self.review()
        return (client or self.client).post('/purchase/simple/', dict(data, action='checkout',
            review_digest=token, accept_terms='on', privacy_acknowledged='on'), secure=True)

    def saved(self):
        from .models import SupportCheckout
        return SupportCheckout.objects.select_related('checkout').get()

    def acceptance(self):
        from shop.catalog.models import SyntheticCheckoutAcceptance
        return SyntheticCheckoutAcceptance.objects.select_related('checkout', 'attempt').get()

    def test_review_has_no_commercial_effect_and_checkout_accepts_exact_hours_once(self):
        from shop.catalog.models import SyntheticCheckout, SyntheticFulfilment
        from shop.payments.models import SyntheticPaymentAttempt
        data, token = self.review()
        self.assertEqual(SyntheticCheckout.objects.count(), 0)
        response = self.checkout(data, token)
        self.assertEqual(response.status_code, 302, (response.context.get('error'),response.context['form'].errors) if response.context else 'no context')
        saved = self.saved(); accepted = self.acceptance()
        self.assertIsNotNone(accepted.simulated_accepted_at)
        self.assertEqual(saved.checkout.snapshot['purchase']['hours_purchased'], 30)
        self.assertEqual(saved.checkout.snapshot['purchase']['quantity'], 3)
        self.assertEqual(saved.checkout.snapshot['purchase']['hours_per_bundle'], 10)
        self.assertIsNone(saved.checkout.business_snapshot_id)
        self.assertTrue(saved.checkout.archive_receipt); self.assertTrue(accepted.archive_receipt)
        self.assertEqual(self.checkout(data, token)['Location'], response['Location'])
        self.assertEqual(SyntheticCheckout.objects.count(), 1)
        self.assertEqual(SyntheticPaymentAttempt.objects.count(), 0)
        self.assertEqual(SyntheticFulfilment.objects.count(), 0)
        self.assertFalse(self.client.session.get('_auth_user_id'))

    def test_terms_privacy_digest_and_material_edits_require_review(self):
        from shop.catalog.models import SyntheticCheckout
        data, token = self.review()
        for changes in ({'accept_terms':''}, {'privacy_acknowledged':''}, {'review_digest':'bad'},
                {'quantity':'2'}, {'contact_email':'changed@synthetic.invalid'}, {'customer_id':'1'},
                {'total_minor':'1'}, {'hours_purchased':'100'}, {'approved':'on'}):
            value = dict(data, action='checkout', review_digest=token,
                accept_terms='on', privacy_acknowledged='on', **{})
            value.update(changes)
            response = self.client.post('/purchase/simple/', value, secure=True)
            self.assertIn(response.status_code, (409, 422))
        self.assertEqual(SyntheticCheckout.objects.count(), 0)

    def test_price_or_policy_change_requires_new_review(self):
        from shop.catalog.models import SyntheticCheckout
        data, token = self.review()
        offer = catalog.synthetic_offer()
        with patch('shop.shb.catalog.synthetic_offer', return_value=dict(offer, fpga_hourly_minor=11000)):
            self.assertEqual(self.checkout(data, token).status_code, 409)
        self.assertEqual(SyntheticCheckout.objects.count(), 0)

    def test_current_invitation_and_session_scope_required_for_every_purchase_read_write(self):
        from .models import Invitation
        data, token = self.review(); result = self.checkout(data, token)
        self.assertEqual(result.status_code, 302); path = result['Location']
        other = ShopClient(); other.get('/invite/' + self.token, secure=True)
        self.assertEqual(other.get(path, secure=True).status_code, 404)
        self.assertEqual(self.checkout(data, token, other).status_code, 409)
        Invitation.objects.filter(pk=self.invitation.pk).update(revoked_at=timezone.now())
        self.assertEqual(self.client.get(path, secure=True).status_code, 403)
        self.assertEqual(self.client.post(path, {'action':'pay'}, secure=True).status_code, 403)

    def test_unapproved_asic_and_unknown_live_config_cannot_capture_checkout(self):
        from shop.catalog.models import SyntheticCheckout
        self.assertIn(self.checkout(dict(self.data, variant='shb-asic-25h', assistance='Help'), 'bad').status_code, (409, 422))
        data, token = self.review()
        with override_settings(SHB_SYNTHETIC_FIXTURE=False):
            self.assertEqual(self.checkout(data, token).status_code, 503)
        self.assertEqual(SyntheticCheckout.objects.count(), 0)

    def test_archive_failure_retains_identity_without_acceptance_or_payment_and_retry_recovers(self):
        from shop.adapters.evidence_archive import PreparedArchive, ArchiveError
        from shop.payments.models import SyntheticPaymentAttempt
        data, token = self.review()
        with patch.object(PreparedArchive, 'publish', side_effect=ArchiveError('archive_unavailable')):
            self.assertEqual(self.checkout(data, token).status_code, 503)
        saved = self.saved(); accepted = self.acceptance()
        self.assertIsNone(accepted.simulated_accepted_at)
        self.assertEqual(SyntheticPaymentAttempt.objects.count(), 0)
        self.assertEqual(self.checkout(data, token).status_code, 302)
        self.assertEqual(self.saved().pk, saved.pk)
        self.assertIsNotNone(self.acceptance().simulated_accepted_at)

    def test_revocation_during_archive_prevents_acceptance(self):
        from shop.adapters.evidence_archive import PreparedArchive
        from .models import Invitation
        original = PreparedArchive.publish
        def revoke(archive, *args):
            receipt = original(archive, *args)
            Invitation.objects.filter(pk=self.invitation.pk, revoked_at__isnull=True).update(revoked_at=timezone.now())
            return receipt
        data, token = self.review()
        with patch.object(PreparedArchive, 'publish', revoke):
            self.assertEqual(self.checkout(data, token).status_code, 403)
        self.assertIsNone(self.acceptance().simulated_accepted_at)

    def test_coupon_is_held_once_and_retry_preserves_locked_price_after_revocation(self):
        from .discounts import issue_fixture
        from .models import DiscountCode, DiscountReservation, DiscountThrottle
        code, raw = issue_fixture(customer=self.customer, issuer=self.issuer,
            percentage_bps=1250, fpga_allowed=True, asic_allowed=True)
        data, token = self.review(discount_code=raw)
        self.assertEqual(DiscountReservation.objects.count(), 0)
        self.assertEqual(self.checkout(data, token).status_code, 302)
        original = self.saved().checkout.snapshot
        self.assertEqual(original['purchase']['hours_purchased'], 30)
        self.assertEqual(original['total_minor'], 262500)
        self.assertEqual(DiscountReservation.objects.get().checkout_id, self.saved().pk)
        DiscountCode.objects.filter(pk=code.pk).update(revoked_at=timezone.now())
        with patch('shop.shb.discounts.now', return_value=code.expires_at + timedelta(days=1)):
            self.assertEqual(self.checkout(data, token).status_code, 302)
        self.assertEqual(self.saved().checkout.snapshot, original)
        self.assertEqual(DiscountReservation.objects.count(), 1)
        self.assertEqual(DiscountThrottle.objects.get().attempts, 2)  # preview + new checkout
        self.assertNotIn(raw, json.dumps(original))

    def test_parallel_same_checkout_is_one_acceptance_and_reservation(self):
        from .discounts import issue_fixture
        from .models import DiscountReservation, SupportCheckout
        from shop.catalog.models import SyntheticCheckoutAcceptance
        _, raw = issue_fixture(customer=self.customer, issuer=self.issuer, percentage_bps=1000, fpga_allowed=True)
        data, token = self.review(discount_code=raw); cookies = self.client.cookies.copy(); barrier = Barrier(2)
        def submit(_):
            try:
                client = ShopClient(); client.cookies = cookies.copy(); barrier.wait(timeout=5)
                return self.checkout(data, token, client).status_code
            finally: connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool: statuses = list(pool.map(submit, range(2)))
        # The shared archive deliberately fails closed on publication contention.
        # A held response must recover the same immutable identity on exact retry.
        self.assertTrue(all(status in (302,503) for status in statuses),statuses)
        self.assertIn(302,statuses)
        self.assertEqual(self.checkout(data,token).status_code,302)
        self.assertEqual(SupportCheckout.objects.count(), 1)
        self.assertEqual(SyntheticCheckoutAcceptance.objects.count(), 1)
        self.assertEqual(DiscountReservation.objects.count(), 1)

    def test_synthetic_payment_reuses_attempt_and_never_calls_time_or_ip_finalizer(self):
        from shop.catalog.models import SyntheticFulfilment
        from shop.payments.models import SyntheticPaymentAttempt, SyntheticBankOperation
        response = self.checkout(); self.assertEqual(response.status_code, 302); path = response['Location']
        page = self.client.get(path, secure=True)
        self.assertEqual(page.status_code, 200); self.assertContains(page, '30 hours in this order')
        with patch('shop.catalog.fulfilment.provision', side_effect=AssertionError('legacy finalizer called')):
            for _ in range(2): self.assertEqual(self.client.post(path, {'action':'pay'}, secure=True).status_code, 200)
        self.assertEqual(SyntheticPaymentAttempt.objects.count(), 1)
        self.assertEqual(SyntheticBankOperation.objects.count(), 1)
        self.assertEqual(SyntheticFulfilment.objects.count(), 0)
        self.assertFalse(self.acceptance().effects_authorized)
        from shop.adapters.evidence_archive import PreparedArchive
        from shop.catalog import fulfilment
        from shop.catalog.checkout import CheckoutError
        with PreparedArchive(Path(self.directory.name)) as archive:
            with self.assertRaisesMessage(CheckoutError,'shb_manual_support_only'):
                fulfilment.provision(self.customer,self.saved().pk,archive)

    def test_uncertain_dispatch_is_lookup_only_and_internal_reconciliation_survives_invite_expiry(self):
        from shop.adapters.evidence_archive import PreparedArchive
        from shop.catalog import checkout_payment
        from .models import Invitation
        from shop.payments.models import SyntheticBankOperation
        response = self.checkout(); self.assertEqual(response.status_code, 302); path = response['Location']
        original = checkout_payment.pay
        def interrupted(*args, **kwargs): return original(*args, fault='after_commit', **kwargs)
        with patch('shop.catalog.checkout_payment.pay', side_effect=interrupted):
            self.assertEqual(self.client.post(path, {'action':'pay'}, secure=True).status_code, 409)
        attempt = self.acceptance().attempt; self.assertEqual(attempt.state, 'uncertain')
        self.assertEqual(self.client.post(path, {'action':'pay'}, secure=True).status_code, 200)
        self.assertEqual(SyntheticBankOperation.objects.count(), 1)
        Invitation.objects.filter(pk=self.invitation.pk).update(revoked_at=timezone.now())
        with PreparedArchive(Path(self.directory.name)) as archive:
            result = checkout_payment.reconcile(self.customer, self.saved().pk, archive)
        self.assertEqual(result.attempt.provider_status, 'captured')
        self.assertEqual(self.client.get(path, secure=True).status_code, 403)

    def test_sql_immutability_prevents_rewrite_and_reservation_release_without_outcome(self):
        from .discounts import issue_fixture
        from .models import DiscountReservation, SupportCheckout
        from shop.catalog.models import SyntheticCheckout, SyntheticCheckoutAcceptance
        _, raw = issue_fixture(customer=self.customer, issuer=self.issuer, percentage_bps=1000, fpga_allowed=True)
        data, token = self.review(discount_code=raw); self.assertEqual(self.checkout(data, token).status_code, 302)
        for queryset, changes in [(SupportCheckout.objects.all(), {'submission_sha256':'0'*64}),
                (SyntheticCheckout.objects.all(), {'snapshot':{}}),
                (SyntheticCheckoutAcceptance.objects.all(), {'payload':{}}),
                (DiscountReservation.objects.all(), {'state':'released'})]:
            with self.assertRaises(DatabaseError), transaction.atomic(): queryset.update(**changes)

    def test_new_invitation_does_not_authorize_other_checkout_or_legacy_history_route(self):
        from .invitations import issue_fixture
        response = self.checkout(); self.assertEqual(response.status_code, 302)
        identity = self.saved().pk
        _, token = issue_fixture(customer=self.customer, issuer=self.issuer, company_name='Synthetic Company Limited')
        other = ShopClient(); other.get('/invite/' + token, secure=True)
        self.assertEqual(other.get(response['Location'], secure=True).status_code, 404)
        other.force_login(self.customer)
        self.assertIn(other.get('/purchase/checkout-rehearsal/' + str(identity) + '/payment/', secure=True).status_code, (403, 404))

    def test_native_checkout_requires_csrf_and_has_no_query_or_get_side_effect(self):
        from shop.payments.models import SyntheticPaymentAttempt
        response = self.checkout(); self.assertEqual(response.status_code, 302); path = response['Location']
        secure = ShopClient(enforce_csrf_checks=True); secure.cookies = self.client.cookies.copy()
        self.assertEqual(secure.post(path, {'action':'pay'}, secure=True, HTTP_ORIGIN='https://localhost').status_code, 403)
        self.assertEqual(self.client.get(path + '?action=pay', secure=True).status_code, 400)
        self.assertEqual(self.client.get(path, secure=True).status_code, 200)
        self.assertEqual(SyntheticPaymentAttempt.objects.count(), 0)


    def test_expired_review_and_expiry_during_archive_never_accept_or_dispatch(self):
        from datetime import datetime
        from shop.adapters.evidence_archive import PreparedArchive
        from shop.catalog.models import SyntheticCheckout
        from shop.payments.models import SyntheticPaymentAttempt
        from django.core import signing
        from .checkout import SALT
        data,token=self.review()
        until=datetime.fromisoformat(signing.loads(token,salt=SALT)['review_expires_at'])
        with patch('shop.shb.checkout.attempts.database_now',return_value=until):
            self.assertEqual(self.checkout(data,token).status_code,409)
        self.assertEqual(SyntheticCheckout.objects.count(),0)
        original=PreparedArchive.publish
        def delayed(archive,*args):
            receipt=original(archive,*args)
            if not self.clock_started:self.clock.start();self.clock_started=True
            return receipt
        self.clock_started=False
        self.clock=patch('shop.catalog.checkout_payment.attempts.database_now',return_value=until)
        try:
            with patch.object(PreparedArchive,'publish',delayed):
                self.assertEqual(self.checkout(data,token).status_code,409)
        finally:self.clock.stop()
        self.assertIsNone(self.acceptance().simulated_accepted_at)
        self.assertEqual(SyntheticPaymentAttempt.objects.count(),0)

    def test_bank_bounds_cannot_be_bypassed_by_a_discount_or_quantity(self):
        from shop.catalog.models import SyntheticCheckout
        from .discounts import issue_fixture
        offer=catalog.synthetic_offer()
        with patch('shop.shb.catalog.synthetic_offer',return_value=dict(offer,bank_max_minor=100)):
            response=self.client.post('/purchase/simple/',self.data,secure=True)
            self.assertEqual(response.status_code,422)
        _,raw=issue_fixture(customer=self.customer,issuer=self.issuer,percentage_bps=9999,fpga_allowed=True)
        with patch('shop.shb.catalog.synthetic_offer',return_value=dict(offer,bank_min_minor=10000)):
            response=self.client.post('/purchase/simple/',dict(self.data,discount_code=raw),secure=True)
            self.assertEqual(response.status_code,422)
        self.assertEqual(SyntheticCheckout.objects.count(),0)

    def test_parallel_fpga_and_asic_claims_compete_for_the_same_one_use_code(self):
        from .discounts import issue_fixture
        from .models import DiscountReservation,SupportRequest,SupportCheckout
        _,raw=issue_fixture(customer=self.customer,issuer=self.issuer,percentage_bps=1000,fpga_allowed=True,asic_allowed=True)
        data,token=self.review(discount_code=raw)
        cookies=self.client.cookies.copy();barrier=Barrier(2)
        def submit(kind):
            try:
                client=ShopClient();client.cookies=cookies.copy();barrier.wait(timeout=5)
                if kind=='fpga':return self.checkout(data,token,client).status_code
                return client.post('/purchase/simple/',form_data(variant='shb-asic-25h',assistance='Help',action='submit',discount_code=raw),secure=True).status_code
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(submit,('fpga','asic')))
        self.assertIn(results,([302,422],[422,200]))
        self.assertEqual(DiscountReservation.objects.count(),1)
        self.assertEqual(SupportRequest.objects.count()+SupportCheckout.objects.count(),1)

    def test_shared_cart_retry_and_acceptance_provenance_are_sql_immutable(self):
        from shop.catalog.models import CartSnapshot,SyntheticCheckoutKey,SyntheticCheckoutAcceptance
        from shop.access.models import CustomerIdentity
        self.assertEqual(self.checkout().status_code,302)
        self.assertFalse(CustomerIdentity.objects.filter(user=self.customer,verified_at__isnull=False).exists())
        with self.assertRaisesMessage(DatabaseError,'retry scope provenance'),transaction.atomic():
            SyntheticCheckoutKey.objects.create(owner=self.issuer,request_id=uuid.uuid4(),checkout=self.saved().checkout)
        for rows,changes in [(CartSnapshot.objects.all(),{'lines':[]}),
                (SyntheticCheckoutKey.objects.all(),{'request_id':uuid.uuid4()}),
                (SyntheticCheckoutAcceptance.objects.all(),{'simulated_accepted_at':None})]:
            with self.assertRaises(DatabaseError),transaction.atomic():rows.update(**changes)

    def test_csrf_null_origin_exception_requires_same_origin_metadata_on_payment(self):
        from urllib.parse import urlencode
        from shop.payments.models import SyntheticPaymentAttempt
        response=self.checkout();path=response['Location']
        client=ShopClient(enforce_csrf_checks=True);client.cookies=self.client.cookies.copy()
        page=client.get(path,secure=True)
        import re
        token=re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"',page.content.decode())[1]
        data=urlencode({'action':'pay','csrfmiddlewaretoken':token})
        for metadata in ({},{'HTTP_SEC_FETCH_SITE':'cross-site'}):
            self.assertEqual(client.post(path,data,content_type='application/x-www-form-urlencoded',secure=True,HTTP_ORIGIN='null',**metadata).status_code,403)
        self.assertEqual(SyntheticPaymentAttempt.objects.count(),0)
        self.assertEqual(client.post(path,data,content_type='application/x-www-form-urlencoded',secure=True,HTTP_ORIGIN='null',HTTP_SEC_FETCH_SITE='same-origin').status_code,200)


    def test_revocation_during_attempt_archive_prevents_bank_claim_and_internal_start(self):
        from shop.adapters.evidence_archive import PreparedArchive
        from shop.catalog import checkout_payment
        from shop.catalog.checkout import CheckoutError
        from shop.payments.models import SyntheticBankOperation
        from .models import Invitation
        response=self.checkout();self.assertEqual(response.status_code,302)
        original=PreparedArchive.publish
        def revoked(archive,identity,body):
            receipt=original(archive,identity,body)
            if json.loads(body).get('kind')=='synthetic-payment-attempt':
                Invitation.objects.filter(pk=self.invitation.pk).update(revoked_at=timezone.now())
            return receipt
        with patch.object(PreparedArchive,'publish',revoked):
            self.assertEqual(self.client.post(response['Location'],{'action':'pay'},secure=True).status_code,403)
        self.assertEqual(self.acceptance().attempt.state,'prepared')
        self.assertEqual(SyntheticBankOperation.objects.count(),0)
        with PreparedArchive(Path(self.directory.name)) as archive:
            with self.assertRaisesMessage(CheckoutError,'invitation_required'):
                checkout_payment.pay(self.customer,self.saved().pk,archive)
        self.assertEqual(SyntheticBankOperation.objects.count(),0)

    def test_verified_capture_consumes_coupon_once_and_records_paid_purchase(self):
        from .discounts import issue_fixture
        from .models import DiscountReservation
        _,raw=issue_fixture(customer=self.customer,issuer=self.issuer,percentage_bps=1000,fpga_allowed=True)
        data,token=self.review(discount_code=raw)
        response=self.checkout(data,token);self.assertEqual(response.status_code,302)
        for _ in range(2):self.assertEqual(self.client.post(response['Location'],{'action':'pay'},secure=True).status_code,200)
        self.assertEqual(DiscountReservation.objects.get().state,'consumed')
        self.assertContains(self.client.get(response['Location'],secure=True),'Paid purchase recorded')

    def test_pre_dispatch_cancellation_releases_reserved_coupon_once(self):
        from .discounts import issue_fixture
        from .models import DiscountReservation
        _,raw=issue_fixture(customer=self.customer,issuer=self.issuer,percentage_bps=1000,fpga_allowed=True)
        data,token=self.review(discount_code=raw);response=self.checkout(data,token)
        self.assertEqual(response.status_code,302)
        response=self.client.post(response['Location'],{'action':'cancel'},secure=True)
        self.assertEqual(response.status_code,200)
        self.assertEqual(DiscountReservation.objects.get().state,'released')
