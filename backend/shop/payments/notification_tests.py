"""Owned real PostgreSQL hints are not payment proof; lookup/lease/archive controls."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import timedelta
from io import StringIO
from pathlib import Path
from threading import Barrier,Event
from unittest.mock import patch
import json,os,subprocess,sys,uuid
from django.core.management import call_command
from django.db import connection,connections,transaction,IntegrityError
from django.test import TransactionTestCase,override_settings
from django.utils import timezone
from shop.adapters.evidence_archive import ArchiveError
from shop.catalog.models import SyntheticFulfilment,SyntheticSupportEvent
from . import notifications as service,attempts,synthetic_bank,attempt_tests as fixture
from .bank_contract import BankStart,BankError
from .models import (SyntheticBankNotification as Notification,SyntheticNotificationDelivery as Delivery,
    SyntheticNotificationResult as Result,SyntheticBankOperation)


class NotificationTests(TransactionTestCase):
    def setUp(self):
        fixture.SyntheticAttemptTests.setUp(self)
        self.root=Path(self.directory.name)
        override=override_settings(LOCAL_CHECKOUT_ARCHIVE_ROOT=str(self.root));override.enable();self.addCleanup(override.disable)
        with self.assertRaises(TimeoutError):attempts.dispatch(self.row.pk,self.archive,fault='after_commit')

    def enqueue(self,key=None):return service.enqueue(self.row.pk,key or uuid.uuid4(),self.archive)
    def expire(self):Delivery.objects.filter(state='claimed').update(lease_until=timezone.now()-timedelta(seconds=1))
    def current(self):self.row.refresh_from_db();return self.row

    def test_hint_does_not_mark_paid_and_existing_worker_looks_up_without_start(self):
        key=uuid.uuid4();note=self.enqueue(key)
        self.assertEqual(self.enqueue(key).pk,note.pk);self.assertEqual(self.current().state,'uncertain')
        self.assertNotIn('status',note.payload);self.assertNotIn('amount_minor',note.payload)
        from shop.worker.services import execute_once
        with patch.object(synthetic_bank,'start',side_effect=AssertionError('blind start')):self.assertTrue(execute_once())
        self.assertEqual(self.current().provider_status,'captured');self.assertEqual(Delivery.objects.get().state,'checked')
        self.assertEqual(Result.objects.count(),1);self.assertEqual(SyntheticBankOperation.objects.count(),1)
        self.assertEqual(SyntheticFulfilment.objects.count(),0);self.assertEqual(SyntheticSupportEvent.objects.count(),0)
        self.assertFalse(service.inspect(note.pk,self.archive)['financial_confirmation'])
        self.assertFalse(synthetic_bank.CAPABILITIES.callbacks)

    def test_unknown_prepared_cancelled_attempts_and_conflicting_identity_denied(self):
        with self.assertRaises(BankError):service.enqueue(uuid.uuid4(),uuid.uuid4(),self.archive)
        other=attempts.prepare(BankStart('synthetic-other',uuid.uuid4(),uuid.uuid4(),'EUR',123))
        with self.assertRaises(BankError):service.enqueue(other.pk,uuid.uuid4(),self.archive)
        attempts.cancel(other.pk)
        with self.assertRaises(BankError):service.enqueue(other.pk,uuid.uuid4(),self.archive)
        key=uuid.uuid4();self.enqueue(key)
        other=attempts.prepare(BankStart('synthetic-other',uuid.uuid4(),uuid.uuid4(),'EUR',123))
        attempts.dispatch(other.pk,self.archive)
        with self.assertRaises(BankError):service.enqueue(other.pk,key,self.archive)
        self.assertEqual(Notification.objects.count(),1)

    def test_missing_lookup_does_not_confirm_or_dispatch_and_new_hint_can_recheck(self):
        self.enqueue()
        with patch.object(synthetic_bank,'lookup',return_value=None):self.assertTrue(service.execute_once())
        self.assertEqual(self.current().state,'uncertain');self.assertIsNone(Result.objects.get().payload['observation'])
        self.enqueue();self.assertTrue(service.execute_once())
        self.assertEqual(self.current().provider_status,'captured');self.assertEqual(Result.objects.count(),2)

    def test_wrong_identity_value_or_untyped_lookup_cannot_update_attempt(self):
        self.enqueue();observation=synthetic_bank.lookup(self.row.merchant,self.row.reference)
        for wrong in (replace(observation,amount_minor=124),replace(observation,reference=uuid.uuid4()),
                      replace(observation,merchant='synthetic-other'),replace(observation,currency='GBP'),{'status':'captured'}):
            self.expire()
            with patch.object(synthetic_bank,'lookup',return_value=wrong),self.assertRaises(BankError):service.execute_once(max_attempts=5)
            self.assertEqual(self.current().state,'uncertain');self.assertEqual(Result.objects.count(),0)
        self.assertEqual(SyntheticBankOperation.objects.count(),1)

    def test_duplicate_reordered_hints_keep_original_observation_and_no_extra_effect(self):
        for _ in range(3):self.enqueue()
        with patch.object(synthetic_bank,'start',side_effect=AssertionError('blind start')):
            for _ in range(3):self.assertTrue(service.execute_once())
        self.assertEqual(Result.objects.count(),3);self.assertEqual(SyntheticBankOperation.objects.count(),1)
        self.assertEqual(self.current().provider_status,'captured');self.assertEqual(SyntheticFulfilment.objects.count(),0)

    def test_hint_and_result_archive_failures_cannot_commit_state(self):
        with patch.object(self.archive,'publish',side_effect=ArchiveError('offline')):
            with self.assertRaises(ArchiveError):self.enqueue()
        self.assertEqual(Notification.objects.count(),0)
        self.enqueue();owned=service.claim()
        with patch.object(self.archive,'publish',side_effect=ArchiveError('offline')):
            with self.assertRaises(ArchiveError):service.process(owned,self.archive)
        self.assertEqual(Result.objects.count(),0);self.assertEqual(self.current().state,'uncertain')
        self.assertEqual(Delivery.objects.get().state,'claimed')
        self.expire();self.assertTrue(service.process(service.claim(),self.archive))

    def test_prepared_result_is_not_completion_after_database_failure(self):
        self.enqueue();owned=service.claim()
        with patch.object(attempts,'_apply_locked',side_effect=RuntimeError('crash')):
            with self.assertRaises(RuntimeError):service.process(owned,self.archive)
        self.assertEqual(Result.objects.count(),0);self.assertEqual(self.current().state,'uncertain')
        self.expire();self.assertTrue(service.process(service.claim(),self.archive))
        self.assertEqual(Result.objects.count(),1)

    def test_lost_completion_response_is_not_another_lookup_or_payment(self):
        self.enqueue();original=service.process
        def lost(owned,archive):original(owned,archive);raise TimeoutError('lost response')
        with patch.object(service,'process',side_effect=lost),self.assertRaises(TimeoutError):service.execute_once()
        with patch.object(synthetic_bank,'lookup',side_effect=AssertionError('duplicate lookup')):self.assertFalse(service.execute_once())
        self.assertEqual(Result.objects.count(),1);self.assertEqual(Delivery.objects.get().state,'checked')

    def test_expired_worker_cannot_commit_an_observation(self):
        self.enqueue();first=service.claim();self.expire();second=service.claim()
        self.assertFalse(service.process(first,self.archive));self.assertEqual(self.current().state,'uncertain')
        self.assertEqual(Result.objects.count(),0)
        self.assertTrue(service.process(second,self.archive));self.assertEqual(self.current().state,'observed')

    def test_bounded_attempt_exhaustion_holds_for_review(self):
        self.enqueue();service.claim(max_attempts=1);self.expire()
        self.assertIsNone(service.claim(max_attempts=1));self.assertEqual(Delivery.objects.get().state,'held')
        self.assertFalse(service.execute_once());self.assertEqual(self.current().state,'uncertain')

    def test_concurrent_claimants_and_enqueue_retries_converge(self):
        barrier=Barrier(2);key=uuid.uuid4()
        def enqueue(_):
            connections.close_all()
            try:barrier.wait(timeout=10);return self.enqueue(key).pk
            finally:connections.close_all()
        with ThreadPoolExecutor(2) as pool:rows=list(pool.map(enqueue,range(2)))
        self.assertEqual(rows[0],rows[1]);barrier=Barrier(2)
        def claim(_):
            connections.close_all()
            try:barrier.wait(timeout=10);return service.claim()
            finally:connections.close_all()
        with ThreadPoolExecutor(2) as pool:rows=list(pool.map(claim,range(2)))
        self.assertEqual(sum(row is not None for row in rows),1)

    def test_lookup_has_no_held_transaction_or_attempt_delivery_lock(self):
        self.enqueue();entered=Event();release=Event();original=synthetic_bank.lookup
        def lookup(*args):
            self.assertFalse(connection.in_atomic_block);entered.set()
            if not release.wait(10):raise RuntimeError('bounded wait')
            return original(*args)
        def worker():
            try:return service.execute_once()
            finally:connections.close_all()
        with patch.object(synthetic_bank,'lookup',side_effect=lookup),ThreadPoolExecutor(1) as pool:
            future=pool.submit(worker)
            try:
                self.assertTrue(entered.wait(10))
                with transaction.atomic():
                    type(self.row).objects.select_for_update(nowait=True).get(pk=self.row.pk)
                    Delivery.objects.select_for_update(nowait=True).get()
            finally:release.set()
            self.assertTrue(future.result(timeout=10))

    def test_missing_archives_and_sql_mutation_are_denied(self):
        note=self.enqueue();owned=service.claim()
        with patch.object(self.archive,'recover',side_effect=ArchiveError('missing')):
            with self.assertRaises((BankError,ValueError,ArchiveError)):service.process(owned,self.archive)
        self.assertTrue(service.process(owned,self.archive))
        for rows in (Notification.objects.filter(pk=note.pk),Result.objects.all()):
            with self.assertRaises(IntegrityError),transaction.atomic():rows.update(sha256='0'*64)
            with self.assertRaises(IntegrityError),transaction.atomic():rows.delete()

    def test_local_operator_outputs_only_closed_safe_fields(self):
        key=uuid.uuid4();out=StringIO()
        call_command('local_bank_notification','enqueue',notification=str(key),attempt=str(self.row.pk),stdout=out)
        value=json.loads(out.getvalue());self.assertEqual(value['state'],'pending');self.assertNotIn(str(self.row.pk),out.getvalue())
        call_command('run_worker',once=True,stdout=StringIO())
        out=StringIO();call_command('local_bank_notification','inspect',notification=str(key),stdout=out)
        self.assertEqual(json.loads(out.getvalue())['lookup_status'],'captured')
        for overrides in ({'SHOP_ENV':'production'},{'PAYMENT_ADAPTER':'actual'},{'LIVE_PAYMENTS_ENABLED':True}):
            with override_settings(**overrides),self.assertRaises(BankError):service.enqueue(self.row.pk,uuid.uuid4(),self.archive)

    def test_new_worker_process_recovers_prepared_result_without_another_start(self):
        self.enqueue();env=os.environ.copy();env['DATABASE_NAME']=connections['default'].settings_dict['NAME']
        env['SHOP_LOCAL_CHECKOUT_ARCHIVE_ROOT']=str(self.root);backend=Path(__file__).resolve().parents[2]
        code="""from unittest.mock import patch
