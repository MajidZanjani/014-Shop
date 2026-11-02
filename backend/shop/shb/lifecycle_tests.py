"""Pre-acceptance ASIC closing and explicit replacement keep old evidence intact."""
import uuid
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

from django.db import DatabaseError, transaction
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
