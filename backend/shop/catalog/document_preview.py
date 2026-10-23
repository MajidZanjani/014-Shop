"""Current-source read-only prerequisites, never a frozen offer or acceptance."""
import hashlib
import json
from pathlib import Path
from .rules import CATALOG
from .cart_rules import evaluate_cart
from .business_scope import scope_metadata

DEFINITION = json.loads(Path(__file__).with_name('document_preview.json').read_text())


def preview(quotation):
    snapshot = quotation.snapshot
    data = {key: value for key, value in DEFINITION.items() if key != 'revision'}
    digest = hashlib.sha256(json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
    current_source = digest == DEFINITION['revision'] and DEFINITION['source_sha256'] == CATALOG['source_sha256']
    valid = snapshot.cart_id == quotation.cart_id and evaluate_cart(snapshot.lines)['valid'] and bool(snapshot.lines)
    kinds = {line['kind'] for line in snapshot.lines} if valid else set()
    profile = ('mixed' if len(kinds) == 2 else 'ip' if kinds == {'ip'} else 'support_only' if kinds == {'support'} else 'unavailable')
    available = current_source and valid
    required = {'general_terms', 'refund_policy', 'privacy_policy'}
    if 'ip' in kinds: required.add('ip_licence')
    if 'support' in kinds: required.add('support_terms')
    return {'quotation_id': str(quotation.id), 'cart_version': snapshot.version,
            'catalog_revision': snapshot.catalog_revision, 'current_catalog': snapshot.catalog_revision == CATALOG['revision'],
            'business_scope': scope_metadata(quotation), 'profile': profile if available else 'unavailable',
            'state': 'preview_only' if available else 'unavailable',
            'definition_revision': DEFINITION['revision'], 'source_sha256': DEFINITION['source_sha256'],
            'ip_declarations': DEFINITION['ip_declarations'] if available and 'ip' in kinds else [],
            'documents': [row for row in DEFINITION['documents'] if available and row['id'] in required],
            'marketing': DEFINITION['marketing'] if available else None,
            'support_confirmation': 'Owner and positive package quantity require confirmation under approved support terms.' if available and 'support' in kinds else None,
            'lines': snapshot.lines if available else [],
            'country_tax_choices': 'pending', 'acceptance_enabled': False, 'checkout_enabled': False}
