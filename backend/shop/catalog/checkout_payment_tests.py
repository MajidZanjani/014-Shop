"""Real PostgreSQL synthetic acceptance/payment and production-style UI boundaries."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Barrier
from unittest.mock import patch
from urllib.parse import urlencode
import json
import uuid
from django.contrib.auth import get_user_model
from django.db import connections, transaction, IntegrityError
from django.test import Client, TransactionTestCase, override_settings
from django.utils import timezone
from shop.adapters.evidence_archive import PreparedArchive, ArchiveError
from shop.payments import synthetic_bank
from shop.payments.models import SyntheticBankOperation, SyntheticPaymentAttempt
from . import checkout, checkout_payment as service, checkout_tests as fixture
from .models import SyntheticCheckout, SyntheticCheckoutAcceptance
from .tests import verified_login


class CheckoutPaymentTests(TransactionTestCase):
    save_cart = fixture.CheckoutTests.save_cart
    preview = fixture.CheckoutTests.preview

    def setUp(self):
        fixture.CheckoutTests.setUp(self)
        self.directory = TemporaryDirectory();self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.settings_override = override_settings(LOCAL_CHECKOUT_ARCHIVE_ROOT=str(self.root))
        self.settings_override.enable();self.addCleanup(self.settings_override.disable)
        self.archive = PreparedArchive(self.root);self.addCleanup(self.archive.__exit__, None, None, None)
        self.saved, _ = checkout.capture(self.owner, uuid.uuid4(), self.preview()['sha256'])
        self.api = '/api/v1/checkout-rehearsal/' + str(self.saved.pk) + '/payment/'
        self.page = '/purchase/checkout-rehearsal/' + str(self.saved.pk) + '/payment/'

    def accept(self):
        _, expected, _ = service.review(self.owner, self.saved.pk)
        return service.accept(self.owner, self.saved.pk, expected, True, self.archive)

    def api_post(self, value):
        return self.client.post(self.api, data=json.dumps(value), content_type='application/json')

    def test_explicit_confirmation_archives_exact_scope_once_and_pays_total_once(self):
        row = self.accept();first_time = row.simulated_accepted_at
        self.assertIsNotNone(first_time);service.retained(row, self.archive)
        self.assertEqual(row.payload['review']['checkout'], self.saved.snapshot)
        self.assertTrue(all(d['version'] == service.PROFILE for d in row.payload['review']['fixture_documents']))
        self.assertEqual(self.accept().pk, row.pk);self.assertEqual(self.accept().simulated_accepted_at, first_time)
        original = synthetic_bank.start
        def start(request, **kwargs):
            current = SyntheticCheckoutAcceptance.objects.select_related('checkout').get(pk=row.pk)
            service.retained(current, self.archive)
            from shop.payments import attempts
            attempts.retained(current.attempt, self.archive)
            self.assertFalse(connections['default'].in_atomic_block)
            return original(request, **kwargs)
        with patch.object(synthetic_bank, 'start', side_effect=start):
            result = service.pay(self.owner, self.saved.pk, self.archive)
        self.assertEqual(result.attempt.provider_status, 'captured')
        self.assertEqual(result.attempt.amount_minor, self.saved.snapshot['total_minor'])
        self.assertEqual(service.pay(self.owner, self.saved.pk, self.archive).attempt_id, result.attempt_id)
        self.assertEqual(SyntheticBankOperation.objects.count(), 1)
        self.assertEqual(SyntheticPaymentAttempt.objects.count(), 1)
        self.assertFalse(result.financial_confirmation);self.assertFalse(result.effects_authorized)

    def test_no_confirmation_or_wrong_review_cannot_accept_and_no_acceptance_cannot_pay(self):
        value, expected, _ = service.review(self.owner, self.saved.pk)
        for confirmed in (False, 'true', 1):
            with self.assertRaisesRegex(checkout.CheckoutError, 'synthetic_confirmation_required'):
                service.accept(self.owner, self.saved.pk, expected, confirmed, self.archive)
        with self.assertRaisesRegex(checkout.CheckoutError, 'review_changed'):
            service.accept(self.owner, self.saved.pk, '0' * 64, True, self.archive)
        with self.assertRaisesRegex(checkout.CheckoutError, 'synthetic_acceptance_required'):
            service.pay(self.owner, self.saved.pk, self.archive)
        self.assertEqual(SyntheticCheckoutAcceptance.objects.count(), 0)
        self.assertEqual(SyntheticBankOperation.objects.count(), 0)

    def test_archive_failure_leaves_prepared_confirmation_unaccepted_and_no_bank_call(self):
        with patch.object(self.archive, 'publish', side_effect=ArchiveError('unavailable')):
            with self.assertRaises(ArchiveError): self.accept()
        row = SyntheticCheckoutAcceptance.objects.get()
        self.assertIsNone(row.simulated_accepted_at);self.assertIsNone(row.attempt_id)
        self.assertEqual(SyntheticBankOperation.objects.count(), 0)
        self.assertIsNotNone(self.accept().simulated_accepted_at)

    def test_lost_bank_response_is_lookup_only_even_after_repeated_payment_click(self):
        self.accept()
        with self.assertRaises(TimeoutError):service.pay(self.owner, self.saved.pk, self.archive, fault='after_commit')
        with patch.object(synthetic_bank, 'start', side_effect=AssertionError('blind resend')):
            self.assertEqual(service.pay(self.owner, self.saved.pk, self.archive).attempt.state, 'uncertain')
            reconciled = service.reconcile(self.owner, self.saved.pk, self.archive)
        self.assertEqual(reconciled.attempt.provider_status, 'captured')
        self.assertEqual(SyntheticBankOperation.objects.count(), 1)
        self.assertEqual(SyntheticPaymentAttempt.objects.count(), 1)

    def test_absent_provider_operation_stays_uncertain_and_cannot_restart(self):
        self.accept()
        with self.assertRaises(TimeoutError):service.pay(self.owner, self.saved.pk, self.archive, fault='before_commit')
        self.assertEqual(service.reconcile(self.owner, self.saved.pk, self.archive).attempt.state, 'uncertain')
        with patch.object(synthetic_bank, 'start', side_effect=AssertionError('blind resend')):
            self.assertEqual(service.pay(self.owner, self.saved.pk, self.archive).attempt.state, 'uncertain')
        self.assertEqual(SyntheticBankOperation.objects.count(), 0)

    def test_distinct_offer_order_and_bank_deadlines_and_expired_session(self):
        self.saved.created_at = timezone.now() - timedelta(minutes=31);self.saved.save()
        with self.assertRaisesRegex(checkout.CheckoutError, 'synthetic_offer_expired'):self.accept()
        SyntheticCheckoutAcceptance.objects.all().delete()
        self.saved.created_at = timezone.now();self.saved.save()
        row = self.accept();review = row.payload['review']
        self.assertNotEqual(review['offer_expires_at'], review['order_payment_expires_at'])
        # An accepted record remains attributable; expired bank session never authorizes a start.
        SyntheticCheckoutAcceptance.objects.filter(pk=row.pk).update(simulated_accepted_at=timezone.now()-timedelta(minutes=11))
        with patch.object(synthetic_bank, 'start', side_effect=AssertionError('expired dispatch')):
            paid = service.pay(self.owner, self.saved.pk, self.archive)
        self.assertEqual(paid.attempt.state, 'expired')
        self.assertEqual(SyntheticBankOperation.objects.count(), 0)

    def test_frozen_cart_survives_later_cart_edits_and_owner_is_still_required(self):
        row = self.accept();original = row.payload
        self.support['quantity'] = 3;self.save_cart([self.ip, self.support])
        self.assertEqual(service.pay(self.owner, self.saved.pk, self.archive).payload, original)
        verified_login(self.client, self.other)
        with self.assertRaisesRegex(checkout.CheckoutError, 'not_found'):
            service.review(self.other, self.saved.pk)
        self.owner.is_active = False;self.owner.save()
        from shop.payments.bank_contract import BankError
        with self.assertRaises(BankError):service.pay(self.owner, self.saved.pk, self.archive)

    def test_api_and_no_javascript_share_acceptance_and_reject_extra_commercial_fields(self):
        preview = self.client.get(self.api).json()
        form = {'action':'accept', 'sha256':preview['sha256'], 'confirmed':'on'}
        page = self.client.post(self.page, data=urlencode(form), content_type='application/x-www-form-urlencoded')
        self.assertEqual(page.status_code, 200, page.content)
        self.assertContains(page, 'Simulate payment once')
        retry = self.api_post({'action':'accept', 'sha256':preview['sha256'], 'confirmed':True})
        self.assertTrue(retry.json()['synthetic_accepted'])
        self.assertEqual(SyntheticCheckoutAcceptance.objects.count(), 1)
        self.assertEqual(self.api_post({'action':'pay', 'amount_minor':1}).status_code, 400)
        paid = self.api_post({'action':'pay'})
        self.assertTrue(paid.json()['simulated_paid']);self.assertFalse(paid.json()['financial_confirmation'])
        page = self.client.get(self.page)
        self.assertContains(page, 'Simulated payment captured')
        self.assertNotContains(page, 'name="action" value="pay"')

    def test_scope_csrf_live_mode_and_server_archive_configuration(self):
        client = Client(enforce_csrf_checks=True);verified_login(client, self.owner)
        self.assertEqual(client.post(self.api, data='{}', content_type='application/json').status_code, 403)
        verified_login(self.client, self.other)
        self.assertEqual(self.client.get(self.api).status_code, 404)
        self.assertEqual(self.api_post({'action':'pay'}).status_code, 404)
        verified_login(self.client, self.owner)
        with override_settings(SHOP_ENV='production'):
            self.assertEqual(self.client.get(self.page).status_code, 404)
            self.assertEqual(self.api_post({'action':'pay'}).status_code, 404)
        with override_settings(LOCAL_CHECKOUT_ARCHIVE_ROOT=None):
            self.assertEqual(self.api_post({'action':'pay'}).status_code, 503)
        self.assertEqual(self.client.get(self.api+'?amount_minor=1').status_code, 400)

    def test_tampered_confirmation_or_lost_archive_cannot_dispatch(self):
        row = self.accept()
        with patch.object(self.archive, 'recover', side_effect=ArchiveError('lost archive')):
            with self.assertRaises(ArchiveError):service.pay(self.owner, self.saved.pk, self.archive)
        row.payload['review']['checkout']['total_minor'] = 1;row.save()
        with self.assertRaisesRegex(checkout.CheckoutError, 'acceptance_mismatch'):
            service.pay(self.owner, self.saved.pk, self.archive)
        self.assertEqual(SyntheticBankOperation.objects.count(), 0)

    def test_concurrent_confirmations_and_payments_have_one_reference(self):
        _, expected, _ = service.review(self.owner, self.saved.pk)
        second = TemporaryDirectory();self.addCleanup(second.cleanup)
        barrier = Barrier(2)
        def run(directory):
            try:
                with PreparedArchive(Path(directory)) as archive:
                    barrier.wait(timeout=10)
                    row = service.accept(self.owner, self.saved.pk, expected, True, archive)
                    return service.pay(self.owner, self.saved.pk, archive).pk
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(run, [self.directory.name, second.name]))
        self.assertEqual(results[0], results[1])
        self.assertEqual(SyntheticCheckoutAcceptance.objects.count(), 1)
        self.assertEqual(SyntheticPaymentAttempt.objects.count(), 1)
        self.assertEqual(SyntheticBankOperation.objects.count(), 1)

    def test_database_cannot_promote_synthetic_confirmation(self):
        row = self.accept()
        with self.assertRaises(IntegrityError), transaction.atomic():
            SyntheticCheckoutAcceptance.objects.filter(pk=row.pk).update(financial_confirmation=True)

    def test_html_errors_are_actionable_without_changing_api_codes_or_effects(self):
        for code,status,phrase in (
                ('review_changed',409,'review has changed'),
                ('synthetic_confirmation_required',422,'Confirm the synthetic declaration'),
                ('local_archive_unavailable',503,'recovery evidence'),
                ('PRIVATE_SYNTHETIC_UNRECOGNIZED',409,'rehearsal is on hold')):
            with self.subTest(code=code),patch.object(service,'review',side_effect=checkout.CheckoutError(code,status)):
                response=self.client.get(self.page)
                self.assertEqual(response.status_code,status)
                self.assertContains(response,'role="alert"',status_code=status)
                self.assertContains(response,phrase,status_code=status)
                self.assertNotContains(response,code,status_code=status)
                self.assertContains(response,'Reload the retained rehearsal status',status_code=status)
                self.assertNotContains(response,'<form',status_code=status)
                self.assertEqual(self.client.get(self.api).json(),{'error':code})
        query=self.client.get(self.page+'?invalid=synthetic')
        self.assertContains(query,'does not accept query parameters',status_code=400)
        self.assertNotContains(query,'unexpected_query',status_code=400)
        self.assertEqual(self.client.get(self.api+'?invalid=synthetic').json(),{'error':'unexpected_query'})
        bad=self.client.post(self.page,data='action=invalid',content_type='application/x-www-form-urlencoded')
        self.assertContains(bad,'could not be read',status_code=400)
        self.assertNotContains(bad,'invalid_request',status_code=400)
        self.assertEqual(SyntheticCheckoutAcceptance.objects.count(),0)
        self.assertEqual(SyntheticPaymentAttempt.objects.count(),0)
        self.assertEqual(SyntheticBankOperation.objects.count(),0)

    def test_html_uncertain_payment_requires_lookup_without_blind_resend(self):
        self.accept()
        with patch.object(service,'pay',side_effect=TimeoutError):
            response=self.client.post(self.page,data='action=pay',content_type='application/x-www-form-urlencoded')
        self.assertContains(response,'result is uncertain',status_code=409)
        self.assertContains(response,'Use lookup',status_code=409)
        self.assertNotContains(response,'payment_uncertain_use_lookup',status_code=409)
        self.assertNotContains(response,'Simulate payment once',status_code=409)
        self.assertEqual(SyntheticBankOperation.objects.count(),0)
        # A real local response-loss attempt remains lookup-only on the retained page.
        with self.assertRaises(TimeoutError):service.pay(self.owner,self.saved.pk,self.archive,fault='after_commit')
        with patch.object(synthetic_bank,'start',side_effect=AssertionError('blind resend')):
            page=self.client.get(self.page)
            self.assertContains(page,'Look up simulated payment')
            self.assertNotContains(page,'Simulate payment once')
            response=self.client.post(self.page,data='action=reconcile',content_type='application/x-www-form-urlencoded')
            self.assertContains(response,'Simulated payment captured')
        self.assertEqual(SyntheticBankOperation.objects.count(),1)
        self.assertEqual(SyntheticPaymentAttempt.objects.count(),1)

    def test_shared_shop_ui_currency_stylesheet_and_actionable_business_errors(self):
        from .templatetags.shop_money import euro_minor
        self.assertEqual(euro_minor(17035), '€170.35')
        self.assertEqual(euro_minor(True), 'Pending')
        for path in ('/purchase/access/', '/purchase/business/', '/purchase/cart/', '/purchase/checkout-rehearsal/', self.page):
            response = self.client.get(path)
            self.assertContains(response, 'Local shop demo')
            self.assertContains(response, '/purchase/assets/shop.css')
            self.assertIn("style-src 'self'", response['Content-Security-Policy'])
            self.assertNotContains(response, '<script')
        css = self.client.get('/purchase/assets/shop.css')
        self.assertEqual(css.status_code, 200);self.assertIn('text/css', css['Content-Type'])
        self.assertNotIn('SYNTHETIC_BUSINESS_CANARY', css.content.decode())
        self.assertNotIn('Set-Cookie', css)
        self.business.details['purchasing_name'] = '';self.business.details['technical_name'] = ''
        from . import business_rules
        self.business.evaluation = business_rules.evaluate_details(self.business.details);self.business.save()
        response = self.client.get('/purchase/checkout-rehearsal/')
        self.assertContains(response, 'Complete these business fields', status_code=422)
        self.assertContains(response, 'Purchasing contact name', status_code=422)

    def test_checkout_pins_same_commercial_contract_to_buyer_and_documents(self):
        value,_=checkout.current(self.owner)
        pins=[line['commercial_policy'] for line in value['priced_lines']]
        self.assertTrue(pins);self.assertTrue(all(pin['evidence_class']=='local-synthetic' for pin in pins))
        self.assertTrue(all(pin['documents']['general_terms']==value['documents']['revision'] for pin in pins))
        buyer=value['business'];expected=checkout.digest(buyer)
        self.assertTrue(all(pin['buyer_scope_revision']==expected for pin in pins))
        self.assertTrue(all(pin['activation_authorized'] is False for pin in pins))
        self.assertEqual(value['total_minor'],sum(line['total_minor'] for line in value['priced_lines']))

    def test_revision_consumption_failure_holds_existing_checkout(self):
        from .commercial_revisions import CommercialRevisionError
        with patch('shop.catalog.commercial_revisions.consume',side_effect=CommercialRevisionError('untrusted')):
            with self.assertRaises(checkout.CheckoutError):checkout.current(self.owner)
