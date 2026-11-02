"""Scoped staff revocation stops new claims and preserves locked concessions."""
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
from . import invitation_admin_tests,offer_tests,review_tests,discount_admin as service
from .models import DiscountCode,DiscountStaffGrant,DiscountRevocation,DiscountReservation,PaidOrder


@override_settings(SHB_SYNTHETIC_FIXTURE=True)
class DiscountAdminTests(TransactionTestCase):
    client_class=review_tests.RequestReviewTests.client_class
    post=review_tests.RequestReviewTests.post
    challenge=review_tests.RequestReviewTests.challenge
    authenticated=review_tests.RequestReviewTests.authenticated
    customer_submit=review_tests.RequestReviewTests.customer_submit
    submit=review_tests.RequestReviewTests.submit
    issue_offer=offer_tests.OfferTests.issue
    offer=offer_tests.OfferTests.offer
    customer_review=offer_tests.OfferTests.customer_review
    accept_offer=offer_tests.OfferTests.accept_offer
    pay=offer_tests.OfferTests.pay

    def setUp(self):
        invitation_admin_tests.InvitationAdminTests.setUp(self)
        self.discount_grant=DiscountStaffGrant.objects.create(user=self.user,discount=self.discount)
        self.discount_route='shb-discounts/'+str(self.discount.pk)+'/'
        self.revoke_value={'request_id':str(uuid.uuid4()),'reason':'Deliberate synthetic discount revocation.'}

    def revoke(self,**changes):return self.post(self.discount_route,dict(self.revoke_value,**changes))

    def untouched(self):
        self.discount.refresh_from_db();self.assertIsNone(self.discount.revoked_at)
        self.assertFalse(DiscountRevocation.objects.exists())

    def test_get_is_exactly_scoped_code_free_and_has_no_effects(self):
        response=self.browser.get('/staff/'+self.discount_route)
        self.assertEqual(response.status_code,200);self.assertEqual(response['Cache-Control'],'no-store')
        self.assertEqual(response['Referrer-Policy'],'no-referrer')
        for secret in (self.code,self.discount.code_digest,'code_digest','contact_email'):
            self.assertNotIn(secret,response.content.decode())
        self.assertEqual(self.browser.get('/staff/shb-discounts/').json()['discounts'][0]['id'],str(self.discount.pk))
        self.untouched()

    def test_exact_retry_preserves_original_discount_and_held_request(self):
        before=service.snapshot(self.discount);hold=list(DiscountReservation.objects.values());payload=self.row.payload
        self.assertEqual(self.revoke().status_code,201);self.assertEqual(self.revoke().status_code,200)
        event=DiscountRevocation.objects.get();self.assertEqual(event.payload['discount'],before)
        self.assertEqual(event.payload['actor']['staff_id'],self.user.pk);self.assertFalse(event.payload['actual_discount_authority'])
        self.assertEqual(self.revoke(reason='Changed decision').status_code,409)
        self.assertEqual(self.revoke(request_id=str(uuid.uuid4())).status_code,409)
        self.discount.refresh_from_db();self.assertEqual(service.snapshot(self.discount),before)
        self.row.refresh_from_db();self.assertEqual(self.row.payload,payload)
        self.assertEqual(list(DiscountReservation.objects.values()),hold)
        self.assertEqual(DiscountRevocation.objects.count(),1)

    def test_new_claim_is_denied_after_revocation_without_affecting_invitation(self):
        from .discounts import issue_fixture
        row,code=issue_fixture(customer=self.customer,issuer=self.user,percentage_bps=1500,asic_allowed=True,use_limit=2)
        DiscountStaffGrant.objects.create(user=self.user,discount=row)
        with override_settings(**self.customer_settings):self.assertEqual(self.customer_submit(action='apply_discount',discount_code=code).status_code,200)
        self.discount_route='shb-discounts/'+str(row.pk)+'/'
        self.assertEqual(self.revoke().status_code,201)
        with override_settings(**self.customer_settings):
            self.assertEqual(self.customer_submit(action='apply_discount',discount_code=code).status_code,422)
            self.assertEqual(self.client.get('/shop/',secure=True).status_code,200)
        self.invitation.refresh_from_db();self.assertIsNone(self.invitation.revoked_at)

    def test_reserved_asic_offer_still_accepts_and_pays_original_concession_once(self):
        self.assertEqual(self.issue_offer().status_code,201)
        original=self.offer().payload;expiry=self.discount.expires_at
        self.assertEqual(self.revoke().status_code,201)
        data,digest=self.customer_review();accepted=self.accept_offer(data,digest)
        self.assertEqual(accepted.status_code,302)
        self.assertEqual(self.pay(accepted['Location']).status_code,200);self.assertEqual(self.pay(accepted['Location']).status_code,200)
        order=PaidOrder.objects.get();hold=DiscountReservation.objects.get()
        self.assertEqual(order.payload['purchase'],original['purchase']);self.assertEqual(order.payload['purchase']['hours_purchased'],50)
        self.assertEqual(order.payload['purchase']['total_minor'],875000)
        self.assertEqual(hold.state,'consumed');self.assertEqual(hold.consumed_order_id,order.pk)
        self.discount.refresh_from_db();self.assertEqual(self.discount.expires_at,expiry);self.assertIsNotNone(self.discount.revoked_at)
        self.assertEqual(PaidOrder.objects.count(),1);self.assertEqual(DiscountRevocation.objects.count(),1)

    def test_missing_exact_grant_and_cursor_cannot_disclose_or_revoke(self):
        self.discount_grant.delete()
        self.assertEqual(self.revoke().status_code,404);self.assertEqual(self.browser.get('/staff/'+self.discount_route).status_code,404)
        self.assertEqual(self.browser.get('/staff/shb-discounts/').json()['discounts'],[])
        self.assertEqual(self.browser.get('/staff/shb-discounts/',{'before':str(self.discount.pk)}).status_code,404)
        self.untouched()

    def test_recent_mfa_and_synthetic_only_gate_are_enforced(self):
        session=self.browser.session;marker=session['shop_staff_mfa'];old=marker['verified_at']
        marker['verified_at']-=301;session['shop_staff_mfa']=marker;session.save();self.assertEqual(self.revoke().status_code,403)
        marker['verified_at']=old;session['shop_staff_mfa']=marker;session.save()
        with override_settings(SHB_SYNTHETIC_FIXTURE=False):self.assertEqual(self.revoke().status_code,503)
        self.untouched()

    def test_native_form_and_csrf_use_same_archived_action(self):
        page=self.browser.get('/staff/'+self.discount_route,HTTP_ACCEPT='text/html');self.assertContains(page,'Revoke synthetic discount')
        token=self.browser.cookies['shop_staff_csrftoken'].value
        no_csrf=Client(enforce_csrf_checks=True,HTTP_HOST='staff.localhost');no_csrf.cookies=self.browser.cookies.copy()
        self.assertEqual(no_csrf.post('/staff/'+self.discount_route,self.revoke_value).status_code,403);self.untouched()
        response=self.browser.post('/staff/'+self.discount_route,urlencode(dict(self.revoke_value,csrfmiddlewaretoken=token)),content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code,303)
        page=self.browser.get(response['Location'],HTTP_ACCEPT='text/html');self.assertContains(page,'Revoked:');self.assertNotContains(page,'Revoke synthetic discount')

    def test_invalid_reason_forged_policy_and_cursors_do_not_write(self):
        for value in ('',' ',None,True,1,'x'*513,chr(0)):
            self.assertEqual(self.revoke(reason=value).status_code,400)
        for key in ('percentage_bps','customer_id','expires_at','use_limit','approved','replacement','code'):
            self.assertEqual(self.revoke(**{key:'forged'}).status_code,400)
        self.assertEqual(self.revoke(request_id='bad-id').status_code,422)
        self.assertEqual(self.browser.get('/staff/shb-discounts/',{'before':'bad-id'}).status_code,400)
        self.untouched()

    def test_archive_failure_does_not_revoke_or_release_reservation(self):
        from shop.adapters.evidence_archive import PreparedArchive,ArchiveError
        with patch.object(PreparedArchive,'publish',side_effect=ArchiveError('owned outage')):self.assertEqual(self.revoke().status_code,503)
        self.untouched();self.assertEqual(DiscountReservation.objects.get().state,'reserved')
        self.assertEqual(self.revoke().status_code,201)

    def test_grant_is_rechecked_after_archive_io_and_uncertain_archive_is_not_overwritten(self):
        original=service.notifications.evidence
        def changed(*args,**kwargs):
            result=original(*args,**kwargs);self.discount_grant.delete();return result
        with patch.object(service.notifications,'evidence',side_effect=changed):self.assertEqual(self.revoke().status_code,404)
        self.untouched()
        self.assertEqual(self.revoke().status_code,503);self.untouched()

    def test_mfa_is_rechecked_after_archive_io(self):
        original=service.notifications.evidence;clock=None
        def expired(*args,**kwargs):
            nonlocal clock
            result=original(*args,**kwargs);clock=patch('shop.access.staff_auth.timezone.now',return_value=timezone.now()+timedelta(seconds=301));clock.start();return result
        try:
            with patch.object(service.notifications,'evidence',side_effect=expired):self.assertEqual(self.revoke().status_code,403)
        finally:
            if clock:clock.stop()
        self.untouched()

    def test_sql_timestamp_must_commit_with_audit_and_uncertain_archive_holds_retry(self):
        with patch.object(DiscountCode,'save',return_value=None):
            with self.assertRaisesMessage(DatabaseError,'audit and revocation must commit together'):self.revoke()
        self.untouched();self.assertEqual(self.revoke().status_code,503);self.untouched()

    def test_sql_revocation_audit_is_append_only(self):
        self.assertEqual(self.revoke().status_code,201)
        for command in (lambda:DiscountRevocation.objects.update(payload={}),lambda:DiscountRevocation.objects.all().delete()):
            with self.assertRaises(DatabaseError),transaction.atomic():command()

    def test_concurrent_exact_retries_record_one_revocation(self):
        cookies=self.browser.cookies.copy();barrier=Barrier(2)
        def invoke(_):
            connections.close_all()
            try:
                client=Client(enforce_csrf_checks=True,HTTP_HOST='staff.localhost');client.cookies=cookies.copy();barrier.wait(timeout=5)
                return client.post('/staff/'+self.discount_route,data=json.dumps(self.revoke_value),content_type='application/json',HTTP_X_CSRFTOKEN=cookies['shop_staff_csrftoken'].value).status_code
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:statuses=list(pool.map(invoke,range(2)))
        self.assertEqual(sorted(statuses),[200,201]);self.assertEqual(DiscountRevocation.objects.count(),1)

    def test_operator_reset_and_selected_restore_clear_discount_grants_keep_audit(self):
        from shop.access.grants import revoke_staff_resource_grants
        from shop.access.recovery import local_recovery_operation
        self.discount_grant.delete()
        call_command('local_staff','grant-discount',username=self.user.username,discount=str(self.discount.pk),stdout=io.StringIO())
        self.assertEqual(self.revoke().status_code,201)
        with transaction.atomic():counts=revoke_staff_resource_grants(user_id=self.user.pk)
        self.assertEqual(counts['shb_discount'],1);self.assertEqual(DiscountRevocation.objects.count(),1)
        DiscountStaffGrant.objects.create(user=self.user,discount=self.discount)
        reset=uuid.uuid4()
        with override_settings(LOCAL_RESTORE_ID=reset):
            result=local_recovery_operation(action='quarantine',request_id=reset,expected_database=connection.settings_dict['NAME'])
            self.assertEqual(result['invalidated']['staff_resource_grants']['shb_discount'],1)
            local_recovery_operation(action='release',request_id=uuid.uuid4(),basis_reset=reset,expected_database=connection.settings_dict['NAME'])
        self.assertFalse(DiscountStaffGrant.objects.exists());self.assertEqual(DiscountRevocation.objects.count(),1)

    def test_missing_archive_holds_recovery_and_original_policy_is_retained(self):
        from shop.access.recovery import local_recovery_operation,AccessRecoveryError
        from .recovery import inspect_local_shb_recovery
        self.assertEqual(self.revoke().status_code,201);event=DiscountRevocation.objects.get()
        reset=uuid.uuid4();local_recovery_operation(action='quarantine',request_id=reset,expected_database=connection.settings_dict['NAME'])
        report=inspect_local_shb_recovery();self.assertEqual(report['counts']['discount_revocations'],1)
        self.assertFalse(report['post_backup_completeness_established']);self.assertFalse(report['reopening_authorized'])
        (Path(self.directory.name)/('blob-'+event.sha256)).unlink()
        with self.assertRaisesMessage(AccessRecoveryError,'shb_recovery_evidence_required'):
            local_recovery_operation(action='release',request_id=uuid.uuid4(),basis_reset=reset,expected_database=connection.settings_dict['NAME'])

    def test_legacy_revocation_keeps_original_state_without_invented_audit(self):
        DiscountCode.objects.filter(pk=self.discount.pk).update(revoked_at=timezone.now())
        self.assertEqual(self.revoke().status_code,409);self.assertFalse(DiscountRevocation.objects.exists())
        self.assertContains(self.browser.get('/staff/'+self.discount_route,HTTP_ACCEPT='text/html'),'Revoked:')
