"""Immutable commercial consumption; fixtures never establish actual approval."""
import hashlib
from copy import deepcopy
from unittest.mock import Mock, patch
from django.test import SimpleTestCase
from shop.payments.purchase_flow_tests import configuration
from . import commercial_revisions as revisions
from .rules import CATALOG


class CommercialRevisionTests(SimpleTestCase):
    def setUp(self):
        self.configuration = configuration(packages=2)
        self.policy = revisions.fixture_revision(self.configuration, 'synthetic-development',
            buyer_scope_revision='b' * 64, documents_revision='d' * 64)

    def consume(self, value=None, **kwargs):
        value = deepcopy(self.policy['policy'] if value is None else value)
        body = revisions.canonical(value)
        params = dict(revision=revisions.digest(value), catalog_revision=CATALOG['revision'],
                      buyer_scope_revision='b' * 64, synthetic=True)
        params.update(kwargs)
        return revisions.consume(body, **params)

    def test_exact_immutable_policy_and_custom_unfinished_boards(self):
        for platform in ({'choice': 'other-board', 'kit_id': None, 'name': 'Unfinished custom board'},
                         {'choice': 'not-designed', 'kit_id': None, 'name': None}):
            config = self.configuration | {'platform': platform}
            snapshot = revisions.quote(self.policy, config, 'synthetic-development', support_packages=2)
            self.assertEqual(snapshot['total_minor'], 17035)
            self.assertEqual(snapshot['support_seconds'], 72000)
            self.assertTrue(snapshot['offer']['later_reference_design'])
            self.assertFalse(snapshot['activation_authorized'])
            self.assertEqual(snapshot['evidence_class'], 'local-synthetic')

    def test_digest_catalog_source_and_buyer_scope_mismatch(self):
        with self.assertRaises(revisions.CommercialRevisionError):
            self.consume(revision='0' * 64)
        for key in ('catalog_revision', 'source_sha256', 'buyer_scope_revision'):
            value = deepcopy(self.policy['policy']); value[key] = '0' * 64
            with self.assertRaises(revisions.CommercialRevisionError):
                revisions.quote(self.consume(value), self.configuration, 'synthetic-development', support_packages=2)

    def test_stale_licence_scope_not_inferred_from_compatible_vendor(self):
        for field, replacement in [('families', ['altera-cyclone-v']), ('fixed_nodes', 2), ('term', 'perpetual')]:
            with self.assertRaises(revisions.CommercialRevisionError):
                revisions.quote(self.policy, self.configuration | {field: replacement},
                                'synthetic-development', support_packages=2)

    def test_required_support_minimum_server_owned(self):
        for value in (0, 1, 3, True, 2.0, -1):
            with self.assertRaises(revisions.CommercialRevisionError):
                revisions.quote(self.policy, self.configuration, 'synthetic-development', support_packages=value)
        policy = deepcopy(self.policy['policy']); policy['offers'][0]['minimum_packages'] = None
        with self.assertRaises(revisions.CommercialRevisionError):
            revisions.quote(self.consume(policy), self.configuration, 'synthetic-development', support_packages=2)

    def test_missing_facts_never_approve_a_sale(self):
        for key in revisions.FACTS:
            value = deepcopy(self.policy['policy']); value['offers'][0]['facts'][key] = None
            with self.assertRaises(revisions.CommercialRevisionError):
                revisions.quote(self.consume(value), self.configuration, 'synthetic-development', support_packages=2)
        for key in revisions.FACTS:
            value = deepcopy(self.policy['policy']); value['support']['facts'][key] = None
            with self.assertRaises(revisions.CommercialRevisionError):
                revisions.quote(self.consume(value), self.configuration, 'synthetic-development', support_packages=2)
        value = deepcopy(self.policy['policy']); value['support']['unit_minor'] = None
        with self.assertRaises(revisions.CommercialRevisionError):
            revisions.quote(self.consume(value), self.configuration, 'synthetic-development', support_packages=2)

    def test_json_flags_and_fixture_cannot_supply_protected_approval(self):
        value = deepcopy(self.policy['policy']); value['evidence_class'] = 'approved-commercial'
        for verifier in (None, lambda **pins: False, lambda **pins: 'approved'):
            with self.assertRaises(revisions.CommercialRevisionError):
                self.consume(value, synthetic=False, verify_approval=verifier)
        with self.assertRaises(revisions.CommercialRevisionError): self.consume(synthetic=False, verify_approval=lambda **pins: True)
        with self.assertRaises(revisions.CommercialRevisionError): self.consume(value)

    def test_qualified_adapter_receives_every_exact_pin(self):
        value = deepcopy(self.policy['policy']); value['evidence_class'] = 'approved-commercial'
        verifier = Mock(return_value=True)
        consumed = self.consume(value, synthetic=False, verify_approval=verifier)
        verifier.assert_called_once_with(revision=revisions.digest(value), catalog_revision=CATALOG['revision'],
            source_sha256=CATALOG['source_sha256'], buyer_scope_revision='b' * 64)
        self.assertFalse(consumed['effects_authorized'])

    def test_support_only_no_questionnaire_and_no_expiry(self):
        policy = revisions.fixture_support_revision(buyer_scope_revision='b' * 64, documents_revision='d' * 64)
        result = revisions.quote_support(policy, quantity=3)
        self.assertEqual(result['support_seconds'], 108000)
        self.assertEqual(result['total_minor'], 7035)
        self.assertFalse(result['expires'])
        self.assertNotIn('configuration', result)
        for value in (0, -1, True, 1.0):
            with self.assertRaises(revisions.CommercialRevisionError): revisions.quote_support(policy, quantity=value)

    def test_mutated_consumed_revision_cannot_be_quoted(self):
        self.policy['policy']['offers'][0]['licence_minor'] = 1
        with self.assertRaises(revisions.CommercialRevisionError):
            revisions.quote(self.policy, self.configuration, 'synthetic-development', support_packages=2)
        with self.assertRaises(revisions.CommercialRevisionError): revisions.quote_support(self.policy, quantity=1)

    def test_duplicate_noncanonical_and_unbounded_json_rejected(self):
        for body in (b'{"schema":1,"schema":1}', b' ' + revisions.canonical(self.policy['policy']), b'x' * 262145):
            import hashlib
            with self.assertRaises(revisions.CommercialRevisionError):
                revisions.consume(body, revision=hashlib.sha256(body).hexdigest(), catalog_revision=CATALOG['revision'],
                                  buyer_scope_revision='b' * 64, synthetic=True)

    def test_optional_zero_support_ignores_pending_unrelated_policies(self):
        config = configuration('listed-kit', packages=0)
        consumed = revisions.fixture_revision(config, 'synthetic-ready-kit',
            buyer_scope_revision='b' * 64, documents_revision='d' * 64)
        value = deepcopy(consumed['policy'])
        value['support'].update(unit_minor=None, seconds=None, expires=None,
                                facts={key: None for key in revisions.FACTS})
        value['documents']['support_terms'] = None
        other = deepcopy(self.policy['policy']['offers'][0]); other['licence_minor'] = None
        other['facts'] = {key: None for key in revisions.FACTS}
        value['offers'].append(other)
        snapshot = revisions.quote(self.consume(value), config, 'synthetic-ready-kit', support_packages=0)
        self.assertEqual(snapshot['total_minor'], 12345)
        self.assertEqual(snapshot['support_seconds'], 0)
        with self.assertRaises(revisions.CommercialRevisionError):
            revisions.quote(self.consume(value), self.configuration, 'synthetic-development', support_packages=2)

    def test_support_only_ignores_pending_ip_policy_and_licence_document(self):
        value = deepcopy(self.policy['policy'])
        del value['documents']['ip_licence']
        value['offers'][0]['licence_minor'] = None
        value['offers'][0]['facts'] = {key: None for key in revisions.FACTS}
        result = revisions.quote_support(self.consume(value), quantity=1)
        self.assertEqual(result['support_seconds'], 36000)
        for key in ('general_terms', 'refund_policy', 'privacy_policy', 'support_terms'):
            pending = deepcopy(value); pending['documents'][key] = None
            with self.assertRaises(revisions.CommercialRevisionError):
                revisions.quote_support(self.consume(pending), quantity=1)

    def test_pending_fact_sentinels_and_strict_selected_types(self):
        for sentinel in ('pending', ' UNKNOWN ', 'tbd', 'unapproved'):
            value = deepcopy(self.policy['policy']); value['offers'][0]['facts']['rights'] = sentinel
            with self.assertRaises(revisions.CommercialRevisionError):
                revisions.quote(self.consume(value), self.configuration, 'synthetic-development', support_packages=2)
        for field, values in [('licence_minor', [True, 1.5, '12345', None]),
                              ('minimum_packages', [True, 2.0, '2', None]),
                              ('support_required', [1, 'required', None])]:
            for invalid in values:
                value = deepcopy(self.policy['policy']); value['offers'][0][field] = invalid
                with self.assertRaises(revisions.CommercialRevisionError):
                    revisions.quote(self.consume(value), self.configuration, 'synthetic-development', support_packages=2)

    def test_nonfinite_deep_and_integer_overflow_bytes_use_domain_rejection(self):
        bodies=[b'NaN',b'Infinity',b'-Infinity',b'1e9999',b'1'*5000,
                b'['*2000+b'0'+b']'*2000]
        for body in bodies:
            verifier=Mock(return_value=True)
            with self.subTest(body_kind=body[:8]),self.assertRaises(revisions.CommercialRevisionError):
                revisions.consume(body,revision=hashlib.sha256(body).hexdigest(),
                    catalog_revision=CATALOG['revision'],buyer_scope_revision='b'*64,
                    verify_approval=verifier,synthetic=False)
            verifier.assert_not_called()

    def test_approval_adapter_failures_hold_once_without_private_diagnostics(self):
        value=deepcopy(self.policy['policy']);value['evidence_class']='approved-commercial'
        for failure in (RuntimeError,TimeoutError,OSError,ValueError):
            with self.subTest(failure=failure):
                verifier=Mock(side_effect=failure('SYNTHETIC_PRIVATE_APPROVAL_CANARY'))
                with self.assertRaises(revisions.CommercialRevisionError) as caught:
                    self.consume(value,synthetic=False,verify_approval=verifier)
                self.assertEqual(str(caught.exception),'protected_approval_required')
                self.assertNotIn('CANARY',str(caught.exception))
                verifier.assert_called_once()
        verifier=Mock(side_effect=RuntimeError('fixture must not use actual adapter'))
        result=self.consume(verify_approval=verifier)
        verifier.assert_not_called()
        self.assertEqual(result['policy']['evidence_class'],'local-synthetic')
        self.assertFalse(result['effects_authorized'])

    def test_nonserializable_mutated_policy_quotes_use_domain_rejection(self):
        for invalid in (float('nan'),float('inf'),object()):
            value=deepcopy(self.policy)
            value['policy']['offers'][0]['licence_minor']=invalid
            for quote in (lambda:revisions.quote(value,self.configuration,'synthetic-development',support_packages=2),
                          lambda:revisions.quote_support(value,quantity=1)):
                with self.subTest(kind=type(invalid).__name__),self.assertRaises(revisions.CommercialRevisionError):quote()
        value=deepcopy(self.policy);value['policy']['cycle']=value['policy']
        with self.assertRaises(revisions.CommercialRevisionError):
            revisions.quote_support(value,quantity=1)

    def test_detachment_failure_is_a_fixed_domain_hold(self):
        body=revisions.canonical(self.policy['policy'])
        with patch.object(revisions,'deepcopy',side_effect=RecursionError('SYNTHETIC_PRIVATE_COPY_CANARY')):
            with self.assertRaises(revisions.CommercialRevisionError) as caught:
                revisions.consume(body,revision=hashlib.sha256(body).hexdigest(),
                    catalog_revision=CATALOG['revision'],buyer_scope_revision='b'*64,synthetic=True)
        self.assertEqual(str(caught.exception),'revision_unavailable')
