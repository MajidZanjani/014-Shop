"""Actual local Django command execution with safe output and fail-closed modes."""
from io import StringIO
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch
import uuid
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection,transaction
from django.test import TransactionTestCase,override_settings
from shop.access import staff_tests
from shop.adapters.archive_destination import BoundPreparedArchive,MARKER,initialize_destination
from shop.catalog.models import ArchivePreparedVerification,ArchiveWorkClaim
from . import prepared_tests as fixtures

@override_settings(**staff_tests.STAFF_SETTINGS)
class PreparedCommandTests(TransactionTestCase):
    owner_context=fixtures.PreparedWorkerTests.owner_context
    owner_request=fixtures.PreparedWorkerTests.owner_request
    attach=fixtures.PreparedWorkerTests.attach
    business=fixtures.PreparedWorkerTests.business
    save_envelope=fixtures.PreparedWorkerTests.save_envelope
    post=fixtures.PreparedWorkerTests.post
    challenge=fixtures.PreparedWorkerTests.challenge
    authenticated=fixtures.PreparedWorkerTests.authenticated
    grant=fixtures.PreparedWorkerTests.grant
    enable_private=fixtures.PreparedWorkerTests.enable_private
    bind=fixtures.PreparedWorkerTests.bind
    authorize=fixtures.PreparedWorkerTests.authorize
    revoke=fixtures.PreparedWorkerTests.revoke
    setUp=fixtures.PreparedWorkerTests.setUp
    def run_command(self,reference,**changes):
        output=StringIO();options={'authorization':str(reference.authorization_id),'destination':str(self.proof.id),'root':str(self.root)}
        options.update(changes)
        call_command('run_prepared_archive',stdout=output,stderr=StringIO(),**options)
        return output.getvalue()

    def test_success_outputs_only_fixed_safe_fields_and_duplicate_never_republishes(self):
        reference=self.authorize();output=self.run_command(reference)
        self.assertEqual(json.loads(output),{'status':'local_prepared_verified','created':True,'retention_qualified':False,'effects_authorized':False})
        for value in (str(self.root),str(self.proof.id),str(reference.authorization_id),str(ArchiveWorkClaim.objects.get().token)):
            self.assertNotIn(value,output)
        with self.assertRaisesMessage(CommandError,'Local prepared archive job unavailable'):self.run_command(reference)
        self.assertEqual(ArchiveWorkClaim.objects.count(),1);self.assertEqual(ArchivePreparedVerification.objects.count(),1)
        self.assertEqual(len(list(self.root.iterdir())),3)

    def test_bad_ids_missing_root_revocation_and_live_mode_are_fixed_errors(self):
        reference=self.authorize()
        for changes in ({'authorization':'private-invalid-value'},{'destination':str(uuid.uuid4())},{'root':str(self.root/'missing')}):
            with self.assertRaisesMessage(CommandError,'Local prepared archive job unavailable') as raised:self.run_command(reference,**changes)
            self.assertEqual(str(raised.exception),'Local prepared archive job unavailable')
        self.assertFalse((self.root/'missing').exists())
        with override_settings(SHOP_ENV='production'):
            with self.assertRaisesMessage(CommandError,'Local prepared archive job unavailable'):self.run_command(reference)
        self.revoke(reference)
        with self.assertRaisesMessage(CommandError,'Local prepared archive job unavailable'):self.run_command(reference)
        self.assertEqual(ArchiveWorkClaim.objects.count(),0);self.assertEqual(len(list(self.root.iterdir())),1)

    def test_manual_transaction_denied_before_opening_archive(self):
        reference=self.authorize()
        with patch('shop.worker.management.commands.run_prepared_archive.BoundPreparedArchive') as archive:
            connection.set_autocommit(False)
            try:
                with self.assertRaisesMessage(CommandError,'Local prepared archive job unavailable'):self.run_command(reference)
            finally:
                connection.rollback();connection.set_autocommit(True)
            archive.assert_not_called()
        self.assertEqual(ArchiveWorkClaim.objects.count(),0)

    def run_child(self,reference,**changes):
        # Only frozen runtime tool/library paths are inherited (libpq discovery). No provider,
        # credential, libpq-service or application configuration is inherited.
        env={key:os.environ[key] for key in ('PATH','LD_LIBRARY_PATH') if key in os.environ}
        env.update(DJANGO_SETTINGS_MODULE='shop.config.synthetic',SHOP_ENV='synthetic',
            LIVE_PAYMENTS_ENABLED='false',PAYMENT_ADAPTER='fake',MAIL_ADAPTER='fake',
            STORAGE_ADAPTER='fake',PSYCOPG_IMPL='python',PYTHONDONTWRITEBYTECODE='1',NO_COLOR='1')
        for key in ('NAME','USER','HOST','PORT'):
            env['DATABASE_'+key]=str(connection.settings_dict[key])
        options={'authorization':str(reference.authorization_id),'destination':str(self.proof.id),'root':str(self.root)}
        options.update(changes)
        backend=Path(__file__).resolve().parents[2]
        argv=[sys.executable,str(backend/'manage.py'),'run_prepared_archive']
        for key,value in options.items():argv.extend(('--'+key,value))
        # subprocess.run kills and waits for this single child on timeout.
        # No shell, daemon, child process tree or automatic retry is involved.
        return subprocess.run(argv,cwd=backend,env=env,capture_output=True,text=True,timeout=15)

    def assert_child_unavailable(self,result):
        self.assertEqual(result.returncode,1)
        self.assertEqual(result.stdout,'')
        self.assertEqual(result.stderr,'CommandError: Local prepared archive job unavailable\n')

    def test_separate_process_commits_verification_and_duplicate_preserves_exact_files(self):
        reference=self.authorize();result=self.run_child(reference)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(result.stderr,'')
        self.assertEqual(result.stdout,'{"created":true,"effects_authorized":false,"retention_qualified":false,"status":"local_prepared_verified"}\n')
        verification=ArchivePreparedVerification.objects.get()
        claim=ArchiveWorkClaim.objects.get()
        files={p.name:p.read_bytes() for p in self.root.iterdir()}
        self.assertEqual(len(files),3)
        self.assert_child_unavailable(self.run_child(reference))
        self.assertEqual(ArchivePreparedVerification.objects.get().pk,verification.pk)
        self.assertEqual(ArchiveWorkClaim.objects.get().pk,claim.pk)
        self.assertEqual({p.name:p.read_bytes() for p in self.root.iterdir()},files)

    def test_separate_process_bad_scope_missing_root_and_revocation_have_no_effects(self):
        reference=self.authorize();files={p.name:p.read_bytes() for p in self.root.iterdir()}
        for changes in ({'authorization':'private-invalid-value'},
                        {'destination':str(uuid.uuid4())},{'root':str(self.root/'missing')}):
            with self.subTest(changes=tuple(changes)):
                self.assert_child_unavailable(self.run_child(reference,**changes))
        self.revoke(reference)
        self.assert_child_unavailable(self.run_child(reference))
        self.assertEqual(ArchiveWorkClaim.objects.count(),0)
        self.assertEqual(ArchivePreparedVerification.objects.count(),0)
        self.assertEqual({p.name:p.read_bytes() for p in self.root.iterdir()},files)

    def test_separate_process_busy_root_fails_before_claim_and_does_not_retry(self):
        reference=self.authorize();files={p.name:p.read_bytes() for p in self.root.iterdir()}
        with BoundPreparedArchive(self.root,self.proof) as archive:
            with archive.operation():
                self.assert_child_unavailable(self.run_child(reference))
                self.assertEqual(ArchiveWorkClaim.objects.count(),0)
                self.assertEqual(ArchivePreparedVerification.objects.count(),0)
                self.assertEqual({p.name:p.read_bytes() for p in self.root.iterdir()},files)
        # Releasing the lock cannot itself cause work: the child already exited.
        self.assertEqual(ArchiveWorkClaim.objects.count(),0)
        self.assertEqual(ArchivePreparedVerification.objects.count(),0)
        self.assertEqual({p.name:p.read_bytes() for p in self.root.iterdir()},files)

    def test_separate_process_tampered_marker_is_never_repaired_or_adopted(self):
        reference=self.authorize();marker=self.root/MARKER;original=marker.read_bytes()
        marker.write_bytes(b'private-tampered-marker')
        files={p.name:p.read_bytes() for p in self.root.iterdir()}
        try:
            self.assert_child_unavailable(self.run_child(reference))
            self.assertEqual(ArchiveWorkClaim.objects.count(),0)
            self.assertEqual(ArchivePreparedVerification.objects.count(),0)
            self.assertEqual({p.name:p.read_bytes() for p in self.root.iterdir()},files)
        finally:
            # Only the test repairs its own fixture after observing refusal.
            marker.write_bytes(original)

    def test_separate_process_database_lock_timeout_rolls_back_without_archive_effects(self):
        reference=self.authorize();files={p.name:p.read_bytes() for p in self.root.iterdir()}
        with transaction.atomic():
            type(self.owner).objects.select_for_update().get(pk=self.owner.pk)
            # The child uses its own DB connection and the configured one-second
            # statement timeout. This is normal lock contention, never an outage.
            self.assert_child_unavailable(self.run_child(reference))
            self.assertEqual(ArchiveWorkClaim.objects.count(),0)
            self.assertEqual(ArchivePreparedVerification.objects.count(),0)
        self.assertEqual(ArchiveWorkClaim.objects.count(),0)
        self.assertEqual(ArchivePreparedVerification.objects.count(),0)
        self.assertEqual({p.name:p.read_bytes() for p in self.root.iterdir()},files)

    def test_separate_process_same_destination_uuid_cannot_adopt_different_physical_root(self):
        reference=self.authorize();files={p.name:p.read_bytes() for p in self.root.iterdir()}
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            replacement=initialize_destination(root,self.proof.id)
            self.assertNotEqual((replacement.device,replacement.inode),(self.proof.device,self.proof.inode))
            other_files={p.name:p.read_bytes() for p in root.iterdir()}
            self.assert_child_unavailable(self.run_child(reference,root=str(root)))
            self.assertEqual({p.name:p.read_bytes() for p in root.iterdir()},other_files)
        self.assertEqual(ArchiveWorkClaim.objects.count(),0)
        self.assertEqual(ArchivePreparedVerification.objects.count(),0)
        self.assertEqual({p.name:p.read_bytes() for p in self.root.iterdir()},files)
