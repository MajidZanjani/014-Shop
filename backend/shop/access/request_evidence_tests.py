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
    def assert_private(self,response,policy='same-origin'):
        self.assertEqual(response['Cache-Control'],'no-store');self.assertEqual(response['Referrer-Policy'],policy)
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
                self.assertEqual(response.status_code,503);self.assert_private(response,policy='no-referrer');self.assertNotIn(b'PRIVATE_DB_CANARY',response.content)
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

    def status_url(self,version=1):return self.url(version)+'status/'
    def assert_status(self,response,status):
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json(),{'status':status,'evidence_class':'local-synthetic','evidence_kind':'prepared',
            'retention_qualified':False,'effects_authorized':False})
        self.assertEqual(response['Cache-Control'],'no-store');self.assertEqual(response['Referrer-Policy'],'no-referrer')
        self.assertIn('Cookie',response['Vary']);self.assertIn("form-action 'none'",response['Content-Security-Policy'])

    def test_capture_status_absent_recorded_retry_and_held_are_safe_read_only(self):
        from django.test.utils import CaptureQueriesContext
        self.staff();value=self.form()
        self.assert_status(self.browser.get(self.status_url()),'capture_not_recorded')
        self.assertEqual(RequestEnvelope.objects.count(),0);self.assertEqual(RequestArchiveIntent.objects.count(),0)
        self.assertEqual(self.submit(value).status_code,201)
        self.assertEqual(self.submit(value).status_code,200)
        row=RequestEnvelope.objects.get();RequestArchiveIntent.objects.update(state='held')
        before=list(RequestEnvelope.objects.values()),list(RequestArchiveIntent.objects.values())
        with patch('shop.access.request_evidence.capture_request_envelope',side_effect=AssertionError('no capture')), \
             patch('shop.adapters.evidence_archive.PreparedArchive.publish',side_effect=AssertionError('no I/O')), \
             patch('shop.adapters.evidence_archive.PreparedArchive.recover',side_effect=AssertionError('no I/O')), \
             patch('shop.adapters.archive_destination.BoundPreparedArchive.attest',side_effect=AssertionError('no I/O')), \
             CaptureQueriesContext(connection) as queries:
            self.assert_status(self.browser.get(self.status_url()),'capture_recorded')
            html=self.browser.get(self.status_url(),HTTP_ACCEPT='text/html')
        self.assertEqual((list(RequestEnvelope.objects.values()),list(RequestArchiveIntent.objects.values())),before)
        self.assertFalse(any(re.match(r'\s*(INSERT|UPDATE|DELETE|ALTER|CREATE|DROP)\b',q['sql'],re.I) for q in queries))
        self.assertContains(html,'Prepared database capture recorded');self.assertContains(html,'grants retry or work permission')
        self.assertNotContains(html,'<form');self.assertNotContains(html,'csrfmiddlewaretoken')
        self.assertContains(html,self.url());self.assertContains(html,'/staff/quotation-requests/'+str(self.quotation.pk)+'/')
        for secret in ('BUSINESS_SCOPE_ONE_PRIVATE_SYNTHETIC',row.sha256,str(row.pk),str(row.staff_generation),str(RequestArchiveIntent.objects.get().pk)):
            self.assertNotIn(secret,html.content.decode())
        self.assert_no_work()

    def test_capture_status_historical_and_explicit_unbound_never_retarget(self):
        self.staff();self.assertEqual(self.submit(self.form()).status_code,201)
        self.business(2,'PRIVATE_NEXT_OBSERVATION_SCOPE')
        self.assertEqual(self.attach(dict(self.request,request_id=str(uuid.uuid4()),expected_scope_version='1',business_version='2')).status_code,303)
        self.assert_status(self.browser.get(self.status_url()),'capture_recorded')
        self.assert_status(self.browser.get(self.status_url(0)),'capture_not_recorded')
        self.assertEqual(self.browser.get(self.status_url(2)).status_code,404)
        self.enable_private(2)
        self.assertEqual(self.browser.get(self.status_url()).status_code,404)
        self.assert_status(self.browser.get(self.status_url(2)),'capture_not_recorded')
        self.assertEqual(RequestEnvelope.objects.count(),1);self.assert_no_work()

    def test_capture_status_permissions_mfa_owner_and_environment(self):
        self.assertEqual(self.browser.get(self.status_url()).status_code,403)
        self.staff();self.assertEqual(self.submit(self.form()).status_code,201)
        StaffQuotationGrant.objects.filter(user=self.user).delete()
        self.assertEqual(self.browser.get(self.status_url()).status_code,404)
        self.grant();self.enable_private(1)
        cart=self.quotation.cart;owner=cart.owner;cart.owner=self.other;cart.save(update_fields=['owner'])
        self.assertEqual(self.browser.get(self.status_url()).status_code,404)
        cart.owner=owner;cart.save(update_fields=['owner'])
        with override_settings(SHOP_ENV='production'):self.assertEqual(self.browser.get(self.status_url()).status_code,404)
        with self.owner_context():self.assertEqual(self.owner_client.get(self.status_url()).status_code,404)
        self.credential.enabled=False;self.credential.save(update_fields=['enabled'])
        self.assertEqual(self.browser.get(self.status_url()).status_code,403)
        self.credential.enabled=True;self.credential.save(update_fields=['enabled'])
        session=self.browser.session;session['shop_staff_mfa']={**session['shop_staff_mfa'],'verified_at':0};session.save()
        self.assertEqual(self.browser.get(self.status_url()).status_code,403)
        self.assertEqual(RequestEnvelope.objects.count(),1);self.assert_no_work()

    def test_capture_status_corrupt_fact_missing_intent_or_source_is_unavailable_not_absent(self):
        self.staff();self.assertEqual(self.submit(self.form()).status_code,201)
        row=RequestEnvelope.objects.get()
        for changes in ({'sha256':'0'*64},{'owner_id':self.other.pk}):
            RequestEnvelope.objects.filter(pk=row.pk).update(**changes)
            before=list(RequestEnvelope.objects.values())
            self.assertEqual(self.browser.get(self.status_url()).status_code,404)
            self.assertEqual(list(RequestEnvelope.objects.values()),before)
            RequestEnvelope.objects.filter(pk=row.pk).update(sha256=row.sha256,owner_id=row.owner_id)
        changed=copy.deepcopy(self.saved.details);changed['trading_name']='PRIVATE_STATUS_TAMPER'
        BusinessDraftSnapshot.objects.filter(pk=self.saved.pk).update(details=changed)
        self.assertEqual(self.browser.get(self.status_url()).status_code,404)
        BusinessDraftSnapshot.objects.filter(pk=self.saved.pk).update(details=self.saved.details)
        RequestArchiveIntent.objects.all().delete()
        self.assertEqual(self.browser.get(self.status_url()).status_code,404)
        self.assertEqual(RequestArchiveIntent.objects.count(),0);self.assertEqual(RequestEnvelope.objects.count(),1)
        self.assert_no_work()

    def test_capture_status_closed_methods_queries_errors_and_service_transaction_guards(self):
        from django.db import transaction
        from shop.catalog.envelope_capture import observe_request_capture
        self.staff();url=self.status_url()
        self.assertEqual(self.browser.get(url+'?retry=1').status_code,400)
        for method in ('head','options','put','delete','post'):
            response=getattr(self.browser,method)(url,HTTP_X_CSRFTOKEN=self.browser.cookies['shop_staff_csrftoken'].value)
            self.assertEqual(response.status_code,405);self.assertEqual(response['Allow'],'GET')
        self.assertEqual(self.browser.get(self.status_url(1000000001)).status_code,404)
        for target in ('observe_request_capture','staff_credential'):
            with patch('shop.access.request_evidence.'+target,side_effect=DatabaseError('PRIVATE_STATUS_DB')):
                response=self.browser.get(url);self.assertEqual(response.status_code,503)
                self.assertEqual(response.json(),{'error':'observation_unavailable'});self.assertNotIn(b'PRIVATE_STATUS_DB',response.content)
                self.assertIn("form-action 'none'",response['Content-Security-Policy'])
        with patch('shop.access.request_evidence.observe_request_capture',return_value='PRIVATE_BAD_STATUS'):
            self.assertEqual(self.browser.get(url).status_code,503)
        request=self.browser.get('/staff/quotation-requests/').wsgi_request
        with transaction.atomic():
            with self.assertRaisesRegex(EnvelopeError,'observation_transaction_active'):observe_request_capture(request,self.quotation.pk,1)
        connection.set_autocommit(False)
        try:
            with self.assertRaisesRegex(EnvelopeError,'observation_transaction_active'):observe_request_capture(request,self.quotation.pk,1)
        finally:connection.rollback();connection.set_autocommit(True)
        with self.owner_context():owner_request=self.owner_client.get('/api/v1/customer/session/').wsgi_request
        with self.assertRaises(EnvelopeError):observe_request_capture(owner_request,self.quotation.pk,1)
        self.assertEqual(RequestEnvelope.objects.count(),0);self.assert_no_work()

    def test_capture_status_waits_for_inflight_capture_commit_and_rollback(self):
        from threading import Event
        import time
        self.staff();value=self.form()
        for rollback in (False,True):
            with self.subTest(rollback=rollback):
                # Reset only synthetic test facts, without changing the supported setup.
                RequestArchiveIntent.objects.all().delete();RequestEnvelope.objects.all().delete()
                entered=Event();release=Event();observing=Event();pids=[]
                original_create=RequestArchiveIntent.objects.create
                def blocked_create(*args,**kwargs):
                    result=original_create(*args,**kwargs);entered.set()
                    if not release.wait(10):raise AssertionError('capture release timeout')
                    if rollback:raise EnvelopeError('synthetic_capture_rollback')
                    return result
                def reading(*args,**kwargs):
                    with connection.cursor() as cursor:cursor.execute('SELECT pg_backend_pid()');pids.append(cursor.fetchone()[0])
                    observing.set()
                    return prepare_request_envelope(*args,**kwargs)
                def run_capture():
                    client=Client(enforce_csrf_checks=True,HTTP_HOST='staff.localhost');client.cookies=self.browser.cookies.copy()
                    try:return client.post(self.url(),data=urlencode(value),content_type='application/x-www-form-urlencoded').status_code
                    finally:connections.close_all()
                def run_observation():
                    client=Client(enforce_csrf_checks=True,HTTP_HOST='staff.localhost');client.cookies=self.browser.cookies.copy()
                    try:return client.get(self.status_url())
                    finally:connections.close_all()
                with patch.object(RequestArchiveIntent.objects,'create',side_effect=blocked_create),ThreadPoolExecutor(max_workers=2) as pool:
                    capture=pool.submit(run_capture)
                    try:
                        self.assertTrue(entered.wait(10))
                        with patch('shop.catalog.envelope_capture.prepare_request_envelope',side_effect=reading):
                            observation=pool.submit(run_observation);self.assertTrue(observing.wait(10))
                            deadline=time.monotonic()+5;locked=False
                            while time.monotonic()<deadline:
                                with connection.cursor() as cursor:
                                    cursor.execute('SELECT cardinality(pg_blocking_pids(%s))>0',[pids[0]]);locked=cursor.fetchone()[0]
                                if locked:break
                                time.sleep(.01)
                            self.assertTrue(locked,'real PostgreSQL blocking lock required');self.assertFalse(observation.done())
                            release.set()
                            self.assertEqual(capture.result(timeout=10),404 if rollback else 201)
                            self.assert_status(observation.result(timeout=10),'capture_not_recorded' if rollback else 'capture_recorded')
                    finally:release.set()
                self.assertEqual(RequestEnvelope.objects.count(),0 if rollback else 1)
                self.assert_no_work()

    def operator_change_during_status(self,action):
        import io
        from pathlib import Path
        import tempfile
        from threading import Event
        import time
        from django.core.management import call_command
        from django.db import transaction
        self.staff();self.assertEqual(self.submit(self.form()).status_code,201)
        facts=list(RequestEnvelope.objects.values()),list(RequestArchiveIntent.objects.values())
        # Rollback first leaves the same authenticated session and grants for commit.
        for rollback in (True,False):
            with self.subTest(action=action,rollback=rollback),tempfile.TemporaryDirectory() as root:
                entered=Event();release=Event();observing=Event();pids={}
                def operator():
                    try:
                        with transaction.atomic():
                            with connection.cursor() as cursor:
                                cursor.execute('SELECT pg_backend_pid()');pids['operator']=cursor.fetchone()[0]
                            call_command('local_staff',action,username=self.user.username,
                                quotation=str(self.quotation.pk),capture_root=root,stdout=io.StringIO())
                            entered.set()
                            if not release.wait(10):raise AssertionError('operator release timeout')
                            if rollback:transaction.set_rollback(True)
                    finally:connections.close_all()
                def reading(*args,**kwargs):
                    with connection.cursor() as cursor:
                        cursor.execute('SELECT pg_backend_pid()');pids['observation']=cursor.fetchone()[0]
                    observing.set()
                    return prepare_request_envelope(*args,**kwargs)
                def observation():
                    client=Client(enforce_csrf_checks=True,HTTP_HOST='staff.localhost')
                    client.cookies=self.browser.cookies.copy()
                    try:return client.get(self.status_url())
                    finally:connections.close_all()
                with patch('shop.adapters.evidence_archive.PreparedArchive.publish',side_effect=AssertionError('no archive I/O')), \
                     patch('shop.adapters.evidence_archive.PreparedArchive.recover',side_effect=AssertionError('no archive I/O')), \
                     patch('shop.adapters.archive_destination.BoundPreparedArchive.attest',side_effect=AssertionError('no archive I/O')), \
                     ThreadPoolExecutor(max_workers=2) as pool:
                    change=pool.submit(operator)
                    try:
                        self.assertTrue(entered.wait(10),'supported operator change must hold locks')
                        operator_files={p.name:p.read_bytes() for p in Path(root).iterdir()}
                        with patch('shop.catalog.envelope_capture.prepare_request_envelope',side_effect=reading):
                            read=pool.submit(observation);self.assertTrue(observing.wait(10))
                            deadline=time.monotonic()+5;blocked=False
                            while time.monotonic()<deadline:
                                with connection.cursor() as cursor:
                                    cursor.execute('SELECT %s = ANY(pg_blocking_pids(%s))',
                                        [pids['operator'],pids['observation']]);blocked=cursor.fetchone()[0]
                                if blocked:break
                                time.sleep(.01)
                            self.assertTrue(blocked,'exact operator backend must block observation')
                            self.assertFalse(read.done());release.set();change.result(timeout=10)
                            response=read.result(timeout=10)
                        if rollback:self.assert_status(response,'capture_recorded')
                        else:
                            self.assertEqual(response.status_code,404)
                            self.assertEqual(response.json(),{'error':'not_found'})
                            self.assertIn("form-action 'none'",response['Content-Security-Policy'])
                        self.assertEqual({p.name:p.read_bytes() for p in Path(root).iterdir()},operator_files)
                    finally:release.set()
                self.assertEqual((list(RequestEnvelope.objects.values()),list(RequestArchiveIntent.objects.values())),facts)
                self.assert_no_work()

    def test_capture_status_waits_for_operator_credential_reset_commit_and_rollback(self):
        self.operator_change_during_status('reset')

    def test_capture_status_waits_for_operator_credential_revoke_commit_and_rollback(self):
        self.operator_change_during_status('revoke')

    def test_capture_status_waits_for_operator_business_grant_withdrawal_commit_and_rollback(self):
        self.operator_change_during_status('revoke-business')
