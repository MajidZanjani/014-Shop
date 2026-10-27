"""Synthetic staff MFA, host/cookie isolation and explicit resource grants on real PG."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from base64 import b64encode
from hashlib import sha256
import io
import json
from pathlib import Path
import re
import stat
import tempfile
from threading import Barrier
from urllib.parse import urlencode
from unittest.mock import patch
import uuid
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connections
from django.test import Client, TransactionTestCase, override_settings
from django.utils import timezone
from shop.catalog.cart_tests import CASES
from shop.catalog.cart_rules import evaluate_cart
from shop.catalog.models import DraftCart,CartSnapshot,QuotationRequest
from shop.catalog.rules import CATALOG
from .models import StaffCredential,StaffChallenge,StaffQuotationGrant

STAFF_SETTINGS=dict(ROOT_URLCONF='shop.staff_urls',LOCAL_STAFF_ENABLED=True,
    ALLOWED_HOSTS=['staff.localhost','shop.xspi.pro','shop-admin.xspi.pro','127.0.0.1'],
    SESSION_COOKIE_NAME='shop_staff_sessionid',CSRF_COOKIE_NAME='shop_staff_csrftoken',
    MIDDLEWARE=[settings.MIDDLEWARE[0],'shop.access.staff_middleware.StaffHostMiddleware',*settings.MIDDLEWARE[1:],'shop.access.staff_middleware.StaffMFAMiddleware'],
    TEMPLATES=[{'BACKEND':'django.template.backends.django.DjangoTemplates','APP_DIRS':True}])
BASE='/staff/'

@override_settings(**STAFF_SETTINGS)
class StaffTests(TransactionTestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory();self.addCleanup(self.directory.cleanup)
        self.capture=override_settings(LOCAL_STAFF_CAPTURE_ROOT=self.directory.name);self.capture.enable();self.addCleanup(self.capture.disable)
        self.password='synthetic-password-only'
        self.user=get_user_model().objects.create_user(username='reviewer',password=self.password,is_staff=True)
        self.credential=StaffCredential.objects.create(user=self.user)
        owner=get_user_model().objects.create_user(username='customer')
        cart=DraftCart.objects.create(owner=owner,version=1)
        snapshot=CartSnapshot.objects.create(cart=cart,version=1,request_id=uuid.uuid4(),catalog_revision=CATALOG['revision'],lines=CASES[3]['lines'],evaluation=evaluate_cart(CASES[3]['lines']))
        self.quotation=QuotationRequest.objects.create(cart=cart,snapshot=snapshot,request_id=uuid.uuid4())
        self.browser=Client(enforce_csrf_checks=True,HTTP_HOST='staff.localhost')
    def post(self,path,value,client=None):
        client=client or self.browser
        token=client.get(BASE+'session/').json()['csrf_token']
        return client.post(BASE+path,data=json.dumps(value),content_type='application/json',HTTP_X_CSRFTOKEN=token)
    def challenge(self,client=None):
        before=set(Path(self.directory.name).iterdir())
        response=self.post('login/',{'username':'reviewer','password':self.password},client)
        self.assertEqual(response.status_code,200)
        files=set(Path(self.directory.name).iterdir())-before;self.assertEqual(len(files),1)
        path=files.pop();self.assertEqual(stat.S_IMODE(path.stat().st_mode),0o600)
        code=re.search(r'^Code: (.+)$',path.read_text(),re.M)[1]
        self.assertNotIn(code,response.content.decode());return code
    def authenticated(self):
        code=self.challenge();self.assertEqual(self.post('verify/',{'code':code}).status_code,200)
    def grant(self):StaffQuotationGrant.objects.create(user=self.user,quotation=self.quotation)
    def test_two_factors_session_rotation_cookie_and_no_js_forms(self):
        first=self.browser.get(BASE);self.assertEqual(first.status_code,200)
        self.assertContains(first,'type="password"');self.assertContains(first,'csrfmiddlewaretoken')
        self.assertIn("frame-ancestors 'none'",first['Content-Security-Policy'])
        styles=re.findall(r'<style>(.*?)</style>',first.content.decode(),re.S)
        self.assertEqual(len(styles),1)
        from shop.catalog.presentation import CSS
        self.assertEqual(styles[0],CSS)
        style_hash=b64encode(sha256(styles[0].encode('utf-8')).digest()).decode('ascii')
        directives=dict(part.strip().split(' ',1) for part in first['Content-Security-Policy'].split(';'))
        self.assertEqual(directives,{'default-src':"'none'",'style-src':"'sha256-"+style_hash+"'",
                                     'form-action':"'self'",'frame-ancestors':"'none'",'base-uri':"'none'"})
        self.assertEqual(self.browser.get('/purchase/assets/shop.css').status_code,403)
        code=self.challenge();old_key=self.browser.session.session_key;old_csrf=self.browser.cookies['shop_staff_csrftoken'].value
        self.assertEqual(self.browser.get(BASE+'quotation-requests/').status_code,403)
        self.assertFalse(self.browser.get(BASE+'session/').json()['authenticated'])
        self.assertEqual(self.browser.get('/purchase/assets/shop.css').status_code,403)
        response=self.post('verify/',{'code':code});self.assertEqual(response.status_code,200)
        self.assertNotEqual(old_key,self.browser.session.session_key)
        self.assertNotEqual(old_csrf,self.browser.cookies['shop_staff_csrftoken'].value)
        self.assertEqual(self.browser.get('/purchase/assets/shop.css').status_code,200)
        self.assertTrue(self.browser.cookies['shop_staff_sessionid']['httponly'])
        self.assertFalse(self.browser.cookies['shop_staff_sessionid']['domain'])
        self.assertEqual(self.browser.cookies['shop_staff_sessionid']['samesite'],'Strict')
        self.assertNotIn(code,str(self.browser.session.items()))
        self.assertEqual(self.post('verify/',{'code':code}).status_code,400)
        self.assertTrue(self.browser.get(BASE+'session/').json()['authenticated'])
        self.assertEqual(self.browser.post(BASE+'logout/',data='{}',content_type='application/json',HTTP_X_CSRFTOKEN=old_csrf).status_code,403)
        self.assertEqual(self.post('logout/',{}).status_code,200)
        self.assertFalse(self.browser.get(BASE+'session/').json()['authenticated'])
    def test_explicit_resource_grants_no_staff_or_superuser_bypass(self):
        self.authenticated()
        detail=BASE+'quotation-requests/'+str(self.quotation.id)+'/'
        self.assertEqual(self.browser.get(BASE+'quotation-requests/').json()['requests'],[])
        self.assertEqual(self.browser.get(detail).status_code,404)
        self.user.is_superuser=True;self.user.save()
        self.assertEqual(self.browser.get(detail).status_code,404)
        self.grant()
        result=self.browser.get(detail);self.assertEqual(result.status_code,200)
        self.assertEqual(result.json()['lines'],self.quotation.snapshot.lines)
        self.assertFalse(result.json()['checkout_enabled']);self.assertFalse(result.json()['acceptance_enabled'])
        self.assertEqual(result['Cache-Control'],'no-store')
        self.assertEqual(self.browser.get(BASE+'quotation-requests/').json()['requests'][0]['id'],str(self.quotation.id))
        html=self.browser.get(detail,HTTP_ACCEPT='text/html');self.assertContains(html,'Captured quotation request')
        self.assertContains(html,'Prices and rights pending');self.assertNotContains(html,'type="password"')
        self.assertContains(self.browser.get(BASE+'quotation-requests/',HTTP_ACCEPT='text/html'),'Assigned quotation requests')
        StaffQuotationGrant.objects.all().delete()
        self.assertEqual(self.browser.get(detail).status_code,404)
        self.assertEqual(self.post('quotation-requests/'+str(self.quotation.id)+'/',{}).status_code,405)
    def test_recent_expiry_credential_revocation_and_inactive_staff(self):
        self.authenticated();self.grant()
        session=self.browser.session;marker=session['shop_staff_mfa'];marker['verified_at']=timezone.now().timestamp()-301;session['shop_staff_mfa']=marker;session.save()
        self.assertEqual(self.browser.get(BASE+'quotation-requests/').status_code,403)
        self.assertTrue(self.browser.get(BASE+'session/').json()['authenticated'])
        marker['verified_at']=timezone.now().timestamp()-901;session['shop_staff_mfa']=marker;session.save()
        self.assertFalse(self.browser.get(BASE+'session/').json()['authenticated'])
        self.authenticated();self.credential.generation=uuid.uuid4();self.credential.save()
        self.assertEqual(self.browser.get(BASE+'quotation-requests/').status_code,403)
        self.authenticated();self.user.is_active=False;self.user.save()
        self.assertEqual(self.browser.get(BASE+'quotation-requests/').status_code,403)
    def test_challenge_binding_expiry_attempts_and_revocation(self):
        code=self.challenge();stranger=Client(HTTP_HOST='staff.localhost')
        self.assertEqual(self.post('verify/',{'code':code},stranger).status_code,400)
        self.assertEqual(StaffChallenge.objects.get().attempts,0)
        for _ in range(5):self.assertEqual(self.post('verify/',{'code':'wrong'}).status_code,400)
        self.assertEqual(self.post('verify/',{'code':code}).status_code,400)
        code=self.challenge();StaffChallenge.objects.filter(consumed_at=None).update(expires_at=timezone.now()-timedelta(seconds=1))
        self.assertEqual(self.post('verify/',{'code':code}).status_code,400)
        code=self.challenge();self.credential.generation=uuid.uuid4();self.credential.save()
        self.assertEqual(self.post('verify/',{'code':code}).status_code,400)
    def test_password_limits_and_customer_account_cannot_enroll(self):
        for _ in range(5):self.assertEqual(self.post('login/',{'username':'reviewer','password':'wrong'}).status_code,400)
        self.assertEqual(self.post('login/',{'username':'reviewer','password':self.password}).status_code,429)
        customer=get_user_model().objects.get(username='customer');customer.set_password(self.password);customer.save()
        self.assertEqual(self.post('login/',{'username':'customer','password':self.password}).status_code,400)
        self.assertEqual(StaffChallenge.objects.count(),0)
    def test_csrf_parsing_hosts_and_production_closed(self):
        self.assertEqual(self.browser.post(BASE+'login/',data='{}',content_type='application/json').status_code,403)
        for payload in [{'username':'reviewer','password':True},{'username':'reviewer','password':self.password,'is_staff':True}]:
            self.assertEqual(self.post('login/',payload).status_code,400)
        client=Client(HTTP_HOST='staff.localhost')
        for raw in ['NaN','{"username":1,"username":2}','x'*1025]:
            self.assertEqual(client.post(BASE+'login/',data=raw,content_type='application/json').status_code,400)
        for host in ['shop.xspi.pro','shop-admin.xspi.pro','127.0.0.1']:
            for path in [BASE,BASE+'session/',BASE+'quotation-requests/','/admin/']:
                self.assertEqual(client.get(path,HTTP_HOST=host).status_code,404)
        for mode in ['production','bank-sandbox']:
            with override_settings(SHOP_ENV=mode):
                self.assertEqual(client.get(BASE).status_code,404)
                self.assertEqual(client.post(BASE+'login/',data='{}',content_type='application/json').status_code,404)
        with override_settings(ROOT_URLCONF='shop.urls',MIDDLEWARE=settings.MIDDLEWARE[0:1]+settings.MIDDLEWARE[2: -1]):
            self.assertEqual(client.get(BASE,HTTP_HOST='shop.xspi.pro').status_code,404)
    def test_operator_reset_revocation_private_credentials_and_grants(self):
        self.authenticated();self.grant();code=self.challenge()
        before=set(Path(self.directory.name).iterdir());output=io.StringIO()
        call_command('local_staff','reset',username='reviewer',capture_root=self.directory.name,stdout=output)
        path=(set(Path(self.directory.name).iterdir())-before).pop()
        password=re.search(r'^Password: (.+)$',path.read_text(),re.M)[1]
        self.assertNotIn(password,output.getvalue());self.assertEqual(stat.S_IMODE(path.stat().st_mode),0o600)
        self.assertEqual(StaffQuotationGrant.objects.count(),0)
        self.assertEqual(self.post('verify/',{'code':code}).status_code,400)
        self.password=password;self.authenticated()
        call_command('local_staff','grant',username='reviewer',quotation=str(self.quotation.id),stdout=output)
        self.assertEqual(self.browser.get(BASE+'quotation-requests/').json()['requests'][0]['id'],str(self.quotation.id))
        call_command('local_staff','revoke-grant',username='reviewer',quotation=str(self.quotation.id),stdout=output)
        self.assertEqual(self.browser.get(BASE+'quotation-requests/').json()['requests'],[])
        call_command('local_staff','revoke',username='reviewer',stdout=output)
        self.assertEqual(self.browser.get(BASE+'quotation-requests/').status_code,403)
        with override_settings(SHOP_ENV='production'):
            with self.assertRaises(CommandError):call_command('local_staff','reset',username='reviewer',capture_root=self.directory.name,stdout=output)
        with self.assertRaises(CommandError):call_command('local_staff','provision',username='customer',capture_root=self.directory.name,stdout=output)
    def test_concurrent_code_consumption(self):
        code=self.challenge();clients=[Client(HTTP_HOST='staff.localhost'),Client(HTTP_HOST='staff.localhost')]
        for client in clients:client.cookies=self.browser.cookies.copy()
        barrier=Barrier(2)
        def run(index):
            try:
                barrier.wait(timeout=10)
                return clients[index].post(BASE+'verify/',data=json.dumps({'code':code}),content_type='application/json').status_code
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(run,range(2)))
        self.assertEqual(sorted(results),[200,400])
        self.assertEqual(StaffChallenge.objects.get().attempts,1)

    def form_post(self,path,values):
        self.browser.get(BASE)
        return self.browser.post(BASE+path,data=urlencode(values),content_type='application/x-www-form-urlencoded',
            HTTP_X_CSRFTOKEN=self.browser.cookies['shop_staff_csrftoken'].value)

    def test_form_error_recovery_keeps_credentials_private_and_mfa_closed(self):
        bad_password='private-invalid-password'
        failed=self.form_post('login/',{'username':'reviewer','password':bad_password})
        self.assertEqual(failed.status_code,400)
        self.assertContains(failed,'role="alert"',status_code=400)
        self.assertNotContains(failed,bad_password,status_code=400)
        self.assertNotContains(failed,'reviewer',status_code=400)
        self.assertEqual(failed['Cache-Control'],'no-store')
        self.assertEqual(self.browser.get(BASE+'quotation-requests/').status_code,403)
        malformed=self.form_post('login/',[('username','reviewer'),('username','other'),('password',self.password)])
        self.assertEqual(malformed.status_code,400)
        self.assertContains(malformed,'role="alert"',status_code=400)
        self.assertNotContains(malformed,self.password,status_code=400)
        code=self.challenge()
        bad_code='private-invalid-code'
        failed=self.form_post('verify/',{'code':bad_code})
        self.assertEqual(failed.status_code,400)
        self.assertContains(failed,'role="alert"',status_code=400)
        self.assertContains(failed,'name="code"',status_code=400)
        self.assertNotContains(failed,bad_code,status_code=400)
        self.assertNotContains(failed,code,status_code=400)
        self.assertNotContains(failed,'Both local factors verified.',status_code=400)
        challenge=StaffChallenge.objects.get()
        self.assertEqual(challenge.attempts,1);self.assertIsNone(challenge.consumed_at)
        self.assertFalse(self.browser.get(BASE+'session/').json()['authenticated'])
        self.assertEqual(self.browser.get(BASE+'quotation-requests/').status_code,403)
        self.assertEqual(self.form_post('verify/',{'code':code}).status_code,302)
        self.assertTrue(self.browser.get(BASE+'session/').json()['authenticated'])
        self.assertEqual(self.form_post('verify/',{'code':code}).status_code,400)
        self.assertTrue(self.browser.get(BASE+'session/').json()['authenticated'])

    def test_form_capture_failure_renders_after_transaction_rollback(self):
        session=self.browser.session;session['synthetic_prior_state']='retained';session.save()
        with patch('shop.access.staff_auth.LocalStorage',side_effect=OSError('private-capture-failure')):
            response=self.form_post('login/',{'username':'reviewer','password':self.password})
        self.assertEqual(response.status_code,503)
        self.assertContains(response,'role="alert"',status_code=503)
        self.assertNotContains(response,self.password,status_code=503)
        self.assertNotContains(response,'private-capture-failure',status_code=503)
        self.assertEqual(StaffChallenge.objects.count(),0)
        from .models import StaffLoginThrottle
        self.assertEqual(StaffLoginThrottle.objects.count(),0)
        self.assertEqual(self.browser.session['synthetic_prior_state'],'retained')
        self.assertFalse(self.browser.get(BASE+'session/').json()['authenticated'])
