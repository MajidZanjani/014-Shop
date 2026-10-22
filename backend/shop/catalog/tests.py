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
