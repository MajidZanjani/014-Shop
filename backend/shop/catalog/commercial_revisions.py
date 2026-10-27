"""Consume immutable offer revisions; approval verification is a separate trusted adapter.

JSON cannot approve itself. No actual approval adapter is supplied by this module.
The existing fake-only checkout/runtime guards remain authoritative.
"""
from copy import deepcopy
import hashlib
import json
from .rules import CATALOG, KEYS, evaluate


class CommercialRevisionError(ValueError):
    pass


def canonical(value):
    try:
        return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()
    except (TypeError, ValueError, RecursionError, OverflowError) as exc:
        raise CommercialRevisionError('revision_unavailable') from exc


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def _reject_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise CommercialRevisionError('duplicate_field')
        result[key] = value
    return result


def _reject_constant(value):
    raise CommercialRevisionError('nonfinite_number')


FACTS = {'rights', 'access', 'coverage', 'terms', 'recurrence', 'production_accounting',
         'tax_legal_applicability', 'host_manager_applicability'}
SCOPE = KEYS - {'support_packages'}


def consume(body, *, revision, catalog_revision, buyer_scope_revision, verify_approval=None, synthetic=False):
    """Verify exact bytes/pins then return a detached revision for quote().

    verify_approval is server-owned trusted code, never a request parameter. It
    must authenticate protected approval for all four supplied pins and return
    exactly True. Missing verifier means actual revisions are unavailable.
    Fixture verification never calls or substitutes for that approval adapter.
    """
    if type(body) is not bytes or len(body) > 262144 or type(synthetic) is not bool:
        raise CommercialRevisionError('revision_unavailable')
    if hashlib.sha256(body).hexdigest() != revision:
        raise CommercialRevisionError('revision_mismatch')
    try:
        value = json.loads(body, object_pairs_hook=_reject_duplicates, parse_constant=_reject_constant)
        if canonical(value) != body:
            raise CommercialRevisionError('noncanonical_revision')
        if set(value) != {'schema', 'evidence_class', 'catalog_revision', 'source_sha256',
                          'buyer_scope_revision', 'currency', 'support', 'offers', 'documents'}:
            raise CommercialRevisionError('revision_fields')
        evidence = 'local-synthetic' if synthetic else 'approved-commercial'
        if (value['schema'] != 1 or type(value['schema']) is not int or value['evidence_class'] != evidence
                or value['catalog_revision'] != catalog_revision or catalog_revision != CATALOG['revision']
                or value['source_sha256'] != CATALOG['source_sha256']
                or value['buyer_scope_revision'] != buyer_scope_revision
                or not isinstance(buyer_scope_revision, str) or len(buyer_scope_revision) != 64
                or any(c not in '0123456789abcdef' for c in buyer_scope_revision)):
            raise CommercialRevisionError('revision_scope_mismatch')
        if not synthetic:
            if verify_approval is None:
                raise CommercialRevisionError('protected_approval_required')
            try:
                approved=verify_approval(revision=revision,catalog_revision=catalog_revision,
                    source_sha256=value['source_sha256'],buyer_scope_revision=buyer_scope_revision)
            except Exception as exc:
                # A failed trusted observation is unavailable, never approval or a retry.
                raise CommercialRevisionError('protected_approval_required') from exc
            if approved is not True:
                raise CommercialRevisionError('protected_approval_required')
        if value['currency'] != 'EUR':
            raise CommercialRevisionError('currency_unavailable')
        support = value['support']
        if (not isinstance(support, dict) or set(support) != {'product_id', 'unit_minor', 'seconds', 'expires', 'facts'}
                or support['product_id'] != CATALOG['support_product_id']):
            raise CommercialRevisionError('support_policy_unavailable')
        _fact_shape(support['facts'])
        if not isinstance(value['offers'], list) or len(value['offers']) > 100:
            raise CommercialRevisionError('offer_policy_unavailable')
        seen = set()
        for offer in value['offers']:
            if set(offer) != {'id', 'scope', 'kind', 'kit_id', 'licence_minor', 'support_required',
                              'minimum_packages', 'later_reference_design', 'delivery', 'facts'}:
                raise CommercialRevisionError('offer_fields')
            if (not isinstance(offer['id'], str) or not 1 <= len(offer['id']) <= 100 or offer['id'] in seen
                    or set(offer['scope']) != SCOPE or offer['kind'] not in ('development', 'ready-kit')
                    or (offer['kind'] == 'development' and offer['kit_id'] is not None)
                    or (offer['kind'] == 'ready-kit' and not isinstance(offer['kit_id'], str))):
                raise CommercialRevisionError('offer_policy_unavailable')
            seen.add(offer['id'])
            _fact_shape(offer['facts'])
        documents = value['documents']
        if (not isinstance(documents, dict) or not set(documents) <= {'general_terms', 'refund_policy', 'privacy_policy', 'ip_licence', 'support_terms'}
                or any(pin is not None and (not isinstance(pin, str) or len(pin) != 64 or any(c not in '0123456789abcdef' for c in pin)) for pin in documents.values())):
            raise CommercialRevisionError('document_policy_unavailable')
        detached=deepcopy(value)
    except CommercialRevisionError:
        raise
    except (TypeError, KeyError, ValueError, RecursionError, OverflowError) as exc:
        raise CommercialRevisionError('revision_unavailable') from exc
    return {'revision': revision, 'policy': detached, 'financial_confirmation': False, 'effects_authorized': False}


