"""PostgreSQL authentication/quarantine interleavings; private synthetic captures."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import re
import tempfile
from threading import Event
from unittest.mock import patch
from urllib.parse import urlencode
import uuid
from django.contrib.auth import get_user_model
from django.db import connection,connections,transaction
from django.test import Client,TransactionTestCase,override_settings
from . import effects,views,staff_auth
from .effect_tests import RecoveryFixture
from .models import LocalEffectAdmission,StaffCredential,StaffChallenge,VerificationChallenge
from .recovery import AccessRecoveryError
from .staff_tests import STAFF_SETTINGS
from .tests import BASE,csrf_post,request_capture


class AuthenticationRecoveryTests(RecoveryFixture,TransactionTestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory();self.addCleanup(self.directory.cleanup)
        config=override_settings(LOCAL_CAPTURE_ROOT=self.directory.name,LOCAL_STAFF_CAPTURE_ROOT=self.directory.name)
        config.enable();self.addCleanup(config.disable)
        self.database=connection.settings_dict['NAME']
        self.browser=Client(enforce_csrf_checks=True)

    def customer_login_overlap(self,*,form=False):
        code=request_capture(self.browser,self.directory.name);reset=uuid.uuid4()
        original=views.login;release_blocked=[]
        def reset_then_login(request,user,**kwargs):
            self.assertFalse(connection.in_atomic_block)
            self.assertIsNotNone(VerificationChallenge.objects.get().consumed_at)
            self.recover(request_id=reset)
            try:self.recover('release',basis_reset=reset)
            except AccessRecoveryError as error:
                self.assertEqual(str(error),'recovery_effects_unfinished');release_blocked.append(True)
            else:release_blocked.append(False)
            return original(request,user,**kwargs)
        with patch.object(views,'login',side_effect=reset_then_login):
            if form:
                self.browser.get('/purchase/access/')
                response=self.browser.post('/purchase/access/',data=urlencode({'action':'verify','code':code}),
                    content_type='application/x-www-form-urlencoded',HTTP_X_CSRFTOKEN=self.browser.cookies['csrftoken'].value)
            else:response=csrf_post(self.browser,BASE+'verify/',{'code':code})
        state=self.browser.get(BASE+'session/').json()
        self.assertFalse(state.get('authenticated',False),'old code authenticated after recovery release')
        self.assertEqual(release_blocked,[True])
        self.assertEqual(response.status_code,503)
        if form:self.assertContains(response,'Customer access is temporarily paused for recovery review.',status_code=503)
        else:self.assertEqual(response.json(),{'error':'access_recovery_pending'})
        self.assertEqual(response['Cache-Control'],'no-store');self.assertNotIn(code,response.content.decode())
        self.assertEqual(LocalEffectAdmission.objects.filter(finished_at__isnull=True).count(),0)
        self.recover('release',basis_reset=reset)
        self.assertEqual(csrf_post(self.browser,BASE+'verify/',{'code':code}).status_code,400)
        fresh=request_capture(self.browser,self.directory.name)
        self.assertEqual(csrf_post(self.browser,BASE+'verify/',{'code':fresh}).status_code,200)
        self.assertTrue(self.browser.get(BASE+'session/').json()['authenticated'])

    def test_customer_code_cannot_login_after_mid_request_quarantine_and_release(self):
        self.customer_login_overlap()

    def test_customer_form_cannot_login_after_mid_request_quarantine_and_release(self):
        self.customer_login_overlap(form=True)

    def held_thread(self,post,entered,release):
        reset=uuid.uuid4()
        def request():
            try:return post()
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=1) as pool:
            future=pool.submit(request)
            try:
                self.assertTrue(entered.wait(5),'authentication pause was not reached')
                held=self.recover(request_id=reset)
                self.assertEqual(held['unfinished_effects'],1);self.assertFalse(held['local_effects_drained'])
                with self.assertRaisesMessage(AccessRecoveryError,'recovery_effects_unfinished'):
                    self.recover('release',basis_reset=reset)
            finally:release.set()
            response=future.result(timeout=10)
        self.assertEqual(response.status_code,503);self.assertEqual(response.json(),{'error':'access_recovery_pending'})
        self.assertEqual(response['Cache-Control'],'no-store')
        self.assertEqual(LocalEffectAdmission.objects.filter(finished_at__isnull=True).count(),0)
        return reset

    def test_customer_code_capture_overlapping_quarantine_is_consumed_before_release(self):
        entered=Event();release=Event();original=views.CaptureMail.send
        def wait(capture,message):
            entered.set()
            if not release.wait(8):raise RuntimeError('bounded capture wait')
            return original(capture,message)
        def post():return csrf_post(self.browser,BASE+'request-code/',{'email':'pending@synthetic.invalid'})
        with patch.object(views.CaptureMail,'send',wait):reset=self.held_thread(post,entered,release)
        self.assertEqual(VerificationChallenge.objects.filter(consumed_at__isnull=True).count(),1)
        self.recover('release',basis_reset=reset)
        self.assertEqual(VerificationChallenge.objects.filter(consumed_at__isnull=True).count(),0)
        fresh=request_capture(self.browser,self.directory.name)
        self.assertEqual(csrf_post(self.browser,BASE+'verify/',{'code':fresh}).status_code,200)

    def setup_staff(self):
        self.password='synthetic-overlap-password'
        self.staff=get_user_model().objects.create_user(username='overlap-staff',password=self.password,is_staff=True)
        StaffCredential.objects.create(user=self.staff)
        self.staff_browser=Client(enforce_csrf_checks=True,HTTP_HOST='staff.localhost')

    def staff_post(self,path,value):
        if 'shop_staff_csrftoken' not in self.staff_browser.cookies:self.staff_browser.get('/staff/session/')
        return self.staff_browser.post('/staff/'+path,data=json.dumps(value),content_type='application/json',
            HTTP_X_CSRFTOKEN=self.staff_browser.cookies['shop_staff_csrftoken'].value)

    def staff_code(self):
        before=set(Path(self.directory.name).iterdir())
        result=self.staff_post('login/',{'username':self.staff.username,'password':self.password})
        self.assertEqual(result.status_code,200)
        path=(set(Path(self.directory.name).iterdir())-before).pop()
        return re.search(r'^Code: (.+)$',path.read_text(),re.M)[1]

    def fresh_staff(self):
        self.assertFalse(self.staff_browser.get('/staff/session/').json()['authenticated'])
        code=self.staff_code()
        self.assertEqual(self.staff_browser.get('/staff/quotation-requests/').status_code,403)
        self.assertEqual(self.staff_post('verify/',{'code':code}).status_code,200)
        self.assertTrue(self.staff_browser.get('/staff/session/').json()['authenticated'])

    @override_settings(**STAFF_SETTINGS)
    def test_staff_password_capture_overlapping_quarantine_requires_both_fresh_factors(self):
        self.setup_staff();entered=Event();release=Event();original=staff_auth.authenticate
        def wait(*args,**kwargs):
            entered.set()
            if not release.wait(8):raise RuntimeError('bounded password wait')
            return original(*args,**kwargs)
        def post():return self.staff_post('login/',{'username':self.staff.username,'password':self.password})
        with patch.object(staff_auth,'authenticate',side_effect=wait):reset=self.held_thread(post,entered,release)
        self.assertEqual(StaffChallenge.objects.filter(consumed_at__isnull=True).count(),1)
        self.recover('release',basis_reset=reset)
        self.assertEqual(StaffChallenge.objects.filter(consumed_at__isnull=True).count(),0)
        self.fresh_staff()

    @override_settings(**STAFF_SETTINGS)
    def test_staff_verification_admitted_before_hold_cannot_use_the_old_code(self):
        self.setup_staff();code=self.staff_code();entered=Event();release=Event();original=effects._begin
        def wait(kind):
            identity=original(kind)
            if kind=='staff-verify':
                self.assertFalse(connection.in_atomic_block);entered.set()
                if not release.wait(8):raise RuntimeError('bounded staff verification wait')
            return identity
        with patch.object(effects,'_begin',side_effect=wait):
            reset=self.held_thread(lambda:self.staff_post('verify/',{'code':code}),entered,release)
        self.recover('release',basis_reset=reset)
        self.assertEqual(self.staff_post('verify/',{'code':code}).status_code,400)
        self.fresh_staff()

    def test_authentication_transaction_denial_is_fixed_and_does_not_create_a_challenge(self):
        with transaction.atomic():
            result,status=views.start_verification(None,'blocked@synthetic.invalid')
        self.assertEqual((result,status),({'error':'access_recovery_pending'},503))
        self.assertEqual(VerificationChallenge.objects.count(),0)
        self.assertEqual(LocalEffectAdmission.objects.count(),0)
