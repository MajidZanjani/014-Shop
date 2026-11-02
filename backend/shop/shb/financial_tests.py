"""SHB refunds retain original money/order identity and manual support decisions."""
import uuid
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
