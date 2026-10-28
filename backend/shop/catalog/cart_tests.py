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

    def test_malformed_platform_names_are_rejected_before_storage(self):
        from .tests import CASES as configurations
        for case in configurations:
            if not case['name'].startswith('platform name ') or case['status']!='invalid':continue
            with self.subTest(case=case['name']):
                value=copy.deepcopy(self.value)
                value['lines'][0]['configuration']=case['value']
                response=self.post(value)
                self.assertEqual(response.status_code,422)
                self.assertIn({'field':'lines.0.configuration.platform','code':'short_name'},response.json()['errors'])
                self.assertEqual(DraftCart.objects.count(),0)
                self.assertEqual(CartSnapshot.objects.count(),0)

    def test_unicode_platform_names_round_trip_and_retry(self):
        value=copy.deepcopy(self.value)
        value['lines'][0]['configuration']['platform']={'choice':'other-board','kit_id':None,'name':'🚀'*120}
        first=self.post(value);self.assertEqual(first.status_code,201)
        self.assertEqual(first.json()['lines'],value['lines'])
        self.assertEqual(self.post().status_code,409)
        retry=self.post(value);self.assertEqual(retry.status_code,200)
        self.assertEqual(retry.json(),first.json())
        self.assertEqual(CartSnapshot.objects.get().lines,value['lines'])
        self.assertEqual(DraftCart.objects.get().version,1)
    def test_denied_customer_resources_are_not_cacheable(self):
        paths=('/api/v1/configuration-drafts/','/api/v1/cart/',
               '/api/v1/quotation-requests/'+str(uuid.uuid4())+'/')
        clients=[(Client(),401)]
        unverified=Client();unverified.force_login(self.owner);clients.append((unverified,403))
        staff=get_user_model().objects.create_user(username='denied-staff',is_staff=True)
        privileged=Client();privileged.force_login(staff);clients.append((privileged,403))
        for client,status in clients:
            for path in paths:
                with self.subTest(status=status,path=path):
                    response=client.get(path)
                    self.assertEqual(response.status_code,status)
                    self.assertEqual(response['Cache-Control'],'no-store')
                    self.assertEqual(set(response.json()),{'error'})
        with override_settings(SHOP_ENV='production'):
            response=Client().get('/api/v1/cart/')
            self.assertEqual(response.status_code,404)
            self.assertEqual(response['Cache-Control'],'no-store')

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


class CartRecoveryMixin:
    def recover(self,action='quarantine',*,basis_reset=None):
        from django.db import connection
        from shop.access.recovery import local_recovery_operation
        return local_recovery_operation(action=action,request_id=uuid.uuid4(),
            expected_database=connection.settings_dict['NAME'],basis_reset=basis_reset)

    def facts(self):
        return {
            'cart':list(DraftCart.objects.order_by('id').values_list('id','owner_id','version')),
            'snapshots':list(CartSnapshot.objects.order_by('id').values_list(
                'id','cart_id','version','request_id','catalog_revision','lines','evaluation')),
        }

    def reset(self,released):
        reset=self.recover()
        if released:self.recover('release',basis_reset=reset['operation_id'])

    def fresh(self,browser=None):
        from shop.access.models import AccessEpoch
        epoch=AccessEpoch.objects.get(pk=1)
        if epoch.quarantined:self.recover('release',basis_reset=epoch.active_reset)
        verified_login(browser or self.client,self.owner)
        self.assertEqual((browser or self.client).get('/api/v1/customer/session/').status_code,200)

    def assert_epoch_locked(self):
        from django.db import DatabaseError,transaction
        from shop.access.models import AccessEpoch
        def contender():
            try:
                with transaction.atomic():AccessEpoch.objects.select_for_update(nowait=True).get(pk=1)
            except DatabaseError as error:return getattr(error.__cause__,'sqlstate',None)
            finally:connections.close_all()
            return 'unlocked'
        with ThreadPoolExecutor(max_workers=1) as pool:
            self.assertEqual(pool.submit(contender).result(timeout=10),'55P03')


