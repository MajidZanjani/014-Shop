import copy
import json
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.db import connections
from django.test import Client, TransactionTestCase, override_settings
from .cart_tests import CASES
from .models import QuotationRequest, QuotationRequestKey
from .rules import CATALOG
from .tests import verified_login

URL='/api/v1/quotation-requests/'

class QuotationTests(TransactionTestCase):
    def setUp(self):
        self.owner=get_user_model().objects.create_user(username='quotation-owner')
        self.other=get_user_model().objects.create_user(username='quotation-other')
        verified_login(self.client,self.owner)
        self.saved=self.save_cart(0,CASES[1]['lines'])
        self.payload={'request_id':str(uuid.uuid4()),'cart_id':self.saved['cart_id'],'version':1}
    def save_cart(self,version,lines):
        response=self.client.post('/api/v1/cart/',data=json.dumps({'request_id':str(uuid.uuid4()),'expected_version':version,'catalog_revision':CATALOG['revision'],'lines':copy.deepcopy(lines)}),content_type='application/json')
        self.assertEqual(response.status_code,201)
        return response.json()
    def post(self,payload=None,client=None):
        return (client or self.client).post(URL,data=json.dumps(self.payload if payload is None else payload),content_type='application/json')
    def test_exact_capture_replay_and_later_edits(self):
        first=self.post();self.assertEqual(first.status_code,201)
        self.assertEqual(first.json()['lines'],self.saved['lines'])
        self.assertEqual(first.json()['evaluation'],self.saved['evaluation'])
        self.assertFalse(first.json()['checkout_enabled']);self.assertFalse(first.json()['acceptance_enabled'])
        self.assertIsNone(first.json()['prices']);self.assertIsNone(first.json()['rights'])
        alias=dict(self.payload,request_id=str(uuid.uuid4()))
        self.assertEqual(self.post(alias).json(),first.json())
        self.save_cart(1,CASES[2]['lines'])
        with patch.dict(CATALOG,revision='f'*64):
            self.assertEqual(self.post().json(),first.json())
            self.assertEqual(self.post(alias).json(),first.json())
            self.assertEqual(self.post(dict(self.payload,request_id=str(uuid.uuid4()),version=2)).status_code,409)
        self.assertEqual(self.post(dict(alias,version=2)).status_code,409)
        self.assertEqual(self.client.get(URL+first.json()['id']+'/').json(),first.json())
        self.assertEqual(QuotationRequest.objects.count(),1)
        self.assertEqual(first['Cache-Control'],'no-store')
    def test_freshness_empty_and_support(self):
        self.save_cart(1,[])
        self.assertEqual(self.post().status_code,409)
        self.assertEqual(self.post(dict(self.payload,version=2)).status_code,422)
        self.save_cart(2,CASES[2]['lines'])
        result=self.post(dict(self.payload,version=3));self.assertEqual(result.status_code,201)
        self.assertEqual(result.json()['evaluation']['quoted_support_seconds'],72000)
        self.assertEqual(len(result.json()['lines']),1)
    def test_owner_auth_and_production_boundaries(self):
        first=self.post().json();detail=URL+first['id']+'/'
        self.assertEqual(self.post(client=Client()).status_code,401)
        strict=Client(enforce_csrf_checks=True);verified_login(strict,self.owner)
        self.assertEqual(self.post(client=strict).status_code,403)
        verified_login(self.client,self.other)
        self.assertEqual(self.client.get(URL).json()['requests'],[])
        self.assertEqual(self.client.get(detail).status_code,404)
        self.assertEqual(self.post().status_code,404)
        with override_settings(SHOP_ENV='production'):
            for path in [URL,detail]:self.assertEqual(self.client.get(path).status_code,404)
            self.assertEqual(self.post().status_code,404)
        self.other.is_staff=True;self.other.save()
        self.assertEqual(self.post().status_code,403)
        self.other.is_staff=False;self.other.save()
        session=self.client.session;session.pop('shop_verified_identity');session.save()
        self.assertEqual(self.client.get(detail).status_code,403)
    def test_parser_scope_and_methods(self):
        for payload in [dict(self.payload,version=True),dict(self.payload,owner=1),dict(self.payload,version=0),dict(self.payload,cart_id=1),dict(self.payload,version='1')]:
            self.assertEqual(self.post(payload).status_code,400)
        for raw in ['NaN','{}','{"version":1,"version":2}','x'*1025]:
            self.assertEqual(self.client.post(URL,data=raw,content_type='application/json').status_code,400)
        self.assertEqual(self.client.post(URL,data='{}',content_type='text/plain').status_code,415)
        self.assertEqual(self.client.get(URL+'?owner=1').status_code,400)
        self.assertEqual(self.client.delete(URL).status_code,405)
        self.assertEqual(QuotationRequest.objects.count(),0)
    def test_list_and_immutable_resource_methods(self):
        first=self.post().json()
        rows=self.client.get(URL).json()['requests'];self.assertEqual([r['id'] for r in rows],[first['id']])
        self.assertEqual(self.client.post(URL+first['id']+'/').status_code,405)
        self.assertEqual(self.client.get(URL+str(uuid.uuid4())+'/').status_code,404)
    def race(self,same):
        clients=[Client(),Client()]
        for client in clients:verified_login(client,self.owner)
        barrier=Barrier(2)
        def run(index):
            try:
                payload=dict(self.payload)
                if not same:payload['request_id']=str(uuid.uuid4())
                barrier.wait(timeout=10)
                response=self.post(payload,clients[index])
                return response.status_code,response.json()['id']
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(run,range(2)))
        self.assertEqual(sorted(r[0] for r in results),[200,201])
        self.assertEqual(results[0][1],results[1][1]);self.assertEqual(QuotationRequest.objects.count(),1)
        self.assertEqual(QuotationRequestKey.objects.count(),1 if same else 2)
    def test_concurrent_exact_retry(self):self.race(True)
    def test_concurrent_different_keys(self):self.race(False)

    def test_submission_racing_cart_edit_never_captures_newer_lines(self):
        clients=[Client(),Client()]
        for client in clients:verified_login(client,self.owner)
        barrier=Barrier(2)
        edit={'request_id':str(uuid.uuid4()),'expected_version':1,'catalog_revision':CATALOG['revision'],'lines':copy.deepcopy(CASES[2]['lines'])}
        def run(index):
            try:
                barrier.wait(timeout=10)
                if index==0:
                    response=self.post(client=clients[index])
                    return response.status_code,response.json()
                response=clients[index].post('/api/v1/cart/',data=json.dumps(edit),content_type='application/json')
                return response.status_code,response.json()
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(run,range(2)))
        self.assertEqual(results[1][0],201)
        self.assertIn(results[0][0],[201,409])
        if results[0][0]==201:
            self.assertEqual(results[0][1]['lines'],self.saved['lines'])
            self.assertEqual(results[0][1]['version'],1)
        else:self.assertEqual(QuotationRequest.objects.count(),0)
