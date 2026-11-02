"""Owned PostgreSQL recovery/replay components; no actual restore qualification."""
from pathlib import Path
import uuid

from django.db import connection
from django.test import TransactionTestCase, override_settings

from shop.access.models import AccessEpoch, LocalAccessRecoveryOperation
from shop.access.recovery import AccessRecoveryError, local_recovery_operation
from . import revision_tests


@override_settings(SHB_SYNTHETIC_FIXTURE=True)
class RecoveryTests(TransactionTestCase):
    client_class = revision_tests.RevisionTests.client_class
    setUp = revision_tests.RevisionTests.setUp
    post = revision_tests.RevisionTests.post
    challenge = revision_tests.RevisionTests.challenge
    authenticated = revision_tests.RevisionTests.authenticated
    customer_submit = revision_tests.RevisionTests.customer_submit
    submit = revision_tests.RevisionTests.submit
    issue = revision_tests.RevisionTests.issue
    offer = revision_tests.RevisionTests.offer
    customer_review = revision_tests.RevisionTests.customer_review
    accept_offer = revision_tests.RevisionTests.accept_offer
    pay = revision_tests.RevisionTests.pay
    withdraw = revision_tests.RevisionTests.withdraw
    revised = revision_tests.RevisionTests.revised

    def operation(self, action='quarantine', *, request_id=None, basis=None):
        return local_recovery_operation(action=action, request_id=request_id or uuid.uuid4(),
            expected_database=connection.settings_dict['NAME'], basis_reset=basis)

    def test_release_refuses_missing_ordinary_capture_archive_without_clearing_hold(self):
        from . import transaction_mail
        from .models import TransactionNoticeCapture
        self.assertTrue(transaction_mail.execute_once())
        capture = TransactionNoticeCapture.objects.get()
        (Path(self.directory.name) / ('blob-' + capture.sha256)).unlink()
        reset = uuid.uuid4()
        self.operation(request_id=reset)
        epoch = AccessEpoch.objects.get().value
        with self.assertRaisesMessage(AccessRecoveryError, 'shb_recovery_evidence_required'):
            self.operation('release', basis=reset)
        self.assertTrue(AccessEpoch.objects.get().quarantined)
        self.assertEqual(AccessEpoch.objects.get().value, epoch)
        self.assertEqual(LocalAccessRecoveryOperation.objects.count(), 1)
