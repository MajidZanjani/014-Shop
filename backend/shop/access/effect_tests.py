"""Real PostgreSQL admission/hold races; synthetic effects only, no actual restore."""
from concurrent.futures import ThreadPoolExecutor
from io import StringIO
import json
import os
from pathlib import Path
import subprocess
import sys
from threading import Barrier,Event
from unittest.mock import patch
import uuid
from django.core.management import call_command
from django.db import connection,connections,DatabaseError,transaction
from django.test import TransactionTestCase,override_settings
from django.utils import timezone
from shop.adapters.fake_bank import perform_fake_probe
from shop.adapters.ports import ProbeRequest
from shop.payments import attempts,synthetic_bank,notifications,operations
from shop.payments import attempt_tests as attempt_fixture
from shop.payments import operation_tests as operation_fixture
from shop.payments.bank_contract import BankError,BankMutation
from shop.payments.models import (SyntheticBankOperation,SyntheticBankTransition,
    SyntheticNotificationDelivery,SyntheticNotificationResult,SyntheticOperationDispatch)
from shop.worker import services,statement_mail
from shop.worker.models import Probe,FakeReceipt
from shop.worker import statement_mail_tests as statement_fixture
from shop.catalog import checkout
from shop.catalog.models import SyntheticStatementCapture,SyntheticStatementDelivery
from . import effects
from .models import AccessEpoch,LocalEffectAdmission,LocalAccessRecoveryOperation
from .recovery import AccessRecoveryError,local_recovery_operation,stamp_session_epoch


class RecoveryFixture:
    def recover(self,action='quarantine',*,request_id=None,basis_reset=None):
        return local_recovery_operation(action=action,request_id=request_id or uuid.uuid4(),
            expected_database=self.database,basis_reset=basis_reset)


