"""Real PostgreSQL leased statement capture, fault recovery and support-effect isolation."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from io import StringIO
from threading import Barrier
from unittest.mock import patch
import uuid
import os
from pathlib import Path
import subprocess
import sys
from django.core.management import call_command
from django.db import connections,transaction,IntegrityError
from django.test import TransactionTestCase,override_settings
from django.utils import timezone
from shop.adapters.evidence_archive import ArchiveError
from shop.payments.bank_contract import BankError
from shop.catalog import checkout,support_ledger as ledger,support_ledger_tests as fixture
from shop.catalog.models import (SyntheticSupportEvent,SyntheticSupportStaffGrant,
    SyntheticStatementMail as Mail,SyntheticStatementDelivery as Delivery,SyntheticStatementCapture as Capture)
from . import statement_mail as service


class StatementMailTests(TransactionTestCase):
    save_cart=fixture.SupportLedgerTests.save_cart
    preview=fixture.SupportLedgerTests.preview
    accept=fixture.SupportLedgerTests.accept

    def setUp(self):
        fixture.SupportLedgerTests.setUp(self)
        reservation=ledger.record(self.owner,self.saved.pk,uuid.uuid4(),'reserve',self.archive,seconds=3600,task_id=uuid.uuid4())
        ledger.record(self.owner,self.saved.pk,uuid.uuid4(),'work',self.archive,seconds=1800,target_id=reservation.pk,staff_request=self.request)

    def statement(self,key=None):
        return ledger.record(self.owner,self.saved.pk,key or uuid.uuid4(),'statement',self.archive,staff_request=self.request)

    def expire(self):Delivery.objects.filter(state='claimed').update(lease_until=timezone.now()-timedelta(seconds=1))

    def balance(self):return ledger.read(self.owner,self.saved.pk,self.archive)['spent_seconds']

    def test_statement_retry_enqueues_once_and_worker_captures_without_debit(self):
        key=uuid.uuid4();event=self.statement(key)
        self.assertEqual(self.statement(key).pk,event.pk);self.assertEqual(Mail.objects.count(),1)
        self.assertEqual(Delivery.objects.get().state,'pending');self.assertEqual(self.balance(),1800)
        from .services import execute_once
        self.assertTrue(execute_once());self.assertEqual(Capture.objects.count(),1)
        self.assertEqual(Delivery.objects.get().state,'captured');self.assertEqual(self.balance(),1800)
        self.assertEqual(SyntheticSupportEvent.objects.count(),3)
        self.assertFalse(Capture.objects.get().payload['actual_email_sent'])
        self.assertEqual(service.status(event,self.archive),'captured')
        self.assertEqual(Mail.objects.get().payload['recipient'],'support-statement@synthetic.invalid')
        self.assertNotIn('actor',Mail.objects.get().payload['body'])

    def test_lost_capture_response_reuses_effect_across_new_claim(self):
        self.statement();first=service.claim()
        self.assertTrue(service.capture(first,self.archive));receipt=Capture.objects.get().pk
        self.expire();second=service.claim()
        self.assertNotEqual(first.token,second.token)
        self.assertTrue(service.capture(second,self.archive));self.assertTrue(service.complete(second,self.archive))
        self.assertEqual(Capture.objects.get().pk,receipt);self.assertEqual(Capture.objects.count(),1)
        self.assertEqual(self.balance(),1800);self.assertEqual(SyntheticSupportEvent.objects.count(),3)

    def test_stale_worker_cannot_capture_or_acknowledge(self):
        self.statement();first=service.claim();self.expire();second=service.claim()
        self.assertFalse(service.capture(first,self.archive));self.assertFalse(service.complete(first,self.archive))
        self.assertTrue(service.capture(second,self.archive));self.assertTrue(service.complete(second,self.archive))
        self.assertFalse(service.complete(first,self.archive))

    def test_intent_archive_failure_rolls_back_statement_and_queue(self):
        original=self.archive.publish
        def publish(identity,body):
            if b'"recipient"' in body:raise ArchiveError('synthetic unavailable')
            return original(identity,body)
        key=uuid.uuid4()
        with patch.object(self.archive,'publish',side_effect=publish):
            with self.assertRaises(ArchiveError):self.statement(key)
        self.assertEqual(SyntheticSupportEvent.objects.count(),2);self.assertEqual(Mail.objects.count(),0)
        self.assertEqual(Delivery.objects.count(),0)
        self.statement(key);self.assertEqual(Mail.objects.count(),1);self.assertEqual(self.balance(),1800)

    def test_capture_archive_failure_leaves_claim_retryable_without_spending(self):
        self.statement();owned=service.claim()
        with patch.object(self.archive,'publish',side_effect=ArchiveError('offline')):
            with self.assertRaises(ArchiveError):service.capture(owned,self.archive)
        self.assertEqual(Capture.objects.count(),0);self.assertEqual(Delivery.objects.get().state,'claimed')
        self.expire();retry=service.claim();self.assertTrue(service.capture(retry,self.archive))
        self.assertTrue(service.complete(retry,self.archive));self.assertEqual(self.balance(),1800)

    def test_prepared_capture_without_database_commit_is_not_completion(self):
        self.statement();owned=service.claim()
        with patch.object(Capture.objects,'create',side_effect=RuntimeError('synthetic crash')):
            with self.assertRaises(RuntimeError):service.capture(owned,self.archive)
        self.assertEqual(Capture.objects.count(),0)
        with self.assertRaises(checkout.CheckoutError):service.complete(owned,self.archive)
        self.expire();retry=service.claim()
        self.assertTrue(service.capture(retry,self.archive));self.assertTrue(service.complete(retry,self.archive))
        self.assertEqual(Capture.objects.count(),1)

    def test_later_ledger_activity_does_not_change_statement_revision(self):
        event=self.statement();original=Mail.objects.get().payload
        ledger.record(self.owner,self.saved.pk,uuid.uuid4(),'reserve',self.archive,seconds=60,task_id=uuid.uuid4())
        self.assertTrue(service.execute_once())
        self.assertEqual(Mail.objects.get().payload,original)
        self.assertEqual(original['body']['revision'],2);self.assertEqual(event.payload['statement']['spent_seconds'],1800)

    def test_missing_source_archive_blocks_capture(self):
        self.statement();owned=service.claim()
        with patch.object(self.archive,'recover',side_effect=ArchiveError('missing')):
            with self.assertRaises((checkout.CheckoutError,ArchiveError)):service.capture(owned,self.archive)
        self.assertEqual(Capture.objects.count(),0)

    def test_staff_scope_or_generation_revocation_blocks_capture(self):
        self.statement();owned=service.claim()
        SyntheticSupportStaffGrant.objects.filter(user=self.staff).delete()
        with self.assertRaises(checkout.CheckoutError):service.capture(owned,self.archive)
        SyntheticSupportStaffGrant.objects.create(user=self.staff,fulfilment=self.grant)
        self.credential.generation=uuid.uuid4();self.credential.save()
        with self.assertRaises(checkout.CheckoutError):service.capture(owned,self.archive)
        self.assertEqual(Capture.objects.count(),0)

    def test_disabled_owner_blocks_capture(self):
        self.statement();owned=service.claim();self.owner.is_active=False;self.owner.save()
        with self.assertRaises((checkout.CheckoutError,ValueError)):service.capture(owned,self.archive)
        self.assertEqual(Capture.objects.count(),0)

    def test_bounded_attempt_exhaustion_holds(self):
        self.statement();service.claim(max_attempts=1);self.expire()
        self.assertIsNone(service.claim(max_attempts=1));self.assertEqual(Delivery.objects.get().state,'held')
        self.assertIsNone(service.claim());self.assertEqual(self.balance(),1800)

    def test_concurrent_claimants_have_one_owner(self):
        self.statement();barrier=Barrier(2)
        def run(_):
            connections.close_all()
            try:
                barrier.wait(timeout=10);return service.claim()
            finally:connections.close_all()
        with ThreadPoolExecutor(2) as pool:results=list(pool.map(run,range(2)))
        self.assertEqual(sum(row is not None for row in results),1);self.assertEqual(Delivery.objects.get().attempts,1)

    def test_history_immutable_and_captured_status_requires_receipt(self):
        event=self.statement();mail=Mail.objects.get()
        with self.assertRaises(IntegrityError),transaction.atomic():Mail.objects.filter(pk=mail.pk).update(sha256='0'*64)
        Delivery.objects.update(state='captured')
        with self.assertRaises(checkout.CheckoutError):service.status(event,self.archive)
        Delivery.objects.update(state='pending')
        service.execute_once()
        with self.assertRaises(IntegrityError),transaction.atomic():Capture.objects.all().delete()

    def test_existing_worker_command_captures_statement(self):
        self.statement();call_command('run_worker',once=True,stdout=StringIO())
        self.assertEqual(Delivery.objects.get().state,'captured');self.assertEqual(Capture.objects.count(),1)

    def test_nonfake_mail_and_production_are_closed(self):
        for overrides in ({'MAIL_ADAPTER':'smtp'},{'SHOP_ENV':'production'},{'LIVE_PAYMENTS_ENABLED':True}):
            with override_settings(**overrides),self.assertRaises((checkout.CheckoutError,BankError)):self.statement()
        self.assertEqual(Mail.objects.count(),0);self.assertEqual(SyntheticSupportEvent.objects.count(),2)

    def test_missing_capture_archive_blocks_acknowledgement(self):
        self.statement();owned=service.claim();service.capture(owned,self.archive)
        with patch.object(self.archive,'recover',side_effect=ArchiveError('missing')):
            with self.assertRaises((checkout.CheckoutError,ArchiveError)):service.complete(owned,self.archive)
        self.assertEqual(Delivery.objects.get().state,'claimed')

    def test_new_worker_process_recovers_lost_response_from_database_capture(self):
        self.statement()
        env=os.environ.copy();env['DATABASE_NAME']=connections['default'].settings_dict['NAME']
        env['SHOP_LOCAL_CHECKOUT_ARCHIVE_ROOT']=str(self.root)
        backend=Path(__file__).resolve().parents[2]
        code="""from unittest.mock import patch
from shop.worker.services import execute_once
try:
    with patch('shop.worker.statement_mail.complete',side_effect=TimeoutError('synthetic response loss')):
        execute_once()
except TimeoutError:
    pass
else:
    raise RuntimeError('expected synthetic response loss')
"""
        first=subprocess.run([sys.executable,'manage.py','shell','--no-imports','-c',code],env=env,cwd=backend,capture_output=True,timeout=20)
        self.assertEqual(first.returncode,0)
        receipt=Capture.objects.get().pk;self.assertEqual(Delivery.objects.get().state,'claimed')
        self.expire()
        second=subprocess.run([sys.executable,'manage.py','run_worker','--once'],env=env,cwd=backend,capture_output=True,timeout=20)
        self.assertEqual(second.returncode,0)
        self.assertEqual(Capture.objects.get().pk,receipt);self.assertEqual(Delivery.objects.get().state,'captured')
        self.assertEqual(self.balance(),1800);self.assertEqual(SyntheticSupportEvent.objects.count(),3)
