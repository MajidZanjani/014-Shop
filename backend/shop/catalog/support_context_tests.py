"""Real-PG confidential fixture context: archive/CAS/history/access and no purchase effects."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch
from urllib.parse import urlencode
import json
import uuid
from django.contrib.auth import get_user_model
from django.db import connections,transaction,IntegrityError
from django.test import TransactionTestCase,Client,override_settings
from shop.adapters.evidence_archive import ArchiveError
from . import support_context as service, checkout, support_ledger as ledger
from . import support_ledger_tests as fixture
from .models import SyntheticSupportContext as Context,SyntheticSupportStaffGrant


class SupportContextTests(TransactionTestCase):
    save_cart=fixture.SupportLedgerTests.save_cart
    preview=fixture.SupportLedgerTests.preview
    accept=fixture.SupportLedgerTests.accept
    setUp=fixture.SupportLedgerTests.setUp

    def record(self,key=None,fixture='synthetic-context-v1',revision=0):
        return service.record(self.owner,self.saved.pk,key or uuid.uuid4(),fixture,revision,self.archive)

    def read(self,**kw):return service.read(self.owner,self.saved.pk,self.archive,**kw)

    def test_versioned_retries_preserve_scope_grant_and_ledger(self):
        ledger_before=ledger.read(self.owner,self.saved.pk,self.archive)
        accepted=self.grant.acceptance.sha256
        key=uuid.uuid4();first=self.record(key)
        second=self.record(fixture='synthetic-context-v2',revision=1)
        self.assertEqual(self.record(key).pk,first.pk)
        value=self.read();self.assertEqual(value['revision'],2)
        self.assertEqual([row['context']['board'] for row in value['versions']],['Synthetic prototype A','Synthetic prototype B'])
        self.assertEqual(Context.objects.get(pk=first.pk).sha256,first.sha256)
        self.assertEqual(second.payload['previous_sha256'],first.sha256)
        self.assertEqual(ledger.read(self.owner,self.saved.pk,self.archive),ledger_before)
        self.grant.acceptance.refresh_from_db();self.assertEqual(self.grant.acceptance.sha256,accepted)
        self.assertFalse(value['actual_technical_intake']);self.assertFalse(value['effects_authorized'])

    def test_changed_command_and_stale_revision_deny(self):
        key=uuid.uuid4();self.record(key)
        for args in ({'key':key,'fixture':'synthetic-context-v2'},{'key':key,'revision':1},{'revision':0}):
            with self.subTest(args=args),self.assertRaisesRegex(checkout.CheckoutError,'support_context_conflict'):
                self.record(**args)
        self.assertEqual(Context.objects.count(),1)

    def test_competing_revisions_have_one_winner(self):
        barrier=Barrier(2)
        def action(_):
            try:
                barrier.wait(timeout=10)
                try:self.record();return 'recorded'
                except checkout.CheckoutError as error:return str(error)
            finally:connections.close_all()
        with ThreadPoolExecutor(2) as pool:results=list(pool.map(action,range(2)))
        self.assertCountEqual(results,['recorded','support_context_conflict'])
        self.assertEqual(Context.objects.count(),1)

    def test_archive_failure_and_readback_failure_publish_no_context(self):
        for name in ('publish','recover'):
            with patch.object(self.archive,name,side_effect=ArchiveError('unavailable')):
                with self.assertRaises(ArchiveError):self.record()
            self.assertEqual(Context.objects.count(),0)
        self.record()
        with patch.object(self.archive,'recover',side_effect=ArchiveError('lost')):
            with self.assertRaises(ArchiveError):self.read()

    def test_cross_owner_and_exact_staff_grant(self):
        self.record();other=get_user_model().objects.create_user(username='other-context-owner')
        from .tests import verified_login
        verified_login(self.client,other)
        with self.assertRaises(checkout.CheckoutError):service.read(other,self.saved.pk,self.archive)
        self.assertEqual(self.read(staff_request=self.request)['revision'],1)
        SyntheticSupportStaffGrant.objects.filter(user=self.staff).delete()
        with self.assertRaises(checkout.CheckoutError):self.read(staff_request=self.request)
        self.assertNotIn('owner_id',json.dumps(self.read()))
        self.assertNotIn('grant_sha256',json.dumps(self.read()))

    def test_expired_staff_mfa_denies_context_history(self):
        self.record();self.request.session['shop_staff_mfa']['verified_at']-=301
        with self.assertRaises(checkout.CheckoutError):self.read(staff_request=self.request)

    def test_sql_history_is_immutable(self):
        self.record()
        for mutation in (lambda:Context.objects.all().delete(),lambda:Context.objects.all().update(sha256='0'*64)):
            with self.assertRaises(IntegrityError),transaction.atomic():mutation()

    def test_actual_text_and_invalid_revision_or_live_modes_are_refused(self):
        for fixture,revision in (('ACTUAL_TECHNICAL_CANARY',0),('synthetic-context-v1',True),('synthetic-context-v1',-1)):
            with self.assertRaises(checkout.CheckoutError):self.record(fixture=fixture,revision=revision)
        with override_settings(SHOP_ENV='production'),self.assertRaises(ValueError):self.record()
        self.assertEqual(Context.objects.count(),0)

    def test_owner_form_json_and_closed_fields(self):
        from .tests import verified_login
        with override_settings(LOCAL_CHECKOUT_ARCHIVE_ROOT=self.directory.name):
            browser=Client(enforce_csrf_checks=True);verified_login(browser,self.owner)
            url='/purchase/checkout-rehearsal/'+str(self.saved.pk)+'/support/'
            page=browser.get(url);self.assertEqual(page.status_code,200)
            self.assertContains(page,'Optional private support follow-up')
            value={'action':'context','request_id':str(uuid.uuid4()),'fixture':'synthetic-context-v1','expected_revision':'0'}
            self.assertEqual(browser.post(url,data=urlencode(value),content_type='application/x-www-form-urlencoded').status_code,403)
            headers={'HTTP_X_CSRFTOKEN':browser.cookies['csrftoken'].value}
            self.assertEqual(browser.post(url,data=urlencode(value),content_type='application/x-www-form-urlencoded',**headers).status_code,303)
            value['expected_revision']=0
            response=browser.post(url,data=json.dumps(value),content_type='application/json',**headers)
            self.assertEqual(response.status_code,200);self.assertEqual(response.json()['followup']['revision'],1)
            self.assertIn('no-store',response['Cache-Control'])
            value['technical_text']='PRIVATE_CANARY'
            self.assertEqual(browser.post(url,data=json.dumps(value),content_type='application/json',**headers).status_code,400)
            with override_settings(ROOT_URLCONF='shop.staff_urls'):
                staff=Client(HTTP_HOST='staff.localhost');staff.force_login(self.staff)
                session=staff.session;session['shop_staff_mfa']=self.request.session['shop_staff_mfa'];session.save()
                response=staff.get('/staff/support/'+str(self.saved.pk)+'/',HTTP_ACCEPT='application/json')
                self.assertEqual(response.status_code,200);self.assertEqual(response.json()['followup']['revision'],1)
                self.assertEqual(staff.post('/staff/support/'+str(self.saved.pk)+'/',data=json.dumps(value),content_type='application/json').status_code,400)