class EffectAdmissionTests(RecoveryFixture,TransactionTestCase):
    def setUp(self):
        attempt_fixture.SyntheticAttemptTests.setUp(self)
        self.database=connection.settings_dict['NAME']

    def test_hold_denies_new_claims_dispatch_and_direct_bank_mutations(self):
        observed=synthetic_bank.start(self.request,outcome='authorized')
        mutation=BankMutation(self.request.merchant,self.request.reference,observed.provider_operation_id,
            uuid.uuid4(),self.request.currency,self.request.amount_minor,'capture')
        probe=Probe.objects.create();self.recover()
        before=LocalEffectAdmission.objects.count()
        with patch.object(self.archive,'publish',side_effect=AssertionError('held archive dispatch')):
            with self.assertRaisesMessage(BankError,'recovery_effects_pending'):attempts.dispatch(self.row.pk,self.archive)
        self.assertIsNone(services.claim_probe());self.assertFalse(services.execute_once())
        self.assertIsNone(statement_mail.claim());self.assertIsNone(notifications.claim())
        self.assertFalse(statement_mail.execute_once());self.assertFalse(notifications.execute_once())
        with self.assertRaisesMessage(BankError,'recovery_effects_pending'):synthetic_bank.start(self.request,outcome='authorized')
        with self.assertRaisesMessage(BankError,'recovery_effects_pending'):synthetic_bank.mutate(mutation)
        with self.assertRaisesMessage(effects.RecoveryEffectError,'recovery_effects_pending'):perform_fake_probe(ProbeRequest(probe.effect_id))
        probe.refresh_from_db();self.row.refresh_from_db()
        self.assertEqual((probe.state,probe.attempts,self.row.state),('pending',0,'prepared'))
        self.assertEqual(self.row.archive_receipt,{})
        self.assertEqual(synthetic_bank.lookup(self.request.merchant,self.request.reference).status,'authorized')
        self.assertIsNone(synthetic_bank.lookup_mutation(mutation))
        self.assertEqual(SyntheticBankTransition.objects.count(),0);self.assertEqual(FakeReceipt.objects.count(),0)
        self.assertEqual(LocalEffectAdmission.objects.count(),before)
        self.assertTrue(effects.inspect_local_effects()['local_effects_drained'])

    def test_held_inbox_and_old_claim_cannot_process_but_manual_lookup_recovers(self):
        with self.assertRaises(TimeoutError):attempts.dispatch(self.row.pk,self.archive,fault='after_commit')
        note=notifications.enqueue(self.row.pk,uuid.uuid4(),self.archive);claim=notifications.claim()
        self.recover()
        with patch.object(synthetic_bank,'lookup',wraps=synthetic_bank.lookup) as lookup:
            self.assertFalse(notifications.process(claim,self.archive))
            self.assertIsNone(notifications.claim());self.assertFalse(services.execute_once())
            lookup.assert_not_called()
            result=attempts.reconcile(self.row.pk,self.archive)
            self.assertEqual(lookup.call_count,1)
        self.assertEqual(result.provider_status,'captured')
        self.assertEqual(SyntheticNotificationDelivery.objects.get(pk=note.pk).state,'claimed')
        self.assertEqual(SyntheticNotificationResult.objects.count(),0)
        before=list(LocalEffectAdmission.objects.values())
        output=StringIO();call_command('inspect_synthetic_payment',attempt=str(self.row.pk),stdout=output)
        self.assertFalse(json.loads(output.getvalue())['retry_authorized'])
        self.assertEqual(list(LocalEffectAdmission.objects.values()),before)
        self.assertEqual(SyntheticBankOperation.objects.count(),1)

    def test_held_lookup_miss_never_restores_dispatch_permission(self):
        with self.assertRaises(TimeoutError):attempts.dispatch(self.row.pk,self.archive,fault='before_commit')
        reset=uuid.uuid4();self.recover(request_id=reset)
        self.assertEqual(attempts.reconcile(self.row.pk,self.archive).state,'uncertain')
        self.assertTrue(attempts.inspect(self.row.pk).lookup_required)
        self.recover('release',basis_reset=reset)
        with patch.object(synthetic_bank,'start',side_effect=AssertionError('blind resend')):
            self.assertEqual(attempts.dispatch(self.row.pk,self.archive).state,'uncertain')
        self.assertEqual(SyntheticBankOperation.objects.count(),0)

    def test_admitted_bank_call_remains_visible_until_exit_without_held_locks(self):
        entered=Event();release=Event();original=synthetic_bank.validate;reset=uuid.uuid4()
        def wait(request):
            self.assertFalse(connection.in_atomic_block);self.assertTrue(connection.get_autocommit())
            original(request);entered.set()
            if not release.wait(8):raise RuntimeError('bounded adapter wait')
        def send():
            try:return attempts.dispatch(self.row.pk,self.archive).state
            finally:connections.close_all()
        with patch.object(synthetic_bank,'validate',side_effect=wait),ThreadPoolExecutor(max_workers=1) as pool:
            future=pool.submit(send)
            try:
                self.assertTrue(entered.wait(5))
                with transaction.atomic():
                    AccessEpoch.objects.select_for_update(nowait=True).get(pk=1)
                    type(self.row).objects.select_for_update(nowait=True).get(pk=self.row.pk)
                held=self.recover(request_id=reset)
                self.assertEqual(held['unfinished_effects'],2);self.assertFalse(held['local_effects_drained'])
                with self.assertRaisesMessage(AccessRecoveryError,'recovery_effects_unfinished'):
                    self.recover('release',basis_reset=reset)
                with self.assertRaisesMessage(BankError,'recovery_effects_pending'):synthetic_bank.start(self.request)
                self.assertFalse(services.execute_once())
                self.assertIsNone(synthetic_bank.lookup(self.request.merchant,self.request.reference))
            finally:release.set()
            self.assertEqual(future.result(timeout=10),'observed')
        current=self.recover(request_id=reset)
        self.assertEqual(current['invalidated'],held['invalidated'])
        self.assertEqual(current['unfinished_effects'],0);self.assertTrue(current['local_effects_drained'])
        self.assertFalse(current['actual_recovery_qualified'])
        self.assertFalse(self.recover('release',basis_reset=reset)['currently_quarantined'])
        self.assertEqual(SyntheticBankOperation.objects.count(),1)

    def test_quarantine_after_one_way_claim_prevents_new_provider_admission(self):
        original=synthetic_bank.start;reset=uuid.uuid4()
        def hold(request,**kwargs):
            self.row.refresh_from_db();self.assertEqual(self.row.state,'uncertain')
            self.assertEqual(self.recover(request_id=reset)['unfinished_effects'],1)
            return original(request,**kwargs)
        with patch.object(synthetic_bank,'start',side_effect=hold):
            with self.assertRaisesMessage(BankError,'recovery_effects_pending'):attempts.dispatch(self.row.pk,self.archive)
        self.assertEqual(SyntheticBankOperation.objects.count(),0)
        self.assertTrue(effects.inspect_local_effects()['local_effects_drained'])
        self.assertEqual(attempts.reconcile(self.row.pk,self.archive).state,'uncertain')
        self.recover('release',basis_reset=reset)
        with patch.object(synthetic_bank,'start',side_effect=AssertionError('blind resend')):
            self.assertEqual(attempts.dispatch(self.row.pk,self.archive).state,'uncertain')

    def test_failed_exit_after_provider_commit_blocks_release_and_keeps_lookup_available(self):
        original=effects._finish
        def fail(identity,status):
            if LocalEffectAdmission.objects.get(pk=identity).kind=='bank-start':raise DatabaseError('synthetic exit failure')
            return original(identity,status)
        with patch.object(effects,'_finish',side_effect=fail):
            with self.assertRaisesMessage(DatabaseError,'synthetic exit failure'):attempts.dispatch(self.row.pk,self.archive)
        self.row.refresh_from_db();self.assertEqual(self.row.state,'uncertain')
        reset=uuid.uuid4();self.assertEqual(self.recover(request_id=reset)['unfinished_effects'],1)
        self.assertEqual(attempts.reconcile(self.row.pk,self.archive).provider_status,'captured')
        with self.assertRaisesMessage(AccessRecoveryError,'recovery_effects_unfinished'):self.recover('release',basis_reset=reset)
        self.assertEqual(SyntheticBankOperation.objects.count(),1)
        self.assertFalse(effects.inspect_local_effects()['local_effects_drained'])

    def test_abandoned_committed_admission_survives_process_exit_and_later_holds(self):
        code="import django; django.setup(); from shop.access.effects import _begin; _begin('worker-run'); print('LOCAL_ADMISSION_COMMITTED')"
        env=dict(os.environ,DATABASE_NAME=self.database)
        child=subprocess.run([sys.executable,'-c',code],env=env,cwd=Path(__file__).resolve().parents[2],
            capture_output=True,text=True,timeout=15)
        self.assertEqual(child.returncode,0,child.stderr);self.assertEqual(child.stdout.strip(),'LOCAL_ADMISSION_COMMITTED')
        reset=uuid.uuid4();first=self.recover(request_id=reset)
        self.assertEqual(first['unfinished_effects'],1);self.assertFalse(first['local_effects_drained'])
        later=uuid.uuid4();self.recover(request_id=later)
        with self.assertRaisesMessage(AccessRecoveryError,'recovery_changed'):self.recover('release',basis_reset=reset)
        with self.assertRaisesMessage(AccessRecoveryError,'recovery_effects_unfinished'):self.recover('release',basis_reset=later)
        self.assertEqual(LocalEffectAdmission.objects.filter(finished_at__isnull=True).count(),1)
        self.assertEqual(LocalAccessRecoveryOperation.objects.count(),2)

    def test_scope_exits_and_history_are_one_way_and_database_protected(self):
        @effects.local_effect('worker-run')
        def returned():return 'synthetic'
        @effects.local_effect('probe-bank')
        def raised():raise RuntimeError('synthetic scope error')
        self.assertEqual(returned(),'synthetic')
        with self.assertRaisesMessage(RuntimeError,'synthetic scope error'):raised()
        self.assertCountEqual(LocalEffectAdmission.objects.values_list('exit_status',flat=True),['returned','raised'])
        row=LocalEffectAdmission.objects.first()
        for changes in ({'kind':'probe-claim'},{'epoch':uuid.uuid4()},{'finished_at':None,'exit_status':''},{'created_at':timezone.now()}):
            with self.assertRaises(DatabaseError),transaction.atomic():LocalEffectAdmission.objects.filter(pk=row.pk).update(**changes)
        with self.assertRaises(DatabaseError),transaction.atomic():LocalEffectAdmission.objects.filter(pk=row.pk).delete()
        with self.assertRaises(DatabaseError),transaction.atomic():LocalEffectAdmission.objects.create(kind='unknown',epoch=uuid.uuid4())
        with self.assertRaises(DatabaseError),transaction.atomic():LocalEffectAdmission.objects.create(kind='worker-run',epoch=uuid.uuid4(),exit_status='returned')
        self.assertEqual(LocalEffectAdmission.objects.count(),2)

    def test_inspection_never_initializes_and_denied_modes_write_nothing(self):
        self.assertFalse(AccessEpoch.objects.exists())
        value=effects.inspect_local_effects()
        self.assertFalse(value['local_effects_drained']);self.assertFalse(value['currently_quarantined'])
        self.assertFalse(value['retry_authorized']);self.assertFalse(value['actual_recovery_qualified'])
        self.assertFalse(AccessEpoch.objects.exists())
        for changes in ({'SHOP_ENV':'production'},{'PAYMENT_ADAPTER':'real'},{'MAIL_ADAPTER':'real'},
                        {'STORAGE_ADAPTER':'real'},{'LIVE_PAYMENTS_ENABLED':True}):
            with override_settings(**changes):
                with self.assertRaises(effects.RecoveryEffectError):effects._begin('worker-run')
        with transaction.atomic():
            with self.assertRaisesMessage(effects.RecoveryEffectError,'effect_transaction_active'):effects._begin('worker-run')
        connection.set_autocommit(False)
        try:
            with self.assertRaisesMessage(effects.RecoveryEffectError,'effect_transaction_active'):effects._begin('worker-run')
        finally:connection.rollback();connection.set_autocommit(True)
        self.assertEqual(LocalEffectAdmission.objects.count(),0);self.assertFalse(AccessEpoch.objects.exists())

    def test_idle_worker_poll_does_not_accumulate_admissions(self):
        for root in (None,self.directory.name):
            with override_settings(LOCAL_CHECKOUT_ARCHIVE_ROOT=root):
                for _ in range(3):self.assertFalse(services.execute_once())
        self.assertEqual(LocalEffectAdmission.objects.count(),0);self.assertFalse(AccessEpoch.objects.exists())
        with self.assertRaises(ValueError):services.execute_once(lease_seconds=0)

    def test_concurrent_quarantine_and_admission_have_one_serial_order(self):
        barrier=Barrier(2,timeout=5);reset=uuid.uuid4()
        def run(action):
            try:
                barrier.wait()
                if action=='hold':return self.recover(request_id=reset)
                try:synthetic_bank.start(self.request);return 'sent'
                except BankError as error:return str(error)
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:held,sent=list(pool.map(run,('hold','send')))
        self.assertTrue(held['currently_quarantined']);self.assertIn(sent,('sent','recovery_effects_pending'))
        self.assertEqual(SyntheticBankOperation.objects.count(),int(sent=='sent'))
        self.assertTrue(effects.inspect_local_effects()['local_effects_drained'])
        self.assertFalse(effects.inspect_local_effects()['actual_recovery_qualified'])