def _fact_shape(value):
    if (not isinstance(value, dict) or set(value) != FACTS
            or any(fact is not None and not isinstance(fact, str) for fact in value.values())):
        raise CommercialRevisionError('policy_fact_fields')


def _known(value):
    return isinstance(value, str) and bool(value.strip()) and value.strip().lower() not in {'pending', 'unknown', 'unapproved', 'tbd'}


def _facts(value):
    _fact_shape(value)
    if any(not _known(fact) for fact in value.values()):
        raise CommercialRevisionError('pending_commercial_policy')


def _support(policy):
    support = policy['support']
    if (type(support['unit_minor']) is not int or support['unit_minor'] < 1
            or type(support['seconds']) is not int or support['seconds'] != 36000
            or support['expires'] is not False):
        raise CommercialRevisionError('support_policy_unavailable')
    _facts(support['facts'])


def _documents(policy, required):
    if any(policy['documents'].get(key) is None for key in required):
        raise CommercialRevisionError('document_policy_unavailable')


def _offer(offer):
    if (type(offer['licence_minor']) is not int or offer['licence_minor'] < 1
            or type(offer['support_required']) is not bool or type(offer['minimum_packages']) is not int
            or not 0 <= offer['minimum_packages'] <= 1000000
            or offer['support_required'] != (offer['minimum_packages'] > 0)
            or type(offer['later_reference_design']) is not bool or not _known(offer['delivery'])):
        raise CommercialRevisionError('offer_policy_unavailable')
    _facts(offer['facts'])


def quote(consumed, configuration, offer_id, *, support_packages):
    """Exact licence scope and seller minima. Custom/unfinished boards stay eligible.

    The caller allocates purchased support once across the basket, as existing
    checkout.build does. This function never creates grants, payment or acceptance.
    """
    policy = consumed['policy']
    if (digest(policy) != consumed['revision'] or type(support_packages) is not int
            or not 0 <= support_packages <= 1000000):
        raise CommercialRevisionError('revision_or_quantity_mismatch')
    offer = next((item for item in policy['offers'] if item['id'] == offer_id), None)
    kits = [{'id': item['kit_id']} for item in policy['offers'] if item['kind'] == 'ready-kit']
    if not evaluate(configuration, kit_catalog=kits)['valid'] or 'platform' not in configuration:
        raise CommercialRevisionError('configuration_invalid')
    if configuration['support_packages'] != support_packages:
        raise CommercialRevisionError('support_allocation_mismatch')
    if configuration.get('production_band') == 'higher-volume':
        raise CommercialRevisionError('higher_volume_requires_quote')
    if offer is None or {key: configuration[key] for key in SCOPE} != offer['scope']:
        raise CommercialRevisionError('offer_scope_mismatch')
    _offer(offer)
    required = {'general_terms', 'refund_policy', 'privacy_policy', 'ip_licence'}
    if support_packages:
        _support(policy)
        required.add('support_terms')
    _documents(policy, required)
    platform = configuration['platform']
    if offer['kind'] == 'ready-kit' and (platform['choice'] != 'listed-kit' or platform['kit_id'] != offer['kit_id']):
        raise CommercialRevisionError('ready_design_not_applicable')
    if support_packages < offer['minimum_packages']:
        raise CommercialRevisionError('required_support_minimum')
    total = offer['licence_minor'] + (support_packages * policy['support']['unit_minor'] if support_packages else 0)
    if not 1 <= total <= 9223372036854775807:
        raise CommercialRevisionError('total_unavailable')
    return {'commercial_revision': consumed['revision'], 'catalog_revision': policy['catalog_revision'],
            'buyer_scope_revision': policy['buyer_scope_revision'], 'evidence_class': policy['evidence_class'],
            'configuration': deepcopy(configuration), 'offer': deepcopy(offer), 'documents': deepcopy(policy['documents']),
            'currency': policy['currency'], 'support_packages': support_packages,
            'support_seconds': support_packages * 36000, 'total_minor': total,
            'financial_confirmation': False, 'effects_authorized': False, 'activation_authorized': False}


