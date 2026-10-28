import json
from pathlib import Path
from django.test import SimpleTestCase
from .rules import CATALOG, evaluate
ROOT = Path(__file__).resolve().parents[3]
CASES = json.loads((ROOT / 'frontend/tests/conformance.json').read_text())

class CatalogTests(SimpleTestCase):
    def test_shared_conformance(self):
        for case in CASES:
            with self.subTest(case=case['name']):
                result = evaluate(case['value'])
                self.assertEqual(result['status'],case['status'])
                self.assertEqual([e['field']+':'+e['code'] for e in result['errors']],case['errors'])
                self.assertFalse(result['purchase_enabled'])
                self.assertTrue(all(v is None for k,v in result['money'].items() if k.endswith('_minor')))
                self.assertEqual(result['support_seconds'],case['value']['support_packages']*36000 if result['valid'] else None)

    def test_all_product_hosts_are_validated(self):
        self.assertEqual(self.client.get('/api/v1/catalog/',HTTP_HOST='unexpected.invalid').status_code,400)
        self.assertEqual(self.client.get('/api/v1/configuration-drafts/',HTTP_HOST='unexpected.invalid').status_code,400)

    def test_catalog_http(self):
        response=self.client.get('/api/v1/catalog/')
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json(),CATALOG)
        self.assertEqual(response['ETag'],'"'+CATALOG['revision']+'"')
        self.assertEqual(self.client.post('/api/v1/catalog/').status_code,405)

    def test_validation_http(self):
        for case in CASES:
            with self.subTest(case=case['name']):
                r=self.client.post('/api/v1/configurations/validate/',data=json.dumps(case['value']),content_type='application/json')
                self.assertEqual(r.status_code,422 if case['status']=='invalid' else 200)
                self.assertEqual(r.json(),evaluate(case['value']))
                self.assertEqual(r['Cache-Control'],'no-store')
                self.assertNotIn('Set-Cookie',r)
                self.assertNotIn('SYNTHETIC_HOST_CANARY',r.content.decode())

    def test_parser_bounds_and_no_echo(self):
        for raw in ('{','{"vendor":1,"vendor":2}','NaN','x'*8193):
            r=self.client.post('/api/v1/configurations/validate/',data=raw,content_type='application/json')
            self.assertEqual(r.status_code,400)
            self.assertEqual(r.json(),{'error':'invalid_json'})
        self.assertEqual(self.client.get('/api/v1/configurations/validate/').status_code,405)
        self.assertEqual(self.client.post('/api/v1/configurations/validate/',data='x',content_type='text/plain').status_code,415)

    def test_no_private_or_offer_fields_in_catalog(self):
        self.assertEqual(len(CATALOG['vendors']),3)
        self.assertEqual(sum(len(v['families']) for v in CATALOG['vendors']),13)
        self.assertTrue(all(v is None for v in CATALOG['approvals'].values()))
        self.assertNotIn('host_id',json.dumps(CATALOG))


from django.contrib.auth import get_user_model
from django.test import Client, TestCase, TransactionTestCase, override_settings
from django.db import connections
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import uuid
from .models import ConfigurationDraft

def verified_login(client,user):
    # Trusted test fixture only, not a public authentication bypass.
    from shop.access.models import CustomerIdentity
    from django.utils import timezone
    identity,_=CustomerIdentity.objects.get_or_create(user=user,defaults={'email':'fixture-'+str(user.pk)+'@synthetic.invalid','verified_at':timezone.now()})
    client.force_login(user)
    session=client.session;session['shop_verified_identity']=str(identity.id);session.save()

