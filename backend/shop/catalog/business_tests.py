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
from .cart_tests import CartRecoveryMixin

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
        self.assertEqual(page['Referrer-Policy'],'same-origin');self.assertIn("frame-ancestors 'none'",page['Content-Security-Policy'])
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

    def test_accessible_validation_keeps_rejected_values_and_revisions_private(self):
        page=self.client.get(URL)
        self.assertEqual(page['Content-Security-Policy'],"default-src 'none'; style-src 'self'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'")
        self.assertNotContains(page,'aria-invalid="true"')
        invalid=dict(self.value,business_email='INVALID_PRIVATE@example.com')
        response=self.post(invalid)
        self.assertEqual(response.status_code,422)
        self.assertContains(response,'role="alert"',status_code=422)
        self.assertContains(response,'href="#id_business_email"',status_code=422)
        self.assertContains(response,'id="id_business_email_error"',status_code=422)
        field=next(field for group in response.context['groups'] for field in group['fields'] if field.name=='business_email')
        self.assertEqual(field.field.widget.attrs['aria-invalid'],'true')
        self.assertEqual(field.field.widget.attrs['aria-describedby'],'id_business_email_error')
        self.assertEqual(field.value(),'')
        self.assertNotContains(response,invalid['business_email'],status_code=422)
        self.assertEqual(BusinessDraftSnapshot.objects.count(),0)
        self.assertEqual(self.post().status_code,303)
        self.assertNotContains(self.client.get(URL),'aria-invalid="true"')

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


class BusinessRecoveryMixin(CartRecoveryMixin):
    """Compare private immutable business facts separately from HTTP/session effects."""
    def facts(self):
        from .models import QuotationBusinessScope,QuotationBusinessKey
        from .models import QuotationRequest,QuotationRequestKey,QuotationReview
        facts=super().facts()
        for name,model in [('quotations',QuotationRequest),('quotation_keys',QuotationRequestKey),
                           ('reviews',QuotationReview),('business',BusinessDraft),('business_snapshots',BusinessDraftSnapshot),
                           ('business_scopes',QuotationBusinessScope),('business_keys',QuotationBusinessKey)]:
            facts[name]=list(model.objects.order_by('id').values())
        return facts

    def assert_denied(self,response):
        self.assertEqual(response.status_code,403,response.content)
        self.assertEqual(response.json(),{'error':'verification_required'})
        self.assertEqual(response['Cache-Control'],'no-store')
        self.assertNotContains(response,'<form',status_code=403)
        self.assertNotContains(response,'BUSINESS_PRIVATE',status_code=403)
        if hasattr(self,'quotation'):self.assertNotContains(response,str(self.quotation.pk),status_code=403)


