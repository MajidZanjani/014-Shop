"""Selected disposable-restore staff authority; actual revocation/MFA recovery pending."""
from io import StringIO
import json
from pathlib import Path
import re
import tempfile
from unittest.mock import patch
import uuid
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.core.management import call_command
from django.db import connection,transaction
from django.test import Client,TransactionTestCase,override_settings
from shop.catalog import support_ledger_tests as fixture,support_ledger as ledger,licence_changes,support_refunds,checkout
from shop.catalog.models import (DraftCart,CartSnapshot,QuotationRequest,BusinessDraftSnapshot,SyntheticCheckout,
    SyntheticCheckoutAcceptance,SyntheticFulfilment,SyntheticLineEntitlement,SyntheticSupportEvent,
    SyntheticLicenceCase,SyntheticSupportRefundCase,SyntheticSupportStaffGrant,SyntheticDeliveryStaffGrant,
    SyntheticLicenceCaseStaffGrant,SyntheticSupportRefundStaffGrant)
from shop.payments import attempts
from shop.payments.bank_contract import BankStart
from shop.payments.models import SyntheticBankOperation,SyntheticPaymentAttempt,SyntheticOverpaymentStaffGrant,SyntheticPaymentStaffGrant
from .grants import revoke_staff_resource_grants
from .models import AccessEpoch,LocalAccessRecoveryOperation,StaffCredential,StaffQuotationGrant,StaffChallenge
from .recovery import AccessRecoveryError,local_recovery_operation
from .staff_auth import staff_credential
from .staff_tests import STAFF_SETTINGS


