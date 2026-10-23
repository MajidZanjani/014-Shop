"""Exact-scope read-only staff readiness, never commercial authorization."""
from concurrent.futures import ThreadPoolExecutor
import io
import json
from unittest.mock import patch
import uuid
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import connections, transaction
from django.test import Client, TransactionTestCase, override_settings
from django.utils import timezone
from shop.catalog import binding_tests as bindings
from shop.catalog.cart_tests import CASES
from shop.catalog.document_preview import DEFINITION
from shop.catalog.models import QuotationRequest, QuotationReview, QuotationBusinessScope, BusinessDraftSnapshot, DraftCart, CartSnapshot
from shop.catalog.rules import CATALOG
from shop.catalog import business_rules
from . import staff_tests
from .models import StaffQuotationGrant
from .offer_preparation import assess


@override_settings(**staff_tests.STAFF_SETTINGS)
class PreparationTests(TransactionTestCase):
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
        if bound:
            self.assertEqual(self.attach().status_code,303);self.enable_private(1)
        self.prep=self.detail+'preparation/'
    def get(self,html=False):
        return self.browser.get(self.prep,HTTP_ACCEPT='text/html' if html else 'application/json')
    def decision(self,code='ready_for_commercial_review'):
        value=self.review_value(code)
        response=self.post(self.review_route,value);self.assertEqual(response.status_code,201)
        return value
    def test_auth_assignment_private_scope_revocation_and_new_scope(self):
        self.prep=self.detail+'preparation/'
        self.assertEqual(self.get().status_code,403)
        self.authenticated();self.assertEqual(self.get().status_code,404)
        self.grant();self.assertEqual(self.get().status_code,200)
        self.assertEqual(self.attach().status_code,303)
        self.assertEqual(self.get().status_code,403)
        self.enable_private(1);self.assertEqual(self.get().status_code,200)
        call_command('local_staff','revoke-business',username='reviewer',quotation=str(self.quotation.id),stdout=io.StringIO())
        self.assertEqual(self.get().status_code,403)
        self.enable_private(1)
        self.business(2,'PRIVATE_SECOND_PREPARATION_BUSINESS')
        self.assertEqual(self.attach(dict(self.request,request_id=str(uuid.uuid4()),expected_scope_version='1',business_version='2')).status_code,303)
        self.assertEqual(self.get().status_code,403)
        self.enable_private(2);self.assertEqual(self.get().json()['business']['scope_version'],2)
        StaffQuotationGrant.objects.filter(user=self.user).delete();self.assertEqual(self.get().status_code,404)
    def test_readiness_matches_exact_review_and_corrections_without_approval(self):
        self.prepare(bound=True)
        self.assertEqual(self.get().json()['review']['code'],'awaiting_review')
        self.decision()
        value=self.get().json();self.assertEqual(value['review']['code'],'ready_for_commercial_review')
        self.assertNotIn('internal_review',{r['code'] for r in value['blockers']})
        self.assertEqual(value['state'],'blocked')
        for field in ['offer_creation_enabled','publication_enabled','acceptance_enabled','checkout_enabled']:self.assertFalse(value[field])
        self.decision('needs_information')
        self.assertEqual(self.get().json()['review']['code'],'needs_information')
        self.decision('declined');self.assertEqual(self.get().json()['review']['code'],'declined')
        self.assertEqual(QuotationReview.objects.count(),3)
        # No successful internal outcome substitutes for exact scope evidence.
        self.decision();QuotationReview.objects.filter(version=4).update(snapshot_digest='0'*64)
        self.assertEqual(self.get().json()['review']['code'],'scope_mismatch')
    def test_new_attachment_awaits_review_and_draft_edits_do_not_retarget(self):
        self.prepare();self.decision()
        self.assertEqual(self.attach().status_code,303);self.enable_private(1)
        self.assertEqual(self.get().json()['review']['code'],'awaiting_review')
        self.decision();before=self.get().json()
        self.business(2,'PRIVATE_LATER_UNATTACHED_BUSINESS')
        after=self.get().json();self.assertEqual(before,after)
        self.assertEqual(after['business']['draft_version'],1)
        self.assertNotIn('PRIVATE_LATER_UNATTACHED_BUSINESS',json.dumps(after))
    def test_profiles_line_requirements_and_money_remain_unknown(self):
        self.prepare()
        for case,profile in [(CASES[1],'ip'),(CASES[2],'support_only'),(CASES[3],'mixed'),(CASES[4],'ip')]:
            self.quotation.snapshot.lines=case['lines'];self.quotation.snapshot.save()
            value=self.get().json();self.assertEqual(value['profile'],profile)
            ids={row['id'] for row in value['document_requirements']}
            self.assertEqual('ip_licence' in ids,profile!='support_only')
            self.assertEqual('support_terms' in ids,profile!='ip')
            for line in value['lines']:
                self.assertTrue(all(row['value'] is None and row['state']=='pending' for row in line['inputs']))
                if line['kind']=='support':
                    self.assertNotIn('host_binding',line);self.assertNotIn('rights',line)
                    self.assertEqual({row['code'] for row in line['inputs']},{'prices','terms'})
                else:self.assertIsNone(line['rights']);self.assertEqual(line['host_binding'],'pending')
            self.assertEqual(value['money'],{'currency':'EUR','currency_status':'draft','subtotal_minor':None,'tax_minor':None,'total_minor':None})
            self.assertIsNone(value['quote_valid_until']);self.assertIsNone(value['payment_due_at'])
            self.assertFalse(value['publication_enabled'])
            if case==CASES[4]:self.assertTrue(value['lines'][0]['quotation_required'])
    def test_private_values_never_render_missing_fields_and_entity_flag_are_safe(self):
        self.prepare(bound=True)
        self.saved.details['licensed_entity']='PRIVATE_DIFFERENT_LICENSEE'
        self.saved.evaluation=business_rules.evaluate_details(self.saved.details);self.saved.save()
        value=self.get().json()
        self.assertTrue(value['business']['licensed_entity_review_required'])
        self.assertIn('registered_address',{r['field'] for r in value['business']['missing_required']})
        self.assertNotIn('tax_status',{r['field'] for r in value['business']['missing_required']})
        self.assertEqual(value['country_tax_choices'],'deferred')
        for text in [self.get().content.decode(),self.get(html=True).content.decode()]:
            for secret in ['PRIVATE_DIFFERENT_LICENSEE','BUSINESS_SCOPE_ONE_PRIVATE_SYNTHETIC','owner@scope.synthetic.invalid',self.saved.submission_digest,str(self.credential.generation)]:self.assertNotIn(secret,text)
        for field in business_rules.PENDING:self.assertIsNone(self.saved.details[field])
        html=self.get(html=True);self.assertNotContains(html,'<form');self.assertNotContains(html,'<input')
        self.assertContains(html,'Country/tax choices are explicitly deferred')
        self.assertEqual(html['Cache-Control'],'no-store');self.assertEqual(html['Referrer-Policy'],'no-referrer')
        self.assertEqual(html['Vary'],'Cookie');self.assertIn("form-action 'none'",html['Content-Security-Policy'])
    def test_source_catalog_invalid_business_and_inconsistent_links_fail_closed(self):
        self.prepare(bound=True)
        with patch.dict(DEFINITION,revision='f'*64):
            value=self.get().json();self.assertEqual(value['profile'],'unavailable');self.assertEqual(value['lines'],[])
            self.assertIn('captured_scope',{r['code'] for r in value['blockers']})
        with patch.dict(CATALOG,revision='f'*64):
            self.assertIn('catalog_revision',{r['code'] for r in self.get().json()['blockers']})
        self.saved.details['tax_status']='invented';self.saved.save()
        self.assertEqual(self.get().json()['business']['state'],'unavailable')
        self.saved.draft.owner=get_user_model().objects.create_user(username='unrelated-preparation-owner');self.saved.draft.save()
        self.assertEqual(self.get().status_code,409)
        cart=DraftCart.objects.create(owner=self.saved.draft.owner,version=2)
        foreign=CartSnapshot.objects.create(cart=cart,version=2,request_id=uuid.uuid4(),catalog_revision=CATALOG['revision'],lines=[],evaluation={})
        self.quotation.snapshot=foreign;self.quotation.save(update_fields=['snapshot'])
        self.assertEqual(self.get().status_code,404)
    def test_modes_host_recent_mfa_methods_queries_and_no_domain_writes(self):
        self.prepare()
        before=(QuotationRequest.objects.count(),QuotationReview.objects.count(),QuotationBusinessScope.objects.count(),BusinessDraftSnapshot.objects.count())
        for _ in range(2):self.assertEqual(self.get().status_code,200)
        after=(QuotationRequest.objects.count(),QuotationReview.objects.count(),QuotationBusinessScope.objects.count(),BusinessDraftSnapshot.objects.count())
        self.assertEqual(before,after)
        self.assertEqual(self.browser.get(self.prep+'?price=0&approve=true').status_code,400)
        self.assertEqual(self.post('quotation-requests/'+str(self.quotation.id)+'/preparation/',{'approve':True}).status_code,405)
        for mode in ['production','bank-sandbox']:
            with override_settings(SHOP_ENV=mode):self.assertEqual(self.get().status_code,404)
        self.assertEqual(self.browser.get(self.prep,HTTP_HOST='shop.xspi.pro').status_code,404)
        with self.owner_context():self.assertEqual(self.owner_client.get(self.prep).status_code,404)
        session=self.browser.session;marker=session['shop_staff_mfa'];marker['verified_at']-=301;session['shop_staff_mfa']=marker;session.save()
        self.assertEqual(self.get().status_code,403)
    def test_missing_review_or_tampered_approval_values_never_enable_actions(self):
        self.prepare();self.decision()
        QuotationRequest.objects.filter(pk=self.quotation.pk).update(review_version=2)
        self.assertEqual(self.get().json()['review']['code'],'unavailable')
        with patch.dict(CATALOG['approvals'],{key:True for key in CATALOG['approvals']}),patch.dict(CATALOG['money'],total_minor=0,tax_minor=0):
            value=self.get().json()
            self.assertIsNone(value['money']['total_minor']);self.assertIsNone(value['money']['tax_minor'])
            self.assertTrue(all(row['value'] is None for line in value['lines'] for row in line['inputs']))
            self.assertFalse(value['offer_creation_enabled']);self.assertFalse(value['publication_enabled'])
    def test_committed_review_prefix_does_not_mix_in_concurrent_correction(self):
        self.prepare();self.decision('needs_information')
        def correction_after_parent(quotation):
            def append():
                connections.close_all()
                try:
                    with transaction.atomic():
                        q=QuotationRequest.objects.select_for_update().get(pk=quotation.pk)
                        old=QuotationReview.objects.get(quotation=q,version=q.review_version)
                        QuotationReview.objects.create(quotation=q,version=2,business_version=0,request_id=uuid.uuid4(),snapshot_digest=old.snapshot_digest,
                            decision='declined',reviewer=self.user,reviewer_generation=self.credential.generation,mfa_verified_at=timezone.now())
                        q.review_version=2;q.save(update_fields=['review_version'])
                finally:connections.close_all()
            with ThreadPoolExecutor(max_workers=1) as pool:pool.submit(append).result(timeout=5)
            return assess(quotation)
        with patch('shop.access.preparation_views.assess',side_effect=correction_after_parent):
            value=self.get().json()
        self.assertEqual(value['review']['code'],'needs_information');self.assertEqual(value['latest_review_version'],1)
        self.assertEqual(self.get().json()['review']['code'],'declined')