class DraftTests(TestCase):
    def setUp(self):
        self.owner=get_user_model().objects.create_user(username='synthetic-owner')
        self.other=get_user_model().objects.create_user(username='synthetic-other')
        self.payload={'request_id':str(uuid.uuid4()),'revision':CATALOG['revision'],'configuration':CASES[0]['value']}
        self.url='/api/v1/configuration-drafts/'

    def save(self,payload=None):
        return self.client.post(self.url,data=json.dumps(payload or self.payload),content_type='application/json')

    def test_response_context_tracks_identity_and_session_without_raw_identifiers(self):
        header='X-Shop-Access-Context'
        verified_login(self.client,self.owner)
        first=self.client.get('/api/v1/customer/session/')[header]
        self.assertRegex(first,r'^[a-f0-9]{64}$')
        for path in (self.url,'/api/v1/cart/','/api/v1/quotation-requests/'):
            response=self.client.get(path)
            self.assertEqual(response[header],first)
            self.assertEqual(response['Cache-Control'],'no-store')
        other_session=Client();verified_login(other_session,self.owner)
        self.assertNotEqual(other_session.get('/api/v1/customer/session/')[header],first)
        session=self.client.session;session.cycle_key();session.save()
        self.client.cookies['sessionid']=session.session_key
        rotated=self.client.get('/api/v1/customer/session/')[header]
        self.assertNotEqual(rotated,first)
        verified_login(self.client,self.other)
        switched=self.client.get('/api/v1/cart/')[header]
        self.assertNotEqual(switched,rotated)
        self.assertNotIn(header,self.client.get('/api/v1/catalog/'))
        self.assertNotIn(header,self.client.get('/health/live'))
        anonymous=Client().get('/api/v1/cart/',HTTP_X_SHOP_ACCESS_CONTEXT=first)
        self.assertEqual(anonymous.status_code,401)
        self.assertRegex(anonymous[header],r'^[a-f0-9]{64}$')
        self.assertEqual(set(anonymous.json()),{'error'})

    def test_authenticated_owner_and_idempotency(self):
        self.assertEqual(self.save().status_code,401)
        verified_login(self.client,self.owner)
        first=self.save();self.assertEqual(first.status_code,201)
        self.assertEqual(self.save().status_code,200)
        self.assertEqual(ConfigurationDraft.objects.count(),1)
        path=self.url+first.json()['id']+'/'
        self.assertEqual(self.client.get(path).json(),first.json())
        self.assertEqual(first.json()['state'],'draft')
        self.assertFalse(first.json()['evaluation']['purchase_enabled'])
        verified_login(self.client,self.other)
        self.assertEqual(self.client.get(path).status_code,404)
        # Same client request ID belongs to its owner, not another customer.
        self.assertEqual(self.save().status_code,201)
        self.assertEqual(ConfigurationDraft.objects.count(),2)

    def test_stale_conflicting_and_invalid_drafts(self):
        verified_login(self.client,self.owner)
        self.assertEqual(self.save(self.payload|{'revision':'0'*64}).status_code,409)
        self.assertEqual(self.save(self.payload|{'configuration':CASES[0]['value']|{'host_id':'SYNTHETIC_HOST_CANARY'}}).status_code,422)
        self.assertEqual(ConfigurationDraft.objects.count(),0)
        self.assertEqual(self.save().status_code,201)
        self.assertEqual(self.save(self.payload|{'configuration':CASES[0]['value']|{'support_packages':1}}).status_code,409)
        self.assertEqual(ConfigurationDraft.objects.get().configuration,self.payload['configuration'])

    def test_malformed_platform_names_are_rejected_before_storage(self):
        verified_login(self.client,self.owner)
        for case in CASES:
            if not case['name'].startswith('platform name ') or case['status']!='invalid':continue
            with self.subTest(case=case['name']):
                response=self.save(self.payload|{'configuration':case['value']})
                self.assertEqual(response.status_code,422)
                self.assertEqual(response.json()['errors'],[{'field':'platform','code':'short_name'}])
                self.assertEqual(ConfigurationDraft.objects.count(),0)

    def test_unicode_platform_names_round_trip_and_retry(self):
        verified_login(self.client,self.owner)
        for case in CASES:
            if not case['name'].startswith('platform name ') or case['status']=='invalid':continue
            with self.subTest(case=case['name']):
                payload=self.payload|{'request_id':str(uuid.uuid4()),'configuration':case['value']}
                first=self.save(payload);self.assertEqual(first.status_code,201)
                self.assertEqual(first.json()['configuration'],case['value'])
                self.assertEqual(self.save(payload).json(),first.json())
                self.assertEqual(ConfigurationDraft.objects.get(pk=first.json()['id']).configuration,case['value'])

    def test_csrf_and_production_gate(self):
        protected=Client(enforce_csrf_checks=True)
        verified_login(protected,self.owner)
        self.assertEqual(protected.post(self.url,data=json.dumps(self.payload),content_type='application/json').status_code,403)
        verified_login(self.client,self.owner)
        with override_settings(SHOP_ENV='production'):
            self.assertEqual(self.save().status_code,404)
        self.owner.is_staff=True;self.owner.save()
        self.assertEqual(self.save().status_code,403)

