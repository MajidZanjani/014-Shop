"""Synthetic dispatch arbitration on owned PostgreSQL; no financial proof."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime,timedelta,timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Barrier,Event,local
from unittest.mock import patch
import uuid
from django.db import connection,connections,transaction,IntegrityError
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
        barrier=Barrier(2);original=PreparedArchive.recover;synchronized=local()
        def recover(archive,receipt):
            value=original(archive,receipt)
            # Synchronize the initial pre-claim read only; journal verification adds later reads.
            if not getattr(synchronized,"done",False):
                synchronized.done=True;barrier.wait(timeout=10)
            return value
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


    def dated(self,deadline):
        request=replace(self.request,reference=uuid.uuid4(),idempotency_key=uuid.uuid4())
        return attempts.prepare(request,expires_at=deadline)

    def test_deadline_exact_replay_validation_and_canonical_archive_binding(self):
        deadline=datetime.now(timezone.utc)+timedelta(hours=1)
        row=self.dated(deadline);request=attempts.request_for(row)
        self.assertEqual(attempts.prepare(request,expires_at=deadline).pk,row.pk)
        for value in (None,deadline+timedelta(seconds=1)):
            with self.assertRaisesRegex(BankError,'synthetic_attempt_conflict'):
                attempts.prepare(request,expires_at=value)
        for value in (datetime(2026,1,1),'tomorrow',True):
            with self.assertRaisesRegex(BankError,'invalid_synthetic_deadline'):
                attempts.prepare(request,expires_at=value)
        attempts.dispatch(row.pk,self.archive);row.refresh_from_db()
        self.assertIn(deadline.isoformat().encode(),attempts.payload(row))
        attempts.retained(row,self.archive)
        row.expires_at+=timedelta(seconds=1)
        with self.assertRaisesRegex(BankError,'synthetic_archive_mismatch'):attempts.retained(row,self.archive)
        self.assertNotIn(b'expires_at',attempts.payload(self.row))

    def test_cancellation_is_terminal_idempotent_and_cannot_record_or_lookup(self):
        stopped=attempts.cancel(self.row.pk)
        self.assertEqual(stopped.state,'cancelled');self.assertIsNotNone(stopped.stopped_at)
        self.assertEqual(attempts.cancel(self.row.pk).stopped_at,stopped.stopped_at)
        self.assertEqual(attempts.prepare(self.request).state,'cancelled')
        observation=synthetic_bank.observe(SyntheticBankOperation(id=uuid.uuid4(),merchant=self.request.merchant,
            reference=self.request.reference,currency='EUR',amount_minor=123,status='captured'))
        with patch.object(self.archive,'publish') as publish,patch.object(synthetic_bank,'lookup') as lookup:
            self.assertEqual(attempts.dispatch(self.row.pk,self.archive).state,'cancelled')
            with self.assertRaisesRegex(BankError,'synthetic_attempt_not_dispatched'):
                attempts.reconcile(self.row.pk,self.archive)
            with self.assertRaisesRegex(BankError,'synthetic_attempt_not_dispatched'):
                attempts._record(self.row.pk,observation)
            publish.assert_not_called();lookup.assert_not_called()
        self.assertEqual(SyntheticBankOperation.objects.count(),0)

    def test_due_expiry_is_terminal_and_inspection_does_not_persist_it(self):
        row=self.dated(datetime.now(timezone.utc)-timedelta(seconds=1))
        before=SyntheticPaymentAttempt.objects.get(pk=row.pk).__dict__.copy()
        with patch.object(synthetic_bank,'lookup') as lookup,patch.object(PreparedArchive,'recover') as recover:
            report=attempts.inspect(row.pk)
            self.assertEqual(report.state,'prepared');self.assertTrue(report.expiry_due)
            self.assertFalse(report.lookup_required);self.assertFalse(report.retry_authorized)
            self.assertFalse(report.financial_confirmation);self.assertFalse(report.effects_authorized)
            lookup.assert_not_called();recover.assert_not_called()
        after=SyntheticPaymentAttempt.objects.get(pk=row.pk).__dict__.copy()
        before.pop('_state');after.pop('_state');self.assertEqual(before,after)
        with patch.object(self.archive,'publish') as publish:
            expired=attempts.dispatch(row.pk,self.archive);publish.assert_not_called()
        self.assertEqual(expired.state,'expired');self.assertGreaterEqual(expired.stopped_at,row.expires_at)
        self.assertEqual(attempts.cancel(row.pk).state,'expired')
        self.assertEqual(attempts.expire(row.pk).stopped_at,expired.stopped_at)
        with self.assertRaisesRegex(BankError,'synthetic_attempt_not_dispatched'):attempts.reconcile(row.pk,self.archive)
        with self.assertRaisesRegex(BankError,'synthetic_attempt_not_dispatched'):attempts._record(row.pk,None)
        self.assertEqual(SyntheticBankOperation.objects.count(),0)

    def test_not_due_expiry_has_no_effect_and_claimed_attempt_cannot_be_cancelled(self):
        row=self.dated(datetime.now(timezone.utc)+timedelta(hours=1))
        self.assertEqual(attempts.expire(row.pk).state,'prepared')
        with self.assertRaises(TimeoutError):attempts.dispatch(row.pk,self.archive,fault='after_commit')
        with self.assertRaisesRegex(BankError,'synthetic_attempt_already_dispatched'):attempts.cancel(row.pk)
        with patch.object(attempts,'database_now',return_value=row.expires_at+timedelta(seconds=1)):
            self.assertEqual(attempts.expire(row.pk).state,'uncertain')
            report=attempts.inspect(row.pk);self.assertTrue(report.lookup_required);self.assertFalse(report.expiry_due)
        self.assertEqual(attempts.reconcile(row.pk,self.archive).state,'observed')
        with self.assertRaisesRegex(BankError,'synthetic_attempt_already_dispatched'):attempts.cancel(row.pk)

    def test_expiry_rechecked_after_archive_recovery(self):
        deadline=datetime.now(timezone.utc)+timedelta(hours=1);row=self.dated(deadline)
        # Controlled clock advancement isolates the exact post-I/O eligibility check.
        with patch.object(attempts,'database_now',side_effect=[deadline-timedelta(seconds=1),deadline]):
            with patch.object(synthetic_bank,'start') as start:
                result=attempts.dispatch(row.pk,self.archive);start.assert_not_called()
        self.assertEqual(result.state,'expired');self.assertEqual(result.archive_receipt,{})
        self.assertEqual(SyntheticBankOperation.objects.count(),0)

    def test_cancel_wins_while_dispatch_is_outside_transaction_recovering_archive(self):
        recovered=Event();release=Event();original=self.archive.recover
        def recover(receipt):
            result=original(receipt);recovered.set()
            if not release.wait(10):raise AssertionError('release timeout')
            return result
        def dispatch():
            try:return attempts.dispatch(self.row.pk,self.archive)
            finally:connections.close_all()
        with patch.object(self.archive,'recover',side_effect=recover),patch.object(synthetic_bank,'start') as start:
            with ThreadPoolExecutor(max_workers=1) as pool:
                pending=pool.submit(dispatch)
                try:
                    self.assertTrue(recovered.wait(10))
                    cancelled=attempts.cancel(self.row.pk)
                finally:release.set()
                self.assertEqual(pending.result(timeout=10).state,'cancelled')
            start.assert_not_called()
        self.assertEqual(attempts.inspect(self.row.pk).stopped_at,cancelled.stopped_at)

    def test_dispatch_claim_wins_before_late_cancellation(self):
        claimed=Event();release=Event();original=synthetic_bank.start
        def start(request,**kwargs):
            claimed.set()
            if not release.wait(10):raise AssertionError('release timeout')
            return original(request,**kwargs)
        def dispatch():
            try:return attempts.dispatch(self.row.pk,self.archive)
            finally:connections.close_all()
        with patch.object(synthetic_bank,'start',side_effect=start):
            with ThreadPoolExecutor(max_workers=1) as pool:
                pending=pool.submit(dispatch)
                try:
                    self.assertTrue(claimed.wait(10))
                    with self.assertRaisesRegex(BankError,'synthetic_attempt_already_dispatched'):
                        attempts.cancel(self.row.pk)
                    self.assertTrue(attempts.inspect(self.row.pk).lookup_required)
                finally:release.set()
                self.assertEqual(pending.result(timeout=10).state,'observed')
        self.assertEqual(SyntheticBankOperation.objects.count(),1)

    def test_database_rejects_invalid_terminal_shapes(self):
        now=datetime.now(timezone.utc)
        for values in ({'state':'cancelled'},{'state':'expired','stopped_at':now},
                       {'state':'expired','expires_at':now,'stopped_at':now-timedelta(seconds=1)},
                       {'state':'expired','expires_at':now},
                       {'state':'cancelled','stopped_at':now,'provider_status':'captured'},
                       {'state':'prepared','stopped_at':now}):
            with self.assertRaises(IntegrityError):
                with transaction.atomic():SyntheticPaymentAttempt.objects.filter(pk=self.row.pk).update(**values)

    def test_lifecycle_and_inspection_guards(self):
        for operation in (attempts.cancel,attempts.expire,attempts.inspect):
            with override_settings(SHOP_ENV='production'):
                with self.assertRaisesRegex(BankError,'synthetic_bank_unavailable'):operation(self.row.pk)
            with transaction.atomic():
                with self.assertRaisesRegex(BankError,'bank_transaction_active'):operation(self.row.pk)


    def test_actual_database_deadline_passes_during_archive_io(self):
        deadline=attempts.database_now()+timedelta(seconds=0.5)
        row=self.dated(deadline);original=self.archive.recover
        def recover(receipt):
            value=original(receipt)
            # Wait on the owned PostgreSQL clock, without changing immutable scope.
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_sleep(GREATEST(0, EXTRACT(EPOCH FROM (%s::timestamptz-clock_timestamp())))+0.01)",[deadline])
            return value
        with patch.object(self.archive,'recover',side_effect=recover) as recovery,patch.object(synthetic_bank,'start') as start:
            result=attempts.dispatch(row.pk,self.archive);start.assert_not_called();recovery.assert_called_once()
        self.assertEqual(result.state,'expired');self.assertGreaterEqual(result.stopped_at,deadline)
        self.assertEqual(SyntheticBankOperation.objects.count(),0)
