"""Scoped percentage-code invariants on actual PostgreSQL transactions."""
from datetime import timedelta
import json
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch
import uuid

from django.contrib.auth import get_user_model
from django.db import DatabaseError, connections, transaction
from django.test import TransactionTestCase, override_settings
from django.utils import timezone

from .tests import ShopClient, form_data


@override_settings(SHB_SYNTHETIC_FIXTURE=True)
class DiscountTests(TransactionTestCase):
    client_class = ShopClient

    def setUp(self):
        from .invitations import issue_fixture
        from .discounts import issue_fixture as issue_discount
        self.customer = get_user_model().objects.create_user(username='discount-customer')
        self.issuer = get_user_model().objects.create_user(username='discount-issuer', is_staff=True)
        self.invitation, token = issue_fixture(customer=self.customer, issuer=self.issuer,
            company_name='Synthetic Company Limited', project_reference='SLL fixture')
        self.client.get('/invite/' + token, secure=True)
        self.discount, self.code = issue_discount(customer=self.customer, issuer=self.issuer,
            percentage_bps=1250, fpga_allowed=True, asic_allowed=True)

    def post(self, **changes):
        data = form_data(variant='shb-asic-25h', quantity='2', assistance='Help with SLL IP',
            action='submit', discount_code=self.code, accept_terms='')
        data.update(changes)
        return self.client.post('/purchase/simple/', data, secure=True)

    def test_apply_and_remove_preview_only_and_preserve_hours(self):
        from .models import DiscountReservation, SupportRequest
        response = self.post(action='apply_discount')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['purchase']['hours_purchased'], 50)
        self.assertEqual(response.context['purchase']['discount_minor'], 125000)
        self.assertEqual(response.context['purchase']['total_minor'], 875000)
        self.assertContains(response, 'Discount applied')
        response = self.post(action='remove_discount')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['purchase']['discount_bps'], 0)
        self.assertNotContains(response, 'value="' + self.code + '"')
        self.assertEqual(DiscountReservation.objects.count(), 0)
        self.assertEqual(SupportRequest.objects.count(), 0)

    def test_get_does_not_claim_or_test_codes(self):
        from .models import DiscountReservation, DiscountThrottle
        self.client.get('/purchase/simple/', secure=True)
        response = self.client.get('/purchase/simple/', {'discount_code': self.code}, secure=True)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(DiscountReservation.objects.count(), 0)
        self.assertEqual(DiscountThrottle.objects.count(), 0)

    def test_raw_code_is_not_in_any_request_or_discount_record(self):
        from .models import DiscountCode, DiscountReservation, SupportRequest
        from .discounts import verifier
        response = self.post(discount_code=self.code.lower())
        self.assertEqual(response.status_code, 200)
        row = SupportRequest.objects.get()
        self.assertEqual(row.payload['purchase']['discount_bps'], 1250)
        self.assertEqual(DiscountCode.objects.get().code_digest, verifier(self.code))
        for model in (DiscountCode, DiscountReservation, SupportRequest):
            self.assertNotIn(self.code, json.dumps(list(model.objects.values()), default=str))
        self.assertEqual(row.payload['details']['discount_code'], '')
        self.assertEqual(DiscountReservation.objects.get().request_id, row.pk)

    def test_wrong_customer_and_variant_expiry_revocation_and_stacking_are_generic(self):
        from .discounts import issue_fixture
        other = get_user_model().objects.create_user(username='other-discount-customer')
        now = timezone.now()
        options = [dict(customer=other), dict(asic_allowed=False),
            dict(starts_at=now + timedelta(days=1), expires_at=now + timedelta(days=2)),
            dict(starts_at=now - timedelta(days=2), expires_at=now - timedelta(days=1))]
        for changes in options:
            values = dict(customer=self.customer, issuer=self.issuer, percentage_bps=1000,
                fpga_allowed=True, asic_allowed=True)
            values.update(changes)
            _, code = issue_fixture(**values)
            with self.subTest(changes=tuple(changes)):
                response = self.post(discount_code=code)
                self.assertEqual(response.status_code, 422)
                self.assertContains(response, 'Discount unavailable', status_code=422)
        response = self.post(discount_code=self.code + ',SLL-OTHER')
        self.assertEqual(response.status_code, 422)
        response = self.post(discount_bps='9999')
        self.assertEqual(response.status_code, 422)
        from .models import DiscountCode, DiscountReservation, SupportRequest
        DiscountCode.objects.filter(pk=self.discount.pk).update(revoked_at=now)
        self.assertEqual(self.post().status_code, 422)
        self.assertFalse(DiscountReservation.objects.exists())
        self.assertFalse(SupportRequest.objects.exists())

    def test_exact_claim_expiry_and_live_configuration_fail_closed(self):
        with patch('shop.shb.discounts.now', return_value=self.discount.expires_at):
            self.assertEqual(self.post().status_code, 422)
        for settings in ({'SHB_SYNTHETIC_FIXTURE': False}, {'SHOP_ENV': 'production'},
                {'LIVE_PAYMENTS_ENABLED': True}, {'PAYMENT_ADAPTER': 'real'}):
            with self.subTest(settings=settings), override_settings(**settings):
                self.assertEqual(self.post(action='apply_discount').status_code, 503)

    def test_reservation_survives_expiry_revocation_and_rate_change_on_retry(self):
        from . import catalog
        from .models import DiscountCode, DiscountReservation, SupportRequest
        identity = str(uuid.uuid4())
        first = self.post(request_id=identity)
        self.assertEqual(first.status_code, 200)
        original = SupportRequest.objects.get().payload
        DiscountCode.objects.filter(pk=self.discount.pk).update(revoked_at=timezone.now())
        changed = dict(catalog.synthetic_offer(), asic_hourly_minor=30000)
        with patch('shop.shb.discounts.now', return_value=self.discount.expires_at + timedelta(days=31)), \
                patch('shop.shb.catalog.synthetic_offer', return_value=changed):
            response = self.post(request_id=identity)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['purchase'], original['purchase'])
        self.assertEqual(SupportRequest.objects.count(), 1)
        self.assertEqual(DiscountReservation.objects.count(), 1)
        self.assertEqual(self.post(request_id=identity, quantity='1').status_code, 409)
        self.assertEqual(self.post(request_id=identity, discount_code='').status_code, 409)

    def test_retry_does_not_spend_guessing_budget_or_reserve_again(self):
        from .models import DiscountReservation, DiscountThrottle
        identity = str(uuid.uuid4())
        self.assertEqual(self.post(request_id=identity).status_code, 200)
        for _ in range(12):
            self.assertEqual(self.post(request_id=identity).status_code, 200)
        self.assertEqual(DiscountThrottle.objects.get().attempts, 1)
        self.assertEqual(DiscountReservation.objects.count(), 1)
        self.assertEqual(self.post().status_code, 422)

    def test_invalid_attempt_budget_is_durable_and_shared_across_invitations(self):
        from .discounts import MAX_ATTEMPTS
        from .invitations import issue_fixture
        from .models import DiscountThrottle
        for _ in range(MAX_ATTEMPTS):
            self.assertEqual(self.post(discount_code='SLL-NOT-A-CODE', action='apply_discount').status_code, 422)
        _, token = issue_fixture(customer=self.customer, issuer=self.issuer,
            company_name='Synthetic Company Limited', project_reference='SLL fixture')
        self.client.get('/invite/' + token, secure=True)
        self.assertEqual(self.post(action='apply_discount').status_code, 429)
        self.assertEqual(DiscountThrottle.objects.get().attempts, MAX_ATTEMPTS)

    def test_parallel_requests_for_one_use_have_one_winner_and_atomic_rollback(self):
        from .invitations import issue_fixture
        from .models import DiscountReservation, SupportRequest
        from shop.catalog.models import QuotationRequest
        clients = [self.client]
        _, token = issue_fixture(customer=self.customer, issuer=self.issuer,
            company_name='Synthetic Company Limited', project_reference='SLL fixture')
        second = ShopClient(); second.get('/invite/' + token, secure=True); clients.append(second)
        barrier = Barrier(2)
        def submit(client):
            try:
                barrier.wait(timeout=5)
                return client.post('/purchase/simple/', form_data(variant='shb-asic-25h',
                    assistance='Help', action='submit', discount_code=self.code), secure=True).status_code
            finally:
                connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(submit, clients))
        self.assertEqual(sorted(outcomes), [200, 422])
        self.assertEqual(DiscountReservation.objects.count(), 1)
        self.assertEqual(SupportRequest.objects.count(), 1)
        self.assertEqual(QuotationRequest.objects.count(), 1)

    def test_parallel_same_request_returns_original_reservation(self):
        from .models import DiscountReservation, SupportRequest
        cookies = self.client.cookies.copy(); identity = str(uuid.uuid4()); barrier = Barrier(2)
        def submit(_):
            try:
                client = ShopClient(); client.cookies = cookies.copy(); barrier.wait(timeout=5)
                return client.post('/purchase/simple/', form_data(variant='shb-asic-25h',
                    assistance='Help', action='submit', discount_code=self.code,
                    request_id=identity), secure=True).status_code
            finally:
                connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(submit, range(2)))
        self.assertEqual(outcomes, [200, 200])
        self.assertEqual(DiscountReservation.objects.count(), 1)
        self.assertEqual(SupportRequest.objects.count(), 1)

    def test_database_rejects_policy_rewrite_and_unsafe_reservation_release(self):
        from .models import DiscountCode, DiscountReservation
        self.assertEqual(self.post().status_code, 200)
        for changes in ({'percentage_bps': 9900}, {'expires_at': self.discount.expires_at + timedelta(days=1)},
                {'use_limit': 5}, {'customer_id': self.issuer.pk}):
            with self.subTest(changes=tuple(changes)), self.assertRaises(DatabaseError), transaction.atomic():
                DiscountCode.objects.filter(pk=self.discount.pk).update(**changes)
        DiscountCode.objects.filter(pk=self.discount.pk).update(revoked_at=timezone.now())
        with self.assertRaises(DatabaseError), transaction.atomic():
            DiscountCode.objects.filter(pk=self.discount.pk).update(revoked_at=None)
        row = DiscountReservation.objects.get()
        for changes in ({'snapshot': {}}, {'slot': 2}, {'state': 'released'}, {'state': 'consumed'}):
            with self.subTest(changes=tuple(changes)), self.assertRaises(DatabaseError), transaction.atomic():
                DiscountReservation.objects.filter(pk=row.pk).update(**changes)
        with self.assertRaises(DatabaseError), transaction.atomic():
            DiscountReservation.objects.filter(pk=row.pk).delete()

    def test_failed_capture_rolls_back_reservation_but_keeps_attempt_budget(self):
        from . import discounts
        from .models import DiscountReservation, DiscountThrottle, SupportRequest
        from shop.catalog.models import CartSnapshot, QuotationRequest
        reserve = discounts.reserve
        def interrupted(*args):
            reserve(*args)
            raise RuntimeError('fixture failure after reservation insert')
        with patch('shop.shb.services.discounts.reserve', side_effect=interrupted):
            with self.assertRaises(RuntimeError): self.post()
        self.assertEqual(DiscountReservation.objects.count(), 0)
        self.assertEqual(SupportRequest.objects.count(), 0)
        self.assertEqual(CartSnapshot.objects.count(), 0)
        self.assertEqual(QuotationRequest.objects.count(), 0)
        self.assertEqual(DiscountThrottle.objects.get().attempts, 1)

    def test_database_arbitrates_concurrent_inserts_without_application_access_lock(self):
        from . import catalog
        from .models import DiscountReservation, SupportRequest
        # Deliberately omit reservation in two fixture captures to exercise the
        # database boundary directly, without the app's shared access-epoch lock.
        with patch('shop.shb.services.discounts.reserve', return_value=None):
            self.assertEqual(self.post().status_code, 200)
            self.assertEqual(self.post().status_code, 200)
        rows = list(SupportRequest.objects.all())
        barrier = Barrier(2)
        def insert(row):
            try:
                barrier.wait(timeout=5)
                with transaction.atomic():
                    snapshot = row.payload['purchase']['discount_policy']
                    DiscountReservation.objects.create(discount_id=self.discount.pk, request=row,
                        slot=1, snapshot=snapshot, sha256=catalog.digest(snapshot))
                return 'held'
            except DatabaseError as error:
                return error.__cause__.sqlstate
            finally:
                connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(insert, rows))
        self.assertEqual(sorted(results), ['23505', 'held'])
        self.assertEqual(DiscountReservation.objects.count(), 1)
        unused = next(row for row in rows if not DiscountReservation.objects.filter(request=row).exists())
        snapshot = unused.payload['purchase']['discount_policy']
        with self.assertRaisesMessage(DatabaseError, 'scope or capacity'), transaction.atomic():
            DiscountReservation.objects.create(discount=self.discount, request=unused, slot=2,
                snapshot=snapshot, sha256=catalog.digest(snapshot))
        with self.assertRaisesMessage(DatabaseError, 'scope or capacity'), transaction.atomic():
            DiscountReservation.objects.create(discount=self.discount, request=unused, slot=1,
                snapshot=dict(snapshot, percentage_bps=9999), sha256='a' * 64)

    def test_explicit_two_use_fixture_has_two_slots_and_no_third_claim(self):
        from .discounts import issue_fixture
        from .models import DiscountReservation
        row, code = issue_fixture(customer=self.customer, issuer=self.issuer,
            percentage_bps=1000, asic_allowed=True, use_limit=2)
        for expected in (200, 200, 422):
            self.assertEqual(self.post(discount_code=code).status_code, expected)
        self.assertEqual(set(DiscountReservation.objects.filter(discount=row).values_list('slot', flat=True)), {1, 2})

    def test_preview_for_fpga_does_not_bypass_checkout_or_asic_approval(self):
        from .models import DiscountReservation, SupportRequest
        from shop.payments.models import SyntheticPaymentAttempt
        response = self.post(variant='shb-fpga-10h', quantity='3', action='apply_discount')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['purchase']['total_minor'], 262500)
        self.assertEqual(response.context['purchase']['hours_purchased'], 30)
        self.assertEqual(self.post(variant='shb-fpga-10h', action='checkout').status_code, 422)  # exact review is required
        self.assertEqual(self.post(action='checkout').status_code, 422)  # unapproved ASIC cannot check out
        self.assertEqual(self.post(variant='shb-fpga-10h', action='submit').status_code, 422)
        self.assertFalse(SupportRequest.objects.exists())
        self.assertFalse(DiscountReservation.objects.exists())
        self.assertFalse(SyntheticPaymentAttempt.objects.exists())

    def test_discount_never_bypasses_revoked_access_or_duplicate_form_fields(self):
        from .models import Invitation, DiscountReservation, DiscountThrottle
        data = form_data(variant='shb-asic-25h', assistance='Help', action='submit',
            discount_code=[self.code, self.code])
        self.assertEqual(self.client.post('/purchase/simple/', data, secure=True).status_code, 422)
        Invitation.objects.filter(pk=self.invitation.pk).update(revoked_at=timezone.now())
        self.assertEqual(self.post().status_code, 403)
        self.assertFalse(DiscountReservation.objects.exists())
        self.assertFalse(DiscountThrottle.objects.exists())

    def test_shb_15_wrong_customer_variant_expired_revoked_or_stacked_rejects_no_bypass(self):
        """SHB-15: wrong-customer/variant/expired/revoked/stacked coupon
        attempts are rejected server-side with no access or approval bypass.

        Pairs with test_wrong_customer_and_variant_expiry_revocation_and_stacking_are_generic
        (same five branches at the generic level) and
        test_discount_never_bypasses_revoked_access_or_duplicate_form_fields
        (revoked-access branch). This test tags the invariant as SHB-15 and
        asserts the composite side-effect bound across all branches: 422
        'Discount unavailable', no DiscountReservation, no SupportRequest,
        and the invitation row/digest is left untouched by the rejection."""
        from .discounts import issue_fixture as issue_discount
        from .models import DiscountCode, DiscountReservation, Invitation, SupportRequest
        other = get_user_model().objects.create_user(username='shb-15-wrong-customer')
        now = timezone.now()
        before_invite_digest = self.invitation.token_digest
        branches = (
            ('wrong_customer', dict(customer=other)),
            ('wrong_variant', dict(asic_allowed=False)),
            ('not_yet_active', dict(starts_at=now + timedelta(days=1), expires_at=now + timedelta(days=2))),
            ('expired', dict(starts_at=now - timedelta(days=2), expires_at=now - timedelta(days=1))),
        )
        for name, changes in branches:
            with self.subTest(branch=name):
                values = dict(customer=self.customer, issuer=self.issuer, percentage_bps=1000,
                    fpga_allowed=True, asic_allowed=True)
                values.update(changes)
                _, code = issue_discount(**values)
                response = self.post(discount_code=code)
                self.assertEqual(response.status_code, 422, name)
                self.assertContains(response, 'Discount unavailable', status_code=422)
                self.assertFalse(DiscountReservation.objects.exists(), name)
                self.assertEqual(SupportRequest.objects.count(), 0, name)
        # Stacked codes: two valid codes concatenated are still one rejected submission.
        _, second_code = issue_discount(customer=self.customer, issuer=self.issuer,
            percentage_bps=1000, fpga_allowed=True, asic_allowed=True)
        response = self.post(discount_code=self.code + ',' + second_code)
        self.assertEqual(response.status_code, 422)
        self.assertFalse(DiscountReservation.objects.exists())
        self.assertEqual(SupportRequest.objects.count(), 0)
        # Revoked branch: existing DiscountCode becomes revoked and the apply fails
        # without erasing the DiscountCode row or affecting the invitation.
        DiscountCode.objects.filter(pk=self.discount.pk).update(revoked_at=now)
        self.assertEqual(self.post().status_code, 422)
        self.assertTrue(DiscountCode.objects.filter(pk=self.discount.pk).exists())
        self.assertEqual(Invitation.objects.get(pk=self.invitation.pk).token_digest,
                         before_invite_digest, 'rejection must not touch the invitation row')
        self.assertFalse(DiscountReservation.objects.exists())
        self.assertEqual(SupportRequest.objects.count(), 0)
