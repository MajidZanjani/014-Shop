"""Real PostgreSQL form journeys; synthetic private captures only."""
from datetime import timedelta
import tempfile
from urllib.parse import urlencode
from django.test import Client,TestCase,override_settings
from django.utils import timezone
from . import tests as access_tests
from .models import CustomerIdentity,VerificationChallenge

PATH='/purchase/access/'

class CustomerPortalTests(TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory();self.addCleanup(self.directory.cleanup)
        config=override_settings(LOCAL_CAPTURE_ROOT=self.directory.name)
        config.enable();self.addCleanup(config.disable)
        self.browser=Client(enforce_csrf_checks=True)

    def post(self,data,client=None):
        client=client or self.browser
        client.get(PATH)
        return client.post(PATH,data=urlencode(data),content_type='application/x-www-form-urlencoded',HTTP_X_CSRFTOKEN=client.cookies['csrftoken'].value)

    def capture(self):
        from pathlib import Path
        before=set(Path(self.directory.name).iterdir())
        response=self.post({'action':'request','email':'portal@synthetic.invalid'})
        self.assertEqual(response.status_code,303)
        self.assertEqual(response['Location'],PATH)
        return access_tests.captured_code(self.directory.name,before)

    def test_form_journey_rotates_credentials_and_never_reflects_private_input(self):
        page=self.browser.get(PATH)
        self.assertContains(page,'Request a code')
        self.assertNotContains(page,'<script')
        code=self.capture()
        old_key=self.browser.session.session_key;old_csrf=self.browser.cookies['csrftoken'].value
        page=self.browser.get(PATH)
        self.assertContains(page,'Verify code')
        self.assertNotContains(page,code);self.assertNotContains(page,'portal@synthetic.invalid')
        self.assertNotIn(code,str(dict(self.browser.session)))
        response=self.post({'action':'verify','code':code})
        self.assertEqual(response.status_code,303);self.assertEqual(response['Location'],PATH)
        self.assertNotEqual(old_key,self.browser.session.session_key)
        self.assertNotEqual(old_csrf,self.browser.cookies['csrftoken'].value)
        page=self.browser.get(PATH)
        self.assertContains(page,'Your customer access is verified.')
        self.assertNotContains(page,'portal@synthetic.invalid');self.assertNotContains(page,code)
        self.assertEqual(self.browser.get('/purchase/business/').status_code,200)
        self.assertEqual(page['Cache-Control'],'no-store');self.assertEqual(page['Referrer-Policy'],'same-origin')
        self.assertIn("form-action 'self'",page['Content-Security-Policy'])
        directives=dict(part.strip().split(' ',1) for part in page['Content-Security-Policy'].split(';'))
        self.assertEqual(directives,{'default-src':"'none'",'style-src':"'self'",'form-action':"'self'",
                                     'frame-ancestors':"'none'",'base-uri':"'none'"})
        self.assertIn('Cookie',page['Vary'])
        self.assertEqual(self.browser.post(PATH,data={'action':'logout'},HTTP_X_CSRFTOKEN=old_csrf).status_code,403)
        self.assertEqual(self.post({'action':'logout'}).status_code,303)
        self.assertFalse(self.browser.get(access_tests.BASE+'session/').json()['authenticated'])
        self.assertEqual(self.post({'action':'verify','code':code}).status_code,400)
        self.assertEqual(CustomerIdentity.objects.count(),1)

    def test_api_and_form_share_attempt_and_request_limits(self):
        code=self.capture()
        for _ in range(4):
            self.assertEqual(access_tests.csrf_post(self.browser,access_tests.BASE+'verify/',{'code':'wrong'}).status_code,400)
        self.assertEqual(self.post({'action':'verify','code':'wrong'}).status_code,400)
        self.assertEqual(self.post({'action':'verify','code':code}).status_code,400)
        self.assertEqual(VerificationChallenge.objects.get().attempts,5)
        for _ in range(2):access_tests.request_capture(self.browser,self.directory.name)
        self.assertEqual(self.post({'action':'request','email':'new@synthetic.invalid'}).status_code,429)
        self.assertEqual(CustomerIdentity.objects.count(),0)

    def test_api_code_can_be_verified_by_form_with_same_browser_only(self):
        code=access_tests.request_capture(self.browser,self.directory.name)
        other=Client(enforce_csrf_checks=True)
        self.assertEqual(self.post({'action':'verify','code':code},other).status_code,400)
        self.assertEqual(VerificationChallenge.objects.get().attempts,0)
        self.assertEqual(self.post({'action':'verify','code':code}).status_code,303)
        self.assertTrue(self.browser.get(access_tests.BASE+'session/').json()['authenticated'])

    def test_expired_form_code_cannot_create_identity(self):
        code=self.capture()
        VerificationChallenge.objects.update(expires_at=timezone.now()-timedelta(seconds=1))
        self.assertEqual(self.post({'action':'verify','code':code}).status_code,400)
        self.assertEqual(CustomerIdentity.objects.count(),0)

    def test_strict_forms_reject_ambiguous_unexpected_and_oversized_inputs(self):
        for values in (
            [('action','request'),('email','one@synthetic.invalid'),('email','two@synthetic.invalid')],
            [('action','request'),('email','one@synthetic.invalid'),('next','https://example.invalid/private')],
            [('action','logout'),('code','private-code')],
            [('action','verify'),('code','x'*1100)],
            [('action','unknown')],
        ):
            response=self.post(values)
            self.assertEqual(response.status_code,400)
            self.assertNotContains(response,'private-code',status_code=400)
            self.assertNotContains(response,'example.invalid',status_code=400)
        self.assertEqual(self.browser.get(PATH+'?next=/private').status_code,400)
        self.assertEqual(VerificationChallenge.objects.count(),0)
        token=self.browser.cookies['csrftoken'].value
        self.assertEqual(self.browser.post(PATH,data='{}',content_type='application/json',HTTP_X_CSRFTOKEN=token).status_code,400)
        self.assertEqual(self.browser.post(PATH,{'action':'request','email':'x@synthetic.invalid'}).status_code,403)
        self.assertEqual(self.browser.put(PATH,HTTP_X_CSRFTOKEN=token).status_code,405)
        self.assertEqual(self.browser.post(access_tests.BASE+'request-code/',data={'email':'x@synthetic.invalid'},HTTP_X_CSRFTOKEN=token).status_code,400)

    def test_real_address_and_missing_private_capture_fail_without_mutation(self):
        response=self.post({'action':'request','email':'private@example.com'})
        self.assertEqual(response.status_code,400);self.assertNotContains(response,'private@example.com',status_code=400)
        with override_settings(LOCAL_CAPTURE_ROOT=None):
            self.assertEqual(self.post({'action':'request','email':'x@synthetic.invalid'}).status_code,503)
        self.assertEqual(VerificationChallenge.objects.count(),0)
        self.assertNotIn('shop_challenge',self.browser.session)

    def test_nonlocal_environment_and_privileged_user_are_unavailable(self):
        for env in ('production','bank-sandbox'):
            with override_settings(SHOP_ENV=env):self.assertEqual(self.browser.get(PATH).status_code,404)
        code=self.capture();self.assertEqual(self.post({'action':'verify','code':code}).status_code,303)
        user=CustomerIdentity.objects.get().user;user.is_staff=True;user.save(update_fields=['is_staff'])
        self.assertEqual(self.browser.get(PATH).status_code,403)
