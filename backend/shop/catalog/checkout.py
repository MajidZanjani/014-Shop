"""Complete-cart local rehearsal. Pending legal/tax/host facts never become acceptance."""
from copy import deepcopy
import hashlib
import json
import uuid
from django.db import transaction
from shop.payments.purchase_demo import owner_locked
from shop.payments import synthetic_bank
from shop.adapters.evidence_archive import PreparedArchive, manifest
from . import business_rules,commercial_revisions
from .business_scope import valid_business
from .cart_rules import evaluate_cart
from .document_preview import DEFINITION
from .models import DraftCart, CartSnapshot, BusinessDraft, BusinessDraftSnapshot, SyntheticCheckout, SyntheticCheckoutKey
from .purchase_policy import quote, FIXTURE_OFFERS
from .rules import CATALOG


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


class CheckoutError(ValueError):
    def __init__(self, code, status=409, fields=None):
        super().__init__(code)
        self.status = status
        self.fields = fields or []


def build(cart, business):
    """Quote every line or hold every line. Only purchased support in this basket is allocated."""
    errors = []
    if cart.catalog_revision != CATALOG['revision'] or not cart.lines or not evaluate_cart(cart.lines)['valid']:
        errors.append('cart_requires_review')
    if not valid_business(business, cart.cart.owner_id):
        errors.append('business_requires_review')
    missing = business_rules.evaluate_details(business.details)['missing_required']
    if any(field not in business_rules.PENDING for field in missing):
        errors.append('business_details_required')
    if business.details.get('licensed_entity') != business.details.get('legal_business_name'):
        errors.append('licensed_entity_requires_review')
    definition = deepcopy(DEFINITION)
    if (digest({k: v for k, v in definition.items() if k != 'revision'}) != definition['revision']
            or definition['source_sha256'] != CATALOG['source_sha256']):
        errors.append('document_source_requires_review')
    priced = []
    buyer_pin=digest({'id':business.pk,'version':business.version,'schema_version':business.schema_version,
                      'source_sha256':business.source_sha256,'details':business.details})
    support = sum(line['quantity'] for line in cart.lines if line.get('kind') == 'support') if not errors else 0
    allocated = 0
    total = 0
    support_policy=None
    if not errors:
        for line in cart.lines:
            if line['kind'] == 'support':
                try:
                    support_policy=commercial_revisions.fixture_support_revision(buyer_scope_revision=buyer_pin,documents_revision=definition['revision'])
                    support_snapshot=commercial_revisions.quote_support(support_policy,quantity=line['quantity'])
                except commercial_revisions.CommercialRevisionError:
                    errors.append('commercial_revision_requires_review');continue
                total+=support_snapshot['total_minor']
                priced.append({'line_id':line['id'],'kind':'support','quantity':line['quantity'],
                               'scope':CATALOG['product_id'],'total_minor':support_snapshot['total_minor'],
                               'commercial_policy':support_snapshot})
                continue
            configuration = deepcopy(line['configuration'])
            platform = configuration.get('platform') or {}
            offer = 'synthetic-ready-kit' if platform.get('choice') == 'listed-kit' else 'synthetic-development'
            policy = next((row for row in FIXTURE_OFFERS if row.id == offer), None)
            packages = policy.minimum_packages if policy and type(policy.minimum_packages) is int and policy.minimum_packages >= 0 else 0
            configuration['support_packages'] = packages
            result = quote(configuration, offer)
            if result['status'] != 'synthetic_purchasable':
                errors.append('line_requires_review')
                continue
            try:
                consumed=commercial_revisions.fixture_revision(configuration,offer,buyer_scope_revision=buyer_pin,documents_revision=definition['revision'])
                policy_snapshot=commercial_revisions.quote(consumed,configuration,offer,support_packages=packages)
            except commercial_revisions.CommercialRevisionError:
                errors.append('commercial_revision_requires_review');continue
            allocated += packages
            licence_minor=policy_snapshot['offer']['licence_minor']
            total += licence_minor
            priced.append({'line_id': line['id'], 'kind': 'ip', 'offer': result['snapshot'],
                           'allocated_purchased_packages': packages, 'commercial_policy':policy_snapshot,
                           'total_minor': licence_minor})
    if allocated > support:
        errors.append('required_support_minimum')
    if not 1 <= total <= 9223372036854775807:
        errors.append('total_unavailable')
    if errors:
        raise CheckoutError(errors[0], 422, fields=[field for field in missing if field not in business_rules.PENDING] if errors[0] == 'business_details_required' else [])
    kinds = {line['kind'] for line in cart.lines}
    required = {'general_terms', 'refund_policy', 'privacy_policy'}
    if 'ip' in kinds: required.add('ip_licence')
    if support: required.add('support_terms')
    return {'schema': 1, 'evidence_class': 'local-synthetic', 'financial_confirmation': False,
            'effects_authorized': False, 'acceptance_enabled': False, 'checkout_enabled': False,
            'cart': {'id': str(cart.cart_id), 'version': cart.version, 'catalog_revision': cart.catalog_revision,
                     'lines': deepcopy(cart.lines)},
            'business': {'id': business.pk, 'version': business.version, 'schema_version': business.schema_version,
                         'source_sha256': business.source_sha256, 'details': deepcopy(business.details)},
            'documents': definition, 'required_document_ids': sorted(required), 'priced_lines': priced, 'currency': 'EUR', 'total_minor': total,
            'support_packages': support, 'allocated_purchased_packages': allocated,
            'unallocated_purchased_packages': support - allocated,
            'pending': ['actual_commercial_approval', 'country_tax_applicability', 'approved_terms',
                        'applicable_host_bindings', 'actual_acceptance_payment_and_delivery']}


