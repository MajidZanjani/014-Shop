"""Owned synthetic prepared-job integration and real transaction boundaries."""
from pathlib import Path
import tempfile
from unittest.mock import patch
import uuid
from django.db import connection,transaction
from django.test import TransactionTestCase,override_settings
from shop.access import staff_tests
from shop.adapters.archive_destination import BoundPreparedArchive,initialize_destination
from shop.catalog import archive_reconciliation_tests as fixtures
from shop.catalog.archive_binding import bind_request_destination
from shop.catalog.archive_authority import authorize_request_archive,revoke_request_archive,inspect_active_authorization
from shop.catalog.archive_claim import claim_request_archive,inspect_archive_claim
from shop.catalog.archive_publication import publish_request_archive,inspect_prepared_verification
from shop.catalog.archive_reconciliation import reconcile_archive_publication
from shop.catalog.envelope_capture import capture_request_envelope
from shop.catalog.request_envelope import recover_request_envelope,EnvelopeError
from shop.catalog.models import ArchiveWorkClaim,ArchivePreparedVerification
from .models import Probe,FakeReceipt
from .prepared import execute_prepared_once

@override_settings(**staff_tests.STAFF_SETTINGS)
class PreparedWorkerTests(TransactionTestCase):
    owner_context=fixtures.ArchiveReconciliationTests.owner_context
    owner_request=fixtures.ArchiveReconciliationTests.owner_request
    attach=fixtures.ArchiveReconciliationTests.attach
    business=fixtures.ArchiveReconciliationTests.business
    save_envelope=fixtures.ArchiveReconciliationTests.save_envelope
    post=fixtures.ArchiveReconciliationTests.post
    challenge=fixtures.ArchiveReconciliationTests.challenge
    authenticated=fixtures.ArchiveReconciliationTests.authenticated
    grant=fixtures.ArchiveReconciliationTests.grant
    enable_private=fixtures.ArchiveReconciliationTests.enable_private
    bind=fixtures.ArchiveReconciliationTests.bind
    authorize=fixtures.ArchiveReconciliationTests.authorize
    revoke=fixtures.ArchiveReconciliationTests.revoke
    setUp=fixtures.ArchiveReconciliationTests.setUp

    def test_one_explicit_job_creates_only_prepared_verification_and_never_probe_effects(self):
        reference=self.authorize()
        with BoundPreparedArchive(self.root,self.proof) as archive,patch('shop.worker.services.perform_fake_probe') as bank,patch('shop.worker.services.CaptureMail') as mail:
            first=execute_prepared_once(reference.authorization_id,archive)
            self.assertTrue(first.created);self.assertFalse(hasattr(first,'token'))
            with self.assertRaises(EnvelopeError):execute_prepared_once(reference.authorization_id,archive)
            bank.assert_not_called();mail.assert_not_called()
        self.assertEqual(ArchiveWorkClaim.objects.count(),1);self.assertEqual(ArchivePreparedVerification.objects.count(),1)
        self.assertEqual(Probe.objects.count(),0);self.assertEqual(FakeReceipt.objects.count(),0)
        self.assertEqual(len(list(self.root.iterdir())),3)

    def test_wrong_root_and_live_mode_fail_before_claim_or_publication(self):
        reference=self.authorize()
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);proof=initialize_destination(root,self.proof.id)
            with BoundPreparedArchive(root,proof) as archive:
                with patch.object(archive,'publish') as publication:
                    with self.assertRaises(EnvelopeError):execute_prepared_once(reference.authorization_id,archive)
                    publication.assert_not_called()
        with BoundPreparedArchive(self.root,self.proof) as archive,patch.object(archive,'attest') as attest:
            with override_settings(SHOP_ENV='production'):
                with self.assertRaises(EnvelopeError):execute_prepared_once(reference.authorization_id,archive)
            with transaction.atomic():
                with self.assertRaises(EnvelopeError):execute_prepared_once(reference.authorization_id,archive)
            attest.assert_not_called()
        self.assertEqual(ArchiveWorkClaim.objects.count(),0)

    def test_revocation_during_one_shot_retains_files_and_does_not_retry(self):
        reference=self.authorize();request=self.owner_request()
        with BoundPreparedArchive(self.root,self.proof) as archive:
            original=archive.publish;calls=0
            def revoke(*args):
                nonlocal calls
                calls+=1;self.assertFalse(connection.in_atomic_block);self.assertTrue(connection.get_autocommit())
                result=original(*args);self.revoke(reference,request);return result
            with patch.object(archive,'publish',revoke):
                with self.assertRaises(EnvelopeError):execute_prepared_once(reference.authorization_id,archive)
        self.assertEqual(calls,1);self.assertEqual(ArchivePreparedVerification.objects.count(),0)
        self.assertEqual(ArchiveWorkClaim.objects.count(),1);self.assertEqual(len(list(self.root.iterdir())),3)

    def test_every_owned_archive_boundary_rejects_manual_autocommit_off_before_io(self):
        reference=self.authorize();request=self.owner_request();random=uuid.uuid4()
        with BoundPreparedArchive(self.root,self.proof) as archive:
            calls=[
                lambda:execute_prepared_once(reference.authorization_id,archive),
                lambda:bind_request_destination(request,self.quotation.pk,1,archive),
                lambda:capture_request_envelope(request,self.quotation.pk,1),
                lambda:authorize_request_archive(request,self.intent.pk,self.proof.id,random,1),
                lambda:revoke_request_archive(request,self.intent.pk,reference.authorization_id),
                lambda:inspect_active_authorization(reference.authorization_id,self.proof.id),
                lambda:claim_request_archive(reference.authorization_id,self.proof.id),
                lambda:inspect_archive_claim(random,random),
                lambda:publish_request_archive(random,random,archive),
                lambda:inspect_prepared_verification(request,self.intent.pk),
                lambda:reconcile_archive_publication(request,self.intent.pk,random),
                lambda:recover_request_envelope(request,self.quotation.pk,1,None,archive),
            ]
            with patch.object(archive,'attest') as attest:
                connection.set_autocommit(False)
                try:
                    for call in calls:
                        with self.assertRaises(EnvelopeError) as raised:call()
                        self.assertIn('transaction_active',str(raised.exception))
                finally:
                    connection.rollback();connection.set_autocommit(True)
                attest.assert_not_called()
        self.assertEqual(ArchiveWorkClaim.objects.count(),0);self.assertEqual(ArchivePreparedVerification.objects.count(),0)
        self.assertEqual(len(list(self.root.iterdir())),1)
