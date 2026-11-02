"""Actual PostgreSQL issuance boundaries, one-time secret handling and recovery."""
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
from . import invitation_admin_tests,invitation_issuance as service
from .models import Invitation,InvitationIssue,InvitationIssueGrant,InvitationIssuanceScope


@override_settings(SHB_SYNTHETIC_FIXTURE=True)
class InvitationIssuanceTests(TransactionTestCase):
    client_class=invitation_admin_tests.InvitationAdminTests.client_class
    post=invitation_admin_tests.InvitationAdminTests.post
    challenge=invitation_admin_tests.InvitationAdminTests.challenge
    authenticated=invitation_admin_tests.InvitationAdminTests.authenticated
    customer_submit=invitation_admin_tests.InvitationAdminTests.customer_submit

    def setUp(self):
        invitation_admin_tests.InvitationAdminTests.setUp(self)
        self.scope=service.register_fixture(customer=self.invitation.customer,registered_by=self.user,
            **{key:getattr(self.invitation,key) for key in service.SCOPE_FIELDS if key!='customer_id'})
        self.issue_grant=InvitationIssueGrant.objects.create(user=self.user,scope=self.scope)
        self.issue_route='shb-invitation-scopes/'+str(self.scope.pk)+'/'
        self.issue_value={'request_id':str(uuid.uuid4()),'reason':'Deliberate synthetic invitation issue.','replaces':''}
        self.initial=Invitation.objects.count()

    def issue(self,**changes):return self.post(self.issue_route,dict(self.issue_value,**changes))

    def no_publication(self):
        self.assertEqual(Invitation.objects.count(),self.initial)
        self.assertFalse(InvitationIssue.objects.filter(invitation__isnull=False).exists())

    def test_get_is_assigned_secret_free_and_effect_free(self):
        response=self.browser.get('/staff/'+self.issue_route)
        self.assertEqual(response.status_code,200)
        self.assertNotIn('token_digest',response.content.decode());self.assertNotIn('contact_email',response.content.decode())
        self.assertEqual(response['Cache-Control'],'no-store');self.assertEqual(response['Referrer-Policy'],'no-referrer')
        self.assertEqual(self.browser.get('/staff/shb-invitation-scopes/').json()['scopes'][0]['id'],str(self.scope.pk))
        self.assertFalse(InvitationIssue.objects.exists());self.no_publication()

    def test_post_shows_one_bearer_and_retry_preserves_original_issue(self):
        response=self.issue();self.assertEqual(response.status_code,201)
        value=response.json();path=value['invitation_path'];token=path.removeprefix('/invite/')
        self.assertRegex(token,r'^[A-Za-z0-9_-]{43}$');event=InvitationIssue.objects.select_related('invitation').get()
        from .invitations import six_month_expiry
        self.assertEqual(event.invitation.expires_at,six_month_expiry(event.created_at))
        self.assertEqual(event.invitation.issuer_id,self.user.pk)
        for key in service.SCOPE_FIELDS:self.assertEqual(getattr(event.invitation,key),getattr(self.scope,key))
        self.assertFalse(value['actual_invitation_authority']);self.assertFalse(value['actual_email_sent'])
        self.assertNotIn(token,json.dumps(event.payload));self.assertNotIn(token,json.dumps(event.archive_receipt))
        self.assertTrue(all(token.encode() not in p.read_bytes() for p in Path(self.directory.name).iterdir() if p.is_file()))
        replay=self.issue();self.assertEqual(replay.status_code,200);self.assertIsNone(replay.json()['invitation_path'])
        self.assertEqual(replay.json()['issue'],value['issue']);self.assertEqual(InvitationIssue.objects.count(),1)
        self.assertNotIn(token,self.browser.get('/staff/'+self.issue_route).content.decode())
        self.assertNotIn(event.invitation.token_digest,self.browser.get('/staff/'+self.issue_route).content.decode())
        with override_settings(**self.customer_settings):
            self.assertEqual(self.client.get(path,secure=True).status_code,302)
            self.assertEqual(self.client.get('/shop/',secure=True).status_code,200)

    def test_changed_same_key_and_forged_scope_fields_cannot_issue(self):
        self.assertEqual(self.issue().status_code,201)
        self.assertEqual(self.issue(reason='Changed command').status_code,409)
        for key in ('customer_id','company_name','expires_at','fpga_eligible','asic_allowed','approved','token'):
            self.assertEqual(self.issue(**{key:'forged'}).status_code,400)
        self.assertEqual(InvitationIssue.objects.count(),1)

    def test_missing_scope_disabled_eligibility_mfa_and_fixture_gate_deny(self):
        self.issue_grant.delete();self.assertEqual(self.issue().status_code,404)
        self.assertEqual(self.browser.get('/staff/'+self.issue_route).status_code,404)
        self.assertEqual(self.browser.get('/staff/shb-invitation-scopes/',{'before':str(self.scope.pk)}).status_code,404)
        self.issue_grant=InvitationIssueGrant.objects.create(user=self.user,scope=self.scope)
        InvitationIssuanceScope.objects.filter(pk=self.scope.pk).update(enabled=False)
        self.assertEqual(self.issue().status_code,409)
        InvitationIssuanceScope.objects.filter(pk=self.scope.pk).update(enabled=True)
        session=self.browser.session;marker=session['shop_staff_mfa'];marker['verified_at']-=301;session['shop_staff_mfa']=marker;session.save()
        self.assertEqual(self.issue().status_code,403)
        marker['verified_at']+=301;session['shop_staff_mfa']=marker;session.save()
        with override_settings(SHB_SYNTHETIC_FIXTURE=False):self.assertEqual(self.issue().status_code,503)
        self.no_publication();self.assertFalse(InvitationIssue.objects.exists())

    def test_inactive_customer_or_staff_customer_is_not_issuable(self):
        customer=self.invitation.customer
        for changes in ({'is_active':False},{'is_active':True,'is_staff':True}):
            type(customer).objects.filter(pk=customer.pk).update(**changes)
            self.assertEqual(self.issue().status_code,409)
        self.no_publication()

    def test_native_form_and_csrf_share_issue_service_without_cookie_secret(self):
        page=self.browser.get('/staff/'+self.issue_route,HTTP_ACCEPT='text/html');self.assertContains(page,'Issue synthetic invitation')
        no_csrf=Client(enforce_csrf_checks=True,HTTP_HOST='staff.localhost');no_csrf.cookies=self.browser.cookies.copy()
        self.assertEqual(no_csrf.post('/staff/'+self.issue_route,self.issue_value).status_code,403);self.no_publication()
        form=dict(self.issue_value,csrfmiddlewaretoken=self.browser.cookies['shop_staff_csrftoken'].value)
        response=self.browser.post('/staff/'+self.issue_route,urlencode(form),content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code,201);self.assertContains(response,'/invite/',status_code=201)
        self.assertFalse(any('/invite/' in cookie.value for cookie in response.cookies.values()))
        self.assertNotContains(self.browser.get('/staff/'+self.issue_route,HTTP_ACCEPT='text/html'),'/invite/')

    def test_archive_failure_retains_same_prepared_digest_and_retry_cannot_reveal_secret(self):
        from shop.adapters.evidence_archive import PreparedArchive,ArchiveError
        with patch.object(PreparedArchive,'publish',side_effect=ArchiveError('owned outage')):
            self.assertEqual(self.issue().status_code,503)
        self.no_publication();event=InvitationIssue.objects.get();original=(event.pk,event.sha256,event.created_at,event.payload)
        response=self.issue();self.assertEqual(response.status_code,200);self.assertIsNone(response.json()['invitation_path'])
        event.refresh_from_db();self.assertEqual((event.pk,event.sha256,event.created_at,event.payload),original)
        self.assertEqual(event.invitation_id,event.pk)

    def test_replacement_requires_inactive_exact_scope_and_preserves_original_clock(self):
        self.assertEqual(self.issue(replaces=str(self.invitation.pk)).status_code,409)
        from .invitations import issue_fixture
        other,_=issue_fixture(customer=self.invitation.customer,issuer=self.user,company_name='Different legal entity')
        self.assertEqual(self.issue(replaces=str(other.pk)).status_code,404)
        old_expiry=self.invitation.expires_at;stamp=timezone.now()
        Invitation.objects.filter(pk=self.invitation.pk).update(revoked_at=stamp)
        response=self.issue(replaces=str(self.invitation.pk));self.assertEqual(response.status_code,201)
        self.invitation.refresh_from_db();self.assertEqual(self.invitation.revoked_at,stamp);self.assertEqual(self.invitation.expires_at,old_expiry)
        event=InvitationIssue.objects.get();self.assertEqual(event.replaces_id,self.invitation.pk)
        self.assertEqual(self.issue(replaces=str(self.invitation.pk),request_id=str(uuid.uuid4())).status_code,409)
        self.assertEqual(self.issue(replaces=str(self.invitation.pk)).status_code,200)

    def test_expired_month_end_replacement_is_separate_six_calendar_month_issue(self):
        from datetime import datetime,timezone as utc
        from .invitations import issue_fixture
        old,_=issue_fixture(customer=self.invitation.customer,issuer=self.user,
            **{key:getattr(self.scope,key) for key in service.SCOPE_FIELDS if key not in ('customer_id','eligibility_reference')},
            created_at=datetime(2025,8,31,6,tzinfo=utc.utc))
        self.assertEqual(old.expires_at,datetime(2026,2,28,6,tzinfo=utc.utc))
        self.assertEqual(self.issue(replaces=str(old.pk)).status_code,201)
        self.assertEqual(InvitationIssue.objects.get().replaces_id,old.pk)

    def test_grant_and_mfa_are_rechecked_after_archive_io(self):
        original=service.notifications.evidence
        def publish(*args,**kwargs):
            result=original(*args,**kwargs);self.issue_grant.delete();return result
        with patch.object(service.notifications,'evidence',side_effect=publish):self.assertEqual(self.issue().status_code,404)
        self.no_publication();self.assertEqual(InvitationIssue.objects.count(),1)
        self.issue_grant=InvitationIssueGrant.objects.get(user=self.user,scope=self.scope)  # Failed publication rolled its grant deletion back.
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
        for replaces in (None,True,1):self.assertEqual(self.issue(replaces=replaces).status_code,400)
        self.assertEqual(self.issue(replaces='bad-id').status_code,422)
        self.assertEqual(self.issue(request_id='bad-id').status_code,422)
        self.no_publication();self.assertFalse(InvitationIssue.objects.exists())

    def test_sql_eligibility_and_published_audit_cannot_be_edited_or_deleted(self):
        self.assertEqual(self.issue().status_code,201)
        for command in (lambda:InvitationIssuanceScope.objects.update(fpga_eligible=False),
                lambda:InvitationIssuanceScope.objects.all().delete(),lambda:InvitationIssue.objects.update(payload={}),
                lambda:InvitationIssue.objects.all().delete(),lambda:InvitationIssue.objects.update(archive_receipt={})):
            with self.assertRaises(DatabaseError),transaction.atomic():command()

    def test_interruption_before_publication_commit_rolls_back_invitation_and_retries_same_intent(self):
        original=InvitationIssue.save
        def interrupted(row,*args,**kwargs):
            if row.invitation_id is not None:raise RuntimeError('owned publication interruption')
            return original(row,*args,**kwargs)
        with patch.object(InvitationIssue,'save',interrupted):
            with self.assertRaisesMessage(RuntimeError,'owned publication interruption'):self.issue()
        self.no_publication();event=InvitationIssue.objects.get();digest=event.sha256
        response=self.issue();self.assertEqual(response.status_code,200);self.assertIsNone(response.json()['invitation_path'])
        event.refresh_from_db();self.assertEqual(event.sha256,digest);self.assertEqual(event.invitation_id,event.pk)

    def test_sql_cannot_publish_prepared_intent_against_another_invitation(self):
        from shop.adapters.evidence_archive import PreparedArchive,ArchiveError
        with patch.object(PreparedArchive,'publish',side_effect=ArchiveError('owned outage')):
            self.assertEqual(self.issue().status_code,503)
        with self.assertRaises(DatabaseError),transaction.atomic():
            InvitationIssue.objects.update(invitation=self.invitation,archive_receipt={'forged':True})
        self.no_publication()

    def test_sql_refuses_active_invitation_when_issue_publication_update_is_omitted(self):
        original=InvitationIssue.save
        def omitted(row,*args,**kwargs):
            if row.invitation_id is None:return original(row,*args,**kwargs)
        with patch.object(InvitationIssue,'save',omitted):
            with self.assertRaisesMessage(DatabaseError,'invitation and issue publication must commit together'):self.issue()
        self.no_publication();self.assertEqual(InvitationIssue.objects.count(),1)

    def test_issuance_preserves_requests_discount_reservations_and_notices(self):
        from .models import SupportRequest,DiscountReservation,TransactionNotice
        models=(SupportRequest,DiscountReservation,TransactionNotice)
        before=[list(model.objects.values()) for model in models]
        self.assertEqual(self.issue().status_code,201)
        self.assertEqual([list(model.objects.values()) for model in models],before)

    def test_concurrent_exact_retries_publish_one_invitation_and_only_one_bearer_response(self):
        cookies=self.browser.cookies.copy();barrier=Barrier(2)
        def invoke(_):
            connections.close_all()
            try:
                client=Client(enforce_csrf_checks=True,HTTP_HOST='staff.localhost');client.cookies=cookies.copy();barrier.wait(timeout=5)
                response=client.post('/staff/'+self.issue_route,data=json.dumps(self.issue_value),content_type='application/json',HTTP_X_CSRFTOKEN=cookies['shop_staff_csrftoken'].value)
                return response.status_code,response.json()
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(invoke,range(2)))
        self.assertEqual(sorted(status for status,_ in results),[200,201]);self.assertEqual(InvitationIssue.objects.count(),1)
        self.assertEqual(sum(bool(value.get('invitation_path')) for _,value in results),1)
        self.assertEqual(Invitation.objects.count(),self.initial+1)

    def test_operator_and_reset_clear_only_mutable_issuance_grants(self):
        from shop.access.grants import revoke_staff_resource_grants
        self.issue_grant.delete()
        call_command('local_staff','grant-invitation-issue',username=self.user.username,issuance_scope=str(self.scope.pk),stdout=io.StringIO())
        self.assertEqual(self.issue().status_code,201)
        with transaction.atomic():counts=revoke_staff_resource_grants(user_id=self.user.pk)
        self.assertEqual(counts['shb_invitation_issue'],1);self.assertFalse(InvitationIssueGrant.objects.exists())
        self.assertEqual(self.issue().status_code,404);self.assertEqual(InvitationIssue.objects.count(),1)

    def test_recovery_retains_issued_evidence_and_original_clocks(self):
        from .recovery import inspect_local_shb_recovery
        from shop.access.recovery import local_recovery_operation
        self.assertEqual(self.issue().status_code,201);event=InvitationIssue.objects.select_related('invitation').get()
        original=(event.sha256,event.invitation.created_at,event.invitation.expires_at)
        reset=uuid.uuid4();local_recovery_operation(action='quarantine',request_id=reset,expected_database=connection.settings_dict['NAME'])
        report=inspect_local_shb_recovery();self.assertEqual(report['counts']['invitation_issues'],1)
        self.assertFalse(report['post_backup_completeness_established']);self.assertFalse(report['reopening_authorized'])
        local_recovery_operation(action='release',request_id=uuid.uuid4(),basis_reset=reset,expected_database=connection.settings_dict['NAME'])
        event=InvitationIssue.objects.select_related('invitation').get()
        self.assertEqual((event.sha256,event.invitation.created_at,event.invitation.expires_at),original)

    def test_missing_published_archive_refuses_fixture_recovery_release(self):
        from shop.access.recovery import local_recovery_operation,AccessRecoveryError
        self.assertEqual(self.issue().status_code,201);event=InvitationIssue.objects.get()
        (Path(self.directory.name)/('blob-'+event.sha256)).unlink()
        reset=uuid.uuid4();local_recovery_operation(action='quarantine',request_id=reset,expected_database=connection.settings_dict['NAME'])
        with self.assertRaisesMessage(AccessRecoveryError,'shb_recovery_evidence_required'):
            local_recovery_operation(action='release',request_id=uuid.uuid4(),basis_reset=reset,expected_database=connection.settings_dict['NAME'])

    def test_selected_restore_clears_issuance_assignment_but_retains_original_audit(self):
        from shop.access.recovery import local_recovery_operation
        self.assertEqual(self.issue().status_code,201);event=InvitationIssue.objects.get();digest=event.sha256
        reset=uuid.uuid4()
        with override_settings(LOCAL_RESTORE_ID=reset):
            result=local_recovery_operation(action='quarantine',request_id=reset,expected_database=connection.settings_dict['NAME'])
            self.assertEqual(result['invalidated']['staff_resource_grants']['shb_invitation_issue'],1)
            local_recovery_operation(action='release',request_id=uuid.uuid4(),basis_reset=reset,expected_database=connection.settings_dict['NAME'])
        self.assertFalse(InvitationIssueGrant.objects.exists());self.assertEqual(InvitationIssue.objects.get().sha256,digest)
        self.assertEqual(self.issue().status_code,403)
