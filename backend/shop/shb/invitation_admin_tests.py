"""Protected invitation revocation, exact staff scope and recoverable audit."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import io,json
from pathlib import Path
from threading import Barrier
from unittest.mock import patch
from urllib.parse import urlencode
import uuid
from django.conf import settings
from django.core.management import call_command
from django.db import DatabaseError,connection,connections,transaction
from django.test import Client,TransactionTestCase,override_settings
from django.utils import timezone
from . import review_tests
from .models import Invitation,InvitationStaffGrant,InvitationRevocation


@override_settings(SHB_SYNTHETIC_FIXTURE=True)
class InvitationAdminTests(TransactionTestCase):
    client_class=review_tests.RequestReviewTests.client_class
    post=review_tests.RequestReviewTests.post
    challenge=review_tests.RequestReviewTests.challenge
    authenticated=review_tests.RequestReviewTests.authenticated
    customer_submit=review_tests.RequestReviewTests.customer_submit

    def setUp(self):
        review_tests.RequestReviewTests.setUp(self)
        archive=override_settings(LOCAL_CHECKOUT_ARCHIVE_ROOT=self.directory.name)
        archive.enable();self.addCleanup(archive.disable)
        self.invite_grant=InvitationStaffGrant.objects.create(user=self.user,invitation=self.invitation)
        self.invite_route='shb-invitations/'+str(self.invitation.pk)+'/'
        self.revoke_value={'request_id':str(uuid.uuid4()),'reason':'Synthetic invitation withdrawn by the assigned staff member.'}

    def revoke(self,**changes):return self.post(self.invite_route,dict(self.revoke_value,**changes))

    def untouched(self):
        self.invitation.refresh_from_db();self.assertIsNone(self.invitation.revoked_at)
        self.assertFalse(InvitationRevocation.objects.exists())

    def test_staff_home_exposes_assigned_invitation_administration(self):
        response=self.browser.get('/staff/',HTTP_ACCEPT='text/html')
        self.assertEqual(response.status_code,200)
        self.assertTrue(b'Assigned invitations' in response.content)

    def test_revocation_assignment_does_not_grant_invitation_issuance(self):
        response=self.browser.get('/staff/shb-invitation-scopes/')
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json()['scopes'],[])
        self.untouched()

    def test_staff_home_exposes_scoped_discount_administration(self):
        response=self.browser.get('/staff/',HTTP_ACCEPT='text/html')
        self.assertEqual(response.status_code,200)
        self.assertIn(b'Assigned discounts',response.content)

    def test_scoped_get_hides_bearer_digest_and_has_no_commercial_effects(self):
        response=self.browser.get('/staff/'+self.invite_route)
        self.assertEqual(response.status_code,200)
        self.assertEqual(response['Cache-Control'],'no-store')
        self.assertEqual(response['Referrer-Policy'],'no-referrer')
        self.assertNotIn(self.invitation.token_digest,response.content.decode())
        self.assertNotIn('token_digest',response.content.decode())
        self.assertNotIn('contact_email',response.content.decode())
        queue=self.browser.get('/staff/shb-invitations/').json()
        self.assertEqual([row['id'] for row in queue['invitations']],[str(self.invitation.pk)])
        self.untouched()

    def test_exact_retry_and_revocation_deny_surviving_customer_session_without_closing_request(self):
        from .models import SupportRequest,DiscountReservation,TransactionNotice
        from shop.payments.models import SyntheticPaymentAttempt
        original=self.row.payload;expires=self.invitation.expires_at;notices=TransactionNotice.objects.count()
        self.assertEqual(self.revoke().status_code,201);self.assertEqual(self.revoke().status_code,200)
        event=InvitationRevocation.objects.get();self.assertEqual(event.payload['invitation']['id'],str(self.invitation.pk))
        self.assertEqual(event.payload['actor']['staff_id'],self.user.pk)
        self.assertFalse(event.payload['actual_invitation_authority'])
        self.assertEqual(self.revoke(reason='Different reason on original key').status_code,409)
        self.assertEqual(self.revoke(request_id=str(uuid.uuid4())).status_code,409)
        with override_settings(**self.customer_settings):
            self.assertEqual(self.client.get('/shop/',secure=True).status_code,403)
        self.assertEqual(SupportRequest.objects.get().payload,original)
        self.assertEqual(DiscountReservation.objects.get().state,'reserved')
        self.assertEqual(TransactionNotice.objects.count(),notices);self.assertFalse(SyntheticPaymentAttempt.objects.exists())
        self.invitation.refresh_from_db();self.assertEqual(self.invitation.expires_at,expires)
        self.assertEqual(review_tests.RequestReviewTests.submit(self,decision='ready_for_commercial_review').status_code,201)
        self.assertEqual(InvitationRevocation.objects.count(),1)

    def test_missing_exact_assignment_and_cursor_never_disclose_other_invitations(self):
        self.invite_grant.delete()
        self.assertEqual(self.browser.get('/staff/'+self.invite_route).status_code,404)
        self.assertEqual(self.revoke().status_code,404)
        self.assertEqual(self.browser.get('/staff/shb-invitations/').json()['invitations'],[])
        self.assertEqual(self.browser.get('/staff/shb-invitations/',{'before':str(self.invitation.pk)}).status_code,404)
        self.untouched()

    def test_recent_mfa_and_live_fixture_gate_are_enforced(self):
        session=self.browser.session;marker=session['shop_staff_mfa'];old=marker['verified_at']
        marker['verified_at']-=301;session['shop_staff_mfa']=marker;session.save()
        self.assertEqual(self.revoke().status_code,403)
        marker['verified_at']=old;session['shop_staff_mfa']=marker;session.save()
        with override_settings(SHB_SYNTHETIC_FIXTURE=False):self.assertEqual(self.revoke().status_code,503)
        self.untouched()

    def test_native_csrf_form_uses_same_service_and_does_not_offer_secret_recovery(self):
        page=self.browser.get('/staff/'+self.invite_route,HTTP_ACCEPT='text/html')
        self.assertContains(page,'Revoke synthetic invitation');self.assertNotContains(page,self.invitation.token_digest)
        token=self.browser.cookies['shop_staff_csrftoken'].value
        body=dict(self.revoke_value,csrfmiddlewaretoken=token)
        no_csrf=Client(enforce_csrf_checks=True,HTTP_HOST='staff.localhost');no_csrf.cookies=self.browser.cookies.copy()
        self.assertEqual(no_csrf.post('/staff/'+self.invite_route,self.revoke_value).status_code,403)
        self.untouched()
        response=self.browser.post('/staff/'+self.invite_route,urlencode(body),content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code,303);self.assertEqual(response['Location'],'/staff/'+self.invite_route)
        page=self.browser.get(response['Location'],HTTP_ACCEPT='text/html')
        self.assertContains(page,'Revoked:');self.assertNotContains(page,'Revoke synthetic invitation')

    def test_invalid_reasons_extra_fields_and_broken_cursors_are_rejected_without_writes(self):
        for value in ('',' ',None,True,1,'x'*513,'\U0001f600'*513,chr(0),'part'+chr(0)+'value'):
            with self.subTest(value_type=type(value).__name__):self.assertEqual(self.revoke(reason=value).status_code,400)
        for field in ('expires_at','customer_id','token','replacement','approved'):
            with self.subTest(field=field):self.assertEqual(self.revoke(**{field:'forged'}).status_code,400)
        self.assertEqual(self.revoke(request_id='bad-id').status_code,422)
        self.assertEqual(self.browser.get('/staff/shb-invitations/',{'before':'bad-id'}).status_code,400)
        self.assertEqual(self.browser.get('/staff/'+self.invite_route,{'before':'bad-id'}).status_code,400)
        self.untouched()

    def test_archive_failure_is_atomic(self):
        from shop.adapters.evidence_archive import PreparedArchive,ArchiveError
        with patch.object(PreparedArchive,'publish',side_effect=ArchiveError('owned outage')):
            self.assertEqual(self.revoke().status_code,503)
        self.untouched();self.assertEqual(self.revoke().status_code,201)

    def test_resource_grant_is_rechecked_after_archive_io(self):
        from . import invitation_admin
        original=invitation_admin.notifications.evidence
        def publish(*args,**kwargs):
            result=original(*args,**kwargs);self.invite_grant.delete();return result
        with patch.object(invitation_admin.notifications,'evidence',side_effect=publish):
            self.assertEqual(self.revoke().status_code,404)
        self.untouched()

    def test_mfa_is_rechecked_after_archive_io(self):
        from . import invitation_admin
        original=invitation_admin.notifications.evidence;clock=None
        def publish(*args,**kwargs):
            nonlocal clock
            result=original(*args,**kwargs)
            clock=patch('shop.access.staff_auth.timezone.now',return_value=timezone.now()+timedelta(seconds=301));clock.start()
            return result
        try:
            with patch.object(invitation_admin.notifications,'evidence',side_effect=publish):self.assertEqual(self.revoke().status_code,403)
        finally:
            if clock:clock.stop()
        self.untouched()

    def test_sql_audit_is_append_only(self):
        self.assertEqual(self.revoke().status_code,201)
        for command in (lambda:InvitationRevocation.objects.update(payload={}),lambda:InvitationRevocation.objects.all().delete()):
            with self.assertRaises(DatabaseError),transaction.atomic():command()
        self.assertEqual(InvitationRevocation.objects.count(),1)

    def test_sql_audit_cannot_commit_without_matching_revocation_state(self):
        with patch.object(Invitation,'save',return_value=None):
            with self.assertRaisesMessage(DatabaseError,'audit and revocation must commit together'):self.revoke()
        self.untouched()

    def test_concurrent_exact_retries_make_one_archived_revocation(self):
        cookies=self.browser.cookies.copy();barrier=Barrier(2)
        def invoke(_):
            connections.close_all()
            try:
                client=Client(enforce_csrf_checks=True,HTTP_HOST='staff.localhost');client.cookies=cookies.copy();barrier.wait(timeout=5)
                return client.post('/staff/'+self.invite_route,data=json.dumps(self.revoke_value),content_type='application/json',HTTP_X_CSRFTOKEN=cookies['shop_staff_csrftoken'].value).status_code
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:statuses=list(pool.map(invoke,range(2)))
        self.assertEqual(sorted(statuses),[200,201]);self.assertEqual(InvitationRevocation.objects.count(),1)

    def test_operator_grants_and_reset_clear_authority_without_erasing_audit(self):
        from shop.access.grants import revoke_staff_resource_grants
        self.invite_grant.delete()
        call_command('local_staff','grant-invitation',username=self.user.username,invitation=str(self.invitation.pk),stdout=io.StringIO())
        self.assertEqual(self.revoke().status_code,201)
        with transaction.atomic():counts=revoke_staff_resource_grants(user_id=self.user.pk)
        self.assertEqual(counts['shb_invitation'],1);self.assertFalse(InvitationStaffGrant.objects.exists())
        self.assertEqual(self.browser.get('/staff/'+self.invite_route).status_code,404)
        self.assertEqual(InvitationRevocation.objects.count(),1)

    def test_quarantine_denies_old_staff_session_and_recovery_retains_original_revocation(self):
        from shop.access.recovery import local_recovery_operation
        from .recovery import inspect_local_shb_recovery
        self.assertEqual(self.revoke().status_code,201)
        original=InvitationRevocation.objects.get();reset=uuid.uuid4()
        token=self.browser.cookies['shop_staff_csrftoken'].value
        local_recovery_operation(action='quarantine',request_id=reset,expected_database=connection.settings_dict['NAME'])
        response=self.browser.post('/staff/'+self.invite_route,data=json.dumps(self.revoke_value),content_type='application/json',HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code,403)
        report=inspect_local_shb_recovery();self.assertEqual(report['counts']['invitation_revocations'],1)
        self.assertFalse(report['post_backup_completeness_established']);self.assertFalse(report['reopening_authorized'])
        local_recovery_operation(action='release',request_id=uuid.uuid4(),basis_reset=reset,expected_database=connection.settings_dict['NAME'])
        self.invitation.refresh_from_db();self.assertEqual(self.invitation.revoked_at,original.revoked_at)
        self.assertEqual(InvitationRevocation.objects.get().sha256,original.sha256)

    def test_missing_audit_archive_refuses_fixture_recovery_release(self):
        from shop.access.recovery import local_recovery_operation,AccessRecoveryError
        from shop.access.models import AccessEpoch
        self.assertEqual(self.revoke().status_code,201)
        event=InvitationRevocation.objects.get();(Path(self.directory.name)/('blob-'+event.sha256)).unlink()
        reset=uuid.uuid4();local_recovery_operation(action='quarantine',request_id=reset,expected_database=connection.settings_dict['NAME'])
        with self.assertRaisesMessage(AccessRecoveryError,'shb_recovery_evidence_required'):
            local_recovery_operation(action='release',request_id=uuid.uuid4(),basis_reset=reset,expected_database=connection.settings_dict['NAME'])
        self.assertTrue(AccessEpoch.objects.get().quarantined)

    def test_legacy_manual_revocation_stays_revoked_without_inventing_an_audit(self):
        Invitation.objects.filter(pk=self.invitation.pk).update(revoked_at=timezone.now())
        page=self.browser.get('/staff/'+self.invite_route,HTTP_ACCEPT='text/html')
        self.assertContains(page,'Revoked:');self.assertNotContains(page,'Revoke synthetic invitation')
        self.assertEqual(self.revoke().status_code,409);self.assertFalse(InvitationRevocation.objects.exists())
