"""Real-PG staff-scoped synthetic capture/refund; actual financial authority stays closed."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from io import StringIO
from threading import Barrier
from unittest.mock import patch
from urllib.parse import urlencode
import json
import uuid
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import connections,transaction,IntegrityError,connection
from django.test import TransactionTestCase,RequestFactory,Client,override_settings
from django.utils import timezone
from shop.access.models import StaffCredential
from shop.adapters.evidence_archive import ArchiveError
from shop.catalog import checkout_payment_tests as fixture,checkout_payment as payment,checkout,fulfilment,support_ledger as ledger
from shop.catalog.models import SyntheticCheckoutAcceptance as Acceptance,SyntheticFulfilment,SyntheticLineEntitlement,SyntheticSupportEvent
from . import operations as service,attempts,observations,synthetic_bank,notifications
from .bank_contract import BankError,BankMutationResult
from .models import (SyntheticPaymentStaffGrant as StaffGrant,SyntheticPaymentOperation as Operation,
    SyntheticOperationDispatch as Dispatch,SyntheticOperationResult as Result,SyntheticBankTransition as Transition,
    SyntheticPaymentObservation as Observation,SyntheticBankOperation)


class OperationTests(TransactionTestCase):
    save_cart=fixture.CheckoutPaymentTests.save_cart
    preview=fixture.CheckoutPaymentTests.preview
    accept=fixture.CheckoutPaymentTests.accept

    def setUp(self):
        fixture.CheckoutPaymentTests.setUp(self);self.accept()
        payment.pay(self.owner,self.saved.pk,self.archive,outcome='authorized')
        self.accepted=Acceptance.objects.get(checkout=self.saved)
        self.staff=get_user_model().objects.create_user(username='finance-staff',is_staff=True)
        self.credential=StaffCredential.objects.create(user=self.staff)
        self.scope=StaffGrant.objects.create(user=self.staff,acceptance=self.accepted,kind='capture')
        self.refund_scope=StaffGrant.objects.create(user=self.staff,acceptance=self.accepted,kind='refund')
        setting=override_settings(LOCAL_STAFF_ENABLED=True,ALLOWED_HOSTS=['staff.localhost','testserver'],LOCAL_CHECKOUT_ARCHIVE_ROOT=self.directory.name)
        setting.enable();self.addCleanup(setting.disable)
        self.request=RequestFactory().get('/staff/payments/',HTTP_HOST='staff.localhost');self.request.user=self.staff
        self.request.session={'shop_staff_mfa':{'generation':str(self.credential.generation),'verified_at':timezone.now().timestamp()}}
        from shop.access.recovery import stamp_session_epoch
        stamp_session_epoch(None,self.request,self.staff)  # Explicit trusted post-MFA fixture.

    def prepare(self,kind='capture',key=None):return service.prepare(self.request,self.accepted.pk,kind,key or uuid.uuid4(),self.archive)
    def dispatch(self,row,**kw):return service.dispatch(self.request,row.pk,self.archive,**kw)
    def reconcile(self,row):return service.reconcile(self.request,row.pk,self.archive)
    def inspect(self,row):return service.inspect(self.request,row.pk,self.archive)
    def capture(self):row=self.prepare();self.dispatch(row);return row
    def refund(self):row=self.prepare('refund');self.dispatch(row);return row
    def current(self):return payment.accepted(self.owner,self.saved.pk).attempt

    def test_authorized_capture_and_refund_retain_original_facts_and_grants_once(self):
        with self.assertRaises(checkout.CheckoutError):fulfilment.provision(self.owner,self.saved.pk,self.archive)
        self.capture();grant=fulfilment.provision(self.owner,self.saved.pk,self.archive)
        ledger.record(self.owner,self.saved.pk,uuid.uuid4(),'reserve',self.archive,seconds=60,task_id=uuid.uuid4())
        before=ledger.read(self.owner,self.saved.pk,self.archive);refund=self.refund()
        self.assertEqual(self.current().provider_status,'refunded')
        self.assertEqual(fulfilment.provision(self.owner,self.saved.pk,self.archive).pk,grant.pk)
        self.assertEqual(ledger.read(self.owner,self.saved.pk,self.archive),before)
        initial=fulfilment.deliver(self.owner,self.saved.pk,uuid.UUID(self.ip['id']),'initial',self.archive)
        self.assertEqual(fulfilment.deliver(self.owner,self.saved.pk,uuid.UUID(self.ip['id']),'initial',self.archive).pk,initial.pk)
        self.assertEqual(SyntheticFulfilment.objects.count(),1);self.assertEqual(SyntheticLineEntitlement.objects.count(),1)
        self.assertEqual(Transition.objects.count(),2);self.assertEqual(SyntheticBankOperation.objects.count(),1)
        self.assertEqual([r.payload['observation']['status'] for r in Observation.objects.order_by('revision')],['authorized','captured','refunded'])
        self.assertTrue(all(value is None for value in self.inspect(refund)['financial_policy'].values()))
        self.assertFalse(self.inspect(refund)['effects_authorized']);self.assertEqual(SyntheticSupportEvent.objects.count(),1)

    def test_refund_before_any_grant_cannot_create_new_entitlement(self):
        self.capture();self.refund()
        with self.assertRaises(checkout.CheckoutError):fulfilment.provision(self.owner,self.saved.pk,self.archive)
        self.assertEqual(SyntheticFulfilment.objects.count(),0)

    def test_prepare_exact_retry_conflict_and_capture_vs_refund_scope(self):
        key=uuid.uuid4();row=self.prepare(key=key)
        self.assertEqual(self.prepare(key=key).pk,row.pk)
        with self.assertRaises(checkout.CheckoutError):self.prepare()
        self.scope.delete()
        with self.assertRaises(checkout.CheckoutError):self.dispatch(row)
        self.assertEqual(Dispatch.objects.get(operation=row).state,'prepared');self.assertEqual(Transition.objects.count(),0)

    def test_archive_before_dispatch_and_no_bank_io_under_transaction(self):
        row=self.prepare();original=synthetic_bank.mutate
        def checking(command,**kw):
            self.assertFalse(connection.in_atomic_block)
            self.assertEqual(Dispatch.objects.get(operation=row).state,'uncertain')
            with transaction.atomic(durable=True):
                accepted,attempt,_=service.scope_locked(self.request,row.acceptance_id,row.kind,self.archive)
                service.retained(row,accepted,attempt,self.archive)
            return original(command,**kw)
        with patch.object(synthetic_bank,'mutate',side_effect=checking):self.dispatch(row)
        self.assertEqual(self.inspect(row)['state'],'observed')

    def test_archive_outage_prevents_intent_and_post_capture_observation_publication(self):
        with patch.object(self.archive,'publish',side_effect=ArchiveError('offline')):
            with self.assertRaises(ArchiveError):self.prepare()
        self.assertEqual(Operation.objects.count(),0);row=self.prepare()
        with patch.object(self.archive,'publish',side_effect=ArchiveError('offline')):
            with self.assertRaises(ArchiveError):self.dispatch(row)
        self.assertEqual(self.inspect(row)['state'],'uncertain');self.assertEqual(self.current().provider_status,'authorized')
        self.assertEqual(Transition.objects.count(),1);self.assertEqual(Result.objects.count(),0)
        with patch.object(synthetic_bank,'mutate',side_effect=AssertionError('blind retry')):
            self.dispatch(row);self.reconcile(row)
        self.assertEqual(self.current().provider_status,'captured');self.assertEqual(Result.objects.count(),1)

    def test_timeout_before_commit_never_permits_second_operation_dispatch(self):
        row=self.prepare()
        with self.assertRaises(TimeoutError):self.dispatch(row,fault='before_commit')
        with patch.object(synthetic_bank,'mutate',side_effect=AssertionError('blind retry')):
            self.dispatch(row);self.reconcile(row)
        self.assertEqual(self.inspect(row)['state'],'uncertain');self.assertEqual(Transition.objects.count(),0)

    def test_timeout_after_commit_lookup_recovers_and_duplicate_lookup_is_once(self):
        row=self.prepare()
        with self.assertRaises(TimeoutError):self.dispatch(row,fault='after_commit')
        self.assertEqual(Transition.objects.count(),1);self.assertEqual(self.current().provider_status,'authorized')
        self.reconcile(row);self.reconcile(row)
        self.assertEqual(Result.objects.count(),1);self.assertEqual(Observation.objects.count(),2)
        self.assertFalse(self.inspect(row)['retry_authorized'])

    def test_refund_uncertainty_preserves_capture_and_lookup_recovers(self):
        self.capture();row=self.prepare('refund')
        with self.assertRaises(TimeoutError):self.dispatch(row,fault='after_commit')
        self.assertEqual(self.current().provider_status,'captured');self.reconcile(row)
        self.assertEqual(self.current().provider_status,'refunded');self.assertEqual(Transition.objects.count(),2)

    def test_known_reordered_authorization_and_capture_do_not_downgrade_refund(self):
        initial=synthetic_bank.lookup(self.current().merchant,self.current().reference)
        capture=self.capture();captured=synthetic_bank.lookup(self.current().merchant,self.current().reference);self.refund()
        attempts._record(self.current().pk,initial,self.archive);attempts._record(self.current().pk,captured,self.archive)
        self.reconcile(capture)
        self.assertEqual(self.current().provider_status,'refunded');self.assertEqual(Observation.objects.count(),3)
        start=synthetic_bank.start(attempts.request_for(self.current()),outcome='authorized')
        self.assertEqual(start.status,'authorized')

    def test_wrong_result_identity_amount_or_kind_cannot_confirm_operation(self):
        row=self.prepare()
        with self.assertRaises(TimeoutError):self.dispatch(row,fault='after_commit')
        result=synthetic_bank.lookup_mutation(service.mutation(row))
        for wrong in (replace(result,request=replace(result.request,kind='refund')),
                      replace(result,observation=replace(result.observation,amount_minor=1)),{'status':'captured'}):
            with self.assertRaises(checkout.CheckoutError):service.record(self.request,row.pk,wrong,self.archive)
        self.assertEqual(Result.objects.count(),0);self.assertEqual(self.current().provider_status,'authorized')

    def test_database_failure_after_prepared_result_recovers_exact_receipts(self):
        row=self.prepare()
        with patch.object(Result.objects,'create',side_effect=IntegrityError('injected')):
            with self.assertRaises(IntegrityError):self.dispatch(row)
        self.assertEqual(self.current().provider_status,'authorized');self.assertEqual(self.inspect(row)['state'],'uncertain')
        self.reconcile(row);self.assertEqual(Result.objects.count(),1)

    def test_competing_dispatchers_commit_one_mutation(self):
        row=self.prepare();barrier=Barrier(2)
        def action(_):
            try:barrier.wait(timeout=10);return self.dispatch(row).pk
            finally:connections.close_all()
        with patch.object(synthetic_bank,'mutate',wraps=synthetic_bank.mutate) as mutate:
            with ThreadPoolExecutor(2) as pool:values=list(pool.map(action,range(2)))
        self.assertEqual(values,[row.pk,row.pk]);self.assertEqual(mutate.call_count,1)
        self.assertEqual(Transition.objects.count(),1);self.assertEqual(Result.objects.count(),1)

    def test_mfa_expiry_generation_and_revocation_are_enforced(self):
        row=self.prepare();old=self.request.session['shop_staff_mfa'].copy()
        for marker in ({**old,'verified_at':old['verified_at']-301},{**old,'generation':str(uuid.uuid4())}):
            self.request.session['shop_staff_mfa']=marker
            with self.assertRaises(checkout.CheckoutError):self.dispatch(row)
        self.request.session['shop_staff_mfa']=old
        call_command('local_staff','revoke-payment',username=self.staff.username,acceptance=str(self.accepted.pk),operation_kind='capture',stdout=StringIO())
        with self.assertRaises(checkout.CheckoutError):self.inspect(row)
        self.assertEqual(Transition.objects.count(),0)

    def test_sql_intents_results_and_provider_transition_are_immutable(self):
        self.capture()
        for model in (Operation,Result,Transition):
            with self.assertRaises(IntegrityError),transaction.atomic():model.objects.all().delete()
        with self.assertRaises(IntegrityError),transaction.atomic():Operation.objects.all().update(sha256='0'*64)

    def test_http_scoped_forms_and_csrf_origin_closed_inputs(self):
        with override_settings(ROOT_URLCONF='shop.staff_urls'):
            browser=Client(enforce_csrf_checks=True,HTTP_HOST='staff.localhost');browser.force_login(self.staff)
            session=browser.session;session['shop_staff_mfa']=self.request.session['shop_staff_mfa'];session.save()
            path=f'/staff/payments/{self.scope.pk}/';self.assertEqual(browser.get(path).status_code,200)
            value={'action':'prepare','request_id':str(uuid.uuid4())}
            self.assertEqual(browser.post(path,data=urlencode(value),content_type='application/x-www-form-urlencoded').status_code,403)
            token=browser.cookies['csrftoken'].value;headers={'HTTP_X_CSRFTOKEN':token,'HTTP_ORIGIN':'http://staff.localhost'}
            self.assertEqual(browser.post(path,data=urlencode(value),content_type='application/x-www-form-urlencoded',**headers).status_code,303)
            self.assertEqual(browser.post(path,{'action':'dispatch'},HTTP_X_CSRFTOKEN=token,HTTP_ORIGIN='null').status_code,403)
            self.assertEqual(browser.post(path,data=urlencode({'action':'dispatch','amount':1}),content_type='application/x-www-form-urlencoded',**headers).status_code,400)
            self.assertEqual(browser.post(path,data=urlencode({'action':'dispatch'}),content_type='application/x-www-form-urlencoded',**headers).status_code,303)
            result=browser.get(path,HTTP_ACCEPT='application/json');self.assertIn('no-store',result['Cache-Control'])
            self.assertNotIn(str(self.current().provider_operation_id),result.content.decode())
            self.scope.delete();self.assertEqual(browser.get(path).status_code,404)

    def test_production_and_live_modes_remain_closed(self):
        for setting in ({'SHOP_ENV':'production'},{'LIVE_PAYMENTS_ENABLED':True}):
            with override_settings(**setting),self.assertRaises(BankError):self.prepare()
        self.assertEqual(Operation.objects.count(),0)

    def test_new_process_recovers_uncertain_operation_without_another_mutation(self):
        import os,subprocess,sys
        from pathlib import Path
        row=self.prepare()
        with self.assertRaises(TimeoutError):self.dispatch(row,fault='after_commit')
        env=os.environ.copy();env['DATABASE_NAME']=connections['default'].settings_dict['NAME']
        code="""import django,uuid
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from shop.access.models import StaffCredential
from shop.adapters.evidence_archive import PreparedArchive
from shop.payments import operations
from django.test import override_settings,RequestFactory
user=get_user_model().objects.get(pk=%s);credential=StaffCredential.objects.get(user=user)
request=RequestFactory().get('/staff/payments/',HTTP_HOST='staff.localhost');request.user=user
request.session={'shop_staff_mfa':{'generation':str(credential.generation),'verified_at':timezone.now().timestamp()}}
from shop.access.recovery import stamp_session_epoch
stamp_session_epoch(None,request,user)
with override_settings(LOCAL_STAFF_ENABLED=True,ALLOWED_HOSTS=['staff.localhost']):
 with PreparedArchive(Path(%r)) as archive:
  with patch('shop.payments.synthetic_bank.mutate',side_effect=AssertionError('blind retry')):
   operations.reconcile(request,uuid.UUID('%s'),archive)
