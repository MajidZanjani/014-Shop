"""Protected invitation revocation, exact staff scope and recoverable audit."""
from django.test import TransactionTestCase, override_settings
from .review_tests import RequestReviewTests


@override_settings(SHB_SYNTHETIC_FIXTURE=True)
class InvitationAdminTests(TransactionTestCase):
    client_class=RequestReviewTests.client_class
    post=RequestReviewTests.post
    challenge=RequestReviewTests.challenge
    authenticated=RequestReviewTests.authenticated
    customer_submit=RequestReviewTests.customer_submit
    setUp=RequestReviewTests.setUp

    def test_staff_home_exposes_assigned_invitation_administration(self):
        response=self.browser.get('/staff/',HTTP_ACCEPT='text/html')
        self.assertEqual(response.status_code,200)
        self.assertTrue(b'Assigned invitations' in response.content)
