"""Local private business editor: exact source groups, real PostgreSQL and scoped owners."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from urllib.parse import urlencode
from unittest.mock import patch
import uuid
import re
from django.contrib.auth import get_user_model
from django.db import connections
from django.test import Client, SimpleTestCase, TransactionTestCase, override_settings
from shop.access.models import CustomerIdentity
from . import business_rules as rules
from .models import BusinessDraft, BusinessDraftSnapshot
from .tests import verified_login

URL='/purchase/business/'

class BusinessSourceTests(SimpleTestCase):
    def test_nineteen_exact_source_groups_and_pending_choices(self):
        source=(Path(__file__).resolve().parents[3]/'docs/product-source/SLL_xSPI_MC_Product_Page.md').read_text()
        section=source.split('### Business and Billing Details')[1].split('Collect further end-user')[0]
        labels=[line.split('|')[1].strip() for line in section.splitlines() if line.startswith('| ')][2:]
        self.assertEqual(len(labels),19)
        self.assertEqual([label for _,label,_,_ in rules.GROUPS],labels)
        self.assertEqual(len({key for _,_,fields,_ in rules.GROUPS for key in fields}),len(rules.empty_details()))
        clean,errors=rules.validate_details(rules.empty_details());self.assertFalse(errors)
        resolved=rules.resolve_details(clean);result=rules.evaluate_details(resolved)
        self.assertEqual(result['state'],'partial_draft');self.assertFalse(result['checkout_enabled'])
        for key in rules.PENDING:self.assertIsNone(resolved[key]);self.assertIn(key,result['missing_required'])
    def test_strict_types_and_no_invented_tax_or_country(self):
        for patch_value in [{'registration_country':'GB'},{'tax_status':'business'},{'deployment_country':'DE'},
                            {'business_email':'private@example.com'},{'technical_same_as_purchasing':'true'},
                            {'notes':'nul\x00value'},{'telephone':1},{'host_id':'HOST_PRIVATE_SYNTHETIC'}]:
            with self.subTest(fields=list(patch_value)):
                self.assertTrue(rules.validate_details(rules.empty_details()|patch_value)[1])

class BusinessDraftTests(TransactionTestCase):
    def setUp(self):
        self.owner=get_user_model().objects.create_user(username='business-owner')
        self.other=get_user_model().objects.create_user(username='business-other')
        verified_login(self.client,self.owner)
        self.value={**{key:'' for key in rules.LIMITS},'request_id':str(uuid.uuid4()),'expected_version':'0',
                    'schema_version':'1','source_sha256':rules.SOURCE_SHA256,
                    'legal_business_name':'BUSINESS_PRIVATE_CANARY_SYNTHETIC','purchasing_name':'PURCHASER_PRIVATE_SYNTHETIC',
                    'business_email':'buyer@business.synthetic.invalid','registered_address':'10 Synthetic Road\r\nUnit 2',
                    'registered_city':'Synthetic City','registered_region':'Synthetic Region','registered_postcode':'SYNTHETIC',
                    'billing_same_as_registered':'on','technical_same_as_purchasing':'on','tax_number':'TAX_PRIVATE_SYNTHETIC'}
    def post(self,value=None,client=None):
        return (client or self.client).post(URL,data=urlencode(self.value if value is None else value),content_type='application/x-www-form-urlencoded')
    def test_form_source_groups_helpers_defaults_private_storage_and_no_effects(self):
        page=self.client.get(URL)
        self.assertEqual(page.status_code,200);self.assertEqual(page.content.count(b'data-source-group='),19)
        self.assertContains(page,'Pending approval');self.assertContains(page,'Incomplete drafts can be saved')
        self.assertNotContains(page,'value="GB"');self.assertNotContains(page,'value="DE"')
        before_users=get_user_model().objects.count();before_identities=CustomerIdentity.objects.count()
        result=self.post();self.assertEqual(result.status_code,303);self.assertEqual(result['Location'],URL)
        row=BusinessDraftSnapshot.objects.get();data=row.details
        for suffix in ['address','city','region','postcode']:self.assertEqual(data['billing_'+suffix],data['registered_'+suffix])
        self.assertEqual(data['registered_address'],'10 Synthetic Road\nUnit 2')
        self.assertEqual(data['technical_name'],data['purchasing_name']);self.assertEqual(data['technical_email'],data['business_email'])
        self.assertEqual(data['invoice_email'],data['business_email']);self.assertEqual(data['licensed_entity'],data['legal_business_name'])
        self.assertEqual(data['registration_number'],'')
        self.assertFalse(row.evaluation['licensed_entity_review_required']);self.assertFalse(row.evaluation['acceptance_enabled'])
        self.assertFalse(row.evaluation['checkout_enabled'])
        for name in rules.PENDING:self.assertIsNone(data[name])
        self.assertEqual(get_user_model().objects.count(),before_users);self.assertEqual(CustomerIdentity.objects.count(),before_identities)
        page=self.client.get(URL)
        self.assertContains(page,self.value['legal_business_name']);self.assertEqual(page['Cache-Control'],'no-store')
        self.assertEqual(page['Referrer-Policy'],'no-referrer');self.assertIn("frame-ancestors 'none'",page['Content-Security-Policy'])
        self.assertContains(page,'autocomplete="off"')
        self.assertNotIn(self.value['legal_business_name'],str(self.client.session.items()))
        for path in ['/api/v1/cart/','/api/v1/catalog/','/api/v1/quotation-requests/','/api/v1/configuration-drafts/']:
            response=self.client.get(path)
            self.assertNotIn(self.value['legal_business_name'],response.content.decode())
            self.assertNotIn(self.value['tax_number'],response.content.decode())
    def test_versions_replay_source_change_and_licensed_entity_review(self):
        self.assertEqual(self.post().status_code,303)
        changed=dict(self.value,request_id=str(uuid.uuid4()),expected_version='1',licensed_entity='DIFFERENT_ENTITY_PRIVATE_SYNTHETIC')
        self.assertEqual(self.post(changed).status_code,303)
        rows=list(BusinessDraftSnapshot.objects.order_by('version'))
        self.assertEqual(rows[0].details['licensed_entity'],self.value['legal_business_name'])
        self.assertTrue(rows[1].evaluation['licensed_entity_review_required'])
        self.assertContains(self.client.get(URL),'review required')
        self.assertEqual(self.post(dict(self.value,notes='changed reuse')).status_code,409)
        self.assertEqual(self.post(dict(self.value,request_id=str(uuid.uuid4()))).status_code,409)
        with patch.object(rules,'SOURCE_SHA256','f'*64):
            self.assertEqual(self.post().status_code,303)
            self.assertEqual(self.client.session['business_last_confirmed_version'],1)
            self.assertEqual(self.post(dict(self.value,request_id=str(uuid.uuid4()),expected_version='2')).status_code,409)
        self.assertEqual(BusinessDraftSnapshot.objects.count(),2)
        self.assertEqual(BusinessDraft.objects.get().version,2)
    def test_owner_staff_unverified_production_and_csrf_boundaries(self):
        self.assertEqual(self.post().status_code,303)
        self.assertEqual(self.client.get(URL+'?owner=another').status_code,400)
        for method in ['GET','POST']:
            self.assertEqual(Client().generic(method,URL).status_code,401)
        verified_login(self.client,self.other)
        self.assertNotContains(self.client.get(URL),self.value['legal_business_name'])
        self.assertEqual(self.post(dict(self.value,owner=str(self.owner.pk))).status_code,400)
        self.assertEqual(BusinessDraft.objects.count(),1)
        self.other.is_staff=True;self.other.save()
        self.assertEqual(self.client.get(URL).status_code,403);self.assertEqual(self.post().status_code,403)
        self.other.is_staff=False;self.other.save()
        session=self.client.session;session.pop('shop_verified_identity');session.save()
        self.assertEqual(self.client.get(URL).status_code,403)
        verified_login(self.client,self.owner)
        for mode in ['production','bank-sandbox']:
            with override_settings(SHOP_ENV=mode):
                self.assertEqual(self.client.get(URL).status_code,404);self.assertEqual(self.post().status_code,404)
        strict=Client(enforce_csrf_checks=True);verified_login(strict,self.owner)
        self.assertEqual(self.post(client=strict).status_code,403)
        token=strict.get(URL).cookies['csrftoken'].value
        value=dict(self.value,request_id=str(uuid.uuid4()),expected_version='1',csrfmiddlewaretoken=token)
        self.assertEqual(self.post(value,strict).status_code,303)
    def test_invalid_raw_values_pending_choices_unknown_fields_and_xss(self):
        for extra in [{'host_id':'HOST_INPUT_PRIVATE_SYNTHETIC'},{'registration_country':'GB'},{'tax_status':'approved'},
                      {'deployment_country':'DE'},{'business_email':'REAL_INPUT_MUST_NOT_REFLECT@example.com'},
                      {'notes':'NOTE_INPUT_MUST_NOT_REFLECT\x00'},{'expected_version':'True'},{'legal_business_name':'X'*201}]:
            response=self.post(dict(self.value,**extra));self.assertIn(response.status_code,[400,422])
            self.assertNotIn('HOST_INPUT_PRIVATE_SYNTHETIC',response.content.decode())
            self.assertNotIn('REAL_INPUT_MUST_NOT_REFLECT',response.content.decode())
            self.assertNotIn('NOTE_INPUT_MUST_NOT_REFLECT',response.content.decode())
        self.assertEqual(BusinessDraftSnapshot.objects.count(),0)
        duplicate=urlencode(list(self.value.items())+[('legal_business_name','DUPLICATE_PRIVATE_SYNTHETIC')])
        self.assertEqual(self.client.post(URL,data=duplicate,content_type='application/x-www-form-urlencoded').status_code,400)
        self.assertEqual(self.client.post(URL,data='x'*32769,content_type='application/x-www-form-urlencoded').status_code,400)
        self.assertEqual(self.post(dict(self.value,legal_business_name='<script>synthetic()</script>')).status_code,303)
        page=self.client.get(URL);self.assertNotContains(page,'<script>synthetic()</script>');self.assertContains(page,'&lt;script&gt;')
    def race(self,same):
        clients=[Client(),Client()]
        for client in clients:verified_login(client,self.owner)
        barrier=Barrier(2)
        def run(index):
            try:
                value=dict(self.value)
                if not same:value['request_id']=str(uuid.uuid4())
                barrier.wait(timeout=10)
                return self.post(value,clients[index]).status_code
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(run,range(2)))
        self.assertEqual(sorted(results),[303,303] if same else [303,409])
        self.assertEqual(BusinessDraftSnapshot.objects.count(),1)
        self.assertEqual(BusinessDraft.objects.get().version,1)
    def test_concurrent_exact_retry(self):self.race(True)
    def test_concurrent_edits(self):self.race(False)

    def test_validation_error_preserves_original_revision_and_source(self):
        self.assertEqual(self.post().status_code,303)
        stale=dict(self.value,request_id=str(uuid.uuid4()),expected_version='1',business_email='INVALID_MUST_NOT_REFLECT',legal_business_name='STALE_PRIVATE_SYNTHETIC')
        newest=dict(self.value,request_id=str(uuid.uuid4()),expected_version='1',legal_business_name='NEWEST_PRIVATE_SYNTHETIC')
        self.assertEqual(self.post(newest).status_code,303)
        with patch.object(rules,'SOURCE_SHA256','0'*64):
            error=self.post(stale);self.assertEqual(error.status_code,422)
            self.assertNotIn('INVALID_MUST_NOT_REFLECT',error.content.decode())
            fields=dict(re.findall(r'<input[^>]*name="([^"]+)"[^>]*value="([^"]*)"',error.content.decode()))
            self.assertEqual(fields['expected_version'],'1')
            self.assertEqual(fields['source_sha256'],self.value['source_sha256'])
        corrected=dict(stale,business_email='corrected@synthetic.invalid',request_id=fields['request_id'],expected_version=fields['expected_version'])
        self.assertEqual(self.post(corrected).status_code,409)
        self.assertEqual(BusinessDraftSnapshot.objects.count(),2)
        self.assertEqual(BusinessDraftSnapshot.objects.get(version=2).details['legal_business_name'],'NEWEST_PRIVATE_SYNTHETIC')
