"""SHB refunds retain original money/order identity and manual support decisions."""
import uuid
import json
from pathlib import Path
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from django.db import DatabaseError,connection,connections,transaction
from django.test import Client
from django.utils import timezone
from urllib.parse import urlencode
from django.test import TransactionTestCase, override_settings
from . import offer_tests


@override_settings(SHB_SYNTHETIC_FIXTURE=True)
class FinancialTests(TransactionTestCase):
    client_class = offer_tests.OfferTests.client_class
    post = offer_tests.OfferTests.post
    challenge = offer_tests.OfferTests.challenge
    authenticated = offer_tests.OfferTests.authenticated
    customer_submit = offer_tests.OfferTests.customer_submit
    submit = offer_tests.OfferTests.submit
    issue = offer_tests.OfferTests.issue
    offer = offer_tests.OfferTests.offer
    customer_review = offer_tests.OfferTests.customer_review
    accept_offer = offer_tests.OfferTests.accept_offer
    pay = offer_tests.OfferTests.pay

    def setUp(self):
        offer_tests.OfferTests.setUp(self)
        self.assertEqual(self.issue().status_code, 201)
        response = self.accept_offer(); self.assertEqual(response.status_code, 302)
        self.assertEqual(self.pay(response['Location']).status_code, 200)
        from .models import PaidOrder, PaidOrderGrant
        from shop.payments.models import SyntheticPaymentStaffGrant
        self.order = PaidOrder.objects.select_related('acceptance').get()
        self.order_grant = PaidOrderGrant.objects.create(user=self.user, order=self.order)
        self.finance_grant = SyntheticPaymentStaffGrant.objects.create(user=self.user,
            acceptance=self.order.acceptance, kind='refund')
        self.order_route = 'shb-orders/' + str(self.order.pk) + '/'
        self.finance_route = 'payments/' + str(self.finance_grant.pk) + '/'

    def test_new_shb_refund_cannot_bypass_manual_support_review_through_shared_finance_route(self):
        from shop.payments.models import SyntheticPaymentOperation, SyntheticBankTransition
        response = self.post(self.finance_route, {'action':'prepare','request_id':str(uuid.uuid4())})
        self.assertEqual(response.status_code, 409)
        self.assertFalse(SyntheticPaymentOperation.objects.exists())
        self.assertFalse(SyntheticBankTransition.objects.exists())

    def manual_review(self, **changes):
        if not hasattr(self,'review_data'):
            self.review_data={'request_id':str(uuid.uuid4()),'manual_records_checked':True,
                'manual_record_reference':'Support team manual decision fixture-1',
                'reason':'Synthetic full-refund test; manual records consulted where relevant.'}
        return self.post(self.order_route+'refund-review/',dict(self.review_data,**changes))

    def prepare_refund(self):
        if not hasattr(self,'operation_key'):self.operation_key=str(uuid.uuid4())
        return self.post(self.finance_route,{'action':'prepare','request_id':self.operation_key})

    def finance(self,action):return self.post(self.finance_route,{'action':action})

    def handoff(self,**changes):
        if not hasattr(self,'handoff_data'):
            self.handoff_data={'request_id':str(uuid.uuid4()),'communication_reference':'Support team informed via fixture-note-2'}
        return self.post(self.order_route+'refund-handoff/',dict(self.handoff_data,**changes))

    def test_review_is_archived_once_and_does_not_start_a_financial_operation(self):
        from .models import RefundReview
        from shop.payments.models import SyntheticPaymentOperation
        self.assertEqual(self.manual_review().status_code,201)
        self.assertEqual(self.manual_review().status_code,200)
        saved=RefundReview.objects.get()
        self.assertEqual(saved.payload['order_reference'],self.order.payload['order_reference'])
        self.assertEqual(saved.payload['amount_minor'],self.order.payload['purchase']['total_minor'])
        self.assertTrue(saved.payload['manual_records_checked'])
        self.assertFalse(saved.payload['actual_financial_authority'])
        self.assertTrue(all(value is None for value in saved.payload['financial_policy'].values()))
        self.assertEqual(self.manual_review(reason='Changed decision on retained key').status_code,409)
        self.assertFalse(SyntheticPaymentOperation.objects.exists())

    def test_full_refund_and_manual_communication_keep_original_purchase_and_coupon(self):
        from .models import PaidOrder,DiscountReservation,RefundSupportHandoff
        from shop.payments.models import SyntheticPaymentOperation,SyntheticBankTransition,SyntheticBankOperation
        from shop.catalog.models import SyntheticFulfilment,SyntheticSupportEvent
        original=self.order.payload;hold=DiscountReservation.objects.get()
        self.assertEqual(self.manual_review().status_code,201)
        self.assertEqual(self.prepare_refund().status_code,200)
        operation=SyntheticPaymentOperation.objects.get()
        self.assertEqual(operation.payload['shb_refund_review']['order_id'],str(self.order.pk))
        self.assertEqual(self.finance('dispatch').status_code,200)
        self.assertEqual(self.finance('dispatch').status_code,200)
        self.assertEqual(self.finance('reconcile').status_code,200)
        self.assertEqual(self.handoff().status_code,201);self.assertEqual(self.handoff().status_code,200)
        self.assertEqual(self.handoff(communication_reference='Different event on same key').status_code,409)
        self.assertEqual(PaidOrder.objects.get().payload,original)
        self.assertEqual(DiscountReservation.objects.get().state,'consumed')
        self.assertEqual(DiscountReservation.objects.get().consumed_order_id,hold.consumed_order_id)
        self.assertEqual(SyntheticBankOperation.objects.count(),1);self.assertEqual(SyntheticBankTransition.objects.count(),1)
        self.assertEqual(RefundSupportHandoff.objects.count(),1)
        self.assertFalse(SyntheticFulfilment.objects.exists());self.assertFalse(SyntheticSupportEvent.objects.exists())

    def test_handoff_waits_for_exact_observed_refund_and_uncertainty_never_redispatches(self):
        from shop.payments import operations,synthetic_bank
        from .models import RefundSupportHandoff
        self.assertEqual(self.manual_review().status_code,201)
        self.assertEqual(self.handoff().status_code,409)
        self.assertEqual(self.prepare_refund().status_code,200)
        original=operations.dispatch
        with patch.object(operations,'dispatch',side_effect=lambda *a,**k:original(*a,fault='after_commit',**k)):
            self.assertEqual(self.finance('dispatch').status_code,409)
        self.assertEqual(self.handoff().status_code,409)
        with patch.object(synthetic_bank,'mutate',side_effect=AssertionError('blind refund retry')):
            self.assertEqual(self.finance('dispatch').status_code,200)
            self.assertEqual(self.finance('reconcile').status_code,200)
        self.assertEqual(self.handoff().status_code,201)
        self.assertEqual(RefundSupportHandoff.objects.count(),1)

    def test_unknown_usage_amounts_and_forged_financial_values_are_rejected(self):
        from .models import RefundReview
        self.assertEqual(self.manual_review(manual_records_checked=False).status_code,422)
        for changes in ({'hours_used':0},{'remaining_hours':50},{'amount_minor':1},{'reason':'x'*513}):
            with self.subTest(changes=changes):self.assertEqual(self.manual_review(**changes).status_code,400)
        self.assertFalse(RefundReview.objects.exists())
        self.assertEqual(self.manual_review(reason='α'*512,manual_record_reference='β'*200).status_code,201)

    def test_order_assignment_and_finance_assignment_are_both_required(self):
        self.order_grant.delete();self.assertEqual(self.manual_review().status_code,404)
        from .models import PaidOrderGrant
        PaidOrderGrant.objects.create(user=self.user,order=self.order)
        self.finance_grant.delete();self.assertEqual(self.manual_review().status_code,404)

    def test_new_shared_refund_intent_requires_order_scope_but_retained_finance_lookup_stays_available(self):
        from .models import PaidOrderGrant
        self.assertEqual(self.manual_review().status_code,201)
        self.order_grant.delete()
        self.assertEqual(self.prepare_refund().status_code,404)
        grant=PaidOrderGrant.objects.create(user=self.user,order=self.order)
        self.assertEqual(self.prepare_refund().status_code,200)
        grant.delete()
        self.assertEqual(self.finance('dispatch').status_code,200)
        self.assertEqual(self.finance('reconcile').status_code,200)

    def test_recent_mfa_live_guard_and_recovery_quarantine_are_enforced(self):
        from shop.access.recovery import local_recovery_operation
        session=self.browser.session;marker=session['shop_staff_mfa'];old=marker['verified_at']
        marker['verified_at']-=301;session['shop_staff_mfa']=marker;session.save()
        self.assertEqual(self.manual_review().status_code,403)
        marker['verified_at']=old;session['shop_staff_mfa']=marker;session.save()
        with override_settings(SHB_SYNTHETIC_FIXTURE=False):self.assertEqual(self.manual_review().status_code,503)
        local_recovery_operation(action='quarantine',request_id=uuid.uuid4(),expected_database=connection.settings_dict['NAME'])
        response=self.browser.post('/staff/'+self.order_route+'refund-review/',data=json.dumps(self.review_data),
            content_type='application/json',HTTP_X_CSRFTOKEN=self.browser.cookies['shop_staff_csrftoken'].value)
        self.assertEqual(response.status_code,403)

    def test_archive_failure_cannot_make_review_or_refund_intent(self):
        from shop.adapters.evidence_archive import PreparedArchive,ArchiveError
        from .models import RefundReview
        from shop.payments.models import SyntheticPaymentOperation
        with patch.object(PreparedArchive,'publish',side_effect=ArchiveError('owned outage')):
            self.assertEqual(self.manual_review().status_code,503)
        self.assertFalse(RefundReview.objects.exists())
        self.assertEqual(self.manual_review().status_code,201)
        review=RefundReview.objects.get()
        (Path(self.directory.name)/('blob-'+review.sha256)).unlink()
        self.assertEqual(self.prepare_refund().status_code,503)
        self.assertFalse(SyntheticPaymentOperation.objects.exists())

    def test_sql_refund_insert_cannot_omit_a_real_review_record(self):
        from shop.payments.models import SyntheticPaymentOperation
        forged={'id':str(uuid.uuid4()),'sha256':'0'*64,'order_id':str(self.order.pk),
            'order_reference':self.order.payload['order_reference']}
        with patch('shop.shb.refunds.required_reference',return_value=forged):
            with self.assertRaisesMessage(DatabaseError,'new refund operation needs archived manual review'):
                self.prepare_refund()
        self.assertFalse(SyntheticPaymentOperation.objects.exists())

    def test_manual_records_are_append_only_and_invitation_revocation_does_not_erase_money(self):
        from .models import Invitation,RefundReview,RefundSupportHandoff
        Invitation.objects.filter(pk=self.invitation.pk).update(revoked_at=timezone.now())
        self.assertEqual(self.manual_review().status_code,201)
        self.assertEqual(self.prepare_refund().status_code,200);self.assertEqual(self.finance('dispatch').status_code,200)
        self.assertEqual(self.handoff().status_code,201)
        for model in (RefundReview,RefundSupportHandoff):
            with self.subTest(model=model.__name__),self.assertRaises(DatabaseError),transaction.atomic():
                model.objects.update(payload={})

    def test_native_forms_share_same_archived_decision_and_csrf_boundary(self):
        page=self.browser.get('/staff/'+self.order_route,HTTP_ACCEPT='text/html')
        self.assertContains(page,'Manual support record or decision reference')
        self.assertEqual(page['Cache-Control'],'no-store')
        self.manual_review()  # Initialize the retained request identity.
        from .models import RefundReview
        before=RefundReview.objects.count()
        data=dict(self.review_data,manual_records_checked='on',csrfmiddlewaretoken=self.browser.cookies['shop_staff_csrftoken'].value)
        response=self.browser.post('/staff/'+self.order_route+'refund-review/',urlencode(data),content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code,303)
        self.assertEqual(RefundReview.objects.count(),before)
        no_csrf=Client(enforce_csrf_checks=True,HTTP_HOST='staff.localhost');no_csrf.cookies=self.browser.cookies.copy()
        self.assertEqual(no_csrf.post('/staff/'+self.order_route+'refund-review/',dict(self.review_data,manual_records_checked='on')).status_code,403)

    def test_parallel_manual_reviews_have_one_original_decision(self):
        from .models import RefundReview
        self.manual_review(manual_records_checked=False)  # Initialize only, no record.
        cookies=self.browser.cookies.copy();barrier=Barrier(2)
        def send(_):
            try:
                client=Client(enforce_csrf_checks=True,HTTP_HOST='staff.localhost');client.cookies=cookies.copy()
                barrier.wait(timeout=5)
                return client.post('/staff/'+self.order_route+'refund-review/',
                    data=json.dumps(dict(self.review_data,request_id=str(uuid.uuid4()))),content_type='application/json',
                    HTTP_X_CSRFTOKEN=cookies['shop_staff_csrftoken'].value).status_code
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:statuses=list(pool.map(send,range(2)))
        self.assertEqual(sorted(statuses),[201,409]);self.assertEqual(RefundReview.objects.count(),1)

    def test_recovery_checks_refund_review_result_and_handoff_without_replaying_money(self):
        from shop.access.recovery import local_recovery_operation
        from .recovery import inspect_local_shb_recovery
        from .models import RefundReview,RefundSupportHandoff,PaidOrder,DiscountReservation
        from shop.payments.models import SyntheticBankTransition
        self.assertEqual(self.manual_review().status_code,201)
        self.assertEqual(self.prepare_refund().status_code,200);self.assertEqual(self.finance('dispatch').status_code,200)
        self.assertEqual(self.handoff().status_code,201)
        review=RefundReview.objects.get();handoff=RefundSupportHandoff.objects.get();reset=uuid.uuid4()
        local_recovery_operation(action='quarantine',request_id=reset,expected_database=connection.settings_dict['NAME'])
        state=inspect_local_shb_recovery()
        self.assertEqual(state['counts']['refund_reviews'],1);self.assertEqual(state['counts']['refund_handoffs'],1)
        local_recovery_operation(action='release',request_id=uuid.uuid4(),basis_reset=reset,expected_database=connection.settings_dict['NAME'])
        self.assertEqual(RefundReview.objects.get().pk,review.pk);self.assertEqual(RefundSupportHandoff.objects.get().pk,handoff.pk)
        self.assertEqual(PaidOrder.objects.get().payload,self.order.payload)
        self.assertEqual(SyntheticBankTransition.objects.count(),1);self.assertEqual(DiscountReservation.objects.get().state,'consumed')

    def test_missing_refund_review_archive_refuses_recovery_release(self):
        from shop.access.recovery import local_recovery_operation,AccessRecoveryError
        from shop.access.models import AccessEpoch
        from .models import RefundReview
        self.assertEqual(self.manual_review().status_code,201)
        review=RefundReview.objects.get();(Path(self.directory.name)/('blob-'+review.sha256)).unlink()
        reset=uuid.uuid4()
        local_recovery_operation(action='quarantine',request_id=reset,expected_database=connection.settings_dict['NAME'])
        with self.assertRaisesMessage(AccessRecoveryError,'shb_recovery_evidence_required'):
            local_recovery_operation(action='release',request_id=uuid.uuid4(),basis_reset=reset,expected_database=connection.settings_dict['NAME'])
        self.assertTrue(AccessEpoch.objects.get().quarantined)
