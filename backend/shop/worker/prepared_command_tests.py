"""Actual local Django command execution with safe output and fail-closed modes."""
from io import StringIO
import json
from unittest.mock import patch
import uuid
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection
from django.test import TransactionTestCase,override_settings
from shop.access import staff_tests
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
