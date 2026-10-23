"""Real-PG staff reads of exact retained attempts; no work capability or I/O."""
from unittest.mock import patch
import uuid
from django.db import DatabaseError
from django.test import TransactionTestCase,override_settings
from shop.catalog.archive_claim import claim_request_archive
from shop.catalog.archive_publication import publish_request_archive
from shop.catalog.models import ArchiveWorkClaim,ArchivePreparedVerification,ArchiveWorkAuthorization
from shop.adapters.archive_destination import BoundPreparedArchive
from shop.worker import prepared_command_tests as fixtures
from . import staff_tests
from .models import StaffQuotationGrant

@override_settings(**staff_tests.STAFF_SETTINGS)
class ArchiveObservationTests(TransactionTestCase):
    owner_context=fixtures.PreparedCommandTests.owner_context
    owner_request=fixtures.PreparedCommandTests.owner_request
    attach=fixtures.PreparedCommandTests.attach
    business=fixtures.PreparedCommandTests.business
    save_envelope=fixtures.PreparedCommandTests.save_envelope
    post=fixtures.PreparedCommandTests.post
    challenge=fixtures.PreparedCommandTests.challenge
    authenticated=fixtures.PreparedCommandTests.authenticated
    grant=fixtures.PreparedCommandTests.grant
    enable_private=fixtures.PreparedCommandTests.enable_private
    bind=fixtures.PreparedCommandTests.bind
    authorize=fixtures.PreparedCommandTests.authorize
    revoke=fixtures.PreparedCommandTests.revoke
    setUp=fixtures.PreparedCommandTests.setUp

    def attempt(self):
        grant=self.authorize();claim=claim_request_archive(grant.authorization_id,self.proof.id)
        return grant,claim

    def staff(self):
        self.authenticated();self.grant();self.enable_private(1)

    def url(self,claim_id,intent_id=None):
        return '/staff/archive-intents/'+str(intent_id or self.intent.pk)+'/claims/'+str(claim_id)+'/reconciliation/'

    def assert_private(self,response):
        self.assertEqual(response['Cache-Control'],'no-store')
        self.assertEqual(response['Referrer-Policy'],'no-referrer')
        self.assertIn('Cookie',response['Vary'])
        self.assertIn("form-action 'none'",response['Content-Security-Policy'])
        self.assertIn("frame-ancestors 'none'",response['Content-Security-Policy'])

    def test_absent_then_committed_verification_is_read_only_safe_and_observable_after_revocation(self):
        grant,claim=self.attempt();self.staff();url=self.url(claim.claim_id)
        files={p.name:p.read_bytes() for p in self.root.iterdir()}
        before=list(ArchiveWorkAuthorization.objects.values())
        with patch('shop.adapters.archive_destination.BoundPreparedArchive.attest') as attest:
            response=self.browser.get(url)
            self.assertEqual(response.status_code,200)
            self.assertEqual(response.json(),{'status':'verification_not_recorded','evidence_class':'local-synthetic',
                'evidence_kind':'prepared','retention_qualified':False,'effects_authorized':False})
            self.assert_private(response);attest.assert_not_called()
        self.assertEqual(list(ArchiveWorkAuthorization.objects.values()),before)
        self.assertEqual(ArchiveWorkClaim.objects.count(),1);self.assertEqual(ArchivePreparedVerification.objects.count(),0)
        self.assertEqual({p.name:p.read_bytes() for p in self.root.iterdir()},files)
        with BoundPreparedArchive(self.root,self.proof) as archive:publish_request_archive(claim.claim_id,claim.token,archive)
        self.revoke(grant);verification=list(ArchivePreparedVerification.objects.values())
        response=self.browser.get(url)
        self.assertEqual(response.json()['status'],'verification_recorded');self.assert_private(response)
        self.assertEqual(list(ArchivePreparedVerification.objects.values()),verification)
        self.assertEqual(ArchiveWorkClaim.objects.count(),1)
        for secret in (str(self.root),str(self.intent.pk),str(claim.claim_id),str(claim.token),'BUSINESS_SCOPE_ONE_PRIVATE_SYNTHETIC'):
            self.assertNotIn(secret,response.content.decode())

    def test_recent_mfa_assignment_and_exact_private_scope_required_on_every_read(self):
        _,claim=self.attempt();url=self.url(claim.claim_id)
        self.assertEqual(self.browser.get(url).status_code,403)
        self.authenticated();self.assertEqual(self.browser.get(url).status_code,404)
        self.grant();self.assertEqual(self.browser.get(url).status_code,404)
        self.enable_private(1);self.assertEqual(self.browser.get(url).status_code,200)
        StaffQuotationGrant.objects.filter(user=self.user).update(business_scope_version=0)
        self.assertEqual(self.browser.get(url).status_code,404)
        self.enable_private(1)
        session=self.browser.session;session['shop_staff_mfa']={**session['shop_staff_mfa'],'verified_at':0};session.save()
        response=self.browser.get(url);self.assertEqual(response.status_code,403)
        # Existing staff middleware denies stale MFA before entering this view.
        self.assertEqual(response['Cache-Control'],'no-store')
        self.assertEqual(response['Referrer-Policy'],'no-referrer')
        self.assertEqual(ArchivePreparedVerification.objects.count(),0)

    def test_html_query_method_unknown_and_wrong_intent_are_fixed_private_responses(self):
        _,claim=self.attempt();self.staff();url=self.url(claim.claim_id)
        response=self.browser.get(url,HTTP_ACCEPT='text/html')
        self.assertContains(response,'Physical publication may still exist or be in progress.')
        self.assertContains(response,'grants no retry');self.assert_private(response)
        self.assertNotContains(response,str(claim.claim_id));self.assertNotContains(response,'BUSINESS_SCOPE_ONE_PRIVATE_SYNTHETIC')
        for path in (self.url(uuid.uuid4()),self.url(claim.claim_id,uuid.uuid4())):
            response=self.browser.get(path);self.assertEqual(response.status_code,404)
            self.assertEqual(response.json(),{'error':'not_found'});self.assert_private(response)
        self.assertEqual(self.browser.get(url+'?retry=true').status_code,400)
        response=self.browser.head(url);self.assertEqual(response.status_code,405);self.assert_private(response)
        self.assertEqual(ArchiveWorkClaim.objects.count(),1);self.assertEqual(ArchivePreparedVerification.objects.count(),0)

    def test_database_failure_is_fixed_unavailable_without_private_diagnostics(self):
        _,claim=self.attempt();self.staff()
        for target in ('reconcile_archive_publication','staff_credential'):
            with patch('shop.access.archive_observation.'+target,side_effect=DatabaseError('PRIVATE_DATABASE_CANARY')):
                response=self.browser.get(self.url(claim.claim_id))
                self.assertEqual(response.status_code,503)
                self.assertEqual(response.json(),{'error':'observation_unavailable'});self.assert_private(response)
                self.assertNotIn(b'PRIVATE_DATABASE_CANARY',response.content)
        self.assertEqual(ArchiveWorkClaim.objects.count(),1);self.assertEqual(ArchivePreparedVerification.objects.count(),0)

    def test_removed_assignment_changed_owner_and_nonstaff_runtime_cannot_observe(self):
        _,claim=self.attempt();self.staff();url=self.url(claim.claim_id)
        self.assertEqual(self.browser.get(url).status_code,200)
        StaffQuotationGrant.objects.filter(user=self.user).delete()
        self.assertEqual(self.browser.get(url).status_code,404)
        self.grant();self.enable_private(1)
        cart=self.quotation.cart;cart.owner=self.other;cart.save(update_fields=['owner'])
        response=self.browser.get(url);self.assertEqual(response.status_code,404);self.assert_private(response)
        with override_settings(SHOP_ENV='production'):
            self.assertEqual(self.browser.get(url).status_code,404)
        with self.owner_context():
            self.assertEqual(self.owner_client.get(url).status_code,404)
        self.assertEqual(ArchiveWorkClaim.objects.count(),1);self.assertEqual(ArchivePreparedVerification.objects.count(),0)