class DraftRaceTests(TransactionTestCase):
    def test_concurrent_same_request_creates_one_snapshot(self):
        owner=get_user_model().objects.create_user(username='synthetic-race')
        from shop.access.models import CustomerIdentity
        from django.utils import timezone
        CustomerIdentity.objects.create(user=owner,email='race@synthetic.invalid',verified_at=timezone.now())
        barrier=Barrier(2)
        payload={'request_id':str(uuid.uuid4()),'revision':CATALOG['revision'],'configuration':CASES[0]['value']}
        def attempt():
            try:
                client=Client();verified_login(client,get_user_model().objects.get(pk=owner.pk))
                barrier.wait(timeout=5)
                response=client.post('/api/v1/configuration-drafts/',data=json.dumps(payload),content_type='application/json')
                return response.status_code,response.json()['id']
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(lambda _:attempt(),range(2)))
        self.assertEqual(sorted(r[0] for r in results),[200,201])
        self.assertEqual(results[0][1],results[1][1])
        self.assertEqual(ConfigurationDraft.objects.count(),1)


class DraftRecoveryTests(TransactionTestCase):
    def setUp(self):
        import copy
        DraftTests.setUp(self)
        self.payload=copy.deepcopy(self.payload)
        self.payload['configuration']['platform']={'choice':'other-board','kit_id':None,'name':'DRAFT_PRIVATE_RECOVERY_CANARY'}
        self.client=Client(enforce_csrf_checks=True)
        verified_login(self.client,self.owner)
        self.assertEqual(self.client.get('/api/v1/customer/session/').status_code,200)

    def recover(self,action='quarantine',*,basis_reset=None):
        from django.db import connection
        from shop.access.recovery import local_recovery_operation
        return local_recovery_operation(action=action,request_id=uuid.uuid4(),
            expected_database=connection.settings_dict['NAME'],basis_reset=basis_reset)

    def reset(self,released):
        reset=self.recover()
        if released:self.recover('release',basis_reset=reset['operation_id'])

    def fresh(self):
        from shop.access.models import AccessEpoch
        epoch=AccessEpoch.objects.get(pk=1)
        if epoch.quarantined:self.recover('release',basis_reset=epoch.active_reset)
        verified_login(self.client,self.owner)
        self.assertEqual(self.client.get('/api/v1/customer/session/').status_code,200)

    def facts(self):
        return list(ConfigurationDraft.objects.order_by('id').values_list(
            'id','owner_id','request_id','revision','configuration','evaluation','created_at'))

    def post(self):
        return self.client.post(self.url,data=json.dumps(self.payload),content_type='application/json',
            HTTP_X_CSRFTOKEN=self.client.cookies['csrftoken'].value)

    def save_overlap(self,released,replay=False):
        from unittest.mock import patch
        from . import views
        if replay:self.assertEqual(self.post().status_code,201)
        before=self.facts();evaluate=views.evaluate
        def interleave(value):
            result=evaluate(value);self.assertTrue(result['valid'])
            self.reset(released)
            return result
        with patch.object(views,'evaluate',side_effect=interleave):response=self.post()
        with self.subTest(check='response'):
            self.assertEqual(response.status_code,403,response.content)
            self.assertEqual(response.json(),{'error':'verification_required'})
            self.assertEqual(response['Cache-Control'],'no-store')
        with self.subTest(check='facts'):self.assertEqual(self.facts(),before)
        self.fresh()
        first=self.post();self.assertEqual(first.status_code,200 if replay else 201)
        committed=self.facts()
        retry=self.post();self.assertEqual(retry.status_code,200)
        self.assertEqual(retry.json(),first.json());self.assertEqual(self.facts(),committed)

    def test_save_after_quarantine_denies(self):self.save_overlap(False)
    def test_save_after_quarantine_release_denies(self):self.save_overlap(True)
    def test_exact_retry_after_quarantine_denies(self):self.save_overlap(False,True)
    def test_exact_retry_after_quarantine_release_denies(self):self.save_overlap(True,True)

    def read_overlap(self,released,single=False):
        from unittest.mock import patch
        from . import views
        saved=self.post();self.assertEqual(saved.status_code,201)
        path=self.url+saved.json()['id']+'/' if single else self.url
        before=self.facts();access=views.local_customer
        def interleave(request):
            result=access(request);self.assertIsNone(result)
            self.reset(released)
            return result
        with patch.object(views,'local_customer',side_effect=interleave):response=self.client.get(path)
        with self.subTest(check='response'):
            self.assertEqual(response.status_code,403,response.content)
            self.assertEqual(response.json(),{'error':'verification_required'})
            self.assertEqual(response['Cache-Control'],'no-store')
        with self.subTest(check='facts'):self.assertEqual(self.facts(),before)
        self.fresh();response=self.client.get(path);self.assertEqual(response.status_code,200)
        if single:self.assertEqual(response.json(),saved.json())
        else:self.assertEqual(response.json()['drafts'][0]['id'],saved.json()['id'])
        self.assertEqual(self.facts(),before)

    def test_list_after_quarantine_denies(self):self.read_overlap(False)
    def test_list_after_quarantine_release_denies(self):self.read_overlap(True)
    def test_get_after_quarantine_denies(self):self.read_overlap(False,True)
    def test_get_after_quarantine_release_denies(self):self.read_overlap(True,True)

    def test_epoch_is_locked_before_draft_queries(self):
        from unittest.mock import patch
        from django.db.models.query import QuerySet
        from .cart_tests import CartRecoveryMixin
        saved=self.post();self.assertEqual(saved.status_code,201)
        path=self.url+saved.json()['id']+'/'
        self.payload['request_id']=str(uuid.uuid4())
        fetch=QuerySet._fetch_all;seen=set();active=[]
        def observe(query):
            if query.model is ConfigurationDraft:
                CartRecoveryMixin.assert_epoch_locked(self);seen.add(active[0])
            return fetch(query)
        with patch.object(QuerySet,'_fetch_all',observe):
            active[:]=['list'];self.assertEqual(self.client.get(self.url).status_code,200)
            active[:]=['get'];self.assertEqual(self.client.get(path).status_code,200)
            active[:]=['create'];self.assertEqual(self.post().status_code,201)
            active[:]=['replay'];self.assertEqual(self.post().status_code,200)
        self.assertEqual(seen,{'list','get','create','replay'})

    def test_exact_retry_preserves_current_catalog_admission(self):
        from unittest.mock import patch
        self.assertEqual(self.post().status_code,201)
        before=self.facts()
        with patch.dict(CATALOG,revision='f'*64):self.assertEqual(self.post().status_code,409)
        self.assertEqual(self.facts(),before)


