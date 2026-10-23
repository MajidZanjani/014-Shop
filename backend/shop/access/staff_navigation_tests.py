"""Real-PG staff navigation; current assignments and exact retained scopes."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import io
import json
from pathlib import Path
import re
from unittest.mock import patch
import uuid
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import connection, connections
from django.test import Client, TransactionTestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from shop.catalog.models import CartSnapshot, QuotationRequest, QuotationReview, DraftCart
from shop.catalog import binding_tests as bindings
from . import staff_tests, preparation_snapshot_tests as fixtures
from .models import PreparationAssessment, StaffCredential, StaffQuotationGrant
from .preparation_snapshots import authorized_history
from .quotation_review import history_rows

QUEUE='/staff/quotation-requests/'


def private(test,response):
    test.assertEqual(response['Cache-Control'],'no-store')
    test.assertEqual(response['Referrer-Policy'],'no-referrer')
    test.assertIn('Cookie',response['Vary'])
    test.assertIn("form-action 'none'",response['Content-Security-Policy'])


def login_staff(test,user,client):
    before=set(Path(test.directory.name).iterdir())
    test.assertEqual(test.post('login/',{'username':user.username,'password':test.password},client).status_code,200)
    added=set(Path(test.directory.name).iterdir())-before;test.assertEqual(len(added),1)
    code=re.search(r'^Code: (.+)$',added.pop().read_text(),re.M)[1]
    test.assertEqual(test.post('verify/',{'code':code},client).status_code,200)


@override_settings(**staff_tests.STAFF_SETTINGS)
class StaffQueueNavigationTests(TransactionTestCase):
    post=staff_tests.StaffTests.post
    challenge=staff_tests.StaffTests.challenge
    authenticated=staff_tests.StaffTests.authenticated
    grant=staff_tests.StaffTests.grant

    def setUp(self):
        staff_tests.StaffTests.setUp(self)
        self.authenticated();self.grant();self.version=1

    def add(self,assigned=True):
        self.version+=1;original=self.quotation.snapshot
        snapshot=CartSnapshot.objects.create(cart=self.quotation.cart,version=self.version,request_id=uuid.uuid4(),
            catalog_revision=original.catalog_revision,lines=original.lines,evaluation=original.evaluation)
        row=QuotationRequest.objects.create(cart=self.quotation.cart,snapshot=snapshot,request_id=uuid.uuid4())
        if assigned:StaffQuotationGrant.objects.create(user=self.user,quotation=row)
        return row

    def test_queue_pages_are_stable_with_timestamp_ties_and_later_insert(self):
        rows=[self.quotation]+[self.add() for _ in range(24)]
        QuotationRequest.objects.update(created_at=timezone.now()-timedelta(days=1))
        expected=[str(row.pk) for row in sorted(rows,key=lambda row:row.pk.int,reverse=True)]
        first=self.browser.get(QUEUE);private(self,first);value=first.json()
        self.assertEqual([row['id'] for row in value['requests']],expected[:20])
        self.assertEqual(value['older'],expected[19]);self.assertEqual(value['limit'],20)
        self.add()  # Newer work must not move the already selected older page.
        older=self.browser.get(QUEUE+'?before='+value['older']).json()
        self.assertEqual([row['id'] for row in older['requests']],expected[20:])
        self.assertIsNone(older['older'])
        html=self.browser.get(QUEUE,HTTP_ACCEPT='text/html')
        self.assertContains(html,'Older assigned requests');self.assertContains(html,'aria-label="Assigned request pages"')
        self.assertNotContains(html,'<form');private(self,html)

    def test_cursor_requires_current_assignment_and_does_not_follow_foreign_rows(self):
        self.assertEqual(self.browser.get(QUEUE+'?before='+str(self.add(assigned=False).pk)).status_code,404)
        self.assertEqual(self.browser.get(QUEUE+'?before='+str(uuid.uuid4())).status_code,404)
        call_command('local_staff','revoke-grant',username=self.user.username,quotation=str(self.quotation.pk),stdout=io.StringIO())
        self.assertEqual(self.browser.get(QUEUE+'?before='+str(self.quotation.pk)).status_code,404)
        self.assertEqual(self.browser.get(QUEUE).json()['requests'],[])

    def test_queue_cursor_is_scoped_to_authenticated_staff_identity(self):
        other=get_user_model().objects.create_user(username='other-navigation-reviewer',password=self.password,is_staff=True)
        StaffCredential.objects.create(user=other)
        browser=Client(enforce_csrf_checks=True,HTTP_HOST='staff.localhost')
        login_staff(self,other,browser)
        self.assertEqual(browser.get(QUEUE).json()['requests'],[])
        self.assertEqual(browser.get(QUEUE+'?before='+str(self.quotation.pk)).status_code,404)

    def test_queue_strict_queries_closed_projection_and_no_writes(self):
        for query in ('before=','before=bad','before='+self.quotation.pk.hex,
                      'before=AAAAAAAA-AAAA-4AAA-8AAA-AAAAAAAAAAAA','before=1&before=2','owner=1',
                      'before='+str(self.quotation.pk)+'&next=/private'):
            self.assertEqual(self.browser.get(QUEUE+'?'+query).status_code,400,query)
        with CaptureQueriesContext(connection) as queries:
            value=self.browser.get(QUEUE).json()
        self.assertEqual(set(value),{'requests','limit','older'})
        self.assertEqual(set(value['requests'][0]),{'id','version','state','review_version'})
        self.assertFalse(any(re.match(r'\s*(INSERT|UPDATE|DELETE)\b',row['sql'],re.I) for row in queries))
        self.assertNotIn(self.user.username,json.dumps(value));self.assertNotIn(str(self.credential.generation),json.dumps(value))
        with override_settings(SHOP_ENV='production'):self.assertEqual(self.browser.get(QUEUE).status_code,404)
        self.assertEqual(Client(HTTP_HOST='staff.localhost').get(QUEUE).status_code,403)


@override_settings(**staff_tests.STAFF_SETTINGS)
class PreparationHistoryNavigationTests(TransactionTestCase):
    setUp=fixtures.PreparationSnapshotTests.setUp
    post=fixtures.PreparationSnapshotTests.post
    challenge=fixtures.PreparationSnapshotTests.challenge
    authenticated=fixtures.PreparationSnapshotTests.authenticated
    grant=fixtures.PreparationSnapshotTests.grant
    owner_context=fixtures.PreparationSnapshotTests.owner_context
    attach=fixtures.PreparationSnapshotTests.attach
    business=fixtures.PreparationSnapshotTests.business
    enable_private=fixtures.PreparationSnapshotTests.enable_private
    prepare=fixtures.PreparationSnapshotTests.prepare
    form=fixtures.PreparationSnapshotTests.form
    submit_capture=fixtures.PreparationSnapshotTests.submit_capture

    def start(self):
        self.prepare();self.history=self.snap+'history/'

    def capture_assessment(self):
        response=self.submit_capture(self.form());self.assertEqual(response.status_code,201)
        return response.json()['snapshot']

    def test_history_pagination_private_metadata_and_navigation_without_writes(self):
        self.start()
        # Actual supported capture requests, rather than manufactured assessment rows.
        for _ in range(23):self.capture_assessment()
        before=list(PreparationAssessment.objects.values())
        with CaptureQueriesContext(connection) as queries:
            first=self.browser.get(self.history);html=self.browser.get(self.history,HTTP_ACCEPT='text/html')
        value=first.json();self.assertEqual(set(value),{'snapshots','limit','older'})
        self.assertEqual([row['version'] for row in value['snapshots']],list(range(23,3,-1)))
        self.assertEqual(value['older'],4);self.assertEqual(value['limit'],20)
        older=self.browser.get(self.history+'?before=4').json()
        self.assertEqual([row['version'] for row in older['snapshots']],[3,2,1]);self.assertIsNone(older['older'])
        for row in value['snapshots']:self.assertEqual(set(row),{'version','business_version','review_version','created_at'})
        for response in (first,html):private(self,response)
        for secret in ('<form','<input','<script','assessment_digest','scope_digest','captured_by','staff_generation','BUSINESS_SCOPE_ONE_PRIVATE_SYNTHETIC'):
            self.assertNotIn(secret,html.content.decode())
        self.assertContains(html,'?before=4');self.assertContains(html,self.snap+'23/')
        self.assertContains(self.browser.get(self.detail,HTTP_ACCEPT='text/html'),self.history)
        self.assertContains(self.browser.get(self.snap,HTTP_ACCEPT='text/html'),self.history)
        self.assertContains(self.browser.get(self.snap+'1/',HTTP_ACCEPT='text/html'),self.history)
        self.assertFalse(any(re.match(r'\s*(INSERT|UPDATE|DELETE)\b',row['sql'],re.I) for row in queries))
        self.assertEqual(list(PreparationAssessment.objects.values()),before)

    def test_historical_permissions_are_independent_of_new_current_scope(self):
        self.start();self.capture_assessment()
        self.assertEqual(self.attach().status_code,303);self.enable_private(1);self.capture_assessment()
        self.business(2,'PRIVATE_NEW_NAVIGATION_SCOPE')
        self.assertEqual(self.attach(dict(self.request,request_id=str(uuid.uuid4()),expected_scope_version='1',business_version='2')).status_code,303)
        self.assertEqual(self.browser.get(self.snap).status_code,403)
        self.assertEqual([row['version'] for row in self.browser.get(self.history).json()['snapshots']],[2,1])

        self.enable_private(2)
        self.assertEqual(self.browser.get(self.history+'?before=2').status_code,404)
        self.capture_assessment()
        self.assertEqual([row['version'] for row in self.browser.get(self.history).json()['snapshots']],[3,1])
        call_command('local_staff','revoke-business',username=self.user.username,quotation=str(self.quotation.pk),stdout=io.StringIO())
        self.assertEqual([row['version'] for row in self.browser.get(self.history).json()['snapshots']],[1])
        self.assertEqual(self.browser.get(self.history+'?before=3').status_code,404)
        call_command('local_staff','revoke-grant',username=self.user.username,quotation=str(self.quotation.pk),stdout=io.StringIO())
        self.assertEqual(self.browser.get(self.history).status_code,404)

    def test_history_queries_methods_mfa_customer_and_environment_boundaries(self):
        self.start();self.capture_assessment()
        for query in ('before=','before=0','before=-1','before=01','before=1.0','before=true',
                      'before=1000000001','before=1&before=1','scope=1','before=1&next=/private'):
            self.assertEqual(self.browser.get(self.history+'?'+query).status_code,400,query)
        self.assertEqual(self.browser.get(self.history+'?before=99').status_code,404)
        for method in ('post','put','delete','patch'):
            response=getattr(self.browser,method)(self.history,HTTP_X_CSRFTOKEN=self.browser.cookies['shop_staff_csrftoken'].value)
            self.assertEqual(response.status_code,405)
        with self.owner_context():self.assertEqual(self.owner_client.get(self.history).status_code,404)
        with override_settings(SHOP_ENV='production'):self.assertEqual(self.browser.get(self.history).status_code,404)
        self.credential.enabled=False;self.credential.save(update_fields=['enabled'])
        self.assertEqual(self.browser.get(self.history).status_code,403)

    def test_history_retains_committed_prefix_during_supported_new_capture(self):
        self.start();self.capture_assessment();value=self.form()
        def after_parent(quotation,grant):
            def capture():
                client=Client(enforce_csrf_checks=True,HTTP_HOST='staff.localhost');client.cookies=self.browser.cookies.copy()
                try:
                    return client.post(self.snap,data=json.dumps(value),content_type='application/json',
                        HTTP_X_CSRFTOKEN=client.cookies['shop_staff_csrftoken'].value).status_code
                finally:connections.close_all()
            with ThreadPoolExecutor(max_workers=1) as pool:self.assertEqual(pool.submit(capture).result(timeout=10),201)
            return authorized_history(quotation,grant)
        with patch('shop.access.preparation_history.authorized_history',side_effect=after_parent):
            first=self.browser.get(self.history).json()
        self.assertEqual([row['version'] for row in first['snapshots']],[1])
        self.assertEqual([row['version'] for row in self.browser.get(self.history).json()['snapshots']],[2,1])


@override_settings(**staff_tests.STAFF_SETTINGS)
class ReviewHistoryNavigationTests(TransactionTestCase):
    setUp=bindings.BusinessBindingTests.setUp
    post=bindings.BusinessBindingTests.post
    challenge=bindings.BusinessBindingTests.challenge
    authenticated=bindings.BusinessBindingTests.authenticated
    grant=bindings.BusinessBindingTests.grant
    owner_context=bindings.BusinessBindingTests.owner_context
    attach=bindings.BusinessBindingTests.attach
    business=bindings.BusinessBindingTests.business
    enable_private=bindings.BusinessBindingTests.enable_private
    review_value=bindings.BusinessBindingTests.review_value

    def start(self):
        self.authenticated();self.grant();self.history=self.detail+'reviews/history/'

    def make_decision(self,decision='needs_information'):
        result=self.post(self.review_route,self.review_value(decision))
        self.assertEqual(result.status_code,201);return result.json()['review']

    def test_older_decisions_and_original_records_remain_reachable_after_correction(self):
        self.start()
        for index in range(23):self.make_decision('declined' if index%2 else 'needs_information')
        first=self.browser.get(self.history).json()
        self.assertEqual([row['version'] for row in first['reviews']],list(range(23,3,-1)))
        self.assertEqual(first['older'],4);self.assertEqual(first['limit'],20)
        before=list(QuotationReview.objects.values())
        self.make_decision()
        second=self.browser.get(self.history+'?before=4').json()
        self.assertEqual([row['version'] for row in second['reviews']],[3,2,1]);self.assertIsNone(second['older'])
        self.assertEqual(list(QuotationReview.objects.order_by('version').values())[:23],before)
        html=self.browser.get(self.history,HTTP_ACCEPT='text/html')
        self.assertContains(html,'Older review decisions');self.assertContains(html,'Review revision 24')
        self.assertContains(self.browser.get(self.detail,HTTP_ACCEPT='text/html'),self.history)

    def test_history_metadata_preserves_original_reviewers_without_mfa_evidence(self):
        self.start();self.make_decision()
        other=get_user_model().objects.create_user(username='second-history-reviewer',password=self.password,is_staff=True)
        StaffCredential.objects.create(user=other)
        call_command('local_staff','grant',username=other.username,quotation=str(self.quotation.pk),stdout=io.StringIO())
        browser=Client(enforce_csrf_checks=True,HTTP_HOST='staff.localhost');login_staff(self,other,browser)
        result=self.post(self.review_route,self.review_value('declined'),browser);self.assertEqual(result.status_code,201)
        response=self.browser.get(self.history);value=response.json()
        self.assertEqual([row['reviewer_id'] for row in value['reviews']],[str(other.pk),str(self.user.pk)])
        self.assertEqual(set(value),{'reviews','limit','older'})
        for row in value['reviews']:
            self.assertEqual(set(row),{'version','business_version','decision','label','reviewer_id','created_at'})
        self.assertNotIn('mfa_verified_at',response.content.decode());private(self,response)

    def test_private_scope_withdrawal_keeps_safe_history_without_digests_or_writes(self):
        self.start();self.assertEqual(self.attach().status_code,303);self.enable_private(1)
        self.make_decision();row=QuotationReview.objects.get()
        call_command('local_staff','revoke-business',username=self.user.username,quotation=str(self.quotation.pk),stdout=io.StringIO())
        self.assertEqual(self.browser.get(self.private).status_code,403)
        before=list(QuotationReview.objects.values())
        with CaptureQueriesContext(connection) as queries:
            response=self.browser.get(self.history);html=self.browser.get(self.history,HTTP_ACCEPT='text/html')
        self.assertEqual(response.status_code,200);self.assertEqual(response.json()['reviews'][0]['business_version'],1)
        for reply in (response,html):
            private(self,reply)
            for secret in (row.snapshot_digest,str(row.reviewer_generation),'BUSINESS_SCOPE_ONE_PRIVATE_SYNTHETIC',
                           'snapshot_digest','mfa_verified_at','<form','<input','<script'):
                self.assertNotIn(secret,reply.content.decode())
        self.assertEqual(list(QuotationReview.objects.values()),before)
        self.assertFalse(any(re.match(r'\s*(INSERT|UPDATE|DELETE)\b',q['sql'],re.I) for q in queries))

    def test_cursor_resource_auth_methods_and_environment_boundaries(self):
        self.start();self.make_decision()
        for query in ('before=','before=0','before=-1','before=01','before=true','before=1000000001',
                      'before=1&before=1','scope=1','before=1&next=/private'):
            self.assertEqual(self.browser.get(self.history+'?'+query).status_code,400,query)
        self.assertEqual(self.browser.get(self.history+'?before=99').status_code,404)
        for method in ('post','put','delete','patch'):
            self.assertEqual(getattr(self.browser,method)(self.history,
                HTTP_X_CSRFTOKEN=self.browser.cookies['shop_staff_csrftoken'].value).status_code,405)
        with self.owner_context():self.assertEqual(self.owner_client.get(self.history).status_code,404)
        with override_settings(SHOP_ENV='production'):self.assertEqual(self.browser.get(self.history).status_code,404)
        otherowner=get_user_model().objects.create_user(username='other-review-history-owner')
        othercart=DraftCart.objects.create(owner=otherowner)
        QuotationRequest.objects.filter(pk=self.quotation.pk).update(cart=othercart)
        self.assertEqual(self.browser.get(self.history+'?before=1').status_code,404)
        QuotationRequest.objects.filter(pk=self.quotation.pk).update(cart_id=self.quotation.cart_id)
        self.credential.enabled=False;self.credential.save(update_fields=['enabled'])
        self.assertEqual(self.browser.get(self.history).status_code,403)
        self.credential.enabled=True;self.credential.save(update_fields=['enabled'])
        call_command('local_staff','revoke-grant',username=self.user.username,quotation=str(self.quotation.pk),stdout=io.StringIO())
        self.assertEqual(self.browser.get(self.history+'?before=1').status_code,404)

    def test_review_history_retains_committed_prefix_during_supported_correction(self):
        self.start();self.make_decision();value=self.review_value('declined')
        def after_parent(quotation):
            def correct():
                client=Client(enforce_csrf_checks=True,HTTP_HOST='staff.localhost');client.cookies=self.browser.cookies.copy()
                try:return client.post('/staff/'+self.review_route,data=json.dumps(value),content_type='application/json',
                    HTTP_X_CSRFTOKEN=client.cookies['shop_staff_csrftoken'].value).status_code
                finally:connections.close_all()
            with ThreadPoolExecutor(max_workers=1) as pool:self.assertEqual(pool.submit(correct).result(timeout=10),201)
            return history_rows(quotation)
        with patch('shop.access.review_history.history_rows',side_effect=after_parent):
            first=self.browser.get(self.history).json()
        self.assertEqual([row['version'] for row in first['reviews']],[1])
        self.assertEqual([row['version'] for row in self.browser.get(self.history).json()['reviews']],[2,1])
