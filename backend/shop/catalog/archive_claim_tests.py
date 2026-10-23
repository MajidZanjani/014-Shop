"""Actual PostgreSQL claim/reclaim/authority races; no publication."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier,Event
from unittest.mock import patch
import uuid
from django.db import connection,connections,transaction,IntegrityError
from django.test import TransactionTestCase,override_settings
from shop.access import staff_tests
from . import archive_authority_tests as fixtures
from .archive_claim import claim_request_archive,inspect_archive_claim
from .models import ArchiveWorkClaim,ArchiveWorkAuthorization,RequestArchiveIntent
from .request_envelope import EnvelopeError

@override_settings(**staff_tests.STAFF_SETTINGS)
class ArchiveClaimTests(TransactionTestCase):
    owner_context=fixtures.ArchiveAuthorityTests.owner_context
    owner_request=fixtures.ArchiveAuthorityTests.owner_request
    attach=fixtures.ArchiveAuthorityTests.attach
    business=fixtures.ArchiveAuthorityTests.business
    save_envelope=fixtures.ArchiveAuthorityTests.save_envelope
    post=fixtures.ArchiveAuthorityTests.post
    challenge=fixtures.ArchiveAuthorityTests.challenge
    authenticated=fixtures.ArchiveAuthorityTests.authenticated
    grant=fixtures.ArchiveAuthorityTests.grant
    enable_private=fixtures.ArchiveAuthorityTests.enable_private
    bind=fixtures.ArchiveAuthorityTests.bind
    authorize=fixtures.ArchiveAuthorityTests.authorize
    revoke=fixtures.ArchiveAuthorityTests.revoke
    setUp=fixtures.ArchiveAuthorityTests.setUp
    def claim(self,reference):return claim_request_archive(reference.authorization_id,self.proof.id)
    def inspect(self,claim):return inspect_archive_claim(claim.claim_id,claim.token)

    def test_lease_busy_expiry_reclaim_and_old_token_fenced(self):
        reference=self.authorize();first=self.claim(reference);row=ArchiveWorkClaim.objects.get()
        self.assertEqual(row.expires_at-row.started_at,timedelta(seconds=30));self.inspect(first)
        self.assertNotIn(str(first.token),repr(first))
        with self.assertRaises(EnvelopeError):self.claim(reference)
        with self.assertRaises(EnvelopeError):inspect_archive_claim(first.claim_id,uuid.uuid4())
        with patch('shop.catalog.archive_authority.db_now',return_value=row.expires_at):
            with self.assertRaises(EnvelopeError):self.inspect(first)
            second=self.claim(reference);self.assertEqual(second.generation,2);self.inspect(second)
            with self.assertRaises(EnvelopeError):self.inspect(first)
        self.assertEqual(ArchiveWorkClaim.objects.count(),2)
        self.assertEqual(RequestArchiveIntent.objects.get().state,'pending')

    def test_lease_capped_at_grant_expiry_and_revocation_hold_supersession(self):
        reference=self.authorize();grant=ArchiveWorkAuthorization.objects.get()
        with patch('shop.catalog.archive_authority.db_now',return_value=grant.not_after-timedelta(seconds=2)):
            claim=self.claim(reference);self.assertEqual(ArchiveWorkClaim.objects.get().expires_at,grant.not_after)
        with self.assertRaises(EnvelopeError):self.inspect(claim)
        with patch('shop.catalog.archive_authority.db_now',return_value=grant.not_after):
            with self.assertRaises(EnvelopeError):self.claim(reference)
        self.revoke(reference)
        with self.assertRaises(EnvelopeError):self.inspect(claim)
        with self.assertRaises(EnvelopeError):self.claim(reference)
        second=self.authorize(generation=1,command=uuid.uuid4())
        RequestArchiveIntent.objects.update(state='held')
        with self.assertRaises(EnvelopeError):self.claim(second)
        self.assertEqual(RequestArchiveIntent.objects.get().state,'held')

    def test_competing_claims_have_one_winner_and_revocation_race_never_survives(self):
        reference=self.authorize();barrier=Barrier(2)
        def competing(_):
            try:
                barrier.wait(timeout=10)
                try:return self.claim(reference)
                except EnvelopeError:return None
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(competing,range(2)))
        self.assertEqual(sum(item is not None for item in results),1);claim=next(item for item in results if item)
        self.assertEqual(ArchiveWorkClaim.objects.count(),1)
        self.revoke(reference)
        with self.assertRaises(EnvelopeError):self.inspect(claim)
        # New intent generation, race its first claim against explicit revocation.
        second=self.authorize(generation=1,command=uuid.uuid4());row=ArchiveWorkClaim.objects.get()
        request=self.owner_request();revocation_locked=Event();owner_locked=Event()
        from . import archive_authority
        original_scope=archive_authority.locked_scope
        def pause_revocation(*args):
            scope=original_scope(*args);revocation_locked.set()
            self.assertTrue(owner_locked.wait(timeout=10));return scope
        def observe_owner(execute,sql,params,many,context):
            result=execute(sql,params,many,context)
            if 'auth_user' in sql and 'FOR NO KEY UPDATE' in sql:owner_locked.set()
            return result
        def race(index):
            try:
                if index==0:
                    self.assertTrue(revocation_locked.wait(timeout=10))
                    with connection.execute_wrapper(observe_owner):
                        try:return self.claim(second)
                        except EnvelopeError:return None
                return self.revoke(second,request)
            finally:connections.close_all()
        with patch('shop.catalog.archive_authority.db_now',return_value=row.expires_at),patch('shop.catalog.archive_authority.locked_scope',pause_revocation):
            with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(race,range(2)))
            if results[0] is not None:
                with self.assertRaises(EnvelopeError):self.inspect(results[0])
            with self.assertRaises(EnvelopeError):self.claim(second)
        self.assertIsNotNone(results[1])

    def test_database_constraints_outer_transaction_and_no_effects(self):
        reference=self.authorize()
        with transaction.atomic():
            with self.assertRaises(EnvelopeError):self.claim(reference)
        claim=self.claim(reference);row=ArchiveWorkClaim.objects.get()
        with transaction.atomic():
            with self.assertRaises(EnvelopeError):self.inspect(claim)
        for values in ({'generation':0},{'effects_authorized':True},{'retention_qualified':True},
            {'expires_at':row.started_at},{'expires_at':row.started_at+timedelta(seconds=31)}):
            with self.assertRaises(IntegrityError):
                with transaction.atomic():ArchiveWorkClaim.objects.filter(pk=row.pk).update(**values)
        self.assertFalse(row.effects_authorized);self.assertFalse(row.retention_qualified)
