"""Changed ASIC work becomes a new linked request with fresh review and acceptance."""
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch
from django.db import DatabaseError, connections, transaction
from django.test import TransactionTestCase, override_settings
from . import offer_tests
from .tests import form_data


@override_settings(SHB_SYNTHETIC_FIXTURE=True)
class RevisionTests(TransactionTestCase):
    client_class=offer_tests.OfferTests.client_class
    post=offer_tests.OfferTests.post
    challenge=offer_tests.OfferTests.challenge
    authenticated=offer_tests.OfferTests.authenticated
    customer_submit=offer_tests.OfferTests.customer_submit
    submit=offer_tests.OfferTests.submit
    setUp=offer_tests.OfferTests.setUp
    issue=offer_tests.OfferTests.issue
    customer_review=offer_tests.OfferTests.customer_review
    accept_offer=offer_tests.OfferTests.accept_offer
    pay=offer_tests.OfferTests.pay

    def offer(self):
        from .models import SupportOffer
        return SupportOffer.objects.select_related('request__invitation').get(request=self.row)

    def withdraw(self):
        from .models import RequestClosure
        self.assertEqual(self.issue().status_code,201)
        with override_settings(**self.customer_settings):
            path='/purchase/shb/offer/'+str(self.offer().pk)+'/'
            self.assertEqual(self.client.post(path,{'action':'withdraw','request_id':str(uuid.uuid4())},secure=True).status_code,200)
        self.closure=RequestClosure.objects.get()
        self.revision_path='/purchase/shb/revise/'+str(self.closure.pk)+'/'

    def revised(self, **changes):
        if not hasattr(self,'revision_data'):
            self.revision_data=form_data(variant='shb-asic-25h',quantity='3',assistance='Investigate a changed SLL IP integration objective.',
                accept_terms='',privacy_acknowledged='on',discount_code='',action='submit',request_id=str(uuid.uuid4()))
        with override_settings(**self.customer_settings):
            return self.client.post(self.revision_path,dict(self.revision_data,**changes),secure=True)

    def test_withdrawn_offer_can_start_blank_linked_revised_request_without_old_private_prefill(self):
        self.withdraw()
        with override_settings(**self.customer_settings):
            page=self.client.get(self.revision_path,secure=True)
        self.assertEqual(page.status_code,200)
        self.assertIsNone(page.context['form']['company_name'].value())
        self.assertNotContains(page,'buyer@synthetic.invalid')
        self.assertContains(page,'Revised ASIC request')

    def test_changed_work_and_quantity_create_fresh_unpaid_revision_and_preserve_old_scope(self):
        from .models import SupportRequest, RequestReplacement
        from shop.catalog.models import SyntheticCheckoutAcceptance
        self.withdraw();old=self.row.payload;old_offer=self.offer().payload
        response=self.revised()
        self.assertEqual(response.status_code,200)
        link=RequestReplacement.objects.select_related('request').get();child=link.request
        self.assertEqual(child.revision,2);self.assertEqual(link.previous_id,self.row.pk)
        self.assertEqual(child.payload['purchase']['hours_purchased'],75)
        self.assertEqual(child.payload['details']['assistance'],self.revision_data['assistance'])
        self.assertEqual(child.state,'submitted')
        self.row.refresh_from_db();self.assertEqual(self.row.payload,old)
        self.assertEqual(self.offer().payload,old_offer)
        self.assertEqual(self.revised().status_code,200)
        self.assertEqual(SupportRequest.objects.count(),2)
        self.assertFalse(SyntheticCheckoutAcceptance.objects.exists())

    def test_revision_retry_conflict_and_one_child_prevent_parallel_replacement_duplicates(self):
        from .models import RequestReplacement,SupportRequest
        self.withdraw();self.assertEqual(self.revised().status_code,200)
        self.assertEqual(self.revised(assistance='Different work on same retry key').status_code,409)
        self.assertEqual(self.revised(request_id=str(uuid.uuid4())).status_code,409)
        self.assertEqual(RequestReplacement.objects.count(),1);self.assertEqual(SupportRequest.objects.count(),2)

    def test_valid_code_is_freshly_claimed_after_old_release_without_extending_deadline(self):
        from .models import DiscountReservation, DiscountCode
        self.withdraw();self.assertEqual(self.revised(discount_code=self.code).status_code,200)
        self.assertEqual(DiscountReservation.objects.filter(state='released').count(),1)
        self.assertEqual(DiscountReservation.objects.filter(state='reserved').count(),1)
        self.assertEqual(DiscountCode.objects.get().expires_at,self.discount.expires_at)

    def test_expired_old_code_is_not_carried_into_changed_work_and_new_total_is_explicit(self):
        from .models import SupportRequest, RequestReplacement
        self.withdraw()
        with patch('shop.shb.discounts.now',return_value=self.discount.expires_at):
            self.assertEqual(self.revised(discount_code=self.code).status_code,422)
            self.assertFalse(RequestReplacement.objects.exists())
            response=self.revised(discount_code='')
        self.assertEqual(response.status_code,200)
        self.assertContains(response,'EUR 15,000.00')
        child=SupportRequest.objects.exclude(pk=self.row.pk).get()
        self.assertNotIn('discount_policy',child.payload['purchase'])

    def test_new_review_offer_acceptance_and_payment_use_only_new_revision(self):
        from .models import RequestReplacement,PaidOrder
        from shop.access.models import StaffQuotationGrant
        self.withdraw();original=self.offer();self.assertEqual(self.revised().status_code,200)
        self.row=RequestReplacement.objects.select_related('request__quotation').get().request
        self.grant=StaffQuotationGrant.objects.create(user=self.user,quotation=self.row.quotation,business_scope_version=2)
        self.route='quotation-requests/'+str(self.row.quotation_id)+'/shb-reviews/'
        self.value.update(scope_sha256=self.row.sha256,request_id=str(uuid.uuid4()),expected_review_version=0)
        del self.issue_value
        self.assertEqual(self.issue().status_code,201)
        self.assertEqual(self.offer().payload['request_revision'],2)
        response=self.accept_offer();self.assertEqual(response.status_code,302)
        self.assertEqual(self.pay(response['Location']).status_code,200)
        order=PaidOrder.objects.get()
        self.assertEqual(order.payload['purchase']['hours_purchased'],75)
        self.assertEqual(order.payload['asic_offer']['payload']['scope']['assistance'],self.revision_data['assistance'])
        original.refresh_from_db();self.assertEqual(original.state,'closed')

    def test_current_customer_project_and_asic_invitation_are_required_without_private_history(self):
        from .invitations import issue_fixture
        from .tests import ShopClient
        from django.contrib.auth import get_user_model
        self.withdraw()
        other=get_user_model().objects.create_user(username='other-revision-customer')
        with override_settings(**self.customer_settings):
            client=ShopClient()
            _,token=issue_fixture(customer=other,issuer=self.issuer,company_name='Other Company')
            client.get('/invite/'+token,secure=True)
            self.assertEqual(client.get(self.revision_path,secure=True).status_code,404)
            _,token=issue_fixture(customer=self.customer,issuer=self.issuer,
                company_name=self.invitation.company_name,project_reference='Different project')
            client.get('/invite/'+token,secure=True)
            self.assertEqual(client.get(self.revision_path,secure=True).status_code,404)

    def test_forged_fpga_quantity_and_missing_privacy_cannot_create_revision(self):
        from .models import RequestReplacement
        self.withdraw()
        for changes in ({'variant':'shb-fpga-10h'},{'quantity':'0'},{'privacy_acknowledged':''}):
            with self.subTest(changes=changes):self.assertEqual(self.revised(**changes).status_code,422)
        self.assertFalse(RequestReplacement.objects.exists())

    def test_link_and_both_request_revision_numbers_are_immutable(self):
        from .models import RequestReplacement,SupportRequest
        self.withdraw();self.assertEqual(self.revised().status_code,200)
        link=RequestReplacement.objects.get()
        for model,pk,changes in [(RequestReplacement,link.pk,{'session_digest':'0'*64}),
                (SupportRequest,link.request_id,{'revision':5}),(SupportRequest,self.row.pk,{'revision':5})]:
            with self.subTest(model=model.__name__),self.assertRaises(DatabaseError),transaction.atomic():
                model.objects.filter(pk=pk).update(**changes)

    def test_parallel_changed_requests_have_one_child_and_one_new_acknowledgement(self):
        from .tests import ShopClient
        from .models import RequestReplacement,TransactionNotice
        self.withdraw();self.revision_data=form_data(variant='shb-asic-25h',quantity='3',assistance='Changed SLL IP objective.',
            accept_terms='',privacy_acknowledged='on',discount_code='',action='submit')
        cookies=self.client.cookies.copy();barrier=Barrier(2)
        with override_settings(**self.customer_settings):
            def submit(_):
                try:
                    client=ShopClient();client.cookies=cookies.copy();barrier.wait(timeout=5)
                    return client.post(self.revision_path,dict(self.revision_data,request_id=str(uuid.uuid4())),secure=True).status_code
                finally:connections.close_all()
            with ThreadPoolExecutor(max_workers=2) as pool:statuses=list(pool.map(submit,range(2)))
        self.assertEqual(sorted(statuses),[200,409])
        self.assertEqual(RequestReplacement.objects.count(),1)
        self.assertEqual(TransactionNotice.objects.filter(event='request-received').count(),2)
