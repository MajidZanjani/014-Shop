"""Cross-route malformed-reference regressions from local workflow audit."""
import copy
import json
from unittest.mock import patch
import uuid
from django.contrib.auth import get_user_model
from django.test import TransactionTestCase, override_settings
from shop.catalog import binding_tests as fixtures
from shop.catalog.cart_tests import CASES
from shop.catalog.models import DraftCart, CartSnapshot, QuotationRequest, QuotationRequestKey, QuotationReview, QuotationBusinessScope
from shop.catalog.rules import CATALOG
from . import staff_tests
from .quotation_review import snapshot_digest


@override_settings(**staff_tests.STAFF_SETTINGS)
class WorkflowAuditTests(TransactionTestCase):
    setUp=fixtures.BusinessBindingTests.setUp
    post=fixtures.BusinessBindingTests.post
    challenge=fixtures.BusinessBindingTests.challenge
    authenticated=fixtures.BusinessBindingTests.authenticated
    grant=fixtures.BusinessBindingTests.grant
    owner_context=fixtures.BusinessBindingTests.owner_context
    owner_get=fixtures.BusinessBindingTests.owner_get
    attach=fixtures.BusinessBindingTests.attach
    business=fixtures.BusinessBindingTests.business
    enable_private=fixtures.BusinessBindingTests.enable_private
    review_value=fixtures.BusinessBindingTests.review_value
    def foreign(self):
        other=get_user_model().objects.create_user(username='foreign-audit-owner')
        cart=DraftCart.objects.create(owner=other,version=73)
        lines=copy.deepcopy(CASES[2]['lines']);lines[0]['quantity']=98761
        snapshot=CartSnapshot.objects.create(cart=cart,version=73,request_id=uuid.uuid4(),catalog_revision=CATALOG['revision'],lines=lines,evaluation={})
        return cart,snapshot
    def corrupt_parent(self):
        cart,snapshot=self.foreign()
        self.quotation.snapshot=snapshot;self.quotation.save(update_fields=['snapshot'])
        return cart,snapshot
    def owner_capture(self,value):
        with self.owner_context():return self.owner_client.post('/api/v1/quotation-requests/',data=json.dumps(value),content_type='application/json')
    def test_F01_customer_routes_reject_cross_cart_snapshot(self):
        self.corrupt_parent()
        for path in ['/api/v1/quotation-requests/'+str(self.quotation.id)+'/',self.path,
                     '/purchase/quotation-documents/'+str(self.quotation.id)+'/','/purchase/quotation-timeline/'+str(self.quotation.id)+'/']:
            with self.subTest(path=path):self.assertEqual(self.owner_get(path).status_code,404)
        self.assertEqual(self.owner_get('/api/v1/quotation-requests/').json()['requests'],[])
        self.assertEqual(self.attach().status_code,404)
        self.assertEqual(QuotationBusinessScope.objects.count(),0)
    def test_F01_staff_routes_and_review_write_reject_cross_cart_snapshot(self):
        self.authenticated();self.grant();self.corrupt_parent()
        for path in [self.detail,self.private]:
            with self.subTest(path=path):self.assertEqual(self.browser.get(path).status_code,404)
        self.assertEqual(self.browser.get('/staff/quotation-requests/').json()['requests'],[])
        value={'request_id':str(uuid.uuid4()),'expected_review_version':0,'snapshot_digest':snapshot_digest(self.quotation),'decision':'needs_information'}
        self.assertEqual(self.post(self.review_route,value).status_code,404)
        self.assertEqual(QuotationReview.objects.count(),0)
    def test_F01_capture_retry_alias_cannot_point_to_another_cart(self):
        cart,snapshot=self.foreign()
        other=QuotationRequest.objects.create(cart=cart,snapshot=snapshot,request_id=uuid.uuid4())
        own_cart=self.quotation.cart
        key=QuotationRequestKey.objects.create(cart=own_cart,quotation=other,request_id=uuid.uuid4())
        value={'cart_id':str(own_cart.id),'version':73,'request_id':str(key.request_id)}
        self.assertEqual(self.owner_capture(value).status_code,404)
        key.delete()
        # An existing snapshot request with an inconsistent parent cannot gain another retry alias.
        self.quotation.cart=cart;self.quotation.save(update_fields=['cart'])
        value.update(version=1,request_id=str(uuid.uuid4()))
        self.assertEqual(self.owner_capture(value).status_code,404)
        self.assertEqual(QuotationRequestKey.objects.count(),0)
    def test_F01_business_attachment_rechecks_owner_after_lock_wait(self):
        cart,snapshot=self.foreign()
        original=QuotationRequest.objects.select_for_update
        def reassign_before_lock(*args,**kwargs):
            QuotationRequest.objects.filter(pk=self.quotation.pk).update(cart=cart,snapshot=snapshot)
            return original(*args,**kwargs)
        with patch('shop.catalog.business_binding_views.QuotationRequest.objects.select_for_update',side_effect=reassign_before_lock):
            response=self.attach()
        self.assertEqual(response.status_code,404)
        self.assertEqual(QuotationBusinessScope.objects.count(),0)
    def test_F01_existing_review_replay_cannot_bypass_parent_identity(self):
        self.authenticated();self.grant();value=self.review_value()
        self.assertEqual(self.post(self.review_route,value).status_code,201)
        self.corrupt_parent()
        self.assertEqual(self.post(self.review_route,value).status_code,404)
        self.assertEqual(QuotationReview.objects.count(),1)
    def test_F02_history_and_replay_recheck_recorded_scope_owner(self):
        self.authenticated();self.grant();self.assertEqual(self.attach().status_code,303);self.enable_private(1)
        value=self.review_value();self.assertEqual(self.post(self.review_route,value).status_code,201)
        self.saved.draft.owner=get_user_model().objects.create_user(username='foreign-review-business-owner');self.saved.draft.save()
        with self.subTest(operation='history'):
            response=self.browser.get(self.detail);self.assertEqual(response.status_code,200)
            self.assertIsNone(response.json()['snapshot_digest'])
            self.assertIsNone(response.json()['reviews'][0]['snapshot_digest'])
        with self.subTest(operation='retry'):
            self.assertEqual(self.post(self.review_route,value).status_code,409)
        self.assertEqual(QuotationReview.objects.count(),1)
    def test_F02_valid_old_scope_history_and_retry_remain_source_independent(self):
        self.authenticated();self.grant();self.assertEqual(self.attach().status_code,303);self.enable_private(1)
        value=self.review_value();original=self.post(self.review_route,value);self.assertEqual(original.status_code,201)
        self.business(2,'SECOND_PRIVATE_AUDIT_BUSINESS')
        self.assertEqual(self.attach(dict(self.request,request_id=str(uuid.uuid4()),expected_scope_version='1',business_version='2')).status_code,303)
        from shop.catalog import business_rules
        with patch.object(business_rules,'SOURCE_SHA256','f'*64):
            response=self.browser.get(self.detail)
            self.assertFalse(response.json()['private_business_access'])
            self.assertEqual(response.json()['reviews'][0]['snapshot_digest'],value['snapshot_digest'])
            self.assertEqual(self.post(self.review_route,value).json()['review'],original.json()['review'])
