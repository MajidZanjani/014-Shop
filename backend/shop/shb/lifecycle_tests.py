"""Pre-acceptance ASIC closing and explicit replacement keep old evidence intact."""
import uuid
from concurrent.futures import ThreadPoolExecutor
import json
from threading import Barrier
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

from django.db import DatabaseError, connection, connections, transaction
from django.test import TransactionTestCase, override_settings
from django.utils import timezone

from . import offer_tests


@override_settings(SHB_SYNTHETIC_FIXTURE=True)
class LifecycleTests(TransactionTestCase):
    client_class = offer_tests.OfferTests.client_class
    post = offer_tests.OfferTests.post
    challenge = offer_tests.OfferTests.challenge
    authenticated = offer_tests.OfferTests.authenticated
    customer_submit = offer_tests.OfferTests.customer_submit
    submit = offer_tests.OfferTests.submit
    setUp = offer_tests.OfferTests.setUp
    issue = offer_tests.OfferTests.issue
    offer = offer_tests.OfferTests.offer
    customer_review = offer_tests.OfferTests.customer_review
    accept_offer = offer_tests.OfferTests.accept_offer
    pay = offer_tests.OfferTests.pay

    def close(self, **changes):
        if not hasattr(self, 'close_value'):
            self.row.refresh_from_db()
            self.row.quotation.refresh_from_db()
            self.close_value = {'request_id': str(uuid.uuid4()),
                'expected_review_version': self.row.quotation.review_version,
                'scope_sha256': self.row.sha256, 'offer_id': '', 'action': 'withdraw',
                'reason': 'Customer asked SLL to withdraw this unpaid request.'}
        return self.post('quotation-requests/' + str(self.row.quotation_id) + '/shb-closing/',
            dict(self.close_value, **changes))

    def test_assigned_withdrawal_releases_request_without_manufacturing_acceptance(self):
        from .models import SupportRequest, DiscountReservation
        from shop.catalog.models import SyntheticCheckoutAcceptance
        from shop.payments.models import SyntheticPaymentAttempt
        response = self.close()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(SupportRequest.objects.get().state, 'withdrawn')
        self.assertEqual(DiscountReservation.objects.get().state, 'released')
        self.assertFalse(SyntheticCheckoutAcceptance.objects.exists())
        self.assertFalse(SyntheticPaymentAttempt.objects.exists())
        self.assertEqual(self.close().status_code, 200)

    def test_issued_offer_withdrawal_preserves_exact_offer_and_releases_once(self):
        from .models import DiscountReservation, DiscountCode
        self.assertEqual(self.issue().status_code, 201)
        offer = self.offer(); payload = offer.payload; receipt = offer.archive_receipt
        self.assertEqual(self.close(offer_id=str(offer.pk)).status_code, 201)
        self.assertEqual(self.close(offer_id=str(offer.pk)).status_code, 200)
        offer.refresh_from_db(); hold = DiscountReservation.objects.get()
        self.assertEqual(offer.state, 'closed')
        self.assertEqual(offer.payload, payload); self.assertEqual(offer.archive_receipt, receipt)
        self.assertEqual(hold.state, 'released'); self.assertIsNotNone(hold.release_lifecycle_id)
        self.assertEqual(DiscountCode.objects.get().expires_at, self.discount.expires_at)
        self.assertEqual(self.close(offer_id=str(offer.pk), reason='Different reason').status_code, 409)
        self.assertEqual(self.issue().status_code, 409)

    def test_archive_interruption_fences_acceptance_and_worker_finishes_saved_intent(self):
        from shop.adapters.evidence_archive import PreparedArchive, ArchiveError
        from shop.worker.services import execute_once
        from .models import RequestClosure, DiscountReservation, SupportRequest
        self.assertEqual(self.issue().status_code, 201)
        value, token = self.customer_review()
        with patch.object(PreparedArchive, 'publish', side_effect=ArchiveError('unavailable')):
            self.assertEqual(self.close(offer_id=str(self.offer().pk)).status_code, 503)
        intent = RequestClosure.objects.get()
        self.assertIsNone(intent.applied_at)
        self.assertEqual(DiscountReservation.objects.get().state, 'reserved')
        self.assertEqual(self.accept_offer(value, token).status_code, 409)
        self.assertTrue(execute_once())
        intent.refresh_from_db()
        self.assertIsNotNone(intent.applied_at); self.assertTrue(intent.archive_receipt)
        self.assertEqual(SupportRequest.objects.get().state, 'withdrawn')
        self.assertEqual(DiscountReservation.objects.get().state, 'released')

    def test_replacement_retains_hold_requires_fresh_review_and_keeps_old_offer_closed(self):
        from .models import SupportOffer, DiscountReservation
        self.assertEqual(self.issue().status_code, 201)
        original = self.offer(); old_payload = original.payload
        self.assertEqual(self.close(offer_id=str(original.pk), action='replace',
            reason='Reissue the unchanged scope with a fresh reviewed offer.').status_code, 201)
        self.assertEqual(DiscountReservation.objects.get().state, 'reserved')
        self.assertEqual(self.issue(request_id=str(uuid.uuid4())).status_code, 409)
        self.assertEqual(self.submit(request_id=str(uuid.uuid4()), expected_review_version=1,
            decision='ready_for_commercial_review', message='The unchanged scope remains feasible.').status_code, 201)
        self.assertEqual(self.issue(request_id=str(uuid.uuid4()), expected_review_version=2).status_code, 201)
        self.assertEqual(SupportOffer.objects.count(), 2)
        original.refresh_from_db(); self.assertEqual(original.state, 'closed')
        self.assertEqual(original.payload, old_payload)
        current = SupportOffer.objects.get(state='issued')
        self.assertEqual(current.revision, 2)
        self.assertEqual(current.payload['purchase']['discount_policy'], original.payload['purchase']['discount_policy'])
        self.assertEqual(DiscountReservation.objects.count(), 1)

    def test_failed_offer_preparation_can_be_abandoned_without_claiming_publication(self):
        from shop.adapters.evidence_archive import PreparedArchive, ArchiveError
        from .models import DiscountReservation
        with patch.object(PreparedArchive, 'publish', side_effect=ArchiveError('unavailable')):
            self.assertEqual(self.issue().status_code, 503)
        offer = self.offer()
        self.assertEqual(self.close(offer_id=str(offer.pk)).status_code, 201)
        offer.refresh_from_db()
        self.assertEqual(offer.state, 'abandoned')
        self.assertIsNone(offer.published_at); self.assertEqual(offer.archive_receipt, {})
        self.assertEqual(DiscountReservation.objects.get().state, 'released')

    def test_accepted_and_uncertain_payment_cannot_use_preacceptance_closing(self):
        from .models import DiscountReservation, RequestClosure
        from shop.catalog import checkout_payment as payment
        self.assertEqual(self.issue().status_code, 201)
        response = self.accept_offer(); self.assertEqual(response.status_code, 302)
        self.assertEqual(self.close(offer_id=str(self.offer().pk)).status_code, 409)
        original = payment.pay
        with patch.object(payment, 'pay', side_effect=lambda *a, **k: original(*a, fault='after_commit', **k)):
            self.assertEqual(self.pay(response['Location']).status_code, 409)
        self.assertEqual(self.close(offer_id=str(self.offer().pk), action='expire').status_code, 409)
        self.assertFalse(RequestClosure.objects.exists())
        self.assertEqual(DiscountReservation.objects.get().state, 'reserved')

    def test_no_get_effect_and_current_exact_staff_scope_is_required(self):
        from .models import RequestClosure
        route = '/staff/quotation-requests/' + str(self.row.quotation_id) + '/shb-closing/'
        self.assertEqual(self.browser.get(route).status_code, 405)
        self.grant.business_scope_version = 0; self.grant.save(update_fields=['business_scope_version'])
        self.assertEqual(self.close().status_code, 403)
        self.grant.business_scope_version = 1; self.grant.save(update_fields=['business_scope_version'])
        session = self.browser.session; marker = session['shop_staff_mfa']; marker['verified_at'] -= 301
        session['shop_staff_mfa'] = marker; session.save()
        self.assertEqual(self.close().status_code, 403)
        self.assertFalse(RequestClosure.objects.exists())

    def test_scope_version_offer_and_unknown_fields_cannot_close_or_free_another_hold(self):
        from .models import DiscountReservation, RequestClosure
        self.assertEqual(self.issue().status_code, 201)
        identity = str(self.offer().pk)
        for changes, status in [({'scope_sha256': '0'*64}, 409),
                ({'expected_review_version': 0}, 409), ({'offer_id': ''}, 409),
                ({'offer_id': str(uuid.uuid4())}, 409), ({'reason': ''}, 400),
                ({'action': 'erase'}, 400), ({'customer_id': self.customer.pk}, 400)]:
            with self.subTest(change=changes):
                self.assertEqual(self.close(**dict({'offer_id':identity}, **changes)).status_code, status)
        self.assertFalse(RequestClosure.objects.exists())
        self.assertEqual(DiscountReservation.objects.get().state, 'reserved')

    def test_unexpired_offer_cannot_be_finally_expired(self):
        from .models import RequestClosure, DiscountReservation
        self.assertEqual(self.issue().status_code, 201)
        self.assertEqual(self.close(offer_id=str(self.offer().pk), action='expire').status_code, 409)
        self.assertFalse(RequestClosure.objects.exists())
        self.assertEqual(DiscountReservation.objects.get().state, 'reserved')

    def test_postgresql_rejects_unproved_release_and_closing_history_rewrites(self):
        from .models import DiscountReservation, RequestClosure
        self.assertEqual(self.close().status_code, 201)
        closure = RequestClosure.objects.get(); hold = DiscountReservation.objects.get()
        for model, pk, changes in [(RequestClosure, closure.pk, {'payload':dict(closure.payload, reason='Changed')}),
                (DiscountReservation, hold.pk, {'state':'reserved','release_lifecycle_id':None})]:
            with self.subTest(model=model.__name__), self.assertRaises(DatabaseError), transaction.atomic():
                model.objects.filter(pk=pk).update(**changes)

    def test_native_customer_withdrawal_is_deliberate_scoped_and_repeat_safe(self):
        from .models import DiscountReservation, RequestClosure
        self.assertEqual(self.issue().status_code, 201)
        path='/purchase/shb/offer/'+str(self.offer().pk)+'/'
        value={'action':'withdraw','request_id':str(uuid.uuid4())}
        with override_settings(**self.customer_settings):
            self.assertContains(self.client.get(path,secure=True),'Withdraw unpaid offer and request')
            self.assertFalse(RequestClosure.objects.exists())
            first=self.client.post(path,value,secure=True)
            self.assertContains(first,'have been withdrawn')
            self.assertContains(self.client.post(path,value,secure=True),'have been withdrawn')
        saved=RequestClosure.objects.get()
        self.assertEqual(saved.payload['actor']['kind'],'invitation-bearer')
        self.assertIs(saved.payload['actor']['named_identity_verified'],False)
        self.assertEqual(DiscountReservation.objects.get().state,'released')

    def expired_fixture(self):
        """Seed an explicitly synthetic pre-existing expired snapshot in the disposable DB.

        This bypass is only fixture setup: normal issuance cannot backdate an
        offer. Every tested closing/reissue write runs with all guards enabled.
        No real 14-day waiting or historic authorization is claimed by this test.
        """
        from shop.adapters.evidence_archive import PreparedArchive, ArchiveError, manifest
        from . import catalog
        from .models import SupportOffer, SupportRequest
        with patch.object(PreparedArchive,'publish',side_effect=ArchiveError('fixture preparation')):
            self.assertEqual(self.issue().status_code,503)
        offer=self.offer();at=timezone.now()-timedelta(days=15)
        payload=dict(offer.payload,issued_at=at.isoformat(),expires_at=(at+timedelta(days=14)).isoformat())
        with PreparedArchive(Path(self.directory.name)) as archive:
            receipt=manifest(archive.publish(offer.pk,catalog.canonical(payload)))
        with transaction.atomic(),connection.cursor() as cursor:
            cursor.execute('ALTER TABLE public.shb_supportoffer DISABLE TRIGGER shb_offer_guard')
            try:
                SupportOffer.objects.filter(pk=offer.pk).update(payload=payload,sha256=catalog.digest(payload),
                    issued_at=at,expires_at=at+timedelta(days=14),published_at=at,archive_receipt=receipt,state='issued')
                SupportRequest.objects.filter(pk=self.row.pk).update(state='offer_issued')
                from .transaction_mail import queue
                offer.refresh_from_db();queue('offer-issued',offer)
                cursor.execute('SET CONSTRAINTS ALL IMMEDIATE')
            finally:cursor.execute('ALTER TABLE public.shb_supportoffer ENABLE TRIGGER shb_offer_guard')
        offer.refresh_from_db()
        return offer

    def test_worker_final_expiry_releases_once_and_does_not_extend_coupon_or_invitation(self):
        from shop.worker.services import execute_once
        from .models import DiscountReservation, RequestClosure, DiscountCode, Invitation
        offer=self.expired_fixture()
        self.assertTrue(execute_once())
        offer.refresh_from_db();self.row.refresh_from_db()
        self.assertEqual(offer.state,'closed');self.assertEqual(self.row.state,'offer_expired')
        self.assertEqual(DiscountReservation.objects.get().state,'released')
        self.assertTrue(RequestClosure.objects.get().archive_receipt)
        from .lifecycle import recover_once
        self.assertFalse(recover_once())
        self.assertEqual(DiscountCode.objects.get().expires_at,self.discount.expires_at)
        self.assertEqual(Invitation.objects.get().expires_at,self.invitation.expires_at)

    def test_expired_offer_reissue_gets_fresh_price_and_acceptance_without_reclaiming_old_hold(self):
        from shop.worker.services import execute_once
        from .models import SupportOffer, DiscountReservation
        original=self.expired_fixture();self.assertTrue(execute_once())
        self.assertEqual(self.submit(request_id=str(uuid.uuid4()), expected_review_version=1,
            decision='ready_for_commercial_review',message='Scope and current eligibility revalidated.').status_code,201)
        self.assertEqual(self.issue(request_id=str(uuid.uuid4()),expected_review_version=2).status_code,201)
        replacement=SupportOffer.objects.get(state='issued')
        self.assertNotEqual(replacement.pk,original.pk)
        self.assertNotIn('discount_policy',replacement.payload['purchase'])
        self.assertEqual(DiscountReservation.objects.get().state,'released')
        self.path='/purchase/shb/offer/'+str(replacement.pk)+'/'
        with override_settings(**self.customer_settings):
            page=self.client.get(self.path,secure=True)
            self.assertContains(page,'EUR 10,000.00')
            self.assertEqual(page.context['form']['company_name'].value(),None)

    def test_acceptance_and_withdrawal_race_has_one_safe_winner(self):
        from .tests import ShopClient
        from .models import DiscountReservation, RequestClosure
        from shop.catalog.models import SyntheticCheckoutAcceptance
        self.assertEqual(self.issue().status_code,201)
        value,token=self.customer_review();barrier=Barrier(2);cookies=self.client.cookies.copy()
        with override_settings(**self.customer_settings):
            def act(withdraw):
                try:
                    client=ShopClient();client.cookies=cookies.copy();barrier.wait(timeout=5)
                    data={'action':'withdraw','request_id':str(uuid.uuid4())} if withdraw else dict(value,
                        action='checkout',review_digest=token,accept_terms='on',privacy_acknowledged='on')
                    response=client.post(self.path,data,secure=True)
                    return response.status_code,response.context.get('error') if response.context else None
                finally:connections.close_all()
            with ThreadPoolExecutor(max_workers=2) as pool: statuses=list(pool.map(act,(True,False)))
        self.assertTrue(all(status in (200,302,409,503) for status,_ in statuses),statuses)
        for status,error in statuses:
            if status==503:self.assertEqual(error,'Required recovery evidence is unavailable.')
        # The shared archive deliberately uses a nonblocking directory lock.
        # An unavailable writer is not success: recover the saved closing
        # intent, or retry the exact acceptance only if no closing was admitted.
        from . import lifecycle
        if lifecycle.pending().exists():self.assertTrue(lifecycle.recover_once())
        if (not SyntheticCheckoutAcceptance.objects.filter(simulated_accepted_at__isnull=False).exists()
                and not RequestClosure.objects.filter(applied_at__isnull=False).exists()):
            self.assertEqual(self.accept_offer(value,token).status_code,302)
        accepted=SyntheticCheckoutAcceptance.objects.filter(simulated_accepted_at__isnull=False).exists()
        closed=RequestClosure.objects.filter(applied_at__isnull=False).exists()
        self.assertNotEqual(accepted,closed)
        self.assertEqual(DiscountReservation.objects.get().state,'reserved' if accepted else 'released')

    def test_pending_intent_cannot_release_concession_without_archived_application(self):
        from shop.adapters.evidence_archive import PreparedArchive, ArchiveError
        from .models import RequestClosure, DiscountReservation, SupportOffer
        self.assertEqual(self.issue().status_code,201)
        with patch.object(PreparedArchive,'publish',side_effect=ArchiveError('unavailable')):
            self.assertEqual(self.close(offer_id=str(self.offer().pk)).status_code,503)
        saved=RequestClosure.objects.get();hold=DiscountReservation.objects.get()
        with self.assertRaisesMessage(DatabaseError,'exact archived request closing'),transaction.atomic():
            DiscountReservation.objects.filter(pk=hold.pk).update(state='released',release_lifecycle=saved)
        with self.assertRaises(DatabaseError),transaction.atomic():
            SupportOffer.objects.filter(pk=self.offer().pk).update(state='closed')
        self.assertEqual(DiscountReservation.objects.get().state,'reserved')

    def test_missing_live_authority_and_revoked_customer_session_cannot_close(self):
        from .models import RequestClosure, Invitation
        self.assertEqual(self.issue().status_code,201)
        with override_settings(SHB_SYNTHETIC_FIXTURE=False):
            self.assertEqual(self.close(offer_id=str(self.offer().pk)).status_code,503)
        path='/purchase/shb/offer/'+str(self.offer().pk)+'/'
        Invitation.objects.filter(pk=self.invitation.pk).update(revoked_at=timezone.now())
        with override_settings(**self.customer_settings):
            self.assertEqual(self.client.post(path,{'action':'withdraw','request_id':str(uuid.uuid4())},secure=True).status_code,403)
        self.assertFalse(RequestClosure.objects.exists())

    def test_scoped_staff_html_closing_form_uses_csrf_and_records_reason(self):
        from urllib.parse import urlencode
        from .models import RequestClosure
        self.assertContains(self.browser.get(self.detail,HTTP_ACCEPT='text/html'),'Confirm closing action')
        token=self.browser.cookies['shop_staff_csrftoken'].value
        value={'request_id':str(uuid.uuid4()),'expected_review_version':'0','scope_sha256':self.row.sha256,
            'offer_id':'','action':'withdraw','reason':'Customer requested closure through the support channel.',
            'csrfmiddlewaretoken':token}
        route='/staff/quotation-requests/'+str(self.row.quotation_id)+'/shb-closing/'
        response=self.browser.post(route,data=urlencode(value),content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code,303)
        self.assertEqual(RequestClosure.objects.get().payload['reason'],value['reason'])
