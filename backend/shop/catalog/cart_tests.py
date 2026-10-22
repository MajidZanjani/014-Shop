import copy
import json
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from pathlib import Path
from django.contrib.auth import get_user_model
from django.db import connections
from django.test import Client, SimpleTestCase, TransactionTestCase, override_settings
from .cart_rules import evaluate_cart
from .models import DraftCart, CartSnapshot
from .rules import CATALOG
from .tests import verified_login
CASES=json.loads((Path(__file__).resolve().parents[3]/'frontend/tests/cart-conformance.json').read_text())

class CartConformance(SimpleTestCase):
    def test_cases(self):
        for case in CASES:
            with self.subTest(case=case['name']):
                result=evaluate_cart(case['lines'])
                self.assertEqual(result['status'],case['status'])
                self.assertEqual([e['field']+':'+e['code'] for e in result['errors']],case['errors'])
                self.assertFalse(result['purchase_enabled'])

class CartTests(TransactionTestCase):
    def setUp(self):
        self.owner=get_user_model().objects.create_user(username='cart-owner')
        self.other=get_user_model().objects.create_user(username='cart-other')
        verified_login(self.client,self.owner)
        self.value={'request_id':str(uuid.uuid4()),'expected_version':0,'catalog_revision':CATALOG['revision'],'lines':copy.deepcopy(CASES[1]['lines'])}
    def post(self,value=None,client=None):
        return (client or self.client).post('/api/v1/cart/',data=json.dumps(self.value if value is None else value),content_type='application/json')
    def test_versions_replay_and_owner_isolation(self):
        self.assertEqual(self.client.get('/api/v1/cart/').json()['version'],0)
        self.assertEqual(DraftCart.objects.count(),0)
        first=self.post();self.assertEqual(first.status_code,201)
        self.assertEqual(self.post().json(),first.json())
        changed=dict(self.value,request_id=str(uuid.uuid4()),expected_version=1,lines=[])
        self.assertEqual(self.post(changed).status_code,201)
        replay=self.post().json();self.assertEqual(replay['version'],1);self.assertEqual(replay['current_version'],2)
        self.assertEqual(CartSnapshot.objects.count(),2)
        self.assertEqual(self.post(dict(self.value,lines=[])).status_code,409)
        self.assertEqual(self.post(dict(self.value,request_id=str(uuid.uuid4()))).status_code,409)
        verified_login(self.client,self.other)
        self.assertEqual(self.client.get('/api/v1/cart/').json()['lines'],[])
        self.assertEqual(self.post().status_code,201)
        self.assertEqual(DraftCart.objects.count(),2)
    def test_stale_catalog_and_invalid_lines_do_not_persist(self):
        self.assertEqual(self.post(dict(self.value,catalog_revision='0'*64)).status_code,409)
        for case in CASES:
            if case['status']=='invalid':
                with self.subTest(case=case['name']):self.assertEqual(self.post(dict(self.value,lines=case['lines'])).status_code,422)
        self.assertEqual(DraftCart.objects.count(),0)
        self.assertEqual(CartSnapshot.objects.count(),0)
    def test_auth_csrf_parser_and_scope(self):
        self.assertEqual(self.post(client=Client()).status_code,401)
        strict=Client(enforce_csrf_checks=True);verified_login(strict,self.owner)
        self.assertEqual(self.post(client=strict).status_code,403)
        self.assertEqual(self.client.get('/api/v1/cart/?owner=other').status_code,400)
        self.assertEqual(self.post(dict(self.value,owner=str(self.other.pk))).status_code,400)
        for raw in ['NaN','{"request_id":1,"request_id":2}','x'*32769]:
            self.assertEqual(self.client.post('/api/v1/cart/',data=raw,content_type='application/json').status_code,400)
    def test_replay_remains_valid_after_catalog_change(self):
        from unittest.mock import patch
        self.assertEqual(self.post().status_code,201)
        with patch.dict(CATALOG,revision='f'*64):
            self.assertEqual(self.post().status_code,200)
            self.assertEqual(self.post(dict(self.value,request_id=str(uuid.uuid4()),expected_version=1)).status_code,409)
    def race(self,same):
        clients=[Client(),Client()]
        for client in clients:verified_login(client,self.owner)
        barrier=Barrier(2)
        def run(index):
            try:
                payload=copy.deepcopy(self.value)
                if not same:payload['request_id']=str(uuid.uuid4())
                barrier.wait(timeout=10)
                return self.post(payload,clients[index]).status_code
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(run,range(2)))
        self.assertEqual(sorted(results),[200,201] if same else [201,409])
        self.assertEqual(CartSnapshot.objects.count(),1)
        self.assertEqual(DraftCart.objects.get().version,1)
    def test_concurrent_retry(self):self.race(True)
    def test_concurrent_edits(self):self.race(False)

    def test_support_only_and_access_boundaries(self):
        value=dict(self.value,lines=copy.deepcopy(CASES[2]['lines']))
        result=self.post(value);self.assertEqual(result.status_code,201)
        self.assertEqual(result.json()['evaluation']['quoted_support_seconds'],72000)
        self.assertFalse(result.json()['checkout_enabled'])
        with override_settings(SHOP_ENV='production'):
            self.assertEqual(self.post().status_code,404)
            self.assertEqual(self.client.get('/api/v1/cart/').status_code,404)
        self.owner.is_staff=True;self.owner.save()
        self.assertEqual(self.post().status_code,403)
        self.owner.is_staff=False;self.owner.save()
        session=self.client.session;session.pop('shop_verified_identity');session.save()
        self.assertEqual(self.post().status_code,403)
