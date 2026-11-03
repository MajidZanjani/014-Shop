"""Per-purchase paid state and ordinary notice; never support-time accounting."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path
from threading import Barrier
from unittest.mock import patch
import uuid

from django.contrib.auth import get_user_model
from django.db import DatabaseError, connections, transaction
from django.test import Client, TransactionTestCase, override_settings
from django.utils import timezone

from shop.adapters.evidence_archive import PreparedArchive, ArchiveError
from shop.catalog import checkout_payment as payment
from shop.catalog.checkout import CheckoutError
from .checkout_tests import CheckoutTests as Fixture


@override_settings(SHB_SYNTHETIC_FIXTURE=True)
class PaidOrderTests(TransactionTestCase):
    client_class=Fixture.client_class
    setUp=Fixture.setUp
    review=Fixture.review
    checkout=Fixture.checkout
    saved=Fixture.saved
    acceptance=Fixture.acceptance

    def pay(self,*,discount=False):
        if discount:
            from .discounts import issue_fixture
            self.code,self.raw=issue_fixture(customer=self.customer,issuer=self.issuer,
                percentage_bps=1000,fpga_allowed=True,asic_allowed=True)
            data,token=self.review(discount_code=self.raw)
        else:data,token=self.review()
        response=self.checkout(data,token);self.assertEqual(response.status_code,302)
        self.path=response['Location']
        response=self.client.post(self.path,{'action':'pay'},secure=True)
        self.assertEqual(response.status_code,200)
        from .models import PaidOrder
        return PaidOrder.objects.get()

    def test_one_order_coupon_and_notice_with_per_order_hours_and_original_reference(self):
        from .models import DiscountReservation,PaidOrder,PurchaseNoticeDelivery
        order=self.pay(discount=True)
        self.assertEqual(order.payload['order_reference'],str(self.acceptance().pk))
        self.assertEqual(order.payload['purchase']['hours_purchased'],30)
        self.assertEqual(order.payload['purchase']['quantity'],3)
        self.assertEqual(order.payload['support_tracking'],'manual-outside-shop')
        self.assertIs(order.payload['effects_authorized'],False)
        self.assertIs(order.payload['financial_confirmation'],False)
        self.assertEqual(DiscountReservation.objects.get().consumed_order_id,order.pk)
        self.assertEqual(DiscountReservation.objects.get().state,'consumed')
        self.assertEqual(PurchaseNoticeDelivery.objects.get().state,'pending')
        for _ in range(2):
            self.assertEqual(self.client.post(self.path,{'action':'pay'},secure=True).status_code,200)
            self.assertEqual(self.client.post(self.path,{'action':'reconcile'},secure=True).status_code,200)
        self.assertEqual(PaidOrder.objects.count(),1)
        self.assertEqual(PurchaseNoticeDelivery.objects.count(),1)
        from shop.catalog.models import SyntheticFulfilment,SyntheticSupportEvent
        self.assertFalse(SyntheticFulfilment.objects.exists());self.assertFalse(SyntheticSupportEvent.objects.exists())
        from .tests import form_data
        response=self.client.post('/purchase/simple/',form_data(variant='shb-asic-25h',assistance='Help',action='submit',discount_code=self.raw),secure=True)
        self.assertEqual(response.status_code,422)
        self.assertContains(self.client.get(self.path,secure=True),'Paid purchase recorded')

    def test_eligible_fpga_top_up_records_independent_paid_orders_per_invitation(self):
        from .invitations import issue_fixture
        from .models import PaidOrder,PurchaseNoticeDelivery
        from .tests import form_data
        from shop.catalog.models import SyntheticFulfilment,SyntheticSupportEvent
        first=self.pay()
        self.assertEqual(first.payload['purchase']['hours_purchased'],30)
        self.assertEqual(first.payload['purchase']['variant_id'],'shb-fpga-10h')
        _,token=issue_fixture(customer=self.customer,issuer=self.issuer,
            company_name='Synthetic Company Limited',project_reference='SLL top-up')
        self.assertNotEqual(token,self.token)
        self.client.get('/invite/'+token,secure=True)
        data=form_data(quantity='2',action='review',accept_terms='',privacy_acknowledged='')
        response=self.client.post('/purchase/simple/',data,secure=True)
        self.assertEqual(response.status_code,200)
        response=self.client.post('/purchase/simple/',dict(data,action='checkout',
            review_digest=response.context['review_digest'],accept_terms='on',privacy_acknowledged='on'),secure=True)
        self.assertEqual(response.status_code,302)
        self.assertNotEqual(response['Location'],self.path)
        self.assertEqual(self.client.post(response['Location'],{'action':'pay'},secure=True).status_code,200)
        orders=list(PaidOrder.objects.order_by('created_at'))
        self.assertEqual(len(orders),2);self.assertNotEqual(orders[0].pk,orders[1].pk)
        self.assertEqual(orders[0].payload['purchase']['hours_purchased'],30)
        self.assertEqual(orders[1].payload['purchase']['hours_purchased'],20)
        self.assertEqual(orders[0].payload['purchase']['quantity'],3)
        self.assertEqual(orders[1].payload['purchase']['quantity'],2)
        self.assertNotEqual(orders[0].payload['order_reference'],orders[1].payload['order_reference'])
        self.assertEqual(orders[0].payload['support_tracking'],'manual-outside-shop')
        self.assertEqual(orders[1].payload['support_tracking'],'manual-outside-shop')
        self.assertIs(orders[0].payload['effects_authorized'],False)
        self.assertIs(orders[1].payload['effects_authorized'],False)
        self.assertEqual(PurchaseNoticeDelivery.objects.count(),2)
        self.assertFalse(SyntheticFulfilment.objects.exists())
        self.assertFalse(SyntheticSupportEvent.objects.exists())

    def test_duplicate_pay_reconcile_and_worker_iterations_keep_one_order_and_one_reference(self):
        from . import purchase_mail
        from .models import DiscountReservation,PaidOrder,PurchaseNoticeCapture,PurchaseNoticeDelivery,TransactionNoticeCapture
        from shop.payments.models import SyntheticBankOperation
        from shop.worker.services import execute_once as worker_execute_once
        order=self.pay(discount=True)
        reservation_consumed=DiscountReservation.objects.get().consumed_order_id
        self.assertEqual(reservation_consumed,order.pk)
        for _ in range(3):
            self.assertEqual(self.client.post(self.path,{'action':'pay'},secure=True).status_code,200)
            self.assertEqual(self.client.post(self.path,{'action':'reconcile'},secure=True).status_code,200)
        self.assertEqual(PaidOrder.objects.count(),1)
        self.assertEqual(SyntheticBankOperation.objects.count(),1)
        self.assertEqual(DiscountReservation.objects.count(),1)
        reservation=DiscountReservation.objects.get()
        self.assertEqual(reservation.state,'consumed')
        self.assertEqual(reservation.consumed_order_id,reservation_consumed)
        self.assertEqual(PurchaseNoticeDelivery.objects.count(),1)
        notice_delivery_pk=PurchaseNoticeDelivery.objects.get().pk
        self.assertTrue(purchase_mail.execute_once())
        self.assertFalse(purchase_mail.execute_once())
        self.assertFalse(purchase_mail.execute_once())
        self.assertEqual(PurchaseNoticeCapture.objects.count(),1)
        self.assertEqual(PurchaseNoticeDelivery.objects.get().pk,notice_delivery_pk)
        while worker_execute_once():pass
        captures_after_first=TransactionNoticeCapture.objects.count()
        self.assertGreater(captures_after_first,0)
        for capture in TransactionNoticeCapture.objects.all():
            self.assertEqual(capture.notice.payload['body']['reference'],order.payload['order_reference'])
            self.assertIs(capture.notice.payload['actual_email_sent'],False)
        for _ in range(5):self.assertFalse(worker_execute_once())
        self.assertEqual(TransactionNoticeCapture.objects.count(),captures_after_first)
        self.assertEqual(PaidOrder.objects.count(),1)
        self.assertEqual(SyntheticBankOperation.objects.count(),1)
        self.assertEqual(DiscountReservation.objects.get().state,'consumed')
        self.assertEqual(DiscountReservation.objects.get().consumed_order_id,reservation_consumed)

    def test_payment_can_be_reconciled_after_invitation_expiry_without_new_checkout(self):
        from shop.catalog import checkout_payment
        from .models import PaidOrder,PaidOrderGrant
        from .tests import form_data
        from shop.payments.models import SyntheticPaymentAttempt
        response=self.checkout();self.assertEqual(response.status_code,302)
        path=response['Location']
        original=checkout_payment.pay
        def interrupted(*args,**kwargs):return original(*args,fault='after_commit',**kwargs)
        with patch('shop.catalog.checkout_payment.pay',side_effect=interrupted):
            self.assertEqual(self.client.post(path,{'action':'pay'},secure=True).status_code,409)
        self.assertEqual(SyntheticPaymentAttempt.objects.get().state,'uncertain')
        self.assertFalse(PaidOrder.objects.exists())
        saved_id=self.saved().pk
        future=self.invitation.expires_at+timedelta(days=1)
        with patch('shop.shb.invitations.now',return_value=future):
            self.assertEqual(self.client.get(path,secure=True).status_code,403)
            self.assertEqual(self.client.post(path,{'action':'pay'},secure=True).status_code,403)
            response=self.client.post('/purchase/simple/',form_data(action='submit',quantity='1'),secure=True)
            self.assertEqual(response.status_code,403)
            self.assertFalse(PaidOrder.objects.exists())
            with PreparedArchive(Path(self.directory.name)) as archive:
                result=checkout_payment.reconcile(self.customer,saved_id,archive)
            self.assertEqual(result.attempt.provider_status,'captured')
            self.assertEqual(PaidOrder.objects.count(),1)
        order=PaidOrder.objects.get()
        self.assertEqual(order.payload['purchase']['hours_purchased'],30)
        self.assertEqual(order.payload['purchase']['variant_id'],'shb-fpga-10h')
        staff_path=self.staff(order);PaidOrderGrant.objects.create(user=self.user,order=order)
        response=self.browser.get(staff_path)
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json()['purchase']['hours_purchased'],30)

    def test_forged_payment_success_fields_at_payment_page_cannot_mark_paid(self):
        from .models import PaidOrder,SupportCheckout
        from shop.payments.models import SyntheticPaymentAttempt,SyntheticBankOperation
        response=self.checkout();self.assertEqual(response.status_code,302)
        path=response['Location']
        self.assertFalse(PaidOrder.objects.exists())
        self.assertFalse(SyntheticBankOperation.objects.exists())
        attempt_count_before=SyntheticPaymentAttempt.objects.count()
        checkouts_before=SupportCheckout.objects.count()
        forged_bodies=(
            {'action':'pay','status':'paid'},
            {'action':'pay','payment_token':'fake-success-token'},
            {'action':'pay','confirmed':'true'},
            {'action':'pay','result':'captured'},
            {'action':'pay','amount_minor':'0'},
            {'action':'pay','provider_operation_id':str(uuid.uuid4())},
        )
        for forged in forged_bodies:
            response=self.client.post(path,forged,secure=True)
            self.assertEqual(response.status_code,400,forged)
            self.assertFalse(PaidOrder.objects.exists())
            self.assertFalse(SyntheticBankOperation.objects.exists())
            self.assertEqual(SyntheticPaymentAttempt.objects.count(),attempt_count_before)
            self.assertEqual(SupportCheckout.objects.count(),checkouts_before)
        for forged_action in ('confirm','succeed','complete','authorized','ok','paid','capture'):
            response=self.client.post(path,{'action':forged_action},secure=True)
            self.assertEqual(response.status_code,400,forged_action)
            self.assertFalse(PaidOrder.objects.exists())
            self.assertFalse(SyntheticBankOperation.objects.exists())
            self.assertEqual(SyntheticPaymentAttempt.objects.count(),attempt_count_before)
        response=self.client.post(path,{'action':'pay'},secure=True)
        self.assertEqual(response.status_code,200)
        self.assertEqual(PaidOrder.objects.count(),1)

    def test_staff_order_views_show_per_order_hours_only_without_cumulative_balance(self):
        from .invitations import issue_fixture
        from .models import PaidOrder,PaidOrderGrant
        from .tests import form_data
        first=self.pay()
        _,token=issue_fixture(customer=self.customer,issuer=self.issuer,
            company_name='Synthetic Company Limited',project_reference='SLL top-up')
        self.client.get('/invite/'+token,secure=True)
        data=form_data(quantity='2',action='review',accept_terms='',privacy_acknowledged='')
        response=self.client.post('/purchase/simple/',data,secure=True)
        response=self.client.post('/purchase/simple/',dict(data,action='checkout',
            review_digest=response.context['review_digest'],accept_terms='on',privacy_acknowledged='on'),secure=True)
        self.assertEqual(self.client.post(response['Location'],{'action':'pay'},secure=True).status_code,200)
        second=PaidOrder.objects.exclude(pk=first.pk).get()
        path=self.staff(first)
        PaidOrderGrant.objects.create(user=self.user,order=first)
        PaidOrderGrant.objects.create(user=self.user,order=second)
        forbidden=('total hours','total_hours','hours_total','cumulative','available hours','remaining hours',
            'used hours','hour balance','hours balance','balance of hours','bundle panel','time ledger',
            'time-ledger','time entry','time-entry','task usage','task-usage')
        response=self.browser.get('/staff/shb-orders/')
        self.assertEqual(response.status_code,200)
        body=response.json()
        self.assertEqual(sorted(o['hours_purchased'] for o in body['orders']),[20,30])
        self.assertEqual(set(body),{'orders','limit','older'})
        self.assertEqual(set(body['orders'][0]),{'id','order_reference','variant','hours_purchased'})
        raw=response.content.decode().lower()
        for keyword in forbidden:self.assertNotIn(keyword,raw)
        html=self.browser.get('/staff/shb-orders/',HTTP_ACCEPT='text/html').content.decode()
        self.assertIn('30 hours in this order',html);self.assertIn('20 hours in this order',html)
        lower=html.lower()
        for keyword in forbidden:self.assertNotIn(keyword,lower)
        for order,hours in ((first,30),(second,20)):
            detail=self.browser.get('/staff/shb-orders/'+str(order.pk)+'/')
            self.assertEqual(detail.status_code,200)
            payload=detail.json()
            self.assertEqual(payload['purchase']['hours_purchased'],hours)
            self.assertNotIn('total_hours',payload);self.assertNotIn('total_hours',payload['purchase'])
            self.assertNotIn('balance',payload);self.assertNotIn('balance',payload['purchase'])
            self.assertNotIn('used_hours',payload['purchase'])
            self.assertNotIn('remaining_hours',payload['purchase'])
            self.assertNotIn('available_hours',payload['purchase'])
            raw=detail.content.decode().lower()
            for keyword in forbidden:self.assertNotIn(keyword,raw)

    def test_temporary_mail_failure_retains_order_coupon_payment_and_staff_view(self):
        from . import purchase_mail
        from .models import PaidOrder,PaidOrderGrant,PurchaseNoticeCapture,PurchaseNoticeDelivery,DiscountReservation
        from shop.payments.models import SyntheticPaymentAttempt
        order=self.pay(discount=True)
        order_payload=dict(order.payload)
        reservation=DiscountReservation.objects.get()
        reservation_state=reservation.state;reservation_consumed=reservation.consumed_order_id
        attempt=SyntheticPaymentAttempt.objects.get()
        attempt_state=attempt.state;attempt_amount=attempt.amount_minor
        path=self.staff(order);PaidOrderGrant.objects.create(user=self.user,order=order)
        with PreparedArchive(Path(self.directory.name)) as archive:
            with patch.object(PreparedArchive,'publish',side_effect=ArchiveError('temporary mail failure')):
                claimed=purchase_mail.claim(lease_seconds=1)
                with self.assertRaises(ArchiveError):purchase_mail.capture(claimed,archive)
                self.assertFalse(PurchaseNoticeCapture.objects.exists())
                order.refresh_from_db();self.assertEqual(order.payload,order_payload)
                self.assertEqual(PaidOrder.objects.count(),1)
                reservation.refresh_from_db()
                self.assertEqual(reservation.state,reservation_state)
                self.assertEqual(reservation.consumed_order_id,reservation_consumed)
                attempt.refresh_from_db()
                self.assertEqual(attempt.state,attempt_state)
                self.assertEqual(attempt.amount_minor,attempt_amount)
                response=self.browser.get(path)
                self.assertEqual(response.status_code,200)
                self.assertEqual(response.json()['purchase']['hours_purchased'],30)
            PurchaseNoticeDelivery.objects.filter(pk=order.pk).update(lease_until=timezone.now()-timedelta(seconds=1))
            self.assertTrue(purchase_mail.execute_once())
        self.assertEqual(PaidOrder.objects.count(),1)
        self.assertEqual(PurchaseNoticeCapture.objects.count(),1)
        order.refresh_from_db();self.assertEqual(order.payload,order_payload)
        reservation.refresh_from_db()
        self.assertEqual(reservation.state,reservation_state)
        self.assertEqual(reservation.consumed_order_id,reservation_consumed)

    def test_paid_order_remains_valid_and_visible_to_staff_after_invitation_expiry(self):
        from . import purchase_mail
        from .models import PaidOrder,PaidOrderGrant,PurchaseNoticeDelivery,SupportCheckout
        from .tests import form_data
        from shop.catalog.models import SyntheticFulfilment,SyntheticSupportEvent
        order=self.pay()
        original_payload=dict(order.payload)
        original_notice_pk=PurchaseNoticeDelivery.objects.get().pk
        future=self.invitation.expires_at+timedelta(days=1)
        with patch('shop.shb.invitations.now',return_value=future):
            checkouts_before=SupportCheckout.objects.count()
            response=self.client.post('/purchase/simple/',form_data(action='submit'),secure=True)
            self.assertNotEqual(response.status_code,302)
            self.assertEqual(PaidOrder.objects.count(),1)
            self.assertEqual(SupportCheckout.objects.count(),checkouts_before)
        path=self.staff(order)
        PaidOrderGrant.objects.create(user=self.user,order=order)
        response=self.browser.get(path)
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json()['purchase']['hours_purchased'],30)
        self.assertEqual(response.json()['purchase']['variant_id'],'shb-fpga-10h')
        self.assertEqual(response.json()['details']['company_name'],'Synthetic Company Limited')
        order.refresh_from_db()
        self.assertEqual(order.payload,original_payload)
        self.assertFalse(SyntheticFulfilment.objects.exists())
        self.assertFalse(SyntheticSupportEvent.objects.exists())
        self.assertTrue(purchase_mail.execute_once())
        self.assertEqual(PurchaseNoticeDelivery.objects.get().pk,original_notice_pk)

    def test_get_cannot_finalize_or_queue_and_accepted_unpaid_order_cannot_finalize(self):
        from . import paid_orders
        from .models import PaidOrder,PurchaseNoticeDelivery
        response=self.checkout();self.assertEqual(response.status_code,302)
        for _ in range(2):self.assertEqual(self.client.get(response['Location'],secure=True).status_code,200)
        self.assertFalse(PaidOrder.objects.exists());self.assertFalse(PurchaseNoticeDelivery.objects.exists())
        with PreparedArchive(Path(self.directory.name)) as archive:
            with self.assertRaises(CheckoutError):paid_orders.finalize(self.customer,self.saved().pk,archive)
        self.assertFalse(PaidOrder.objects.exists())

    def test_archive_failure_after_capture_retains_money_and_hold_until_worker_recovery(self):
        from .models import PaidOrder,DiscountReservation,Invitation
        from .discounts import issue_fixture
        from shop.worker.services import execute_once
        _,raw=issue_fixture(customer=self.customer,issuer=self.issuer,percentage_bps=1000,fpga_allowed=True)
        data,token=self.review(discount_code=raw);response=self.checkout(data,token)
        original=PreparedArchive.publish
        def fail_order(archive,identity,body):
            import json
            if json.loads(body).get('kind')=='shb-paid-order':raise ArchiveError('owned failure')
            return original(archive,identity,body)
        with patch.object(PreparedArchive,'publish',fail_order):
            self.assertEqual(self.client.post(response['Location'],{'action':'pay'},secure=True).status_code,503)
        self.assertEqual(self.acceptance().attempt.provider_status,'captured')
        self.assertFalse(PaidOrder.objects.exists());self.assertEqual(DiscountReservation.objects.get().state,'reserved')
        Invitation.objects.filter(pk=self.invitation.pk).update(revoked_at=timezone.now())
        self.assertTrue(execute_once())
        self.assertEqual(PaidOrder.objects.count(),1);self.assertEqual(DiscountReservation.objects.get().state,'consumed')
        self.assertEqual(self.client.get(response['Location'],secure=True).status_code,403)

    def test_uncertainty_never_finalizes_or_releases_and_lookup_after_expiry_recovers(self):
        from .models import PaidOrder,DiscountReservation,Invitation
        from .discounts import issue_fixture
        _,raw=issue_fixture(customer=self.customer,issuer=self.issuer,percentage_bps=1000,fpga_allowed=True)
        data,token=self.review(discount_code=raw);response=self.checkout(data,token)
        original=payment.pay
        with patch('shop.catalog.checkout_payment.pay',side_effect=lambda *a,**k:original(*a,fault='after_commit',**k)):
            self.assertEqual(self.client.post(response['Location'],{'action':'pay'},secure=True).status_code,409)
        self.assertFalse(PaidOrder.objects.exists());self.assertEqual(DiscountReservation.objects.get().state,'reserved')
        Invitation.objects.filter(pk=self.invitation.pk).update(revoked_at=timezone.now())
        with PreparedArchive(Path(self.directory.name)) as archive:payment.reconcile(self.customer,self.saved().pk,archive)
        self.assertEqual(PaidOrder.objects.count(),1);self.assertEqual(DiscountReservation.objects.get().state,'consumed')

    def test_concurrent_finalization_is_one_order_and_one_concession(self):
        from . import paid_orders
        from .models import PaidOrder,PurchaseNoticeDelivery
        response=self.checkout();self.assertEqual(response.status_code,302)
        with patch('shop.catalog.checkout_payment.finalize_shb'):
            self.assertEqual(self.client.post(response['Location'],{'action':'pay'},secure=True).status_code,200)
        self.assertFalse(PaidOrder.objects.exists())
        expected=uuid.uuid5(self.acceptance().pk,'shb-paid-order-v1');barrier=Barrier(2)
        def finish(_):
            try:
                owner=get_user_model().objects.get(pk=self.customer.pk);barrier.wait(timeout=5)
                with PreparedArchive(Path(self.directory.name)) as archive:return paid_orders.finalize(owner,self.saved().pk,archive).pk
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:self.assertEqual(list(pool.map(finish,range(2))),[expected,expected])
        self.assertEqual(PaidOrder.objects.count(),1);self.assertEqual(PurchaseNoticeDelivery.objects.count(),1)

    def test_missing_archived_capture_holds_new_paid_state(self):
        from .models import PaidOrder
        original=PreparedArchive.recover
        def unreadable(archive,receipt):
            from shop.payments.models import SyntheticPaymentObservation
            if SyntheticPaymentObservation.objects.filter(pk=receipt.evidence_id).exists():raise ArchiveError('unrecoverable')
            return original(archive,receipt)
        response=self.checkout()
        with patch.object(PreparedArchive,'recover',unreadable):
            self.assertEqual(self.client.post(response['Location'],{'action':'pay'},secure=True).status_code,503)
        self.assertFalse(PaidOrder.objects.exists())

    def test_sql_paid_record_and_concession_are_immutable(self):
        from .models import PaidOrder,DiscountReservation,PurchaseNoticeCapture
        from . import purchase_mail
        order=self.pay(discount=True)
        for rows,changes in [(PaidOrder.objects.all(),{'payload':{}}),
                (DiscountReservation.objects.all(),{'state':'reserved','consumed_order':None})]:
            with self.assertRaises(DatabaseError),transaction.atomic():rows.update(**changes)
        with self.assertRaises(DatabaseError),transaction.atomic():PaidOrder.objects.all().delete()
        with self.assertRaises(DatabaseError),transaction.atomic():
            PurchaseNoticeCapture.objects.create(order=order,payload={},sha256='0'*64,archive_receipt={})
        self.assertTrue(purchase_mail.execute_once())
        with self.assertRaises(DatabaseError),transaction.atomic():PurchaseNoticeCapture.objects.all().update(payload={})

    def test_mail_failure_and_expired_claim_keep_paid_state_and_reuse_same_effect(self):
        from . import purchase_mail
        from .models import PaidOrder,PurchaseNoticeDelivery,PurchaseNoticeCapture
        order=self.pay(discount=True)
        claimed=purchase_mail.claim(lease_seconds=1)
        with PreparedArchive(Path(self.directory.name)) as archive:
            with patch.object(PreparedArchive,'publish',side_effect=ArchiveError('temporary notice failure')):
                with self.assertRaises(ArchiveError):purchase_mail.capture(claimed,archive)
            self.assertEqual(PaidOrder.objects.count(),1);self.assertFalse(PurchaseNoticeCapture.objects.exists())
            PurchaseNoticeDelivery.objects.filter(pk=order.pk).update(lease_until=timezone.now()-timedelta(seconds=1))
            fresh=purchase_mail.claim()
            self.assertNotEqual(fresh.token,claimed.token)
            self.assertFalse(purchase_mail.capture(claimed,archive))
            self.assertTrue(purchase_mail.capture(fresh,archive))
            self.assertTrue(purchase_mail.capture(fresh,archive))  # lost completion response
            self.assertFalse(purchase_mail.complete(claimed,archive))
            self.assertTrue(purchase_mail.complete(fresh,archive))
        self.assertEqual(PurchaseNoticeCapture.objects.count(),1)
        self.assertEqual(PurchaseNoticeDelivery.objects.get().state,'captured')
        self.assertFalse(purchase_mail.execute_once())

    def test_worker_processes_notice_once_without_real_mail_or_time_work(self):
        from shop.worker.services import execute_once
        from .models import PurchaseNoticeCapture,PurchaseNoticeDelivery,TransactionNoticeCapture
        order=self.pay()
        with patch('shop.worker.statement_mail.execute_once',return_value=False):
            self.assertTrue(execute_once());self.assertTrue(execute_once());self.assertFalse(execute_once())
        captured=PurchaseNoticeCapture.objects.get()
        self.assertEqual(captured.order_id,order.pk)
        self.assertEqual(captured.payload['order_reference'],order.payload['order_reference'])
        self.assertIs(captured.payload['actual_email_sent'],False)
        self.assertEqual(PurchaseNoticeDelivery.objects.get().attempts,1)
        self.assertEqual(TransactionNoticeCapture.objects.get().notice.payload['body']['reference'],order.payload['order_reference'])

    def test_notification_retries_are_bounded_and_do_not_undo_purchase(self):
        from . import purchase_mail
        from .models import PaidOrder,PurchaseNoticeDelivery
        order=self.pay()
        for _ in range(3):
            self.assertIsNotNone(purchase_mail.claim())
            PurchaseNoticeDelivery.objects.filter(pk=order.pk).update(lease_until=timezone.now()-timedelta(seconds=1))
        self.assertIsNone(purchase_mail.claim())
        self.assertEqual(PurchaseNoticeDelivery.objects.get().state,'held')
        self.assertEqual(PaidOrder.objects.count(),1)

    def test_refunded_order_keeps_original_purchase_coupon_and_notice_reference(self):
        from . import paid_orders,purchase_mail
        from .models import PaidOrder,DiscountReservation
        from shop.payments import synthetic_bank,attempts
        order=self.pay(discount=True);accepted=self.acceptance()
        from shop.payments.bank_contract import BankMutation
        a=accepted.attempt
        synthetic_bank.mutate(BankMutation(a.merchant,a.reference,a.provider_operation_id,uuid.uuid4(),a.currency,a.amount_minor,'refund'))
        with PreparedArchive(Path(self.directory.name)) as archive:
            payment.reconcile(self.customer,self.saved().pk,archive)
            self.assertEqual(paid_orders.finalize(self.customer,self.saved().pk,archive).payload,order.payload)
        self.assertEqual(PaidOrder.objects.count(),1);self.assertEqual(DiscountReservation.objects.get().state,'consumed')
        self.assertTrue(purchase_mail.execute_once())

    def test_recovery_hold_blocks_finalization_and_notice_worker(self):
        from . import paid_orders,purchase_mail
        from shop.access.models import AccessEpoch
        from shop.access.effects import RecoveryEffectError
        self.pay()
        AccessEpoch.objects.filter(pk=1).update(quarantined=True,active_reset=uuid.uuid4())
        with PreparedArchive(Path(self.directory.name)) as archive:
            with self.assertRaises(CheckoutError):paid_orders.finalize(self.customer,self.saved().pk,archive)
        self.assertFalse(purchase_mail.execute_once())

    def staff(self,order):
        from shop.access import staff_tests
        from shop.access.models import StaffCredential
        self.user=self.issuer;self.password='synthetic-paid-view-password'
        self.user.set_password(self.password);self.user.save(update_fields=['password'])
        self.credential=StaffCredential.objects.create(user=self.user)
        self.post=staff_tests.StaffTests.post.__get__(self)
        self.challenge=staff_tests.StaffTests.challenge.__get__(self)
        self.authenticated=staff_tests.StaffTests.authenticated.__get__(self)
        configuration=dict(staff_tests.STAFF_SETTINGS,LOCAL_STAFF_CAPTURE_ROOT=self.directory.name)
        context=override_settings(**configuration);context.enable();self.addCleanup(context.disable)
        self.browser=Client(enforce_csrf_checks=True,HTTP_HOST='staff.localhost');self.authenticated()
        return '/staff/shb-orders/'+str(order.pk)+'/'

    def test_staff_order_requires_exact_assignment_recent_mfa_and_no_customer_history(self):
        from .models import PaidOrderGrant
        order=self.pay();path=self.staff(order)
        self.assertEqual(self.browser.get(path).status_code,404)
        grant=PaidOrderGrant.objects.create(user=self.user,order=order)
        response=self.browser.get(path);self.assertEqual(response.status_code,200)
        self.assertEqual(response.json()['purchase']['hours_purchased'],30)
        self.assertEqual(response.json()['details']['company_name'],'Synthetic Company Limited')
        self.assertEqual(response['Cache-Control'],'no-store')
        self.assertContains(self.browser.get(path,HTTP_ACCEPT='text/html'),'30 hours in this order')
        self.assertEqual(len(self.browser.get('/staff/shb-orders/').json()['orders']),1)
        grant.delete();self.assertEqual(self.browser.get(path).status_code,404)
        session=self.browser.session;session['shop_staff_mfa']['verified_at']-=301;session.save()
        self.assertEqual(self.browser.get(path).status_code,403)

    def test_staff_reset_and_restore_clear_new_paid_order_grants(self):
        from .models import PaidOrderGrant
        from shop.access.grants import revoke_staff_resource_grants
        from django.core.management import call_command
        order=self.pay();path=self.staff(order)
        call_command('local_staff','grant-shb-order',username=self.user.username,order=str(order.pk))
        self.assertTrue(PaidOrderGrant.objects.exists())
        call_command('local_staff','revoke',username=self.user.username)
        self.assertFalse(PaidOrderGrant.objects.exists())
        PaidOrderGrant.objects.create(user=self.user,order=order)
        with transaction.atomic():revoke_staff_resource_grants(user_id=None)
        self.assertFalse(PaidOrderGrant.objects.exists())
