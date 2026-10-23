#!/usr/bin/env python3
"""Compile source declaration labels only; never fabricate approved policy bodies."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'docs/product-source/SLL_xSPI_MC_Product_Page.md'
OUTPUT = ROOT / 'backend/shop/catalog/document_preview.json'


def compile_preview():
    source = SOURCE.read_bytes()
    section = source.decode().split('### Before Placing Your Order\n', 1)[1].split('## Frequently Asked Questions', 1)[0]
    labels = re.findall(r'^- \[ \] \*\*(.+)\*\*$', section, re.MULTILINE)
    if len(labels) != 5:
        raise ValueError('Expected four declarations and one separate marketing choice')
    ids = ['business_authority', 'configuration_terms', 'refund_policy', 'configuration_accuracy']
    data = {'schema_version': 1, 'source_sha256': hashlib.sha256(source).hexdigest(),
            'ip_declarations': [{'id': identity, 'text': text} for identity, text in zip(ids, labels[:4])],
            'marketing': {'text': labels[4], 'required': False, 'selected': False},
            'documents': [{'id': identity, 'title': title, 'version': None, 'body': None, 'approved': False}
                          for identity, title in [('general_terms', 'Terms and Conditions'),
                          ('ip_licence', 'xSPI-MC IP Licence Agreement'),
                          ('refund_policy', 'Refund and Cancellation Policy'),
                          ('privacy_policy', 'Privacy Policy'),
                          ('support_terms', 'Engineering support terms')]]}
    data['revision'] = hashlib.sha256(json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
    return json.dumps(data, ensure_ascii=False, indent=2) + '\n'


if __name__ == '__main__':
    OUTPUT.write_text(compile_preview())
