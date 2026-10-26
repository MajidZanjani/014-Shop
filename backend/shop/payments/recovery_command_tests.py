"""Actual read-only local inspection processes on owned PostgreSQL."""
from datetime import datetime,timedelta,timezone
from io import StringIO
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from unittest.mock import patch
from uuid import uuid4
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection,transaction
from django.test import TransactionTestCase,override_settings
from shop.adapters.evidence_archive import PreparedArchive
from . import attempts,synthetic_bank
from .bank_contract import BankStart
from .models import SyntheticPaymentAttempt,SyntheticBankOperation,SyntheticBankKey,SyntheticAttemptControl


class RecoveryCommandTests(TransactionTestCase):
    def prepare(self,**kwargs):
        return attempts.prepare(BankStart('synthetic-recovery',uuid4(),uuid4(),'EUR',123),**kwargs)

    def child(self,attempt_id,**changes):
        env={key:os.environ[key] for key in ('PATH','LD_LIBRARY_PATH') if key in os.environ}
        env.update(DJANGO_SETTINGS_MODULE='shop.config.synthetic',SHOP_ENV='synthetic',
            LIVE_PAYMENTS_ENABLED='false',PAYMENT_ADAPTER='fake',MAIL_ADAPTER='fake',
            STORAGE_ADAPTER='fake',PSYCOPG_IMPL='python',PYTHONDONTWRITEBYTECODE='1',NO_COLOR='1')
        for key in ('NAME','USER','HOST','PORT'):env['DATABASE_'+key]=str(connection.settings_dict[key])
        env.update(changes)
        backend=Path(__file__).resolve().parents[2]
        return subprocess.run([sys.executable,str(backend/'manage.py'),'inspect_synthetic_payment',
            '--attempt',str(attempt_id)],cwd=backend,env=env,capture_output=True,text=True,timeout=10)

    def unavailable(self,result):
        self.assertEqual(result.returncode,1)
        self.assertEqual(result.stdout,'')
        self.assertEqual(result.stderr,'CommandError: Local synthetic payment inspection unavailable\n')

    def snapshot(self):
        return (list(SyntheticPaymentAttempt.objects.order_by('pk').values()),
            list(SyntheticBankOperation.objects.order_by('pk').values()),
            list(SyntheticBankKey.objects.order_by('pk').values()),
            list(SyntheticAttemptControl.objects.order_by('pk').values()))

    def test_separate_process_reports_prepared_due_cancelled_uncertain_and_observed_without_writes(self):
        prepared=self.prepare()
        attempts.set_hold(prepared.pk,held=True,expected_revision=0,command_id=uuid4())
        due=self.prepare(expires_at=datetime.now(timezone.utc)-timedelta(seconds=1))
        cancelled=self.prepare();attempts.cancel(cancelled.pk)
        uncertain=self.prepare();observed=self.prepare()
        with TemporaryDirectory() as directory:
            with PreparedArchive(Path(directory)) as archive:
                with self.assertRaises(TimeoutError):attempts.dispatch(uncertain.pk,archive,fault='after_commit')
                attempts.dispatch(observed.pk,archive,outcome='authorized')
        before=self.snapshot()
        for row,state,is_due,lookup in ((prepared,'prepared',False,False),(due,'prepared',True,False),
                (cancelled,'cancelled',False,False),(uncertain,'uncertain',False,True),(observed,'observed',False,True)):
            result=self.child(row.pk);self.assertEqual(result.returncode,0,result.stderr);self.assertEqual(result.stderr,'')
            value=json.loads(result.stdout)
            self.assertEqual(set(value),{'state','expires_at','stopped_at','dispatch_held','control_revision','expiry_due','provider_status',
                'lookup_required','evidence_class','retry_authorized','financial_confirmation','effects_authorized'})
            self.assertEqual(value['state'],state);self.assertEqual(value['expiry_due'],is_due)
            self.assertEqual(value['dispatch_held'],row.pk==prepared.pk)
            self.assertEqual(value['control_revision'],1 if row.pk==prepared.pk else 0)
            self.assertEqual(value['lookup_required'],lookup);self.assertEqual(value['evidence_class'],'local-synthetic')
            for key in ('retry_authorized','financial_confirmation','effects_authorized'):self.assertIs(value[key],False)
            for private in (str(row.pk),row.merchant,str(row.reference),str(row.idempotency_key),'amount_minor','archive_receipt','provider_operation_id'):
                self.assertNotIn(private,result.stdout)
            self.assertLess(len(result.stdout),700)
        self.assertEqual(self.snapshot(),before)

    def test_process_invalid_ids_and_disallowed_modes_have_fixed_errors(self):
        row=self.prepare();before=self.snapshot()
        for value in ('private-invalid-value',str(uuid4()),str(row.pk).upper()):self.unavailable(self.child(value))
        for changes in ({'PAYMENT_ADAPTER':'real'},{'LIVE_PAYMENTS_ENABLED':'true'}):
            result=self.child(row.pk,**changes)
            self.assertNotEqual(result.returncode,0);self.assertEqual(result.stdout,'')
            self.assertIn('startup rejected',result.stderr)
            for private in (str(row.pk),row.merchant,str(row.reference),str(row.idempotency_key)):
                self.assertNotIn(private,result.stderr)
        self.assertEqual(self.snapshot(),before)

    def test_process_lock_timeout_has_fixed_error_and_no_writes(self):
        row=self.prepare();before=self.snapshot()
        with transaction.atomic():
            SyntheticPaymentAttempt.objects.select_for_update().get(pk=row.pk)
            self.unavailable(self.child(row.pk))
        self.assertEqual(self.snapshot(),before)

    def test_service_failures_and_outer_transactions_never_touch_archive_or_provider(self):
        row=self.prepare()
        def run():call_command('inspect_synthetic_payment',attempt=str(row.pk),stdout=StringIO(),stderr=StringIO())
        with patch.object(synthetic_bank,'lookup') as lookup,patch.object(PreparedArchive,'recover') as recover:
            with override_settings(SHOP_ENV='production'):
                with self.assertRaisesMessage(CommandError,'Local synthetic payment inspection unavailable'):run()
            with transaction.atomic():
                with self.assertRaisesMessage(CommandError,'Local synthetic payment inspection unavailable'):run()
            connection.set_autocommit(False)
            try:
                with self.assertRaisesMessage(CommandError,'Local synthetic payment inspection unavailable'):run()
            finally:connection.rollback();connection.set_autocommit(True)
            lookup.assert_not_called();recover.assert_not_called()
