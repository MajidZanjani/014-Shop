"""Real PostgreSQL private synthetic package release and body-only download grants."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from types import SimpleNamespace
from unittest.mock import patch
import json
import uuid
from django.db import connection,connections,transaction,IntegrityError,DatabaseError
from django.test import Client,RequestFactory,TransactionTestCase,override_settings
from django.utils import timezone
from shop.access.models import StaffCredential,AccessEpoch,LocalAccessRecoveryOperation
from shop.access.recovery import local_recovery_operation
from shop.adapters.evidence_archive import ArchiveError
from . import private_packages as packages,fulfilment,checkout,checkout_payment as payment
from . import support_ledger_tests as fixture
from .models import (SyntheticDeliveryStaffGrant,SyntheticPackageRevision,SyntheticPackageAccess,
                     SyntheticLineEntitlement,SyntheticLineDelivery,SyntheticFulfilment)


class PrivatePackageTests(TransactionTestCase):
    save_cart=fixture.SupportLedgerTests.save_cart
    preview=fixture.SupportLedgerTests.preview
    accept=fixture.SupportLedgerTests.accept

    def setUp(self):
        fixture.SupportLedgerTests.setUp(self)
        self.line=SyntheticLineEntitlement.objects.get(fulfilment=self.grant)
        SyntheticDeliveryStaffGrant.objects.create(user=self.staff,entitlement=self.line)
        self.customer=RequestFactory().post('/private/')
        self.customer.user=self.owner;self.customer.session=self.client.session

    def form(self,browser,path,value):
        from urllib.parse import urlencode
        return browser.post(path,data=urlencode(value),content_type='application/x-www-form-urlencoded')

    def release(self,stage='initial',fixture='synthetic-materials-v1',request_id=None):
        return packages.release(self.request,self.owner,self.saved.pk,self.line.pk,
            request_id or uuid.uuid4(),stage,fixture,self.archive)

    def issue(self,row,artifact='sll-synthetic-rtl.txt'):
        return packages.issue(self.customer,self.saved.pk,row.identity,artifact,self.archive)

    def download(self,row,token,request=None):
        return packages.download(request or self.customer,self.saved.pk,row.identity,token,self.archive)

    def recover(self,action='quarantine',*,request_id=None,basis_reset=None):
        return local_recovery_operation(action=action,request_id=request_id or uuid.uuid4(),
            expected_database=connection.settings_dict['NAME'],basis_reset=basis_reset)

    def stale_package_request(self,kind,*,released=False):
        row=self.release();token=self.issue(row);dict(self.customer.session)
        from shop.access.views import verified_identity
        self.assertIsNotNone(verified_identity(self.customer))
        reset=uuid.uuid4();self.recover(request_id=reset)
        if released:self.recover('release',basis_reset=reset)
        with self.assertRaisesRegex(checkout.CheckoutError,'download_unavailable'):
            self.issue(row) if kind=='issue' else self.download(row,token)
        self.assertEqual(SyntheticPackageAccess.objects.count(),1)
        self.assertIsNone(SyntheticPackageAccess.objects.get().consumed_at)
        if not released:self.recover('release',basis_reset=reset)
        from .tests import verified_login
        verified_login(self.client,self.owner);self.customer.session=self.client.session
        with self.assertRaisesRegex(checkout.CheckoutError,'download_unavailable'):self.download(row,token)
        fresh=self.issue(row);self.assertTrue(self.download(row,fresh)[1])

    def test_cached_customer_cannot_issue_after_quarantine(self):
        self.stale_package_request('issue')

    def test_cached_customer_cannot_issue_after_release(self):
        self.stale_package_request('issue',released=True)

    def test_cached_customer_cannot_download_after_quarantine(self):
        self.stale_package_request('download')

    def test_cached_customer_cannot_download_after_release(self):
        self.stale_package_request('download',released=True)

    def test_selected_restore_blocks_cached_package_access_before_quarantine(self):
        row=self.release();token=self.issue(row);dict(self.customer.session)
        epoch=AccessEpoch.objects.get().value
        with override_settings(LOCAL_RESTORE_ID=uuid.uuid4()):
            for kind in ('issue','download'):
                with self.subTest(kind=kind),self.assertRaisesRegex(checkout.CheckoutError,'download_unavailable'):
                    self.issue(row) if kind=='issue' else self.download(row,token)
        self.assertEqual(AccessEpoch.objects.get().value,epoch)
        self.assertEqual(LocalAccessRecoveryOperation.objects.count(),0)
        self.assertEqual(SyntheticPackageAccess.objects.count(),1)
        self.assertIsNone(SyntheticPackageAccess.objects.get().consumed_at)

    def package_epoch_lock(self,kind):
        row=self.release();token=self.issue(row);original=self.archive.recover
        original_locked=packages.payment.locked;observed=[]
        def observe(stage):
            if stage in observed:return
            def contender():
                try:
                    with transaction.atomic():AccessEpoch.objects.select_for_update(nowait=True).get(pk=1)
                except DatabaseError as error:return getattr(error.__cause__,'sqlstate',None)
                finally:connections.close_all()
                return 'unlocked'
            with ThreadPoolExecutor(max_workers=1) as pool:
                self.assertEqual(pool.submit(contender).result(timeout=10),'55P03')
            observed.append(stage)
        def locked(*args,**kwargs):
            observe('before-owner')
            return original_locked(*args,**kwargs)
        def recover(receipt):
            observe('archive')
            return original(receipt)
        with patch.object(packages.payment,'locked',side_effect=locked),patch.object(self.archive,'recover',side_effect=recover):
            result=self.issue(row) if kind=='issue' else self.download(row,token)
        self.assertEqual(observed,['before-owner','archive']);self.assertTrue(result)

    def test_issuance_holds_epoch_before_private_archive_and_resource_work(self):
        self.package_epoch_lock('issue')

    def test_download_holds_epoch_before_private_archive_and_resource_work(self):
        self.package_epoch_lock('download')

    def test_archive_initial_and_reference_versions_keep_one_entitlement_and_credit(self):
        original=self.saved.snapshot.copy();key=uuid.uuid4()
        with self.assertRaisesRegex(checkout.CheckoutError,'initial_package_required'):self.release('reference')
        initial=self.release(request_id=key)
        self.assertEqual(self.release(request_id=key).pk,initial.pk)
        status=fulfilment.status(payment.accepted(self.owner,self.saved.pk))
        self.assertTrue(status['lines'][0]['initial_delivered']);self.assertFalse(status['lines'][0]['reference_delivered'])
        reference=self.release('reference')
        self.assertEqual(reference.version,1)
        self.assertEqual(set(reference.payload['artifacts']),{'sll-synthetic-reference-design.txt'})
        self.assertTrue(fulfilment.status(payment.accepted(self.owner,self.saved.pk))['lines'][0]['reference_delivered'])
        self.assertEqual(SyntheticLineEntitlement.objects.count(),1);self.assertEqual(SyntheticFulfilment.objects.get().support_seconds,72000)
        self.saved.refresh_from_db();self.assertEqual(self.saved.snapshot,original)
        self.assertEqual(SyntheticLineDelivery.objects.count(),2)
        self.assertFalse(initial.effects_authorized);self.assertFalse(initial.payload['actual_delivery'])
        with self.assertRaisesRegex(checkout.CheckoutError,'package_request_conflict'):self.release(fixture='synthetic-materials-v2',request_id=key)

    def test_material_revision_retains_old_bytes_and_version_bound_single_use_access(self):
        first=self.release();token=self.issue(first)
        second=self.release(fixture='synthetic-materials-v2')
        self.assertEqual(second.version,2);self.assertEqual(second.payload['previous_sha256'],first.sha256)
        with self.assertRaisesRegex(checkout.CheckoutError,'download_unavailable'):self.download(second,token)
        name,body=self.download(first,token)
        self.assertEqual(name,'sll-synthetic-rtl.txt');self.assertIn(b'synthetic-materials-v1',body)
        self.assertIn(b'No executable RTL, real key',body)
        with self.assertRaisesRegex(checkout.CheckoutError,'download_unavailable'):self.download(first,token)
        access=SyntheticPackageAccess.objects.get()
        self.assertNotEqual(access.token_digest,token);self.assertIsNotNone(access.consumed_at)
        self.assertNotIn(token,str(first.payload));self.assertNotIn(token,str(first.archive_receipt))

    def test_staff_needs_exact_delivery_scope_recent_mfa_and_current_generation(self):
        SyntheticDeliveryStaffGrant.objects.all().delete()
        with self.assertRaisesRegex(checkout.CheckoutError,'delivery_scope_required'):self.release()
        SyntheticDeliveryStaffGrant.objects.create(user=self.staff,entitlement=self.line)
        self.request.session['shop_staff_mfa']['verified_at']-=301
        with self.assertRaisesRegex(checkout.CheckoutError,'recent_staff_mfa_required'):self.release()
        self.request.session['shop_staff_mfa']['verified_at']=timezone.now().timestamp()
        StaffCredential.objects.filter(pk=self.credential.pk).update(generation=uuid.uuid4())
        with self.assertRaisesRegex(checkout.CheckoutError,'recent_staff_mfa_required'):self.release()
        self.assertEqual(SyntheticPackageRevision.objects.count(),0)

    def test_archive_failure_before_publication_keeps_stage_and_package_unreleased(self):
        original=self.archive.publish
        def broken(identity,body):
            if b'"kind":"synthetic-private-package"' in body:raise ArchiveError('unavailable')
            return original(identity,body)
        with patch.object(self.archive,'publish',side_effect=broken):
            with self.assertRaises(ArchiveError):self.release()
        self.assertEqual(SyntheticPackageRevision.objects.count(),0);self.assertEqual(SyntheticLineDelivery.objects.count(),0)
        self.assertEqual(self.release().version,1)

    def test_expired_authority_during_archive_cannot_release_package(self):
        original=self.archive.publish
        def expire(identity,body):
            result=original(identity,body)
            if b'"kind":"synthetic-private-package"' in body:self.request.session['shop_staff_mfa']['verified_at']-=301
            return result
        with patch.object(self.archive,'publish',side_effect=expire):
            with self.assertRaisesRegex(checkout.CheckoutError,'recent_staff_mfa_required'):self.release()
        self.assertEqual(SyntheticPackageRevision.objects.count(),0);self.assertEqual(SyntheticLineDelivery.objects.count(),0)

    def test_download_expiry_session_rotation_and_current_owner_revocation(self):
        row=self.release();token=self.issue(row)
        other_session=SimpleNamespace(user=self.owner,session=SimpleNamespace(session_key='another-session'))
        with self.assertRaisesRegex(checkout.CheckoutError,'download_unavailable'):self.download(row,token,other_session)
        SyntheticPackageAccess.objects.update(expires_at=timezone.now()-timedelta(seconds=1))
        with self.assertRaisesRegex(checkout.CheckoutError,'download_unavailable'):self.download(row,token)
        token=self.issue(row)
        type(self.owner).objects.filter(pk=self.owner.pk).update(is_active=False)
        from shop.payments.bank_contract import BankError
        with self.assertRaises(BankError):self.download(row,token)
        self.assertFalse(SyntheticPackageAccess.objects.filter(consumed_at__isnull=False).exists())

    def test_missing_artifact_archive_cannot_issue_or_consume_access(self):
        row=self.release();token=self.issue(row)
        target=uuid.uuid5(row.identity,'sll-synthetic-rtl.txt');original=self.archive.recover
        def bad(receipt):return b'bad' if receipt.evidence_id==target else original(receipt)
        with patch.object(self.archive,'recover',side_effect=bad):
            with self.assertRaisesRegex(checkout.CheckoutError,'archive_mismatch'):self.issue(row)
            with self.assertRaisesRegex(checkout.CheckoutError,'archive_mismatch'):self.download(row,token)
        self.assertIsNone(SyntheticPackageAccess.objects.get().consumed_at)
        self.assertTrue(self.download(row,token)[1])

    def test_competing_same_request_release_and_token_consumption_commit_once(self):
        key=uuid.uuid4();barrier=Barrier(2)
        def release(_):
            try:barrier.wait(timeout=10);return self.release(request_id=key).pk
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:ids=list(pool.map(release,range(2)))
        self.assertEqual(ids[0],ids[1]);self.assertEqual(SyntheticPackageRevision.objects.count(),1)
        row=SyntheticPackageRevision.objects.get();token=self.issue(row);barrier=Barrier(2)
        def consume(_):
            try:
                barrier.wait(timeout=10)
                try:return self.download(row,token)[0]
                except checkout.CheckoutError as e:return str(e)
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:outcomes=list(pool.map(consume,range(2)))
        self.assertCountEqual(outcomes,['sll-synthetic-rtl.txt','download_unavailable'])

    def test_revision_history_cannot_be_updated_or_deleted(self):
        row=self.release()
        for mutate in (lambda:SyntheticPackageRevision.objects.filter(pk=row.pk).update(payload={}),
                       lambda:SyntheticPackageRevision.objects.filter(pk=row.pk).delete()):
            with self.assertRaises(IntegrityError),transaction.atomic():mutate()
        packages.retained(SyntheticPackageRevision.objects.get(),self.line,self.archive)

    def test_owner_forms_body_only_token_csrf_closed_parser_and_no_staff_metadata(self):
        row=self.release();base=f'/purchase/checkout-rehearsal/{self.saved.pk}/packages/'
        page=self.client.get(base);self.assertContains(page,'Prepare private download')
        for forbidden in ('credential_generation','mfa_verified_at','archive_receipt','SYNTHETIC_BUSINESS_CANARY'):
            self.assertNotIn(forbidden,page.content.decode())
        access=base+str(row.identity)+'/access/';download=base+str(row.identity)+'/download/'
        response=self.form(self.client,access,{'artifact':'sll-synthetic-rtl.txt'})
        self.assertEqual(response.status_code,200)
        import re
        token=re.search(r'name="token" value="([A-Za-z0-9_-]+)"',response.content.decode())[1]
        self.assertNotIn(token,download);self.assertEqual(response['Cache-Control'],'no-store')
        result=self.form(self.client,download,{'token':token});self.assertEqual(result.status_code,200)
        self.assertEqual(result['Content-Type'],'application/octet-stream');self.assertEqual(result['X-Content-Type-Options'],'nosniff')
        self.assertIn('attachment',result['Content-Disposition']);self.assertEqual(result['Cache-Control'],'no-store')
        self.assertEqual(self.client.get(download).status_code,405)
        self.assertEqual(self.form(self.client,download,{'token':token}).status_code,404)
        for value in ({'artifact':1},{'artifact':'x','token':'x'},{'artifact':'../key'}):
            self.assertIn(self.client.post(access,data=json.dumps(value),content_type='application/json').status_code,(400,404))
        csrf=Client(enforce_csrf_checks=True);csrf.cookies=self.client.cookies.copy()
        self.assertEqual(self.form(csrf,access,{'artifact':'sll-synthetic-rtl.txt'}).status_code,403)
        self.assertEqual(self.client.get(base+'?unexpected=1').status_code,400)
        from .tests import verified_login
        verified_login(self.client,self.other)
        self.assertEqual(self.client.get(base).status_code,404)
        self.assertEqual(self.form(self.client,access,{'artifact':'sll-synthetic-rtl.txt'}).status_code,404)
        with override_settings(SHOP_ENV='production'):self.assertEqual(self.client.get(base).status_code,404)

    def test_access_issuance_bounded_and_artifact_bound(self):
        row=self.release()
        with self.assertRaises(checkout.CheckoutError):self.issue(row,'not-an-artifact')
        tokens=[self.issue(row) for _ in range(20)]
        self.assertEqual(len(set(tokens)),20)
        with self.assertRaisesRegex(checkout.CheckoutError,'download_grant_limit'):self.issue(row)
        self.download(row,tokens[0]);self.assertTrue(self.issue(row))

    def test_staff_queue_release_and_operator_reset_revoke_delivery_scope(self):
        from shop.access.staff_tests import STAFF_SETTINGS
        from django.core.management import call_command
        with override_settings(**STAFF_SETTINGS):
            browser=Client(HTTP_HOST='staff.localhost');route=f'/staff/delivery/{self.line.pk}/'
            self.assertEqual(browser.get(route).status_code,403)
            browser.force_login(self.staff);session=browser.session;session['shop_staff_mfa']=self.request.session['shop_staff_mfa'];session.save()
            self.assertContains(browser.get('/staff/delivery/'),str(self.line.pk))
            self.assertContains(browser.get(route),'Archive and release synthetic materials')
            key=str(uuid.uuid4())
            for _ in range(2):
                result=self.form(browser,route,{'request_id':key,'stage':'initial','fixture':'synthetic-materials-v1'})
                self.assertEqual(result.status_code,303)
            self.assertEqual(SyntheticPackageRevision.objects.count(),1)
            call_command('local_staff','revoke-delivery',username=self.staff.username,entitlement=str(self.line.pk),verbosity=0)
            self.assertEqual(browser.get(route).status_code,404)
            call_command('local_staff','grant-delivery',username=self.staff.username,entitlement=str(self.line.pk),verbosity=0)
            self.assertEqual(browser.get(route).status_code,200)
            call_command('local_staff','reset',username=self.staff.username,capture_root=str(self.root),verbosity=0)
            self.assertFalse(SyntheticDeliveryStaffGrant.objects.exists());self.assertEqual(browser.get(route).status_code,403)

    def test_ready_kit_initial_materials_include_reference_without_extra_entitlement(self):
        from copy import deepcopy
        from shop.payments.purchase_flow_tests import configuration
        from .purchase_policy import FIXTURE_KITS
        from .rules import CATALOG
        ready=deepcopy(self.ip);ready['configuration']=configuration('listed-kit',0)
        with patch.dict(CATALOG['purchase_flow'],{'ready_kits':list(FIXTURE_KITS)}):
            self.save_cart([ready]);self.saved,_=checkout.capture(self.owner,uuid.uuid4(),self.preview()['sha256'])
        self.accept();payment.pay(self.owner,self.saved.pk,self.archive)
        self.grant=fulfilment.provision(self.owner,self.saved.pk,self.archive)
        self.line=SyntheticLineEntitlement.objects.get(fulfilment=self.grant)
        SyntheticDeliveryStaffGrant.objects.create(user=self.staff,entitlement=self.line)
        initial=self.release()
        self.assertIn('sll-synthetic-reference-design.txt',initial.payload['artifacts'])
        self.assertEqual(self.grant.support_seconds,0)
        self.assertTrue(fulfilment.status(payment.accepted(self.owner,self.saved.pk))['lines'][0]['reference_delivered'])
        with self.assertRaisesRegex(checkout.CheckoutError,'initial_package_required'):self.release('reference')
        self.assertEqual(SyntheticLineEntitlement.objects.filter(fulfilment=self.grant).count(),1)

    def test_private_revision_paging_retains_all_versions(self):
        for _ in range(21):self.release()
        base=f'/purchase/checkout-rehearsal/{self.saved.pk}/packages/'
        first=self.client.get(base,HTTP_ACCEPT='application/json').json()
        self.assertEqual(len(first['packages']),20);self.assertEqual(first['packages'][0]['version'],21)
        second=self.client.get(base+'?before='+str(first['next_before']),HTTP_ACCEPT='application/json').json()
        self.assertEqual([item['version'] for item in second['packages']],[1]);self.assertIsNone(second['next_before'])
        self.assertEqual(SyntheticPackageRevision.objects.count(),21)

    def test_expiry_during_final_archive_read_does_not_consume_token(self):
        row=self.release();token=self.issue(row);access=SyntheticPackageAccess.objects.get()
        now=timezone.now()
        with patch.object(packages.attempts,'database_now',side_effect=[now,access.expires_at+timedelta(seconds=1)]):
            with self.assertRaisesRegex(checkout.CheckoutError,'download_unavailable'):self.download(row,token)
        access.refresh_from_db();self.assertIsNone(access.consumed_at)