class StatementRecoveryTests(RecoveryFixture,TransactionTestCase):
    save_cart=statement_fixture.StatementMailTests.save_cart
    preview=statement_fixture.StatementMailTests.preview
    accept=statement_fixture.StatementMailTests.accept
    statement=statement_fixture.StatementMailTests.statement
    balance=statement_fixture.StatementMailTests.balance

    def setUp(self):
        statement_fixture.StatementMailTests.setUp(self)
        self.database=connection.settings_dict['NAME']

    def test_old_statement_claim_and_pending_work_are_held_without_spend_or_capture(self):
        event=self.statement();claim=statement_mail.claim();before=self.balance();self.recover()
        with patch.object(self.archive,'publish',side_effect=AssertionError('held capture')):
            self.assertFalse(statement_mail.capture(claim,self.archive))
        self.assertIsNone(statement_mail.claim());self.assertFalse(services.execute_once())
        self.assertEqual(statement_mail.status(event,self.archive),'claimed')
        self.assertEqual(SyntheticStatementCapture.objects.count(),0);self.assertEqual(self.balance(),before)
        self.assertTrue(effects.inspect_local_effects()['local_effects_drained'])

    def test_existing_capture_can_be_acknowledged_during_hold_without_another_send(self):
        event=self.statement();claim=statement_mail.claim();self.assertTrue(statement_mail.capture(claim,self.archive))
        before=self.balance();self.recover()
        self.assertTrue(statement_mail.complete(claim,self.archive))
        self.assertEqual(statement_mail.status(event,self.archive),'captured')
        self.assertEqual(SyntheticStatementCapture.objects.count(),1);self.assertEqual(self.balance(),before)
        self.assertEqual(SyntheticStatementDelivery.objects.get().state,'captured')


