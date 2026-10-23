"""Retained noncommercial preparation: attribution, replay, privacy and PG races."""
from concurrent.futures import ThreadPoolExecutor
import copy
import io
import json
import re
from threading import Barrier
from urllib.parse import urlencode
from unittest.mock import patch
import uuid
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import connections
from django.test import Client, TransactionTestCase, override_settings
from shop.catalog import binding_tests as bindings
from shop.catalog.document_preview import DEFINITION
from shop.catalog.models import QuotationRequest, QuotationReview, QuotationBusinessScope
from shop.catalog.rules import CATALOG
from . import staff_tests
from .models import PreparationAssessment, StaffQuotationGrant
from .preparation_snapshots import fingerprint, DISABLED


@override_settings(**staff_tests.STAFF_SETTINGS)
class PreparationSnapshotTests(TransactionTestCase):
    setUp=bindings.BusinessBindingTests.setUp
    post=bindings.BusinessBindingTests.post
    challenge=bindings.BusinessBindingTests.challenge
    authenticated=bindings.BusinessBindingTests.authenticated
    grant=bindings.BusinessBindingTests.grant
    owner_context=bindings.BusinessBindingTests.owner_context
    attach=bindings.BusinessBindingTests.attach
    business=bindings.BusinessBindingTests.business
    enable_private=bindings.BusinessBindingTests.enable_private
    review_value=bindings.BusinessBindingTests.review_value
    def prepare(self,bound=False):
        self.authenticated();self.grant()
        if bound:self.assertEqual(self.attach().status_code,303);self.enable_private(1)
        self.snap=self.detail+'preparation-snapshots/'
        self.route='quotation-requests/'+str(self.quotation.id)+'/preparation-snapshots/'
        self.value=self.form()
    def form(self):
        response=self.browser.get(self.snap);self.assertEqual(response.status_code,200)
        value=response.json()
        return {key:value[key] for key in ['request_id','expected_preparation_version','assessment_digest']}
    def submit_capture(self,value=None,client=None):return self.post(self.route,self.value if value is None else value,client)
    def detail_snapshot(self,version=1):return self.browser.get(self.snap+str(version)+'/')
    def decision(self):
        self.assertEqual(self.post(self.review_route,self.review_value()).status_code,201)
    def test_capture_attribution_exact_retry_and_append_history(self):
        self.prepare(bound=True);self.decision();self.value=self.form()
        first=self.submit_capture();self.assertEqual(first.status_code,201)
        row=PreparationAssessment.objects.get()
        self.assertEqual(row.captured_by,self.user);self.assertEqual(row.staff_generation,self.credential.generation)
        self.assertEqual(row.business_scope,QuotationBusinessScope.objects.get());self.assertEqual(row.review,QuotationReview.objects.get())
        self.assertEqual(row.review_version,1);self.assertEqual(row.business_version,1)
        self.assertIn('—',row.assessment['review']['label'])
        self.assertEqual(row.assessment_digest,fingerprint(row.assessment,row.scope_digest))
        self.assertEqual(row.mfa_verified_at.timestamp(),self.browser.session['shop_staff_mfa']['verified_at'])
        self.assertEqual(self.submit_capture().json()['snapshot'],first.json()['snapshot'])
        self.assertEqual(self.submit_capture().status_code,200)
        next_value=self.form();self.assertEqual(self.submit_capture(next_value).status_code,201)
        self.assertEqual(self.submit_capture().json()['snapshot'],first.json()['snapshot'])
        self.quotation.refresh_from_db();self.assertEqual(self.quotation.preparation_version,2)
        self.assertEqual(PreparationAssessment.objects.count(),2)
        self.assertEqual(self.detail_snapshot().json(),first.json()['snapshot'])
        self.assertEqual([row['version'] for row in self.browser.get(self.snap).json()['snapshots']],[2,1])
    def test_stale_cas_changed_key_actor_digest_and_review_form_rejected(self):
        self.prepare();self.assertEqual(self.submit_capture().status_code,201)
        for change in [{'expected_preparation_version':1},{'assessment_digest':'0'*64}]:
            self.assertEqual(self.submit_capture(dict(self.value,**change)).json()['error'],'request_conflict')
        self.assertEqual(self.submit_capture(dict(self.value,request_id=str(uuid.uuid4()))).json()['error'],'preparation_changed')
        # Changing attributed actor cannot reconcile someone else's submission.
        other=get_user_model().objects.create_user(username='different-preparation-actor',is_staff=True)
        PreparationAssessment.objects.update(captured_by=other)
        self.assertEqual(self.submit_capture().json()['error'],'request_conflict')
        PreparationAssessment.objects.update(captured_by=self.user)
        fresh=self.form();self.decision()
        self.assertEqual(self.submit_capture(fresh).json()['error'],'assessment_changed')
        self.assertEqual(self.submit_capture(self.form()).status_code,201)
    def test_old_retries_and_retained_reads_precede_new_source_freshness(self):
        self.prepare();original=self.submit_capture().json()['snapshot']
        with patch.dict(CATALOG,revision='f'*64),patch.dict(DEFINITION,revision='f'*64):
            self.assertEqual(self.submit_capture().json()['snapshot'],original)
            self.assertEqual(self.detail_snapshot().json(),original)
            self.assertIsNone(self.browser.get(self.snap).json()['assessment_digest'])
            new=dict(self.value,request_id=str(uuid.uuid4()),expected_preparation_version=1)
            self.assertEqual(self.submit_capture(new).json()['error'],'assessment_changed')
        self.assertEqual(PreparationAssessment.objects.count(),1)
    def test_historical_scopes_are_authorized_independently_and_edits_do_not_retarget(self):
        self.prepare();legacy=self.submit_capture().json()['snapshot']
        self.assertEqual(self.attach().status_code,303);self.enable_private(1)
        one=self.form();captured=self.submit_capture(one).json()['snapshot']
        self.business(2,'UNATTACHED_PRIVATE_PREPARATION_BUSINESS')
        self.assertEqual(self.detail_snapshot(2).json(),captured)
        self.assertEqual(self.attach(dict(self.request,request_id=str(uuid.uuid4()),expected_scope_version='1',business_version='2')).status_code,303)
        self.assertEqual(self.browser.get(self.snap).status_code,403)
        # Permission for scope1 can reconcile its own record despite a later attachment.
        self.assertEqual(self.submit_capture(one).json()['snapshot'],captured)
        self.assertEqual(self.detail_snapshot(2).json(),captured)
        self.enable_private(2)
        self.assertEqual(self.detail_snapshot(2).status_code,403)
        self.assertEqual(self.submit_capture(one).status_code,403)
        self.assertEqual(self.detail_snapshot(1).json(),legacy)
        self.assertEqual(self.submit_capture(self.form()).status_code,201)
        history=self.browser.get(self.snap).json()['snapshots'];self.assertEqual([r['version'] for r in history],[3,1])
    def test_csrf_strict_parser_no_js_form_replay_and_methods(self):
        self.prepare()
        for extra in [{'price':0},{'approve':True},{'expected_preparation_version':True},{'assessment_digest':'x'},{'request_id':1}]:
            self.assertEqual(self.submit_capture(dict(self.value,**extra)).status_code,400)
        self.assertEqual(self.browser.post(self.snap,data=json.dumps(self.value),content_type='application/json').status_code,403)
        token=self.browser.get('/staff/session/').json()['csrf_token']
        for raw in ['{"request_id":1,"request_id":2}','NaN','x'*1025]:
            self.assertEqual(self.browser.post(self.snap,data=raw,content_type='application/json',HTTP_X_CSRFTOKEN=token).status_code,400)
        page=self.browser.get(self.snap,HTTP_ACCEPT='text/html');self.assertContains(page,'Retain displayed internal assessment')
        fields=dict(re.findall(r'<input[^>]*name="([^"]+)"[^>]*value="([^"]*)"',page.content.decode()))
        for _ in range(2):
            result=self.browser.post(self.snap,data=urlencode(fields),content_type='application/x-www-form-urlencoded',HTTP_ACCEPT='text/html')
            self.assertEqual(result.status_code,303);self.assertEqual(result['Location'],self.snap+'1/')
        bad=dict(fields,request_id=str(uuid.uuid4()))
        result=self.browser.post(self.snap,data=urlencode(bad),content_type='application/x-www-form-urlencoded',HTTP_ACCEPT='text/html')
        self.assertEqual(result.status_code,409);self.assertContains(result,'Reload',status_code=409)
        for path in [self.snap,self.snap+'1/']:
            self.assertEqual(self.browser.get(path+'?approve=true').status_code,400)
            self.assertEqual(self.browser.delete(path,HTTP_X_CSRFTOKEN=token).status_code,405)
        self.assertEqual(self.post(self.route+'1/',self.value).status_code,405)
        self.assertEqual(PreparationAssessment.objects.count(),1)
    def test_permissions_modes_revocation_and_cross_owner_links(self):
        self.prepare(bound=True);self.assertEqual(self.submit_capture().status_code,201)
        call_command('local_staff','revoke-business',username='reviewer',quotation=str(self.quotation.id),stdout=io.StringIO())
        self.assertEqual(self.browser.get(self.snap).status_code,403);self.assertEqual(self.detail_snapshot().status_code,403)
        self.assertEqual(self.submit_capture().status_code,403);self.enable_private(1)
        for mode in ['production','bank-sandbox']:
            with override_settings(SHOP_ENV=mode):self.assertEqual(self.detail_snapshot().status_code,404)
        self.assertEqual(self.browser.get(self.snap,HTTP_HOST='shop.xspi.pro').status_code,404)
        with self.owner_context():self.assertEqual(self.owner_client.get(self.snap).status_code,404)
        stranger=get_user_model().objects.create_user(username='stranger-preparation')
        self.saved.draft.owner=stranger;self.saved.draft.save()
        self.assertEqual(self.detail_snapshot().status_code,409);self.assertEqual(self.submit_capture().status_code,409)
        StaffQuotationGrant.objects.filter(user=self.user).delete()
        self.assertEqual(self.detail_snapshot().status_code,404);self.assertEqual(self.submit_capture().status_code,404)
        session=self.browser.session;marker=session['shop_staff_mfa'];marker['verified_at']-=301;session['shop_staff_mfa']=marker;session.save()
        self.assertEqual(self.detail_snapshot().status_code,403);self.assertEqual(self.submit_capture().status_code,403)
    def test_privacy_pending_values_read_only_get_and_tamper_detection(self):
        self.prepare(bound=True)
        self.assertEqual(PreparationAssessment.objects.count(),0)
        page=self.browser.get(self.snap,HTTP_ACCEPT='text/html');self.assertEqual(PreparationAssessment.objects.count(),0)
        self.assertEqual(page['Cache-Control'],'no-store');self.assertEqual(page['Referrer-Policy'],'no-referrer')
        original=self.submit_capture().json()['snapshot'];row=PreparationAssessment.objects.get()
        for text in [json.dumps(original),self.browser.get(self.snap+'1/',HTTP_ACCEPT='text/html').content.decode()]:
            for secret in ['BUSINESS_SCOPE_ONE_PRIVATE_SYNTHETIC','owner@scope.synthetic.invalid',row.scope_digest,row.assessment_digest,str(self.credential.generation),str(row.request_id)]:self.assertNotIn(secret,text)
        for field in DISABLED:self.assertFalse(original['assessment'][field])
        self.assertIsNone(original['assessment']['money']['total_minor']);self.assertEqual(original['assessment']['country_tax_choices'],'deferred')
        changed=copy.deepcopy(row.assessment);changed['publication_enabled']=True
        PreparationAssessment.objects.update(assessment=changed)
        self.assertEqual(self.detail_snapshot().status_code,409);self.assertEqual(self.submit_capture().status_code,409)
        PreparationAssessment.objects.update(assessment=row.assessment)
        self.quotation.snapshot.lines=[];self.quotation.snapshot.save()
        self.assertEqual(self.detail_snapshot().status_code,409)
    def test_invalid_source_business_or_nonblocked_assessment_cannot_capture(self):
        self.prepare(bound=True)
        with patch.dict(DEFINITION,revision='0'*64):self.assertEqual(self.submit_capture().status_code,409)
        self.saved.details['tax_status']='invented';self.saved.save()
        self.assertIsNone(self.browser.get(self.snap).json()['assessment_digest']);self.assertEqual(self.submit_capture().status_code,409)
        self.saved.details['tax_status']=None;self.saved.save()
        from .offer_preparation import assess
        self.quotation.refresh_from_db();real=assess(self.quotation)
        for change in [{'publication_enabled':True},{'money':dict(real['money'],total_minor=0)}]:
            with patch('shop.access.preparation_snapshots.assess',return_value=dict(real,**change)):
                self.assertIsNone(self.browser.get(self.snap).json()['assessment_digest']);self.assertEqual(self.submit_capture().status_code,409)
        self.assertEqual(PreparationAssessment.objects.count(),0)
    def race(self,same=False,review=False):
        self.prepare();clients=[Client(HTTP_HOST='staff.localhost') for _ in range(2)]
        for client in clients:client.cookies=self.browser.cookies.copy()
        barrier=Barrier(2)
        review_value=self.review_value()
        def run(index):
            try:
                route=self.route;value=dict(self.value)
                if review and index:route=self.review_route;value=review_value
                elif not same and index:value['request_id']=str(uuid.uuid4())
                barrier.wait(timeout=10)
                return clients[index].post('/staff/'+route,data=json.dumps(value),content_type='application/json').status_code
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(run,range(2)))
        if review:
            self.assertIn(results[0],[201,409]);self.assertEqual(results[1],201)
            if results[0]==201:self.assertEqual(PreparationAssessment.objects.get().review_version,0)
        else:
            self.assertEqual(sorted(results),[200,201] if same else [201,409]);self.assertEqual(PreparationAssessment.objects.count(),1)
        q=QuotationRequest.objects.get(pk=self.quotation.pk);self.assertEqual(q.preparation_version,PreparationAssessment.objects.count())
    def test_same_key_race(self):self.race(same=True)
    def test_competing_key_race(self):self.race()
    def test_capture_against_review_race(self):self.race(review=True)
