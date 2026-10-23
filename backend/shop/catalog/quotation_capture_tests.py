"""Deliberate form capture interoperates with existing API snapshot/key arbitration."""
import copy
import json
from pathlib import Path
from urllib.parse import urlencode
from unittest.mock import patch
import uuid
from django.test import Client,TransactionTestCase,override_settings
from shop.access import tests as access_tests
from shop.access.journey_tests import HiddenForms
from . import cart_editor_tests as carts
from .models import QuotationRequest,QuotationRequestKey,CartSnapshot
from .rules import CATALOG

PATH='/purchase/request-quotation/'

class QuotationCaptureTests(TransactionTestCase):
    setUp=carts.CartEditorTests.setUp
    form=carts.CartEditorTests.form
    ip=carts.CartEditorTests.ip
    cart=carts.CartEditorTests.cart
    def cart_post(self,form):return carts.CartEditorTests.post(self,form)
    def quote_form(self):
        response=self.browser.get(PATH);self.assertEqual(response.status_code,200)
        return HiddenForms(response.content.decode()).forms[0]
    def post(self,form):
        return self.browser.post(PATH,data=urlencode(form),content_type='application/x-www-form-urlencoded')
    def save_support(self,quantity='2'):
        form=self.form('add_support');form['quantity']=quantity
        self.assertEqual(self.cart_post(form).status_code,303);return form

    def test_mixed_review_capture_replay_alias_and_later_edits(self):
        self.assertEqual(self.cart_post(self.ip()).status_code,303)
        self.save_support()
        form=self.quote_form();page=self.browser.get(PATH)
        self.assertContains(page,'IP · altera');self.assertContains(page,'10-hour support packages: 2')
        self.assertEqual(QuotationRequest.objects.count(),0)
        response=self.post(form);self.assertEqual(response.status_code,303)
        row=QuotationRequest.objects.get();self.assertEqual(response['Location'],'/purchase/quotation-timeline/'+str(row.pk)+'/')
        captured=copy.deepcopy(row.snapshot.lines)
        update=self.form('add_support');update['quantity']='3';self.assertEqual(self.cart_post(update).status_code,303)
        with patch.dict(CATALOG,revision='f'*64):self.assertEqual(self.post(form).status_code,303)
        alias=dict(form,request_id=str(uuid.uuid4()));self.assertEqual(self.post(alias).status_code,303)
        self.assertEqual(QuotationRequest.objects.count(),1);self.assertEqual(QuotationRequestKey.objects.count(),2)
        row.refresh_from_db();self.assertEqual(row.snapshot.lines,captured)
        self.assertEqual(self.post(dict(form,version='3')).status_code,409)
        for path in (response['Location'],'/purchase/quotation-documents/'+str(row.pk)+'/', '/purchase/quotations/'):
            result=self.browser.get(path);self.assertEqual(result.status_code,200)
            self.assertEqual(result['Cache-Control'],'no-store')
            self.assertNotContains(result,'engineer@synthetic.invalid')
        self.assertEqual(response['Referrer-Policy'],'no-referrer')

    def test_support_only_entire_customer_entry_cart_and_quote_use_forms(self):
        self.browser=Client(enforce_csrf_checks=True)
        page=self.browser.get('/purchase/access/')
        form=HiddenForms(page.content.decode()).forms[0];form['email']='nojs@quote.synthetic.invalid'
        before=set(Path(self.directory.name).iterdir())
        self.assertEqual(self.browser.post('/purchase/access/',data=urlencode(form),content_type='application/x-www-form-urlencoded').status_code,303)
        code=access_tests.captured_code(self.directory.name,before)
        page=self.browser.get('/purchase/access/')
        verify=next(f for f in HiddenForms(page.content.decode()).forms if f['action']=='verify');verify['code']=code
        self.assertEqual(self.browser.post('/purchase/access/',data=urlencode(verify),content_type='application/x-www-form-urlencoded').status_code,303)
        self.save_support('3')
        form=self.quote_form();response=self.post(form);self.assertEqual(response.status_code,303)
        row=QuotationRequest.objects.get();self.assertEqual(row.snapshot.evaluation['quoted_support_seconds'],108000)
        self.assertEqual(row.snapshot.lines[0]['kind'],'support')
        documents=self.browser.get('/purchase/quotation-documents/'+str(row.pk)+'/')
        self.assertNotContains(documents,'NIC / host IDs');self.assertNotContains(documents,'xSPI-MC IP Licence Agreement')
        for value in ('nojs@quote.synthetic.invalid',code):self.assertNotContains(documents,value)
        self.assertEqual(QuotationRequestKey.objects.count(),1)

    def test_empty_stale_catalog_and_uncaptured_old_revision_fail_without_capture(self):
        self.assertEqual(HiddenForms(self.browser.get(PATH).content.decode()).forms,[])
        self.save_support();old=self.quote_form()
        with patch.dict(CATALOG,revision='f'*64):
            self.assertEqual(HiddenForms(self.browser.get(PATH).content.decode()).forms,[])
            self.assertEqual(self.post(old).status_code,409)
        update=self.form('save_support');update['quantity']='3';self.assertEqual(self.cart_post(update).status_code,303)
        self.assertEqual(self.post(old).status_code,409)
        remove=self.form('remove');self.assertEqual(self.cart_post(remove).status_code,303)
        empty=dict(old,version='3',request_id=str(uuid.uuid4()))
        self.assertEqual(self.post(empty).status_code,422)
        self.assertEqual(QuotationRequest.objects.count(),0);self.assertEqual(QuotationRequestKey.objects.count(),0)

    def test_strict_fields_csrf_no_reflection_and_no_get_effects(self):
        self.save_support();form=self.quote_form()
        for changes in ({'version':'01'},{'version':'0'},{'cart_id':'private-host-id'},{'request_id':'bad'},{'action':'pay'},
                        {'next':'https://private.invalid'},{'tax_details':'PRIVATE_TAX_QUOTE'},{'version':'1'*1100}):
            response=self.post(dict(form,**changes));self.assertEqual(response.status_code,400)
            for value in ('private-host-id','https://private.invalid','PRIVATE_TAX_QUOTE'):self.assertNotContains(response,value,status_code=400)
        self.assertEqual(self.post(list(form.items())+[('version','2')]).status_code,400)
        self.assertEqual(self.browser.post(PATH,{'action':'request'}).status_code,403)
        self.assertEqual(self.browser.get(PATH+'?next=/private').status_code,400)
        page=self.browser.get(PATH);self.assertEqual(page['Cache-Control'],'no-store')
        self.assertIn("form-action 'self'",page['Content-Security-Policy']);self.assertNotContains(page,'<script')
        self.assertEqual(QuotationRequest.objects.count(),0)
        self.assertEqual(CartSnapshot.objects.count(),1)

    def test_foreign_cart_and_environment_are_closed(self):
        self.save_support();form=self.quote_form()
        other=Client(enforce_csrf_checks=True)
        code=access_tests.request_capture(other,self.directory.name,'other@quote.synthetic.invalid')
        self.assertEqual(access_tests.csrf_post(other,access_tests.BASE+'verify/',{'code':code}).status_code,200)
        form.pop('csrfmiddlewaretoken');token=other.get(access_tests.BASE+'session/').json()['csrf_token']
        self.assertEqual(other.post(PATH,data=urlencode(form),content_type='application/x-www-form-urlencoded',HTTP_X_CSRFTOKEN=token).status_code,404)
        self.assertEqual(Client().get(PATH).status_code,401)
        for env in ('production','bank-sandbox'):
            with override_settings(SHOP_ENV=env):self.assertEqual(self.browser.get(PATH).status_code,404)
        self.assertEqual(QuotationRequest.objects.count(),0)

    def test_concurrent_form_and_json_aliases_capture_one_snapshot_once(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        from django.db import connections
        self.save_support();form=self.quote_form()
        value={key:form[key] for key in ('request_id','cart_id','version')};value['request_id']=str(uuid.uuid4());value['version']=int(value['version'])
        clients=[Client(enforce_csrf_checks=True),Client(enforce_csrf_checks=True)]
        for client in clients:client.cookies=copy.deepcopy(self.browser.cookies)
        barrier=Barrier(2)
        def submit(index):
            try:
                barrier.wait(timeout=10)
                if index==0:return clients[index].post(PATH,data=urlencode(form),content_type='application/x-www-form-urlencoded').status_code
                return clients[index].post('/api/v1/quotation-requests/',data=json.dumps(value),content_type='application/json',HTTP_X_CSRFTOKEN=clients[index].cookies['csrftoken'].value).status_code
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:statuses=list(pool.map(submit,range(2)))
        self.assertEqual(statuses[0],303);self.assertIn(statuses[1],(200,201))
        self.assertEqual(QuotationRequest.objects.count(),1);self.assertEqual(QuotationRequestKey.objects.count(),2)
