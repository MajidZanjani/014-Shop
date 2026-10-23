"""Detached point-in-time checks against current source/authority, no worker."""
from datetime import timedelta
from unittest.mock import patch
import uuid
from django.contrib.auth import get_user_model
from django.db import transaction
from django.test import TransactionTestCase,override_settings
from shop.access import staff_tests
from shop.access.models import StaffCredential,StaffQuotationGrant
from . import archive_authority_tests as fixtures
from .archive_authority import inspect_active_authorization
from .models import RequestArchiveIntent,RequestEnvelope
from .request_envelope import EnvelopeError

@override_settings(**staff_tests.STAFF_SETTINGS)
class ArchiveInspectionTests(TransactionTestCase):
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
    def inspect(self,reference):return inspect_active_authorization(reference.authorization_id,self.proof.id)

    def test_absent_authority_exact_destination_expiry_supersession_revocation(self):
        with self.assertRaises(EnvelopeError):inspect_active_authorization(uuid.uuid4(),self.proof.id)
        first=self.authorize();active=self.inspect(first)
        self.assertEqual(active.intent_id,self.intent.pk);self.assertFalse(hasattr(active,'payload'))
        with self.assertRaises(EnvelopeError):inspect_active_authorization(first.authorization_id,uuid.uuid4())
        from .models import ArchiveWorkAuthorization
        grant=ArchiveWorkAuthorization.objects.get()
        for instant in (grant.issued_at-timedelta(microseconds=1),grant.not_after):
            with patch('shop.catalog.archive_authority.db_now',return_value=instant):
                with self.assertRaises(EnvelopeError):self.inspect(first)
        second=self.authorize(generation=1,command=uuid.uuid4())
        with self.assertRaises(EnvelopeError):self.inspect(first)
        self.inspect(second);self.revoke(second)
        with self.assertRaises(EnvelopeError):self.inspect(second)

    def test_current_account_ownership_payload_and_hold_rechecked(self):
        reference=self.authorize()
        get_user_model().objects.filter(pk=self.owner.pk).update(is_active=False)
        with self.assertRaises(EnvelopeError):self.inspect(reference)
        get_user_model().objects.filter(pk=self.owner.pk).update(is_active=True)
        self.inspect(reference)
        from .models import DraftCart
        DraftCart.objects.filter(pk=self.quotation.cart_id).update(owner=self.other)
        with self.assertRaises(EnvelopeError):self.inspect(reference)
        DraftCart.objects.filter(pk=self.quotation.cart_id).update(owner=self.owner)
        original=RequestEnvelope.objects.get().sha256;RequestEnvelope.objects.update(sha256='0'*64)
        with self.assertRaises(EnvelopeError):self.inspect(reference)
        RequestEnvelope.objects.update(sha256=original);RequestArchiveIntent.objects.update(state='held')
        with self.assertRaises(EnvelopeError):self.inspect(reference)
        self.assertEqual(RequestArchiveIntent.objects.get().state,'held')

    def test_staff_generation_and_private_scope_are_current_without_browser_session(self):
        self.authenticated();self.grant();self.enable_private(1)
        request=self.browser.get('/staff/quotation-requests/').wsgi_request;reference=self.authorize(request)
        self.inspect(reference)
        StaffQuotationGrant.objects.filter(user=self.user).update(business_scope_version=0)
        with self.assertRaises(EnvelopeError):self.inspect(reference)
        self.enable_private(1);self.inspect(reference)
        StaffCredential.objects.filter(pk=self.credential.pk).update(generation=uuid.uuid4())
        with self.assertRaises(EnvelopeError):self.inspect(reference)

    def test_outer_transaction_and_live_mode_denied_without_work(self):
        reference=self.authorize()
        with transaction.atomic():
            with self.assertRaises(EnvelopeError):self.inspect(reference)
        with override_settings(SHOP_ENV='production'):
            with self.assertRaises(EnvelopeError):self.inspect(reference)
        self.assertEqual(RequestArchiveIntent.objects.get().state,'pending')