from shop.payments.notifications import execute_once
try:
    with patch('shop.payments.attempts._apply_locked',side_effect=RuntimeError('synthetic commit fault')):
        execute_once()
except RuntimeError:
    pass
else:
    raise RuntimeError('expected synthetic fault')
"""
        result=subprocess.run([sys.executable,'manage.py','shell','--no-imports','-c',code],env=env,cwd=backend,capture_output=True,timeout=20)
        self.assertEqual(result.returncode,0);self.assertEqual(Result.objects.count(),0);self.expire()
        result=subprocess.run([sys.executable,'manage.py','run_worker','--once'],env=env,cwd=backend,capture_output=True,timeout=20)
        self.assertEqual(result.returncode,0);self.assertEqual(Result.objects.count(),1)
        self.assertEqual(self.current().provider_status,'captured');self.assertEqual(SyntheticBankOperation.objects.count(),1)

    def test_lease_expiry_after_final_lock_or_archive_wait_cannot_commit(self):
        self.enqueue();owned=service.claim()
        after_lease=Delivery.objects.get().lease_until+timedelta(seconds=1)
        with patch.object(attempts,'database_now',return_value=after_lease):
            self.assertFalse(service.process(owned,self.archive))
        self.assertEqual(Result.objects.count(),0);self.assertEqual(self.current().state,'uncertain')
        self.assertEqual(Delivery.objects.get().state,'claimed')
