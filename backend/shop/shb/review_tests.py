"""Assigned recent-MFA ASIC review and safe unused-concession closure."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import json
from pathlib import Path
import tempfile
from threading import Barrier
from unittest.mock import patch
from urllib.parse import urlencode
import uuid

from django.db import DatabaseError, connections, transaction
from django.conf import settings
from django.test import Client, TransactionTestCase, override_settings
from django.utils import timezone

from shop.access import staff_tests
from shop.access.models import StaffCredential, StaffQuotationGrant
from shop.catalog.models import QuotationReview
from .discount_tests import DiscountTests


@override_settings(SHB_SYNTHETIC_FIXTURE=True)
class RequestReviewTests(TransactionTestCase):
    client_class = DiscountTests.client_class
    post = staff_tests.StaffTests.post
    challenge = staff_tests.StaffTests.challenge
    authenticated = staff_tests.StaffTests.authenticated
    customer_submit = DiscountTests.post

    def setUp(self):
        DiscountTests.setUp(self)
        self.assertEqual(self.customer_submit().status_code, 200)
        from .models import SupportRequest
        self.row = SupportRequest.objects.select_related('quotation').get()
        self.user = self.issuer
        self.password = 'synthetic-review-password'
        self.user.set_password(self.password); self.user.save(update_fields=['password'])
        self.credential = StaffCredential.objects.create(user=self.user)
        self.directory = tempfile.TemporaryDirectory(); self.addCleanup(self.directory.cleanup)
        self.customer_settings = {key: getattr(settings, key, None) for key in staff_tests.STAFF_SETTINGS}
        staff_settings = dict(staff_tests.STAFF_SETTINGS, LOCAL_STAFF_CAPTURE_ROOT=self.directory.name)
        self.staff_settings = override_settings(**staff_settings)
        self.staff_settings.enable(); self.addCleanup(self.staff_settings.disable)
        self.browser = Client(enforce_csrf_checks=True, HTTP_HOST='staff.localhost')
        self.authenticated()
        self.grant = StaffQuotationGrant.objects.create(user=self.user,
            quotation=self.row.quotation, business_scope_version=self.row.revision)
        self.detail = '/staff/quotation-requests/' + str(self.row.quotation_id) + '/'
        self.route = 'quotation-requests/' + str(self.row.quotation_id) + '/shb-reviews/'
        self.value = {'request_id': str(uuid.uuid4()), 'expected_review_version': 0,
            'scope_sha256': self.row.sha256, 'decision': 'needs_information',
            'message': 'Which SLL project objective should the support address?'}

    def submit(self, **changes):
        return self.post(self.route, dict(self.value, **changes))

    def test_assigned_private_scope_recent_mfa_and_no_get_effects(self):
        from .models import SupportRequestReview
        response = self.browser.get(self.detail)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['state'], 'submitted')
        self.assertEqual(response.json()['details']['company_name'], 'Synthetic Company Limited')
        self.assertEqual(response['Cache-Control'], 'no-store')
        self.assertNotIn(self.code, response.content.decode())
        self.assertFalse(SupportRequestReview.objects.exists())
        self.grant.business_scope_version = 0; self.grant.save(update_fields=['business_scope_version'])
        self.assertEqual(self.browser.get(self.detail).status_code, 403)
        self.assertEqual(self.submit().status_code, 403)
        self.grant.delete()
        self.assertEqual(self.browser.get(self.detail).status_code, 404)

    def test_clarification_preserves_discount_after_claim_and_invitation_expiry(self):
        from .models import DiscountReservation, SupportRequest, SupportRequestReview
        with patch('shop.shb.invitations.now', return_value=self.invitation.expires_at), \
                patch('shop.shb.discounts.now', return_value=self.discount.expires_at + timedelta(days=1)):
            response = self.submit()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(SupportRequest.objects.get().state, 'needs_information')
        self.assertEqual(DiscountReservation.objects.get().state, 'reserved')
        self.assertEqual(SupportRequestReview.objects.count(), 1)
        review = QuotationReview.objects.get()
        self.assertEqual(review.reviewer_id, self.user.pk)
        self.assertEqual(review.reviewer_generation, self.credential.generation)
        self.assertEqual(review.snapshot_digest, self.row.sha256)
        self.assertFalse(response.json()['checkout_enabled'])

    def test_technical_readiness_is_not_offer_approval_payment_or_release(self):
        from .models import DiscountReservation, SupportRequest
        from shop.payments.models import SyntheticPaymentAttempt
        self.assertEqual(self.submit(decision='ready_for_commercial_review').status_code, 201)
        self.assertEqual(SupportRequest.objects.get().state, 'under_review')
        self.assertEqual(DiscountReservation.objects.get().state, 'reserved')
        self.assertFalse(SyntheticPaymentAttempt.objects.exists())
        self.assertEqual(self.submit(decision='approved').status_code, 400)

    def test_decline_releases_once_without_extending_claim_or_reopening_request(self):
        from .models import DiscountCode, DiscountReservation, SupportRequestReview
        response = self.submit(decision='declined', message='The requested scope cannot be supported.')
        self.assertEqual(response.status_code, 201)
        hold = DiscountReservation.objects.get()
        self.assertEqual(hold.state, 'released')
        self.assertEqual(hold.release_review_id, SupportRequestReview.objects.get().pk)
        self.assertEqual(DiscountCode.objects.get().expires_at, self.discount.expires_at)
        self.assertEqual(self.submit(decision='declined', message='The requested scope cannot be supported.').status_code, 200)
        self.assertEqual(self.submit(decision='declined', message='Changed reason').status_code, 409)
        self.assertEqual(self.submit(request_id=str(uuid.uuid4()), expected_review_version=1).status_code, 409)
        with override_settings(**self.customer_settings):
            self.assertEqual(self.customer_submit().status_code, 200)
        self.assertEqual(DiscountReservation.objects.filter(state='reserved').count(), 1)
        self.assertEqual(DiscountReservation.objects.filter(state='released').count(), 1)

    def test_closure_after_original_expiry_never_reactivates_new_claims(self):
        from .models import DiscountReservation
        with patch('shop.shb.discounts.now', return_value=self.discount.expires_at):
            self.assertEqual(self.submit(decision='declined').status_code, 201)
            with override_settings(**self.customer_settings):
                self.assertEqual(self.customer_submit().status_code, 422)
        self.assertEqual(DiscountReservation.objects.get().state, 'released')

    def test_customer_retry_reports_closed_request_and_actual_released_reservation(self):
        self.assertEqual(self.submit(decision='declined').status_code, 201)
        with override_settings(**self.customer_settings):
            response = self.customer_submit(request_id=str(self.row.request_id))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Status: Declined')
        self.assertContains(response, 'discount reservation was released')
        self.assertNotContains(response, 'Discount reserved for this request')

    def test_bad_scope_stale_version_and_malformed_messages_do_not_mutate(self):
        from .models import SupportRequestReview, DiscountReservation
        for changes, status in [({'scope_sha256': '0' * 64}, 409),
                ({'expected_review_version': 1}, 409), ({'expected_review_version': True}, 400),
                ({'message': ''}, 400), ({'message': 'x' * 513}, 400),
                ({'customer_id': self.customer.pk}, 400)]:
            with self.subTest(changes=tuple(changes)):
                self.assertEqual(self.submit(**changes).status_code, status)
        self.assertFalse(SupportRequestReview.objects.exists())
        self.assertEqual(DiscountReservation.objects.get().state, 'reserved')

    def test_no_javascript_form_csrf_and_fresh_mfa_on_read_and_write(self):
        page = self.browser.get(self.detail, HTTP_ACCEPT='text/html')
        self.assertContains(page, 'Review ASIC support request')
        self.assertContains(page, 'name="scope_sha256"')
        token = self.browser.cookies['shop_staff_csrftoken'].value
        fields = dict(self.value, csrfmiddlewaretoken=token)
        self.assertEqual(self.browser.post('/staff/' + self.route,
            data=urlencode(fields), content_type='application/x-www-form-urlencoded').status_code, 303)
        session = self.browser.session; marker = session['shop_staff_mfa']
        marker['verified_at'] -= 301; session['shop_staff_mfa'] = marker; session.save()
        self.assertEqual(self.browser.get(self.detail).status_code, 403)
        self.assertEqual(self.submit().status_code, 403)

    def test_concurrent_decisions_have_one_winner(self):
        from .models import SupportRequestReview
        cookies = self.browser.cookies.copy(); barrier = Barrier(2)
        token = self.browser.get('/staff/session/').json()['csrf_token']
        def decide(decision):
            try:
                client = Client(enforce_csrf_checks=True, HTTP_HOST='staff.localhost')
                client.cookies = cookies.copy(); barrier.wait(timeout=5)
                value = dict(self.value, request_id=str(uuid.uuid4()), decision=decision)
                return client.post('/staff/' + self.route, data=json.dumps(value),
                    content_type='application/json', HTTP_X_CSRFTOKEN=token).status_code
            finally:
                connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(decide, ('declined', 'needs_information')))
        self.assertEqual(sorted(results), [201, 409])
        self.assertEqual(SupportRequestReview.objects.count(), 1)

    def test_review_and_release_provenance_cannot_be_rewritten_in_sql(self):
        from .models import DiscountReservation, SupportRequestReview
        self.assertEqual(self.submit(decision='declined').status_code, 201)
        event = SupportRequestReview.objects.get(); hold = DiscountReservation.objects.get()
        for model, identity, changes in [(SupportRequestReview, event.pk, {'message': 'Changed'}),
                (QuotationReview, event.review_id, {'decision': 'needs_information'}),
                (DiscountReservation, hold.pk, {'state': 'reserved', 'release_review_id': None})]:
            with self.subTest(model=model.__name__), self.assertRaises(DatabaseError), transaction.atomic():
                model.objects.filter(pk=identity).update(**changes)

    def test_credential_revocation_prevents_decisions(self):
        from .models import SupportRequestReview
        StaffCredential.objects.filter(pk=self.credential.pk).update(enabled=False)
        self.assertEqual(self.submit().status_code, 403)
        self.assertFalse(SupportRequestReview.objects.exists())

    def test_existing_operator_command_grants_and_revokes_exact_private_shb_scope(self):
        from io import StringIO
        from django.core.management import call_command, CommandError
        self.grant.business_scope_version = 0; self.grant.save(update_fields=['business_scope_version'])
        options = {'username': self.user.username, 'quotation': str(self.row.quotation_id), 'stdout': StringIO()}
        with self.assertRaises(CommandError):
            call_command('local_staff', 'grant-business', business_scope=2, **options)
        call_command('local_staff', 'grant-business', business_scope=1, **options)
        self.assertEqual(self.browser.get(self.detail).status_code, 200)
        call_command('local_staff', 'revoke-business', **options)
        self.assertEqual(self.browser.get(self.detail).status_code, 403)
        with override_settings(SHB_SYNTHETIC_FIXTURE=False), self.assertRaises(CommandError):
            call_command('local_staff', 'grant-business', business_scope=1, **options)

    def test_recovery_quarantine_denies_existing_verified_staff_session(self):
        from django.db import connection
        from shop.access.recovery import local_recovery_operation
        from .models import SupportRequestReview
        token = self.browser.get('/staff/session/').json()['csrf_token']
        local_recovery_operation(action='quarantine', request_id=uuid.uuid4(),
            expected_database=connection.settings_dict['NAME'])
        response = self.browser.post('/staff/' + self.route, data=json.dumps(self.value),
            content_type='application/json', HTTP_X_CSRFTOKEN=token)
        self.assertIn(response.status_code, (403, 503))
        self.assertFalse(SupportRequestReview.objects.exists())

    def test_offer_or_payment_states_cannot_use_pre_offer_release(self):
        from .models import DiscountReservation, SupportRequest, SupportRequestReview
        for state in ('approved', 'offer_issued', 'paid'):
            SupportRequest.objects.filter(pk=self.row.pk).update(state=state)
            self.assertEqual(self.submit(decision='declined').status_code, 409)
        self.assertFalse(SupportRequestReview.objects.exists())
        self.assertEqual(DiscountReservation.objects.get().state, 'reserved')

    def test_closing_request_without_code_cannot_release_another_requests_code(self):
        from .models import DiscountReservation, SupportRequest, SupportRequestReview
        with override_settings(**self.customer_settings):
            self.assertEqual(self.customer_submit(discount_code='').status_code, 200)
        second = SupportRequest.objects.exclude(pk=self.row.pk).get()
        StaffQuotationGrant.objects.create(user=self.user, quotation=second.quotation,
            business_scope_version=second.revision)
        value = dict(self.value, scope_sha256=second.sha256, decision='declined')
        route = 'quotation-requests/' + str(second.quotation_id) + '/shb-reviews/'
        self.assertEqual(self.post(route, value).status_code, 201)
        hold = DiscountReservation.objects.get()
        self.assertEqual(hold.state, 'reserved')
        with self.assertRaisesMessage(DatabaseError, 'matching pre-offer decline'), transaction.atomic():
            DiscountReservation.objects.filter(pk=hold.pk).update(state='released',
                release_review=SupportRequestReview.objects.get())
