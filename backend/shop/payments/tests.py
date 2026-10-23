"""Owned PostgreSQL fake-provider durability; never financial approval evidence."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace,FrozenInstanceError
from threading import Barrier
import re
import uuid
from django.db import connection,connections,transaction,IntegrityError
from django.test import TransactionTestCase,override_settings
from django.test.utils import CaptureQueriesContext
from shop.worker.models import FakeReceipt
from .bank_contract import BankStart,BankObservation,BankError,correlates
from .models import SyntheticBankOperation,SyntheticBankKey
from .synthetic_bank import start,lookup,CAPABILITIES


class SyntheticBankTests(TransactionTestCase):
    def request(self):return BankStart('synthetic-merchant',uuid.uuid4(),uuid.uuid4(),'EUR',12500)

    def test_explicit_capabilities_and_observations_cannot_confirm_commerce(self):
        request=self.request();observed=start(request)
        self.assertTrue(CAPABILITIES.idempotent_start);self.assertTrue(CAPABILITIES.reference_lookup)
        self.assertTrue(CAPABILITIES.authorization_status);self.assertTrue(CAPABILITIES.capture_status)
        self.assertFalse(CAPABILITIES.separate_capture);self.assertFalse(CAPABILITIES.refunds);self.assertFalse(CAPABILITIES.callbacks)
        self.assertFalse(CAPABILITIES.financial_confirmation);self.assertEqual(CAPABILITIES.evidence_class,'local-synthetic')
        self.assertTrue(correlates(request,observed));self.assertEqual(observed.status,'captured')
        self.assertFalse(observed.financial_confirmation);self.assertFalse(observed.effects_authorized)
        with self.assertRaises(FrozenInstanceError):observed.financial_confirmation=True
        self.assertEqual(FakeReceipt.objects.count(),0)

    def test_reference_and_key_retries_preserve_one_operation_and_all_aliases(self):
        request=self.request();first=start(request)
        self.assertEqual(start(request),first)
        alias=replace(request,idempotency_key=uuid.uuid4())
        self.assertEqual(start(alias),first);self.assertEqual(start(alias),first)
        self.assertEqual(SyntheticBankOperation.objects.count(),1);self.assertEqual(SyntheticBankKey.objects.count(),2)
        before=list(SyntheticBankOperation.objects.values())
        for changed in (replace(request,amount_minor=1),replace(request,currency='USD'),
                        replace(alias,reference=uuid.uuid4()),replace(request,merchant='synthetic-other')):
            with self.assertRaisesRegex(BankError,'synthetic_bank_conflict'):start(changed)
        self.assertEqual(list(SyntheticBankOperation.objects.values()),before)
        self.assertEqual(SyntheticBankKey.objects.count(),2)

    def test_response_loss_after_commit_is_reconciled_without_repeating_start(self):
        request=self.request()
        with self.assertRaisesRegex(TimeoutError,'synthetic_bank_timeout'):start(request,fault='after_commit')
        self.assertEqual(SyntheticBankOperation.objects.count(),1);self.assertEqual(SyntheticBankKey.objects.count(),1)
        connection.close()  # Actual independent readback connection, not a process-crash claim.
        with CaptureQueriesContext(connection) as queries:observed=lookup(request.merchant,request.reference)
        self.assertTrue(correlates(request,observed));self.assertEqual(observed.status,'captured')
        self.assertFalse(observed.financial_confirmation)
        self.assertFalse(any(re.match(r'\s*(INSERT|UPDATE|DELETE)\b',q['sql'],re.I) for q in queries))
        self.assertEqual(SyntheticBankOperation.objects.count(),1)

    def test_precommit_timeout_and_distinct_provider_statuses_remain_synthetic(self):
        request=self.request()
        with self.assertRaises(TimeoutError):start(request,fault='before_commit')
        self.assertIsNone(lookup(request.merchant,request.reference));self.assertEqual(SyntheticBankKey.objects.count(),0)
        for outcome in ('authorized','captured','declined','pending'):
            request=self.request();observed=start(request,outcome=outcome)
            self.assertEqual(observed.status,outcome);self.assertEqual(lookup(request.merchant,request.reference),observed)
            self.assertFalse(observed.financial_confirmation);self.assertFalse(observed.effects_authorized)

    def test_exact_and_changed_keys_compete_for_one_semantic_provider_operation(self):
        request=self.request();barrier=Barrier(4)
        requests=[request,request,replace(request,idempotency_key=uuid.uuid4()),replace(request,idempotency_key=uuid.uuid4())]
        def send(value):
            try:barrier.wait(timeout=10);return start(value)
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(send,requests))
        self.assertEqual(len({row.provider_operation_id for row in results}),1)
        self.assertEqual(SyntheticBankOperation.objects.count(),1);self.assertEqual(SyntheticBankKey.objects.count(),3)

    def test_key_collision_rolls_back_the_losing_reference_without_orphan_operation(self):
        first=self.request();second=replace(first,reference=uuid.uuid4());barrier=Barrier(2)
        def send(value):
            try:
                barrier.wait(timeout=10)
                try:return start(value)
                except BankError as error:return str(error)
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(send,(first,second)))
        self.assertEqual(sum(type(row) is BankObservation for row in results),1)
        self.assertIn('synthetic_bank_conflict',results)
        self.assertEqual(SyntheticBankOperation.objects.count(),1);self.assertEqual(SyntheticBankKey.objects.count(),1)

    def test_correlation_distinguishes_wrong_identity_amount_currency_and_types(self):
        request=self.request();observed=start(request)
        for changed in (replace(observed,merchant='synthetic-other'),replace(observed,reference=uuid.uuid4()),
                        replace(observed,currency='USD'),replace(observed,amount_minor=1),
                        replace(observed,amount_minor=float(request.amount_minor)),replace(observed,amount_minor=True),
                        replace(observed,provider_operation_id='private-invalid'),replace(observed,status='unknown')):
            self.assertFalse(correlates(request,changed))
        self.assertFalse(correlates(request,{}));self.assertTrue(correlates(request,observed))

    def test_live_and_outer_manual_transaction_calls_are_refused_before_mutation(self):
        request=self.request()
        for override in ({'SHOP_ENV':'production'},{'SHOP_ENV':'bank-sandbox'},
                         {'PAYMENT_ADAPTER':'real'},{'LIVE_PAYMENTS_ENABLED':True}):
            with override_settings(**override):
                with self.assertRaises(BankError):start(request)
                with self.assertRaises(BankError):lookup(request.merchant,request.reference)
        with transaction.atomic():
            with self.assertRaisesRegex(BankError,'bank_transaction_active'):start(request)
            with self.assertRaisesRegex(BankError,'bank_transaction_active'):lookup(request.merchant,request.reference)
        connection.set_autocommit(False)
        try:
            with self.assertRaisesRegex(BankError,'bank_transaction_active'):start(request)
            with self.assertRaisesRegex(BankError,'bank_transaction_active'):lookup(request.merchant,request.reference)
        finally:connection.rollback();connection.set_autocommit(True)
        self.assertEqual(SyntheticBankOperation.objects.count(),0);self.assertEqual(SyntheticBankKey.objects.count(),0)

    def test_malformed_values_and_database_constraints_cannot_authorize_real_money(self):
        request=self.request()
        for value in (None,{},replace(request,merchant='real-merchant'),replace(request,reference=str(request.reference)),
                      replace(request,idempotency_key='private-key'),replace(request,currency='eur'),
                      replace(request,amount_minor=0),replace(request,amount_minor=True),
                      replace(request,amount_minor=1.5),replace(request,amount_minor=9223372036854775808)):
            with self.assertRaisesRegex(BankError,'invalid_synthetic_request'):start(value)
        for scenario in ({'outcome':'unknown'},{'fault':'retry'},{'outcome':False}):
            with self.assertRaisesRegex(BankError,'invalid_synthetic_scenario'):start(request,**scenario)
        self.assertEqual(SyntheticBankOperation.objects.count(),0)
        start(request);row=SyntheticBankOperation.objects.get()
        for changes in ({'status':'paid'},{'evidence_class':'production'},{'financial_confirmation':True},
                        {'effects_authorized':True},{'amount_minor':0},{'merchant':'actual-merchant'},{'currency':'eur'}):
            with self.assertRaises(IntegrityError):
                with transaction.atomic():SyntheticBankOperation.objects.filter(pk=row.pk).update(**changes)
        row.refresh_from_db();self.assertFalse(row.financial_confirmation);self.assertFalse(row.effects_authorized)
