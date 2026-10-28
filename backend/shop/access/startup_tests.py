"""Disposable PostgreSQL restore startup boundary; no actual restore or reopening."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import uuid
from django.contrib.auth import get_user_model
from django.db import connection
from django.test import Client,TransactionTestCase,override_settings
from shop.adapters.fake_bank import perform_fake_probe
from shop.adapters.ports import ProbeRequest
from shop.catalog.tests import verified_login
from shop.payments import synthetic_bank,notifications
from shop.payments.bank_contract import BankError,BankStart,BankMutation
from shop.payments.models import SyntheticBankOperation,SyntheticBankTransition
from shop.worker import services,statement_mail
from shop.worker.models import Probe,FakeReceipt
from . import effects
from .models import AccessEpoch,LocalAccessRecoveryOperation,LocalEffectAdmission,CustomerIdentity,StaffCredential,StaffChallenge,VerificationChallenge
from .recovery import AccessRecoveryError,SESSION_EPOCH,current_session_epoch,local_recovery_operation,recovery_held,stamp_session_epoch
from .staff_auth import staff_credential
from .staff_tests import STAFF_SETTINGS
from .tests import BASE,csrf_post,request_capture
from .views import verified_identity


class LocalRestoreStartupTests(TransactionTestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory();self.addCleanup(self.directory.cleanup)
        config=override_settings(LOCAL_CAPTURE_ROOT=self.directory.name,LOCAL_STAFF_CAPTURE_ROOT=self.directory.name)
        config.enable();self.addCleanup(config.disable)
        self.database=connection.settings_dict['NAME']
        self.owner=get_user_model().objects.create_user(username='startup-synthetic-owner')
        self.customer=Client(enforce_csrf_checks=True)
        verified_login(self.customer,self.owner)

    def operation(self,action='quarantine',*,request_id=None,basis_reset=None):
        return local_recovery_operation(action=action,request_id=request_id or uuid.uuid4(),
            expected_database=self.database,basis_reset=basis_reset)

    def complete_restore(self,identity):
        self.operation(request_id=identity)
        return self.operation('release',basis_reset=identity)

    def test_fresh_restore_identity_blocks_unheld_restored_session_without_writes(self):
        self.assertTrue(self.customer.get(BASE+'session/').json()['authenticated'])
        original=AccessEpoch.objects.get().value
        with override_settings(LOCAL_RESTORE_ID=uuid.uuid4()):
            response=self.customer.get(BASE+'session/')
            self.assertEqual(response.status_code,503)
            self.assertEqual(response.json(),{'error':'access_recovery_pending'})
            self.assertEqual(response['X-Shop-Access-Recovery'],'pending')
            self.assertEqual(response['Cache-Control'],'no-store')
        epoch=AccessEpoch.objects.get()
        self.assertEqual(epoch.value,original);self.assertFalse(epoch.quarantined)
        self.assertEqual(LocalAccessRecoveryOperation.objects.count(),0)
        self.assertEqual(LocalEffectAdmission.objects.count(),0)

    def test_pending_startup_denies_private_authority_and_customer_code_capture(self):
        code=request_capture(self.customer,self.directory.name,'startup@synthetic.invalid')
        cached=SimpleNamespace(user=self.owner,session=dict(self.customer.session))
        token=self.customer.cookies['csrftoken'].value
        before=set(Path(self.directory.name).iterdir())
        counts=(VerificationChallenge.objects.count(),LocalEffectAdmission.objects.count())
        with override_settings(LOCAL_RESTORE_ID=uuid.uuid4()):
            self.assertIsNone(verified_identity(cached));self.assertFalse(current_session_epoch(cached))
            response=self.customer.get('/api/v1/configuration-drafts/')
            self.assertEqual(response.status_code,403)
            self.assertEqual(response.json(),{'error':'verification_required'})
            self.assertContains(self.customer.get('/purchase/access/'),'temporarily paused',status_code=503)
            for path,value in [('request-code/',{'email':'another@synthetic.invalid'}),('verify/',{'code':code})]:
                response=self.customer.post(BASE+path,data=json.dumps(value),content_type='application/json',HTTP_X_CSRFTOKEN=token)
                self.assertEqual(response.status_code,503)
                self.assertEqual(response['X-Shop-Access-Recovery'],'pending')
            session={SESSION_EPOCH:str(AccessEpoch.objects.get().value)}
            stamp_session_epoch(None,SimpleNamespace(session=session),self.owner)
            self.assertNotIn(SESSION_EPOCH,session)
        self.assertIsNone(VerificationChallenge.objects.get().consumed_at)
        self.assertEqual((VerificationChallenge.objects.count(),LocalEffectAdmission.objects.count()),counts)
        self.assertEqual(set(Path(self.directory.name).iterdir()),before)

    def test_pending_startup_denies_existing_staff_mfa_and_both_factors(self):
        user=get_user_model().objects.create_user(username='startup-synthetic-staff',password='synthetic-password',is_staff=True)
        StaffCredential.objects.create(user=user)
        browser=Client(enforce_csrf_checks=True,HTTP_HOST='staff.localhost')
        with override_settings(**STAFF_SETTINGS):
            self.assertEqual(browser.get('/staff/session/').status_code,200)
            def post(path,value):
                return browser.post('/staff/'+path,data=json.dumps(value),content_type='application/json',HTTP_X_CSRFTOKEN=browser.cookies['shop_staff_csrftoken'].value)
            before=set(Path(self.directory.name).iterdir())
            self.assertEqual(post('login/',{'username':user.username,'password':'synthetic-password'}).status_code,200)
            code=re.search(r'^Code: (.+)$',(set(Path(self.directory.name).iterdir())-before).pop().read_text(),re.M)[1]
            self.assertEqual(post('verify/',{'code':code}).status_code,200)
            cached=SimpleNamespace(user=user,session=dict(browser.session),get_host=lambda:'staff.localhost')
            self.assertIsNotNone(staff_credential(cached))
            counts=(StaffChallenge.objects.count(),LocalEffectAdmission.objects.count())
            with override_settings(LOCAL_RESTORE_ID=uuid.uuid4()):
                self.assertIsNone(staff_credential(cached))
                self.assertEqual(browser.get('/staff/session/').status_code,503)
                self.assertEqual(browser.get('/staff/quotation-requests/').status_code,403)
                for path,value in [('login/',{'username':user.username,'password':'synthetic-password'}),('verify/',{'code':code})]:
                    self.assertEqual(post(path,value).status_code,503)
            self.assertEqual((StaffChallenge.objects.count(),LocalEffectAdmission.objects.count()),counts)

    def test_missing_epoch_stays_missing_even_with_earlier_matching_history(self):
        identity=uuid.uuid4();self.complete_restore(identity)
        AccessEpoch.objects.all().delete()
        before=LocalAccessRecoveryOperation.objects.count()
        with override_settings(LOCAL_RESTORE_ID=identity):
            self.assertTrue(recovery_held())
            self.assertEqual(self.customer.get(BASE+'session/').status_code,503)
            with self.assertRaisesMessage(effects.RecoveryEffectError,'recovery_effects_pending'):
                effects._begin('worker-run')
            stamp_session_epoch(None,SimpleNamespace(session={}),self.owner)
            state=effects.inspect_local_effects()
            self.assertTrue(state['startup_recovery_pending']);self.assertFalse(state['currently_quarantined'])
            self.assertFalse(state['local_effects_drained'])
        self.assertFalse(AccessEpoch.objects.exists())
        self.assertEqual(LocalAccessRecoveryOperation.objects.count(),before)
        self.assertEqual(LocalEffectAdmission.objects.count(),0)

    def test_old_or_unrelated_release_cannot_satisfy_fresh_identity(self):
        previous=uuid.uuid4();self.complete_restore(previous)
        selected=uuid.uuid4()
        with override_settings(LOCAL_RESTORE_ID=selected):
            self.assertTrue(recovery_held())
            self.complete_restore(uuid.uuid4())
            self.assertTrue(effects.inspect_local_effects()['startup_recovery_pending'])
            self.assertEqual(self.customer.get(BASE+'session/').status_code,503)
            self.assertFalse(self.complete_restore(selected)['startup_recovery_pending'])
            self.assertEqual(self.customer.get(BASE+'session/').status_code,200)
        with override_settings(LOCAL_RESTORE_ID=uuid.uuid4()):
            self.assertTrue(recovery_held())
            replay=self.operation('release',basis_reset=selected,request_id=LocalAccessRecoveryOperation.objects.get(action='release',basis_reset=selected).pk)
            self.assertTrue(replay['startup_recovery_pending'])
            self.assertEqual(self.customer.get(BASE+'session/').status_code,503)

    def test_matching_sequence_requires_fresh_login_and_preserves_later_holds(self):
        email=CustomerIdentity.objects.get(user=self.owner).email
        old_code=request_capture(self.customer,self.directory.name,email)
        cached=SimpleNamespace(user=self.owner,session=dict(self.customer.session))
        identity=uuid.uuid4()
        with override_settings(LOCAL_RESTORE_ID=identity):
            held=self.operation(request_id=identity)
            self.assertTrue(held['currently_quarantined']);self.assertTrue(held['startup_recovery_pending'])
            self.assertEqual(self.customer.get(BASE+'session/').status_code,503)
            self.assertFalse(self.operation('release',basis_reset=identity)['startup_recovery_pending'])
            self.assertFalse(self.customer.get(BASE+'session/').json()['authenticated'])
            self.assertIsNone(verified_identity(cached))
            self.assertEqual(csrf_post(self.customer,BASE+'verify/',{'code':old_code}).status_code,400)
            fresh=request_capture(self.customer,self.directory.name,email)
            self.assertEqual(csrf_post(self.customer,BASE+'verify/',{'code':fresh}).status_code,200)
            self.assertTrue(self.customer.get(BASE+'session/').json()['authenticated'])
            later=uuid.uuid4();self.operation(request_id=later)
            self.assertEqual(self.customer.get(BASE+'session/').status_code,503)
            released=self.operation('release',basis_reset=later)
            self.assertFalse(released['startup_recovery_pending']);self.assertFalse(released['actual_recovery_qualified'])
            self.assertFalse(self.customer.get(BASE+'session/').json()['authenticated'])

    def test_startup_blocks_worker_and_bank_mutation_but_lookup_is_read_only(self):
        request=BankStart('synthetic-startup',uuid.uuid4(),uuid.uuid4(),'EUR',100)
        observed=synthetic_bank.start(request,outcome='authorized')
        mutation=BankMutation(request.merchant,request.reference,observed.provider_operation_id,uuid.uuid4(),'EUR',100,'capture')
        probe=Probe.objects.create()
        before=list(LocalEffectAdmission.objects.values())
        with override_settings(LOCAL_RESTORE_ID=uuid.uuid4()):
            with self.assertRaisesMessage(BankError,'recovery_effects_pending'):synthetic_bank.start(request,outcome='authorized')
            with self.assertRaisesMessage(BankError,'recovery_effects_pending'):synthetic_bank.mutate(mutation)
            self.assertFalse(services.execute_once());self.assertIsNone(services.claim_probe())
            self.assertFalse(statement_mail.execute_once());self.assertIsNone(statement_mail.claim())
            self.assertFalse(notifications.execute_once());self.assertIsNone(notifications.claim())
            with self.assertRaisesMessage(effects.RecoveryEffectError,'recovery_effects_pending'):perform_fake_probe(ProbeRequest(probe.effect_id))
            self.assertEqual(synthetic_bank.lookup(request.merchant,request.reference).status,'authorized')
            self.assertIsNone(synthetic_bank.lookup_mutation(mutation))
            state=effects.inspect_local_effects()
            self.assertTrue(state['startup_recovery_pending']);self.assertFalse(state['currently_quarantined'])
            self.assertFalse(state['local_effects_drained']);self.assertFalse(state['retry_authorized'])
        probe.refresh_from_db();self.assertEqual((probe.state,probe.attempts),('pending',0))
        self.assertEqual(SyntheticBankOperation.objects.count(),1);self.assertEqual(SyntheticBankTransition.objects.count(),0)
        self.assertEqual(FakeReceipt.objects.count(),0);self.assertEqual(list(LocalEffectAdmission.objects.values()),before)

    def test_startup_release_waits_for_prior_call_exit(self):
        active=effects._begin('worker-run');identity=uuid.uuid4()
        with override_settings(LOCAL_RESTORE_ID=identity):
            self.operation(request_id=identity)
            with self.assertRaisesMessage(AccessRecoveryError,'recovery_effects_unfinished'):
                self.operation('release',basis_reset=identity)
            self.assertTrue(effects.inspect_local_effects()['startup_recovery_pending'])
            # Existing calls may record their exit while all new calls are held.
            effects._finish(active,'returned')
            released=self.operation('release',basis_reset=identity)
            self.assertFalse(released['startup_recovery_pending']);self.assertEqual(released['unfinished_effects'],0)

    def test_separate_customer_staff_worker_processes_share_persisted_startup_sequence(self):
        identity=uuid.uuid4();probe=Probe.objects.create()
        source='''import django,json,sys
django.setup()
from django.test import Client
from shop.access.effects import inspect_local_effects
from shop.worker.services import execute_once
role=sys.argv[1]
if role=='worker': result={'ran':execute_once()}
else:
 response=Client(HTTP_HOST='staff.localhost' if role=='staff' else '127.0.0.1').get('/staff/session/' if role=='staff' else '/api/v1/customer/session/')
 result={'status':response.status_code,'authenticated':response.json().get('authenticated',False)}
result['startup_pending']=inspect_local_effects()['startup_recovery_pending']
print(json.dumps(result))
'''
        for completed in (False,True):
            if completed:
                with override_settings(LOCAL_RESTORE_ID=identity):self.complete_restore(identity)
            for role in ('customer','staff','worker'):
                env=dict(os.environ,DATABASE_NAME=self.database,SHOP_LOCAL_RESTORE_ID=str(identity),
                    DJANGO_SETTINGS_MODULE='shop.config.staff_synthetic' if role=='staff' else 'shop.config.synthetic')
                result=subprocess.run([sys.executable,'-c',source,role],env=env,capture_output=True,text=True,timeout=8)
                self.assertEqual(result.returncode,0,result.stderr)
                value=json.loads(result.stdout)
                self.assertEqual(value['startup_pending'],not completed)
                if role=='worker':self.assertEqual(value['ran'],completed)
                else:self.assertEqual(value,{'status':200 if completed else 503,'authenticated':False,'startup_pending':not completed})
        probe.refresh_from_db();self.assertEqual(probe.state,'complete')
        self.assertEqual(FakeReceipt.objects.count(),1)

    def test_invalid_runtime_restore_setting_cannot_enable_access_or_effects(self):
        for identity in (False,'',str(uuid.uuid4()),uuid.UUID('12345678-1234-1abc-8def-123456789abc')):
            with self.subTest(kind=type(identity).__name__),override_settings(LOCAL_RESTORE_ID=identity):
                self.assertTrue(recovery_held())
                self.assertFalse(current_session_epoch(SimpleNamespace(session=dict(self.customer.session))))
                with self.assertRaisesMessage(effects.RecoveryEffectError,'recovery_effects_pending'):effects._begin('worker-run')
        self.assertEqual(LocalEffectAdmission.objects.count(),0)
