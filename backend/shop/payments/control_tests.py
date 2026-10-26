"""Retained synthetic hold controls and dispatch arbitration on real PostgreSQL."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timedelta,timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Barrier,Event
from unittest.mock import patch
from uuid import uuid4
from django.db import connections,transaction,IntegrityError
from django.test import TransactionTestCase,override_settings
from shop.adapters.evidence_archive import PreparedArchive
from . import attempts,synthetic_bank
from .bank_contract import BankStart,BankError
from .models import SyntheticAttemptControl,SyntheticBankOperation


class SyntheticControlTests(TransactionTestCase):
    def setUp(self):
        self.row=attempts.prepare(BankStart('synthetic-control',uuid4(),uuid4(),'EUR',123))
        self.directory=TemporaryDirectory();self.addCleanup(self.directory.cleanup)
        self.archive=PreparedArchive(Path(self.directory.name));self.addCleanup(self.archive.__exit__,None,None,None)

    def control(self,held,revision,command_id=None):
        return attempts.set_hold(self.row.pk,held=held,expected_revision=revision,command_id=command_id or uuid4())

    def test_hold_blocks_archive_and_release_preserves_exact_request_bytes(self):
        original=attempts.payload(self.row);event=self.control(True,0)
        self.assertEqual(event.revision,1)
        with patch.object(self.archive,'publish') as publish,patch.object(synthetic_bank,'start') as start:
            self.assertEqual(attempts.dispatch(self.row.pk,self.archive).state,'prepared')
            publish.assert_not_called();start.assert_not_called()
        self.row.refresh_from_db();self.assertTrue(self.row.dispatch_held)
        self.assertEqual(attempts.payload(self.row),original)
        report=attempts.inspect(self.row.pk)
        self.assertTrue(report.dispatch_held);self.assertEqual(report.control_revision,1)
        self.assertFalse(report.retry_authorized)
        self.control(False,1)
        result=attempts.dispatch(self.row.pk,self.archive)
        self.assertEqual(result.state,'observed');self.assertFalse(result.financial_confirmation)
        self.assertEqual(SyntheticBankOperation.objects.count(),1)

    def test_historical_release_retry_cannot_clear_newer_hold(self):
        first=self.control(True,0);released=self.control(False,1);latest=self.control(True,2)
        self.assertEqual(self.control(False,1,released.command_id).pk,released.pk)
        self.assertEqual(self.control(True,0,first.command_id).pk,first.pk)
        self.row.refresh_from_db();self.assertTrue(self.row.dispatch_held);self.assertEqual(self.row.control_revision,3)
        for held,revision,key in ((False,1,None),(False,2,None),(True,1,released.command_id),(False,0,released.command_id)):
            with self.assertRaisesRegex(BankError,'synthetic_control_conflict'):self.control(held,revision,key)
        self.assertEqual(SyntheticAttemptControl.objects.count(),3)
        self.assertEqual(SyntheticAttemptControl.objects.get(pk=latest.pk).revision,3)

    def test_competing_commands_have_one_revision_winner_and_exact_retry_is_durable(self):
        barrier=Barrier(2)
        def change(key):
            try:
                barrier.wait(timeout=10)
                try:return self.control(True,0,key).pk
                except BankError as error:return str(error)
            finally:connections.close_all()
        keys=[uuid4(),uuid4()]
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(change,keys))
        self.assertEqual(results.count('synthetic_control_conflict'),1)
        event=SyntheticAttemptControl.objects.get()
        connections.close_all()
        self.assertEqual(self.control(True,0,event.command_id).pk,event.pk)
        self.assertEqual(SyntheticAttemptControl.objects.count(),1)

    def test_hold_wins_during_archive_recovery_and_blocks_final_claim(self):
        recovered=Event();release=Event();original=self.archive.recover
        def recover(receipt):
            value=original(receipt);recovered.set()
            if not release.wait(10):raise AssertionError('release timeout')
            return value
        def dispatch():
            try:return attempts.dispatch(self.row.pk,self.archive)
            finally:connections.close_all()
        with patch.object(self.archive,'recover',side_effect=recover),patch.object(synthetic_bank,'start') as start:
            with ThreadPoolExecutor(max_workers=1) as pool:
                pending=pool.submit(dispatch)
                try:
                    self.assertTrue(recovered.wait(10));self.control(True,0)
                finally:release.set()
                result=pending.result(timeout=10)
            start.assert_not_called()
        self.assertEqual(result.state,'prepared');self.assertTrue(result.dispatch_held)
        self.assertEqual(result.archive_receipt,{})
        self.assertEqual(SyntheticBankOperation.objects.count(),0)
        self.control(False,1)
        self.assertEqual(attempts.dispatch(self.row.pk,self.archive).state,'observed')

    def test_dispatch_claim_wins_and_late_hold_cannot_cancel_it(self):
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
                    with self.assertRaisesRegex(BankError,'synthetic_attempt_not_prepared'):self.control(True,0)
                finally:release.set()
                self.assertEqual(pending.result(timeout=10).state,'observed')
        self.assertEqual(SyntheticAttemptControl.objects.count(),0)

    def test_expiry_precedes_hold_and_terminal_or_uncertain_attempts_refuse_new_controls(self):
        held=self.control(True,0)
        attempts.cancel(self.row.pk)
        self.assertEqual(self.control(True,0,held.command_id).pk,held.pk)
        with self.assertRaisesRegex(BankError,'synthetic_attempt_not_prepared'):self.control(False,1)
        row=attempts.prepare(BankStart('synthetic-expired-control',uuid4(),uuid4(),'EUR',1),
            expires_at=datetime.now(timezone.utc)-timedelta(seconds=1))
        attempts.set_hold(row.pk,held=True,expected_revision=0,command_id=uuid4())
        self.assertEqual(attempts.dispatch(row.pk,self.archive).state,'expired')
        with self.assertRaisesRegex(BankError,'synthetic_attempt_not_prepared'):
            attempts.set_hold(row.pk,held=False,expected_revision=1,command_id=uuid4())

    def test_controls_validate_types_guards_and_database_revision_constraint(self):
        for held,revision,key in ((1,0,uuid4()),(True,False,uuid4()),(True,-1,uuid4()),
                (True,2147483647,uuid4()),(True,0,'private-invalid-key')):
            with self.assertRaisesRegex(BankError,'invalid_synthetic_control'):
                attempts.set_hold(self.row.pk,held=held,expected_revision=revision,command_id=key)
        with override_settings(SHOP_ENV='production'):
            with self.assertRaisesRegex(BankError,'synthetic_bank_unavailable'):self.control(True,0)
        with transaction.atomic():
            with self.assertRaisesRegex(BankError,'bank_transaction_active'):self.control(True,0)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                SyntheticAttemptControl.objects.create(attempt=self.row,revision=0,command_id=uuid4(),held=True)
        self.assertEqual(SyntheticAttemptControl.objects.count(),0)


    def test_same_command_race_retains_one_event(self):
        barrier=Barrier(2);key=uuid4()
        def change(_):
            try:
                barrier.wait(timeout=10)
                return self.control(True,0,key).pk
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(change,range(2)))
        self.assertEqual(results[0],results[1])
        self.assertEqual(SyntheticAttemptControl.objects.count(),1)
        self.row.refresh_from_db();self.assertEqual(self.row.control_revision,1)
