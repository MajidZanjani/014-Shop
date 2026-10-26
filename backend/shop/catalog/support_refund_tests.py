"""Real PostgreSQL refund-review snapshots; original money/work/credit remain unchanged."""
from concurrent.futures import ThreadPoolExecutor
from io import StringIO
from threading import Barrier
from unittest.mock import patch
from urllib.parse import urlencode
import json
import uuid
from django.core.management import call_command
from django.db import connections,transaction,IntegrityError
from django.test import Client,TransactionTestCase,override_settings
from shop.adapters.evidence_archive import PreparedArchive,ArchiveError
from shop.payments.bank_contract import BankError
from shop.payments.models import SyntheticBankOperation
from . import support_refunds as service,support_ledger as ledger,support_ledger_tests as fixture,checkout
from .models import (SyntheticSupportRefundCase as Case,SyntheticSupportRefundReview as Review,
    SyntheticSupportRefundStaffGrant as StaffGrant,SyntheticSupportEvent,SyntheticSupportStaffGrant)


class SupportRefundTests(TransactionTestCase):
    save_cart=fixture.SupportLedgerTests.save_cart
    preview=fixture.SupportLedgerTests.preview
    accept=fixture.SupportLedgerTests.accept

    def setUp(self):
        fixture.SupportLedgerTests.setUp(self)
        self.reservation=ledger.record(self.owner,self.saved.pk,uuid.uuid4(),'reserve',self.archive,seconds=3600,task_id=uuid.uuid4())
        self.work=ledger.record(self.owner,self.saved.pk,uuid.uuid4(),'work',self.archive,seconds=1800,target_id=self.reservation.pk,staff_request=self.request)
        self.base=f'/purchase/checkout-rehearsal/{self.saved.pk}/support/refunds/'

    def capture(self,seconds=72000,key=None):return service.capture(self.owner,self.saved.pk,key or uuid.uuid4(),seconds,self.archive)
    def assign(self,case):StaffGrant.objects.get_or_create(user=self.staff,case=case)
    def state(self,case,before=None):
        with transaction.atomic(durable=True):
            row,state=service.case_locked(self.owner,self.saved.pk,case.identity,self.archive)
            return service.summary(row,state,self.archive,before)
    def review(self,case,decision='ready_for_financial_review',key=None,expected=None,revision=None):
        if expected is None:expected=Review.objects.filter(case=case).count()
        if revision is None:revision=SyntheticSupportEvent.objects.filter(fulfilment=self.grant).count()
        return service.review(self.request,self.owner,self.saved.pk,case.identity,key or uuid.uuid4(),expected,revision,decision,self.archive)
    def form(self,browser,path,value):return browser.post(path,data=urlencode(value),content_type='application/x-www-form-urlencoded')

    def test_snapshot_distinguishes_available_reserved_consumed_without_effects(self):
        before=ledger.read(self.owner,self.saved.pk,self.archive);bank=SyntheticBankOperation.objects.count()
        case=self.capture();state=self.state(case)
        self.assertEqual(state['captured_credit']['available_seconds'],68400)
        self.assertEqual(state['captured_credit']['reserved_seconds'],1800)
        self.assertEqual(state['captured_credit']['spent_seconds'],1800)
        self.assertTrue(state['consumed_support_present']);self.assertTrue(state['request_exceeds_available'])
        self.assign(case);self.review(case)
        self.assertTrue(self.state(case)['review_current']);self.assertFalse(state['refund_authorized'])
        self.assertFalse(state['balance_hold_created']);self.assertTrue(all(value is None for value in state['financial_policy'].values()))
        self.assertEqual(ledger.read(self.owner,self.saved.pk,self.archive),before)
        self.assertEqual(SyntheticBankOperation.objects.count(),bank);self.assertEqual(SyntheticSupportEvent.objects.count(),2)

    def test_exact_capture_retry_keeps_original_snapshot_after_work(self):
        key=uuid.uuid4();case=self.capture(key=key);original=case.payload.copy()
        ledger.record(self.owner,self.saved.pk,uuid.uuid4(),'work',self.archive,seconds=900,target_id=self.reservation.pk,staff_request=self.request)
        self.assertEqual(self.capture(key=key).pk,case.pk);case.refresh_from_db();self.assertEqual(case.payload,original)
        self.assertEqual(self.state(case)['current_credit']['spent_seconds'],2700)
        with self.assertRaises(checkout.CheckoutError):self.capture(1,key)
        self.assertEqual(Case.objects.count(),1)

    def test_stale_ledger_review_denied_and_changed_credit_marks_review_outdated(self):
        case=self.capture();self.assign(case)
        ledger.record(self.owner,self.saved.pk,uuid.uuid4(),'release',self.archive,target_id=self.reservation.pk)
        with self.assertRaisesRegex(checkout.CheckoutError,'refund_ledger_revision_changed'):self.review(case,revision=2)
        self.review(case);self.assertTrue(self.state(case)['review_current'])
        ledger.record(self.owner,self.saved.pk,uuid.uuid4(),'correct',self.archive,seconds=900,target_id=self.work.pk,staff_request=self.request)
        self.assertFalse(self.state(case)['review_current']);self.assertEqual(self.state(case)['current_credit']['spent_seconds'],900)
        self.review(case,'needs_information');self.assertTrue(self.state(case)['review_current'])
        self.assertEqual(Review.objects.count(),2)

    def test_review_retries_revision_conflict_and_correction_history(self):
        case=self.capture();self.assign(case);key=uuid.uuid4()
        first=self.review(case,key=key,expected=0,revision=2)
        self.assertEqual(self.review(case,key=key,expected=0,revision=2).pk,first.pk)
        with self.assertRaises(checkout.CheckoutError):self.review(case,'declined',key,0,2)
        with self.assertRaisesRegex(checkout.CheckoutError,'refund_review_revision_changed'):self.review(case,expected=0)
        self.review(case,'declined');value=self.state(case)
        self.assertEqual(value['revision'],2);self.assertEqual(value['decision'],'declined')
        self.assertEqual([row['decision'] for row in value['history']],['declined','ready_for_financial_review'])
        with self.assertRaises(checkout.CheckoutError):self.review(case,'approved')

    def test_archive_outage_prevents_case_and_review_publication(self):
        with patch.object(self.archive,'publish',side_effect=ArchiveError('offline')):
            with self.assertRaises(ArchiveError):self.capture()
        self.assertEqual(Case.objects.count(),0)
        case=self.capture();self.assign(case)
        with patch.object(self.archive,'publish',side_effect=ArchiveError('offline')):
            with self.assertRaises(ArchiveError):self.review(case)
        self.assertEqual(Review.objects.count(),0);self.assertEqual(SyntheticSupportEvent.objects.count(),2)

    def test_missing_archives_block_case_and_review_reads(self):
        case=self.capture();self.assign(case);self.review(case)
        with patch.object(self.archive,'recover',side_effect=ArchiveError('missing')):
            with self.assertRaises((checkout.CheckoutError,ArchiveError)):self.state(case)
        self.assertEqual(Review.objects.count(),1)

    def test_database_history_cannot_be_rewritten_or_deleted(self):
        case=self.capture();self.assign(case);review=self.review(case)
        for query in (Case.objects.filter(pk=case.pk),Review.objects.filter(pk=review.pk)):
            with self.assertRaises(IntegrityError),transaction.atomic():query.update(sha256='0'*64)
            with self.assertRaises(IntegrityError),transaction.atomic():query.delete()

    def test_recent_mfa_and_separate_refund_assignment_required(self):
        case=self.capture()
        # Existing support assignment is insufficient for financial-case review.
        self.assertTrue(SyntheticSupportStaffGrant.objects.filter(user=self.staff).exists())
        with self.assertRaises(checkout.CheckoutError):self.review(case)
        self.assign(case);self.review(case);StaffGrant.objects.all().delete()
        with self.assertRaises(checkout.CheckoutError):self.review(case)
        self.assign(case);self.request.session['shop_staff_mfa']['verified_at']-=301
        with self.assertRaises(checkout.CheckoutError):self.review(case)

    def test_concurrent_exact_capture_retries_converge(self):
        key=uuid.uuid4();barrier=Barrier(2)
        def run(_):
            connections.close_all()
            try:
                barrier.wait(timeout=10);return self.capture(key=key).pk
            finally:connections.close_all()
        with ThreadPoolExecutor(2) as pool:rows=list(pool.map(run,range(2)))
        self.assertEqual(rows[0],rows[1]);self.assertEqual(Case.objects.count(),1)

    def test_concurrent_reviews_one_revision_wins(self):
        case=self.capture();self.assign(case);barrier=Barrier(2)
        def run(_):
            connections.close_all()
            try:
                barrier.wait(timeout=10)
                try:
                    with PreparedArchive(self.root) as archive:
                        service.review(self.request,self.owner,self.saved.pk,case.identity,uuid.uuid4(),0,2,'needs_information',archive)
                    return 'reviewed'
                except checkout.CheckoutError as error:return str(error)
            finally:connections.close_all()
        with ThreadPoolExecutor(2) as pool:rows=list(pool.map(run,range(2)))
        self.assertCountEqual(rows,['reviewed','refund_review_revision_changed']);self.assertEqual(Review.objects.count(),1)

    def test_owner_isolation_resource_bounds_and_production_denied(self):
        from .tests import verified_login
        verified_login(Client(),self.other)
        with self.assertRaises(checkout.CheckoutError):service.capture(self.other,self.saved.pk,uuid.uuid4(),1,self.archive)
        for seconds in (True,0,-1,1.5,'1',9223372036854775808,72001):
            with self.assertRaises(checkout.CheckoutError):self.capture(seconds)
        with override_settings(SHOP_ENV='production'):
            with self.assertRaises(BankError):self.capture()
        self.assertEqual(Case.objects.count(),0)

    def test_owner_json_forms_privacy_and_closed_schema(self):
        response=self.client.get(self.base);self.assertContains(response,'Support refund review rehearsal')
        self.assertIn('no-store',response['Cache-Control'])
        key=str(uuid.uuid4());payload={'request_id':key,'seconds':72000}
        for _ in range(2):self.assertEqual(self.client.post(self.base,data=json.dumps(payload),content_type='application/json').status_code,201)
        case=Case.objects.get();detail=self.base+str(case.identity)+'/'
        self.assertContains(self.client.get(detail),'Consumed support requires explicit review')
        result=self.client.get(detail,HTTP_ACCEPT='application/json').json()['case']
        self.assertNotIn('actor',json.dumps(result));self.assertNotIn('credential_generation',json.dumps(result))
        self.assertEqual(self.form(self.client,self.base,{'request_id':str(uuid.uuid4()),'seconds':'60'}).status_code,303)
        for data in ({'request_id':str(uuid.uuid4()),'seconds':True},{'request_id':str(uuid.uuid4()),'seconds':1,'amount_minor':100}):
            self.assertEqual(self.client.post(self.base,data=json.dumps(data),content_type='application/json').status_code,400)
        self.assertEqual(self.client.get(detail+'?token=private').status_code,400)
        from .tests import verified_login
        verified_login(self.client,self.other)
        self.assertEqual(self.client.get(detail).status_code,404);self.assertEqual(self.client.get(self.base).status_code,404)

    def test_staff_forms_operator_grants_revoke_reset(self):
        from shop.access.staff_tests import STAFF_SETTINGS
        case=self.capture();path='/staff/support-refunds/'+str(case.identity)+'/'
        with override_settings(**STAFF_SETTINGS):
            staff=Client(HTTP_HOST='staff.localhost');self.assertEqual(staff.get(path).status_code,403)
            staff.force_login(self.staff);session=staff.session;session['shop_staff_mfa']=self.request.session['shop_staff_mfa'];session.save()
            self.assertEqual(staff.get(path).status_code,404)
            call_command('local_staff','grant-refund',username=self.staff.username,case=str(case.identity),stdout=StringIO())
            self.assertContains(staff.get('/staff/support-refunds/'),str(case.identity));self.assertContains(staff.get(path),'Record simulated review')
            payload={'request_id':str(uuid.uuid4()),'expected_revision':'0','ledger_revision':'2','decision':'ready_for_financial_review'}
            for _ in range(2):self.assertEqual(self.form(staff,path,payload).status_code,303)
            self.assertContains(staff.get(path),'does not authorize a refund')
            call_command('local_staff','revoke-refund',username=self.staff.username,case=str(case.identity),stdout=StringIO())
            self.assertEqual(staff.get(path).status_code,404)
            call_command('local_staff','grant-refund',username=self.staff.username,case=str(case.identity),stdout=StringIO())
            call_command('local_staff','reset',username=self.staff.username,capture_root=str(self.root),stdout=StringIO())
            self.assertFalse(StaffGrant.objects.exists());self.assertEqual(staff.get(path).status_code,403)

    def test_review_history_paging_retains_latest_review(self):
        case=self.capture();self.assign(case)
        for _ in range(21):self.review(case,'needs_information')
        first=self.state(case);self.assertEqual(len(first['history']),20);self.assertEqual(first['next_before'],2)
        second=self.state(case,first['next_before']);self.assertEqual([row['revision'] for row in second['history']],[1])
        self.assertEqual(second['revision'],21)

    def test_review_racing_work_never_captures_a_mixed_credit_snapshot(self):
        case=self.capture();self.assign(case);barrier=Barrier(2)
        def run(kind):
            connections.close_all()
            try:
                barrier.wait(timeout=10)
                with PreparedArchive(self.root) as archive:
                    if kind=='work':
                        ledger.record(self.owner,self.saved.pk,uuid.uuid4(),'work',archive,seconds=900,target_id=self.reservation.pk,staff_request=self.request)
                        return 'work'
                    try:
                        service.review(self.request,self.owner,self.saved.pk,case.identity,uuid.uuid4(),0,2,'needs_information',archive)
                        return 'reviewed'
                    except checkout.CheckoutError as error:return str(error)
            finally:connections.close_all()
        with ThreadPoolExecutor(2) as pool:rows=list(pool.map(run,['work','review']))
        self.assertIn('work',rows);self.assertEqual(self.state(case)['current_credit']['spent_seconds'],2700)
        if 'reviewed' in rows:
            self.assertEqual(Review.objects.get().payload['credit']['spent_seconds'],1800)
            self.assertFalse(self.state(case)['review_current'])
        else:
            self.assertIn('refund_ledger_revision_changed',rows);self.assertEqual(Review.objects.count(),0)

    def test_customer_csrf_and_origin_are_required(self):
        from .tests import verified_login
        browser=Client(enforce_csrf_checks=True);verified_login(browser,self.owner)
        self.assertEqual(browser.get(self.base).status_code,200)
        payload=json.dumps({'request_id':str(uuid.uuid4()),'seconds':60})
        self.assertEqual(browser.post(self.base,data=payload,content_type='application/json').status_code,403)
        token=browser.cookies['csrftoken'].value
        self.assertEqual(browser.post(self.base,data=payload,content_type='application/json',HTTP_X_CSRFTOKEN=token,HTTP_ORIGIN='null').status_code,403)
        self.assertEqual(browser.post(self.base,data=payload,content_type='application/json',HTTP_X_CSRFTOKEN=token,HTTP_ORIGIN='http://testserver').status_code,201)
        self.assertEqual(Case.objects.count(),1)