class BusinessDraftRecoveryTests(BusinessRecoveryMixin,TransactionTestCase):
    def setUp(self):
        BusinessDraftTests.setUp(self)
        self.client=Client(enforce_csrf_checks=True,raise_request_exception=False)
        verified_login(self.client,self.owner)
        self.assertEqual(self.client.get(URL).status_code,200)

    def post(self,value=None):
        value=dict(self.value if value is None else value,csrfmiddlewaretoken=self.client.cookies['csrftoken'].value)
        return self.client.post(URL,data=urlencode(value),content_type='application/x-www-form-urlencoded')

    def command_overlap(self,mode,released=False):
        from . import business_views
        if mode in ('edit','replay'):
            self.assertEqual(self.post().status_code,303)
            if mode=='edit':self.value.update(request_id=str(uuid.uuid4()),expected_version='1',notes='BUSINESS_PRIVATE_EDIT_SYNTHETIC')
        before=self.facts();parse=business_views.read_submission
        def interleave(request):
            result=parse(request);self.reset(released);return result
        with patch.object(business_views,'read_submission',side_effect=interleave):response=self.post()
        with self.subTest(check='response'):self.assert_denied(response)
        with self.subTest(check='facts'):self.assertEqual(self.facts(),before)
        self.fresh();self.assertEqual(self.post().status_code,303)
        committed=self.facts();self.assertEqual(self.post().status_code,303)
        self.assertEqual(self.facts(),committed)
        self.assertEqual(BusinessDraft.objects.get().version,2 if mode=='edit' else 1)
        self.assertEqual(BusinessDraftSnapshot.objects.count(),2 if mode=='edit' else 1)

    def test_create_after_quarantine_denies(self):self.command_overlap('create')
    def test_create_after_quarantine_release_denies(self):self.command_overlap('create',True)
    def test_edit_after_quarantine_denies(self):self.command_overlap('edit')
    def test_edit_after_quarantine_release_denies(self):self.command_overlap('edit',True)
    def test_retry_after_quarantine_denies(self):self.command_overlap('replay')
    def test_retry_after_quarantine_release_denies(self):self.command_overlap('replay',True)

    def read_overlap(self,mode,released=False):
        from . import business_views
        self.assertEqual(self.post().status_code,303);before=self.facts()
        if mode in ('page','query'):
            access=business_views.local_customer
            def interleave(request):
                result=access(request);self.assertIsNone(result);self.reset(released);return result
            with patch.object(business_views,'local_customer',side_effect=interleave):
                response=self.client.get(URL+('?ignored=1' if mode=='query' else ''))
        elif mode=='conflict':
            page=business_views.page
            def interleave(*args,**kwargs):
                self.assertEqual(kwargs['status'],409);self.reset(released);return page(*args,**kwargs)
            with patch.object(business_views,'page',side_effect=interleave):
                response=self.post(dict(self.value,request_id=str(uuid.uuid4())))
        else:
            parse=business_views.read_submission
            def interleave(request):
                result=parse(request);self.reset(released)
                if mode=='malformed':raise ValueError('synthetic invalid submission')
                return result
            value=dict(self.value,business_email='REJECTED_PRIVATE@example.com') if mode=='validation' else self.value
            with patch.object(business_views,'read_submission',side_effect=interleave):response=self.post(value)
        with self.subTest(check='response'):self.assert_denied(response)
        with self.subTest(check='facts'):self.assertEqual(self.facts(),before)
        self.fresh();self.assertContains(self.client.get(URL),self.value['legal_business_name'])
        self.assertEqual(self.facts(),before)

    def test_page_after_quarantine_denies(self):self.read_overlap('page')
    def test_page_after_quarantine_release_denies(self):self.read_overlap('page',True)
    def test_query_error_after_quarantine_denies(self):self.read_overlap('query')
    def test_query_error_after_quarantine_release_denies(self):self.read_overlap('query',True)
    def test_parse_error_after_quarantine_denies(self):self.read_overlap('malformed')
    def test_parse_error_after_quarantine_release_denies(self):self.read_overlap('malformed',True)
    def test_validation_error_after_quarantine_denies(self):self.read_overlap('validation')
    def test_validation_error_after_quarantine_release_denies(self):self.read_overlap('validation',True)
    def test_conflict_page_after_quarantine_denies(self):self.read_overlap('conflict')
    def test_conflict_page_after_quarantine_release_denies(self):self.read_overlap('conflict',True)

    def test_epoch_locked_before_business_queries_and_rendering(self):
        from django.db.models.query import QuerySet
        from . import business_views
        fetch=QuerySet._fetch_all;render=business_views.render;seen=set();active=[]
        def observe(query):
            if query.model in (BusinessDraft,BusinessDraftSnapshot):self.assert_epoch_locked();seen.add(active[0])
            return fetch(query)
        def materialize(*args,**kwargs):
            self.assert_epoch_locked();seen.add(active[0]+'-render');return render(*args,**kwargs)
        with patch.object(QuerySet,'_fetch_all',observe),patch.object(business_views,'render',side_effect=materialize):
            active[:]=['create'];self.assertEqual(self.post().status_code,303)
            active[:]=['retry'];self.assertEqual(self.post().status_code,303)
            active[:]=['page'];self.assertEqual(self.client.get(URL).status_code,200)
            active[:]=['query'];self.assertEqual(self.client.get(URL+'?ignored=1').status_code,400)
            active[:]=['parse'];self.assertEqual(self.post(dict(self.value,unknown='synthetic')).status_code,400)
            active[:]=['validation'];self.assertEqual(self.post(dict(self.value,business_email='INVALID_PRIVATE@example.com')).status_code,422)
            active[:]=['conflict'];self.assertEqual(self.post(dict(self.value,request_id=str(uuid.uuid4()))).status_code,409)
        self.assertEqual(seen,{'create','retry'}|{kind+suffix for kind in ('page','query','parse','validation','conflict') for suffix in ('','-render')})

    def test_selected_startup_after_entry_denies(self):
        from . import business_views
        access=business_views.local_customer;before=self.facts()
        def entry(request):
            with override_settings(LOCAL_RESTORE_ID=None):result=access(request)
            self.assertIsNone(result);return result
        with override_settings(LOCAL_RESTORE_ID=uuid.uuid4()),patch.object(business_views,'local_customer',side_effect=entry):
            with self.subTest(kind='get'):self.assert_denied(self.client.get(URL))
            with self.subTest(kind='post'):self.assert_denied(self.post())
        self.assertEqual(self.facts(),before)

    def test_fresh_historical_retry_keeps_source_identity_and_newer_revision(self):
        from . import business_views
        self.assertEqual(self.post().status_code,303)
        self.assertEqual(self.post(dict(self.value,request_id=str(uuid.uuid4()),expected_version='1',notes='newer synthetic')).status_code,303)
        self.reset(True);self.fresh();before=self.facts()
        with patch.object(business_views.rules,'SOURCE_SHA256','f'*64):self.assertEqual(self.post().status_code,303)
        self.assertEqual(self.client.session['business_last_confirmed_version'],1)
        self.assertEqual(self.facts(),before)
