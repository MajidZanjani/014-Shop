"""Source-derived, effect-free document prerequisites on retained owner scopes."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from unittest.mock import patch
import uuid
from django.test import Client, TransactionTestCase, SimpleTestCase, override_settings
from . import quotation_tests as fixtures
from .cart_tests import CASES
from .document_preview import DEFINITION, preview
from .models import (QuotationRequest, QuotationReview, QuotationBusinessScope, BusinessDraft,
                     BusinessDraftSnapshot, CartSnapshot)
from .rules import CATALOG
from . import business_rules
from .tests import verified_login


class DocumentSourceTests(SimpleTestCase):
    def test_compiled_source_exact_bytes_and_revision(self):
        root=Path(__file__).resolve().parents[3]
        spec=importlib.util.spec_from_file_location('document_compiler',root/'scripts/compile_document_preview.py')
        compiler=importlib.util.module_from_spec(spec);spec.loader.exec_module(compiler)
        self.assertEqual(compiler.compile_preview(),(root/'backend/shop/catalog/document_preview.json').read_text())
        self.assertEqual(DEFINITION['source_sha256'],CATALOG['source_sha256'])
        definition={key:value for key,value in DEFINITION.items() if key!='revision'}
        self.assertEqual(hashlib.sha256(json.dumps(definition,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest(),DEFINITION['revision'])
        self.assertEqual(len(DEFINITION['ip_declarations']),4)
        for row in DEFINITION['documents']:
            self.assertIsNone(row['version']);self.assertIsNone(row['body']);self.assertFalse(row['approved'])
        self.assertFalse(DEFINITION['marketing']['selected']);self.assertFalse(DEFINITION['marketing']['required'])


class DocumentPreviewTests(TransactionTestCase):
    setUp=fixtures.QuotationTests.setUp
    save_cart=fixtures.QuotationTests.save_cart
    post=fixtures.QuotationTests.post
    def capture(self):
        response=self.post();self.assertEqual(response.status_code,201)
        row=QuotationRequest.objects.get(pk=response.json()['id'])
        self.path='/purchase/quotation-documents/'+str(row.id)+'/'
        return row
    def test_profiles_have_applicable_documents_and_no_acceptance_controls(self):
        # Every source profile uses the retained cart, with four IP labels only for IP-containing carts.
        ip=copy.deepcopy(next(case['lines'] for case in CASES if case['status']!='invalid' and case['lines'] and all(line['kind']=='ip' for line in case['lines'])))
        support=copy.deepcopy(next(case['lines'] for case in CASES if case['status']!='invalid' and case['lines'] and all(line['kind']=='support' for line in case['lines'])))
        support[0]['id']=str(uuid.uuid4())
        version=1
        for lines,profile,documents,count in [(ip,'ip',{'general_terms','ip_licence','refund_policy','privacy_policy'},4),
            (support,'support_only',{'general_terms','support_terms','refund_policy','privacy_policy'},0),
            (ip+support,'mixed',{'general_terms','ip_licence','support_terms','refund_policy','privacy_policy'},4)]:
            saved=self.save_cart(version,lines);version+=1
            self.payload={'request_id':str(uuid.uuid4()),'cart_id':saved['cart_id'],'version':version}
            row=self.capture()
            value=preview(row)
            self.assertEqual(value['profile'],profile);self.assertEqual({d['id'] for d in value['documents']},documents)
            self.assertEqual(len(value['ip_declarations']),count)
            self.assertFalse(value['acceptance_enabled']);self.assertFalse(value['checkout_enabled'])
            response=self.client.get(self.path);self.assertEqual(response.status_code,200)
            self.assertContains(response,'No declaration, consent or acceptance is recorded.')
            self.assertNotContains(response,'<form');self.assertNotContains(response,'<input');self.assertNotContains(response,'PLACE ORDER')
            if profile=='support_only':
                self.assertNotContains(response,'NIC / host IDs');self.assertNotContains(response,'xSPI-MC IP Licence Agreement')
                self.assertContains(response,'Support packages:')
            else:
                for declaration in DEFINITION['ip_declarations']:self.assertContains(response,declaration['text'])
    def test_owner_modes_verification_methods_and_query_boundaries(self):
        self.capture()
        self.assertEqual(Client().get(self.path).status_code,401)
        verified_login(self.client,self.other)
        self.assertEqual(self.client.get(self.path).status_code,404)
        verified_login(self.client,self.owner)
        for method in ['post','put','delete','patch']:
            self.assertEqual(getattr(self.client,method)(self.path,{'accept':True}).status_code,405)
        self.assertEqual(self.client.get(self.path+'?accept=true').status_code,400)
        for mode in ['production','bank-sandbox']:
            with override_settings(SHOP_ENV=mode):self.assertEqual(self.client.get(self.path).status_code,404)
        self.owner.is_staff=True;self.owner.save()
        self.assertEqual(self.client.get(self.path).status_code,403)
        self.owner.is_staff=False;self.owner.save()
        session=self.client.session;session.pop('shop_verified_identity');session.save()
        self.assertEqual(self.client.get(self.path).status_code,403)
        self.assertEqual(QuotationReview.objects.count(),0)
    def test_preview_uses_captured_lines_and_no_domain_writes(self):
        row=self.capture();original=copy.deepcopy(row.snapshot.lines)
        self.save_cart(1,CASES[2]['lines'])
        counts=(QuotationRequest.objects.count(),CartSnapshot.objects.count(),QuotationBusinessScope.objects.count(),QuotationReview.objects.count(),BusinessDraftSnapshot.objects.count())
        for _ in range(2):
            response=self.client.get(self.path);self.assertEqual(response.status_code,200)
            self.assertEqual(preview(row)['lines'],original)
            self.assertEqual(preview(row)['cart_version'],1)
            self.assertEqual(response['Cache-Control'],'no-store');self.assertEqual(response['Referrer-Policy'],'no-referrer')
            self.assertIn("form-action 'none'",response['Content-Security-Policy'])
            self.assertEqual(response['Vary'],'Cookie')
        self.assertEqual(counts,(QuotationRequest.objects.count(),CartSnapshot.objects.count(),QuotationBusinessScope.objects.count(),QuotationReview.objects.count(),BusinessDraftSnapshot.objects.count()))
    def test_business_metadata_is_private_value_free_and_current_scope_specific(self):
        row=self.capture();draft=BusinessDraft.objects.create(owner=self.owner,version=1)
        clean=business_rules.empty_details();clean.update(legal_business_name='NEVER_DISPLAY_PRIVATE_BUSINESS',business_email='private@document.synthetic.invalid')
        details=business_rules.resolve_details(clean)
        saved=BusinessDraftSnapshot.objects.create(draft=draft,version=1,request_id=uuid.uuid4(),schema_version=business_rules.SCHEMA_VERSION,
            source_sha256=business_rules.SOURCE_SHA256,submission_digest=business_rules.submission_digest(clean),details=details,evaluation=business_rules.evaluate_details(details))
        QuotationBusinessScope.objects.create(quotation=row,version=1,business_snapshot=saved)
        row.business_version=1;row.save()
        response=self.client.get(self.path)
        self.assertContains(response,'Business scope 1 · Saved business revision 1')
        self.assertNotContains(response,'NEVER_DISPLAY_PRIVATE_BUSINESS');self.assertNotContains(response,'private@document.synthetic.invalid')
        self.assertNotContains(response,saved.submission_digest)
        for field in business_rules.PENDING:self.assertIsNone(saved.details[field])
        # An inconsistent FK must not disclose the unrelated revision or private fields.
        draft.owner=self.other;draft.save()
        response=self.client.get(self.path);self.assertContains(response,'Saved business revision unavailable')
        self.assertNotContains(response,'NEVER_DISPLAY_PRIVATE_BUSINESS')
    def test_source_or_scope_drift_fails_closed_and_stale_catalog_is_explicit(self):
        row=self.capture()
        for changed in [{'source_sha256':'0'*64},{'revision':'0'*64}]:
            with patch.dict(DEFINITION,changed):
                response=self.client.get(self.path);self.assertEqual(response.status_code,409)
                self.assertContains(response,'Preview unavailable',status_code=409)
                self.assertNotContains(response,DEFINITION['ip_declarations'][0]['text'],status_code=409)
                self.assertEqual(preview(row)['documents'],[])
        with patch.dict(CATALOG,revision='f'*64):
            response=self.client.get(self.path);self.assertEqual(response.status_code,200)
            self.assertContains(response,'captured catalog differs')
            self.assertFalse(preview(row)['acceptance_enabled'])
        for invalid in [[],[{'kind':'unsupported'}],None]:
            row.snapshot.lines=invalid
            if invalid is not None:row.snapshot.save();self.assertEqual(self.client.get(self.path).status_code,409)
            self.assertEqual(preview(row)['profile'],'unavailable')