def current(owner):
    synthetic_bank.guard()
    cart = DraftCart.objects.filter(owner=owner).first()
    business = BusinessDraft.objects.filter(owner=owner).first()
    saved = CartSnapshot.objects.select_related('cart').filter(cart=cart, version=cart.version).first() if cart else None
    details = BusinessDraftSnapshot.objects.select_related('draft').filter(draft=business, version=business.version).first() if business else None
    if saved is None or details is None:
        raise CheckoutError('saved_cart_and_business_required', 422)
    value = build(saved, details)
    return value, digest(value)


def capture(owner, request_id, expected_digest):
    """Freeze reviewed bytes once. No order, acceptance, bank operation or entitlement."""
    synthetic_bank.guard()
    if type(request_id) is not uuid.UUID or not isinstance(expected_digest, str) or len(expected_digest) != 64:
        raise CheckoutError('invalid_request', 400)
    with transaction.atomic(durable=True):
        owner_locked(owner)
        key = SyntheticCheckoutKey.objects.select_related('checkout').filter(owner=owner, request_id=request_id).first()
        old = key.checkout if key else None
        if old:
            if old.sha256 != expected_digest:
                raise CheckoutError('request_conflict')
            return old, False
        cart = DraftCart.objects.select_for_update().filter(owner=owner).first()
        business = BusinessDraft.objects.select_for_update().filter(owner=owner).first()
        if cart is None or business is None:
            raise CheckoutError('saved_cart_and_business_required', 422)
        saved = CartSnapshot.objects.select_for_update().select_related('cart').filter(cart=cart, version=cart.version).first()
        details = BusinessDraftSnapshot.objects.select_for_update().select_related('draft').filter(draft=business, version=business.version).first()
        if saved is None or details is None:
            raise CheckoutError('saved_cart_and_business_required', 422)
        value = build(saved, details)
        if digest(value) != expected_digest:
            raise CheckoutError('checkout_changed')
        # The locked owner serializes different retry keys for the same reviewed snapshot.
        row, created = SyntheticCheckout.objects.get_or_create(owner=owner, sha256=expected_digest,
            defaults={'request_id': request_id, 'cart_snapshot': saved, 'business_snapshot': details, 'snapshot': value})
        SyntheticCheckoutKey.objects.create(owner=owner, request_id=request_id, checkout=row)
        return row, created


def archive_capture(identity, owner, archive, *, customer_request=None):
    """Retain exact private checkout bytes before any future simulated dispatch integration."""
    synthetic_bank.guard()
    if type(archive) is not PreparedArchive:
        raise CheckoutError('local_archive_required')
    from .checkout_payment import locked
    with transaction.atomic(durable=True):
        row=locked(owner,identity,customer_request=customer_request)
        value = canonical(row.snapshot)
        if hashlib.sha256(value).hexdigest() != row.sha256: raise CheckoutError('snapshot_mismatch')
    receipt = archive.publish(row.pk, value)
    if archive.recover(receipt) != value: raise CheckoutError('archive_mismatch')
    with transaction.atomic(durable=True):
        row=locked(owner,identity,customer_request=customer_request)
        if canonical(row.snapshot) != value: raise CheckoutError('snapshot_mismatch')
        row.archive_receipt = manifest(receipt)
        row.save(update_fields=['archive_receipt'])
    return row
