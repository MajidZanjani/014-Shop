"""Protected PostgreSQL discount issuance, one-time code handling and recovery."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import io,json
from pathlib import Path
from threading import Barrier
from unittest.mock import patch
from urllib.parse import urlencode
import uuid
from django.core.management import call_command
from django.db import DatabaseError,connection,connections,transaction
from django.test import Client,TransactionTestCase,override_settings
from django.utils import timezone
from . import invitation_admin_tests,discount_issuance as service
from .discounts import verifier
from .models import DiscountCode,DiscountIssue,DiscountIssueGrant,DiscountIssuanceScope,DiscountReservation


@override_settings(SHB_SYNTHETIC_FIXTURE=True)
class DiscountIssuanceTests(TransactionTestCase):
    client_class=invitation_admin_tests.InvitationAdminTests.client_class
    post=invitation_admin_tests.InvitationAdminTests.post
    challenge=invitation_admin_tests.InvitationAdminTests.challenge
    authenticated=invitation_admin_tests.InvitationAdminTests.authenticated
    customer_submit=invitation_admin_tests.InvitationAdminTests.customer_submit

    def setUp(self):
        invitation_admin_tests.InvitationAdminTests.setUp(self)
        self.scope=service.register_fixture(customer=self.customer,registered_by=self.user,
            percentage_bps=1500,fpga_allowed=False,asic_allowed=True,use_limit=2,claim_period_days=30)
        self.issue_grant=DiscountIssueGrant.objects.create(user=self.user,scope=self.scope)
        self.issue_route='shb-discount-scopes/'+str(self.scope.pk)+'/'
        self.issue_value={'request_id':str(uuid.uuid4()),'reason':'Deliberate synthetic discount issue.'}
        self.initial=DiscountCode.objects.count()

    def issue(self,**changes):return self.post(self.issue_route,dict(self.issue_value,**changes))

    def no_publication(self):
        self.assertEqual(DiscountCode.objects.count(),self.initial)
        self.assertFalse(DiscountIssue.objects.filter(discount__isnull=False).exists())

    def test_staff_home_exposes_discount_issuance_scopes(self):
        response=self.browser.get('/staff/',HTTP_ACCEPT='text/html')
        self.assertEqual(response.status_code,200)
        self.assertIn(b'Discount issuance scopes',response.content)

    def test_get_is_assigned_code_free_and_effect_free(self):
        response=self.browser.get('/staff/'+self.issue_route)
        self.assertEqual(response.status_code,200)
        self.assertNotIn('code_digest',response.content.decode());self.assertNotIn('contact_email',response.content.decode())
        self.assertEqual(response['Cache-Control'],'no-store');self.assertEqual(response['Referrer-Policy'],'no-referrer')
        self.assertEqual(self.browser.get('/staff/shb-discount-scopes/').json()['scopes'][0]['id'],str(self.scope.pk))
        self.assertFalse(DiscountIssue.objects.exists());self.no_publication()

    def test_post_shows_one_code_and_retry_preserves_original_issue(self):
        response=self.issue();self.assertEqual(response.status_code,201)
        value=response.json();code=value['discount_code']
        self.assertRegex(code,r'^SLL-[A-Z0-9]{24}$')
        event=DiscountIssue.objects.select_related('discount').get()
        self.assertEqual(event.discount.code_digest,verifier(code))
        self.assertEqual(event.discount.percentage_bps,self.scope.percentage_bps)
        self.assertEqual(event.discount.use_limit,self.scope.use_limit)
        self.assertEqual(event.discount.fpga_allowed,self.scope.fpga_allowed)
        self.assertEqual(event.discount.asic_allowed,self.scope.asic_allowed)
        self.assertEqual(event.discount.customer_id,self.scope.customer_id)
        self.assertEqual(event.discount.issuer_id,self.user.pk)
        self.assertEqual(event.discount.policy_revision,'synthetic-shb-discounts-v1')
        self.assertEqual(event.discount.evidence_class,'local-synthetic')
        self.assertEqual(event.discount.starts_at,event.created_at)
        self.assertEqual(event.discount.expires_at,event.created_at+timedelta(days=30))
        self.assertFalse(value['actual_discount_authority']);self.assertFalse(value['actual_email_sent'])
        self.assertNotIn(code,json.dumps(event.payload));self.assertNotIn(code,json.dumps(event.archive_receipt))
        self.assertTrue(all(code.encode() not in p.read_bytes() for p in Path(self.directory.name).iterdir() if p.is_file()))
        replay=self.issue();self.assertEqual(replay.status_code,200);self.assertIsNone(replay.json()['discount_code'])
        self.assertEqual(replay.json()['issue'],value['issue']);self.assertEqual(DiscountIssue.objects.count(),1)
        self.assertNotIn(code,self.browser.get('/staff/'+self.issue_route).content.decode())
        self.assertNotIn(event.discount.code_digest,self.browser.get('/staff/'+self.issue_route).content.decode())
        with override_settings(**self.customer_settings):
            self.assertEqual(self.customer_submit(action='apply_discount',discount_code=code).status_code,200)

    def test_changed_same_key_and_forged_scope_fields_cannot_issue(self):
        self.assertEqual(self.issue().status_code,201)
        self.assertEqual(self.issue(reason='Changed command').status_code,409)
        for key in ('customer_id','percentage_bps','use_limit','fpga_allowed','asic_allowed','claim_period_days','approved','code'):
            self.assertEqual(self.issue(**{key:'forged'}).status_code,400)
        self.assertEqual(DiscountIssue.objects.count(),1)

    def test_missing_scope_disabled_eligibility_mfa_and_fixture_gate_deny(self):
        self.issue_grant.delete();self.assertEqual(self.issue().status_code,404)
        self.assertEqual(self.browser.get('/staff/'+self.issue_route).status_code,404)
        self.assertEqual(self.browser.get('/staff/shb-discount-scopes/',{'before':str(self.scope.pk)}).status_code,404)
        self.issue_grant=DiscountIssueGrant.objects.create(user=self.user,scope=self.scope)
        DiscountIssuanceScope.objects.filter(pk=self.scope.pk).update(enabled=False)
        self.assertEqual(self.issue().status_code,409)
        DiscountIssuanceScope.objects.filter(pk=self.scope.pk).update(enabled=True)
        session=self.browser.session;marker=session['shop_staff_mfa'];marker['verified_at']-=301;session['shop_staff_mfa']=marker;session.save()
        self.assertEqual(self.issue().status_code,403)
        marker['verified_at']+=301;session['shop_staff_mfa']=marker;session.save()
        with override_settings(SHB_SYNTHETIC_FIXTURE=False):self.assertEqual(self.issue().status_code,503)
        self.no_publication();self.assertFalse(DiscountIssue.objects.exists())

    def test_inactive_customer_or_staff_customer_is_not_issuable(self):
        for changes in ({'is_active':False},{'is_active':True,'is_staff':True}):
            type(self.customer).objects.filter(pk=self.customer.pk).update(**changes)
            self.assertEqual(self.issue().status_code,409)
        self.no_publication()

    def test_native_form_and_csrf_share_issue_service_without_cookie_secret(self):
        page=self.browser.get('/staff/'+self.issue_route,HTTP_ACCEPT='text/html');self.assertContains(page,'Issue synthetic discount')
        no_csrf=Client(enforce_csrf_checks=True,HTTP_HOST='staff.localhost');no_csrf.cookies=self.browser.cookies.copy()
        self.assertEqual(no_csrf.post('/staff/'+self.issue_route,self.issue_value).status_code,403);self.no_publication()
        form=dict(self.issue_value,csrfmiddlewaretoken=self.browser.cookies['shop_staff_csrftoken'].value)
        response=self.browser.post('/staff/'+self.issue_route,urlencode(form),content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code,201);self.assertContains(response,'SLL-',status_code=201)
        self.assertFalse(any('SLL-' in cookie.value for cookie in response.cookies.values()))
        self.assertNotContains(self.browser.get('/staff/'+self.issue_route,HTTP_ACCEPT='text/html'),'SLL-')

    def test_archive_failure_retains_same_prepared_digest_and_retry_cannot_reveal_code(self):
        from shop.adapters.evidence_archive import PreparedArchive,ArchiveError
        with patch.object(PreparedArchive,'publish',side_effect=ArchiveError('owned outage')):
            self.assertEqual(self.issue().status_code,503)
        self.no_publication();event=DiscountIssue.objects.get();original=(event.pk,event.sha256,event.created_at,event.payload)
        response=self.issue();self.assertEqual(response.status_code,200);self.assertIsNone(response.json()['discount_code'])
        event.refresh_from_db();self.assertEqual((event.pk,event.sha256,event.created_at,event.payload),original)
        self.assertEqual(event.discount_id,event.pk)

    def test_grant_and_mfa_are_rechecked_after_archive_io(self):
        original=service.notifications.evidence
        def publish(*args,**kwargs):
            result=original(*args,**kwargs);self.issue_grant.delete();return result
        with patch.object(service.notifications,'evidence',side_effect=publish):self.assertEqual(self.issue().status_code,404)
        self.no_publication();self.assertEqual(DiscountIssue.objects.count(),1)
        self.issue_grant=DiscountIssueGrant.objects.get(user=self.user,scope=self.scope)
        clock=None
        def expired(*args,**kwargs):
            nonlocal clock
            result=original(*args,**kwargs)
            clock=patch('shop.access.staff_auth.timezone.now',return_value=timezone.now()+timedelta(seconds=301));clock.start()
            return result
        try:
            with patch.object(service.notifications,'evidence',side_effect=expired):self.assertEqual(self.issue().status_code,403)
        finally:
            if clock:clock.stop()
        self.no_publication()

    def test_invalid_fields_are_rejected_before_preparation(self):
        for reason in ('',' ',None,True,1,'x'*513,chr(0)):
            self.assertEqual(self.issue(reason=reason).status_code,400)
        self.assertEqual(self.issue(request_id='bad-id').status_code,422)
        self.no_publication();self.assertFalse(DiscountIssue.objects.exists())

    def test_sql_scope_and_published_audit_cannot_be_edited_or_deleted(self):
        self.assertEqual(self.issue().status_code,201)
        for command in (lambda:DiscountIssuanceScope.objects.update(percentage_bps=5000),
                lambda:DiscountIssuanceScope.objects.all().delete(),lambda:DiscountIssue.objects.update(payload={}),
                lambda:DiscountIssue.objects.all().delete(),lambda:DiscountIssue.objects.update(archive_receipt={})):
            with self.assertRaises(DatabaseError),transaction.atomic():command()

    def test_interruption_before_publication_commit_rolls_back_discount_and_retries_same_intent(self):
        original=DiscountIssue.save
        def interrupted(row,*args,**kwargs):
            if row.discount_id is not None:raise RuntimeError('owned publication interruption')
            return original(row,*args,**kwargs)
        with patch.object(DiscountIssue,'save',interrupted):
            with self.assertRaisesMessage(RuntimeError,'owned publication interruption'):self.issue()
        self.no_publication();event=DiscountIssue.objects.get();digest=event.sha256
        response=self.issue();self.assertEqual(response.status_code,200);self.assertIsNone(response.json()['discount_code'])
        event.refresh_from_db();self.assertEqual(event.sha256,digest);self.assertEqual(event.discount_id,event.pk)

    def test_sql_cannot_publish_prepared_intent_against_another_discount(self):
        from shop.adapters.evidence_archive import PreparedArchive,ArchiveError
        with patch.object(PreparedArchive,'publish',side_effect=ArchiveError('owned outage')):
            self.assertEqual(self.issue().status_code,503)
        with self.assertRaises(DatabaseError),transaction.atomic():
            DiscountIssue.objects.update(discount=self.discount,archive_receipt={'forged':True})
        self.no_publication()

    def test_sql_refuses_discount_when_issue_publication_update_is_omitted(self):
        original=DiscountIssue.save
        def omitted(row,*args,**kwargs):
            if row.discount_id is None:return original(row,*args,**kwargs)
        with patch.object(DiscountIssue,'save',omitted):
            with self.assertRaisesMessage(DatabaseError,'discount and issue publication must commit together'):self.issue()
        self.no_publication();self.assertEqual(DiscountIssue.objects.count(),1)

    def test_issuance_preserves_existing_requests_and_reservations(self):
        from .models import SupportRequest,TransactionNotice
        models=(SupportRequest,DiscountReservation,TransactionNotice)
        before=[list(model.objects.values()) for model in models]
        self.assertEqual(self.issue().status_code,201)
        self.assertEqual([list(model.objects.values()) for model in models],before)

    def test_concurrent_exact_retries_publish_one_discount_and_only_one_code_response(self):
        cookies=self.browser.cookies.copy();barrier=Barrier(2)
        def invoke(_):
            connections.close_all()
            try:
                client=Client(enforce_csrf_checks=True,HTTP_HOST='staff.localhost');client.cookies=cookies.copy();barrier.wait(timeout=5)
                response=client.post('/staff/'+self.issue_route,data=json.dumps(self.issue_value),content_type='application/json',HTTP_X_CSRFTOKEN=cookies['shop_staff_csrftoken'].value)
                return response.status_code,response.json()
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(invoke,range(2)))
        self.assertEqual(sorted(status for status,_ in results),[200,201])
        self.assertEqual(DiscountIssue.objects.count(),1)
        self.assertEqual(sum(bool(value.get('discount_code')) for _,value in results),1)
        self.assertEqual(DiscountCode.objects.count(),self.initial+1)

    def test_operator_and_reset_clear_only_mutable_discount_issuance_grants(self):
        from shop.access.grants import revoke_staff_resource_grants
        self.issue_grant.delete()
        call_command('local_staff','grant-discount-issue',username=self.user.username,issuance_scope=str(self.scope.pk),stdout=io.StringIO())
        self.assertEqual(self.issue().status_code,201)
        with transaction.atomic():counts=revoke_staff_resource_grants(user_id=self.user.pk)
        self.assertEqual(counts['shb_discount_issue'],1);self.assertFalse(DiscountIssueGrant.objects.exists())
        self.assertEqual(self.issue().status_code,404);self.assertEqual(DiscountIssue.objects.count(),1)

    def test_recovery_retains_issued_evidence_and_original_clocks(self):
        from .recovery import inspect_local_shb_recovery
        from shop.access.recovery import local_recovery_operation
        self.assertEqual(self.issue().status_code,201);event=DiscountIssue.objects.select_related('discount').get()
        original=(event.sha256,event.discount.issued_at,event.discount.starts_at,event.discount.expires_at)
        reset=uuid.uuid4();local_recovery_operation(action='quarantine',request_id=reset,expected_database=connection.settings_dict['NAME'])
        report=inspect_local_shb_recovery();self.assertEqual(report['counts']['discount_issues'],1)
        self.assertFalse(report['post_backup_completeness_established']);self.assertFalse(report['reopening_authorized'])
        local_recovery_operation(action='release',request_id=uuid.uuid4(),basis_reset=reset,expected_database=connection.settings_dict['NAME'])
        event=DiscountIssue.objects.select_related('discount').get()
        self.assertEqual((event.sha256,event.discount.issued_at,event.discount.starts_at,event.discount.expires_at),original)

    def test_missing_published_archive_refuses_fixture_recovery_release(self):
        from shop.access.recovery import local_recovery_operation,AccessRecoveryError
        self.assertEqual(self.issue().status_code,201);event=DiscountIssue.objects.get()
        (Path(self.directory.name)/('blob-'+event.sha256)).unlink()
        reset=uuid.uuid4();local_recovery_operation(action='quarantine',request_id=reset,expected_database=connection.settings_dict['NAME'])
        with self.assertRaisesMessage(AccessRecoveryError,'shb_recovery_evidence_required'):
            local_recovery_operation(action='release',request_id=uuid.uuid4(),basis_reset=reset,expected_database=connection.settings_dict['NAME'])

    def test_selected_restore_clears_issuance_assignment_but_retains_original_audit(self):
        from shop.access.recovery import local_recovery_operation
        self.assertEqual(self.issue().status_code,201);event=DiscountIssue.objects.get();digest=event.sha256
        reset=uuid.uuid4()
        with override_settings(LOCAL_RESTORE_ID=reset):
            result=local_recovery_operation(action='quarantine',request_id=reset,expected_database=connection.settings_dict['NAME'])
            self.assertEqual(result['invalidated']['staff_resource_grants']['shb_discount_issue'],1)
            local_recovery_operation(action='release',request_id=uuid.uuid4(),basis_reset=reset,expected_database=connection.settings_dict['NAME'])
        self.assertFalse(DiscountIssueGrant.objects.exists());self.assertEqual(DiscountIssue.objects.get().sha256,digest)
        self.assertEqual(self.issue().status_code,403)

    def test_revocation_grant_or_contact_entry_cannot_establish_issuance_authority(self):
        from .models import DiscountStaffGrant
        self.issue_grant.delete()
        DiscountStaffGrant.objects.create(user=self.user,discount=self.discount)
        self.assertEqual(self.issue().status_code,404);self.no_publication()
        self.assertFalse(DiscountIssue.objects.exists())