def quote_support(consumed, *, quantity):
    """Support-only purchase requires no licence/platform questionnaire."""
    policy = consumed['policy']
    if (digest(policy) != consumed['revision'] or type(quantity) is not int or not 1 <= quantity <= 1000000):
        raise CommercialRevisionError('revision_or_quantity_mismatch')
    _support(policy)
    _documents(policy, {'general_terms', 'refund_policy', 'privacy_policy', 'support_terms'})
    total = quantity * policy['support']['unit_minor']
    if not 1 <= total <= 9223372036854775807:
        raise CommercialRevisionError('total_unavailable')
    return {'commercial_revision': consumed['revision'], 'evidence_class': policy['evidence_class'],
            'catalog_revision': policy['catalog_revision'], 'buyer_scope_revision': policy['buyer_scope_revision'],
            'product_id': policy['support']['product_id'], 'quantity': quantity, 'currency': policy['currency'],
            'total_minor': total, 'support_seconds': quantity * 36000, 'expires': False,
            'documents': deepcopy(policy['documents']), 'financial_confirmation': False,
            'effects_authorized': False, 'activation_authorized': False}


def fixture_revision(configuration, offer_id, *, buyer_scope_revision, documents_revision):
    """Bridge existing fixture policy into the same immutable consumer contract.

    This deliberately authenticates no commercial approval. It first uses the
    existing fixture policy validator; no customer-supplied rates/rights enter.
    Document pins identify the fixture definition, never approved legal bodies.
    """
    from .purchase_policy import FIXTURE_OFFERS, quote as fixture_quote
    result = fixture_quote(configuration, offer_id)
    if result['status'] != 'synthetic_purchasable':
        raise CommercialRevisionError('fixture_offer_unavailable')
    source = next(offer for offer in FIXTURE_OFFERS if offer.id == offer_id)
    facts = {key: 'local-synthetic-fixture:' + key for key in FACTS}
    value = {'schema': 1, 'evidence_class': 'local-synthetic', 'catalog_revision': CATALOG['revision'],
             'source_sha256': CATALOG['source_sha256'], 'buyer_scope_revision': buyer_scope_revision,
             'currency': 'EUR', 'support': {'product_id': CATALOG['support_product_id'],
                'unit_minor': source.support_minor, 'seconds': 36000, 'expires': False, 'facts': facts},
             'offers': [{'id': source.id, 'scope': {key: deepcopy(configuration[key]) for key in SCOPE},
                'kind': source.kind, 'kit_id': source.kit_id, 'licence_minor': source.licence_minor,
                'support_required': source.support_required, 'minimum_packages': source.minimum_packages,
                'later_reference_design': source.later_reference_design, 'delivery': source.delivery, 'facts': facts}],
             'documents': {key: documents_revision for key in
                ('general_terms', 'refund_policy', 'privacy_policy', 'ip_licence', 'support_terms')}}
    body = canonical(value)
    return consume(body, revision=hashlib.sha256(body).hexdigest(), catalog_revision=CATALOG['revision'],
                   buyer_scope_revision=buyer_scope_revision, synthetic=True)


def fixture_support_revision(*, buyer_scope_revision, documents_revision):
    """Existing fixture support rate, without an IP or platform prerequisite."""
    from .purchase_policy import FIXTURE_OFFERS
    rates = {offer.support_minor for offer in FIXTURE_OFFERS}
    if len(rates) != 1:
        raise CommercialRevisionError('fixture_support_unavailable')
    value = {'schema': 1, 'evidence_class': 'local-synthetic', 'catalog_revision': CATALOG['revision'],
             'source_sha256': CATALOG['source_sha256'], 'buyer_scope_revision': buyer_scope_revision,
             'currency': 'EUR', 'support': {'product_id': CATALOG['support_product_id'],
                'unit_minor': rates.pop(), 'seconds': 36000, 'expires': False,
                'facts': {key: 'local-synthetic-fixture:' + key for key in FACTS}}, 'offers': [],
             'documents': {key: documents_revision for key in
                ('general_terms', 'refund_policy', 'privacy_policy', 'ip_licence', 'support_terms')}}
    body = canonical(value)
    return consume(body, revision=hashlib.sha256(body).hexdigest(), catalog_revision=CATALOG['revision'],
                   buyer_scope_revision=buyer_scope_revision, synthetic=True)