""" % (self.staff.pk,self.directory.name,row.pk)
        result=subprocess.run([sys.executable,'manage.py','shell','--no-imports','-c',code],env=env,
            cwd=Path(__file__).resolve().parents[2],capture_output=True,timeout=20)
        self.assertEqual(result.returncode,0);self.assertEqual(self.inspect(row)['state'],'observed')
        self.assertEqual(Transition.objects.count(),1);self.assertEqual(Result.objects.count(),1)

    def test_expired_mfa_after_archive_wait_cannot_commit_intent(self):
        publish=self.archive.publish;old=self.request.session['shop_staff_mfa'].copy()
        def expired(identity,body):
            result=publish(identity,body)
            self.request.session['shop_staff_mfa']={**old,'verified_at':old['verified_at']-301}
            return result
        with patch.object(self.archive,'publish',side_effect=expired),self.assertRaises(checkout.CheckoutError):self.prepare()
        self.assertEqual(Operation.objects.count(),0);self.assertEqual(Dispatch.objects.count(),0)

    def test_unknown_stale_observation_and_cross_kind_request_replay_denied(self):
        key=uuid.uuid4();capture=self.prepare(key=key);self.dispatch(capture)
        with self.assertRaises(checkout.CheckoutError):self.prepare('refund',key)
        current=self.current();captured=synthetic_bank.lookup(current.merchant,current.reference)
        with self.assertRaises(BankError):attempts._record(current.pk,replace(captured,status='pending'),self.archive)
        self.assertEqual(self.current().provider_status,'captured')

    def test_http_timeout_requires_lookup_without_another_mutation(self):
        row=self.prepare()
        with override_settings(ROOT_URLCONF='shop.staff_urls'):
            browser=Client(enforce_csrf_checks=True,HTTP_HOST='staff.localhost');browser.force_login(self.staff)
            session=browser.session;session['shop_staff_mfa']=self.request.session['shop_staff_mfa'];session.save()
            path=f'/staff/payments/{self.scope.pk}/';self.assertEqual(browser.get(path).status_code,200)
            headers={'HTTP_X_CSRFTOKEN':browser.cookies['csrftoken'].value,'HTTP_ORIGIN':'http://staff.localhost'}
            original=synthetic_bank.mutate
            def lost(command,**options):return original(command,fault='after_commit')
            with patch.object(synthetic_bank,'mutate',side_effect=lost):
                result=browser.post(path,data=json.dumps({'action':'dispatch'}),content_type='application/json',**headers)
            self.assertEqual(result.status_code,409)
            self.assertEqual(result.json(),{'error':'payment_operation_uncertain_use_lookup'})
            self.assertEqual(Dispatch.objects.get(operation=row).state,'uncertain')
            self.assertEqual(self.current().provider_status,'authorized')
            with patch.object(synthetic_bank,'mutate',side_effect=AssertionError('blind HTTP retry')):
                for action in ('dispatch','reconcile'):
                    result=browser.post(path,data=json.dumps({'action':action}),content_type='application/json',**headers)
                    self.assertEqual(result.status_code,200)
                    self.assertEqual(result.json()['operation']['state'],'uncertain' if action=='dispatch' else 'observed')
            self.assertEqual(self.current().provider_status,'captured')
            self.assertEqual(Transition.objects.count(),1);self.assertEqual(Result.objects.count(),1)
