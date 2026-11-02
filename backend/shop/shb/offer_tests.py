"""Dated ASIC offers stay bound to the reviewed request and shared payment."""
import uuid

from django.test import TransactionTestCase, override_settings

from .review_tests import RequestReviewTests


@override_settings(SHB_SYNTHETIC_FIXTURE=True)
class OfferTests(TransactionTestCase):
    client_class = RequestReviewTests.client_class
    setUp = RequestReviewTests.setUp
    post = RequestReviewTests.post
    challenge = RequestReviewTests.challenge
    authenticated = RequestReviewTests.authenticated
    customer_submit = RequestReviewTests.customer_submit
    submit = RequestReviewTests.submit

    def issue(self, **changes):
        self.assertEqual(self.submit(decision='ready_for_commercial_review').status_code, 201)
        value = {'request_id': str(uuid.uuid4()), 'expected_review_version': 1,
            'scope_sha256': self.row.sha256, 'prerequisites': 'Customer provides authorized tool access separately.',
            'exclusions': 'No tape-out or sign-off commitment.'}
        value.update(changes)
        return self.post('quotation-requests/' + str(self.row.quotation_id) + '/shb-offers/', value)

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
        self.assertEqual(offer.payload['purchase']['hours_purchased'], 50)
        self.assertEqual(offer.payload['purchase']['total_minor'], 875000)
        self.assertEqual(DiscountReservation.objects.get().state, 'reserved')
        self.assertFalse(SyntheticCheckout.objects.exists())
        self.assertFalse(SyntheticPaymentAttempt.objects.exists())
