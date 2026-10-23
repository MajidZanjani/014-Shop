"""Read-only missing-input assessment. Never a live approval/gating engine."""
from shop.catalog.business_scope import current_scope, valid_business
from shop.catalog.business_rules import PENDING
from shop.catalog.business_views import LABELS as BUSINESS_LABELS
from shop.catalog.document_preview import preview
from shop.catalog.models import QuotationReview
from shop.catalog.quotation_status import LABELS
from .quotation_review import snapshot_digest

APPROVAL_LABELS = {
    'prices': 'Approved component prices', 'rights': 'Approved permitted-use rights',
    'access': 'Approved licence access rules', 'coverage': 'Approved maintenance/update/support coverage',
    'terms': 'Approved applicable terms', 'recurrence': 'Approved recurrence and renewal basis',
    'production_accounting': 'Approved production accounting rules',
}


def assess(quotation):
    documents = preview(quotation)
    scope = current_scope(quotation)
    business_valid = bool(scope and valid_business(scope.business_snapshot, quotation.cart.owner_id))
    business = {'state': 'partial' if business_valid else 'unavailable' if quotation.business_version else 'missing',
                'scope_version': quotation.business_version,
                'draft_version': scope.business_snapshot.version if business_valid else None,
                'missing_required': [], 'licensed_entity_review_required': None}
    if business_valid:
        evaluation = scope.business_snapshot.evaluation
        business['missing_required'] = [{'field': field, 'label': BUSINESS_LABELS[field]}
                                        for field in evaluation['missing_required'] if field not in PENDING]
        business['licensed_entity_review_required'] = evaluation['licensed_entity_review_required']
    record = QuotationReview.objects.only('version', 'business_version', 'decision', 'snapshot_digest').filter(quotation=quotation, version=quotation.review_version).first() if quotation.review_version else None
    review_code = 'awaiting_review'
    if quotation.review_version and record is None:
        review_code = 'unavailable'
    elif record and record.business_version == quotation.business_version:
        if quotation.business_version and not business_valid:
            review_code = 'unavailable'
        elif record.snapshot_digest != snapshot_digest(quotation):
            review_code = 'scope_mismatch'
        elif record.decision in {'needs_information', 'ready_for_commercial_review', 'declined'}:
            review_code = record.decision
        else:
            review_code = 'unavailable'
    review = {'code': review_code, 'label': LABELS.get(review_code, 'Review scope evidence mismatch'),
              'version': record.version if record else None}
    blockers = []
    def block(code, label, state='pending'):
        blockers.append({'code': code, 'label': label, 'state': state})
    if documents['state'] != 'preview_only': block('captured_scope', 'Captured scope or document source requires review', 'unavailable')
    if not documents['current_catalog']: block('catalog_revision', 'Captured catalog is not current', 'unavailable')
    if review_code != 'ready_for_commercial_review': block('internal_review', review['label'], 'not_ready')
    block('business_details', 'Saved business details require completion and applicable review', business['state'])
    block('country_tax', 'Country/tax choices deferred to a later step', 'deferred')
    if business['licensed_entity_review_required']:
        block('licensed_entity', 'Differing licensed entity requires an approved review rule')
    lines = []
    for line in documents['lines']:
        ip = line['kind'] == 'ip'
        keys = list(APPROVAL_LABELS) if ip else ['prices', 'terms']
        item = {'line_id': line['id'], 'kind': line['kind'], 'quantity': line['quantity'],
                'inputs': [{'code': key, 'label': APPROVAL_LABELS[key], 'state': 'pending', 'value': None} for key in keys]}
        if ip:
            item.update(vendor=line['configuration']['vendor'], term=line['configuration']['term'],
                        host_binding='pending', rights=None)
            if line['configuration']['production_band'] == 'higher-volume':
                item['quotation_required'] = True
        lines.append(item)
    if any(line['kind'] == 'ip' for line in lines): block('host_binding', 'Protected host binding and actual vendor access validation remain pending')
    block('commercial_inputs', 'Approved per-line commercial inputs and totals are unavailable')
    block('documents', 'Applicable document text and versions require approval')
    block('offer_deadlines', 'Separate quote-validity and payment deadlines require approved definitions')
    block('protected_approval', 'Protected offer approval and publication workflow is not implemented')
    return {'quotation_id': str(quotation.id), 'cart_version': quotation.snapshot.version,
            'catalog_revision': quotation.snapshot.catalog_revision,
            'business': business, 'latest_review_version': quotation.review_version, 'review': review,
            'profile': documents['profile'], 'definition_revision': documents['definition_revision'],
            'document_requirements': [{'id': row['id'], 'title': row['title'], 'version': None, 'state': 'pending'} for row in documents['documents']],
            'lines': lines, 'blockers': blockers, 'state': 'blocked',
            'country_tax_choices': 'deferred', 'quote_valid_until': None, 'payment_due_at': None,
            'money': {'currency': 'EUR', 'currency_status': 'draft', 'subtotal_minor': None, 'tax_minor': None, 'total_minor': None},
            'offer_creation_enabled': False, 'publication_enabled': False, 'acceptance_enabled': False, 'checkout_enabled': False}
