"""Supported-route local journey. Real PG/CSRF; no forced login/domain fixtures."""
import copy
from html.parser import HTMLParser
import io
import json
from pathlib import Path
import re
import stat
import tempfile
from urllib.parse import urlencode
import uuid
from django.core.management import call_command
from django.test import Client, TransactionTestCase, override_settings
from shop.catalog.cart_tests import CASES
from shop.catalog.models import DraftCart, QuotationRequest, BusinessDraftSnapshot, QuotationBusinessScope, QuotationReview
from shop.catalog.rules import CATALOG
from .models import PreparationAssessment
from . import staff_tests


class HiddenForms(HTMLParser):
    def __init__(self,html):
        super().__init__();self.forms=[];self.current=None;self.feed(html)
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=='form':self.current={};self.forms.append(self.current)
        if tag=='input' and self.current is not None and attrs.get('type')=='hidden' and 'name' in attrs:
            self.current[attrs['name']]=attrs.get('value','')
    def handle_endtag(self,tag):
        if tag=='form':self.current=None


class SupportedJourneyTests(TransactionTestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory();self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name)
        self.mail=self.root/'customer';self.codes=self.root/'staff';self.operator=self.root/'operator'
        for path in [self.mail,self.codes,self.operator]:path.mkdir(mode=0o700)
        config=override_settings(LOCAL_CAPTURE_ROOT=str(self.mail),LOCAL_STAFF_CAPTURE_ROOT=str(self.codes))
        config.enable();self.addCleanup(config.disable)
        self.customer=Client(enforce_csrf_checks=True,HTTP_HOST='127.0.0.1')
        self.staff=Client(enforce_csrf_checks=True,HTTP_HOST='staff.localhost')
        for model in [DraftCart,QuotationRequest,BusinessDraftSnapshot,QuotationBusinessScope,QuotationReview,PreparationAssessment]:self.assertEqual(model.objects.count(),0)
    def capture_value(self,root,before,label):
        added=set(root.iterdir())-before;self.assertEqual(len(added),1)
        path=added.pop();self.assertEqual(stat.S_IMODE(path.stat().st_mode),0o600)
        match=re.search('^'+label+r': (.+)$',path.read_text(),re.M);self.assertIsNotNone(match)
        return match[1]
    def customer_json(self,path,value,client=None):
        client=client or self.customer
        token=client.get('/api/v1/customer/session/').json()['csrf_token']
        return client.post(path,data=json.dumps(value),content_type='application/json',HTTP_X_CSRFTOKEN=token)
    def verify_customer(self,email,client=None):
        client=client or self.customer;before=set(self.mail.iterdir())
        result=self.customer_json('/api/v1/customer/request-code/',{'email':email},client);self.assertEqual(result.status_code,200)
        code=self.capture_value(self.mail,before,'Verification code')
        result=self.customer_json('/api/v1/customer/verify/',{'code':code},client);self.assertEqual(result.status_code,200)
        self.assertNotIn(code,result.content.decode());self.assertTrue(result.json()['authenticated'])
    def staff_get(self,path,html=False):
        with override_settings(**staff_tests.STAFF_SETTINGS):
            return self.staff.get(path,HTTP_ACCEPT='text/html' if html else 'application/json')
    def staff_json(self,path,value):
        with override_settings(**staff_tests.STAFF_SETTINGS):
            token=self.staff.get('/staff/session/').json()['csrf_token']
            return self.staff.post(path,data=json.dumps(value),content_type='application/json',HTTP_X_CSRFTOKEN=token)
    def staff_form(self,path,value):
        with override_settings(**staff_tests.STAFF_SETTINGS):
            return self.staff.post(path,data=urlencode(value),content_type='application/x-www-form-urlencoded',HTTP_ACCEPT='text/html')
    def local_operator(self,action,**options):
        call_command('local_staff',action,username='journey-reviewer',stdout=io.StringIO(),**options)
    def authenticate_staff(self):
        before=set(self.operator.iterdir());self.local_operator('provision',capture_root=str(self.operator))
        password=self.capture_value(self.operator,before,'Password')
        before=set(self.codes.iterdir())
        result=self.staff_json('/staff/login/',{'username':'journey-reviewer','password':password});self.assertEqual(result.status_code,200)
        code=self.capture_value(self.codes,before,'Code')
        self.assertEqual(self.staff_get('/staff/quotation-requests/').status_code,403)
        result=self.staff_json('/staff/verify/',{'code':code});self.assertEqual(result.status_code,200)
        self.assertNotIn(code,result.content.decode());self.assertNotIn(password,result.content.decode())
        self.assertEqual(self.staff_get('/staff/quotation-requests/').json()['requests'],[])
    def business_form(self,name):
        page=self.customer.get('/purchase/business/');self.assertEqual(page.status_code,200)
        form=HiddenForms(page.content.decode()).forms[0]
        form.update(legal_business_name=name,registered_address='10 Synthetic Avenue',purchasing_name='PRIVATE_JOURNEY_PURCHASER',
            business_email='purchaser@journey.synthetic.invalid',tax_number='PRIVATE_JOURNEY_TAX',
            billing_same_as_registered='on',technical_same_as_purchasing='on')
        return form
    def save_business(self,form):
        result=self.customer.post('/purchase/business/',data=urlencode(form),content_type='application/x-www-form-urlencoded')
        self.assertEqual(result.status_code,303)
    def review(self,detail,code):
        page=self.staff_get(detail,html=True);self.assertEqual(page.status_code,200)
        form=HiddenForms(page.content.decode()).forms[0];form['decision']=code
        self.assertEqual(self.staff_form(detail+'reviews/',form).status_code,303)
    def round_trip(self,case,profile):
        self.assertEqual(self.customer.get('/api/v1/cart/').status_code,401)
        self.verify_customer('buyer@journey.synthetic.invalid')
        self.authenticate_staff()
        lines=copy.deepcopy(case['lines'])
        cart={'request_id':str(uuid.uuid4()),'expected_version':0,'catalog_revision':CATALOG['revision'],'lines':lines}
        response=self.customer_json('/api/v1/cart/',cart);self.assertEqual(response.status_code,201);saved=response.json()
        self.assertEqual(self.customer_json('/api/v1/cart/',cart).json(),saved)
        request={'request_id':str(uuid.uuid4()),'cart_id':saved['cart_id'],'version':saved['version']}
        response=self.customer_json('/api/v1/quotation-requests/',request);self.assertEqual(response.status_code,201)
        identity=response.json()['id'];owner_detail='/api/v1/quotation-requests/'+identity+'/'
        detail='/staff/quotation-requests/'+identity+'/'
        self.assertEqual(self.customer_json('/api/v1/quotation-requests/',request).status_code,200)
        business=self.business_form('PRIVATE_JOURNEY_BUSINESS — 測試')
        self.save_business(business);self.save_business(business)
        self.assertEqual(BusinessDraftSnapshot.objects.count(),1)
        binding='/purchase/quotation-business/'+identity+'/'
        page=self.customer.get(binding);form=next(f for f in HiddenForms(page.content.decode()).forms if f.get('action')=='attach')
        for _ in range(2):self.assertEqual(self.customer.post(binding,data=urlencode(form),content_type='application/x-www-form-urlencoded').status_code,303)
        self.assertEqual(QuotationBusinessScope.objects.count(),1)
        self.assertEqual(self.staff_get(detail).status_code,404)
        self.local_operator('grant',quotation=identity)
        self.assertEqual(self.staff_get(detail+'business/').status_code,403)
        self.assertEqual(self.staff_get(detail+'preparation/').status_code,403)
        self.local_operator('grant-business',quotation=identity,business_scope=1)
        private=self.staff_get(detail+'business/');self.assertEqual(private.status_code,200)
        self.assertEqual(private.json()['details']['legal_business_name'],'PRIVATE_JOURNEY_BUSINESS — 測試')
        for field in ['registration_country','tax_status','deployment_country']:self.assertIsNone(private.json()['details'][field])
        self.review(detail,'ready_for_commercial_review')
        owner=self.customer.get(owner_detail);self.assertEqual(owner.json()['review_status']['code'],'ready_for_commercial_review')
        self.assertFalse(owner.json()['checkout_enabled']);self.assertFalse(owner.json()['acceptance_enabled'])
        documents=self.customer.get('/purchase/quotation-documents/'+identity+'/');self.assertEqual(documents.status_code,200)
        if profile=='support_only':self.assertNotContains(documents,'NIC / host IDs');self.assertNotContains(documents,'xSPI-MC IP Licence Agreement')
        else:self.assertContains(documents,'NIC / host IDs')
        snap=detail+'preparation-snapshots/'
        form=HiddenForms(self.staff_get(snap,html=True).content.decode()).forms[0]
        for _ in range(2):
            result=self.staff_form(snap,form);self.assertEqual(result.status_code,303)
        self.assertEqual(PreparationAssessment.objects.count(),1)
        retained=self.staff_get(snap+'1/').json();self.assertEqual(retained['assessment']['profile'],profile)
        compare=snap+'1/compare/'
        self.assertEqual(self.staff_get(compare).json()['state'],'no_differences')
        stale=HiddenForms(self.staff_get(snap,html=True).content.decode()).forms[0]
        self.review(detail,'needs_information')
        self.assertEqual(self.customer.get(owner_detail).json()['review_status']['code'],'needs_information')
        self.assertEqual(self.staff_form(snap,stale).status_code,409)
        self.assertEqual(self.staff_form(snap,form).status_code,303)
        self.assertEqual(self.staff_get(snap+'1/').json(),retained)
        self.assertIn('review',{r['code'] for r in self.staff_get(compare).json()['categories'] if r['changed']})
        edited=copy.deepcopy(CASES[2]['lines']);edited[0]['quantity']=3
        cart.update(request_id=str(uuid.uuid4()),expected_version=1,lines=edited)
        self.assertEqual(self.customer_json('/api/v1/cart/',cart).status_code,201)
        self.assertEqual(self.customer.get(owner_detail).json()['lines'],lines)
        self.save_business(self.business_form('PRIVATE_JOURNEY_UNATTACHED_BUSINESS'))
        self.assertEqual(self.staff_get(detail+'business/').json()['business_draft_version'],1)
        history=self.customer.get('/purchase/quotations/');self.assertEqual(history.status_code,200)
        self.assertContains(history,'/purchase/quotation-timeline/'+identity+'/')
        self.assertContains(history,'/purchase/quotation-documents/'+identity+'/')
        timeline=self.customer.get('/purchase/quotation-timeline/'+identity+'/');self.assertEqual(timeline.status_code,200)
        other=Client(enforce_csrf_checks=True,HTTP_HOST='127.0.0.1');self.verify_customer('other@journey.synthetic.invalid',other)
        self.assertEqual(other.get('/purchase/quotations/').context['items'],[])
        self.assertEqual(other.get(owner_detail).status_code,404);self.assertEqual(other.get('/api/v1/quotation-requests/').json()['requests'],[])
        for response in [owner,documents,timeline,self.staff_get(detail),self.staff_get(snap+'1/'),self.staff_get(compare)]:
            text=response.content.decode()
            for value in ['PRIVATE_JOURNEY_BUSINESS','PRIVATE_JOURNEY_TAX','PRIVATE_JOURNEY_PURCHASER','PRIVATE_JOURNEY_UNATTACHED_BUSINESS']:self.assertNotIn(value,text)
            self.assertEqual(response['Cache-Control'],'no-store')
        self.local_operator('revoke-business',quotation=identity)
        for path in [detail+'business/',detail+'preparation/',snap+'1/',compare]:self.assertEqual(self.staff_get(path).status_code,403)
        self.assertIsNone(self.staff_get(detail).json()['reviews'][0]['snapshot_digest'])
        self.assertEqual(self.staff_json('/staff/logout/',{}).status_code,200)
        self.assertEqual(self.staff_get(detail).status_code,403)
        self.assertEqual(self.customer.get(owner_detail).status_code,200)
        self.assertEqual(self.customer_json('/api/v1/customer/logout/',{}).status_code,200)
        self.assertEqual(self.customer.get(owner_detail).status_code,401)
        self.assertEqual(QuotationRequest.objects.count(),1);self.assertEqual(QuotationReview.objects.count(),2)
        self.assertEqual(PreparationAssessment.objects.count(),1)
    def test_mixed_customer_to_staff_round_trip(self):self.round_trip(CASES[3],'mixed')
    def test_support_only_customer_to_staff_round_trip(self):self.round_trip(CASES[2],'support_only')