class FinanceRecoveryTests(RecoveryFixture,TransactionTestCase):
    save_cart=operation_fixture.OperationTests.save_cart
    preview=operation_fixture.OperationTests.preview
    accept=operation_fixture.OperationTests.accept
    prepare=operation_fixture.OperationTests.prepare

    def setUp(self):
        operation_fixture.OperationTests.setUp(self)
        self.database=connection.settings_dict['NAME']

    def fresh_trusted_staff_fixture(self):
        # The public/staff routes still require fresh two-factor authentication.
        self.credential.refresh_from_db()
        self.request.session={'shop_staff_mfa':{'generation':str(self.credential.generation),'verified_at':timezone.now().timestamp()}}
        stamp_session_epoch(None,self.request,self.staff)

    def test_hold_keeps_finance_intent_prepared_and_preserves_staff_access_denial(self):
        row=self.prepare();command=operations.mutation(row);self.recover()
        with self.assertRaisesMessage(BankError,'recovery_effects_pending'):operations.dispatch(self.request,row.pk,self.archive)
        self.assertEqual(SyntheticOperationDispatch.objects.get(operation=row).state,'prepared')
        with self.assertRaisesMessage(BankError,'recovery_effects_pending'):synthetic_bank.mutate(command)
        self.assertIsNone(synthetic_bank.lookup_mutation(command))
        with self.assertRaises(checkout.CheckoutError):operations.inspect(self.request,row.pk,self.archive)
        self.assertEqual(SyntheticBankTransition.objects.count(),0)

    def test_hold_between_finance_claim_and_mutation_keeps_uncertainty_after_release(self):
        row=self.prepare();reset=uuid.uuid4();original=synthetic_bank.mutate
        def hold(command,**kwargs):
            self.assertEqual(SyntheticOperationDispatch.objects.get(operation=row).state,'uncertain')
            self.recover(request_id=reset)
            return original(command,**kwargs)
        with patch.object(synthetic_bank,'mutate',side_effect=hold):
            with self.assertRaisesMessage(BankError,'recovery_effects_pending'):operations.dispatch(self.request,row.pk,self.archive)
        self.assertIsNone(synthetic_bank.lookup_mutation(operations.mutation(row)))
        self.recover('release',basis_reset=reset);self.fresh_trusted_staff_fixture()
        with patch.object(synthetic_bank,'mutate',side_effect=AssertionError('blind mutation')):
            operations.reconcile(self.request,row.pk,self.archive);operations.dispatch(self.request,row.pk,self.archive)
        self.assertEqual(SyntheticOperationDispatch.objects.get(operation=row).state,'uncertain')
        self.assertEqual(SyntheticBankTransition.objects.count(),0)

    def test_lost_finance_response_stays_lookup_only_across_hold_and_fresh_staff_scope(self):
        row=self.prepare()
        with self.assertRaises(TimeoutError):operations.dispatch(self.request,row.pk,self.archive,fault='after_commit')
        reset=uuid.uuid4();self.recover(request_id=reset)
        self.assertEqual(synthetic_bank.lookup_mutation(operations.mutation(row)).observation.status,'captured')
        self.assertEqual(SyntheticOperationDispatch.objects.get(operation=row).state,'uncertain')
        self.recover('release',basis_reset=reset);self.fresh_trusted_staff_fixture()
        with patch.object(synthetic_bank,'mutate',side_effect=AssertionError('blind mutation')):
            operations.reconcile(self.request,row.pk,self.archive);operations.dispatch(self.request,row.pk,self.archive)
        self.assertEqual(SyntheticOperationDispatch.objects.get(operation=row).state,'observed')
        self.assertEqual(SyntheticBankTransition.objects.count(),1)
