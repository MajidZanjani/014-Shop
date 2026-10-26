"""Real-PG archive-before-projection receipts across start, manual lookup and inbox."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from io import StringIO
from pathlib import Path
from threading import Barrier
from unittest.mock import patch
import json,uuid,os,subprocess,sys
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connections,transaction,IntegrityError,connection
from django.test import TransactionTestCase,override_settings
from django.utils import timezone
from shop.adapters.evidence_archive import ArchiveError,PreparedArchive
from shop.catalog.checkout import CheckoutError
from . import observations as service,attempts,synthetic_bank,notifications,attempt_tests as fixture
from .bank_contract import BankError
from .models import SyntheticPaymentObservation as Receipt,SyntheticBankOperation,SyntheticNotificationDelivery as Delivery,SyntheticNotificationResult as Result


class ObservationTests(TransactionTestCase):
    def setUp(self):
        fixture.SyntheticAttemptTests.setUp(self)
        self.root=Path(self.directory.name)
        setting=override_settings(LOCAL_CHECKOUT_ARCHIVE_ROOT=str(self.root));setting.enable();self.addCleanup(setting.disable)

    def uncertain(self):
        with self.assertRaises(TimeoutError):attempts.dispatch(self.row.pk,self.archive,fault='after_commit')
    def current(self):self.row.refresh_from_db();return self.row
    def inspect(self):
        with transaction.atomic(durable=True):
            row=type(self.row).objects.select_for_update().get(pk=self.row.pk)
            return service.inspect_locked(row,self.archive)

    def test_dispatch_receipt_and_exact_lookup_retries_commit_one_fact(self):
        attempts.dispatch(self.row.pk,self.archive)
        first=Receipt.objects.get();self.assertEqual(first.revision,1)
        self.assertEqual(first.payload['observation']['status'],'captured');self.assertEqual(self.current().state,'observed')
        for _ in range(2):attempts.reconcile(self.row.pk,self.archive)
        self.assertEqual(Receipt.objects.count(),1);self.assertEqual(Receipt.objects.get().pk,first.pk)
        self.assertEqual(self.inspect()['retained_statuses'],['captured']);self.assertFalse(self.inspect()['financial_confirmation'])
        self.assertEqual(SyntheticBankOperation.objects.count(),1)

    def test_journal_archive_failure_after_capture_keeps_uncertain_then_lookup_recovers(self):
        publish=self.archive.publish
        def outage(identity,body):
            if identity!=self.row.pk:raise ArchiveError('journal unavailable')
            return publish(identity,body)
        with patch.object(self.archive,'publish',side_effect=outage),self.assertRaises(ArchiveError):attempts.dispatch(self.row.pk,self.archive)
        self.assertEqual(self.current().state,'uncertain');self.assertEqual(Receipt.objects.count(),0)
        self.assertEqual(SyntheticBankOperation.objects.count(),1)
        with patch.object(synthetic_bank,'start',side_effect=AssertionError('blind retry')):
            self.assertEqual(attempts.dispatch(self.row.pk,self.archive).state,'uncertain')
            attempts.reconcile(self.row.pk,self.archive)
        self.assertEqual(Receipt.objects.count(),1);self.assertEqual(self.current().state,'observed')

    def test_lookup_miss_then_captured_fact_retains_hash_chain(self):
        self.uncertain()
        with patch.object(synthetic_bank,'lookup',return_value=None):attempts.reconcile(self.row.pk,self.archive)
        miss=Receipt.objects.get();self.assertIsNone(miss.payload['observation']);self.assertEqual(self.current().state,'uncertain')
        attempts.reconcile(self.row.pk,self.archive);rows=list(Receipt.objects.order_by('revision'))
        self.assertEqual(len(rows),2);self.assertEqual(rows[1].payload['previous_sha256'],miss.sha256)
        self.assertTrue(self.inspect()['retained_lookup_miss']);self.assertEqual(self.inspect()['retained_statuses'],['captured'])

    def test_missing_later_lookup_cannot_erase_prior_capture(self):
        attempts.dispatch(self.row.pk,self.archive)
        with patch.object(synthetic_bank,'lookup',return_value=None):attempts.reconcile(self.row.pk,self.archive)
        self.assertEqual(self.current().provider_status,'captured');self.assertEqual(Receipt.objects.count(),2)
        self.assertTrue(self.inspect()['retained_lookup_miss'])

    def test_untyped_wrong_scope_and_status_progression_denied_without_fact(self):
        self.uncertain();value=synthetic_bank.lookup(self.row.merchant,self.row.reference)
        for wrong in ({'status':'captured'},replace(value,currency='GBP'),replace(value,amount_minor=1),replace(value,reference=uuid.uuid4())):
            with patch.object(synthetic_bank,'lookup',return_value=wrong),self.assertRaises(BankError):attempts.reconcile(self.row.pk,self.archive)
        self.assertEqual(Receipt.objects.count(),0);attempts.reconcile(self.row.pk,self.archive)
        with patch.object(synthetic_bank,'lookup',return_value=replace(value,status='authorized')),self.assertRaises(BankError):attempts.reconcile(self.row.pk,self.archive)
        self.assertEqual(Receipt.objects.count(),1)

    def test_database_failure_leaves_prepared_receipt_for_identical_retry(self):
        self.uncertain()
        with patch.object(Receipt.objects,'create',side_effect=IntegrityError('injected')):
            with self.assertRaises(IntegrityError):attempts.reconcile(self.row.pk,self.archive)
        self.assertEqual(self.current().state,'uncertain');self.assertEqual(Receipt.objects.count(),0)
        attempts.reconcile(self.row.pk,self.archive);self.assertEqual(Receipt.objects.count(),1)

    def test_database_receipts_cannot_be_updated_or_deleted(self):
        attempts.dispatch(self.row.pk,self.archive);query=Receipt.objects.all()
        with self.assertRaises(IntegrityError),transaction.atomic():query.update(sha256='0'*64)
        with self.assertRaises(IntegrityError),transaction.atomic():query.delete()

    def test_missing_retained_receipt_blocks_inspection_and_replay(self):
        attempts.dispatch(self.row.pk,self.archive);recover=self.archive.recover;key=Receipt.objects.get().pk
        def missing(receipt):
            if receipt.evidence_id==key:raise ArchiveError('missing receipt')
            return recover(receipt)
        with patch.object(self.archive,'recover',side_effect=missing):
            with self.assertRaises(ArchiveError):self.inspect()
            with self.assertRaises(ArchiveError):attempts.reconcile(self.row.pk,self.archive)
        self.assertEqual(Receipt.objects.count(),1);self.assertEqual(self.current().provider_status,'captured')

    def test_competing_manual_and_inbox_lookup_share_one_fact(self):
        self.uncertain();notifications.enqueue(self.row.pk,uuid.uuid4(),self.archive);owned=notifications.claim();barrier=Barrier(2)
        def action(kind):
            try:
                barrier.wait(timeout=10)
                with PreparedArchive(self.root) as archive:
                    try:
                        if kind=='manual':return attempts.reconcile(self.row.pk,archive).state
                        return notifications.process(owned,archive)
                    except ArchiveError:return 'archive_held'
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(action,['manual','inbox']))
        # The archive's independent nonblocking root lock may deny a competing reader.
        # Resume lookup after contention; this is never a second provider start.
        if results[0]=='archive_held':attempts.reconcile(self.row.pk,self.archive)
        if results[1]=='archive_held':self.assertTrue(notifications.process(owned,self.archive))
        self.assertTrue(all(value in ('observed',True,'archive_held') for value in results))
        self.assertEqual(Receipt.objects.count(),1);self.assertEqual(Result.objects.count(),1)

    def test_fresh_worker_lease_after_journal_archive_wait_rolls_back_all_publication(self):
        from datetime import timedelta
        self.uncertain();notifications.enqueue(self.row.pk,uuid.uuid4(),self.archive);owned=notifications.claim()
        publish=self.archive.publish;clock=[None];database_now=attempts.database_now
        expired=Delivery.objects.get(pk=owned.notification_id).lease_until+timedelta(seconds=1)
        def delayed(identity,body):
            if b'synthetic-normalized-observation' in body:
                clock[0]=expired
            return publish(identity,body)
        with patch.object(self.archive,'publish',side_effect=delayed),patch.object(attempts,'database_now',side_effect=lambda:clock[0] or database_now()):
            self.assertFalse(notifications.process(owned,self.archive))
        self.assertEqual(Receipt.objects.count(),0);self.assertEqual(Result.objects.count(),0);self.assertEqual(self.current().state,'uncertain')
        Delivery.objects.filter(pk=owned.notification_id).update(lease_until=timezone.now()-timedelta(seconds=1))
        self.assertTrue(notifications.process(notifications.claim(),self.archive));self.assertEqual(Receipt.objects.count(),1)

    def test_provider_lookup_is_outside_transaction_and_no_new_start(self):
        self.uncertain();lookup=synthetic_bank.lookup
        def checking(*args):self.assertFalse(connection.in_atomic_block);return lookup(*args)
        with patch.object(synthetic_bank,'lookup',side_effect=checking),patch.object(synthetic_bank,'start',side_effect=AssertionError('blind retry')):
            attempts.reconcile(self.row.pk,self.archive)
        self.assertEqual(Receipt.objects.count(),1)

    def test_local_inspection_is_closed_read_only_and_checks_archive(self):
        attempts.dispatch(self.row.pk,self.archive);out=StringIO()
        with patch.object(synthetic_bank,'lookup',side_effect=AssertionError('lookup')),patch.object(synthetic_bank,'start',side_effect=AssertionError('start')):
            call_command('inspect_synthetic_observations',attempt=str(self.row.pk),stdout=out)
        value=json.loads(out.getvalue());self.assertEqual(value['retained_observations'],1)
        for private in (str(self.row.pk),str(self.row.reference),self.row.merchant,str(self.root)):
            self.assertNotIn(private,out.getvalue())
        self.assertFalse(value['retry_authorized']);self.assertEqual(Receipt.objects.count(),1)
        with self.assertRaises(CommandError):call_command('inspect_synthetic_observations',attempt=str(uuid.uuid4()),stdout=StringIO())

    def test_production_live_and_outer_transaction_closed(self):
        for setting in ({'SHOP_ENV':'production'},{'LIVE_PAYMENTS_ENABLED':True}):
            with override_settings(**setting),self.assertRaises(BankError):attempts.dispatch(self.row.pk,self.archive)
        with transaction.atomic(),self.assertRaises(BankError):attempts.dispatch(self.row.pk,self.archive)
        self.assertEqual(Receipt.objects.count(),0)

    def test_historical_projection_is_not_backfilled_without_new_lookup(self):
        self.uncertain();value=synthetic_bank.lookup(self.row.merchant,self.row.reference)
        # Deliberate pre-journal fixture state, not a migration/provenance claim.
        with transaction.atomic(durable=True):
            row=type(self.row).objects.select_for_update().get(pk=self.row.pk)
            attempts._apply_locked(row,value)
        self.assertEqual(self.inspect()['retained_observations'],0)
        self.assertEqual(self.inspect()['original_response_coverage'],'not_established')
        attempts.reconcile(self.row.pk,self.archive);self.assertEqual(Receipt.objects.count(),1)

    def test_new_process_recovers_prepared_receipt_and_projection_without_second_start(self):
        self.uncertain();env=os.environ.copy();env['DATABASE_NAME']=connections['default'].settings_dict['NAME']
        env['SHOP_LOCAL_CHECKOUT_ARCHIVE_ROOT']=str(self.root);backend=Path(__file__).resolve().parents[2]
        with patch.object(Receipt.objects,'create',side_effect=IntegrityError('injected')):
            with self.assertRaises(IntegrityError):attempts.reconcile(self.row.pk,self.archive)
        code="""from pathlib import Path
