"""Synthetic dispatch arbitration on owned PostgreSQL; no financial proof."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Barrier
from unittest.mock import patch
import uuid
from django.db import connections,transaction
from django.test import TransactionTestCase,override_settings
from shop.adapters.evidence_archive import PreparedArchive,ArchiveError
from . import attempts,synthetic_bank
from .bank_contract import BankStart,BankError
from .models import SyntheticPaymentAttempt,SyntheticBankOperation


class SyntheticAttemptTests(TransactionTestCase):
    def setUp(self):
        self.directory=TemporaryDirectory();self.addCleanup(self.directory.cleanup)
        self.archive=PreparedArchive(Path(self.directory.name));self.addCleanup(self.archive.__exit__,None,None,None)
        self.request=BankStart('synthetic-attempt',uuid.uuid4(),uuid.uuid4(),'EUR',123)
        self.row=attempts.prepare(self.request)

    def test_replay_is_exact_and_no_key_alias_can_create_another_attempt(self):
        self.assertEqual(attempts.prepare(self.request).pk,self.row.pk)
        for request in (replace(self.request,amount_minor=124),replace(self.request,idempotency_key=uuid.uuid4()),
                        replace(self.request,reference=uuid.uuid4())):
            with self.assertRaisesRegex(BankError,'synthetic_attempt_conflict'):attempts.prepare(request)
        self.assertEqual(SyntheticPaymentAttempt.objects.count(),1)
        self.assertEqual(SyntheticBankOperation.objects.count(),0)

    def test_retention_precedes_bank_and_observation_never_confirms_payment(self):
        original=synthetic_bank.start
        def send(request,**kwargs):
            current=SyntheticPaymentAttempt.objects.get(pk=self.row.pk)
            self.assertEqual(current.state,'uncertain');attempts.retained(current,self.archive)
            return original(request,**kwargs)
        with patch.object(synthetic_bank,'start',side_effect=send) as start:
            result=attempts.dispatch(self.row.pk,self.archive,outcome='authorized')
            replay=attempts.dispatch(self.row.pk,self.archive)
        self.assertEqual(start.call_count,1);self.assertEqual(replay.state,'observed')
        self.assertEqual(result.provider_status,'authorized');self.assertFalse(result.financial_confirmation)
        self.assertFalse(result.effects_authorized);self.assertEqual(result.evidence_class,'local-synthetic')
        self.assertFalse(result.archive_receipt['retention_qualified'])

    def test_archive_failure_cannot_claim_or_send(self):
        with patch.object(self.archive,'publish',side_effect=ArchiveError('archive_unavailable')):
            with patch.object(synthetic_bank,'start') as start:
                with self.assertRaises(ArchiveError):attempts.dispatch(self.row.pk,self.archive)
                start.assert_not_called()
        self.row.refresh_from_db();self.assertEqual(self.row.state,'prepared');self.assertEqual(self.row.archive_receipt,{})
        self.assertEqual(SyntheticBankOperation.objects.count(),0)

    def test_lost_response_reconciles_across_connection_without_second_send(self):
        with self.assertRaises(TimeoutError):attempts.dispatch(self.row.pk,self.archive,fault='after_commit')
        connections.close_all()
        with patch.object(synthetic_bank,'start',side_effect=AssertionError('blind retry')):
            uncertain=attempts.dispatch(self.row.pk,self.archive)
            self.assertEqual(uncertain.state,'uncertain')
            observed=attempts.reconcile(self.row.pk,self.archive)
            again=attempts.reconcile(self.row.pk,self.archive)
        self.assertEqual(observed.state,'observed');self.assertEqual(observed.provider_status,'captured')
        self.assertEqual(observed.provider_operation_id,again.provider_operation_id)
        self.assertEqual(SyntheticBankOperation.objects.count(),1)

    def test_no_operation_after_timeout_stays_uncertain_without_retry_permission(self):
        with self.assertRaises(TimeoutError):attempts.dispatch(self.row.pk,self.archive,fault='before_commit')
        with patch.object(synthetic_bank,'start',side_effect=AssertionError('blind retry')):
            self.assertEqual(attempts.reconcile(self.row.pk,self.archive).state,'uncertain')
            self.assertEqual(attempts.dispatch(self.row.pk,self.archive).state,'uncertain')
        self.assertEqual(SyntheticBankOperation.objects.count(),0)

    def test_reconciliation_rejects_mismatch_and_requires_recoverable_retained_bytes(self):
        with self.assertRaises(TimeoutError):attempts.dispatch(self.row.pk,self.archive,fault='after_commit')
        observation=synthetic_bank.lookup(self.request.merchant,self.request.reference)
        with patch.object(synthetic_bank,'lookup',return_value=replace(observation,amount_minor=124)):
            with self.assertRaisesRegex(BankError,'synthetic_observation_mismatch'):attempts.reconcile(self.row.pk,self.archive)
        with patch.object(self.archive,'recover',side_effect=ArchiveError('archive_unavailable')):
            with patch.object(synthetic_bank,'lookup') as lookup:
                with self.assertRaises(ArchiveError):attempts.reconcile(self.row.pk,self.archive)
                lookup.assert_not_called()
        self.row.refresh_from_db();self.assertEqual(self.row.state,'uncertain')

    def test_two_dispatchers_commit_only_one_send_claim(self):
        barrier=Barrier(2);original=PreparedArchive.recover
        def recover(archive,receipt):
            value=original(archive,receipt);barrier.wait(timeout=10);return value
        # Separate roots avoid sharing the archive's intentionally nonblocking lock.
        second=TemporaryDirectory();self.addCleanup(second.cleanup)
        def dispatch(directory):
            try:
                with PreparedArchive(Path(directory)) as archive:return attempts.dispatch(self.row.pk,archive).state
            finally:connections.close_all()
        with patch.object(PreparedArchive,'recover',recover):
            with patch.object(synthetic_bank,'start',wraps=synthetic_bank.start) as start:
                with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(dispatch,[self.directory.name,second.name]))
        self.assertEqual(start.call_count,1);self.assertIn('observed',results)
        self.assertEqual(SyntheticBankOperation.objects.count(),1)

    def test_guards_prevent_live_or_transactional_archive_and_bank_io(self):
        for settings in ({'LIVE_PAYMENTS_ENABLED':True},{'SHOP_ENV':'production'},{'PAYMENT_ADAPTER':'real'}):
            with override_settings(**settings):
                with patch.object(self.archive,'publish') as publish:
                    with self.assertRaises(BankError):attempts.dispatch(self.row.pk,self.archive)
                    publish.assert_not_called()
        with transaction.atomic():
            with self.assertRaisesRegex(BankError,'bank_transaction_active'):attempts.dispatch(self.row.pk,self.archive)
        with self.assertRaisesRegex(BankError,'synthetic_attempt_not_dispatched'):attempts.reconcile(self.row.pk,self.archive)
