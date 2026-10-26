"""Real-PG exact-pair attribution investigation, not real financial approval."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from io import StringIO
from threading import Barrier
from unittest.mock import patch
from urllib.parse import urlencode
import uuid
from django.core.management import call_command
from django.db import connections,transaction,IntegrityError,connection
from django.test import TransactionTestCase,Client,override_settings
from shop.adapters.evidence_archive import ArchiveError
from shop.catalog import support_ledger_tests as fixture,checkout,checkout_payment as payment,fulfilment,support_ledger as ledger
from shop.catalog.models import SyntheticCheckoutAcceptance as Acceptance,SyntheticFulfilment,SyntheticLineEntitlement,SyntheticSupportEvent
from . import overpayments as service,attempts,synthetic_bank
from .bank_contract import BankStart,BankError
from .models import SyntheticOverpaymentStaffGrant as StaffGrant,SyntheticOverpaymentCase as Case,SyntheticOverpaymentReview as Review,SyntheticBankOperation


class OverpaymentTests(TransactionTestCase):
    save_cart=fixture.SupportLedgerTests.save_cart
    preview=fixture.SupportLedgerTests.preview
    accept=fixture.SupportLedgerTests.accept

    def setUp(self):
        fixture.SupportLedgerTests.setUp(self)
        self.accepted=Acceptance.objects.get(checkout=self.saved)
        self.extra=attempts.prepare(BankStart('synthetic-checkout',uuid.uuid4(),uuid.uuid4(),self.accepted.attempt.currency,self.accepted.attempt.amount_minor))
        attempts.dispatch(self.extra.pk,self.archive)
        self.scope=StaffGrant.objects.create(user=self.staff,acceptance=self.accepted,extra_attempt=self.extra)
        setting=override_settings(LOCAL_CHECKOUT_ARCHIVE_ROOT=self.directory.name)
        setting.enable();self.addCleanup(setting.disable)

    def capture(self):return service.capture(self.request,self.accepted.pk,self.extra.pk,self.archive)
    def review(self,decision='ready_for_financial_review',key=None,revision=0):
        return service.review(self.request,self.accepted.pk,self.extra.pk,key or uuid.uuid4(),revision,decision,self.archive)
    def inspect(self):return service.inspect(self.request,self.accepted.pk,self.extra.pk,self.archive)
    def browser(self,enforce=False):
        setting=override_settings(ROOT_URLCONF='shop.staff_urls');setting.enable();self.addCleanup(setting.disable)
        browser=Client(enforce_csrf_checks=enforce,HTTP_HOST='staff.localhost');browser.force_login(self.staff)
        session=browser.session;session['shop_staff_mfa']=self.request.session['shop_staff_mfa'];session.save();return browser

    def test_two_money_facts_one_grant_and_null_financial_policy(self):
        before=ledger.read(self.owner,self.saved.pk,self.archive)
        with patch.object(synthetic_bank,'start',side_effect=AssertionError('new money operation')):
            case=self.capture();self.review();self.assertEqual(self.capture().pk,case.pk)
            self.assertEqual(fulfilment.provision(self.owner,self.saved.pk,self.archive).pk,self.grant.pk)
        self.assertEqual(len(case.payload['captures']),2)
        self.assertNotEqual(case.payload['captures'][0]['observation']['provider_operation_id'],case.payload['captures'][1]['observation']['provider_operation_id'])
        state=self.inspect();self.assertEqual(state['decision'],'ready_for_financial_review')
        self.assertTrue(all(value is None for value in state['financial_policy'].values()))
        self.assertFalse(state['refund_authorized']);self.assertFalse(state['financial_confirmation']);self.assertFalse(state['additional_fulfilment_authorized'])
        self.assertEqual(SyntheticBankOperation.objects.count(),2);self.assertEqual(SyntheticFulfilment.objects.count(),1)
        self.assertEqual(SyntheticLineEntitlement.objects.count(),1);self.assertEqual(ledger.read(self.owner,self.saved.pk,self.archive),before)

    def test_exact_pair_not_existing_support_assignment_or_other_pair(self):
        StaffGrant.objects.all().delete()
        for action in (self.capture,self.inspect,lambda:self.review()):
            with self.assertRaises(checkout.CheckoutError):action()
        StaffGrant.objects.create(user=self.staff,acceptance=self.accepted,extra_attempt=self.accepted.attempt)
        with self.assertRaises(checkout.CheckoutError):self.capture()
        self.assertEqual(Case.objects.count(),0)

    def test_recent_generation_bound_mfa_and_current_scope_required(self):
        self.capture()
        old=self.request.session['shop_staff_mfa'].copy()
        for marker in ({**old,'verified_at':old['verified_at']-301},{**old,'generation':str(uuid.uuid4())},{}):
            self.request.session['shop_staff_mfa']=marker
            with self.assertRaises(checkout.CheckoutError):self.review()
        self.request.session['shop_staff_mfa']=old;self.scope.delete()
        with self.assertRaises(checkout.CheckoutError):self.inspect()
        self.assertEqual(Review.objects.count(),0)

    def test_exact_retry_conflict_cas_and_append_only_correction(self):
        self.capture();key=uuid.uuid4();first=self.review(key=key)
        self.assertEqual(self.review(key=key).pk,first.pk)
        with self.assertRaises(checkout.CheckoutError):self.review('not_attributable',key)
        with self.assertRaises(checkout.CheckoutError):self.review()
        self.review('not_attributable',revision=1)
        self.assertEqual(self.inspect()['revision'],2);self.assertEqual(self.inspect()['decision'],'not_attributable')
        self.assertEqual(Review.objects.get(pk=first.pk).payload['command']['decision'],'ready_for_financial_review')
        with self.assertRaises(checkout.CheckoutError):self.review('refund',revision=2)

    def test_database_prevents_rewriting_or_deleting_money_review_evidence(self):
        case=self.capture();review=self.review()
        for query in (Case.objects.filter(pk=case.pk),Review.objects.filter(pk=review.pk)):
            with self.assertRaises(IntegrityError),transaction.atomic():query.update(sha256='0'*64)
            with self.assertRaises(IntegrityError),transaction.atomic():query.delete()

    def test_archive_failure_blocks_capture_review_and_inspection(self):
        with patch.object(self.archive,'publish',side_effect=ArchiveError('offline')):
            with self.assertRaises(ArchiveError):self.capture()
        self.assertEqual(Case.objects.count(),0)
        self.capture()
        with patch.object(self.archive,'publish',side_effect=ArchiveError('offline')):
            with self.assertRaises(ArchiveError):self.review()
        self.assertEqual(Review.objects.count(),0)
        with patch.object(self.archive,'recover',side_effect=ArchiveError('missing')):
            with self.assertRaises(ArchiveError):self.inspect()

    def test_wrong_typed_lookup_or_missing_capture_never_establishes_attribution(self):
        lookup=synthetic_bank.lookup
        for change in ({'amount_minor':1},{'reference':uuid.uuid4()},{'currency':'GBP'},{'status':'authorized'}):
            def wrong(merchant,reference):return replace(lookup(merchant,reference),**change)
            with patch.object(synthetic_bank,'lookup',side_effect=wrong),self.assertRaises(checkout.CheckoutError):self.capture()
        with patch.object(synthetic_bank,'lookup',return_value=None),self.assertRaises(checkout.CheckoutError):self.capture()
        self.assertEqual(Case.objects.count(),0)

    def test_provider_lookup_has_no_transaction_and_scope_is_rechecked_after_io(self):
        lookup=synthetic_bank.lookup
        def checking(merchant,reference):
            self.assertFalse(connection.in_atomic_block)
            if reference==self.extra.reference:StaffGrant.objects.filter(pk=self.scope.pk).delete()
            return lookup(merchant,reference)
        with patch.object(synthetic_bank,'lookup',side_effect=checking),self.assertRaises(checkout.CheckoutError):self.capture()
        self.assertEqual(Case.objects.count(),0)

    def test_bound_extra_attempt_or_same_attempt_denied(self):
        Acceptance.objects.filter(pk=self.accepted.pk).update(attempt=self.extra)
        with self.assertRaises(checkout.CheckoutError):self.capture()
        self.assertEqual(Case.objects.count(),0)

    def test_two_competing_capture_and_review_commands_serialize(self):
        def run(function):
            barrier=Barrier(2)
            def action(_):
                try:
                    barrier.wait(timeout=10)
                    try:return function().pk
                    except checkout.CheckoutError:return 'held'
                finally:connections.close_all()
            with ThreadPoolExecutor(max_workers=2) as pool:return list(pool.map(action,range(2)))
        cases=run(self.capture);self.assertEqual(cases[0],cases[1]);self.assertEqual(Case.objects.count(),1)
        results=run(self.review);self.assertEqual(results.count('held'),1);self.assertEqual(Review.objects.count(),1)

    def test_operator_grant_revoke_and_staff_reset_scope(self):
        self.scope.delete();out=StringIO()
        args={'username':self.staff.username,'acceptance':str(self.accepted.pk),'attempt':str(self.extra.pk),'stdout':out}
        call_command('local_staff','grant-overpayment',**args);self.capture()
        call_command('local_staff','revoke-overpayment',**args)
        with self.assertRaises(checkout.CheckoutError):self.inspect()
        call_command('local_staff','grant-overpayment',**args)
        call_command('local_staff','revoke',username=self.staff.username,stdout=out)
        self.assertEqual(StaffGrant.objects.count(),0);self.assertNotIn(str(self.extra.pk),out.getvalue())

    def test_assigned_http_review_closed_inputs_private_output_and_scope(self):
        browser=self.browser();path=f'/staff/overpayments/{self.scope.pk}/'
        page=browser.get(path);self.assertEqual(page.status_code,200);self.assertIn('no-store',page['Cache-Control'])
        self.assertEqual(browser.post(path,data=urlencode({'action':'capture'}),content_type='application/x-www-form-urlencoded').status_code,303)
        value={'action':'review','request_id':str(uuid.uuid4()),'expected_revision':'0','decision':'ready_for_financial_review'}
        self.assertEqual(browser.post(path,data=urlencode(value),content_type='application/x-www-form-urlencoded').status_code,303)
        value['amount']='100';self.assertEqual(browser.post(path,data=urlencode(value),content_type='application/x-www-form-urlencoded').status_code,400)
        result=browser.get(path,HTTP_ACCEPT='application/json');self.assertEqual(result.json()['case']['revision'],1)
        self.assertNotIn(str(self.extra.pk),result.content.decode());self.assertNotIn(str(self.extra.reference),result.content.decode())
        self.scope.delete();self.assertEqual(browser.get(path).status_code,404)

    def test_missing_csrf_and_null_origin_rejected(self):
        browser=self.browser(True);path=f'/staff/overpayments/{self.scope.pk}/';browser.get(path)
        self.assertEqual(browser.post(path,{'action':'capture'}).status_code,403)
        token=browser.cookies['csrftoken'].value
        self.assertEqual(browser.post(path,{'action':'capture','csrfmiddlewaretoken':token},HTTP_ORIGIN='null').status_code,403)
        self.assertEqual(Case.objects.count(),0)

    def test_production_and_live_mode_closed(self):
        for settings in ({'SHOP_ENV':'production'},{'LIVE_PAYMENTS_ENABLED':True}):
            with override_settings(**settings),self.assertRaises(BankError):self.capture()
        self.assertEqual(Case.objects.count(),0)

    def test_prepared_evidence_survives_database_failure_for_exact_retry(self):
        with patch.object(service.notifications,'evidence',wraps=service.notifications.evidence) as prepared,patch.object(Case.objects,'create',side_effect=IntegrityError('injected commit failure')):
            with self.assertRaises(IntegrityError):self.capture()
        self.assertEqual(Case.objects.count(),0);self.assertEqual(prepared.call_count,1)
        case=self.capture();key=uuid.uuid4()
        with patch.object(Review.objects,'create',side_effect=IntegrityError('injected commit failure')):
            with self.assertRaises(IntegrityError):self.review(key=key)
        self.assertEqual(Review.objects.count(),0)
        self.review(key=key);self.assertEqual(Case.objects.get().pk,case.pk)

    def test_exact_amount_mismatch_and_unfunded_attempt_are_held(self):
        for amount,status in ((self.extra.amount_minor+1,'captured'),(self.extra.amount_minor,'authorized')):
            extra=attempts.prepare(BankStart('synthetic-checkout',uuid.uuid4(),uuid.uuid4(),'EUR',amount))
            attempts.dispatch(extra.pk,self.archive,outcome=status)
            StaffGrant.objects.create(user=self.staff,acceptance=self.accepted,extra_attempt=extra)
            with self.assertRaises(checkout.CheckoutError):service.capture(self.request,self.accepted.pk,extra.pk,self.archive)
        self.assertEqual(Case.objects.count(),0)

    def test_history_pagination_keeps_current_revision_and_decision(self):
        self.capture()
        for revision in range(21):self.review('needs_information',revision=revision)
        first=self.inspect();self.assertEqual(len(first['history']),20);self.assertEqual(first['next_before'],2)
        last=service.inspect(self.request,self.accepted.pk,self.extra.pk,self.archive,before=2)
        self.assertEqual(last['history'],[{'revision':1,'decision':'needs_information'}]);self.assertEqual(last['revision'],21)
