"""Owned-root publication and PostgreSQL fencing; no domain completion."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event,Barrier,Lock
from unittest.mock import patch
import tempfile
import uuid
from django.db import connection,connections,transaction,IntegrityError
from django.test import TransactionTestCase,override_settings
from shop.access import staff_tests
from shop.access.models import StaffQuotationGrant
from shop.adapters.archive_destination import BoundPreparedArchive,initialize_destination,MARKER
from shop.adapters.evidence_archive import ArchiveError,PreparedReceipt
from . import archive_claim_tests as fixtures
from .archive_publication import publish_request_archive,inspect_prepared_verification
from .models import ArchivePreparedVerification,ArchiveWorkClaim,RequestArchiveIntent
from .request_envelope import EnvelopeError

@override_settings(**staff_tests.STAFF_SETTINGS)
class ArchivePublicationTests(TransactionTestCase):
    owner_context=fixtures.ArchiveClaimTests.owner_context
    owner_request=fixtures.ArchiveClaimTests.owner_request
    attach=fixtures.ArchiveClaimTests.attach
    business=fixtures.ArchiveClaimTests.business
    save_envelope=fixtures.ArchiveClaimTests.save_envelope
    post=fixtures.ArchiveClaimTests.post
    challenge=fixtures.ArchiveClaimTests.challenge
    authenticated=fixtures.ArchiveClaimTests.authenticated
    grant=fixtures.ArchiveClaimTests.grant
    enable_private=fixtures.ArchiveClaimTests.enable_private
    bind=fixtures.ArchiveClaimTests.bind
    authorize=fixtures.ArchiveClaimTests.authorize
    revoke=fixtures.ArchiveClaimTests.revoke
    claim=fixtures.ArchiveClaimTests.claim
    setUp=fixtures.ArchiveClaimTests.setUp
    def publish(self,claim,archive):return publish_request_archive(claim.claim_id,claim.token,archive)

    def test_publish_reopen_no_transaction_io_exact_replay_and_historical_permissions(self):
        reference=self.authorize();claim=self.claim(reference)
        with BoundPreparedArchive(self.root,self.proof) as archive:
            original_publish=archive.publish;original_attest=archive.attest;original_recover=BoundPreparedArchive.recover
            def publish(*args):self.assertFalse(connection.in_atomic_block);return original_publish(*args)
            def attest():self.assertFalse(connection.in_atomic_block);return original_attest()
            def recover(other,*args):
                self.assertIsNot(other,archive);self.assertFalse(connection.in_atomic_block);return original_recover(other,*args)
            with patch.object(archive,'publish',publish),patch.object(archive,'attest',attest),patch.object(BoundPreparedArchive,'recover',recover):
                first=self.publish(claim,archive);self.assertTrue(first.created)
                self.assertFalse(self.publish(claim,archive).created)
        row=ArchivePreparedVerification.objects.get();observed=row.verified_at
        self.assertEqual(row.claim_id,claim.claim_id);self.assertEqual(row.evidence_id,self.captured.envelope_id)
        self.assertFalse(row.effects_authorized);self.assertFalse(row.retention_qualified)
        self.assertFalse(hasattr(first,'sha256'));self.assertEqual(len(list(self.root.iterdir())),3)
        with self.assertRaises(EnvelopeError):self.claim(reference)
        with self.assertRaises(EnvelopeError):self.authorize(generation=1,command=uuid.uuid4())
        self.assertFalse(self.authorize().created)
        self.revoke(reference)
        self.assertEqual(inspect_prepared_verification(self.owner_request(),self.intent.pk).verification_id,first.verification_id)
        request=self.owner_request();request.user=self.other
        with self.assertRaises(EnvelopeError):inspect_prepared_verification(request,self.intent.pk)
        row.refresh_from_db();self.assertEqual(row.verified_at,observed)

    def test_wrong_root_receipt_and_marker_fail_closed_without_verification(self):
        reference=self.authorize();claim=self.claim(reference)
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);proof=initialize_destination(root,uuid.uuid4())
            with BoundPreparedArchive(root,proof) as archive:
                with patch.object(archive,'publish') as publication:
                    with self.assertRaises(EnvelopeError):self.publish(claim,archive)
                    publication.assert_not_called()
        with BoundPreparedArchive(self.root,self.proof) as archive:
            original=archive.publish
            def wrong(*args):
                receipt=original(*args);return PreparedReceipt(uuid.uuid4(),receipt.sha256,receipt.size)
            with patch.object(archive,'publish',wrong):
                with self.assertRaises(EnvelopeError):self.publish(claim,archive)
            marker=(self.root/MARKER).read_bytes()
            def changed(*args):
                receipt=original(*args);(self.root/MARKER).write_bytes(b'changed');return receipt
            with patch.object(archive,'publish',changed):
                with self.assertRaises(EnvelopeError):self.publish(claim,archive)
            (self.root/MARKER).write_bytes(marker)
        self.assertEqual(ArchivePreparedVerification.objects.count(),0);self.assertEqual(len(list(self.root.iterdir())),3)

    def test_lost_storage_ack_and_database_rollback_reconcile_exact_files(self):
        claim=self.claim(self.authorize())
        with BoundPreparedArchive(self.root,self.proof) as archive:
            original=archive.publish
            def lost(*args):original(*args);raise ArchiveError('archive_unavailable')
            with patch.object(archive,'publish',lost):
                with self.assertRaises(EnvelopeError):self.publish(claim,archive)
            self.assertEqual(ArchivePreparedVerification.objects.count(),0);files={p.name:p.read_bytes() for p in self.root.iterdir()}
            with patch.object(ArchivePreparedVerification.objects,'create',side_effect=IntegrityError('synthetic commit failure')):
                with self.assertRaises(IntegrityError):self.publish(claim,archive)
            self.assertEqual(ArchivePreparedVerification.objects.count(),0)
            self.assertTrue(self.publish(claim,archive).created)
            self.assertEqual(files,{p.name:p.read_bytes() for p in self.root.iterdir()})
            self.assertFalse(self.publish(claim,archive).created)

    def test_private_staff_revocation_during_io_retains_files_without_verification(self):
        self.authenticated();self.grant();self.enable_private(1)
        request=self.browser.get('/staff/quotation-requests/').wsgi_request
        reference=self.authorize(request);claim=self.claim(reference)
        with BoundPreparedArchive(self.root,self.proof) as archive:
            original=archive.publish
            def revoke(*args):
                receipt=original(*args)
                StaffQuotationGrant.objects.filter(user=self.user).update(business_scope_version=0)
                return receipt
            with patch.object(archive,'publish',revoke):
                with self.assertRaises(EnvelopeError):self.publish(claim,archive)
        self.assertEqual(ArchivePreparedVerification.objects.count(),0);self.assertEqual(len(list(self.root.iterdir())),3)

    def test_reclaim_while_old_publisher_paused_fences_completion_and_keeps_new_result(self):
        reference=self.authorize();old=self.claim(reference);lease=ArchiveWorkClaim.objects.get()
        published=Event();resume=Event()
        with BoundPreparedArchive(self.root,self.proof) as archive:
            original=archive.publish
            def paused(*args):
                receipt=original(*args);published.set();self.assertTrue(resume.wait(timeout=10));return receipt
            def run():
                try:
                    with patch.object(archive,'publish',paused):
                        try:return self.publish(old,archive)
                        except EnvelopeError:return None
                finally:connections.close_all()
            with ThreadPoolExecutor(max_workers=1) as pool:
                future=pool.submit(run);self.assertTrue(published.wait(timeout=10))
                with patch('shop.catalog.archive_authority.db_now',return_value=lease.expires_at):
                    new=self.claim(reference)
                    with BoundPreparedArchive(self.root,self.proof) as other:self.assertTrue(self.publish(new,other).created)
                    resume.set();self.assertIsNone(future.result(timeout=10))
        self.assertEqual(ArchivePreparedVerification.objects.count(),1)
        self.assertEqual(ArchivePreparedVerification.objects.get().claim_id,new.claim_id)
        self.assertEqual(ArchiveWorkClaim.objects.count(),2);self.assertEqual(len(list(self.root.iterdir())),3)

    def test_nesting_and_no_effect_constraints(self):
        claim=self.claim(self.authorize())
        with BoundPreparedArchive(self.root,self.proof) as archive:
            with transaction.atomic():
                with patch.object(archive,'attest') as attestation:
                    with self.assertRaises(EnvelopeError):self.publish(claim,archive)
                    attestation.assert_not_called()
            self.publish(claim,archive)
        row=ArchivePreparedVerification.objects.get()
        for values in ({'effects_authorized':True},{'retention_qualified':True},{'claim_generation':0},{'evidence_kind':'completed'}):
            with self.assertRaises(IntegrityError):
                with transaction.atomic():ArchivePreparedVerification.objects.filter(pk=row.pk).update(**values)
        self.assertEqual(RequestArchiveIntent.objects.get().state,'pending')

    def test_same_claim_publishers_race_to_one_original_verification(self):
        claim=self.claim(self.authorize());ready=Barrier(2);io=Lock()
        original_publish=BoundPreparedArchive.publish;original_attest=BoundPreparedArchive.attest;original_recover=BoundPreparedArchive.recover
        def serialized_publish(archive,*args):
            self.assertFalse(connection.in_atomic_block)
            with io:return original_publish(archive,*args)
        def serialized_attest(archive):
            self.assertFalse(connection.in_atomic_block)
            with io:return original_attest(archive)
        def readback_then_race(archive,*args):
            self.assertFalse(connection.in_atomic_block)
            with io:raw=original_recover(archive,*args)
            # Both completed physical readback before either completion transaction.
            ready.wait(timeout=10);return raw
        with BoundPreparedArchive(self.root,self.proof) as first,BoundPreparedArchive(self.root,self.proof) as second:
            def run(index):
                try:return self.publish(claim,(first,second)[index])
                finally:connections.close_all()
            with patch.object(BoundPreparedArchive,'publish',serialized_publish),patch.object(BoundPreparedArchive,'attest',serialized_attest),patch.object(BoundPreparedArchive,'recover',readback_then_race):
                with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(run,range(2)))
        self.assertEqual(sum(result.created for result in results),1)
        self.assertEqual(results[0].verification_id,results[1].verification_id)
        self.assertEqual(ArchivePreparedVerification.objects.count(),1)
        self.assertEqual(ArchivePreparedVerification.objects.get().claim_id,claim.claim_id)
        self.assertEqual(ArchiveWorkClaim.objects.count(),1);self.assertEqual(len(list(self.root.iterdir())),3)

    def test_busy_archive_and_corrupt_readback_retain_files_and_deny_verification(self):
        claim=self.claim(self.authorize())
        with BoundPreparedArchive(self.root,self.proof) as archive,BoundPreparedArchive(self.root,self.proof) as busy:
            with busy.operation():
                with self.assertRaises(EnvelopeError):self.publish(claim,archive)
            self.assertEqual([p.name for p in self.root.iterdir()],[MARKER])
            original=archive.publish;retained={}
            def corrupt(*args):
                receipt=original(*args);blob=self.root/('blob-'+receipt.sha256)
                retained['blob']=blob;retained['bytes']=blob.read_bytes();blob.write_bytes(b'corrupt')
                return receipt
            with patch.object(archive,'publish',corrupt):
                with self.assertRaises(EnvelopeError):self.publish(claim,archive)
            self.assertEqual(ArchivePreparedVerification.objects.count(),0)
            self.assertEqual(len(list(self.root.iterdir())),3)
            self.assertEqual(retained['blob'].read_bytes(),b'corrupt')
            # Test fixture restores exact bytes; runtime never repairs/deletes uncertain data.
            retained['blob'].write_bytes(retained['bytes'])
            self.assertTrue(self.publish(claim,archive).created)
