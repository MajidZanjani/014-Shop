"""Final amendment: real PG/local synthetic purchases, never actual financial proof."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Barrier
from unittest.mock import patch
import json,uuid
from django.contrib.auth import get_user_model
from django.db import connections
from django.test import SimpleTestCase,TransactionTestCase,override_settings
from shop.adapters.evidence_archive import PreparedArchive,ArchiveError
from shop.catalog.models import ConfigurationDraft
from shop.catalog.rules import CATALOG,evaluate
from shop.catalog.simple import ConfigurationForm
from shop.catalog.tests import verified_login
from shop.catalog.purchase_policy import quote,FIXTURE_OFFERS
from . import purchase_demo as demo,synthetic_bank
from .bank_contract import BankError
from .models import SyntheticPurchase,SyntheticCreditReservation,SyntheticBankOperation


def configuration(choice='not-designed',packages=2):
    return {'product_id':CATALOG['product_id'],'profile_id':CATALOG['profile_id'],'quantity':1,
        'vendor':'altera','families':['altera-max-10'],'term':'rd-annual','production_band':None,
        'production_units':None,'fixed_nodes':1,'floating_nodes':0,'support_packages':packages,
        'platform':{'choice':choice,'kit_id':'synthetic-kit-rev-a' if choice=='listed-kit' else None,'name':None}}


class PurchasePolicyTests(SimpleTestCase):
    def test_ready_kit_zero_support_and_unknown_custom_development(self):
        ready=quote(configuration('listed-kit',0),'synthetic-ready-kit')
        self.assertEqual(ready['status'],'synthetic_purchasable')
        self.assertEqual(ready['snapshot']['support_policy'],'optional')
        for choice in ('not-designed','other-board'):
            result=quote(configuration(choice),'synthetic-development')
            self.assertEqual(result['status'],'synthetic_purchasable')
            self.assertEqual(result['snapshot']['support_policy'],'required')
            self.assertFalse(result['financial_confirmation']);self.assertFalse(result['effects_authorized'])

    def test_support_tampering_and_missing_licence_or_commercial_terms_fail_closed(self):
        self.assertIn('required_support_minimum',quote(configuration(packages=0),'synthetic-development')['errors'])
        self.assertEqual(quote(configuration('other-board'),'synthetic-ready-kit')['status'],'unavailable')
        for field in ('licence_minor','rights','annual_start','delivery','support_required','minimum_packages'):
            offer=replace(FIXTURE_OFFERS[1],**{field:None})
            self.assertEqual(quote(configuration(),offer.id,offers=(offer,))['status'],'awaiting_review')
        value=configuration();value['families']=[]
        self.assertEqual(quote(value,'synthetic-development')['status'],'invalid')
        value=configuration();value['platform']['pinout']='PRIVATE_TECHNICAL_CANARY'
        self.assertEqual(quote(value,'synthetic-development')['status'],'invalid')

    def test_no_javascript_form_uses_same_rule_and_only_relevant_optional_detail(self):
        data=configuration();platform=data.pop('platform');data.pop('product_id');data.pop('profile_id');data.pop('quantity')
        data['production_band']='';data['platform_choice']=platform['choice']
        form=ConfigurationForm(data)
        self.assertNotIn('board_name',form.fields);self.assertNotIn('kit_id',form.fields)
        self.assertTrue(form.is_valid(),form.errors)
        self.assertEqual(quote(form.configuration(),'synthetic-development')['status'],'synthetic_purchasable')
        data['support_packages']=0;form=ConfigurationForm(data);self.assertTrue(form.is_valid())
        self.assertIn('required_support_minimum',quote(form.configuration(),'synthetic-development')['errors'])
        data['platform_choice']='other-board';data['board_name']='Prototype'
        form=ConfigurationForm(data);self.assertIn('board_name',form.fields);self.assertNotIn('kit_id',form.fields)
        self.assertTrue(form.is_valid());self.assertEqual(form.configuration()['platform']['name'],'Prototype')


class PurchaseFlowTests(TransactionTestCase):
    def setUp(self):
        self.owner=get_user_model().objects.create_user(username='synthetic-purchase-owner')
        self.other=get_user_model().objects.create_user(username='synthetic-purchase-other')
        verified_login(self.client,self.owner)
        self.directory=TemporaryDirectory();self.addCleanup(self.directory.cleanup)
        self.archive=PreparedArchive(Path(self.directory.name));self.addCleanup(self.archive.__exit__,None,None,None)
        # Use the supported owner draft API rather than manufacture an order/approval.
        payload={'request_id':str(uuid.uuid4()),'revision':CATALOG['revision'],'configuration':configuration()}
        response=self.client.post('/api/v1/configuration-drafts/',data=json.dumps(payload),content_type='application/json')
        self.assertEqual(response.status_code,201,response.content)
        self.draft=ConfigurationDraft.objects.get(pk=response.json()['id'])

    def prepare(self,key=None):
        return demo.prepare(self.owner,key or uuid.uuid4(),draft_id=self.draft.pk,offer_id='synthetic-development')

    def test_purchase_archive_bank_support_and_staged_design_keep_one_entitlement(self):
        row=self.prepare();self.assertEqual(self.prepare().pk,row.pk)
        original=synthetic_bank.start
        def start(request,**kwargs):
            current=SyntheticPurchase.objects.get(pk=row.pk);demo.retained(current,self.archive)
            return original(request,**kwargs)
        with patch.object(synthetic_bank,'start',side_effect=start):funded=demo.fund(row.pk,self.owner,self.archive)
        self.assertTrue(funded.simulated_funded);self.assertEqual(funded.simulated_credit_seconds,72000)
        self.assertEqual(funded.simulated_entitlements,1)
        initial=demo.deliver(row.pk,self.owner,self.archive,'initial')
        self.assertTrue(initial.initial_delivered);self.assertFalse(initial.reference_delivered)
        self.assertTrue(initial.snapshot['later_reference_design'])
        later=demo.deliver(row.pk,self.owner,self.archive,'reference')
        demo.deliver(row.pk,self.owner,self.archive,'reference');demo.fund(row.pk,self.owner,self.archive)
        later.refresh_from_db();self.assertEqual(later.simulated_entitlements,1);self.assertEqual(later.simulated_credit_seconds,72000)
        self.assertTrue(later.reference_delivered);self.assertFalse(later.financial_confirmation);self.assertFalse(later.effects_authorized)
        self.assertEqual(SyntheticBankOperation.objects.count(),1)
        self.assertEqual(later.snapshot['configuration']['platform'],configuration()['platform'])

    def test_no_funding_or_delivery_without_archive_and_lost_response_never_resends(self):
        row=self.prepare()
        with self.assertRaisesRegex(BankError,'synthetic_delivery_unavailable'):demo.deliver(row.pk,self.owner,self.archive,'initial')
        with patch.object(self.archive,'publish',side_effect=ArchiveError('unavailable')):
            with patch.object(synthetic_bank,'start') as start:
                with self.assertRaises(ArchiveError):demo.fund(row.pk,self.owner,self.archive)
                start.assert_not_called()
        with self.assertRaises(TimeoutError):demo.fund(row.pk,self.owner,self.archive,fault='after_commit')
        with patch.object(synthetic_bank,'start',side_effect=AssertionError('blind resend')):
            self.assertFalse(demo.fund(row.pk,self.owner,self.archive).simulated_funded)
            funded=demo.reconcile(row.pk,self.owner,self.archive)
        self.assertTrue(funded.simulated_funded);self.assertEqual(funded.simulated_credit_seconds,72000)
        with self.assertRaisesRegex(BankError,'synthetic_delivery_unavailable'):demo.deliver(row.pk,self.owner,self.archive,'reference')

    def test_topup_needs_no_licence_platform_or_new_entitlement_and_reservation_is_once(self):
        row=demo.prepare(self.owner,uuid.uuid4(),support_packages=1)
        self.assertIsNone(row.draft_id);self.assertNotIn('platform',row.snapshot)
        funded=demo.fund(row.pk,self.owner,self.archive)
        self.assertEqual(funded.simulated_entitlements,0);self.assertEqual(funded.simulated_credit_seconds,36000)
        key=uuid.uuid4();first=demo.reserve_credit(row.pk,self.owner,key,36000)
        self.assertEqual(demo.reserve_credit(row.pk,self.owner,key,36000).pk,first.pk)
        with self.assertRaisesRegex(BankError,'synthetic_credit_unavailable'):demo.reserve_credit(row.pk,self.owner,uuid.uuid4(),1)
        self.assertEqual(SyntheticCreditReservation.objects.count(),1)
        self.assertEqual(SyntheticPurchase.objects.count(),1)

    def test_concurrent_existing_credit_reservations_cannot_double_allocate(self):
        row=demo.fund(self.prepare().pk,self.owner,self.archive);barrier=Barrier(2)
        def reserve(_):
            try:
                barrier.wait(timeout=10)
                try:return demo.reserve_credit(row.pk,self.owner,uuid.uuid4(),50000).pk
                except BankError as error:return str(error)
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(reserve,range(2)))
        self.assertEqual(results.count('synthetic_credit_unavailable'),1)
        row.refresh_from_db();self.assertEqual(row.reserved_seconds,50000)
        self.assertEqual(SyntheticBankOperation.objects.count(),1)

    def test_private_scope_revoked_owner_and_live_mode_refuse_without_effects(self):
        row=self.prepare()
        with self.assertRaisesRegex(BankError,'synthetic_purchase_unavailable'):demo.fund(row.pk,self.other,self.archive)
        self.owner.is_active=False;self.owner.save()
        with self.assertRaisesRegex(BankError,'synthetic_purchase_unavailable'):demo.fund(row.pk,self.owner,self.archive)
        with override_settings(SHOP_ENV='production'):
            with self.assertRaisesRegex(BankError,'synthetic_bank_unavailable'):self.prepare()
        self.assertEqual(SyntheticBankOperation.objects.count(),0)
        self.assertEqual(SyntheticPurchase.objects.get().snapshot['configuration'],self.draft.configuration)


    def test_concurrent_funding_uses_one_bank_operation_and_fixed_credit_grant(self):
        row=self.prepare();barrier=Barrier(2);original=PreparedArchive.recover
        second=TemporaryDirectory();self.addCleanup(second.cleanup)
        def recover(archive,receipt):
            value=original(archive,receipt)
            if receipt.evidence_id==row.pk:barrier.wait(timeout=10)
            return value
        def fund(directory):
            try:
                with PreparedArchive(Path(directory)) as archive:
                    return demo.fund(row.pk,self.owner,archive).simulated_funded
            finally:connections.close_all()
        with patch.object(PreparedArchive,'recover',recover):
            with ThreadPoolExecutor(max_workers=2) as pool:
                results=list(pool.map(fund,[self.directory.name,second.name]))
        self.assertIn(True,results);row.refresh_from_db()
        self.assertEqual(row.simulated_credit_seconds,72000);self.assertEqual(row.simulated_entitlements,1)
        self.assertEqual(SyntheticBankOperation.objects.count(),1)

    def test_funding_uses_committed_attempt_and_archived_snapshot_stays_immutable(self):
        from types import SimpleNamespace
        row=self.prepare();original=deepcopy(row.snapshot)
        # Caller-supplied observed status cannot replace committed bank/attempt facts.
        fake=SimpleNamespace(pk=row.attempt_id,state='observed',provider_status='captured')
        self.assertFalse(demo._record_funding(row.pk,self.owner,fake).simulated_funded)
        demo.fund(row.pk,self.owner,self.archive)
        self.draft.configuration['platform']['name']='Later draft edit'
        self.draft.save(update_fields=['configuration'])
        row.refresh_from_db();self.assertEqual(row.snapshot,original)
        demo.retained(row,self.archive)


    def test_draft_owner_change_cannot_return_another_owners_retained_purchase(self):
        row=self.prepare()
        verified_login(self.client,self.other)
        self.draft.owner=self.other;self.draft.save(update_fields=['owner'])
        with self.assertRaisesRegex(BankError,'synthetic_purchase_conflict'):
            demo.prepare(self.other,uuid.uuid4(),draft_id=self.draft.pk,offer_id='synthetic-development')
        row.refresh_from_db();self.assertEqual(row.owner_id,self.owner.pk)
        self.assertEqual(SyntheticPurchase.objects.count(),1);self.assertEqual(SyntheticBankOperation.objects.count(),0)


    def test_saved_api_draft_cannot_remove_required_support_or_supply_its_policy(self):
        value=configuration(packages=0)
        response=self.client.post('/api/v1/configuration-drafts/',data=json.dumps({'request_id':str(uuid.uuid4()),
            'revision':CATALOG['revision'],'configuration':value}),content_type='application/json')
        self.assertEqual(response.status_code,201)  # Unaccepted drafts can be incomplete for sale.
        with self.assertRaisesRegex(BankError,'synthetic_offer_unavailable'):
            demo.prepare(self.owner,uuid.uuid4(),draft_id=response.json()['id'],offer_id='synthetic-development')
        value['support_policy']='optional'
        response=self.client.post('/api/v1/configurations/validate/',data=json.dumps(value),content_type='application/json')
        self.assertEqual(response.status_code,422)
        self.assertEqual(SyntheticPurchase.objects.count(),0);self.assertEqual(SyntheticBankOperation.objects.count(),0)
