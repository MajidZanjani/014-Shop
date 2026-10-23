"""Actual synthetic staff/CSRF requests and durable captures on owned PostgreSQL."""
import copy
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import re
from unittest.mock import patch
from urllib.parse import urlencode
import uuid
from django.db import DatabaseError, connection, connections
from django.test import Client, TransactionTestCase, override_settings
from shop.catalog import request_envelope_tests as fixtures
from shop.catalog.envelope_capture import capture_request_envelope
from shop.catalog.request_envelope import EnvelopeError, prepare_request_envelope
from shop.catalog.models import (RequestEnvelope, RequestArchiveIntent, BusinessDraftSnapshot,
    ArchiveDestination, ArchiveWorkAuthorization, ArchiveWorkClaim, ArchivePreparedVerification)
from . import staff_tests
from .models import StaffQuotationGrant

@override_settings(**staff_tests.STAFF_SETTINGS)
class RequestEvidenceTests(TransactionTestCase):
    setUp=fixtures.RequestEnvelopeTests.setUp
    owner_context=fixtures.RequestEnvelopeTests.owner_context
    owner_get=fixtures.RequestEnvelopeTests.owner_get
    attach=fixtures.RequestEnvelopeTests.attach
    business=fixtures.RequestEnvelopeTests.business
    enable_private=fixtures.RequestEnvelopeTests.enable_private
    post=fixtures.RequestEnvelopeTests.post
    challenge=fixtures.RequestEnvelopeTests.challenge
    authenticated=fixtures.RequestEnvelopeTests.authenticated
    grant=fixtures.RequestEnvelopeTests.grant

    def url(self,version=1):return '/staff/quotation-requests/'+str(self.quotation.pk)+'/request-evidence/'+str(version)+'/'
    def staff(self):
        self.assertEqual(self.attach().status_code,303)
        self.authenticated();self.grant();self.enable_private(1)
    def form(self,version=1):
        response=self.browser.get(self.url(version));self.assertEqual(response.status_code,200)
        return {'action':'capture','expected_source_sha256':re.search(r'name="expected_source_sha256" value="([0-9a-f]{64})"',response.content.decode())[1],
            'csrfmiddlewaretoken':self.browser.cookies['shop_staff_csrftoken'].value}
    def submit(self,value,version=1,raw=None,**kwargs):
        return self.browser.post(self.url(version),data=urlencode(value) if raw is None else raw,
            content_type='application/x-www-form-urlencoded',**kwargs)
    def assert_private(self,response):
        self.assertEqual(response['Cache-Control'],'no-store');self.assertEqual(response['Referrer-Policy'],'no-referrer')
        self.assertIn('Cookie',response['Vary']);self.assertIn("form-action 'self'",response['Content-Security-Policy'])
    def assert_no_work(self):
        for model in (ArchiveDestination,ArchiveWorkAuthorization,ArchiveWorkClaim,ArchivePreparedVerification):
            self.assertEqual(model.objects.count(),0)
        for intent in RequestArchiveIntent.objects.all():
            self.assertIn(intent.state,('pending','held'));self.assertFalse(intent.effects_authorized);self.assertFalse(intent.retention_qualified)

    def test_preview_no_writes_capture_replay_safe_confirmation_and_original_actor(self):
        self.staff()
        detail=self.browser.get('/staff/quotation-requests/'+str(self.quotation.pk)+'/',HTTP_ACCEPT='text/html')
        self.assertContains(detail,self.url())
        value=self.form();self.assertEqual(RequestEnvelope.objects.count(),0);self.assertEqual(RequestArchiveIntent.objects.count(),0)
        with patch('shop.adapters.evidence_archive.PreparedArchive.publish',side_effect=AssertionError('no storage')):
            first=self.submit(value);self.assertContains(first,'Captured',status_code=201);self.assert_private(first)
            original=list(RequestEnvelope.objects.values());intents=list(RequestArchiveIntent.objects.values())
            second=self.submit(value);self.assertContains(second,'Original capture retained');self.assert_private(second)
        self.assertEqual(list(RequestEnvelope.objects.values()),original);self.assertEqual(list(RequestArchiveIntent.objects.values()),intents)
        row=RequestEnvelope.objects.get();self.assertEqual(row.captured_by_id,self.user.pk)
        self.assertEqual(row.staff_generation,self.credential.generation);self.assertIsNotNone(row.mfa_verified_at)
        for response in (first,second):
            for secret in ('BUSINESS_SCOPE_ONE_PRIVATE_SYNTHETIC',value['expected_source_sha256'],str(row.staff_generation),str(row.pk),str(RequestArchiveIntent.objects.get().pk)):
                self.assertNotIn(secret,response.content.decode())
        self.assertNotIn(value['expected_source_sha256'],str(self.browser.session.items()))
        self.assert_no_work()

    def test_strict_parser_methods_queries_csrf_and_size_have_no_capture(self):
        self.staff();value=self.form()
        bad=[dict(value,action='approve'),dict(value,extra='x'),dict(value,expected_source_sha256='F'*64),dict(value,expected_source_sha256='bad')]
        for item in bad:self.assertEqual(self.submit(item).status_code,400)
        self.assertEqual(self.submit(value,raw=urlencode(value)+'&action=capture').status_code,400)
        self.assertEqual(self.submit(value,raw=urlencode(value)+'&csrfmiddlewaretoken='+value['csrfmiddlewaretoken']).status_code,400)
        self.assertEqual(self.submit(value,raw=urlencode(value)+'&extra='+'x'*1024).status_code,400)
        self.assertEqual(self.submit({'action':'capture','expected_source_sha256':value['expected_source_sha256']}).status_code,403)
        self.assertEqual(self.browser.post(self.url(),data='{}',content_type='application/json',HTTP_X_CSRFTOKEN=value['csrfmiddlewaretoken']).status_code,400)
        self.assertEqual(self.browser.get(self.url()+'?capture=1').status_code,400)
        self.assertEqual(self.browser.post(self.url()+'?capture=1',data=urlencode(value),content_type='application/x-www-form-urlencoded').status_code,400)
        self.assertEqual(self.browser.head(self.url()).status_code,405)
        self.assertEqual(RequestEnvelope.objects.count(),0);self.assertEqual(RequestArchiveIntent.objects.count(),0);self.assert_no_work()

    def test_digest_mismatch_before_insert_and_replay_and_stale_source(self):
        self.staff();value=self.form()
        self.assertEqual(self.submit(dict(value,expected_source_sha256='0'*64)).status_code,409)
        self.assertEqual(RequestEnvelope.objects.count(),0)
        changed=copy.deepcopy(self.saved.details);changed['trading_name']='PRIVATE_CHANGED_SOURCE'
        BusinessDraftSnapshot.objects.filter(pk=self.saved.pk).update(details=changed)
        self.assertEqual(self.submit(value).status_code,409);self.assertEqual(RequestEnvelope.objects.count(),0)
        BusinessDraftSnapshot.objects.filter(pk=self.saved.pk).update(details=self.saved.details)
        self.assertEqual(self.submit(value).status_code,201)
        original=list(RequestEnvelope.objects.values())
        self.assertEqual(self.submit(dict(value,expected_source_sha256='0'*64)).status_code,409)
        self.assertEqual(list(RequestEnvelope.objects.values()),original);self.assert_no_work()

    def test_exact_historical_scope_and_unbound_scope_do_not_retarget(self):
        self.staff();old=self.form();unbound=self.form(0)
        self.business(2,'PRIVATE_NEXT_SCOPE')
        self.assertEqual(self.attach(dict(self.request,request_id=str(uuid.uuid4()),expected_scope_version='1',business_version='2')).status_code,303)
        self.assertEqual(self.submit(old).status_code,201)
        self.assertEqual(self.submit(unbound,0).status_code,201)
        self.assertEqual(self.browser.get(self.url(2)).status_code,404)
        self.enable_private(2)
        self.assertEqual(self.submit(old).status_code,404)
        self.assertEqual(self.browser.get(self.url()).status_code,404)
        self.assertEqual(self.submit(self.form(2),2).status_code,201)
        self.assertEqual(set(RequestEnvelope.objects.values_list('business_version',flat=True)),{0,1,2})
        self.assertNotIn(b'PRIVATE_NEXT_SCOPE',bytes(RequestEnvelope.objects.get(business_version=1).payload));self.assert_no_work()

    def test_current_grants_mfa_owner_and_runtime_required_for_preview_capture_retry(self):
        self.assertEqual(self.browser.get(self.url()).status_code,403)
        self.staff();value=self.form();self.assertEqual(self.submit(value).status_code,201)
        StaffQuotationGrant.objects.filter(user=self.user).update(business_scope_version=0)
        self.assertEqual(self.browser.get(self.url()).status_code,404);self.assertEqual(self.submit(value).status_code,404)
        self.enable_private(1)
        cart=self.quotation.cart;owner=cart.owner;cart.owner=self.other;cart.save(update_fields=['owner'])
        self.assertEqual(self.browser.get(self.url()).status_code,404);self.assertEqual(self.submit(value).status_code,404)
        cart.owner=owner;cart.save(update_fields=['owner'])
        with override_settings(SHOP_ENV='production'):
            self.assertEqual(self.browser.get(self.url()).status_code,404);self.assertEqual(self.submit(value).status_code,404)
        StaffQuotationGrant.objects.filter(user=self.user).delete()
        self.assertEqual(self.submit(value).status_code,404);self.grant();self.enable_private(1)
        session=self.browser.session;session['shop_staff_mfa']={**session['shop_staff_mfa'],'verified_at':0};session.save()
        self.assertEqual(self.browser.get(self.url()).status_code,403);self.assertEqual(self.submit(value).status_code,403)
        self.assertEqual(RequestEnvelope.objects.count(),1);self.assert_no_work()

    def test_safe_unavailable_database_source_and_unknown_scope(self):
        self.staff();value=self.form()
        self.assertEqual(self.browser.get(self.url(1000000001)).status_code,404)
        for target in ('prepare_request_envelope','capture_request_envelope','staff_credential'):
            with patch('shop.access.request_evidence.'+target,side_effect=DatabaseError('PRIVATE_DB_CANARY')):
                response=self.submit(value) if target=='capture_request_envelope' else self.browser.get(self.url())
                self.assertEqual(response.status_code,503);self.assert_private(response);self.assertNotIn(b'PRIVATE_DB_CANARY',response.content)
        with patch('shop.access.request_evidence.prepare_request_envelope',side_effect=EnvelopeError('PRIVATE_SOURCE_CANARY')):
            response=self.browser.get(self.url());self.assertEqual(response.status_code,404);self.assertNotIn(b'PRIVATE_SOURCE_CANARY',response.content)
        self.assertEqual(RequestEnvelope.objects.count(),0);self.assert_no_work()

    def test_service_digest_is_validated_and_compared_inside_locked_capture_transaction(self):
        self.staff();request=self.browser.get('/staff/quotation-requests/').wsgi_request
        for bad in ('bad','F'*64,1,False):
            with self.assertRaises(EnvelopeError):capture_request_envelope(request,self.quotation.pk,1,expected_source_sha256=bad)
        observed=[]
        def locked(*args):
            raw=prepare_request_envelope(*args)
            observed.append(connection.in_atomic_block)
            self.assertEqual(RequestEnvelope.objects.count(),0)
            return raw
        digest=self.form()['expected_source_sha256']
        with patch('shop.catalog.envelope_capture.prepare_request_envelope',side_effect=locked):
            reference=capture_request_envelope(request,self.quotation.pk,1,expected_source_sha256=digest)
        self.assertEqual(observed,[True]);self.assertTrue(reference.created);self.assert_no_work()

    def test_concurrent_exact_staff_form_submissions_commit_one_fact_and_intent(self):
        self.staff();value=self.form();barrier=Barrier(2)
        clients=[Client(enforce_csrf_checks=True,HTTP_HOST='staff.localhost') for _ in range(2)]
        for client in clients:client.cookies=self.browser.cookies.copy()
        def run(client):
            try:
                barrier.wait(timeout=10)
                response=client.post(self.url(),data=urlencode(value),content_type='application/x-www-form-urlencoded')
                return response.status_code,response.content.decode()
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(run,clients))
        self.assertEqual(sorted(status for status,_ in results),[200,201])
        self.assertEqual(sum('Original capture retained' in body for _,body in results),1)
        self.assertEqual(RequestEnvelope.objects.count(),1);self.assertEqual(RequestArchiveIntent.objects.count(),1)
        self.assertEqual(RequestEnvelope.objects.get().captured_by_id,self.user.pk);self.assert_no_work()

    def test_staff_retry_of_owner_capture_preserves_attribution_and_held_intent(self):
        self.staff();value=self.form()
        with self.owner_context():request=self.owner_client.get('/api/v1/customer/session/').wsgi_request
        first=capture_request_envelope(request,self.quotation.pk,1,expected_source_sha256=value['expected_source_sha256'])
        self.assertTrue(first.created)
        RequestArchiveIntent.objects.filter(pk=first.intent_id).update(state='held')
        original=list(RequestEnvelope.objects.values());intent=list(RequestArchiveIntent.objects.values())
        response=self.submit(value);self.assertContains(response,'Original capture retained')
        self.assertNotContains(response,'unbound');self.assert_private(response)
        self.assertEqual(list(RequestEnvelope.objects.values()),original);self.assertEqual(list(RequestArchiveIntent.objects.values()),intent)
        row=RequestEnvelope.objects.get();self.assertEqual(row.captured_by_id,self.owner.pk)
        self.assertIsNone(row.staff_generation);self.assertIsNone(row.mfa_verified_at);self.assert_no_work()
