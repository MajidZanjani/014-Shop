"""Saved form commands share PostgreSQL/API CAS and retry semantics."""
import copy
import json
from pathlib import Path
import tempfile
from urllib.parse import urlencode
from unittest.mock import patch
import uuid
from django.test import Client,TransactionTestCase,override_settings
from shop.access import tests as access_tests
from shop.access.journey_tests import HiddenForms
from .models import DraftCart,CartSnapshot,QuotationRequest
from .rules import CATALOG

PATH='/purchase/cart/'

class CartEditorTests(TransactionTestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory();self.addCleanup(self.directory.cleanup)
        config=override_settings(LOCAL_CAPTURE_ROOT=self.directory.name);config.enable();self.addCleanup(config.disable)
        self.browser=Client(enforce_csrf_checks=True)
        code=access_tests.request_capture(self.browser,self.directory.name)
        self.assertEqual(access_tests.csrf_post(self.browser,access_tests.BASE+'verify/',{'code':code}).status_code,200)

    def form(self,action,path=PATH,line=None):
        page=self.browser.get(path);self.assertEqual(page.status_code,200)
        forms=HiddenForms(page.content.decode()).forms
        return next(form for form in forms if form.get('action')==action and (line is None or form.get('line_id')==line))

    def post(self,form):
        return self.browser.post(PATH,data=urlencode(form,doseq=True),content_type='application/x-www-form-urlencoded')

    def ip(self,**changes):
        result=self.form('add_ip')
        result.update(vendor='altera',families=['altera-agilex-5'],term='rd-annual',production_band='',production_units='',fixed_nodes='1',floating_nodes='0')
        result.update(changes);return result

    def cart(self):return self.browser.get('/api/v1/cart/').json()

    def test_complete_mixed_cart_add_edit_remove_and_api_interoperability(self):
        self.assertEqual(DraftCart.objects.count(),0)
        form=self.ip();self.assertEqual(self.post(form).status_code,303)
        line=form['line_id'];self.assertEqual(self.cart()['version'],1)
        support=self.form('add_support');support['quantity']='2'
        self.assertEqual(self.post(support).status_code,303)
        self.assertEqual(self.cart()['evaluation']['quoted_support_seconds'],72000)
        edit=self.form('save_ip',PATH+'?edit='+line);edit.update(vendor='altera',families=['altera-agilex-5'],term='rd-annual',production_band='',production_units='',fixed_nodes='2',floating_nodes='0')
        self.assertEqual(self.post(edit).status_code,303)
        self.assertEqual(self.cart()['lines'][0]['configuration']['fixed_nodes'],2)
        quantity=self.form('save_support',line=support['line_id']);quantity['quantity']='3'
        self.assertEqual(self.post(quantity).status_code,303)
        self.assertEqual(self.cart()['evaluation']['quoted_support_seconds'],108000)
        remove=self.form('remove',line=line);self.assertEqual(self.post(remove).status_code,303)
        self.assertEqual(len(self.cart()['lines']),1)
        current=self.cart()
        result=access_tests.csrf_post(self.browser,'/api/v1/cart/',{'request_id':str(uuid.uuid4()),'expected_version':current['version'],'catalog_revision':CATALOG['revision'],'lines':current['lines']})
        self.assertEqual(result.status_code,201)
        page=self.browser.get(PATH);self.assertContains(page,'Saved cart revision 6')
        self.assertEqual(page['Cache-Control'],'no-store');self.assertEqual(page['Referrer-Policy'],'same-origin')
        self.assertIn("form-action 'self'",page['Content-Security-Policy'])
        self.assertNotContains(page,'<script');self.assertNotContains(page,'engineer@synthetic.invalid')
        self.assertEqual(QuotationRequest.objects.count(),0)

    def test_exact_retries_survive_later_edit_and_catalog_revision_change(self):
        original=self.form('add_support');original['quantity']='2'
        self.assertEqual(self.post(original).status_code,303)
        next_form=self.form('save_support',line=original['line_id']);next_form['quantity']='3'
        self.assertEqual(self.post(next_form).status_code,303)
        with patch.dict(CATALOG,revision='f'*64):self.assertEqual(self.post(original).status_code,303)
        self.assertEqual(dict(self.browser.session)['cart_saved_notice'],{'version':1,'replayed':True})
        page=self.browser.get(PATH)
        self.assertContains(page,'Earlier cart submission confirmed at revision 1')
        self.assertContains(page,'Current cart revision 2 is shown below.')
        self.assertContains(page,'Later changes remain saved.')
        self.assertNotContains(self.browser.get(PATH),'Earlier cart submission confirmed')
        self.assertEqual(self.cart()['version'],2)
        self.assertEqual(self.cart()['lines'][0]['quantity'],3)
        self.assertEqual(CartSnapshot.objects.count(),2)
        changed=dict(original,quantity='4');self.assertEqual(self.post(changed).status_code,409)
        stale=dict(original,request_id=str(uuid.uuid4()));self.assertEqual(self.post(stale).status_code,409)
        removed=self.form('remove',line=original['line_id']);self.assertEqual(self.post(removed).status_code,303)
        self.assertEqual(self.post(removed).status_code,303)
        self.assertEqual(self.cart()['lines'],[])
        self.assertEqual(CartSnapshot.objects.count(),3)
        page=self.browser.get(PATH)
        self.assertContains(page,'Earlier cart submission confirmed at revision 3')
        self.assertNotContains(page,'Later changes remain saved.')
        for notice in (True,{'version':True,'replayed':True},{'version':1,'replayed':'PRIVATE_NOTICE'}, {'version':1,'replayed':False,'raw':'PRIVATE_NOTICE'}):
            session=self.browser.session;session['cart_saved_notice']=notice;session.save()
            response=self.browser.get(PATH)
            self.assertEqual(response.status_code,200)
            self.assertNotContains(response,'PRIVATE_NOTICE')
            self.assertNotContains(response,'Cart change saved at revision')

    def test_invalid_ip_domains_support_values_and_max_lines_never_save(self):
        for updates in ({'vendor':'amd'},{'families':['not-a-family']},{'fixed_nodes':'0'},
                        {'term':'rdp-yearly','production_band':''},{'production_units':'1'}):
            self.assertEqual(self.post(self.ip(**updates)).status_code,422,updates)
        for quantity in ('0','-1','1.5','1000001','true','01'):
            form=self.form('add_support');form['quantity']=quantity
            self.assertEqual(self.post(form).status_code,422)
        self.assertEqual(DraftCart.objects.count(),0);self.assertEqual(CartSnapshot.objects.count(),0)
        lines=[{'id':str(uuid.uuid4()),'kind':'support','product_id':CATALOG['support_product_id'],'quantity':1} for _ in range(20)]
        self.assertEqual(access_tests.csrf_post(self.browser,'/api/v1/cart/',{'request_id':str(uuid.uuid4()),'expected_version':0,'catalog_revision':CATALOG['revision'],'lines':lines}).status_code,201)
        extra=self.form('add_support');extra['quantity']='1'
        self.assertEqual(self.post(extra).status_code,422);self.assertEqual(CartSnapshot.objects.count(),1)

    def test_strict_parser_csrf_queries_and_no_input_echo(self):
        form=self.form('add_support');form['quantity']='1'
        for changes in ({'host_id':'PRIVATE_CART_HOST'},{'expected_version':'01'},{'catalog_revision':'x'*64},{'line_id':'bad'},{'owner':'private'}, {'quantity':'1','next':'https://private.invalid'}):
            response=self.post(dict(form,**changes));self.assertEqual(response.status_code,400)
            self.assertNotContains(response,'PRIVATE_CART_HOST',status_code=400)
            self.assertNotContains(response,'https://private.invalid',status_code=400)
        duplicate=list(form.items())+[('quantity','2')]
        self.assertEqual(self.post(duplicate).status_code,400)
        oversized=dict(form,quantity='x'*8193);self.assertEqual(self.post(oversized).status_code,400)
        token=self.browser.cookies['csrftoken'].value
        self.assertEqual(self.browser.post(PATH,data='{}',content_type='application/json',HTTP_X_CSRFTOKEN=token).status_code,400)
        self.assertEqual(self.browser.post(PATH,data={'action':'add_support'}).status_code,403)
        for query in ('owner=1','edit=bad','edit='+str(uuid.uuid4())+'&edit='+str(uuid.uuid4())):
            self.assertEqual(self.browser.get(PATH+'?'+query).status_code,400)
        self.assertEqual(self.browser.get(PATH+'?edit='+str(uuid.uuid4())).status_code,404)
        self.assertEqual(DraftCart.objects.count(),0)

    def test_owner_environment_scope_and_missing_base_revision(self):
        original=self.form('add_support');original['quantity']='2';self.assertEqual(self.post(original).status_code,303)
        other=Client(enforce_csrf_checks=True)
        code=access_tests.request_capture(other,self.directory.name,'other@cart.synthetic.invalid')
        self.assertEqual(access_tests.csrf_post(other,access_tests.BASE+'verify/',{'code':code}).status_code,200)
        self.assertEqual(other.get(PATH+'?edit='+original['line_id']).status_code,404)
        token=other.get(access_tests.BASE+'session/').json()['csrf_token']
        command=dict(original,action='remove',expected_version='1');command.pop('quantity');command.pop('csrfmiddlewaretoken')
        response=other.post(PATH,data=urlencode(command),content_type='application/x-www-form-urlencoded',HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code,404)
        self.assertEqual(Client().get(PATH).status_code,401)
        for env in ('production','bank-sandbox'):
            with override_settings(SHOP_ENV=env):self.assertEqual(self.browser.get(PATH).status_code,404)
        self.assertEqual(CartSnapshot.objects.count(),1)

    def test_form_and_json_competing_first_save_commit_one_exact_snapshot(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        from django.db import connections
        form=self.form('add_support');form['quantity']='2'
        payload={'request_id':str(uuid.uuid4()),'expected_version':0,'catalog_revision':CATALOG['revision'],
            'lines':[{'id':str(uuid.uuid4()),'kind':'support','product_id':CATALOG['support_product_id'],'quantity':3}]}
        barrier=Barrier(2)
        clients=[Client(enforce_csrf_checks=True),Client(enforce_csrf_checks=True)]
        for client in clients:client.cookies=copy.deepcopy(self.browser.cookies)
        def submit(index):
            try:
                barrier.wait(timeout=10)
                if index==0:return clients[index].post(PATH,data=urlencode(form),content_type='application/x-www-form-urlencoded').status_code
                return clients[index].post('/api/v1/cart/',data=json.dumps(payload),content_type='application/json',HTTP_X_CSRFTOKEN=clients[index].cookies['csrftoken'].value).status_code
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:statuses=list(pool.map(submit,range(2)))
        self.assertIn(statuses,([303,409],[409,201]))
        self.assertEqual(CartSnapshot.objects.count(),1)
        self.assertEqual(len(self.cart()['lines']),1)
        self.assertIn(self.cart()['lines'][0]['quantity'],(2,3))

    def test_snapshot_reads_recheck_owner_after_parent_lookup(self):
        from django.contrib.auth import get_user_model
        from django.db.models.query import QuerySet
        form=self.form('add_support');form['quantity']='712341'
        self.assertEqual(self.post(form).status_code,303)
        cart=DraftCart.objects.get();owner=cart.owner
        other=get_user_model().objects.create_user(username='cart-owner-change-audit')
        original=QuerySet.first
        for path in (PATH,'/purchase/request-quotation/','/api/v1/cart/'):
            moved=False
            def first(query):
                nonlocal moved
                row=original(query)
                if query.model is DraftCart and row is not None and row.pk==cart.pk and not moved:
                    moved=True
                    DraftCart.objects.filter(pk=cart.pk).update(owner=other)
                return row
            try:
                with patch.object(QuerySet,'first',first):response=self.browser.get(path)
                self.assertTrue(moved)
                self.assertEqual(response.status_code,404,path)
                self.assertNotContains(response,'712341',status_code=404)
            finally:DraftCart.objects.filter(pk=cart.pk).update(owner=owner)