class StaffRestoreTests(TransactionTestCase):
    save_cart=fixture.SupportLedgerTests.save_cart
    preview=fixture.SupportLedgerTests.preview
    accept=fixture.SupportLedgerTests.accept

    def setUp(self):
        fixture.SupportLedgerTests.setUp(self)
        self.database=connection.settings_dict['NAME']
        self.password='synthetic-restored-password'
        self.staff.set_password(self.password);self.staff.save(update_fields=['password'])
        self.second=get_user_model().objects.create_user(username='second-restored-staff',is_staff=True)
        self.second_credential=StaffCredential.objects.create(user=self.second)
        self.line=SyntheticLineEntitlement.objects.get(fulfilment=self.grant)
        self.accepted=SyntheticCheckoutAcceptance.objects.get(checkout=self.saved)
        cart=DraftCart.objects.get(owner=self.owner)
        snapshot=CartSnapshot.objects.get(cart=cart,version=cart.version)
        self.quotation=QuotationRequest.objects.create(cart=cart,snapshot=snapshot,request_id=uuid.uuid4())
        case=licence_changes.capture(self.owner,self.saved.pk,self.line.pk,uuid.uuid4(),{'kind':'renewal'},self.archive)
        refund=support_refunds.capture(self.owner,self.saved.pk,uuid.uuid4(),36000,self.archive)
        extra=attempts.prepare(BankStart('synthetic-restore-extra',uuid.uuid4(),uuid.uuid4(),'EUR',100))
        self.scopes={
            'quotation':(StaffQuotationGrant,{'quotation':self.quotation}),
            'support':(SyntheticSupportStaffGrant,{'fulfilment':self.grant}),
            'delivery':(SyntheticDeliveryStaffGrant,{'entitlement':self.line}),
            'licence_case':(SyntheticLicenceCaseStaffGrant,{'case':case}),
            'support_refund':(SyntheticSupportRefundStaffGrant,{'case':refund}),
            'overpayment':(SyntheticOverpaymentStaffGrant,{'acceptance':self.accepted,'extra_attempt':extra}),
            'payment':(SyntheticPaymentStaffGrant,{'acceptance':self.accepted,'kind':'refund'})}
        for model,fields in self.scopes.values():
            for user in (self.staff,self.second):model.objects.get_or_create(user=user,**fields)
        self.reservation=ledger.record(self.owner,self.saved.pk,uuid.uuid4(),'reserve',self.archive,seconds=3600,task_id=uuid.uuid4())
        ledger.record(self.owner,self.saved.pk,uuid.uuid4(),'work',self.archive,seconds=600,target_id=self.reservation.pk,staff_request=self.request)
        self.original=self.history()

    def history(self):
        models=(QuotationRequest,BusinessDraftSnapshot,SyntheticCheckout,SyntheticCheckoutAcceptance,
            SyntheticFulfilment,SyntheticLineEntitlement,SyntheticSupportEvent,SyntheticLicenceCase,
            SyntheticSupportRefundCase,SyntheticBankOperation,SyntheticPaymentAttempt)
        return {model._meta.label:list(model.objects.order_by('pk').values()) for model in models}

    def counts(self,user=None):
        return {name:model.objects.filter(**({'user':user} if user is not None else {})).count()
            for name,(model,_) in self.scopes.items()}

    def operation(self,action='quarantine',*,request_id=None,basis_reset=None):
        return local_recovery_operation(action=action,request_id=request_id or uuid.uuid4(),
            expected_database=self.database,basis_reset=basis_reset)

    def test_selected_restore_disables_restored_staff_credentials(self):
        selected=uuid.uuid4()
        with override_settings(LOCAL_RESTORE_ID=selected):
            self.operation(request_id=selected)
            self.operation('release',basis_reset=selected)
        self.credential.refresh_from_db()
        self.assertFalse(self.credential.enabled,'fresh sign-in must not reuse restored staff authority')

    def test_selected_restore_clears_all_seven_scopes_for_all_staff_and_keeps_business_history(self):
        selected=uuid.uuid4()
        self.assertEqual(self.counts(),dict.fromkeys(self.scopes,2))
        with override_settings(LOCAL_RESTORE_ID=selected):
            result=self.operation(request_id=selected)
            self.assertEqual(result['invalidated']['staff_credentials_disabled'],2)
            self.assertEqual(result['invalidated']['staff_resource_grants'],dict(dict.fromkeys(self.scopes,2),shb_order=0,shb_invitation=0,shb_invitation_issue=0,shb_discount=0))
            self.assertEqual(self.counts(),dict.fromkeys(self.scopes,0))
            self.operation('release',basis_reset=selected)
        self.assertFalse(StaffCredential.objects.filter(enabled=True).exists())
        self.assertEqual(self.history(),self.original)
        self.owner.refresh_from_db();self.assertTrue(self.owner.is_active)
        self.assertEqual(ledger.read(self.owner,self.saved.pk,self.archive)['spent_seconds'],600)

    def test_ordinary_hold_preserves_enabled_credentials_and_all_resource_assignments(self):
        key=uuid.uuid4();held=self.operation(request_id=key)
        self.assertNotIn('staff_credentials_disabled',held['invalidated'])
        self.assertEqual(self.counts(),dict.fromkeys(self.scopes,2))
        self.operation('release',basis_reset=key)
        self.assertEqual(StaffCredential.objects.filter(enabled=True).count(),2)
        self.assertEqual(self.history(),self.original)

    def test_unrelated_hold_does_not_clear_until_the_selected_restore_quarantine(self):
        selected=uuid.uuid4();other=uuid.uuid4()
        with override_settings(LOCAL_RESTORE_ID=selected):
            held=self.operation(request_id=other)
            self.assertTrue(held['startup_recovery_pending'])
            self.assertEqual(self.counts(),dict.fromkeys(self.scopes,2))
            self.operation(request_id=selected)
            self.assertEqual(self.counts(),dict.fromkeys(self.scopes,0))
            with self.assertRaisesMessage(AccessRecoveryError,'recovery_changed'):self.operation('release',basis_reset=other)
            self.operation('release',basis_reset=selected)

    def test_explicit_reset_two_factors_and_reassignment_survive_exact_quarantine_replay(self):
        selected=uuid.uuid4()
        capture=tempfile.TemporaryDirectory();self.addCleanup(capture.cleanup)
        with override_settings(LOCAL_RESTORE_ID=selected,**STAFF_SETTINGS,LOCAL_STAFF_CAPTURE_ROOT=capture.name):
            original=self.operation(request_id=selected)
            self.operation('release',basis_reset=selected)
            browser=Client(enforce_csrf_checks=True,HTTP_HOST='staff.localhost')
            self.assertEqual(browser.get('/staff/session/').status_code,200)
            def post(path,value):
                return browser.post('/staff/'+path,data=json.dumps(value),content_type='application/json',
                    HTTP_X_CSRFTOKEN=browser.cookies['shop_staff_csrftoken'].value)
            self.assertEqual(post('login/',{'username':self.staff.username,'password':self.password}).status_code,400)
            self.assertEqual(StaffChallenge.objects.count(),0)
            before=set(Path(capture.name).iterdir())
            call_command('local_staff','reset',username=self.staff.username,capture_root=capture.name,stdout=StringIO())
            password=re.search(r'^Password: (.+)$',(set(Path(capture.name).iterdir())-before).pop().read_text(),re.M)[1]
            self.assertEqual(self.counts(self.staff),dict.fromkeys(self.scopes,0))
            before=set(Path(capture.name).iterdir())
            self.assertEqual(post('login/',{'username':self.staff.username,'password':password}).status_code,200)
            code=re.search(r'^Code: (.+)$',(set(Path(capture.name).iterdir())-before).pop().read_text(),re.M)[1]
            self.assertEqual(post('verify/',{'code':code}).status_code,200)
            self.assertTrue(browser.get('/staff/session/').json()['authenticated'])
            self.request.session=dict(browser.session)
            self.assertIsNotNone(staff_credential(self.request,recent=True))
            with self.assertRaises(checkout.CheckoutError):
                ledger.record(self.owner,self.saved.pk,uuid.uuid4(),'work',self.archive,seconds=60,target_id=self.reservation.pk,staff_request=self.request)
            self.assertEqual(self.history(),self.original)
            call_command('local_staff','grant-support',username=self.staff.username,checkout=str(self.saved.pk),stdout=StringIO())
            credential=StaffCredential.objects.get(user=self.staff)
            replay=self.operation(request_id=selected)
            self.assertEqual(replay['invalidated'],original['invalidated'])
            self.assertFalse(replay['currently_quarantined'])
            self.assertEqual(StaffCredential.objects.get(user=self.staff).generation,credential.generation)
            self.assertTrue(StaffCredential.objects.get(user=self.staff).enabled)
            self.assertTrue(SyntheticSupportStaffGrant.objects.filter(user=self.staff,fulfilment=self.grant).exists())
            self.assertTrue(browser.get('/staff/session/').json()['authenticated'])
            ledger.record(self.owner,self.saved.pk,uuid.uuid4(),'work',self.archive,seconds=60,target_id=self.reservation.pk,staff_request=self.request)
            later=uuid.uuid4();self.operation(request_id=later);self.operation('release',basis_reset=later)
            self.assertTrue(StaffCredential.objects.get(user=self.staff).enabled)
            self.assertTrue(SyntheticSupportStaffGrant.objects.filter(user=self.staff,fulfilment=self.grant).exists())

    def test_failure_rolls_back_credentials_grants_sessions_and_recovery_history(self):
        selected=uuid.uuid4();epoch=AccessEpoch.objects.get().value
        generation=self.credential.generation;sessions=list(Session.objects.order_by('session_key').values())
        def fail_after_one_removal(*,user_id):
            StaffQuotationGrant.objects.all().delete()
            raise AccessRecoveryError('synthetic_reset_failure')
        with override_settings(LOCAL_RESTORE_ID=selected),patch('shop.access.recovery.revoke_staff_resource_grants',side_effect=fail_after_one_removal):
            with self.assertRaisesMessage(AccessRecoveryError,'synthetic_reset_failure'):self.operation(request_id=selected)
        self.assertEqual(self.counts(),dict.fromkeys(self.scopes,2))
        self.credential.refresh_from_db();self.assertTrue(self.credential.enabled);self.assertEqual(self.credential.generation,generation)
        self.assertEqual(AccessEpoch.objects.get().value,epoch);self.assertFalse(AccessEpoch.objects.get().quarantined)
        self.assertEqual(list(Session.objects.order_by('session_key').values()),sessions)
        self.assertEqual(LocalAccessRecoveryOperation.objects.count(),0);self.assertEqual(self.history(),self.original)

    def test_operator_reset_and_revoke_remove_only_the_selected_users_all_seven_scopes(self):
        call_command('local_staff','reset',username=self.staff.username,capture_root=self.directory.name,stdout=StringIO())
        self.assertEqual(self.counts(self.staff),dict.fromkeys(self.scopes,0))
        self.assertEqual(self.counts(self.second),dict.fromkeys(self.scopes,1))
        self.assertTrue(StaffCredential.objects.get(user=self.staff).enabled)
        call_command('local_staff','revoke',username=self.second.username,stdout=StringIO())
        self.assertEqual(self.counts(),dict.fromkeys(self.scopes,0))
        self.assertFalse(StaffCredential.objects.get(user=self.second).enabled)
        self.assertTrue(StaffCredential.objects.get(user=self.staff).enabled)
        self.assertEqual(self.history(),self.original)

    def test_shared_removal_requires_local_fake_transaction_and_rolls_back_with_caller(self):
        with self.assertRaisesMessage(ValueError,'local_staff_reset_unavailable'):revoke_staff_resource_grants(user_id=None)
        for values in ({'SHOP_ENV':'production'},{'LIVE_PAYMENTS_ENABLED':True},{'MAIL_ADAPTER':'smtp'}):
            with override_settings(**values),transaction.atomic():
                with self.assertRaisesMessage(ValueError,'local_staff_reset_unavailable'):revoke_staff_resource_grants(user_id=None)
        with transaction.atomic():
            self.assertEqual(revoke_staff_resource_grants(user_id=self.staff.pk),dict(dict.fromkeys(self.scopes,1),shb_order=0,shb_invitation=0,shb_invitation_issue=0,shb_discount=0))
            transaction.set_rollback(True)
        self.assertEqual(self.counts(),dict.fromkeys(self.scopes,2))
