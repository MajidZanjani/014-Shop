"""Real PostgreSQL atomic request evidence+intent, without storage/network calls."""
from concurrent.futures import ThreadPoolExecutor
import copy
from threading import Barrier
from unittest.mock import patch
import uuid
from django.db import connections,IntegrityError,transaction
from django.test import TransactionTestCase,override_settings
from shop.access import staff_tests
from shop.access.models import StaffQuotationGrant
from shop.adapters.evidence_archive import PreparedArchive
from . import request_envelope_tests as fixtures
from .models import RequestEnvelope,RequestArchiveIntent,BusinessDraftSnapshot
from .envelope_capture import capture_request_envelope
from .request_envelope import EnvelopeError

@override_settings(**staff_tests.STAFF_SETTINGS)
class EnvelopeCaptureTests(TransactionTestCase):
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

    def owner_request(self):
        with self.owner_context():return self.owner_client.get('/api/v1/customer/session/').wsgi_request
    def save_envelope(self,version=1,request=None):
        return capture_request_envelope(request or self.owner_request(),self.quotation.pk,version)

    def test_atomic_capture_exact_replay_and_no_storage_or_summary_leak(self):
        self.assertEqual(self.attach().status_code,303)
        with patch.object(PreparedArchive,'publish',side_effect=AssertionError('storage must not run')):
            first=self.save_envelope();second=self.save_envelope()
        self.assertTrue(first.created);self.assertFalse(second.created)
        self.assertEqual(first.envelope_id,second.envelope_id);self.assertEqual(first.intent_id,second.intent_id)
        row=RequestEnvelope.objects.get();intent=RequestArchiveIntent.objects.get()
        self.assertEqual(row.captured_by,self.owner);self.assertIsNone(row.staff_generation)
        self.assertEqual(intent.envelope,row);self.assertEqual(intent.state,'pending')
        self.assertFalse(intent.effects_authorized);self.assertFalse(intent.retention_qualified)
        self.assertIn(b'BUSINESS_SCOPE_ONE_PRIVATE_SYNTHETIC',bytes(row.payload))
        ordinary=self.owner_get('/api/v1/quotation-requests/'+str(self.quotation.pk)+'/')
        self.assertNotContains(ordinary,'BUSINESS_SCOPE_ONE_PRIVATE_SYNTHETIC')
        self.assertNotContains(ordinary,row.sha256);self.assertNotIn(row.sha256,repr(first))

    def test_intent_insert_failure_rolls_back_both_and_retry_succeeds(self):
        self.assertEqual(self.attach().status_code,303)
        with patch.object(RequestArchiveIntent.objects,'create',side_effect=IntegrityError('synthetic insert failure')):
            with self.assertRaises(EnvelopeError):self.save_envelope()
        self.assertEqual(RequestEnvelope.objects.count(),0);self.assertEqual(RequestArchiveIntent.objects.count(),0)
        self.assertTrue(self.save_envelope().created)
        self.assertEqual(RequestEnvelope.objects.count(),1);self.assertEqual(RequestArchiveIntent.objects.count(),1)

    def test_changed_same_scope_conflicts_without_overwrite_and_scopes_stay_separate(self):
        self.assertEqual(self.attach().status_code,303);first=self.save_envelope()
        row=RequestEnvelope.objects.get();original=bytes(row.payload)
        changed=copy.deepcopy(self.saved.details);changed['trading_name']='PRIVATE_TAMPERED_RECORD'
        BusinessDraftSnapshot.objects.filter(pk=self.saved.pk).update(details=changed)
        with self.assertRaises(EnvelopeError) as raised:self.save_envelope()
        self.assertEqual(str(raised.exception),'capture_conflict')
        row.refresh_from_db();self.assertEqual(bytes(row.payload),original)
        BusinessDraftSnapshot.objects.filter(pk=self.saved.pk).update(details=self.saved.details)
        self.business(2,'PRIVATE_NEXT_CAPTURE_SCOPE')
        self.assertEqual(self.attach(dict(self.request,request_id=str(uuid.uuid4()),expected_scope_version='1',business_version='2')).status_code,303)
        second=self.save_envelope(2);self.assertNotEqual(first.envelope_id,second.envelope_id)
        self.assertFalse(self.save_envelope(1).created)
        self.assertEqual(RequestEnvelope.objects.count(),2);self.assertEqual(RequestArchiveIntent.objects.count(),2)

    def test_revoked_private_grant_cannot_reconcile_and_actor_attribution_is_retained(self):
        self.assertEqual(self.attach().status_code,303)
        self.authenticated();self.grant();self.enable_private(1)
        request=self.browser.get('/staff/quotation-requests/').wsgi_request
        first=self.save_envelope(request=request);row=RequestEnvelope.objects.get()
        self.assertEqual(row.captured_by,self.user);self.assertEqual(row.staff_generation,self.credential.generation)
        self.assertIsNotNone(row.mfa_verified_at)
        self.assertFalse(self.save_envelope().created)
        row.refresh_from_db();self.assertEqual(row.captured_by,self.user)
        StaffQuotationGrant.objects.filter(user=self.user).update(business_scope_version=0)
        with self.assertRaises(EnvelopeError):self.save_envelope(request=request)
        self.assertEqual(RequestEnvelope.objects.count(),1);self.assertEqual(RequestArchiveIntent.objects.count(),1)

    def test_owner_and_staff_competing_captures_return_one_semantic_fact_and_intent(self):
        self.assertEqual(self.attach().status_code,303)
        self.authenticated();self.grant();self.enable_private(1)
        requests=[self.owner_request(),self.browser.get('/staff/quotation-requests/').wsgi_request]
        barrier=Barrier(2)
        def run(request):
            try:
                barrier.wait(timeout=10)
                return capture_request_envelope(request,self.quotation.pk,1)
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(run,requests))
        self.assertEqual(sum(item.created for item in results),1)
        self.assertEqual(len({item.envelope_id for item in results}),1)
        self.assertEqual(len({item.intent_id for item in results}),1)
        self.assertEqual(RequestEnvelope.objects.count(),1);self.assertEqual(RequestArchiveIntent.objects.count(),1)

    def test_database_constraints_and_corrupt_missing_intent_are_held(self):
        self.assertEqual(self.attach().status_code,303);self.save_envelope()
        row=RequestEnvelope.objects.get();intent=RequestArchiveIntent.objects.get()
        for model,key,updates in [
            (RequestEnvelope,row.pk,{'byte_length':1}),
            (RequestEnvelope,row.pk,{'payload':b'x'*131073,'byte_length':131073}),
            (RequestEnvelope,row.pk,{'sha256':'bad'}),
            (RequestEnvelope,row.pk,{'schema_version':2}),
            (RequestArchiveIntent,intent.pk,{'state':'local-verified'}),
            (RequestArchiveIntent,intent.pk,{'effects_authorized':True}),
            (RequestArchiveIntent,intent.pk,{'retention_qualified':True}),
            (RequestArchiveIntent,intent.pk,{'destination_profile':'production'}),
        ]:
            with self.assertRaises(IntegrityError):
                with transaction.atomic():model.objects.filter(pk=key).update(**updates)
        RequestArchiveIntent.objects.filter(pk=intent.pk).update(state='held')
        self.assertFalse(self.save_envelope().created)
        RequestArchiveIntent.objects.filter(pk=intent.pk).delete()
        with self.assertRaises(EnvelopeError):self.save_envelope()
        self.assertEqual(RequestEnvelope.objects.count(),1);self.assertEqual(RequestArchiveIntent.objects.count(),0)

    def test_capture_owns_commit_boundary_and_rejects_an_outer_transaction(self):
        self.assertEqual(self.attach().status_code,303)
        request=self.owner_request()
        with transaction.atomic():
            with self.assertRaises(EnvelopeError) as raised:self.save_envelope(request=request)
            self.assertEqual(str(raised.exception),'capture_transaction_active')
        self.assertEqual(RequestEnvelope.objects.count(),0)
        self.assertEqual(RequestArchiveIntent.objects.count(),0)
        self.assertTrue(self.save_envelope(request=request).created)
