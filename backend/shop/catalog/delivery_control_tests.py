"""Real PostgreSQL delivery holds, archive ordering and stale bearer fencing."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch
import uuid
from django.db import connections,transaction,IntegrityError
from django.test import Client,TransactionTestCase,override_settings
from shop.adapters.evidence_archive import PreparedArchive,ArchiveError
from . import delivery_controls as controls,private_packages as packages,private_package_tests as fixture,checkout,fulfilment,support_ledger as ledger
from .models import SyntheticDeliveryControl as Control,SyntheticDeliveryStaffGrant,SyntheticPackageAccess,SyntheticLineDelivery,SyntheticPackageRevision


class DeliveryControlTests(TransactionTestCase):
    save_cart=fixture.PrivatePackageTests.save_cart
    preview=fixture.PrivatePackageTests.preview
    accept=fixture.PrivatePackageTests.accept
    release=fixture.PrivatePackageTests.release
    issue=fixture.PrivatePackageTests.issue
    form=fixture.PrivatePackageTests.form

    def setUp(self):
        fixture.PrivatePackageTests.setUp(self)
        self.package=self.release()

    def record(self,action='hold',key=None,expected=None,archive=None):
        if expected is None:expected=Control.objects.filter(entitlement=self.line).count()
        return controls.record(self.request,self.owner,self.saved.pk,self.line.pk,key or uuid.uuid4(),expected,action,archive or self.archive)

    def download(self,token,archive=None):return packages.download(self.customer,self.saved.pk,self.package.identity,token,archive or self.archive)

    def test_hold_blocks_release_grants_downloads_and_stage_completion(self):
        token=self.issue(self.package);before=ledger.read(self.owner,self.saved.pk,self.archive)
        self.record()
        for call in (lambda:self.issue(self.package),lambda:self.download(token),lambda:self.release(fixture='synthetic-materials-v2'),
                     lambda:fulfilment.deliver(self.owner,self.saved.pk,self.line.line_id,'reference',self.archive)):
            with self.assertRaisesRegex(checkout.CheckoutError,'delivery_held'):call()
        self.assertEqual(SyntheticPackageRevision.objects.count(),1);self.assertEqual(SyntheticLineDelivery.objects.count(),1)
        self.assertEqual(ledger.read(self.owner,self.saved.pk,self.archive),before)
        self.assertIsNone(SyntheticPackageAccess.objects.get().consumed_at)

    def test_clear_does_not_revive_old_token_but_fresh_grant_works(self):
        token=self.issue(self.package);self.record();self.record('clear')
        with self.assertRaisesRegex(checkout.CheckoutError,'download_unavailable'):self.download(token)
        fresh=self.issue(self.package);name,body=self.download(fresh)
        self.assertEqual(name,'sll-synthetic-rtl.txt');self.assertIn(b'synthetic-materials-v1',body)
        self.assertEqual(SyntheticPackageAccess.objects.get(token_digest=packages.digest('package-token',fresh)).authority_revision,2)
        with self.assertRaises(checkout.CheckoutError):self.download(fresh)

    def test_exact_retry_cannot_reapply_historical_hold_after_clear(self):
        key=uuid.uuid4();row=self.record(key=key,expected=0);self.record('clear')
        self.assertEqual(self.record(key=key,expected=0).pk,row.pk)
        self.assertFalse(controls.state(self.line,self.archive)[0]['held'])
        with self.assertRaisesRegex(checkout.CheckoutError,'delivery_control_retry_conflict'):self.record('clear',key,0)
        with self.assertRaisesRegex(checkout.CheckoutError,'delivery_control_revision_changed'):self.record(expected=0)
        with self.assertRaisesRegex(checkout.CheckoutError,'delivery_control_state_changed'):self.record('clear')
        self.assertEqual(Control.objects.count(),2)

    def test_archive_failure_prevents_hold_and_failed_clear_keeps_hold(self):
        with patch.object(self.archive,'publish',side_effect=ArchiveError('offline')):
            with self.assertRaises(ArchiveError):self.record()
        self.assertEqual(Control.objects.count(),0)
        self.record()
        with patch.object(self.archive,'publish',side_effect=ArchiveError('offline')):
            with self.assertRaises(ArchiveError):self.record('clear')
        self.assertTrue(controls.state(self.line,self.archive)[0]['held']);self.assertEqual(Control.objects.count(),1)

    def test_missing_control_evidence_blocks_download_even_after_clear(self):
        self.record();self.record('clear');token=self.issue(self.package)
        original=self.archive.recover;ids=set(Control.objects.values_list('pk',flat=True))
        def recover(receipt):
            if receipt.evidence_id in ids:raise ArchiveError('missing control')
            return original(receipt)
        with patch.object(self.archive,'recover',side_effect=recover):
            with self.assertRaises((checkout.CheckoutError,ArchiveError)):self.download(token)
            with self.assertRaises((checkout.CheckoutError,ArchiveError)):self.record()
        self.assertEqual(SyntheticPackageAccess.objects.filter(consumed_at__isnull=False).count(),0)

    def test_control_history_is_append_only(self):
        row=self.record()
        with self.assertRaises(IntegrityError),transaction.atomic():Control.objects.filter(pk=row.pk).update(sha256='0'*64)
        with self.assertRaises(IntegrityError),transaction.atomic():Control.objects.filter(pk=row.pk).delete()

    def test_recent_mfa_scope_and_revocation_required(self):
        SyntheticDeliveryStaffGrant.objects.all().delete()
        with self.assertRaises(checkout.CheckoutError):self.record()
        SyntheticDeliveryStaffGrant.objects.create(user=self.staff,entitlement=self.line)
        self.request.session['shop_staff_mfa']['verified_at']-=301
        with self.assertRaises(checkout.CheckoutError):self.record()
        self.assertEqual(Control.objects.count(),0)

    def test_concurrent_hold_commands_one_revision_wins(self):
        barrier=Barrier(2)
        def run(_):
            connections.close_all()
            try:
                barrier.wait(timeout=10)
                with PreparedArchive(self.root) as archive:
                    try:self.record(expected=0,archive=archive);return 'held'
                    except checkout.CheckoutError as error:return str(error)
            finally:connections.close_all()
        with ThreadPoolExecutor(2) as pool:results=list(pool.map(run,range(2)))
        self.assertCountEqual(results,['held','delivery_control_revision_changed'])
        self.assertEqual(Control.objects.count(),1)

    def test_download_racing_hold_is_serialized_and_no_new_grant_is_available(self):
        token=self.issue(self.package);barrier=Barrier(2)
        def run(kind):
            connections.close_all()
            try:
                barrier.wait(timeout=10)
                with PreparedArchive(self.root) as archive:
                    if kind=='hold':self.record(archive=archive);return 'held'
                    try:self.download(token,archive);return 'downloaded'
                    except checkout.CheckoutError as error:return str(error)
            finally:connections.close_all()
        with ThreadPoolExecutor(2) as pool:results=list(pool.map(run,['hold','download']))
        self.assertIn('held',results);self.assertTrue('downloaded' in results or 'delivery_held' in results)
        self.assertEqual(SyntheticPackageAccess.objects.filter(consumed_at__isnull=False).count(),1 if 'downloaded' in results else 0)
        with self.assertRaises(checkout.CheckoutError):self.issue(self.package)

    def test_private_owner_status_retains_versions_and_hides_download_buttons(self):
        self.record();path=f'/purchase/checkout-rehearsal/{self.saved.pk}/packages/'
        response=self.client.get(path);self.assertContains(response,'Delivery held');self.assertNotContains(response,'Prepare private download')
        value=self.client.get(path,HTTP_ACCEPT='application/json').json()['packages'][0]
        self.assertTrue(value['delivery_held']);self.assertEqual(value['delivery_revision'],1)
        self.assertNotIn('actor',value);self.assertIn('no-store',response['Cache-Control'])
        self.record('clear');self.assertContains(self.client.get(path),'Prepare private download')

    def test_staff_hold_clear_forms_are_private_and_scoped(self):
        from shop.access.staff_tests import STAFF_SETTINGS
        path=f'/staff/delivery/{self.line.pk}/'
        with override_settings(**STAFF_SETTINGS):
            staff=Client(HTTP_HOST='staff.localhost');staff.force_login(self.staff)
            session=staff.session;session['shop_staff_mfa']=self.request.session['shop_staff_mfa'];session.save()
            self.assertContains(staff.get(path),'Hold simulated delivery')
            command={'request_id':str(uuid.uuid4()),'expected_revision':'0','action':'hold'}
            for _ in range(2):self.assertEqual(self.form(staff,path+'control/',command).status_code,303)
            held=staff.get(path);self.assertContains(held,'Clear simulated delivery hold');self.assertNotContains(held,'Archive and release synthetic materials')
            self.assertEqual(self.form(staff,path+'control/',{'request_id':str(uuid.uuid4()),'expected_revision':'1','action':'clear'}).status_code,303)
            self.assertContains(staff.get(path),'Hold simulated delivery')
            self.assertEqual(staff.get(path+'control/').status_code,405)
            SyntheticDeliveryStaffGrant.objects.all().delete()
            self.assertEqual(self.form(staff,path+'control/',command).status_code,404)

    def test_bad_actions_revision_and_production_are_closed(self):
        for expected in (True,-1,1000,'0'):
            with self.assertRaises(checkout.CheckoutError):self.record(expected=expected)
        for action in ('approve','revoke-rights',None):
            with self.assertRaises(checkout.CheckoutError):self.record(action)
        from shop.payments.bank_contract import BankError
        with override_settings(SHOP_ENV='production'):
            with self.assertRaises(BankError):self.record()
        self.assertEqual(Control.objects.count(),0)
