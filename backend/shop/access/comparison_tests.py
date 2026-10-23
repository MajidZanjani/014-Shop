"""Private fixed-category comparison with real PG prefix/authorization checks."""
from concurrent.futures import ThreadPoolExecutor
import copy
import io
import json
from unittest.mock import patch
import uuid
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import connections
from django.test import SimpleTestCase, TransactionTestCase, Client, override_settings
from shop.catalog.document_preview import DEFINITION
from shop.catalog.rules import CATALOG
from shop.catalog.models import QuotationRequest, QuotationReview, QuotationBusinessScope
from . import preparation_snapshot_tests as fixtures, staff_tests
from .models import PreparationAssessment, StaffQuotationGrant
from .offer_preparation import assess
from .preparation_comparison import compare, CATEGORIES


class ComparisonValueTests(SimpleTestCase):
    def test_null_missing_zero_false_and_empty_are_distinct_without_values_in_output(self):
        base={'blockers':[],'money':{'total_minor':None}}
        self.assertEqual(compare(base,base)['changed_categories'],0)
        for value in [0,False,'',[]]:
            other=dict(base,money={'total_minor':value})
            result=compare(base,other)
            self.assertTrue(next(row['changed'] for row in result['categories'] if row['code']=='money_deadlines'))
        for other in [{'blockers':[],'money':{}},{'blockers':[]}]:
            self.assertEqual(compare(base,other)['changed_categories'],1)
        self.assertEqual(compare(dict(base,money={'total_minor':0}),dict(base,money={'total_minor':False}))['changed_categories'],1)
        secret=dict(base,business={'raw_unexpected':'PRIVATE_COMPARISON_VALUE_CANARY'})
        result=compare(base,secret)
        self.assertNotIn('PRIVATE_COMPARISON_VALUE_CANARY',json.dumps(result))
        self.assertEqual({row['code'] for row in result['categories']},{code for code,_ in CATEGORIES})
        for key in ['offer_creation_enabled','publication_enabled','acceptance_enabled','checkout_enabled']:self.assertFalse(result[key])


