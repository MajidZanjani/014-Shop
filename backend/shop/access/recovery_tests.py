"""Real PostgreSQL application recovery component; no restore or actual reopening."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import re
import tempfile
from threading import Barrier
from types import SimpleNamespace
from unittest.mock import patch
import uuid
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.db import connection,connections,DatabaseError,transaction
from django.test import Client,TransactionTestCase,override_settings
from shop.catalog.models import ConfigurationDraft,DraftCart,CartSnapshot,QuotationRequest
from shop.catalog.rules import CATALOG,evaluate
from shop.catalog.cart_rules import evaluate_cart
from shop.catalog.tests import CASES,verified_login
from .models import AccessEpoch,CustomerIdentity,LocalAccessRecoveryOperation,StaffChallenge,StaffCredential,StaffQuotationGrant,VerificationChallenge
from .recovery import AccessRecoveryError,SESSION_EPOCH,local_recovery_operation
from .staff_auth import staff_credential
from .staff_tests import STAFF_SETTINGS
from .tests import BASE,csrf_post,request_capture
from .views import verified_identity

class RecoveryTests(TransactionTestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory();self.addCleanup(self.directory.cleanup)
        config=override_settings(LOCAL_CAPTURE_ROOT=self.directory.name,LOCAL_STAFF_CAPTURE_ROOT=self.directory.name)
        config.enable();self.addCleanup(config.disable)
        self.database=connection.settings_dict['NAME']
        self.owner=get_user_model().objects.create_user(username='recovery-synthetic-owner')
        self.customer=Client(enforce_csrf_checks=True);verified_login(self.customer,self.owner)
        self.customer.get(BASE+'session/')
        self.draft=ConfigurationDraft.objects.create(owner=self.owner,request_id=uuid.uuid4(),revision=CATALOG['revision'],configuration=CASES[0]['value'],evaluation=evaluate(CASES[0]['value']))
        self.password='synthetic-recovery-password'
        self.user=get_user_model().objects.create_user(username='recovery-synthetic-staff',password=self.password,is_staff=True)
        self.credential=StaffCredential.objects.create(user=self.user)
        self.staff=Client(enforce_csrf_checks=True,HTTP_HOST='staff.localhost')
        cart=DraftCart.objects.create(owner=self.owner,version=1)
        lines=[{'id':str(uuid.uuid4()),'kind':'support','product_id':CATALOG['support_product_id'],'quantity':1}]
        snapshot=CartSnapshot.objects.create(cart=cart,version=1,request_id=uuid.uuid4(),catalog_revision=CATALOG['revision'],lines=lines,evaluation=evaluate_cart(lines))
        self.quotation=QuotationRequest.objects.create(cart=cart,snapshot=snapshot,request_id=uuid.uuid4())
        StaffQuotationGrant.objects.create(user=self.user,quotation=self.quotation)
        with override_settings(**STAFF_SETTINGS):self.staff_login()

    def operation(self,action='quarantine',request_id=None,basis_reset=None,**kwargs):
        return local_recovery_operation(action=action,request_id=request_id or uuid.uuid4(),
            expected_database=kwargs.pop('expected_database',self.database),basis_reset=basis_reset,**kwargs)

    def staff_post(self,path,value,browser=None):
        browser=browser or self.staff
        if 'shop_staff_csrftoken' not in browser.cookies:browser.get('/staff/session/')
        return browser.post('/staff/'+path,data=json.dumps(value),content_type='application/json',
            HTTP_X_CSRFTOKEN=browser.cookies['shop_staff_csrftoken'].value)

    def staff_challenge(self,browser=None):
        before=set(Path(self.directory.name).iterdir())
        self.assertEqual(self.staff_post('login/',{'username':self.user.username,'password':self.password},browser).status_code,200)
        path=(set(Path(self.directory.name).iterdir())-before).pop()
        return re.search(r'^Code: (.+)$',path.read_text(),re.M)[1]

    def staff_login(self):
        code=self.staff_challenge()
        self.assertEqual(self.staff.get('/staff/quotation-requests/').status_code,403)
        self.assertEqual(self.staff_post('verify/',{'code':code}).status_code,200)

    def test_quarantine_invalidates_cookies_cached_markers_and_pending_challenges(self):
        pending_customer=Client(enforce_csrf_checks=True)
        request_capture(pending_customer,self.directory.name,'pending@synthetic.invalid')
        customer_state=dict(self.customer.session);staff_state=dict(self.staff.session)
        pending_staff=Client(enforce_csrf_checks=True,HTTP_HOST='staff.localhost')
        with override_settings(**STAFF_SETTINGS):self.staff_challenge(pending_staff)
        used=StaffChallenge.objects.get(consumed_at__isnull=False).consumed_at
        previous=self.credential.generation
        result=self.operation()
        self.assertTrue(result['currently_quarantined']);self.assertFalse(result['actual_recovery_qualified'])
        self.assertEqual(result['invalidated']['customer_challenges'],1)
        self.assertEqual(result['invalidated']['staff_challenges'],1)
        self.assertEqual(Session.objects.count(),0)
        self.assertEqual(StaffChallenge.objects.filter(consumed_at=used).count(),1)
        self.assertFalse(VerificationChallenge.objects.filter(consumed_at__isnull=True).exists())
        self.credential.refresh_from_db();self.assertNotEqual(self.credential.generation,previous);self.assertTrue(self.credential.enabled)
        self.assertIsNone(verified_identity(SimpleNamespace(user=self.owner,session=customer_state)))
        self.assertEqual(self.customer.get('/api/v1/configuration-drafts/'+str(self.draft.id)+'/').status_code,401)
        self.assertEqual(self.customer.get(BASE+'session/').status_code,503)
        self.assertEqual(self.customer.get('/purchase/access/').status_code,503)
        token=self.customer.cookies['csrftoken'].value
        for path,value in [('request-code/',{'email':'new@synthetic.invalid'}),('verify/',{'code':'synthetic'})]:
            response=self.customer.post(BASE+path,data=json.dumps(value),content_type='application/json',HTTP_X_CSRFTOKEN=token)
            self.assertEqual(response.status_code,503);self.assertEqual(response.json(),{'error':'access_recovery_pending'})
            self.assertEqual(response['Cache-Control'],'no-store')
        with override_settings(**STAFF_SETTINGS):
            cached=SimpleNamespace(user=self.user,session=staff_state,get_host=lambda:'staff.localhost')
            self.assertIsNone(staff_credential(cached))
            self.assertEqual(self.staff.get('/staff/quotation-requests/').status_code,403)
            self.assertEqual(self.staff.get('/staff/session/').status_code,503)
            self.assertContains(self.staff.get('/staff/'),'Staff access is temporarily paused',status_code=503)
            for path,value in [('login/',{'username':self.user.username,'password':self.password}),('verify/',{'code':'synthetic'})]:
                self.assertEqual(self.staff_post(path,value).status_code,503)
        self.assertEqual(ConfigurationDraft.objects.get().configuration,self.draft.configuration)
        self.assertEqual(CustomerIdentity.objects.count(),1)
        self.assertEqual(StaffQuotationGrant.objects.count(),1)
        self.assertEqual(QuotationRequest.objects.get().snapshot.lines,self.quotation.snapshot.lines)

    def test_release_requires_current_hold_and_fresh_verification(self):
        reset=uuid.uuid4();self.operation(request_id=reset)
        with self.assertRaisesMessage(AccessRecoveryError,'recovery_changed'):
            self.operation('release',basis_reset=uuid.uuid4())
        self.assertTrue(AccessEpoch.objects.get().quarantined)
        result=self.operation('release',basis_reset=reset)
        self.assertFalse(result['currently_quarantined']);self.assertFalse(result['actual_recovery_qualified'])
        self.assertEqual(self.customer.get('/api/v1/configuration-drafts/').status_code,401)
        code=request_capture(self.customer,self.directory.name,'fixture-'+str(self.owner.pk)+'@synthetic.invalid')
        self.assertEqual(csrf_post(self.customer,BASE+'verify/',{'code':code}).status_code,200)
        self.assertEqual(self.customer.get('/api/v1/configuration-drafts/'+str(self.draft.id)+'/').status_code,200)
        with override_settings(**STAFF_SETTINGS):
            self.assertEqual(self.staff.get('/staff/quotation-requests/').status_code,403)
            self.staff_login()
            self.assertEqual(self.staff.get('/staff/quotation-requests/'+str(self.quotation.id)+'/').status_code,200)
        self.assertEqual(LocalAccessRecoveryOperation.objects.count(),2)

    def test_exact_retries_preserve_fresh_sessions_and_later_quarantine(self):
        reset=uuid.uuid4();release=uuid.uuid4()
        held=self.operation(request_id=reset)
        released=self.operation('release',request_id=release,basis_reset=reset)
        verified_login(self.customer,self.owner)
        key=self.customer.session.session_key;epoch=AccessEpoch.objects.get().value
        with override_settings(**STAFF_SETTINGS):self.staff_login()
        self.assertEqual(self.operation(request_id=reset)['invalidated'],held['invalidated'])
        self.assertEqual(self.operation('release',request_id=release,basis_reset=reset),released)
        self.assertEqual(AccessEpoch.objects.get().value,epoch)
        self.assertEqual(self.customer.session.session_key,key)
        self.assertEqual(self.customer.get('/api/v1/configuration-drafts/').status_code,200)
        with override_settings(**STAFF_SETTINGS):self.assertEqual(self.staff.get('/staff/quotation-requests/').status_code,200)
        newer=uuid.uuid4();self.operation(request_id=newer)
        self.assertTrue(self.operation('release',request_id=release,basis_reset=reset)['currently_quarantined'])
        self.assertEqual(AccessEpoch.objects.get().active_reset,newer)
        with self.assertRaisesMessage(AccessRecoveryError,'recovery_changed'):self.operation('release',basis_reset=reset)
        with self.assertRaisesMessage(AccessRecoveryError,'request_conflict'):self.operation('release',request_id=reset,basis_reset=newer)
        self.assertEqual(LocalAccessRecoveryOperation.objects.count(),3)

    def test_denied_targets_modes_and_inputs_do_not_mutate(self):
        before=AccessEpoch.objects.get().value;session_count=Session.objects.count()
        for changes in ({'SHOP_ENV':'production'},{'SHOP_ENV':'bank-sandbox'},{'LIVE_PAYMENTS_ENABLED':True},
                        {'MAIL_ADAPTER':'actual'},{'STORAGE_ADAPTER':'actual'},{'PAYMENT_ADAPTER':'actual'}):
            with override_settings(**changes),self.assertRaisesMessage(AccessRecoveryError,'local_recovery_unavailable'):self.operation()
        for database in ('protected-shop','test_'+'0'*24):
            with self.assertRaisesMessage(AccessRecoveryError,'database_identity_mismatch'):self.operation(expected_database=database)
        for kwargs in ({'action':'unknown'},{'action':'release'},{'request_id':'invalid'}, {'basis_reset':uuid.uuid4()}):
            with self.assertRaisesMessage(AccessRecoveryError,'invalid_request'):self.operation(**kwargs)
        self.assertEqual(LocalAccessRecoveryOperation.objects.count(),0)
        self.assertEqual(AccessEpoch.objects.get().value,before)
        self.assertEqual(Session.objects.count(),session_count)

    def test_missing_and_stale_epoch_markers_deny_without_read_side_effects(self):
        snapshot=dict(self.customer.session)
        self.assertIsNotNone(verified_identity(SimpleNamespace(user=self.owner,session=snapshot)))
        for marker in (None,'bad',str(uuid.uuid4())):
            candidate=dict(snapshot)
            if marker is None:candidate.pop(SESSION_EPOCH)
            else:candidate[SESSION_EPOCH]=marker
            self.assertIsNone(verified_identity(SimpleNamespace(user=self.owner,session=candidate)))
        epoch=str(AccessEpoch.objects.get().value)
        self.assertNotIn(epoch,self.customer.get(BASE+'session/').content.decode())
        AccessEpoch.objects.all().delete()
        self.assertIsNone(verified_identity(SimpleNamespace(user=self.owner,session=snapshot)))
        self.assertFalse(self.customer.get(BASE+'session/').json()['authenticated'])
        self.assertEqual(AccessEpoch.objects.count(),0)

    def test_failed_operation_rolls_back_all_invalidations(self):
        epoch=AccessEpoch.objects.get().value;generation=self.credential.generation;sessions=Session.objects.count()
        with patch('shop.access.recovery.LocalAccessRecoveryOperation.objects.create',side_effect=RuntimeError('synthetic failure')):
            with self.assertRaises(RuntimeError):self.operation()
        self.assertEqual(AccessEpoch.objects.get().value,epoch)
        self.assertFalse(AccessEpoch.objects.get().quarantined)
        self.credential.refresh_from_db();self.assertEqual(self.credential.generation,generation)
        self.assertEqual(Session.objects.count(),sessions)
        self.assertEqual(LocalAccessRecoveryOperation.objects.count(),0)
        self.assertEqual(self.customer.get('/api/v1/configuration-drafts/').status_code,200)

    def test_operation_history_is_immutable(self):
        result=self.operation();row=LocalAccessRecoveryOperation.objects.get()
        for mutate in (lambda:LocalAccessRecoveryOperation.objects.filter(pk=row.pk).update(counts={}),
                       lambda:LocalAccessRecoveryOperation.objects.filter(pk=row.pk).delete()):
            with self.assertRaises(DatabaseError),transaction.atomic():mutate()
        self.assertEqual(LocalAccessRecoveryOperation.objects.get().counts,result['invalidated'])

    def race(self,action,request_id,basis=None):
        barrier=Barrier(2)
        def attempt(_):
            try:
                barrier.wait(timeout=10)
                return local_recovery_operation(action=action,request_id=request_id,expected_database=self.database,basis_reset=basis)
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:return list(pool.map(attempt,range(2)))

    def test_concurrent_quarantine_retry_rotates_once(self):
        result=self.race('quarantine',uuid.uuid4())
        self.assertEqual(result[0],result[1]);self.assertTrue(result[0]['currently_quarantined'])
        self.assertEqual(LocalAccessRecoveryOperation.objects.count(),1)
        self.assertEqual(AccessEpoch.objects.get().value,LocalAccessRecoveryOperation.objects.get().epoch)

    def test_concurrent_release_retry_rotates_once(self):
        reset=uuid.uuid4();self.operation(request_id=reset)
        result=self.race('release',uuid.uuid4(),reset)
        self.assertEqual(result[0],result[1]);self.assertFalse(result[0]['currently_quarantined'])
        self.assertEqual(LocalAccessRecoveryOperation.objects.count(),2)
