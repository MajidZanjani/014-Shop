"""Business-scope isolation, append-only bindings and real PostgreSQL races."""
from concurrent.futures import ThreadPoolExecutor
import io
import json
from threading import Barrier
from urllib.parse import urlencode
from unittest.mock import patch
import uuid
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connections
from django.test import Client, TransactionTestCase, override_settings
from shop.access import staff_tests
from shop.access.models import StaffQuotationGrant
from shop.access.quotation_review import snapshot_digest
from . import business_rules as rules
from .models import BusinessDraft, BusinessDraftSnapshot, QuotationBusinessScope, QuotationBusinessKey, QuotationReview, QuotationRequest
from .tests import verified_login

@override_settings(**staff_tests.STAFF_SETTINGS)
class BusinessBindingTests(TransactionTestCase):
    post=staff_tests.StaffTests.post
    challenge=staff_tests.StaffTests.challenge
    authenticated=staff_tests.StaffTests.authenticated
    grant=staff_tests.StaffTests.grant
    def setUp(self):
        staff_tests.StaffTests.setUp(self)
        self.owner=self.quotation.cart.owner
        self.owner_client=Client(HTTP_HOST='127.0.0.1')
        with self.owner_context():verified_login(self.owner_client,self.owner)
        self.path='/purchase/quotation-business/'+str(self.quotation.id)+'/'
        self.detail='/staff/quotation-requests/'+str(self.quotation.id)+'/'
        self.review_route='quotation-requests/'+str(self.quotation.id)+'/reviews/'
        self.private=self.detail+'business/'
        self.request={'action':'attach','request_id':str(uuid.uuid4()),'expected_scope_version':'0','business_version':'1'}
        self.saved=self.business(1,'BUSINESS_SCOPE_ONE_PRIVATE_SYNTHETIC')
    def owner_context(self):
        middleware=[name for name in staff_tests.STAFF_SETTINGS['MIDDLEWARE'] if name not in
                    ('shop.access.staff_middleware.StaffHostMiddleware','shop.access.staff_middleware.StaffMFAMiddleware')]
        return override_settings(ROOT_URLCONF='shop.urls',LOCAL_STAFF_ENABLED=False,MIDDLEWARE=middleware,
                                 SESSION_COOKIE_NAME='sessionid',CSRF_COOKIE_NAME='csrftoken')
    def owner_get(self,path=None,client=None):
        with self.owner_context():return (client or self.owner_client).get(path or self.path)
    def attach(self,value=None,client=None):
        with self.owner_context():return (client or self.owner_client).post(self.path,data=urlencode(self.request if value is None else value),content_type='application/x-www-form-urlencoded')
    def business(self,version,name,owner=None):
        draft,_=BusinessDraft.objects.get_or_create(owner=owner or self.owner)
        clean=rules.empty_details();clean.update(legal_business_name=name,business_email='owner@scope.synthetic.invalid')
        details=rules.resolve_details(clean)
        row=BusinessDraftSnapshot.objects.create(draft=draft,version=version,request_id=uuid.uuid4(),schema_version=rules.SCHEMA_VERSION,
            source_sha256=rules.SOURCE_SHA256,submission_digest=rules.submission_digest(clean),details=details,evaluation=rules.evaluate_details(details))
        draft.version=max(draft.version,version);draft.save()
        return row
    def safe_customer(self):return self.owner_get('/api/v1/quotation-requests/'+str(self.quotation.id)+'/').json()
    def enable_private(self,scope):
        call_command('local_staff','grant-business',username='reviewer',quotation=str(self.quotation.id),business_scope=scope,stdout=io.StringIO())
    def review_value(self,decision='ready_for_commercial_review'):
        detail=self.browser.get(self.detail).json()
        return {'request_id':str(uuid.uuid4()),'expected_review_version':detail['review_version'],
                'snapshot_digest':detail['snapshot_digest'],'decision':decision}
    def test_owner_preview_confirm_noop_alias_history_and_private_summary(self):
        self.assertContains(self.owner_get(),'BUSINESS_SCOPE_ONE_PRIVATE_SYNTHETIC')
        self.assertEqual(self.attach().status_code,303)
        first=QuotationBusinessScope.objects.get()
        self.assertEqual(first.business_snapshot,self.saved)
        self.business(2,'BUSINESS_SCOPE_TWO_PRIVATE_SYNTHETIC')
        preview=self.attach(dict(self.request,action='preview',business_version='2',expected_scope_version='1'))
        self.assertContains(preview,'BUSINESS_SCOPE_TWO_PRIVATE_SYNTHETIC')
        self.assertEqual(QuotationBusinessScope.objects.count(),1)
        self.assertContains(self.owner_get(),'BUSINESS_SCOPE_ONE_PRIVATE_SYNTHETIC')
        safe=self.safe_customer();self.assertEqual(safe['business_scope']['business_draft_version'],1)
        self.assertNotIn('BUSINESS_SCOPE_ONE_PRIVATE_SYNTHETIC',json.dumps(safe))
        self.assertFalse(safe['checkout_enabled']);self.assertFalse(safe['acceptance_enabled'])
        alias=dict(self.request,request_id=str(uuid.uuid4()),expected_scope_version='1')
        self.assertEqual(self.attach(alias).status_code,303)
        self.assertEqual(QuotationBusinessScope.objects.count(),1);self.assertEqual(QuotationBusinessKey.objects.count(),2)
        self.assertEqual(self.attach(dict(alias,business_version='2')).status_code,409)
        newer=dict(self.request,request_id=str(uuid.uuid4()),expected_scope_version='1',business_version='2')
        self.assertEqual(self.attach(newer).status_code,303)
        self.assertEqual(self.attach().status_code,303)
        self.assertEqual(self.safe_customer()['business_scope']['version'],2)
        self.assertEqual(QuotationRequest.objects.count(),1)
        self.assertEqual(self.attach(dict(self.request,request_id=str(uuid.uuid4()),expected_scope_version='2')).status_code,303)
        self.assertEqual(self.safe_customer()['business_scope']['version'],3)
        self.assertEqual(self.safe_customer()['business_scope']['business_draft_version'],1)
        self.assertEqual(QuotationBusinessScope.objects.get(version=1).business_snapshot.details,self.saved.details)
        for row in BusinessDraftSnapshot.objects.all():
            for name in rules.PENDING:self.assertIsNone(row.details[name])
    def test_original_retry_before_freshness_and_preview_does_not_rebase(self):
        self.assertEqual(self.attach().status_code,303)
        self.business(2,'BUSINESS_SCOPE_TWO_PRIVATE_SYNTHETIC')
        preview=self.attach(dict(self.request,action='preview',business_version='2'))
        self.assertContains(preview,'name="expected_scope_version" value="0"')
        self.assertEqual(self.attach(dict(self.request,request_id=str(uuid.uuid4()),business_version='2')).status_code,409)
        with patch.object(rules,'SOURCE_SHA256','f'*64):
            self.assertEqual(self.attach().status_code,303)
            self.assertEqual(self.attach(dict(self.request,request_id=str(uuid.uuid4()),expected_scope_version='1',business_version='2')).status_code,409)
        self.assertEqual(QuotationBusinessScope.objects.count(),1)
    def test_owner_csrf_parser_pending_choices_and_production_boundaries(self):
        other=get_user_model().objects.create_user(username='binding-other')
        client=Client(HTTP_HOST='127.0.0.1')
        with self.owner_context():verified_login(client,other)
        self.assertEqual(self.owner_get(client=client).status_code,404)
        self.assertEqual(self.attach(client=client).status_code,404)
        self.assertEqual(self.owner_get(client=Client(HTTP_HOST='127.0.0.1')).status_code,401)
        for extra in [{'owner':str(other.pk)},{'tax_status':'approved'},{'business_version':'True'},{'action':'approve'}]:
            self.assertEqual(self.attach(dict(self.request,**extra)).status_code,400)
        strict=Client(enforce_csrf_checks=True,HTTP_HOST='127.0.0.1')
        with self.owner_context():verified_login(strict,self.owner)
        self.assertEqual(self.attach(client=strict).status_code,403)
        token=self.owner_get(client=strict).cookies['csrftoken'].value
        self.assertEqual(self.attach(dict(self.request,csrfmiddlewaretoken=token),strict).status_code,303)
        with self.owner_context():
            for mode in ['production','bank-sandbox']:
                with override_settings(SHOP_ENV=mode):
                    self.assertEqual(self.owner_client.get(self.path).status_code,404)
        bad=self.business(2,'BUSINESS_BAD_TAX_SYNTHETIC');bad.details['tax_status']='approved';bad.save()
        self.assertEqual(self.attach(dict(self.request,request_id=str(uuid.uuid4()),expected_scope_version='1',business_version='2')).status_code,409)
        self.assertEqual(QuotationBusinessScope.objects.count(),1)
    def test_general_staff_grant_never_gives_private_business_access(self):
        self.authenticated();self.grant()
        legacy=self.review_value()
        self.assertEqual(self.attach().status_code,303)
        detail=self.browser.get(self.detail).json()
        self.assertFalse(detail['review_enabled']);self.assertIsNone(detail['snapshot_digest'])
        self.assertEqual(self.browser.get(self.private).status_code,403)
        self.assertEqual(self.post(self.review_route,legacy).status_code,403)
        self.enable_private(1)
        raw=self.browser.get(self.private);self.assertEqual(raw.status_code,200)
        self.assertEqual(raw.json()['details'],self.saved.details)
        self.assertEqual(raw['Cache-Control'],'no-store')
        self.assertNotIn('BUSINESS_SCOPE_ONE_PRIVATE_SYNTHETIC',self.browser.get(self.detail).content.decode())
        html=self.browser.get(self.private,HTTP_ACCEPT='text/html');self.assertContains(html,'BUSINESS_SCOPE_ONE_PRIVATE_SYNTHETIC')
        value=self.review_value();self.assertNotEqual(value['snapshot_digest'],legacy['snapshot_digest'])
        self.assertEqual(self.post(self.review_route,value).status_code,201)
        review=QuotationReview.objects.get();self.assertEqual(review.business_version,1)
        self.assertEqual(self.safe_customer()['review_status']['code'],'ready_for_commercial_review')
    def test_new_scope_needs_new_private_grant_and_rejects_old_review_form(self):
        self.authenticated();self.grant();self.assertEqual(self.attach().status_code,303);self.enable_private(1)
        stale=self.review_value()
        self.business(2,'BUSINESS_SCOPE_TWO_PRIVATE_SYNTHETIC')
        self.assertEqual(self.attach(dict(self.request,request_id=str(uuid.uuid4()),expected_scope_version='1',business_version='2')).status_code,303)
        self.assertEqual(self.browser.get(self.private).status_code,403)
        self.assertEqual(self.post(self.review_route,stale).status_code,403)
        with self.assertRaises(CommandError):self.enable_private(1)
        self.enable_private(2)
        self.assertEqual(self.post(self.review_route,stale).json()['error'],'snapshot_changed')
        current=self.review_value('needs_information');self.assertEqual(self.post(self.review_route,current).status_code,201)
        self.business(3,'BUSINESS_SCOPE_THREE_PRIVATE_SYNTHETIC')
        self.assertEqual(self.browser.get(self.private).json()['details']['legal_business_name'],'BUSINESS_SCOPE_TWO_PRIVATE_SYNTHETIC')
        self.assertEqual(self.review_value()['snapshot_digest'],current['snapshot_digest'])
        self.assertEqual(QuotationReview.objects.get().business_version,2)
    def test_legacy_review_is_retained_but_not_current_after_attachment(self):
        self.authenticated();self.grant()
        legacy=self.review_value();original=self.post(self.review_route,legacy);self.assertEqual(original.status_code,201)
        self.assertEqual(self.safe_customer()['review_status']['code'],'ready_for_commercial_review')
        self.assertEqual(self.attach().status_code,303)
        self.assertEqual(self.safe_customer()['review_status']['code'],'awaiting_review')
        self.assertEqual(self.post(self.review_route,legacy).json()['review'],original.json()['review'])
        self.enable_private(1)
        current=self.review_value();self.assertEqual(self.post(self.review_route,current).status_code,201)
        self.assertEqual(list(QuotationReview.objects.order_by('version').values_list('business_version',flat=True)),[0,1])
        self.assertEqual(QuotationReview.objects.get(version=1).snapshot_digest,legacy['snapshot_digest'])
        call_command('local_staff','revoke-business',username='reviewer',quotation=str(self.quotation.id),stdout=io.StringIO())
        self.assertEqual(self.browser.get(self.private).status_code,403)
        history=self.browser.get(self.detail).json()['reviews']
        self.assertIsNone(history[0]['snapshot_digest']);self.assertEqual(history[1]['snapshot_digest'],legacy['snapshot_digest'])
        self.assertEqual(self.post(self.review_route,current).status_code,403)
    def race(self,same):
        clients=[Client(HTTP_HOST='127.0.0.1'),Client(HTTP_HOST='127.0.0.1')]
        barrier=Barrier(2)
        def run(index):
            try:
                value=dict(self.request)
                if not same:value['request_id']=str(uuid.uuid4())
                barrier.wait(timeout=10)
                return clients[index].post(self.path,data=urlencode(value),content_type='application/x-www-form-urlencoded').status_code
            finally:connections.close_all()
        with self.owner_context():
            for client in clients:verified_login(client,self.owner)
            with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(run,range(2)))
        self.assertEqual(sorted(results),[303,303] if same else [303,409])
        self.assertEqual(QuotationBusinessScope.objects.count(),1)
        self.assertEqual(QuotationBusinessKey.objects.count(),1)
    def test_concurrent_exact_retry(self):self.race(True)
    def test_concurrent_scope_changes(self):self.race(False)

    def test_attachment_racing_review_never_reviews_an_ungranted_new_scope(self):
        from django.test import RequestFactory
        from .business_binding_views import bind_business
        self.authenticated();self.grant();self.assertEqual(self.attach().status_code,303);self.enable_private(1)
        stale=self.review_value()
        self.business(2,'BUSINESS_SCOPE_TWO_PRIVATE_SYNTHETIC')
        with self.owner_context():
            owner_session=self.owner_client.session
            dict(owner_session.items())
        staff=Client(HTTP_HOST='staff.localhost');staff.cookies=self.browser.cookies.copy()
        change=dict(self.request,request_id=str(uuid.uuid4()),expected_scope_version='1',business_version='2')
        barrier=Barrier(2)
        def run(index):
            try:
                barrier.wait(timeout=10)
                if index==0:
                    request=RequestFactory().post(self.path,data=urlencode(change),content_type='application/x-www-form-urlencoded',HTTP_HOST='127.0.0.1')
                    # Explicit verified-owner service fixture; CSRF/host middleware is covered separately.
                    request.user=self.owner;request.session=owner_session
                    return bind_business(request,self.quotation.id).status_code
                return staff.post('/staff/'+self.review_route,data=json.dumps(stale),content_type='application/json').status_code
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(run,range(2)))
        self.assertEqual(results[0],303);self.assertIn(results[1],[201,403])
        self.assertEqual(self.safe_customer()['business_scope']['version'],2)
        self.assertEqual(self.safe_customer()['review_status']['code'],'awaiting_review')
        self.assertEqual(QuotationReview.objects.count(),1 if results[1]==201 else 0)
        self.assertFalse(QuotationReview.objects.exclude(business_version=1).exists())

    def test_inconsistent_cross_owner_binding_cannot_disclose_business_values(self):
        other=get_user_model().objects.create_user(username='inconsistent-binding-other')
        foreign=self.business(1,'FOREIGN_BUSINESS_PRIVATE_SYNTHETIC',owner=other)
        QuotationBusinessScope.objects.create(quotation=self.quotation,version=1,business_snapshot=foreign)
        self.quotation.business_version=1;self.quotation.save(update_fields=['business_version'])
        page=self.owner_get();self.assertEqual(page.status_code,200)
        self.assertNotIn('FOREIGN_BUSINESS_PRIVATE_SYNTHETIC',page.content.decode())
        self.assertEqual(self.safe_customer()['business_scope']['state'],'unavailable')
        self.authenticated();self.grant();self.enable_private(1)
        self.assertEqual(self.browser.get(self.private).status_code,404)
        response=self.browser.get(self.detail)
        self.assertNotIn('FOREIGN_BUSINESS_PRIVATE_SYNTHETIC',response.content.decode())
        self.assertFalse(response.json()['review_enabled'])