class CartRecoveryTests(CartRecoveryMixin,TransactionTestCase):
    def setUp(self):
        CartTests.setUp(self)
        strict=Client(enforce_csrf_checks=True);strict.cookies.update(self.client.cookies)
        self.client=strict
        self.assertEqual(self.client.get('/api/v1/customer/session/').status_code,200)

    def post(self,value=None):
        return self.client.post('/api/v1/cart/',data=json.dumps(self.value if value is None else value),
            content_type='application/json',HTTP_X_CSRFTOKEN=self.client.cookies['csrftoken'].value)

    def command_overlap(self,mode,released=False):
        from unittest.mock import patch
        from . import cart_views
        value=self.value
        if mode in ('update','replay'):
            self.assertEqual(self.post().status_code,201)
            later=dict(self.value,request_id=str(uuid.uuid4()),expected_version=1,lines=[])
            if mode=='update':value=later
            else:self.assertEqual(self.post(later).status_code,201)
        before=self.facts();store=cart_views.store_cart
        def interleave(*args,**kwargs):
            self.reset(released)
            return store(*args,**kwargs)
        with patch.object(cart_views,'store_cart',side_effect=interleave):response=self.post(value)
        with self.subTest(check='response'):
            self.assertEqual(response.status_code,403,response.content)
            self.assertEqual(response.json(),{'error':'verification_required'})
            self.assertEqual(response['Cache-Control'],'no-store')
        with self.subTest(check='facts'):self.assertEqual(self.facts(),before)
        self.fresh()
        self.assertEqual(self.post(value).status_code,200 if mode=='replay' else 201)
        committed=self.facts()
        self.assertEqual(self.post(value).status_code,200)
        self.assertEqual(self.facts(),committed)

    def test_first_save_after_quarantine_denies(self):self.command_overlap('create')
    def test_first_save_after_quarantine_release_denies(self):self.command_overlap('create',True)
    def test_update_after_quarantine_denies(self):self.command_overlap('update')
    def test_update_after_quarantine_release_denies(self):self.command_overlap('update',True)
    def test_exact_replay_after_quarantine_denies(self):self.command_overlap('replay')
    def test_exact_replay_after_quarantine_release_denies(self):self.command_overlap('replay',True)

    def read_overlap(self,released):
        from unittest.mock import patch
        from . import cart_views
        self.assertEqual(self.post().status_code,201)
        before=self.facts();access=cart_views.local_customer
        def interleave(request):
            result=access(request);self.assertIsNone(result)
            self.reset(released)
            return result
        with patch.object(cart_views,'local_customer',side_effect=interleave):response=self.client.get('/api/v1/cart/')
        self.assertEqual(response.status_code,403,response.content)
        self.assertEqual(response.json(),{'error':'verification_required'})
        self.assertEqual(response['Cache-Control'],'no-store')
        self.assertEqual(self.facts(),before)

    def test_private_read_after_quarantine_denies(self):self.read_overlap(False)
    def test_private_read_after_quarantine_release_denies(self):self.read_overlap(True)

    def test_epoch_is_locked_before_cart_reads_and_writes(self):
        from unittest.mock import patch
        from django.db.models.query import QuerySet
        first=QuerySet.first;create=QuerySet.get_or_create;seen=set();active=[]
        def observe():
            self.assert_epoch_locked()
            seen.add(active[0])
        def read(query,*args,**kwargs):
            if query.model is DraftCart:observe()
            return first(query,*args,**kwargs)
        def write(query,*args,**kwargs):
            if query.model is DraftCart:observe()
            return create(query,*args,**kwargs)
        with patch.object(QuerySet,'first',read),patch.object(QuerySet,'get_or_create',write):
            active[:]=['get'];self.assertEqual(self.client.get('/api/v1/cart/').status_code,200)
            active[:]=['create'];self.assertEqual(self.post().status_code,201)
            active[:]=['replay'];self.assertEqual(self.post().status_code,200)
        self.assertEqual(seen,{'get','create','replay'})

    def test_trusted_internal_cart_calls_preserve_the_no_request_interface(self):
        from .cart_views import store_cart
        self.reset(False)
        first,status=store_cart(self.owner,self.value)
        self.assertEqual(status,201)
        before=self.facts()
        retry,status=store_cart(self.owner,self.value)
        self.assertEqual(status,200);self.assertEqual(retry,first)
        self.assertEqual(self.facts(),before)
