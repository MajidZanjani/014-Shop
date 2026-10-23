"""Real PostgreSQL explicit authorization/revocation; no detached execution."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from unittest.mock import patch
import uuid
from django.db import connections,transaction,IntegrityError
from django.test import TransactionTestCase,override_settings
from shop.access import staff_tests
from shop.access.models import StaffQuotationGrant
from shop.adapters.archive_destination import BoundPreparedArchive,MARKER
from . import archive_binding_tests as fixtures
from .archive_authority import authorize_request_archive,revoke_request_archive
from .models import RequestArchiveIntent,ArchiveWorkAuthorization,ArchiveWorkRevocation,RequestEnvelope
from .request_envelope import EnvelopeError

@override_settings(**staff_tests.STAFF_SETTINGS)
class ArchiveAuthorityTests(TransactionTestCase):
    owner_context=fixtures.ArchiveBindingTests.owner_context
    owner_request=fixtures.ArchiveBindingTests.owner_request
    attach=fixtures.ArchiveBindingTests.attach
    business=fixtures.ArchiveBindingTests.business
    save_envelope=fixtures.ArchiveBindingTests.save_envelope
    post=fixtures.ArchiveBindingTests.post
    challenge=fixtures.ArchiveBindingTests.challenge
    authenticated=fixtures.ArchiveBindingTests.authenticated
    grant=fixtures.ArchiveBindingTests.grant
    enable_private=fixtures.ArchiveBindingTests.enable_private
    bind=fixtures.ArchiveBindingTests.bind
    def setUp(self):
        fixtures.ArchiveBindingTests.setUp(self)
        with BoundPreparedArchive(self.root,self.proof) as archive:self.bind(archive)
        self.intent=RequestArchiveIntent.objects.get();self.command=uuid.uuid4()
    def authorize(self,request=None,generation=0,command=None):
        return authorize_request_archive(request or self.owner_request(),self.intent.pk,self.proof.id,command or self.command,generation)
    def revoke(self,reference,request=None):
        return revoke_request_archive(request or self.owner_request(),self.intent.pk,reference.authorization_id)

    def test_exact_retry_expiration_and_revocation_do_not_refresh_attribution(self):
        first=self.authorize();row=ArchiveWorkAuthorization.objects.get();issued=row.issued_at
        self.assertEqual(row.not_after-issued,timedelta(minutes=5));self.assertEqual(row.authorized_by,self.owner)
        self.assertIsNone(row.staff_generation);self.assertFalse(row.effects_authorized);self.assertFalse(row.retention_qualified)
        with patch('shop.catalog.archive_authority.db_now',return_value=row.not_after+timedelta(seconds=1)):
            self.assertFalse(self.authorize().created)
            self.assertTrue(self.revoke(first).created);self.assertFalse(self.revoke(first).created)
            self.assertFalse(self.authorize().created)
        row.refresh_from_db();self.assertEqual(row.issued_at,issued)
        self.assertEqual(ArchiveWorkRevocation.objects.count(),1)
        second=self.authorize(generation=1,command=uuid.uuid4());self.assertEqual(second.generation,2)
        self.assertEqual([p.name for p in self.root.iterdir()],[MARKER])

    def test_current_scope_required_and_wrong_root_payload_held_outer_transaction_denied(self):
        with self.assertRaises(EnvelopeError):authorize_request_archive(self.owner_request(),self.intent.pk,uuid.uuid4(),self.command,0)
        RequestArchiveIntent.objects.filter(pk=self.intent.pk).update(state='held')
        with self.assertRaises(EnvelopeError):self.authorize()
        RequestArchiveIntent.objects.filter(pk=self.intent.pk).update(state='pending')
        with transaction.atomic():
            with self.assertRaises(EnvelopeError):self.authorize()
        original=RequestEnvelope.objects.get().sha256
        RequestEnvelope.objects.update(sha256='0'*64)
        with self.assertRaises(EnvelopeError):self.authorize()
        RequestEnvelope.objects.update(sha256=original)
        request=self.owner_request();request.user=self.other
        with self.assertRaises(EnvelopeError):self.authorize(request)
        self.assertEqual(ArchiveWorkAuthorization.objects.count(),0)
        first=self.authorize();RequestArchiveIntent.objects.update(state='held')
        self.assertFalse(self.authorize().created);self.assertTrue(self.revoke(first).created)
        with self.assertRaises(EnvelopeError):self.authorize(generation=1,command=uuid.uuid4())
        self.assertEqual(RequestArchiveIntent.objects.get().state,'held')

    def test_staff_requires_current_exact_private_scope_for_issue_retry_revoke(self):
        self.authenticated();self.grant();request=self.browser.get('/staff/quotation-requests/').wsgi_request
        with self.assertRaises(EnvelopeError):self.authorize(request)
        self.enable_private(1);reference=self.authorize(request)
        row=ArchiveWorkAuthorization.objects.get();self.assertEqual(row.staff_generation,self.credential.generation)
        self.assertIsNotNone(row.mfa_verified_at)
        StaffQuotationGrant.objects.filter(user=self.user).delete()
        with self.assertRaises(EnvelopeError):self.authorize(request)
        with self.assertRaises(EnvelopeError):self.revoke(reference,request)
        # Owner can revoke staff-origin authority without impersonating staff.
        self.assertTrue(self.revoke(reference).created)
        row.refresh_from_db();self.assertEqual(row.authorized_by,self.user)

    def test_constraints_and_stale_generation_fail_closed(self):
        first=self.authorize()
        with self.assertRaises(EnvelopeError):self.authorize(command=uuid.uuid4())
        row=ArchiveWorkAuthorization.objects.get()
        for change in ({'effects_authorized':True},{'retention_qualified':True},{'generation':0},
            {'not_after':row.not_after+timedelta(seconds=1)},{'staff_generation':uuid.uuid4()}):
            with self.assertRaises(IntegrityError):
                with transaction.atomic():ArchiveWorkAuthorization.objects.filter(pk=row.pk).update(**change)
        self.revoke(first)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():ArchiveWorkRevocation.objects.update(reason='resume')

    def test_competing_commands_and_revoke_retry_serialize(self):
        requests=[self.owner_request(),self.owner_request()];barrier=Barrier(2)
        def issue(index):
            try:
                barrier.wait(timeout=10)
                try:return self.authorize(requests[index],command=uuid.uuid4())
                except EnvelopeError:return None
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(issue,range(2)))
        self.assertEqual(sum(item is not None for item in results),1)
        reference=next(item for item in results if item);barrier=Barrier(2)
        def revoke(index):
            try:
                barrier.wait(timeout=10);return self.revoke(reference,requests[index])
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(revoke,range(2)))
        self.assertEqual(sum(item.created for item in results),1);self.assertEqual(ArchiveWorkRevocation.objects.count(),1)
