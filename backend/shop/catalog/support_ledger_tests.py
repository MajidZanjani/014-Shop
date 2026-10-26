"""Real PostgreSQL support accounting, archive gates, exact retries and staff scope."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from types import SimpleNamespace
from unittest.mock import patch
import uuid
from django.contrib.auth import get_user_model
from django.db import connections, transaction, IntegrityError
from django.test import TransactionTestCase, RequestFactory, override_settings
from django.utils import timezone
from shop.access.models import StaffCredential
from shop.adapters.evidence_archive import ArchiveError
from . import support_ledger as ledger, fulfilment, checkout, checkout_payment_tests as fixture
from .models import SyntheticSupportEvent, SyntheticSupportStaffGrant


class SupportLedgerTests(TransactionTestCase):
    save_cart=fixture.CheckoutPaymentTests.save_cart
    preview=fixture.CheckoutPaymentTests.preview
    accept=fixture.CheckoutPaymentTests.accept

    def setUp(self):
        fixture.CheckoutPaymentTests.setUp(self)
        self.accept()
        from . import checkout_payment
        checkout_payment.pay(self.owner,self.saved.pk,self.archive)
        self.grant=fulfilment.provision(self.owner,self.saved.pk,self.archive)
        self.staff=get_user_model().objects.create_user(username='support-staff',is_staff=True)
        self.credential=StaffCredential.objects.create(user=self.staff)
        SyntheticSupportStaffGrant.objects.create(user=self.staff,fulfilment=self.grant)
        self.settings=override_settings(LOCAL_STAFF_ENABLED=True,ALLOWED_HOSTS=['staff.localhost','testserver'])
        self.settings.enable();self.addCleanup(self.settings.disable)
        self.request=RequestFactory().get('/staff/support/',HTTP_HOST='staff.localhost')
        self.request.user=self.staff
        self.request.session={'shop_staff_mfa':{'generation':str(self.credential.generation),'verified_at':timezone.now().timestamp()}}

    def record(self,kind,**kw):
        return ledger.record(self.owner,self.saved.pk,kw.pop('request_id',uuid.uuid4()),kind,self.archive,**kw)

    def reserve(self,seconds=3600,**kw):
        return self.record('reserve',seconds=seconds,task_id=kw.pop('task_id',uuid.uuid4()),**kw)

    def state(self):return ledger.read(self.owner,self.saved.pk,self.archive)

    def work(self,reservation,seconds=1800,**kw):
        return self.record('work',seconds=seconds,target_id=reservation.pk,staff_request=self.request,**kw)

    def test_reservation_retry_conflict_release_and_no_expiry(self):
        request_id=uuid.uuid4();task_id=uuid.uuid4()
        first=self.reserve(request_id=request_id,task_id=task_id)
        self.assertEqual(self.reserve(request_id=request_id,task_id=task_id).pk,first.pk)
        self.assertEqual(self.state()['available_seconds'],68400)
        with self.assertRaisesRegex(checkout.CheckoutError,'support_request_conflict'):
            self.reserve(7200,request_id=request_id,task_id=task_id)
        release_id=uuid.uuid4()
        release=self.record('release',target_id=first.pk,request_id=release_id)
        self.assertEqual(self.record('release',target_id=first.pk,request_id=release_id).pk,release.pk)
        self.assertEqual(self.state()['reserved_seconds'],0);self.assertEqual(self.state()['available_seconds'],72000)
        with self.assertRaisesRegex(checkout.CheckoutError,'support_reservation_unavailable'):
            self.record('release',target_id=first.pk)
        self.assertIsNone(self.state()['expires_at']);self.assertFalse(self.state()['actual_support_spendable'])

    def test_competing_reservations_cannot_double_allocate(self):
        barrier=Barrier(2)
        def run(_):
            try:
                barrier.wait(timeout=10)
                try:return self.reserve(50000).kind
                except checkout.CheckoutError as e:return str(e)
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:outcomes=list(pool.map(run,range(2)))
        self.assertCountEqual(outcomes,['reserve','support_credit_unavailable'])
        self.assertEqual(self.state()['reserved_seconds'],50000)
        self.assertEqual(SyntheticSupportEvent.objects.count(),1)

    def test_completion_spend_correction_and_statement_from_committed_revision(self):
        reservation=self.reserve(7200);work_id=uuid.uuid4();work=self.work(reservation,3600,request_id=work_id)
        self.assertEqual(self.work(reservation,3600,request_id=work_id).pk,work.pk)
        self.assertEqual(work.payload['completion'],{'simulated_completed':True,'actual_completion':False,'scope':'sll-xspi-mc'})
        self.assertEqual(self.state()['reserved_seconds'],3600);self.assertEqual(self.state()['spent_seconds'],3600)
        statement=self.record('statement',staff_request=self.request)
        self.assertEqual(statement.payload['statement']['revision'],2)
        self.assertEqual(statement.payload['statement']['spent_seconds'],3600)
        correction_id=uuid.uuid4()
        correction=self.record('correct',seconds=1800,target_id=work.pk,staff_request=self.request,request_id=correction_id)
        self.assertEqual(self.record('correct',seconds=1800,target_id=work.pk,staff_request=self.request,request_id=correction_id).pk,correction.pk)
        self.assertEqual(correction.payload['operations'],[{'kind':'reverse','event_id':str(work.pk),'seconds':3600},{'kind':'replace','seconds':1800}])
        self.assertEqual(self.state()['spent_seconds'],1800)
        self.assertEqual(self.state()['statements'][0]['statement']['spent_seconds'],3600)
        self.assertEqual(SyntheticSupportEvent.objects.get(pk=work.pk).payload['command']['seconds'],3600)
        with self.assertRaisesRegex(checkout.CheckoutError,'support_work_unavailable'):
            self.record('correct',seconds=0,target_id=work.pk,staff_request=self.request)
        self.record('correct',seconds=0,target_id=correction.pk,staff_request=self.request)
        self.assertEqual(self.state()['spent_seconds'],0)

    def test_correction_cannot_steal_reserved_seconds(self):
        reservation=self.reserve(72000);work=self.work(reservation,3600)
        with self.assertRaisesRegex(checkout.CheckoutError,'support_credit_unavailable'):
            self.record('correct',seconds=3601,target_id=work.pk,staff_request=self.request)
        self.assertEqual(self.state()['spent_seconds'],3600)

    def test_archive_failure_or_bad_readback_prevents_reservation_spend_and_statement(self):
        with patch.object(self.archive,'publish',side_effect=ArchiveError('unavailable')):
            with self.assertRaises(ArchiveError):self.reserve()
        self.assertEqual(SyntheticSupportEvent.objects.count(),0)
        reservation=self.reserve()
        for kind,kw in [('work',{'seconds':1800,'target_id':reservation.pk}),('statement',{})]:
            with patch.object(self.archive,'publish',side_effect=ArchiveError('unavailable')):
                with self.assertRaises(ArchiveError):self.record(kind,staff_request=self.request,**kw)
        self.assertEqual(self.state()['spent_seconds'],0)
        original=self.archive.recover
        def bad(receipt):
            return b'bad' if receipt.evidence_id==reservation.pk else original(receipt)
        with patch.object(self.archive,'recover',side_effect=bad):
            with self.assertRaisesRegex(checkout.CheckoutError,'archive_mismatch'):self.work(reservation)
        self.assertEqual(SyntheticSupportEvent.objects.count(),1)

    def test_archive_completion_is_recoverable_before_debit_and_failed_commit_retry(self):
        reservation=self.reserve();original=SyntheticSupportEvent.save
        def save(row,*a,**kw):
            if row.kind=='work':
                from . import checkout_payment
                checkout_payment.recover(self.archive,row.archive_receipt,row.pk,checkout.canonical(row.payload))
                self.assertEqual(SyntheticSupportEvent.objects.filter(kind='work').count(),0)
                raise RuntimeError('commit unavailable')
            return original(row,*a,**kw)
        key=uuid.uuid4()
        with patch.object(SyntheticSupportEvent,'save',save):
            with self.assertRaisesRegex(RuntimeError,'commit unavailable'):self.work(reservation,request_id=key)
        self.assertEqual(self.state()['spent_seconds'],0)
        self.assertEqual(self.work(reservation,request_id=key).kind,'work')

    def test_owner_scope_invalid_seconds_target_and_production_denied(self):
        from .tests import verified_login
        from django.test import Client
        verified_login(Client(),self.other)
        with self.assertRaisesRegex(checkout.CheckoutError,'not_found'):
            ledger.record(self.other,self.saved.pk,uuid.uuid4(),'reserve',self.archive,seconds=1,task_id=uuid.uuid4())
        for seconds in (True,0,-1,1.5,'1',9223372036854775808):
            with self.assertRaises(checkout.CheckoutError):self.reserve(seconds)
        with self.assertRaises(checkout.CheckoutError):self.record('release',target_id=uuid.uuid4())
        with self.assertRaises(checkout.CheckoutError):self.reserve(request_id='bad')
        with override_settings(SHOP_ENV='production'):
            from shop.payments.bank_contract import BankError
            with self.assertRaises(BankError):self.reserve()
        self.assertEqual(SyntheticSupportEvent.objects.count(),0)

    def test_recent_mfa_explicit_scope_and_revocation_required_even_for_retries(self):
        reservation=self.reserve();key=uuid.uuid4()
        with self.assertRaisesRegex(checkout.CheckoutError,'recent_staff_mfa_required'):
            self.record('work',seconds=1,target_id=reservation.pk)
        work=self.work(reservation,1,request_id=key)
        SyntheticSupportStaffGrant.objects.all().delete()
        with self.assertRaisesRegex(checkout.CheckoutError,'support_scope_required'):self.work(reservation,1,request_id=key)
        SyntheticSupportStaffGrant.objects.create(user=self.staff,fulfilment=self.grant)
        self.request.session['shop_staff_mfa']['verified_at']-=301
        with self.assertRaisesRegex(checkout.CheckoutError,'recent_staff_mfa_required'):self.work(reservation)
        self.request.session['shop_staff_mfa']['verified_at']=timezone.now().timestamp()
        StaffCredential.objects.filter(pk=self.credential.pk).update(enabled=False)
        with self.assertRaisesRegex(checkout.CheckoutError,'recent_staff_mfa_required'):self.work(reservation)
        self.assertEqual(self.state()['spent_seconds'],1)

    def test_event_history_cannot_be_updated_or_deleted_in_database(self):
        event=self.reserve()
        for mutation in (lambda:SyntheticSupportEvent.objects.filter(pk=event.pk).update(payload={}),
                         lambda:SyntheticSupportEvent.objects.filter(pk=event.pk).delete()):
            with self.assertRaises(IntegrityError),transaction.atomic():mutation()
        self.assertEqual(self.state()['revision'],1)

    def test_competing_work_and_corrections_cannot_double_spend_or_reverse_twice(self):
        reservation=self.reserve(3600);barrier=Barrier(2)
        def spend(_):
            try:
                barrier.wait(timeout=10)
                try:return str(self.work(reservation,2400).pk)
                except checkout.CheckoutError as e:return str(e)
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:outcomes=list(pool.map(spend,range(2)))
        self.assertEqual(outcomes.count('support_credit_unavailable'),1)
        work=SyntheticSupportEvent.objects.get(kind='work');barrier=Barrier(2)
        def correct(_):
            try:
                barrier.wait(timeout=10)
                try:return self.record('correct',seconds=1200,target_id=work.pk,staff_request=self.request).kind
                except checkout.CheckoutError as e:return str(e)
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:outcomes=list(pool.map(correct,range(2)))
        self.assertCountEqual(outcomes,['correct','support_work_unavailable'])
        self.assertEqual(self.state()['spent_seconds'],1200)
        self.assertEqual(self.state()['reserved_seconds'],1200)

    def test_customer_form_api_privacy_cross_owner_and_csrf(self):
        import json,re
        from urllib.parse import urlencode
        from django.test import Client
        from .tests import verified_login
        route=f'/purchase/checkout-rehearsal/{self.saved.pk}/support/'
        page=self.client.get(route)
        self.assertContains(page,'Simulate support reservation');self.assertEqual(page['Cache-Control'],'no-store')
        values={'action':'reserve','request_id':str(uuid.uuid4()),'task_id':str(uuid.uuid4()),'seconds':'3600'}
        for _ in range(2):
            response=self.client.post(route,data=urlencode(values),content_type='application/x-www-form-urlencoded')
            self.assertEqual(response.status_code,303)
        state=self.client.get(route,HTTP_ACCEPT='application/json').json()['ledger']
        self.assertEqual(state['reserved_seconds'],3600)
        text=json.dumps(state)
        for forbidden in ('staff_id','credential_generation','mfa_verified_at','archive_receipt','SYNTHETIC_BUSINESS_CANARY'):
            self.assertNotIn(forbidden,text)
        for value in (dict(values,seconds=True),dict(values,task_id=1),dict(values,amount=1),dict(values,action='work')):
            self.assertEqual(self.client.post(route,data=json.dumps(value),content_type='application/json').status_code,400)
        csrf=Client(enforce_csrf_checks=True);csrf.cookies=self.client.cookies.copy()
        self.assertEqual(csrf.post(route,data=urlencode(values),content_type='application/x-www-form-urlencoded').status_code,403)
        verified_login(self.client,self.other)
        self.assertEqual(self.client.get(route).status_code,404)
        with override_settings(SHOP_ENV='production'):self.assertEqual(self.client.get(route).status_code,404)

    def test_staff_routes_require_recent_mfa_grant_and_command_recovery_revokes_scope(self):
        import json
        from django.test import Client
        from django.core.management import call_command
        from shop.access.staff_tests import STAFF_SETTINGS
        reservation=self.reserve()
        route=f'/staff/support/{self.saved.pk}/'
        with override_settings(**STAFF_SETTINGS):
            browser=Client(HTTP_HOST='staff.localhost')
            self.assertEqual(browser.get(route).status_code,403)
            browser.force_login(self.staff)
            session=browser.session;session['shop_staff_mfa']=self.request.session['shop_staff_mfa'];session.save()
            self.assertContains(browser.get(route),'Simulate completed support work')
            self.assertEqual(browser.get('/purchase/assets/shop.css').status_code,200)
            value={'action':'work','request_id':str(uuid.uuid4()),'target_id':str(reservation.pk),'seconds':1800}
            result=browser.post(route,data=json.dumps(value),content_type='application/json')
            self.assertEqual(result.status_code,200,result.content)
            self.assertEqual(result.json()['ledger']['spent_seconds'],1800)
            self.assertEqual(browser.post(route,data=json.dumps(value),content_type='application/json').status_code,200)
            call_command('local_staff','revoke-support',username=self.staff.username,checkout=str(self.saved.pk),verbosity=0)
            self.assertEqual(browser.get(route).status_code,404)
            call_command('local_staff','grant-support',username=self.staff.username,checkout=str(self.saved.pk),verbosity=0)
            self.assertEqual(browser.get(route).status_code,200)
            call_command('local_staff','reset',username=self.staff.username,capture_root=str(self.root),verbosity=0)
            self.assertFalse(SyntheticSupportStaffGrant.objects.filter(user=self.staff).exists())
            self.assertEqual(browser.get(route).status_code,403)

    def test_mfa_expiry_during_archive_cannot_commit_work(self):
        reservation=self.reserve();publish=self.archive.publish
        def expire(identity,body):
            result=publish(identity,body)
            self.request.session['shop_staff_mfa']['verified_at']-=301
            return result
        with patch.object(self.archive,'publish',side_effect=expire):
            with self.assertRaisesRegex(checkout.CheckoutError,'recent_staff_mfa_required'):self.work(reservation)
        self.assertEqual(self.state()['spent_seconds'],0)
