"""Real PostgreSQL complete-cart checkout boundaries, retries and scope races."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Barrier
from unittest.mock import patch
import json
import uuid
from urllib.parse import urlencode
from django.contrib.auth import get_user_model
from django.db import connections, IntegrityError, transaction
from django.test import Client, TransactionTestCase, override_settings
from shop.adapters.evidence_archive import PreparedArchive, ArchiveError
from shop.payments.models import SyntheticBankOperation
from shop.payments.purchase_flow_tests import configuration
from . import checkout, business_rules
from .cart_views import store_cart
from .document_preview import DEFINITION
from .models import BusinessDraft, BusinessDraftSnapshot, SyntheticCheckout, SyntheticCheckoutKey
from .rules import CATALOG
from .tests import verified_login

API = '/api/v1/checkout-rehearsal/'
PAGE = '/purchase/checkout-rehearsal/'


class CheckoutTests(TransactionTestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(username='checkout-owner')
        self.other = get_user_model().objects.create_user(username='checkout-other')
        verified_login(self.client, self.owner)
        self.ip = {'id': str(uuid.uuid4()), 'kind': 'ip', 'product_id': CATALOG['product_id'],
                   'quantity': 1, 'configuration': configuration(packages=0)}
        self.support = {'id': str(uuid.uuid4()), 'kind': 'support', 'product_id': CATALOG['support_product_id'], 'quantity': 2}
        self.lines = [self.ip, self.support]
        self.save_cart(self.lines)
        draft = BusinessDraft.objects.create(owner=self.owner, version=1)
        details = business_rules.empty_details() | {'legal_business_name': 'SYNTHETIC_BUSINESS_CANARY',
            'registered_address': 'Synthetic address', 'billing_same_as_registered': True,
            'purchasing_name': 'Synthetic buyer', 'business_email': 'checkout@synthetic.invalid',
            'technical_same_as_purchasing': True}
        resolved = business_rules.resolve_details(details)
        self.business = BusinessDraftSnapshot.objects.create(draft=draft, version=1, request_id=uuid.uuid4(),
            schema_version=business_rules.SCHEMA_VERSION, source_sha256=business_rules.SOURCE_SHA256,
            submission_digest=business_rules.submission_digest(details), details=resolved,
            evaluation=business_rules.evaluate_details(resolved))

    def save_cart(self, lines):
        from .models import DraftCart
        cart = DraftCart.objects.filter(owner=self.owner).first()
        result, status = store_cart(self.owner, {'request_id': str(uuid.uuid4()), 'expected_version': cart.version if cart else 0,
            'catalog_revision': CATALOG['revision'], 'lines': lines})
        self.assertEqual(status, 201, result)
        return result

    def preview(self):
        response = self.client.get(API)
        self.assertEqual(response.status_code, 200, response.content)
        return response.json()

    def submit(self, value=None):
        value = value or {'request_id': str(uuid.uuid4()), 'sha256': self.preview()['sha256']}
        return self.client.post(API, data=json.dumps(value), content_type='application/json')

    def test_complete_mixed_cart_preserves_business_documents_and_staged_obligation(self):
        value = self.preview();snapshot = value['snapshot']
        self.assertEqual(snapshot['cart']['lines'], self.lines)
        self.assertEqual(snapshot['business']['details'], self.business.details)
        self.assertEqual(snapshot['documents'], DEFINITION)
        self.assertEqual(snapshot['total_minor'], 12345 + 2 * 2345)
        self.assertEqual(sum(line['total_minor'] for line in snapshot['priced_lines']), snapshot['total_minor'])
        self.assertEqual(snapshot['allocated_purchased_packages'], 2)
        self.assertEqual(snapshot['unallocated_purchased_packages'], 0)
        self.assertTrue(snapshot['priced_lines'][0]['offer']['later_reference_design'])
        response = self.submit();self.assertEqual(response.status_code, 201)
        self.assertNotIn('SYNTHETIC_BUSINESS_CANARY', response.content.decode())
        self.assertFalse(response.json()['acceptance_enabled'])
        self.assertFalse(response.json()['effects_authorized'])
        self.assertEqual(SyntheticBankOperation.objects.count(), 0)

    def test_support_only_has_no_platform_or_ip_declarations_required(self):
        self.save_cart([self.support])
        value = self.preview()['snapshot']
        self.assertEqual(value['total_minor'], 4690)
        self.assertEqual(value['allocated_purchased_packages'], 0)
        self.assertNotIn('ip_licence', value['required_document_ids'])
        self.assertNotIn('configuration', value['priced_lines'][0])
        self.assertEqual(self.submit().status_code, 201)

    def test_ready_kit_can_buy_zero_support(self):
        line = deepcopy(self.ip);line['configuration'] = configuration('listed-kit', 0)
        from .purchase_policy import FIXTURE_KITS
        # Deliberate fixture catalog only; the retained public catalog has no approved kits.
        with patch.dict(CATALOG['purchase_flow'], {'ready_kits': list(FIXTURE_KITS)}):
            self.save_cart([line])
            value = self.preview()['snapshot']
        self.assertEqual(value['support_packages'], 0)
        self.assertFalse(value['priced_lines'][0]['offer']['later_reference_design'])
        self.assertEqual(value['total_minor'], 12345)

    def test_all_lines_hold_for_missing_support_and_uncovered_licence(self):
        self.save_cart([self.ip])
        self.assertEqual(self.client.get(API).json()['error'], 'required_support_minimum')
        other = deepcopy(self.ip);other['id'] = str(uuid.uuid4());other['configuration']['families'] = ['altera-cyclone-v']
        # A valid draft scope can still be outside a specific approved fixture offer.
        self.save_cart([self.ip, other, self.support])
        self.assertEqual(self.client.get(API).json()['error'], 'line_requires_review')
        self.assertEqual(SyntheticCheckout.objects.count(), 0)

    def test_two_ip_lines_cannot_double_allocate_two_packages(self):
        other = deepcopy(self.ip);other['id'] = str(uuid.uuid4())
        self.save_cart([self.ip, other, self.support])
        self.assertEqual(self.client.get(API).json()['error'], 'required_support_minimum')
        self.support['quantity'] = 4;self.save_cart([self.ip, other, self.support])
        value = self.preview()['snapshot']
        self.assertEqual(value['allocated_purchased_packages'], 4)
        self.assertEqual(value['total_minor'], 2 * 12345 + 4 * 2345)

    def test_minimum_comes_from_seller_policy_rather_than_board_category(self):
        from dataclasses import replace
        from .purchase_policy import FIXTURE_OFFERS, quote
        changed = tuple(replace(row, minimum_packages=3) if row.id == 'synthetic-development' else row for row in FIXTURE_OFFERS)
        # Patch both consumers of the immutable fixture registry, never the public catalog.
        with patch.object(checkout, 'FIXTURE_OFFERS', changed), patch.object(checkout, 'quote', side_effect=lambda c, offer: quote(c, offer, offers=changed)):
            self.assertEqual(self.client.get(API).json()['error'], 'required_support_minimum')
            self.support['quantity'] = 3;self.save_cart([self.ip, self.support])
            value = self.preview()['snapshot']
            self.assertEqual(value['allocated_purchased_packages'], 3)
            self.assertEqual(value['priced_lines'][0]['offer']['minimum_packages'], 3)

    def test_cart_or_business_edit_rejects_stale_submission(self):
        value = {'request_id': str(uuid.uuid4()), 'sha256': self.preview()['sha256']}
        self.support['quantity'] = 3;self.save_cart([self.ip, self.support])
        self.assertEqual(self.submit(value).json()['error'], 'checkout_changed')
        value['sha256'] = self.preview()['sha256']
        self.business.details['purchase_order'] = 'new private revision';self.business.save()
        self.assertEqual(self.submit(value).json()['error'], 'checkout_changed')
        self.assertEqual(SyntheticCheckout.objects.count(), 0)

    def test_committed_retry_survives_cart_edit_and_alias_key_cannot_be_reused(self):
        first = {'request_id': str(uuid.uuid4()), 'sha256': self.preview()['sha256']}
        row = self.submit(first).json()
        alias = first | {'request_id': str(uuid.uuid4())}
        self.assertEqual(self.submit(alias).json()['id'], row['id'])
        self.support['quantity'] = 3;self.save_cart([self.ip, self.support])
        self.assertEqual(self.submit(alias).json()['id'], row['id'])
        alias['sha256'] = self.preview()['sha256']
        self.assertEqual(self.submit(alias).json()['error'], 'request_conflict')
        self.assertEqual(SyntheticCheckout.objects.count(), 1)
        self.assertEqual(SyntheticCheckoutKey.objects.count(), 2)

    def test_no_javascript_and_api_share_exact_capture_and_guard_tampering(self):
        page = self.client.get(PAGE)
        self.assertEqual(page.status_code, 200)
        self.assertIn('Record synthetic checkout', page.content.decode())
        value = {'request_id': str(uuid.uuid4()), 'sha256': self.preview()['sha256']}
        response = self.client.post(PAGE, data=urlencode(value), content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.submit(value).status_code, 200)
        self.assertEqual(SyntheticCheckout.objects.count(), 1)
        self.assertEqual(self.submit(value | {'total_minor': 1}).status_code, 400)
        self.assertEqual(self.client.post(PAGE, data=urlencode(value | {'support_policy': 'optional'}), content_type='application/x-www-form-urlencoded').status_code, 400)
        self.assertEqual(self.client.post(API, data='{"request_id":1,"request_id":2}', content_type='application/json').status_code, 400)

    def test_csrf_access_privacy_and_live_mode(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.get(API).status_code, 401)
        verified_login(client, self.owner)
        self.assertEqual(client.post(API, data='{}', content_type='application/json').status_code, 403)
        response = client.get(PAGE)
        self.assertEqual(response['Cache-Control'], 'no-store')
        self.assertEqual(response['Referrer-Policy'], 'no-referrer')
        self.assertIn("default-src 'none'", response['Content-Security-Policy'])
        csrf = client.cookies['csrftoken'].value
        value = {'request_id': str(uuid.uuid4()), 'sha256': self.preview()['sha256']}
        self.assertEqual(client.post(API, data=json.dumps(value), content_type='application/json', HTTP_X_CSRFTOKEN=csrf).status_code, 201)
        verified_login(client, self.other)
        self.assertEqual(client.post(API, data=json.dumps(value), content_type='application/json', HTTP_X_CSRFTOKEN=client.cookies['csrftoken'].value).status_code, 422)
        self.assertNotIn('SYNTHETIC_BUSINESS_CANARY', client.get(PAGE).content.decode())
        with override_settings(SHOP_ENV='production'):
            self.assertEqual(self.client.get(API).status_code, 404)
            self.assertEqual(self.client.get(PAGE).status_code, 404)
        self.assertEqual(self.client.get(API + '?business_email=PRIVATE').status_code, 400)

    def test_document_revision_change_or_invalid_business_holds(self):
        with patch.dict(checkout.DEFINITION, {'revision': '0' * 64}):
            self.assertEqual(self.client.get(API).json()['error'], 'document_source_requires_review')
        self.business.details['licensed_entity'] = 'Different entity'
        self.business.evaluation = business_rules.evaluate_details(self.business.details);self.business.save()
        self.assertEqual(self.client.get(API).json()['error'], 'licensed_entity_requires_review')

    def test_concurrent_capture_has_one_snapshot_and_retries(self):
        expected = self.preview()['sha256'];barrier = Barrier(2)
        def run(_):
            try:
                barrier.wait(timeout=10)
                return checkout.capture(self.owner, uuid.uuid4(), expected)[0].pk
            finally: connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:
            result = list(pool.map(run, range(2)))
        self.assertEqual(result[0], result[1])
        self.assertEqual(SyntheticCheckout.objects.count(), 1)
        self.assertEqual(SyntheticCheckoutKey.objects.count(), 2)

    def test_archive_exact_snapshot_recovery_failure_and_owner_revocation(self):
        row, _ = checkout.capture(self.owner, uuid.uuid4(), self.preview()['sha256'])
        with TemporaryDirectory() as directory, PreparedArchive(Path(directory)) as archive:
            with patch.object(archive, 'publish', side_effect=ArchiveError('unavailable')):
                with self.assertRaises(ArchiveError): checkout.archive_capture(row.pk, self.owner, archive)
            row.refresh_from_db();self.assertEqual(row.archive_receipt, {})
            retained = checkout.archive_capture(row.pk, self.owner, archive)
            self.assertTrue(retained.archive_receipt)
            self.assertEqual(retained.snapshot, row.snapshot)
            with self.assertRaisesRegex(checkout.CheckoutError, 'not_found'):
                verified_login(self.client, self.other)
                checkout.archive_capture(row.pk, self.other, archive)
        self.owner.is_active = False;self.owner.save()
        from shop.payments.bank_contract import BankError
        with self.assertRaises(BankError): checkout.capture(self.owner, row.request_id, row.sha256)
        self.assertEqual(SyntheticBankOperation.objects.count(), 0)

    def test_database_cannot_promote_synthetic_checkout_to_actual_effects(self):
        row, _ = checkout.capture(self.owner, uuid.uuid4(), self.preview()['sha256'])
        with self.assertRaises(IntegrityError), transaction.atomic():
            SyntheticCheckout.objects.filter(pk=row.pk).update(effects_authorized=True)
