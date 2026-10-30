"""Real PostgreSQL and CSRF tests with private synthetic captures; no real mail."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import json
import re
from pathlib import Path
import stat
import tempfile
from threading import Barrier
from unittest.mock import patch
import uuid
from django.contrib.auth import get_user_model
from django.db import connections
from django.test import Client,TransactionTestCase,override_settings
from django.utils import timezone
from shop.catalog.models import ConfigurationDraft
from shop.catalog.rules import CATALOG
from .models import CustomerIdentity,VerificationChallenge
from .views import digest

BASE='/api/v1/customer/'
MALFORMED_TEXT_CASES=(('high','\ud800'),('last-high','\udbff'),('low','\udc00'),('last-low','\udfff'),
    ('embedded-high','synthetic\ud800text'),('embedded-low','synthetic\udc00text'),
    ('reversed','\udc00\ud800'),('emoji-and-high','🔑\ud800'))

def csrf_post(client,path,value):
    token=client.get(BASE+'session/').json()['csrf_token']
    return client.post(path,data=json.dumps(value),content_type='application/json',HTTP_X_CSRFTOKEN=token)

def captured_code(root,before):
    added=set(Path(root).iterdir())-before
    assert len(added)==1
    path=added.pop()
    assert stat.S_IMODE(path.stat().st_mode)==0o600
    match=re.search(r'^Verification code: ([A-Za-z0-9_-]+)$',path.read_text(),re.M)
    assert match
    return match[1]

def request_capture(client,root,email='engineer@synthetic.invalid'):
    before=set(Path(root).iterdir())
    response=csrf_post(client,BASE+'request-code/',{'email':email})
    assert response.status_code==200,response.content
    return captured_code(root,before)

class VerificationTests(TransactionTestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.settings=override_settings(LOCAL_CAPTURE_ROOT=self.directory.name)
        self.settings.enable();self.addCleanup(self.settings.disable)
        self.browser=Client(enforce_csrf_checks=True)

    def test_actual_verification_rotates_session_and_has_no_public_credentials(self):
        code=request_capture(self.browser,self.directory.name)
        old_key=self.browser.session.session_key
        old_csrf=self.browser.cookies['csrftoken'].value
        challenge=VerificationChallenge.objects.get()
        self.assertNotEqual(challenge.code_digest,code)
        self.assertEqual(challenge.code_digest,digest('code',code))
        self.assertNotIn(code,str(self.browser.session.items()))
        for endpoint in ('request-code/','verify/','logout/'):
            self.assertEqual(self.browser.get(BASE+endpoint).status_code,405)
        challenge.refresh_from_db();self.assertIsNone(challenge.consumed_at)
        response=csrf_post(self.browser,BASE+'verify/',{'code':code})
        self.assertEqual(response.status_code,200)
        self.assertTrue(response.json()['authenticated'])
        self.assertNotIn(code,response.content.decode())
        self.assertNotIn('engineer@synthetic.invalid',response.content.decode())
        self.assertNotEqual(old_key,self.browser.session.session_key)
        self.assertNotEqual(old_csrf,self.browser.cookies['csrftoken'].value)
        stale=self.browser.post(BASE+'logout/',data='{}',content_type='application/json',HTTP_X_CSRFTOKEN=old_csrf)
        self.assertEqual(stale.status_code,403)
        self.assertTrue(self.browser.get(BASE+'session/').json()['authenticated'])
        self.assertTrue(self.browser.cookies['sessionid']['httponly'])
        self.assertEqual(self.browser.cookies['sessionid']['samesite'],'Strict')
        self.assertFalse(self.browser.cookies['sessionid']['domain'])
        self.assertEqual(self.browser.get(BASE+'session/')['Cache-Control'],'no-store')
        challenge.refresh_from_db();self.assertIsNotNone(challenge.consumed_at)
        self.assertEqual(csrf_post(self.browser,BASE+'verify/',{'code':code}).status_code,400)
        self.assertFalse(CustomerIdentity.objects.get().user.has_usable_password())

    def test_wrong_browser_and_expiry(self):
        code=request_capture(self.browser,self.directory.name)
        stranger=Client(enforce_csrf_checks=True)
        self.assertEqual(csrf_post(stranger,BASE+'verify/',{'code':code}).status_code,400)
        self.assertEqual(VerificationChallenge.objects.get().attempts,0)
        VerificationChallenge.objects.update(expires_at=timezone.now()-timedelta(seconds=1))
        self.assertEqual(csrf_post(self.browser,BASE+'verify/',{'code':code}).status_code,400)
        self.assertEqual(CustomerIdentity.objects.count(),0)

    def test_attempt_and_request_limits(self):
        code=request_capture(self.browser,self.directory.name)
        for _ in range(5):self.assertEqual(csrf_post(self.browser,BASE+'verify/',{'code':'wrong'}).status_code,400)
        self.assertEqual(csrf_post(self.browser,BASE+'verify/',{'code':code}).status_code,400)
        self.assertEqual(VerificationChallenge.objects.get().attempts,5)
        for _ in range(2):request_capture(self.browser,self.directory.name)
        self.assertEqual(csrf_post(self.browser,BASE+'request-code/',{'email':'engineer@synthetic.invalid'}).status_code,429)
        self.assertEqual(csrf_post(self.browser,BASE+'request-code/',{'email':'different@synthetic.invalid'}).status_code,429)
        stranger=Client(enforce_csrf_checks=True)
        self.assertEqual(csrf_post(stranger,BASE+'request-code/',{'email':'engineer@synthetic.invalid'}).status_code,429)

    def test_malformed_json_code_returns_fixed_error_without_consuming_challenge(self):
        code=request_capture(self.browser,self.directory.name)
        self.browser.raise_request_exception=False
        session_key=self.browser.session.session_key
        for label,value in MALFORMED_TEXT_CASES:
            with self.subTest(kind=label):
                response=csrf_post(self.browser,BASE+'verify/',{'code':value})
                self.assertEqual(response.status_code,400)
                self.assertEqual(response.json(),{'error':'verification_failed'})
                self.assertEqual(response['Cache-Control'],'no-store')
                self.assertEqual(response['Referrer-Policy'],'no-referrer')
                challenge=VerificationChallenge.objects.get()
                self.assertEqual(challenge.attempts,0)
                self.assertIsNone(challenge.consumed_at)
                self.assertEqual(CustomerIdentity.objects.count(),0)
                self.assertEqual(self.browser.session.session_key,session_key)
                self.assertFalse(self.browser.get(BASE+'session/').json()['authenticated'])
        self.assertEqual(csrf_post(self.browser,BASE+'verify/',{'code':code}).status_code,200)
        self.assertEqual(CustomerIdentity.objects.count(),1)
        self.assertEqual(VerificationChallenge.objects.get().attempts,1)

    def test_well_formed_unicode_wrong_codes_keep_attempt_limits(self):
        code=request_capture(self.browser,self.directory.name)
        for value in ('café','文字','🔑'):
            response=csrf_post(self.browser,BASE+'verify/',{'code':value})
            self.assertEqual(response.status_code,400)
            self.assertEqual(response.json(),{'error':'verification_failed'})
        self.assertEqual(VerificationChallenge.objects.get().attempts,3)
        self.assertFalse(self.browser.get(BASE+'session/').json()['authenticated'])
        self.assertEqual(csrf_post(self.browser,BASE+'verify/',{'code':code}).status_code,200)
        self.assertEqual(VerificationChallenge.objects.get().attempts,4)

    def test_invalid_real_email_missing_capture_and_csrf(self):
        for email in ('person@example.com','bad\r\nBcc: x','x'*161,False):
            r=csrf_post(self.browser,BASE+'request-code/',{'email':email})
            self.assertEqual(r.status_code,400)
            self.assertEqual(r.json(),{'error':'synthetic_email_required'})
        self.assertEqual(VerificationChallenge.objects.count(),0)
        csrf=self.browser.get(BASE+'session/').json()['csrf_token']
        cross_origin=self.browser.post(BASE+'request-code/',data=json.dumps({'email':'a@synthetic.invalid'}),content_type='application/json',HTTP_X_CSRFTOKEN=csrf,HTTP_ORIGIN='https://attacker.invalid')
        self.assertEqual(cross_origin.status_code,403)
        self.assertEqual(VerificationChallenge.objects.count(),0)
        self.assertEqual(self.browser.post(BASE+'request-code/',data='{}',content_type='application/json').status_code,403)
        with override_settings(LOCAL_CAPTURE_ROOT=None):
            self.assertEqual(csrf_post(self.browser,BASE+'request-code/',{'email':'a@synthetic.invalid'}).status_code,503)
        self.assertEqual(VerificationChallenge.objects.count(),0)

    def test_code_replacement_and_same_email_reuses_exact_identity(self):
        old=request_capture(self.browser,self.directory.name)
        current=request_capture(self.browser,self.directory.name)
        self.assertEqual(csrf_post(self.browser,BASE+'verify/',{'code':old}).status_code,400)
        self.assertEqual(csrf_post(self.browser,BASE+'verify/',{'code':current}).status_code,200)
        user_id=CustomerIdentity.objects.get().user_id
        self.assertEqual(csrf_post(self.browser,BASE+'logout/',{}).status_code,200)
        # Email throttling allows the third request; logout cannot bypass it.
        third=request_capture(self.browser,self.directory.name)
        self.assertEqual(csrf_post(self.browser,BASE+'verify/',{'code':third}).status_code,200)
        self.assertEqual(CustomerIdentity.objects.count(),1)
        self.assertEqual(CustomerIdentity.objects.get().user_id,user_id)

    def test_historical_owner_drafts_logout_domain_isolation_and_closed_new_capture(self):
        from shop.catalog.tests import CASES
        code=request_capture(self.browser,self.directory.name)
        self.assertEqual(csrf_post(self.browser,BASE+'verify/',{'code':code}).status_code,200)
        value={'request_id':str(uuid.uuid4()),'revision':CATALOG['revision'],'configuration':CASES[0]['value']}
        response=csrf_post(self.browser,'/api/v1/configuration-drafts/',value)
        self.assertEqual(response.status_code,404)
        self.assertEqual(csrf_post(self.browser,'/api/v1/configuration-drafts/',value).status_code,404)
        # Prior private records survive the storefront revision. Build historical
        # fixture data internally, then keep the actual owner/logout/isolation
        # assertions rather than requiring a new paused-IP submission.
        from shop.catalog.rules import evaluate
        owner=CustomerIdentity.objects.get(email='engineer@synthetic.invalid').user
        saved=ConfigurationDraft.objects.create(owner=owner,request_id=uuid.UUID(value['request_id']),
            revision=value['revision'],configuration=value['configuration'],evaluation=evaluate(value['configuration']))
        identity=str(saved.pk)
        listed=self.browser.get('/api/v1/configuration-drafts/').json()['drafts']
        self.assertEqual([d['id'] for d in listed],[identity])
        self.assertNotIn('configuration',listed[0])
        other=Client(enforce_csrf_checks=True)
        other_code=request_capture(other,self.directory.name,'colleague@synthetic.invalid')
        self.assertEqual(csrf_post(other,BASE+'verify/',{'code':other_code}).status_code,200)
        self.assertEqual(other.get('/api/v1/configuration-drafts/').json()['drafts'],[])
        self.assertEqual(other.get('/api/v1/configuration-drafts/'+identity+'/').status_code,404)
        self.assertEqual(csrf_post(self.browser,BASE+'logout/',{}).status_code,200)
        self.assertEqual(self.browser.get('/api/v1/configuration-drafts/'+identity+'/').status_code,401)
        self.assertEqual(ConfigurationDraft.objects.count(),1)

    def test_unverified_session_staff_revocation_and_production_are_closed(self):
        user=get_user_model().objects.create_user(username='synthetic-unverified')
        self.browser.force_login(user)
        self.assertEqual(self.browser.get('/api/v1/configuration-drafts/').status_code,403)
        self.assertFalse(self.browser.get(BASE+'session/').json()['authenticated'])
        code=request_capture(self.browser,self.directory.name)
        self.assertEqual(csrf_post(self.browser,BASE+'verify/',{'code':code}).status_code,200)
        owner=CustomerIdentity.objects.get().user
        owner.is_staff=True;owner.save()
        self.assertFalse(self.browser.get(BASE+'session/').json()['authenticated'])
        self.assertEqual(self.browser.get('/api/v1/configuration-drafts/').status_code,403)
        with override_settings(SHOP_ENV='production'):
            for endpoint in ('session/','request-code/','verify/','logout/'):
                response=self.browser.get(BASE+endpoint) if endpoint=='session/' else self.browser.post(BASE+endpoint,data='{}',content_type='application/json',HTTP_X_CSRFTOKEN=self.browser.cookies['csrftoken'].value)
                self.assertEqual(response.status_code,404)

    def test_private_capture_never_reaches_logs_or_response(self):
        code=request_capture(self.browser,self.directory.name)
        with self.assertLogs('shop',level='INFO') as output:
            # Health event proves the logger executed while the code is used.
            self.browser.get('/health/live')
            r=csrf_post(self.browser,BASE+'verify/',{'code':code})
        self.assertNotIn(code,' '.join(output.output)+r.content.decode())

class VerificationRaceTests(TransactionTestCase):
    def test_independent_same_email_challenges_converge_on_one_identity(self):
        with tempfile.TemporaryDirectory() as directory,override_settings(LOCAL_CAPTURE_ROOT=directory):
            browsers=[Client(enforce_csrf_checks=True),Client(enforce_csrf_checks=True)]
            codes=[request_capture(browser,directory) for browser in browsers]
            barrier=Barrier(2)
            def attempt(index):
                try:
                    barrier.wait(timeout=5)
                    return csrf_post(browsers[index],BASE+'verify/',{'code':codes[index]}).status_code
                finally:connections.close_all()
            with ThreadPoolExecutor(max_workers=2) as pool:statuses=list(pool.map(attempt,range(2)))
            self.assertEqual(statuses,[200,200])
            self.assertEqual(CustomerIdentity.objects.count(),1)
            self.assertEqual(get_user_model().objects.count(),1)

    def test_concurrent_consumption_allows_exactly_one_login(self):
        with tempfile.TemporaryDirectory() as directory,override_settings(LOCAL_CAPTURE_ROOT=directory):
            client=Client(enforce_csrf_checks=True)
            code=request_capture(client,directory)
            cookies=client.cookies.copy()
            barrier=Barrier(2)
            def attempt(_):
                try:
                    browser=Client(enforce_csrf_checks=True);browser.cookies=cookies.copy()
                    barrier.wait(timeout=5)
                    r=csrf_post(browser,BASE+'verify/',{'code':code})
                    return r.status_code
                finally:connections.close_all()
            with ThreadPoolExecutor(max_workers=2) as pool:statuses=list(pool.map(attempt,range(2)))
            self.assertEqual(sorted(statuses),[200,400])
            self.assertEqual(CustomerIdentity.objects.count(),1)
            self.assertEqual(VerificationChallenge.objects.filter(consumed_at__isnull=False).count(),1)