class SimplePurchaseTests(SimpleTestCase):
    def test_actual_csrf_get_and_post_without_javascript(self):
        client=Client(enforce_csrf_checks=True)
        r=client.get('/purchase/simple/')
        self.assertEqual(r.status_code,200)
        self.assertContains(r,'Altera / Intel FPGA')
        self.assertContains(r,'PolarFire SoC')
        self.assertContains(r,'Purchase unavailable')
        value=CASES[0]['value']
        data={k:v for k,v in value.items() if k not in ('product_id','profile_id','quantity') and v is not None}
        data['platform_choice']='not-designed'
        data['csrfmiddlewaretoken']=client.cookies['csrftoken'].value
        r=client.post('/purchase/simple/',data=data)
        self.assertEqual(r.status_code,200)
        self.assertContains(r,'Configuration ready for review.')
        data['families']=['microchip-polarfire']
        self.assertContains(client.post('/purchase/simple/',data=data),'families: vendor_families')
        data['families']=['altera-agilex-5'];data['term']='rdp-yearly';data['production_band']='higher-volume'
        self.assertContains(client.post('/purchase/simple/',data=data),'Quotation required')

    def test_missing_csrf_private_input_and_production_gate(self):
        protected=Client(enforce_csrf_checks=True)
        self.assertEqual(protected.post('/purchase/simple/',data={}).status_code,403)
        r=self.client.post('/purchase/simple/',data={'host_id':'SYNTHETIC_HOST_CANARY','fixed_nodes':'SYNTHETIC_HOST_CANARY'})
        self.assertNotIn('SYNTHETIC_HOST_CANARY',r.content.decode())
        with override_settings(SHOP_ENV='production'):
            self.assertEqual(self.client.get('/purchase/simple/').status_code,404)


    def test_new_form_requires_platform_without_invalidating_legacy_snapshot(self):
        from .simple import ConfigurationForm
        value=CASES[0]['value']
        self.assertTrue(evaluate(value)['valid'])  # Historical snapshot rules stay recoverable.
        data={k:v for k,v in value.items() if k not in ('product_id','profile_id','quantity') and v is not None}
        for choice in (None,'','not-designed','other-board'):
            payload=dict(data)
            if choice is not None:payload['platform_choice']=choice
            form=ConfigurationForm(payload)
            self.assertEqual(form.is_valid(),choice in ('not-designed','other-board'))
            response=self.client.post('/purchase/simple/',data=payload)
            if choice in ('not-designed','other-board'):
                self.assertContains(response,'Configuration ready for review.')
            else:
                self.assertContains(response,'platform_choice: check this field.')
                self.assertNotContains(response,'Configuration ready for review.')
