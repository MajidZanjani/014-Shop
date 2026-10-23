"""Private immutable request recovery; no new routes or domain writes."""
import copy
from pathlib import Path
import tempfile
from unittest.mock import patch
import uuid
from django.test import Client,TransactionTestCase,override_settings
from shop.access import staff_tests
from shop.access.models import StaffQuotationGrant
from shop.adapters.evidence_archive import PreparedArchive
from . import binding_tests as fixtures
from .models import QuotationRequest,QuotationBusinessScope,BusinessDraftSnapshot,CartSnapshot,DraftCart
from .request_envelope import prepare_request_envelope,validate_envelope,canonical,EnvelopeError
from .rules import CATALOG
from .tests import verified_login

@override_settings(**staff_tests.STAFF_SETTINGS)
class RequestEnvelopeTests(TransactionTestCase):
    def setUp(self):
        fixtures.BusinessBindingTests.setUp(self)
        from django.contrib.auth import get_user_model
        self.other=get_user_model().objects.create_user(username='envelope-other')
    owner_context=fixtures.BusinessBindingTests.owner_context
    owner_get=fixtures.BusinessBindingTests.owner_get
    attach=fixtures.BusinessBindingTests.attach
    business=fixtures.BusinessBindingTests.business
    enable_private=fixtures.BusinessBindingTests.enable_private
    post=fixtures.BusinessBindingTests.post
    challenge=fixtures.BusinessBindingTests.challenge
    authenticated=fixtures.BusinessBindingTests.authenticated
    grant=fixtures.BusinessBindingTests.grant

    def owner_bytes(self,version=1,client=None):
        with self.owner_context():
            request=(client or self.owner_client).get('/api/v1/customer/session/').wsgi_request
            return prepare_request_envelope(request,self.quotation.pk,version)

    def staff_bytes(self,version=1):
        request=self.browser.get('/staff/quotation-requests/').wsgi_request
        return prepare_request_envelope(request,self.quotation.pk,version)

    def test_recoverable_private_scope_and_exact_replay_without_domain_writes(self):
        self.assertEqual(self.attach().status_code,303)
        before=(QuotationRequest.objects.count(),QuotationBusinessScope.objects.count(),BusinessDraftSnapshot.objects.count(),CartSnapshot.objects.count())
        raw=self.owner_bytes();value=validate_envelope(raw)
        from django.db import connection
        self.assertFalse(connection.in_atomic_block)
        self.assertIn(b'BUSINESS_SCOPE_ONE_PRIVATE_SYNTHETIC',raw)
        self.assertEqual(value['business_scope']['snapshot']['details'],self.saved.details)
        self.assertEqual(value['business_scope']['snapshot']['submission_digest'],self.saved.submission_digest)
        self.assertEqual(value['cart']['lines'],self.quotation.snapshot.lines)
        self.assertEqual(value['request']['request_id'],str(self.quotation.request_id))
        self.assertEqual(value['cart']['request_id'],str(self.quotation.snapshot.request_id))
        self.assertEqual(value['business_scope']['snapshot']['request_id'],str(self.saved.request_id))
        self.assertTrue(all(v is None for v in value['commercial'].values()))
        self.assertTrue(all(v is False for v in value['gates'].values()))
        with tempfile.TemporaryDirectory() as directory:
            with PreparedArchive(Path(directory)) as archive:receipt=archive.publish(uuid.UUID(value['envelope_id']),raw)
            with PreparedArchive(Path(directory)) as archive:
                self.assertEqual(validate_envelope(archive.recover(receipt)),value)
                self.assertEqual(archive.publish(receipt.evidence_id,self.owner_bytes()),receipt)
        self.assertEqual(raw,self.owner_bytes())
        self.assertEqual(before,(QuotationRequest.objects.count(),QuotationBusinessScope.objects.count(),BusinessDraftSnapshot.objects.count(),CartSnapshot.objects.count()))
        ordinary=self.owner_get('/api/v1/quotation-requests/'+str(self.quotation.pk)+'/')
        self.assertNotContains(ordinary,'BUSINESS_SCOPE_ONE_PRIVATE_SYNTHETIC')

    def test_historical_scopes_and_later_edits_do_not_change_exact_bytes(self):
        self.assertEqual(self.attach().status_code,303)
        original=self.owner_bytes();unbound=self.owner_bytes(0)
        self.assertIsNone(validate_envelope(unbound)['business_scope'])
        self.business(2,'PRIVATE_LATER_SCOPE')
        self.assertEqual(self.attach(dict(self.request,request_id=str(uuid.uuid4()),expected_scope_version='1',business_version='2')).status_code,303)
        self.assertEqual(self.owner_bytes(),original)
        self.assertEqual(self.owner_bytes(0),unbound)
        later=self.owner_bytes(2);self.assertNotEqual(later,original)
        self.assertNotEqual(validate_envelope(later)['envelope_id'],validate_envelope(original)['envelope_id'])
        self.assertNotIn(b'PRIVATE_LATER_SCOPE',original)

    def test_staff_requires_recent_verification_assignment_and_exact_private_scope(self):
        self.assertEqual(self.attach().status_code,303)
        with self.assertRaises(EnvelopeError):self.staff_bytes()
        self.authenticated()
        with self.assertRaises(EnvelopeError):self.staff_bytes()
        self.grant()
        with self.assertRaises(EnvelopeError):self.staff_bytes()
        self.enable_private(1)
        self.assertEqual(self.staff_bytes(),self.owner_bytes())
        self.assertIsNone(validate_envelope(self.staff_bytes(0))['business_scope'])
        historical=self.owner_bytes()
        self.business(2,'PRIVATE_ENVELOPE_SCOPE_TWO')
        self.assertEqual(self.attach(dict(self.request,request_id=str(uuid.uuid4()),expected_scope_version='1',business_version='2')).status_code,303)
        self.assertEqual(self.staff_bytes(),historical)
        with self.assertRaises(EnvelopeError):self.staff_bytes(2)
        self.enable_private(2)
        self.assertEqual(self.staff_bytes(2),self.owner_bytes(2))
        with self.assertRaises(EnvelopeError):self.staff_bytes()
        StaffQuotationGrant.objects.filter(user=self.user).update(business_scope_version=0)
        with self.assertRaises(EnvelopeError):self.staff_bytes()
        self.enable_private(2)
        marker=self.browser.session;marker['shop_staff_mfa']['verified_at']-=301;marker.save()
        with self.assertRaises(EnvelopeError):self.staff_bytes(2)

    def test_owner_mode_future_scope_and_source_corruption_are_held_without_echo(self):
        self.assertEqual(self.attach().status_code,303)
        stranger=Client(HTTP_HOST='127.0.0.1')
        with self.assertRaises(EnvelopeError):self.owner_bytes(client=stranger)
        with self.owner_context():verified_login(stranger,self.other)
        with self.assertRaises(EnvelopeError):self.owner_bytes(client=stranger)
        for version in (-1,True,2,'1'):
            with self.assertRaises(EnvelopeError):self.owner_bytes(version)
        for mode in ('production','bank-sandbox'):
            with override_settings(SHOP_ENV=mode):
                with self.assertRaises(EnvelopeError):self.owner_bytes()
        BusinessDraftSnapshot.objects.filter(pk=self.saved.pk).update(source_sha256='0'*64)
        with self.assertRaises(EnvelopeError) as raised:self.owner_bytes()
        self.assertNotIn('PRIVATE',str(raised.exception))
        self.assertNotIn(str(self.quotation.pk),str(raised.exception))

    def test_closed_validator_rejects_tampering_noncanonical_and_approval_values(self):
        self.assertEqual(self.attach().status_code,303)
        raw=self.owner_bytes();value=validate_envelope(raw)
        mutations=[]
        for path,replacement in [(('gates','acceptance_enabled'),True),(('gates','effects_authorized'),0),
            (('commercial','tax'),0),(('request','owner_id'),True),(('request','business_version'),True),
            (('cart','version'),False),(('business_scope','version'),True),
            (('business_scope','snapshot','owner_id'),123456),(('business_scope','snapshot','details','tax_status'),'invented')]:
            altered=copy.deepcopy(value);target=altered
            for key in path[:-1]:target=target[key]
            target[path[-1]]=replacement;mutations.append(canonical(altered))
        extra=copy.deepcopy(value);extra['password']='PRIVATE_PASSWORD';mutations.append(canonical(extra))
        altered=copy.deepcopy(value);altered['envelope_id']=str(uuid.uuid4());mutations.append(canonical(altered))
        mutations += [raw+b' ',b'{"schema":1,"schema":1}',b'NaN',b'x'*131073]
        for modified in mutations:
            with self.assertRaises(EnvelopeError) as raised:validate_envelope(modified)
            self.assertNotIn('PRIVATE',str(raised.exception))
        with patch.dict(CATALOG,revision='f'*64):
            with self.assertRaises(EnvelopeError) as raised:validate_envelope(raw)
            self.assertEqual(str(raised.exception),'envelope_source_unavailable')

    def test_changed_cart_parent_and_business_ownership_are_not_recoverable_scope(self):
        self.assertEqual(self.attach().status_code,303)
        from .models import BusinessDraft
        BusinessDraft.objects.filter(pk=self.saved.draft_id).update(owner=self.other)
        with self.assertRaises(EnvelopeError):self.owner_bytes()
        BusinessDraft.objects.filter(pk=self.saved.draft_id).update(owner=self.owner)
        othercart=DraftCart.objects.create(owner=self.other)
        QuotationRequest.objects.filter(pk=self.quotation.pk).update(cart=othercart)
        with self.assertRaises(EnvelopeError):self.owner_bytes(0)

    def test_support_only_original_scope_has_no_invented_ip_or_host_inputs(self):
        from .cart_tests import CASES
        from .cart_rules import evaluate_cart
        lines=copy.deepcopy(CASES[2]['lines'])
        CartSnapshot.objects.filter(pk=self.quotation.snapshot_id).update(lines=lines,evaluation=evaluate_cart(lines))
        value=validate_envelope(self.owner_bytes(0))
        self.assertIsNone(value['business_scope'])
        self.assertEqual(value['cart']['lines'],lines)
        self.assertEqual(value['cart']['evaluation']['quoted_support_seconds'],72000)
        self.assertNotIn(b'host',canonical(value))
        self.assertNotIn(b'vendor',canonical(value))
        CartSnapshot.objects.filter(pk=self.quotation.snapshot_id).update(evaluation={'valid':True})
        with self.assertRaises(EnvelopeError):self.owner_bytes(0)

    def test_authorized_recovery_binds_exact_receipt_and_rejects_outer_transactions(self):
        from django.db import transaction
        from shop.adapters.evidence_archive import PreparedReceipt
        from .request_envelope import recover_request_envelope
        self.assertEqual(self.attach().status_code,303)
        expected=self.owner_bytes();value=validate_envelope(expected)
        with self.owner_context():
            request=self.owner_client.get('/api/v1/customer/session/').wsgi_request
            with tempfile.TemporaryDirectory() as directory,PreparedArchive(Path(directory)) as archive:
                receipt=archive.publish(uuid.UUID(value['envelope_id']),expected)
                self.assertEqual(recover_request_envelope(request,self.quotation.pk,1,receipt,archive),expected)
                wrong=PreparedReceipt(uuid.uuid4(),receipt.sha256,receipt.size)
                with patch.object(archive,'recover') as read:
                    with self.assertRaises(EnvelopeError):recover_request_envelope(request,self.quotation.pk,1,wrong,archive)
                    read.assert_not_called()
                    with transaction.atomic():
                        with self.assertRaises(EnvelopeError) as raised:recover_request_envelope(request,self.quotation.pk,1,receipt,archive)
                    self.assertEqual(str(raised.exception),'archive_transaction_active')
                    read.assert_not_called()

    def test_private_grant_revocation_during_archive_io_denies_return_and_preserves_evidence(self):
        from django.db import connection
        from .request_envelope import recover_request_envelope
        self.assertEqual(self.attach().status_code,303)
        expected=self.owner_bytes();self.authenticated();self.grant();self.enable_private(1)
        request=self.browser.get('/staff/quotation-requests/').wsgi_request
        with tempfile.TemporaryDirectory() as directory,PreparedArchive(Path(directory)) as archive:
            receipt=archive.publish(uuid.UUID(validate_envelope(expected)['envelope_id']),expected)
            original=archive.recover
            def revoke(reference):
                self.assertFalse(connection.in_atomic_block)
                raw=original(reference)
                StaffQuotationGrant.objects.filter(user=self.user).update(business_scope_version=0)
                return raw
            with patch.object(archive,'recover',revoke):
                with self.assertRaises(EnvelopeError):recover_request_envelope(request,self.quotation.pk,1,receipt,archive)
            self.assertEqual(len(list(Path(directory).iterdir())),2)
            self.enable_private(1)
            self.assertEqual(recover_request_envelope(request,self.quotation.pk,1,receipt,archive),expected)
