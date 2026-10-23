"""Local exact-snapshot staff decisions, with real PostgreSQL arbitration."""
from concurrent.futures import ThreadPoolExecutor
import json
import re
from threading import Barrier
from unittest.mock import patch
from urllib.parse import urlencode
import uuid
from django.contrib.auth import get_user_model
from django.db import connections
from django.test import Client, TransactionTestCase, override_settings
from django.utils import timezone
from shop.catalog.models import CartSnapshot, QuotationReview
from shop.catalog.rules import CATALOG
from . import staff_tests
from .models import StaffCredential, StaffQuotationGrant

@override_settings(**staff_tests.STAFF_SETTINGS)
class ReviewTests(TransactionTestCase):
    setUp=staff_tests.StaffTests.setUp
    post=staff_tests.StaffTests.post
    challenge=staff_tests.StaffTests.challenge
    authenticated=staff_tests.StaffTests.authenticated
    grant=staff_tests.StaffTests.grant
    def prepare(self):
        self.authenticated();self.grant()
        self.detail='/staff/quotation-requests/'+str(self.quotation.id)+'/'
        self.route='quotation-requests/'+str(self.quotation.id)+'/reviews/'
        value=self.browser.get(self.detail).json()
        self.value={'request_id':str(uuid.uuid4()),'expected_review_version':value['review_version'],
                    'snapshot_digest':value['snapshot_digest'],'decision':'needs_information'}
    def submit(self,value=None,client=None):return self.post(self.route,self.value if value is None else value,client)
    def test_attribution_exact_retry_correction_and_original_snapshot(self):
        self.prepare();first=self.submit();self.assertEqual(first.status_code,201)
        row=QuotationReview.objects.get();self.assertEqual(row.reviewer,self.user)
        self.assertEqual(row.reviewer_generation,self.credential.generation)
        self.assertLess((timezone.now()-row.mfa_verified_at).total_seconds(),10)
        self.assertFalse(first.json()['checkout_enabled']);self.assertFalse(first.json()['acceptance_enabled'])
        self.assertEqual(self.submit().json(),first.json())
        changed=dict(self.value,request_id=str(uuid.uuid4()),expected_review_version=1,decision='ready_for_commercial_review')
        self.assertEqual(self.submit(changed).status_code,201)
        cart=self.quotation.cart
        CartSnapshot.objects.create(cart=cart,version=2,request_id=uuid.uuid4(),catalog_revision=CATALOG['revision'],lines=[],evaluation={})
        cart.version=2;cart.save()
        with patch.dict(CATALOG,revision='f'*64):
            replay=self.submit();self.assertEqual(replay.status_code,200)
            self.assertEqual(replay.json()['review'],first.json()['review'])
            self.assertEqual(replay.json()['current_review_version'],2)
            self.assertEqual(self.submit(dict(changed,request_id=str(uuid.uuid4()),expected_review_version=2)).json()['error'],'stale_catalog')
        self.assertEqual(self.submit(dict(self.value,decision='declined')).status_code,409)
        self.assertEqual(self.submit(dict(self.value,request_id=str(uuid.uuid4()))).status_code,409)
        detail=self.browser.get(self.detail).json()
        self.assertEqual(detail['version'],1);self.assertEqual(detail['lines'],self.quotation.snapshot.lines)
        self.assertEqual([r['decision'] for r in detail['reviews']],['ready_for_commercial_review','needs_information'])
        self.assertEqual(QuotationReview.objects.count(),2)
    def test_no_js_form_and_exact_browser_resubmission(self):
        self.prepare()
        page=self.browser.get(self.detail,HTTP_ACCEPT='text/html')
        self.assertContains(page,'Record internal review decision')
        fields=dict(re.findall(r'<input[^>]*name="([^"]+)"[^>]*value="([^"]*)"',page.content.decode()))
        fields['decision']='ready_for_commercial_review'
        for _ in range(2):
            result=self.browser.post('/staff/'+self.route,data=urlencode(fields),content_type='application/x-www-form-urlencoded')
            self.assertEqual(result.status_code,303)
            self.assertEqual(result['Location'],self.detail)
        self.assertEqual(QuotationReview.objects.count(),1)
        stale=dict(fields,request_id=str(uuid.uuid4()),decision='declined')
        error=self.browser.post('/staff/'+self.route,data=urlencode(stale),content_type='application/x-www-form-urlencoded')
        self.assertEqual(error.status_code,409)
        self.assertContains(error,'Another decision was recorded',status_code=409)
        self.assertContains(error,'Reload captured request and review history',status_code=409)
        self.assertEqual(error['Cache-Control'],'no-store')
        html=self.browser.get(self.detail,HTTP_ACCEPT='text/html')
        self.assertContains(html,'Ready for commercial review (offer not approved)')
        self.assertContains(html,'Offer approval pending')
        self.assertEqual(html['Cache-Control'],'no-store')
        with patch.dict(CATALOG,revision='f'*64):
            html=self.browser.get(self.detail,HTTP_ACCEPT='text/html')
            self.assertContains(html,'A new current request is required')
            self.assertNotContains(html,'Record internal review decision')
    def test_snapshot_tamper_and_closed_payload(self):
        self.prepare()
        self.assertEqual(self.submit(dict(self.value,snapshot_digest='0'*64)).json()['error'],'snapshot_changed')
        for value in [dict(self.value,price=1),dict(self.value,decision='approved'),dict(self.value,decision=['declined']),
                      dict(self.value,expected_review_version=True),dict(self.value,expected_review_version=-1),
                      dict(self.value,request_id=4),dict(self.value,snapshot_digest='bad')]:
            self.assertEqual(self.submit(value).status_code,400)
        client=Client(HTTP_HOST='staff.localhost');client.cookies=self.browser.cookies.copy()
        for raw in ['NaN','{"request_id":1,"request_id":2}','x'*1025]:
            self.assertEqual(client.post('/staff/'+self.route,data=raw,content_type='application/json').status_code,400)
        self.assertEqual(self.submit(dict(self.value),client=self.browser).status_code,201)
        self.assertEqual(self.submit(dict(self.value,expected_review_version=1)).status_code,409)
    def test_every_write_rechecks_mfa_assignment_and_scope(self):
        self.prepare()
        self.assertEqual(self.browser.get('/staff/'+self.route).status_code,405)
        self.assertEqual(self.browser.delete('/staff/'+self.route).status_code,403)
        self.assertEqual(self.browser.post('/staff/'+self.route,data=json.dumps(self.value),content_type='application/json').status_code,403)
        for mode in ['production','bank-sandbox']:
            with override_settings(SHOP_ENV=mode):
                self.assertEqual(self.browser.post('/staff/'+self.route,data=json.dumps(self.value),content_type='application/json').status_code,404)
        self.assertEqual(self.browser.post('/staff/'+self.route,data=json.dumps(self.value),content_type='application/json',HTTP_HOST='shop.xspi.pro').status_code,404)
        unchecked=Client(HTTP_HOST='staff.localhost');unchecked.cookies=self.browser.cookies.copy()
        self.assertEqual(unchecked.delete('/staff/'+self.route).status_code,405)
        original_route=self.route
        self.route='quotation-requests/'+str(uuid.uuid4())+'/reviews/'
        self.assertEqual(self.submit().status_code,404);self.route=original_route
        StaffQuotationGrant.objects.all().delete()
        self.assertEqual(self.submit().status_code,404);self.grant()
        session=self.browser.session;marker=session['shop_staff_mfa'];marker['verified_at']=timezone.now().timestamp()-301;session['shop_staff_mfa']=marker;session.save()
        self.assertEqual(self.submit().status_code,403)
        marker['verified_at']=timezone.now().timestamp();session['shop_staff_mfa']=marker;session.save()
        self.credential.generation=uuid.uuid4();self.credential.save()
        self.assertEqual(self.submit().status_code,403)
        self.assertEqual(QuotationReview.objects.count(),0)
    def second_actor(self):
        user=get_user_model().objects.create_user(username='other-reviewer',is_staff=True)
        credential=StaffCredential.objects.create(user=user)
        StaffQuotationGrant.objects.create(user=user,quotation=self.quotation)
        client=Client(HTTP_HOST='staff.localhost');client.force_login(user)
        # Explicit post-MFA fixture for actor-binding/arbitration tests only.
        session=client.session;session['shop_staff_mfa']={'generation':str(credential.generation),'verified_at':timezone.now().timestamp()};session.save()
        return client
    def test_key_cannot_be_claimed_by_another_reviewer(self):
        self.prepare();self.assertEqual(self.submit().status_code,201)
        client=self.second_actor()
        self.assertEqual(self.submit(client=client).status_code,409)
        self.assertEqual(self.submit(dict(self.value,request_id=str(uuid.uuid4()),expected_review_version=1,decision='declined'),client=client).status_code,201)
        self.assertEqual(QuotationReview.objects.count(),2)
    def race(self,same):
        self.prepare()
        clients=[Client(HTTP_HOST='staff.localhost'),Client(HTTP_HOST='staff.localhost')]
        for client in clients:client.cookies=self.browser.cookies.copy()
        if not same:clients[1]=self.second_actor()
        barrier=Barrier(2)
        def run(index):
            try:
                value=dict(self.value)
                if not same:value['request_id']=str(uuid.uuid4());value['decision']='declined' if index else 'needs_information'
                barrier.wait(timeout=10)
                result=clients[index].post('/staff/'+self.route,data=json.dumps(value),content_type='application/json')
                return result.status_code
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(run,range(2)))
        self.assertEqual(sorted(results),[200,201] if same else [201,409])
        self.assertEqual(QuotationReview.objects.count(),1)
        self.quotation.refresh_from_db();self.assertEqual(self.quotation.review_version,1)
    def test_concurrent_exact_retry(self):self.race(True)
    def test_concurrent_reviewers(self):self.race(False)

    def test_staff_write_is_visible_only_as_owner_safe_status(self):
        from shop.catalog.tests import verified_login
        self.prepare()
        result=self.submit(dict(self.value,decision='ready_for_commercial_review'))
        self.assertEqual(result.status_code,201)
        middleware=[name for name in staff_tests.STAFF_SETTINGS['MIDDLEWARE'] if name not in
                    ('shop.access.staff_middleware.StaffHostMiddleware','shop.access.staff_middleware.StaffMFAMiddleware')]
        with override_settings(ROOT_URLCONF='shop.urls',LOCAL_STAFF_ENABLED=False,MIDDLEWARE=middleware,
                               SESSION_COOKIE_NAME='sessionid',CSRF_COOKIE_NAME='csrftoken'):
            customer=Client(HTTP_HOST='127.0.0.1')
            verified_login(customer,self.quotation.cart.owner)
            path='/api/v1/quotation-requests/'+str(self.quotation.id)+'/'
            detail=customer.get(path).json()
            listing=customer.get('/api/v1/quotation-requests/').json()['requests'][0]
            self.assertEqual(detail['review_status']['code'],'ready_for_commercial_review')
            self.assertEqual(detail['review_status']['version'],1)
            self.assertEqual(listing['review_status'],detail['review_status'])
            self.assertEqual(detail['lines'],self.quotation.snapshot.lines)
            self.assertFalse(detail['checkout_enabled']);self.assertFalse(detail['acceptance_enabled'])
            for key in ['reviews','reviewer_id','reviewer_generation','mfa_verified_at','snapshot_digest']:
                self.assertNotIn(key,json.dumps(detail))
            another=get_user_model().objects.create_user(username='unrelated-customer')
            verified_login(customer,another)
            self.assertEqual(customer.get(path).status_code,404)
            self.assertEqual(customer.get('/api/v1/quotation-requests/').json()['requests'],[])
