"""Real PG commit/rollback with synthetic acknowledgement loss, no wire fault claim."""
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from time import monotonic,sleep
from unittest.mock import patch
import uuid
from django.db import connections,OperationalError,transaction
from django.test import TransactionTestCase,override_settings
from shop.access import staff_tests
from shop.adapters.archive_destination import BoundPreparedArchive
from . import archive_publication_tests as fixtures
from .archive_reconciliation import reconcile_archive_publication
from .models import ArchivePreparedVerification,ArchiveWorkClaim
from .request_envelope import EnvelopeError

@override_settings(**staff_tests.STAFF_SETTINGS)
class ArchiveReconciliationTests(TransactionTestCase):
    owner_context=fixtures.ArchivePublicationTests.owner_context
    owner_request=fixtures.ArchivePublicationTests.owner_request
    attach=fixtures.ArchivePublicationTests.attach
    business=fixtures.ArchivePublicationTests.business
    save_envelope=fixtures.ArchivePublicationTests.save_envelope
    post=fixtures.ArchivePublicationTests.post
    challenge=fixtures.ArchivePublicationTests.challenge
    authenticated=fixtures.ArchivePublicationTests.authenticated
    grant=fixtures.ArchivePublicationTests.grant
    enable_private=fixtures.ArchivePublicationTests.enable_private
    bind=fixtures.ArchivePublicationTests.bind
    authorize=fixtures.ArchivePublicationTests.authorize
    revoke=fixtures.ArchivePublicationTests.revoke
    claim=fixtures.ArchivePublicationTests.claim
    publish=fixtures.ArchivePublicationTests.publish
    setUp=fixtures.ArchivePublicationTests.setUp
    def reconcile(self,claim,request=None):
        return reconcile_archive_publication(request or self.owner_request(),self.intent.pk,claim.claim_id)

    def test_committed_verification_survives_lost_ack_reconnect_and_expired_work(self):
        reference=self.authorize();claim=self.claim(reference);db=connections['default'];original=db.commit;commits=0
        def lose_ack():
            nonlocal commits
            commits+=1;original()
            if commits==2:raise OperationalError('synthetic acknowledgement loss after actual commit')
        with BoundPreparedArchive(self.root,self.proof) as archive:
            with patch.object(db,'commit',lose_ack):
                with self.assertRaises(OperationalError):self.publish(claim,archive)
        self.assertEqual(commits,2);db.close()
        row=ArchivePreparedVerification.objects.get();retained=(row.pk,row.verified_at,row.claim_generation,row.authorization_generation)
        files={p.name:p.read_bytes() for p in self.root.iterdir()}
        self.revoke(reference);lease=ArchiveWorkClaim.objects.get()
        with patch('shop.catalog.archive_authority.db_now',return_value=lease.expires_at),patch.object(BoundPreparedArchive,'publish') as publication,patch.object(BoundPreparedArchive,'recover') as recovery,patch.object(BoundPreparedArchive,'attest') as attest:
            for _ in range(2):
                observed=self.reconcile(claim)
                self.assertEqual(observed.status,'verification_recorded');self.assertEqual(observed.verification_id,row.pk)
            publication.assert_not_called();recovery.assert_not_called();attest.assert_not_called()
        row.refresh_from_db();self.assertEqual((row.pk,row.verified_at,row.claim_generation,row.authorization_generation),retained)
        self.assertEqual(files,{p.name:p.read_bytes() for p in self.root.iterdir()})
        self.assertFalse(hasattr(observed,'token'));self.assertFalse(hasattr(observed,'sha256'));self.assertFalse(hasattr(observed,'can_retry'))

    def test_failed_commit_leaves_files_and_unverified_observation_without_retry_authority(self):
        claim=self.claim(self.authorize());db=connections['default'];original=db.commit;commits=0
        def fail_before_commit():
            nonlocal commits
            commits+=1
            if commits==2:raise OperationalError('synthetic failure before commit')
            original()
        with BoundPreparedArchive(self.root,self.proof) as archive:
            with patch.object(db,'commit',fail_before_commit):
                with self.assertRaises(OperationalError):self.publish(claim,archive)
        self.assertEqual(commits,2);db.close()
        self.assertEqual(ArchivePreparedVerification.objects.count(),0);self.assertEqual(len(list(self.root.iterdir())),3)
        with patch.object(BoundPreparedArchive,'publish') as publication:
            observed=self.reconcile(claim);self.assertEqual(observed.status,'verification_not_recorded')
            self.assertIsNone(observed.verification_id);publication.assert_not_called()
        self.assertEqual(ArchivePreparedVerification.objects.count(),0)

    def test_other_claim_and_current_scope_nesting_and_missing_claim_are_explicit(self):
        reference=self.authorize();old=self.claim(reference);lease=ArchiveWorkClaim.objects.get()
        with patch('shop.catalog.archive_authority.db_now',return_value=lease.expires_at):
            new=self.claim(reference)
            with BoundPreparedArchive(self.root,self.proof) as archive:verified=self.publish(new,archive)
        observed=self.reconcile(old);self.assertEqual(observed.status,'verification_recorded_by_other_claim')
        self.assertEqual(observed.verification_id,verified.verification_id)
        self.assertEqual(self.reconcile(new).status,'verification_recorded')
        request=self.owner_request();request.user=self.other
        with self.assertRaises(EnvelopeError):self.reconcile(old,request)
        with transaction.atomic():
            with self.assertRaises(EnvelopeError):self.reconcile(old)
        with self.assertRaises(EnvelopeError):reconcile_archive_publication(self.owner_request(),self.intent.pk,uuid.uuid4())
        self.assertEqual(ArchiveWorkClaim.objects.count(),2);self.assertEqual(ArchivePreparedVerification.objects.count(),1)

    def test_reconciliation_waits_for_actual_inflight_verification_commit(self):
        claim=self.claim(self.authorize());request=self.owner_request()
        inserted=Event();release=Event();reader_ready=Event();reader_pid={}
        original_create=ArchivePreparedVerification.objects.create
        def pause_insert(*args,**kwargs):
            row=original_create(*args,**kwargs);inserted.set()
            self.assertTrue(release.wait(timeout=10));return row
        with BoundPreparedArchive(self.root,self.proof) as archive:
            def publish():
                try:return self.publish(claim,archive)
                finally:connections.close_all()
            def observe():
                try:
                    with connections['default'].cursor() as cursor:
                        cursor.execute('SELECT pg_backend_pid()');reader_pid['value']=cursor.fetchone()[0]
                    reader_ready.set();return self.reconcile(claim,request)
                finally:connections.close_all()
            with patch.object(ArchivePreparedVerification.objects,'create',pause_insert),ThreadPoolExecutor(max_workers=2) as pool:
                publisher=pool.submit(publish);self.assertTrue(inserted.wait(timeout=10))
                reader=pool.submit(observe)
                try:
                    self.assertTrue(reader_ready.wait(timeout=10))
                    deadline=monotonic()+2;waiting=False
                    while monotonic()<deadline:
                        with connections['default'].cursor() as cursor:
                            cursor.execute('SELECT wait_event_type FROM pg_stat_activity WHERE pid=%s',[reader_pid['value']])
                            row=cursor.fetchone()
                        if row and row[0]=='Lock':waiting=True;break
                        sleep(0.01)
                    self.assertTrue(waiting,'reconciliation must block on the in-flight publication locks')
                    self.assertFalse(reader.done())
                finally:release.set()
                published=publisher.result(timeout=10);observed=reader.result(timeout=10)
        self.assertEqual(observed.status,'verification_recorded')
        self.assertEqual(observed.verification_id,published.verification_id)
        self.assertEqual(ArchivePreparedVerification.objects.count(),1)
