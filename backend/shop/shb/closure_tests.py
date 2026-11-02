"""Only proved pre-dispatch closure may free a coupon; uncertainty stays held."""
from datetime import timedelta
from threading import Event,Thread
from pathlib import Path
from unittest.mock import patch
import json,time,uuid
from django.core import signing
from django.db import DatabaseError,transaction,connections
from django.test import TransactionTestCase,override_settings
from django.utils import timezone
from shop.adapters.evidence_archive import PreparedArchive,ArchiveError
from shop.catalog import checkout_payment as payment
from shop.payments.models import SyntheticBankOperation
from .checkout_tests import CheckoutTests as Fixture


@override_settings(SHB_SYNTHETIC_FIXTURE=True)
class ClosureTests(TransactionTestCase):
    client_class=Fixture.client_class
    setUp=Fixture.setUp
    review=Fixture.review
    checkout=Fixture.checkout
    saved=Fixture.saved
    acceptance=Fixture.acceptance

    def prepare(self,*,short=False):
        from .discounts import issue_fixture
        self.code,self.raw=issue_fixture(customer=self.customer,issuer=self.issuer,percentage_bps=1000,fpga_allowed=True,asic_allowed=True)
        data,token=self.review(discount_code=self.raw)
        if short:
            from .checkout import SALT
            value=signing.loads(token,salt=SALT);at=timezone.now()
            value.update(review_expires_at=(at+timedelta(seconds=3)).isoformat(),order_payment_expires_at=(at+timedelta(seconds=5)).isoformat())
            token=signing.dumps(value,salt=SALT)
        response=self.checkout(data,token);self.assertEqual(response.status_code,302)
        self.path=response['Location']

    def test_cancel_releases_once_and_cannot_reopen_original_checkout(self):
        from .models import CheckoutClosure,DiscountReservation
        self.prepare()
        for _ in range(2):self.assertEqual(self.client.post(self.path,{'action':'cancel'},secure=True).status_code,200)
        self.assertEqual(CheckoutClosure.objects.count(),1)
        self.assertIsNotNone(CheckoutClosure.objects.get().applied_at)
        self.assertEqual(DiscountReservation.objects.get().state,'released')
        self.assertEqual(self.client.post(self.path,{'action':'pay'},secure=True).status_code,409)
        self.assertFalse(SyntheticBankOperation.objects.exists())
        from .tests import form_data
        self.assertEqual(self.client.post('/purchase/simple/',form_data(variant='shb-asic-25h',assistance='Help',action='submit',discount_code=self.raw),secure=True).status_code,200)
        self.assertEqual(DiscountReservation.objects.filter(state='reserved').count(),1)
        self.assertEqual(self.client.post(self.path,{'action':'pay'},secure=True).status_code,409)

    def test_archive_failure_holds_coupon_and_payment_until_worker_completion_after_revocation(self):
        from .models import CheckoutClosure,DiscountReservation,Invitation
        from shop.worker.services import execute_once
        self.prepare();original=PreparedArchive.publish
        def fail(archive,identity,body):
            if json.loads(body).get('kind')=='shb-checkout-closure':raise ArchiveError('owned fixture archive failure')
            return original(archive,identity,body)
        with patch.object(PreparedArchive,'publish',fail):
            self.assertEqual(self.client.post(self.path,{'action':'cancel'},secure=True).status_code,503)
        self.assertIsNone(CheckoutClosure.objects.get().applied_at)
        self.assertEqual(DiscountReservation.objects.get().state,'reserved')
        self.assertEqual(self.client.post(self.path,{'action':'pay'},secure=True).status_code,409)
        Invitation.objects.filter(pk=self.invitation.pk).update(revoked_at=timezone.now())
        self.assertTrue(execute_once())
        self.assertIsNotNone(CheckoutClosure.objects.get().applied_at)
        self.assertEqual(DiscountReservation.objects.get().state,'released')
        self.assertFalse(SyntheticBankOperation.objects.exists())
        self.assertEqual(self.client.get(self.path,secure=True).status_code,403)

    def test_prepared_attempt_is_stopped_without_bank_dispatch_before_coupon_release(self):
        from .models import DiscountReservation
        from shop.payments import attempts
        self.prepare()
        with patch('shop.catalog.checkout_payment.attempts.dispatch',return_value=None):
            self.assertEqual(self.client.post(self.path,{'action':'pay'},secure=True).status_code,200)
        self.assertEqual(self.acceptance().attempt.state,'prepared')
        self.assertEqual(self.client.post(self.path,{'action':'cancel'},secure=True).status_code,200)
        self.assertEqual(self.acceptance().attempt.state,'cancelled')
        self.assertEqual(DiscountReservation.objects.get().state,'released')
        with PreparedArchive(Path(self.directory.name)) as archive:
            attempts.dispatch(self.acceptance().attempt_id,archive)
        self.assertFalse(SyntheticBankOperation.objects.exists())

    def test_uncertain_or_captured_payment_cannot_be_closed_or_free_its_concession(self):
        from .models import CheckoutClosure,DiscountReservation
        self.prepare();original=payment.pay
        with patch('shop.catalog.checkout_payment.pay',side_effect=lambda *a,**k:original(*a,fault='after_commit',**k)):
            self.assertEqual(self.client.post(self.path,{'action':'pay'},secure=True).status_code,409)
        self.assertEqual(self.client.post(self.path,{'action':'cancel'},secure=True).status_code,409)
        self.assertEqual(DiscountReservation.objects.get().state,'reserved')
        self.assertFalse(CheckoutClosure.objects.exists())
        self.assertEqual(self.client.post(self.path,{'action':'reconcile'},secure=True).status_code,200)
        self.assertEqual(self.client.post(self.path,{'action':'cancel'},secure=True).status_code,409)
        self.assertEqual(DiscountReservation.objects.get().state,'consumed')
        self.assertFalse(CheckoutClosure.objects.exists());self.assertEqual(SyntheticBankOperation.objects.count(),1)

    def test_expired_prepared_attempt_releases_only_after_server_deadline_and_cannot_dispatch(self):
        from . import closures
        from .models import DiscountReservation,CheckoutClosure
        from shop.worker.services import execute_once
        from shop.catalog.checkout import CheckoutError
        self.prepare(short=True)
        with patch('shop.catalog.checkout_payment.attempts.dispatch',return_value=None):
            self.assertEqual(self.client.post(self.path,{'action':'pay'},secure=True).status_code,200)
        with PreparedArchive(Path(self.directory.name)) as archive:
            with self.assertRaises(CheckoutError):closures.expire(self.customer,self.saved().pk,archive)
        self.assertFalse(CheckoutClosure.objects.exists())
        time.sleep(5.1)
        self.assertTrue(execute_once())
        self.assertEqual(self.acceptance().attempt.state,'expired')
        self.assertEqual(DiscountReservation.objects.get().state,'released')
        self.assertFalse(SyntheticBankOperation.objects.exists())
        self.assertEqual(self.client.post(self.path,{'action':'pay'},secure=True).status_code,409)

    def test_closure_sql_is_immutable_and_release_requires_applied_matching_receipt(self):
        from .models import CheckoutClosure,DiscountReservation
        self.prepare()
        with self.assertRaises(DatabaseError),transaction.atomic():DiscountReservation.objects.all().update(state='released')
        self.assertEqual(self.client.post(self.path,{'action':'cancel'},secure=True).status_code,200)
        for rows,changes in [(CheckoutClosure.objects.all(),{'payload':{}}),(CheckoutClosure.objects.all(),{'applied_at':None}),
                (DiscountReservation.objects.all(),{'state':'reserved','release_closure':None})]:
            with self.assertRaises(DatabaseError),transaction.atomic():rows.update(**changes)

    def test_cancel_needs_same_session_csrf_and_is_never_a_get_effect(self):
        from .models import CheckoutClosure,DiscountReservation
        self.prepare()
        self.assertEqual(self.client.get(self.path+'?action=cancel',secure=True).status_code,400)
        self.assertFalse(CheckoutClosure.objects.exists());self.assertEqual(DiscountReservation.objects.get().state,'reserved')
        other=self.client_class();other.get('/invite/'+self.token,secure=True)
        self.assertEqual(other.post(self.path,{'action':'cancel'},secure=True).status_code,404)
        csrf=self.client_class(enforce_csrf_checks=True);csrf.cookies=self.client.cookies.copy()
        self.assertEqual(csrf.post(self.path,{'action':'cancel'},secure=True,HTTP_ORIGIN='https://localhost').status_code,403)
        self.assertFalse(CheckoutClosure.objects.exists())

    def race_payment(self,entered,release):
        values=[];cookies=self.client.cookies.copy()
        def run():
            try:
                client=self.client_class();client.cookies=cookies.copy()
                values.append(client.post(self.path,{'action':'pay'},secure=True).status_code)
            except BaseException as error:values.append(error)
            finally:connections.close_all()
        thread=Thread(target=run);thread.start()
        self.addCleanup(lambda:release.set())
        return thread,values

    def test_cancel_wins_before_bank_claim_and_racing_dispatch_cannot_spend_released_coupon(self):
        from .models import DiscountReservation,CheckoutClosure
        self.prepare();entered=Event();release=Event();original=PreparedArchive.publish
        def paused(archive,identity,body):
            receipt=original(archive,identity,body)
            if json.loads(body).get('kind')=='synthetic-payment-attempt':
                entered.set()
                if not release.wait(8):raise RuntimeError('bounded fixture wait expired')
            return receipt
        with patch.object(PreparedArchive,'publish',paused):
            thread,values=self.race_payment(entered,release)
            try:
                self.assertTrue(entered.wait(8))
                self.assertEqual(self.client.post(self.path,{'action':'cancel'},secure=True).status_code,200)
            finally:release.set();thread.join(10)
        self.assertFalse(thread.is_alive());self.assertEqual(values,[409])
        self.assertEqual(DiscountReservation.objects.get().state,'released')
        self.assertIsNotNone(CheckoutClosure.objects.get().applied_at)
        self.assertFalse(SyntheticBankOperation.objects.exists())

    def test_bank_claim_wins_and_racing_cancel_cannot_free_uncertain_concession(self):
        from .models import DiscountReservation,CheckoutClosure,PaidOrder
        from shop.payments import synthetic_bank
        self.prepare();entered=Event();release=Event();original=synthetic_bank.start
        def paused(*args,**kwargs):
            entered.set()
            if not release.wait(8):raise RuntimeError('bounded fixture wait expired')
            return original(*args,**kwargs)
        with patch('shop.payments.synthetic_bank.start',side_effect=paused):
            thread,values=self.race_payment(entered,release)
            try:
                self.assertTrue(entered.wait(8))
                self.assertEqual(self.client.post(self.path,{'action':'cancel'},secure=True).status_code,409)
                self.assertEqual(DiscountReservation.objects.get().state,'reserved')
            finally:release.set();thread.join(10)
        self.assertFalse(thread.is_alive());self.assertEqual(values,[200])
        self.assertFalse(CheckoutClosure.objects.exists());self.assertEqual(PaidOrder.objects.count(),1)
        self.assertEqual(DiscountReservation.objects.get().state,'consumed')
        self.assertEqual(SyntheticBankOperation.objects.count(),1)
