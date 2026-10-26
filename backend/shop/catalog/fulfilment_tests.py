"""Complete-cart archived grant/delivery semantics on real PostgreSQL."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from threading import Barrier
from unittest.mock import patch
from urllib.parse import urlencode
import uuid
from django.db import connections, transaction, IntegrityError
from django.test import TransactionTestCase, override_settings
from shop.adapters.evidence_archive import ArchiveError
from shop.payments import attempts
from . import fulfilment, checkout_payment as payment, checkout, checkout_payment_tests as fixture
from .models import SyntheticFulfilment, SyntheticLineEntitlement, SyntheticLineDelivery, SyntheticCheckout
from .tests import verified_login


class FulfilmentTests(TransactionTestCase):
    save_cart = fixture.CheckoutPaymentTests.save_cart
    preview = fixture.CheckoutPaymentTests.preview
    api_post = fixture.CheckoutPaymentTests.api_post
    accept = fixture.CheckoutPaymentTests.accept

    def setUp(self):
        fixture.CheckoutPaymentTests.setUp(self)

    def pay(self):
        self.accept();return payment.pay(self.owner, self.saved.pk, self.archive)

    def provision(self):
        return fulfilment.provision(self.owner, self.saved.pk, self.archive)

    def test_grant_once_and_initial_then_reference_keep_one_licence_and_support_balance(self):
        self.pay();first = self.provision();second = self.provision()
        self.assertEqual(first.pk, second.pk);self.assertEqual(first.support_seconds, 72000)
        self.assertIsNone(first.expires_at)
        self.assertEqual(SyntheticLineEntitlement.objects.count(), 1)
        line = uuid.UUID(self.ip['id'])
        with self.assertRaisesRegex(checkout.CheckoutError, 'initial_delivery_required'):
            fulfilment.deliver(self.owner, self.saved.pk, line, 'reference', self.archive)
        initial = fulfilment.deliver(self.owner, self.saved.pk, line, 'initial', self.archive)
        self.assertTrue(initial.payload['simulated_completion'])
        status = fulfilment.status(payment.accepted(self.owner, self.saved.pk))
        self.assertTrue(status['lines'][0]['initial_delivered']);self.assertFalse(status['lines'][0]['reference_delivered'])
        self.assertTrue(status['lines'][0]['later_reference_design'])
        later = fulfilment.deliver(self.owner, self.saved.pk, line, 'reference', self.archive)
        self.assertEqual(fulfilment.deliver(self.owner, self.saved.pk, line, 'reference', self.archive).pk, later.pk)
        self.assertEqual(SyntheticLineDelivery.objects.count(), 2)
        self.assertEqual(SyntheticLineEntitlement.objects.count(), 1)
        self.assertEqual(self.provision().support_seconds, 72000)
        self.assertFalse(fulfilment.status(payment.accepted(self.owner,self.saved.pk))['actual_support_spendable'])

    def test_uncaptured_payment_cannot_create_grant(self):
        with self.assertRaises(checkout.CheckoutError):self.provision()
        self.accept()
        with self.assertRaisesRegex(checkout.CheckoutError, 'synthetic_captured_payment_required'):self.provision()
        with self.assertRaises(TimeoutError):payment.pay(self.owner, self.saved.pk, self.archive, fault='after_commit')
        with self.assertRaisesRegex(checkout.CheckoutError, 'synthetic_captured_payment_required'):self.provision()
        payment.reconcile(self.owner, self.saved.pk, self.archive)
        self.assertEqual(self.provision().support_seconds, 72000)

    def test_archive_failure_prevents_grant_and_completion_flags(self):
        self.pay()
        with patch.object(self.archive, 'publish', side_effect=ArchiveError('unavailable')):
            with self.assertRaises(ArchiveError):self.provision()
        self.assertEqual(SyntheticFulfilment.objects.count(), 0)
        self.provision()
        with patch.object(self.archive, 'publish', side_effect=ArchiveError('unavailable')):
            with self.assertRaises(ArchiveError):fulfilment.deliver(self.owner,self.saved.pk,uuid.UUID(self.ip['id']),'initial',self.archive)
        self.assertEqual(SyntheticLineDelivery.objects.count(), 0)

    def test_two_ip_lines_each_get_one_licence_and_support_not_granted_per_line(self):
        second = deepcopy(self.ip);second['id'] = str(uuid.uuid4());self.support['quantity'] = 4
        self.save_cart([self.ip,second,self.support])
        self.saved,_ = checkout.capture(self.owner,uuid.uuid4(),self.preview()['sha256'])
        self.pay();grant = self.provision()
        self.assertEqual(SyntheticLineEntitlement.objects.filter(fulfilment=grant).count(),2)
        self.assertEqual(grant.support_seconds,144000)
        fulfilment.deliver(self.owner,self.saved.pk,uuid.UUID(self.ip['id']),'initial',self.archive)
        self.assertEqual(SyntheticLineDelivery.objects.count(),1)
        self.assertEqual(self.provision().support_seconds,144000)

    def test_support_only_topup_has_zero_entitlements_and_no_platform(self):
        self.save_cart([self.support]);self.saved,_=checkout.capture(self.owner,uuid.uuid4(),self.preview()['sha256'])
        self.pay();grant=self.provision()
        self.assertEqual(grant.support_seconds,72000);self.assertEqual(grant.payload['entitlements'],[])
        self.assertEqual(SyntheticLineEntitlement.objects.count(),0)
        self.assertNotIn('platform',grant.payload)

    def test_large_valid_package_quantity_uses_bigint_seconds_without_overflow(self):
        self.support['quantity']=1000000
        self.save_cart([self.support]);self.saved,_=checkout.capture(self.owner,uuid.uuid4(),self.preview()['sha256'])
        self.pay();grant=self.provision()
        self.assertEqual(grant.support_seconds,36000000000)
        self.assertEqual(self.provision().support_seconds,36000000000)

    def test_ready_design_has_no_later_reference_obligation(self):
        from shop.payments.purchase_flow_tests import configuration
        from .purchase_policy import FIXTURE_KITS
        from .rules import CATALOG
        ready = deepcopy(self.ip);ready['configuration'] = configuration('listed-kit',0)
        # Only the test installs a synthetic kit; the public catalog stays unapproved.
        with patch.dict(CATALOG['purchase_flow'], {'ready_kits':list(FIXTURE_KITS)}):
            self.save_cart([ready])
            self.saved,_ = checkout.capture(self.owner,uuid.uuid4(),self.preview()['sha256'])
        self.pay();grant=self.provision()
        self.assertEqual(grant.support_seconds,0)
        fulfilment.deliver(self.owner,self.saved.pk,uuid.UUID(self.ip['id']),'initial',self.archive)
        self.assertTrue(fulfilment.status(payment.accepted(self.owner,self.saved.pk))['lines'][0]['reference_delivered'])
        self.assertEqual(SyntheticLineDelivery.objects.count(),1)

    def test_scope_parser_and_frozen_cart_ui_flow(self):
        self.pay()
        response=self.api_post({'action':'provision'});self.assertEqual(response.status_code,200,response.content)
        self.assertEqual(response.json()['fulfilment']['entitlement_count'],1)
        response=self.client.post(self.page,data=urlencode({'action':'deliver_initial','line_id':self.ip['id']}),content_type='application/x-www-form-urlencoded')
        self.assertContains(response,'later reference design remains outstanding')
        self.assertContains(response,'Simulate later reference design')
        self.assertEqual(self.api_post({'action':'deliver_reference','line_id':str(uuid.uuid4())}).status_code,404)
        self.assertEqual(self.api_post({'action':'provision','support_seconds':1}).status_code,400)
        self.assertEqual(self.api_post({'action':'deliver_initial','line_id':123}).status_code,400)
        verified_login(self.client,self.other)
        self.assertEqual(self.api_post({'action':'provision'}).status_code,404)
        verified_login(self.client,self.owner)
        with override_settings(SHOP_ENV='production'):
            self.assertEqual(self.api_post({'action':'provision'}).status_code,404)

    def test_concurrent_grants_with_archive_contention_reconcile_once(self):
        self.pay();barrier=Barrier(2)
        def run(_):
            try:
                barrier.wait(timeout=10)
                try:return self.provision().pk
                except ArchiveError:return 'archive_retry'
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(run,range(2)))
        grant=self.provision()
        self.assertTrue(all(result in (grant.pk,'archive_retry') for result in results))
        self.assertEqual(SyntheticFulfilment.objects.count(),1)
        self.assertEqual(SyntheticLineEntitlement.objects.count(),1)
        self.assertEqual(grant.support_seconds,72000)

    def test_database_enforces_seconds_no_expiry_and_no_actual_effects(self):
        self.pay();grant=self.provision()
        from django.utils import timezone
        for update in ({'support_seconds':1},{'expires_at':timezone.now()},{'effects_authorized':True}):
            with self.assertRaises(IntegrityError),transaction.atomic():SyntheticFulfilment.objects.filter(pk=grant.pk).update(**update)

    def test_reference_requires_recoverable_initial_completion(self):
        self.pay();self.provision();line=uuid.UUID(self.ip['id'])
        fulfilment.deliver(self.owner,self.saved.pk,line,'initial',self.archive)
        event=SyntheticLineDelivery.objects.get();event.archive_receipt={};event.save()
        with self.assertRaisesRegex(checkout.CheckoutError,'archive_mismatch'):
            fulfilment.deliver(self.owner,self.saved.pk,line,'reference',self.archive)
        self.assertEqual(SyntheticLineDelivery.objects.count(),1)