from unittest.mock import patch
from django.conf import settings
from shop.adapters.evidence_archive import PreparedArchive
from shop.payments import attempts
import uuid
with PreparedArchive(Path(settings.LOCAL_CHECKOUT_ARCHIVE_ROOT)) as archive:
    with patch('shop.payments.synthetic_bank.start',side_effect=AssertionError('blind retry')):
        attempts.reconcile(uuid.UUID('%s'),archive)
""" % self.row.pk
        result=subprocess.run([sys.executable,'manage.py','shell','--no-imports','-c',code],env=env,cwd=backend,capture_output=True,timeout=20)
        self.assertEqual(result.returncode,0);self.assertEqual(Receipt.objects.count(),1)
        self.assertEqual(self.current().state,'observed');self.assertEqual(SyntheticBankOperation.objects.count(),1)

    def test_injected_revision_gap_is_held_without_changing_projection(self):
        attempts.dispatch(self.row.pk,self.archive);first=Receipt.objects.get()
        Receipt.objects.create(id=uuid.uuid4(),attempt=self.row,revision=3,payload=first.payload,
                               sha256=first.sha256,archive_receipt=first.archive_receipt)
        with self.assertRaises(BankError):self.inspect()
        with self.assertRaises(BankError):attempts.reconcile(self.row.pk,self.archive)
        self.assertEqual(self.current().provider_status,'captured');self.assertEqual(SyntheticBankOperation.objects.count(),1)
