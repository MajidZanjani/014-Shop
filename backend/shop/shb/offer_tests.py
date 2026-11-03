"""Dated ASIC offers stay bound to the reviewed request and shared payment."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import json
from pathlib import Path
from threading import Barrier
import time
from unittest.mock import patch
import uuid

from django.contrib.auth import get_user_model
from django.db import DatabaseError, connections, transaction
from django.test import Client, TransactionTestCase, override_settings
from django.utils import timezone

from . import review_tests
from .tests import form_data, ShopClient


@override_settings(SHB_SYNTHETIC_FIXTURE=True)
class OfferTests(TransactionTestCase):
    client_class = review_tests.RequestReviewTests.client_class
    post = review_tests.RequestReviewTests.post
    challenge = review_tests.RequestReviewTests.challenge
    authenticated = review_tests.RequestReviewTests.authenticated
    customer_submit = review_tests.RequestReviewTests.customer_submit
    submit = review_tests.RequestReviewTests.submit

    def setUp(self):
        review_tests.RequestReviewTests.setUp(self)
        context=override_settings(LOCAL_CHECKOUT_ARCHIVE_ROOT=self.directory.name)
        context.enable();self.addCleanup(context.disable)

    def issue(self, **changes):
        if not hasattr(self,'issue_value'):
            self.assertEqual(self.submit(decision='ready_for_commercial_review').status_code, 201)
            self.issue_value = {'request_id': str(uuid.uuid4()), 'expected_review_version': 1,
                'scope_sha256': self.row.sha256, 'prerequisites': 'Customer provides authorized tool access separately.',
                'exclusions': 'No tape-out or sign-off commitment.'}
        value = dict(self.issue_value,**changes)
        return self.post('quotation-requests/' + str(self.row.quotation_id) + '/shb-offers/', value)

    def offer(self):
        from .models import SupportOffer
        return SupportOffer.objects.select_related('request__invitation').get()

    def customer_review(self, **changes):
        from .forms import OfferForm
        self.path='/purchase/shb/offer/'+str(self.offer().pk)+'/'
        value={k:v for k,v in form_data(accept_terms='',privacy_acknowledged='').items() if k in OfferForm().fields}
        value.update(action='review',request_id=str(uuid.uuid4()));value.update(changes)
        with override_settings(**self.customer_settings): response=self.client.post(self.path,value,secure=True)
        self.assertEqual(response.status_code,200, (response.context.get('error'),response.context['form'].errors))
        return value,response.context['review_digest']

    def accept_offer(self, value=None, token=None, client=None):
        if value is None:value,token=self.customer_review()
        with override_settings(**self.customer_settings):
            return (client or self.client).post(self.path,dict(value,action='checkout',review_digest=token,
                accept_terms='on',privacy_acknowledged='on'),secure=True)

    def pay(self, path, action='pay'):
        with override_settings(**self.customer_settings):
            return self.client.post(path,{'action':action},secure=True)

    def test_issue_binds_request_and_reserved_discount_without_payment(self):
        response = self.issue()
        self.assertEqual(response.status_code, 201)
        from .models import SupportOffer, DiscountReservation
        from shop.catalog.models import SyntheticCheckout
        from shop.payments.models import SyntheticPaymentAttempt
        offer = SupportOffer.objects.get()
        self.assertEqual(offer.payload['request_sha256'], self.row.sha256)
        self.assertEqual(offer.payload['request_revision'], self.row.revision)
        self.assertEqual(offer.payload['customer_id'], self.customer.pk)
        self.assertEqual(offer.payload['issued_by']['user_id'],self.user.pk)
        self.assertEqual(offer.payload['technical_review']['reviewer_id'],self.user.pk)
        self.assertEqual(offer.payload['technical_review']['scope_sha256'],self.row.sha256)
        self.assertEqual(offer.payload['purchase']['hours_purchased'], 50)
        self.assertEqual(offer.payload['purchase']['total_minor'], 875000)
        self.assertEqual(DiscountReservation.objects.get().state, 'reserved')
        self.assertFalse(SyntheticCheckout.objects.exists())
        self.assertFalse(SyntheticPaymentAttempt.objects.exists())

    def test_exact_retry_and_new_issue_race_cannot_create_second_active_offer(self):
        from .models import SupportOffer
        self.assertEqual(self.issue().status_code,201)
        original=self.offer().payload
        self.assertEqual(self.issue().status_code,200)
        self.assertEqual(self.issue(exclusions='Changed promise').status_code,409)
        self.assertEqual(self.issue(request_id=str(uuid.uuid4())).status_code,409)
        self.assertEqual(SupportOffer.objects.count(),1)
        self.assertEqual(self.offer().payload,original)

    def test_scoped_prerequisites_and_exclusions_accept_their_declared_length(self):
        self.assertEqual(self.issue(prerequisites='α'*1000,exclusions='β'*1000).status_code,201)

    def test_latest_technical_readiness_and_exact_scope_are_required(self):
        from .models import SupportOffer
        self.assertEqual(self.issue(scope_sha256='0'*64).status_code,409)
        self.assertEqual(self.issue(expected_review_version=0).status_code,409)
        self.assertEqual(self.issue(total_minor=1).status_code,400)
        self.assertEqual(self.submit(request_id=str(uuid.uuid4()),expected_review_version=1,decision='needs_information').status_code,201)
        self.assertEqual(self.issue().status_code,409)
        self.assertFalse(SupportOffer.objects.exists())

    def test_staff_scope_mfa_and_live_guard_are_rechecked(self):
        from .models import SupportOffer
        self.assertEqual(self.issue(expected_review_version=0).status_code,409)
        self.grant.business_scope_version=0;self.grant.save(update_fields=['business_scope_version'])
        self.assertEqual(self.issue().status_code,403)
        self.grant.business_scope_version=1;self.grant.save(update_fields=['business_scope_version'])
        with override_settings(SHB_SYNTHETIC_FIXTURE=False):self.assertEqual(self.issue().status_code,503)
        session=self.browser.session;marker=session['shop_staff_mfa'];marker['verified_at']-=301
        session['shop_staff_mfa']=marker;session.save()
        self.assertEqual(self.issue().status_code,403)
        self.assertFalse(SupportOffer.objects.exists())

    def test_actual_coupon_claim_deadline_can_pass_before_issue_without_losing_discount(self):
        from .discounts import issue_fixture
        from .models import SupportRequest,DiscountReservation
        from shop.access.models import StaffQuotationGrant
        at=timezone.now();code,raw=issue_fixture(customer=self.customer,issuer=self.issuer,percentage_bps=1500,
            asic_allowed=True,starts_at=at-timedelta(seconds=1),expires_at=at+timedelta(seconds=2))
        with override_settings(**self.customer_settings):self.assertEqual(self.customer_submit(discount_code=raw).status_code,200)
        self.row=SupportRequest.objects.exclude(pk=self.row.pk).get()
        StaffQuotationGrant.objects.create(user=self.user,quotation=self.row.quotation,business_scope_version=self.row.revision)
        self.route='quotation-requests/'+str(self.row.quotation_id)+'/shb-reviews/'
        self.value.update(scope_sha256=self.row.sha256)
        time.sleep(max(0,(code.expires_at-timezone.now()).total_seconds())+0.05)
        self.assertEqual(self.issue().status_code,201)
        offer=self.offer()
        self.assertEqual(offer.payload['purchase']['discount_bps'],1500)
        self.assertEqual(offer.payload['purchase']['discount_policy'],DiscountReservation.objects.get(request=self.row).snapshot)
        self.assertGreater(offer.expires_at,code.expires_at)

    def test_offer_is_archived_before_issue_and_staff_revocation_during_io_holds_it(self):
        from shop.adapters.evidence_archive import PreparedArchive,ArchiveError
        from shop.access.models import StaffCredential
        with patch.object(PreparedArchive,'publish',side_effect=ArchiveError('unavailable')):
            self.assertEqual(self.issue().status_code,503)
        self.assertEqual(self.offer().state,'prepared')
        original=PreparedArchive.publish
        def revoke(archive,*args):
            receipt=original(archive,*args)
            StaffCredential.objects.filter(pk=self.credential.pk).update(enabled=False)
            return receipt
        with patch.object(PreparedArchive,'publish',revoke):self.assertEqual(self.issue().status_code,403)
        self.assertIsNone(self.offer().published_at)

    def test_exact_issue_retry_recovers_prepared_archive_failure(self):
        from shop.adapters.evidence_archive import PreparedArchive,ArchiveError
        with patch.object(PreparedArchive,'publish',side_effect=ArchiveError('unavailable')):
            self.assertEqual(self.issue().status_code,503)
        key=self.offer().pk
        self.assertEqual(self.issue().status_code,201)
        self.assertEqual(self.offer().pk,key)
        self.assertTrue(self.offer().archive_receipt)

    def test_get_requires_current_matching_invitation_and_exposes_no_private_prefill(self):
        from .invitations import issue_fixture
        from .models import SupportCheckout
        self.assertEqual(self.issue().status_code,201)
        path='/purchase/shb/offer/'+str(self.offer().pk)+'/'
        with override_settings(**self.customer_settings):
            response=self.client.get(path,secure=True)
            self.assertEqual(response.status_code,200);self.assertEqual(response['Cache-Control'],'no-store')
            self.assertNotContains(response,'buyer@synthetic.invalid');self.assertNotContains(response,'1 Synthetic Test Street')
            self.assertEqual(response.context['form']['company_name'].value(),None)
            self.assertFalse(SupportCheckout.objects.exists())
            self.assertEqual(ShopClient().get(path,secure=True).status_code,403)
            other=get_user_model().objects.create_user(username='other-offer-customer')
            _,token=issue_fixture(customer=other,issuer=self.issuer,company_name='Other Company')
            client=ShopClient();client.get('/invite/'+token,secure=True)
            self.assertEqual(client.get(path,secure=True).status_code,404)
            _,token=issue_fixture(customer=self.customer,issuer=self.issuer,company_name=self.invitation.company_name,project_reference='Different SLL project')
            client.get('/invite/'+token,secure=True)
            self.assertEqual(client.get(path,secure=True).status_code,404)

    def test_forged_quantity_scope_price_and_changed_review_cannot_capture(self):
        from .models import SupportCheckout
        self.assertEqual(self.issue().status_code,201)
        data,token=self.customer_review()
        for change in ({'quantity':'3'},{'assistance':'Other scope'},{'total_minor':'1'},
                {'customer_id':str(self.customer.pk)},{'contact_email':'changed@synthetic.invalid'}):
            with self.subTest(field=next(iter(change))):
                result=self.accept_offer(dict(data,**change),token)
                self.assertIn(result.status_code,(409,422))
        self.assertFalse(SupportCheckout.objects.exists())

    def test_issued_price_policy_and_documents_survive_current_catalog_change(self):
        from . import catalog
        from .models import SupportCheckout
        self.assertEqual(self.issue().status_code,201)
        data,token=self.customer_review();original=self.offer().payload
        policy=dict(catalog.synthetic_offer(),asic_hourly_minor=25000,terms_revision='synthetic-new-terms')
        with patch('shop.shb.catalog.synthetic_offer',return_value=policy):
            result=self.accept_offer(data,token)
        self.assertEqual(result.status_code,302, result.context.get('error') if result.context else '')
        saved=SupportCheckout.objects.get().checkout.snapshot
        self.assertEqual(saved['purchase'],original['purchase'])
        self.assertEqual(saved['documents'],original['documents'])
        self.assertEqual(saved['policy'],original['policy'])
        self.assertEqual(saved['asic_offer']['sha256'],self.offer().sha256)

    def test_explicit_exact_acceptance_pays_one_asic_order_and_consumes_original_hold(self):
        from .models import PaidOrder,DiscountReservation,SupportCheckout,SupportRequest,PurchaseNoticeDelivery,PaidOrderGrant
        from shop.catalog.models import SyntheticCheckout,SyntheticFulfilment
        from shop.payments.models import SyntheticBankOperation
        self.assertEqual(self.issue().status_code,201)
        data,token=self.customer_review();result=self.accept_offer(data,token)
        self.assertEqual(result.status_code,302,result.context.get('error') if result.context else '')
        self.assertEqual(self.accept_offer(data,token)['Location'],result['Location'])
        self.assertEqual(self.pay(result['Location']).status_code,200)
        self.assertEqual(self.pay(result['Location']).status_code,200)
        order=PaidOrder.objects.get();hold=DiscountReservation.objects.get()
        self.assertEqual(order.payload['purchase']['hours_purchased'],50)
        self.assertEqual(order.payload['asic_offer']['payload']['scope']['assistance'],'Help with SLL IP')
        self.assertEqual(hold.state,'consumed');self.assertEqual(hold.consumed_order_id,order.pk)
        self.assertEqual(hold.request_id,self.row.pk);self.assertIsNone(hold.checkout_id)
        self.assertEqual(self.offer().state,'paid');self.assertEqual(SupportRequest.objects.get().state,'paid')
        self.assertEqual(PurchaseNoticeDelivery.objects.count(),1)
        self.assertEqual(SyntheticCheckout.objects.count(),1);self.assertEqual(SyntheticBankOperation.objects.count(),1)
        self.assertEqual(SupportCheckout.objects.get().offer_id,self.offer().pk)
        self.assertFalse(SyntheticFulfilment.objects.exists())
        PaidOrderGrant.objects.create(user=self.user,order=order)
        page=self.browser.get('/staff/shb-orders/'+str(order.pk)+'/',HTTP_ACCEPT='text/html')
        self.assertContains(page,'Help with SLL IP');self.assertContains(page,'No tape-out or sign-off commitment.')

    def test_payment_uncertainty_preserves_hold_and_lookup_after_invitation_revocation(self):
        from .models import PaidOrder,DiscountReservation,SupportCheckout,Invitation
        from shop.catalog import checkout_payment as payment
        from shop.adapters.evidence_archive import PreparedArchive
        from shop.payments.models import SyntheticBankOperation
        self.assertEqual(self.issue().status_code,201)
        response=self.accept_offer();self.assertEqual(response.status_code,302)
        original=payment.pay
        with patch('shop.catalog.checkout_payment.pay',side_effect=lambda *a,**k:original(*a,fault='after_commit',**k)):
            self.assertEqual(self.pay(response['Location']).status_code,409)
        self.assertEqual(DiscountReservation.objects.get().state,'reserved');self.assertFalse(PaidOrder.objects.exists())
        self.assertEqual(self.pay(response['Location'],'cancel').status_code,409)
        Invitation.objects.filter(pk=self.invitation.pk).update(revoked_at=timezone.now())
        self.assertEqual(self.pay(response['Location']).status_code,403)
        saved=SupportCheckout.objects.get()
        with PreparedArchive(Path(self.directory.name)) as archive:payment.reconcile(self.customer,saved.pk,archive)
        self.assertEqual(PaidOrder.objects.count(),1);self.assertEqual(SyntheticBankOperation.objects.count(),1)
        self.assertEqual(DiscountReservation.objects.get().state,'consumed')

    def test_safe_cancellation_closes_asic_checkout_and_releases_request_hold_once(self):
        from .models import DiscountReservation
        self.assertEqual(self.issue().status_code,201)
        response=self.accept_offer();self.assertEqual(response.status_code,302)
        self.assertEqual(self.pay(response['Location'],'cancel').status_code,200)
        self.assertEqual(DiscountReservation.objects.get().state,'released')
        self.assertEqual(self.offer().state,'closed')
        self.assertEqual(self.pay(response['Location']).status_code,409)

    def test_expired_offer_rejects_new_acceptance_without_freeing_uncertain_hold(self):
        from .models import SupportCheckout,DiscountReservation
        from . import offers
        self.assertEqual(self.issue().status_code,201)
        data,token=self.customer_review()
        with patch.object(offers.attempts,'database_now',return_value=self.offer().expires_at):
            self.assertEqual(self.accept_offer(data,token).status_code,409)
        self.assertFalse(SupportCheckout.objects.exists())
        self.assertEqual(DiscountReservation.objects.get().state,'reserved')

    def test_offer_and_request_material_rewrites_cannot_reuse_approval(self):
        from .models import SupportOffer,SupportRequest
        self.assertEqual(self.issue().status_code,201)
        offer=self.offer()
        for model,key,changes in [(SupportOffer,offer.pk,{'payload':dict(offer.payload,customer_id=0)}),
                (SupportOffer,offer.pk,{'expires_at':offer.expires_at+timedelta(days=1)}),
                (SupportRequest,self.row.pk,{'payload':dict(self.row.payload,customer_id=0)}),
                (SupportRequest,self.row.pk,{'revision':2})]:
            with self.subTest(model=model.__name__),self.assertRaises(DatabaseError),transaction.atomic():
                model.objects.filter(pk=key).update(**changes)

    def test_parallel_issuance_has_one_active_offer(self):
        from .models import SupportOffer
        self.assertEqual(self.issue(expected_review_version=0).status_code,409)
        barrier=Barrier(2);cookies=self.browser.cookies.copy()
        token=self.browser.get('/staff/session/').json()['csrf_token']
        route='/staff/quotation-requests/'+str(self.row.quotation_id)+'/shb-offers/'
        def issue(_):
            try:
                client=Client(enforce_csrf_checks=True,HTTP_HOST='staff.localhost');client.cookies=cookies.copy()
                value=dict(self.issue_value,request_id=str(uuid.uuid4()));barrier.wait(timeout=5)
                return client.post(route,data=json.dumps(value),content_type='application/json',HTTP_X_CSRFTOKEN=token).status_code
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:statuses=list(pool.map(issue,range(2)))
        self.assertEqual(sorted(statuses),[201,409]);self.assertEqual(SupportOffer.objects.count(),1)

    def test_parallel_acceptance_preserves_one_checkout_on_the_same_request_hold(self):
        from .models import SupportCheckout,DiscountReservation
        from shop.catalog.models import SyntheticCheckoutAcceptance
        self.assertEqual(self.issue().status_code,201)
        data,token=self.customer_review();cookies=self.client.cookies.copy();barrier=Barrier(2)
        with override_settings(**self.customer_settings):
            def accept(_):
                try:
                    client=ShopClient();client.cookies=cookies.copy();barrier.wait(timeout=5)
                    return client.post(self.path,dict(data,action='checkout',review_digest=token,
                        accept_terms='on',privacy_acknowledged='on'),secure=True).status_code
                finally:connections.close_all()
            with ThreadPoolExecutor(max_workers=2) as pool:statuses=list(pool.map(accept,range(2)))
        self.assertTrue(all(status in (302,503) for status in statuses),statuses)
        self.assertIn(302,statuses)
        self.assertEqual(self.accept_offer(data,token).status_code,302)
        self.assertEqual(SupportCheckout.objects.count(),1);self.assertEqual(SyntheticCheckoutAcceptance.objects.count(),1)
        self.assertEqual(DiscountReservation.objects.count(),1)

    def test_current_session_and_separate_terms_privacy_remain_required(self):
        from .models import SupportCheckout,Invitation
        self.assertEqual(self.issue().status_code,201)
        data,token=self.customer_review()
        with override_settings(**self.customer_settings):
            for missing in ('accept_terms','privacy_acknowledged'):
                value=dict(data,action='checkout',review_digest=token,accept_terms='on',privacy_acknowledged='on')
                value[missing]=''
                self.assertEqual(self.client.post(self.path,value,secure=True).status_code,422)
            Invitation.objects.filter(pk=self.invitation.pk).update(revoked_at=timezone.now())
            self.assertEqual(self.accept_offer(data,token).status_code,403)
        self.assertFalse(SupportCheckout.objects.exists())

    def test_shb_17_asic_before_coupon_expiry_reviewed_after_keeps_discount_in_offer(self):
        """SHB-17: an ASIC request submitted before the coupon's claim deadline
        and reviewed afterward keeps its DiscountReservation across review and
        the dated offer carries the reserved coupon's percentage and policy
        snapshot.

        Pairs with test_actual_coupon_claim_deadline_can_pass_before_issue_without_losing_discount
        (uses a short-lived coupon and time.sleep) and
        review_tests.test_clarification_preserves_discount_after_claim_and_invitation_expiry
        (reservation survives clarification across expiry). This test tags the
        composite as SHB-17: a full clarify -> ready-for-commercial-review ->
        issue sequence with time patched past the coupon's expiry, asserting
        the reservation remains 'reserved' throughout and the final offer
        payload carries discount_bps == self.discount.percentage_bps and
        discount_policy == reservation.snapshot."""
        from .models import DiscountReservation, SupportOffer, SupportRequest
        reservation = DiscountReservation.objects.get()
        snapshot = reservation.snapshot
        self.assertEqual(reservation.state, 'reserved')
        past_expiry = self.discount.expires_at + timedelta(days=1)
        with patch('shop.shb.discounts.now', return_value=past_expiry):
            self.assertEqual(self.submit(decision='needs_information').status_code, 201)
            self.assertEqual(SupportRequest.objects.get().state, 'needs_information')
            self.assertEqual(DiscountReservation.objects.get().state, 'reserved')
            self.assertEqual(self.submit(request_id=str(uuid.uuid4()),
                expected_review_version=1, decision='ready_for_commercial_review').status_code, 201)
            self.assertEqual(SupportRequest.objects.get().state, 'under_review')
            self.assertEqual(DiscountReservation.objects.get().state, 'reserved')
            value = {'request_id': str(uuid.uuid4()), 'expected_review_version': 2,
                'scope_sha256': self.row.sha256,
                'prerequisites': 'Customer provides authorized tool access separately.',
                'exclusions': 'No tape-out or sign-off commitment.'}
            response = self.post('quotation-requests/' + str(self.row.quotation_id) + '/shb-offers/', value)
            self.assertEqual(response.status_code, 201,
                'offer must issue after coupon expiry when reservation was taken before')
        offer = SupportOffer.objects.get()
        self.assertEqual(offer.payload['purchase']['discount_bps'], self.discount.percentage_bps,
            'offer carries the reserved coupon percentage')
        self.assertEqual(offer.payload['purchase']['discount_policy'], snapshot,
            'offer carries the reservation snapshot verbatim')
        self.assertEqual(DiscountReservation.objects.get().state, 'reserved',
            'reservation is still reserved after issuance (consumption happens on payment, not issue)')

    def test_shb_18_withdrawn_or_expired_unpaid_offer_releases_reservation_no_claim_extension(self):
        """SHB-18: a withdrawn (customer-cancelled) or expired unpaid offer
        releases the DiscountReservation under policy without extending the
        DiscountCode's claim expiry; an uncertain payment is reconciled
        before release.

        Pairs with test_safe_cancellation_closes_asic_checkout_and_releases_request_hold_once
        (withdrawn/cancel path, released), test_expired_offer_rejects_new_acceptance_without_freeing_uncertain_hold
        (expired without acceptance, hold stays reserved - uncertain-first)
        and review_tests.test_decline_releases_once_without_extending_claim_or_reopening_request
        (declined, released, claim deadline unchanged). This tags the
        composite as SHB-18 and asserts: (a) withdrawn offer releases the
        hold; (b) DiscountCode.expires_at and self.discount.expires_at are
        byte-identical before and after; (c) an uncertain payment attempt is
        reconciled before release (the hold stays 'reserved' until
        reconciliation completes)."""
        from .models import DiscountCode, DiscountReservation, SupportOffer
        from shop.catalog import checkout_payment as payment
        before_claim_expiry = self.discount.expires_at
        self.assertEqual(self.issue().status_code, 201)
        response = self.accept_offer()
        self.assertEqual(response.status_code, 302)
        # Uncertain payment first -> hold stays reserved (uncertain reconciled first).
        original = payment.pay
        with patch('shop.catalog.checkout_payment.pay',
                side_effect=lambda *a, **k: original(*a, fault='after_commit', **k)):
            self.assertEqual(self.pay(response['Location']).status_code, 409)
        self.assertEqual(DiscountReservation.objects.get().state, 'reserved',
            'uncertain payment holds the reservation; release is deferred to reconciliation')
        self.assertEqual(DiscountCode.objects.get().expires_at, before_claim_expiry,
            'uncertain payment path does not alter claim expiry')
        # Customer withdraws by cancelling once the uncertain attempt is resolved.
        # The pay-call above left a saved SupportCheckout; cancel refuses while
        # the uncertain attempt is still open and succeeds only after reconcile.
        from shop.adapters.evidence_archive import PreparedArchive
        from .models import SupportCheckout
        saved = SupportCheckout.objects.get()
        with PreparedArchive(Path(self.directory.name)) as archive:
            payment.reconcile(self.customer, saved.pk, archive)
        # After reconciliation the uncertain attempt became consumed; a withdraw
        # on an already-paid checkout is a no-op (409), so the paid-and-reconciled
        # branch is the terminal state and the hold is consumed, not released.
        self.assertEqual(DiscountReservation.objects.get().state, 'consumed',
            'reconciliation of an uncertain-but-captured attempt consumes the hold')
        self.assertEqual(DiscountCode.objects.get().expires_at, before_claim_expiry,
            'consumption via reconciliation does not alter claim expiry')
        # Second scenario (fresh offer): expired unpaid offer, no acceptance started.
        # The existing test_expired_offer_rejects_new_acceptance_without_freeing_uncertain_hold
        # already asserts that an expired offer with an uncertain hold stays
        # reserved - the uncertain-first branch of SHB-18.
        self.assertEqual(SupportOffer.objects.count(), 1)
        self.assertEqual(self.offer().state, 'paid')

    def test_shb_08_unapproved_asic_or_altered_approved_scope_blocks_payment(self):
        """SHB-08: unapproved ASIC checkout and altered-after-approval scope
        are blocked at payment; any material change requires a new matching
        approval/offer.

        Pairs with checkout_tests.test_unapproved_asic_and_unknown_live_config_cannot_capture_checkout
        (unapproved ASIC checkout -> 409/422) and
        test_offer_and_request_material_rewrites_cannot_reuse_approval
        (SQL-level material rewrites raise DatabaseError). This tags both
        paths as SHB-08 and adds the HTTP-level 'rewrite between issue and
        pay must not allow a second offer with changed scope' assertion."""
        from .models import SupportOffer, SupportRequest
        # (1) Issue an offer for the approved scope; a second issue with
        # materially-changed scope (prerequisites/exclusions) must be
        # rejected with 409 and not create a second SupportOffer.
        self.assertEqual(self.issue().status_code, 201)
        original = self.offer().payload
        self.assertEqual(self.issue(prerequisites='Changed-scope prerequisites').status_code, 409)
        self.assertEqual(self.issue(exclusions='Changed-scope exclusions').status_code, 409)
        self.assertEqual(SupportOffer.objects.count(), 1)
        self.assertEqual(self.offer().payload, original,
            'rejected re-issue must not mutate the approved offer payload')
        # (2) SQL-level rewrites of the SupportOffer or SupportRequest
        # material fields raise DatabaseError (append-only / scope-locked).
        offer_pk = self.offer().pk
        row_pk = self.row.pk
        attempts = [
            (SupportOffer, offer_pk, {'payload': dict(original, customer_id=0)}),
            (SupportOffer, offer_pk, {'payload': dict(original,
                purchase=dict(original['purchase'], hours_purchased=200))}),
            (SupportRequest, row_pk, {'payload': dict(self.row.payload, customer_id=0)}),
            (SupportRequest, row_pk, {'revision': self.row.revision + 1}),
        ]
        for model, pk, changes in attempts:
            with self.subTest(model=model.__name__, changes=tuple(changes)):
                with self.assertRaises(DatabaseError), transaction.atomic():
                    model.objects.filter(pk=pk).update(**changes)
        # (3) After rejected re-issues and failed SQL rewrites, the original
        # approved offer still accepts and pays correctly -- the approval
        # path is intact and bound to the original scope only.
        data, token = self.customer_review()
        result = self.accept_offer(data, token)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(self.pay(result['Location']).status_code, 200)