@override_settings(**staff_tests.STAFF_SETTINGS)
class ComparisonTests(TransactionTestCase):
    setUp=fixtures.PreparationSnapshotTests.setUp
    post=fixtures.PreparationSnapshotTests.post
    challenge=fixtures.PreparationSnapshotTests.challenge
    authenticated=fixtures.PreparationSnapshotTests.authenticated
    grant=fixtures.PreparationSnapshotTests.grant
    owner_context=fixtures.PreparationSnapshotTests.owner_context
    attach=fixtures.PreparationSnapshotTests.attach
    business=fixtures.PreparationSnapshotTests.business
    enable_private=fixtures.PreparationSnapshotTests.enable_private
    review_value=fixtures.PreparationSnapshotTests.review_value
    prepare=fixtures.PreparationSnapshotTests.prepare
    form=fixtures.PreparationSnapshotTests.form
    submit_capture=fixtures.PreparationSnapshotTests.submit_capture
    decision=fixtures.PreparationSnapshotTests.decision
    def capture_for_comparison(self,bound=False):
        self.prepare(bound=bound)
        self.assertEqual(self.submit_capture().status_code,201)
        self.compare_path=self.snap+'1/compare/'
    def changed(self,response):
        self.assertEqual(response.status_code,200)
        return {row['code'] for row in response.json()['categories'] if row['changed']}
    def test_no_changes_does_not_mean_ready_and_reads_do_not_write(self):
        self.capture_for_comparison(bound=True)
        original=copy.deepcopy(PreparationAssessment.objects.get().assessment)
        before=(PreparationAssessment.objects.count(),QuotationReview.objects.count(),QuotationBusinessScope.objects.count())
        for _ in range(2):
            response=self.browser.get(self.compare_path);self.assertEqual(self.changed(response),set())
            value=response.json();self.assertEqual(value['state'],'no_differences');self.assertTrue(value['current_assessment_available'])
            for key in ['offer_creation_enabled','publication_enabled','acceptance_enabled','checkout_enabled']:self.assertFalse(value[key])
            self.assertEqual(value['country_tax_choices'],'deferred')
        self.assertEqual(before,(PreparationAssessment.objects.count(),QuotationReview.objects.count(),QuotationBusinessScope.objects.count()))
        self.assertEqual(original,PreparationAssessment.objects.get().assessment)
        self.business(2,'PRIVATE_UNATTACHED_COMPARISON_BUSINESS')
        self.assertEqual(self.changed(self.browser.get(self.compare_path)),set())
    def test_review_correction_reports_fixed_categories_and_keeps_original(self):
        self.capture_for_comparison();original=copy.deepcopy(PreparationAssessment.objects.get().assessment)
        self.decision()
        response=self.browser.get(self.compare_path);self.assertIn('review',self.changed(response))
        self.assertIn('blockers',self.changed(response));self.assertNotIn('money_deadlines',self.changed(response))
        self.assertEqual(response.json()['retained']['review_version'],0);self.assertEqual(response.json()['current']['review_version'],1)
        self.assertEqual(PreparationAssessment.objects.get().assessment,original)
        html=self.browser.get(self.compare_path,HTTP_ACCEPT='text/html')
        self.assertContains(html,'does not mean ready for an offer');self.assertNotContains(html,'<form');self.assertNotContains(html,'<input')
    def test_legacy_to_current_business_requires_current_permission(self):
        self.capture_for_comparison();self.assertEqual(self.attach().status_code,303)
        self.assertEqual(self.browser.get(self.compare_path).status_code,403)
        self.enable_private(1)
        result=self.browser.get(self.compare_path);self.assertIn('business',self.changed(result))
        self.assertEqual(result.json()['retained']['business_version'],0);self.assertEqual(result.json()['current']['business_version'],1)
        self.assertNotIn('money_deadlines',self.changed(result))
    def test_two_positive_scopes_require_both_permissions_without_grant_widening(self):
        self.capture_for_comparison(bound=True)
        self.business(2,'PRIVATE_NEW_COMPARISON_BUSINESS')
        self.assertEqual(self.attach(dict(self.request,request_id=str(uuid.uuid4()),expected_scope_version='1',business_version='2')).status_code,303)
        self.assertEqual(self.browser.get(self.snap+'1/').status_code,200)
        denied=self.browser.get(self.compare_path);self.assertEqual(denied.status_code,403)
        self.assertEqual(denied.json()['error'],'comparison_scope_access_required')
        self.enable_private(2)
        self.assertEqual(self.browser.get(self.compare_path).status_code,403)
        self.assertEqual(StaffQuotationGrant.objects.get(user=self.user).business_scope_version,2)
    def test_source_changes_are_explicit_and_unavailable_is_not_unchanged(self):
        self.capture_for_comparison()
        with patch.dict(CATALOG,revision='f'*64):
            response=self.browser.get(self.compare_path);self.assertIn('source',self.changed(response))
            self.assertIn('blockers',self.changed(response))
        with patch.dict(DEFINITION,revision='f'*64):
            response=self.browser.get(self.compare_path);self.assertIn('source',self.changed(response))
            self.assertEqual(response.json()['state'],'current_unavailable')
            self.assertFalse(response.json()['current_assessment_available'])
            self.assertFalse(response.json()['publication_enabled'])
            self.assertEqual(self.browser.get(self.snap+'1/').status_code,200)
    def test_auth_revocation_modes_queries_methods_and_privacy_headers(self):
        self.capture_for_comparison(bound=True)
        response=self.browser.get(self.compare_path);row=PreparationAssessment.objects.get()
        self.assertEqual(response['Cache-Control'],'no-store');self.assertEqual(response['Referrer-Policy'],'no-referrer')
        self.assertEqual(response['Vary'],'Cookie');self.assertIn("form-action 'none'",response['Content-Security-Policy'])
        for text in [response.content.decode(),self.browser.get(self.compare_path,HTTP_ACCEPT='text/html').content.decode()]:
            for secret in ['BUSINESS_SCOPE_ONE_PRIVATE_SYNTHETIC','owner@scope.synthetic.invalid',row.scope_digest,row.assessment_digest,str(row.request_id),str(self.credential.generation)]:self.assertNotIn(secret,text)
        self.assertEqual(Client(HTTP_HOST='staff.localhost').get(self.compare_path).status_code,403)
        self.assertEqual(self.browser.get(self.compare_path+'?before=0&approve=true').status_code,400)
        self.assertEqual(self.post(self.route+'1/compare/',{'approve':True}).status_code,405)
        for mode in ['production','bank-sandbox']:
            with override_settings(SHOP_ENV=mode):self.assertEqual(self.browser.get(self.compare_path).status_code,404)
        self.assertEqual(self.browser.get(self.compare_path,HTTP_HOST='shop.xspi.pro').status_code,404)
        with self.owner_context():self.assertEqual(self.owner_client.get(self.compare_path).status_code,404)
        call_command('local_staff','revoke-business',username='reviewer',quotation=str(self.quotation.id),stdout=io.StringIO())
        self.assertEqual(self.browser.get(self.compare_path).status_code,403)
        StaffQuotationGrant.objects.filter(user=self.user).delete();self.assertEqual(self.browser.get(self.compare_path).status_code,404)
        session=self.browser.session;marker=session['shop_staff_mfa'];marker['verified_at']-=301;session['shop_staff_mfa']=marker;session.save()
        self.assertEqual(self.browser.get(self.compare_path).status_code,403)
    def test_corrupted_retained_or_private_reference_or_live_assessment_is_rejected(self):
        self.capture_for_comparison(bound=True)
        row=PreparationAssessment.objects.get();bad=copy.deepcopy(row.assessment);bad['publication_enabled']=True
        PreparationAssessment.objects.update(assessment=bad)
        self.assertEqual(self.browser.get(self.compare_path).status_code,409)
        PreparationAssessment.objects.update(assessment=row.assessment)
        current=assess(QuotationRequest.objects.get(pk=self.quotation.pk))
        with patch('shop.access.comparison_views.assess',return_value=dict(current,publication_enabled=True)):
            self.assertEqual(self.browser.get(self.compare_path).status_code,409)
        stranger=get_user_model().objects.create_user(username='comparison-unrelated')
        self.saved.draft.owner=stranger;self.saved.draft.save()
        self.assertEqual(self.browser.get(self.compare_path).status_code,409)
    def test_concurrent_review_after_parent_read_appears_only_on_reload(self):
        self.capture_for_comparison()
        review_value=self.review_value()
        def assess_after_append(quotation):
            def append():
                client=Client(HTTP_HOST='staff.localhost');client.cookies=self.browser.cookies.copy()
                try:return client.post('/staff/'+self.review_route,data=json.dumps(review_value),content_type='application/json').status_code
                finally:connections.close_all()
            with ThreadPoolExecutor(max_workers=1) as pool:self.assertEqual(pool.submit(append).result(timeout=10),201)
            return assess(quotation)
        with patch('shop.access.comparison_views.assess',side_effect=assess_after_append):
            first=self.browser.get(self.compare_path)
        self.assertEqual(self.changed(first),set());self.assertEqual(first.json()['current']['review_version'],0)
        second=self.browser.get(self.compare_path);self.assertIn('review',self.changed(second))
        self.assertEqual(second.json()['current']['review_version'],1)
