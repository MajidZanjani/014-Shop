"""Explicit local destination binding; no worker or business publication."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import tempfile
from threading import Barrier
from unittest.mock import patch
import uuid
from django.db import connection,connections,IntegrityError,transaction
from django.test import TransactionTestCase,override_settings
from shop.access import staff_tests
from shop.access.models import StaffQuotationGrant
from shop.adapters.archive_destination import initialize_destination,BoundPreparedArchive,MARKER
from . import envelope_capture_tests as fixtures
from .archive_binding import bind_request_destination
from .models import RequestArchiveIntent,ArchiveDestination
from .request_envelope import EnvelopeError

@override_settings(**staff_tests.STAFF_SETTINGS)
class ArchiveBindingTests(TransactionTestCase):
    owner_context=fixtures.EnvelopeCaptureTests.owner_context
    owner_request=fixtures.EnvelopeCaptureTests.owner_request
    attach=fixtures.EnvelopeCaptureTests.attach
    business=fixtures.EnvelopeCaptureTests.business
    save_envelope=fixtures.EnvelopeCaptureTests.save_envelope
    post=fixtures.EnvelopeCaptureTests.post
    challenge=fixtures.EnvelopeCaptureTests.challenge
    authenticated=fixtures.EnvelopeCaptureTests.authenticated
    grant=fixtures.EnvelopeCaptureTests.grant
    enable_private=fixtures.EnvelopeCaptureTests.enable_private
    def setUp(self):
        fixtures.EnvelopeCaptureTests.setUp(self)
        self.assertEqual(self.attach().status_code,303);self.captured=self.save_envelope()
        self.temporary=tempfile.TemporaryDirectory();self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name)
        self.proof=initialize_destination(self.root,uuid.uuid4())
    def bind(self,archive,request=None):
        return bind_request_destination(request or self.owner_request(),self.quotation.pk,1,archive)

    def test_bind_reopen_exact_retry_and_no_publication_or_transaction_io(self):
        with BoundPreparedArchive(self.root,self.proof) as archive:
            original=archive.attest
            def observed():
                self.assertFalse(connection.in_atomic_block);return original()
            with patch.object(archive,'attest',observed):first=self.bind(archive)
        intent=RequestArchiveIntent.objects.get();bound_at=intent.destination_bound_at
        self.assertTrue(first.created);self.assertEqual(first.destination_id,self.proof.id)
        self.assertEqual(intent.destination_bound_by,self.owner);self.assertIsNone(intent.binding_staff_generation)
        self.assertFalse(intent.effects_authorized);self.assertFalse(intent.retention_qualified)
        with BoundPreparedArchive(self.root,self.proof) as archive:self.assertFalse(self.bind(archive).created)
        intent.refresh_from_db();self.assertEqual(intent.destination_bound_at,bound_at)
        self.assertEqual(ArchiveDestination.objects.count(),1)
        self.assertEqual([p.name for p in self.root.iterdir()],[MARKER])

    def test_different_root_cannot_rebind_and_held_work_is_not_cleared(self):
        RequestArchiveIntent.objects.update(state='held')
        with BoundPreparedArchive(self.root,self.proof) as archive:
            with self.assertRaises(EnvelopeError):self.bind(archive)
        self.assertEqual(ArchiveDestination.objects.count(),0)
        RequestArchiveIntent.objects.update(state='pending')
        with BoundPreparedArchive(self.root,self.proof) as archive:self.bind(archive)
        with tempfile.TemporaryDirectory() as other:
            proof=initialize_destination(Path(other),uuid.uuid4())
            with BoundPreparedArchive(Path(other),proof) as archive:
                with self.assertRaises(EnvelopeError) as raised:self.bind(archive)
                self.assertEqual(str(raised.exception),'destination_conflict')
        RequestArchiveIntent.objects.update(state='held')
        with BoundPreparedArchive(self.root,self.proof) as archive:self.assertFalse(self.bind(archive).created)
        intent=RequestArchiveIntent.objects.get();self.assertEqual(intent.state,'held');self.assertEqual(intent.destination_id,self.proof.id)
        self.assertEqual(ArchiveDestination.objects.count(),1)

    def test_staff_exact_scope_and_post_io_revocation_preserve_unacknowledged_binding(self):
        self.authenticated();self.grant()
        request=self.browser.get('/staff/quotation-requests/').wsgi_request
        with BoundPreparedArchive(self.root,self.proof) as archive:
            with self.assertRaises(EnvelopeError):self.bind(archive,request)
            self.assertEqual(ArchiveDestination.objects.count(),0)
            self.enable_private(1)
            original=archive.attest;calls=0
            def revoke():
                nonlocal calls
                calls+=1
                if calls==2:StaffQuotationGrant.objects.filter(user=self.user).update(business_scope_version=0)
                return original()
            with patch.object(archive,'attest',revoke):
                with self.assertRaises(EnvelopeError):self.bind(archive,request)
            intent=RequestArchiveIntent.objects.get()
            self.assertEqual(intent.destination_id,self.proof.id);self.assertEqual(intent.destination_bound_by,self.user)
            self.assertEqual(intent.binding_staff_generation,self.credential.generation)
            self.assertIsNotNone(intent.binding_mfa_verified_at)
            self.enable_private(1);self.assertFalse(self.bind(archive,request).created)
        self.assertEqual([p.name for p in self.root.iterdir()],[MARKER])

    def test_outer_transaction_and_database_binding_constraints(self):
        with BoundPreparedArchive(self.root,self.proof) as archive:
            with patch.object(archive,'attest') as attestation:
                with transaction.atomic():
                    with self.assertRaises(EnvelopeError):self.bind(archive)
                attestation.assert_not_called()
            self.bind(archive)
        intent=RequestArchiveIntent.objects.get()
        for changes in ({'destination_bound_at':None},{'destination_id':None},{'binding_staff_generation':uuid.uuid4()}):
            with self.assertRaises(IntegrityError):
                with transaction.atomic():RequestArchiveIntent.objects.filter(pk=intent.pk).update(**changes)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():ArchiveDestination.objects.filter(pk=self.proof.id).update(profile='production')

    def test_competing_roots_bind_one_destination_without_orphan_rows(self):
        with tempfile.TemporaryDirectory() as other:
            other_proof=initialize_destination(Path(other),uuid.uuid4())
            with BoundPreparedArchive(self.root,self.proof) as first,BoundPreparedArchive(Path(other),other_proof) as second:
                requests=[self.owner_request(),self.owner_request()];barrier=Barrier(2)
                def run(index):
                    try:
                        barrier.wait(timeout=10)
                        try:return self.bind((first,second)[index],requests[index])
                        except EnvelopeError:return None
                    finally:connections.close_all()
                with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(run,range(2)))
        self.assertEqual(sum(result is not None for result in results),1)
        winner=next(result for result in results if result)
        self.assertEqual(RequestArchiveIntent.objects.get().destination_id,winner.destination_id)
        self.assertEqual(ArchiveDestination.objects.count(),1)
