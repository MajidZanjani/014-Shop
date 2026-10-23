"""Fixed delta categories only: no arbitrary values, paths or business diffs."""
import json

CATEGORIES = (
    ('captured_scope', 'Captured request and cart revision'),
    ('business', 'Attached business revision and completeness'),
    ('review', 'Internal review revision and outcome'),
    ('source', 'Catalog/document source identity and availability'),
    ('documents', 'Applicable document prerequisites'),
    ('line_inputs', 'Per-line commercial prerequisites'),
    ('blockers', 'Remaining preparation blockers'),
    ('money_deadlines', 'Money and deadline prerequisites'),
)


def fields(value, names):
    # Missing keys stay missing. None/zero/false/empty are never coalesced.
    return {name: value[name] for name in names if name in value}


def projections(value):
    blockers = value.get('blockers', [])
    return {
        'captured_scope': fields(value, ('quotation_id', 'cart_version', 'profile')),
        'business': fields(value, ('business', 'country_tax_choices')),
        'review': fields(value, ('latest_review_version', 'review')),
        'source': {**fields(value, ('catalog_revision', 'definition_revision')),
                   'catalog_current': not any(row['code'] == 'catalog_revision' for row in blockers),
                   'source_available': value.get('profile') != 'unavailable'},
        'documents': fields(value, ('document_requirements',)),
        'line_inputs': fields(value, ('lines',)),
        'blockers': fields(value, ('blockers',)),
        'money_deadlines': fields(value, ('money', 'quote_valid_until', 'payment_due_at')),
    }


def compare(retained, current):
    before, after = projections(retained), projections(current)
    def encoded(value):
        return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True)
    rows = [{'code': code, 'label': label, 'changed': encoded(before[code]) != encoded(after[code])}
            for code, label in CATEGORIES]
    available = (current.get('profile') != 'unavailable' and current.get('business', {}).get('state') != 'unavailable'
                 and current.get('review', {}).get('code') not in {'unavailable', 'scope_mismatch'})
    count = sum(row['changed'] for row in rows)
    return {'categories': rows, 'changed_categories': count, 'current_assessment_available': available,
            'state': 'current_unavailable' if not available else 'differences_found' if count else 'no_differences',
            'country_tax_choices': 'deferred', 'offer_creation_enabled': False,
            'publication_enabled': False, 'acceptance_enabled': False, 'checkout_enabled': False}
