#!/usr/bin/env python3
"""Retain reviewed-path embedded licence candidates from exact verified wheels."""
import argparse
import io
import json
from pathlib import Path
import zipfile
from audit_licence_gaps import ROOT, targets, fetch, verify, inspect_archive, require, sha256

SELECTED = {
    ('pip-requirements-parser', '32.0.1'): 'pip_requirements_parser.py',
    ('packageurl-python', '0.17.6'): 'packageurl/__init__.py',
}
LIMIT = 16384


def header(data):
    """Return exact leading blank/comment bytes, with no decommenting or rewriting."""
    lines = []
    for line in data.splitlines(keepends=True):
        if not line.strip() or line.startswith(b'#'):
            lines.append(line)
        else:
            break
        require(sum(map(len, lines)) <= LIMIT, 'leading comment bound exceeded')
    result = b''.join(lines)
    comments = [line.lstrip(b'#').strip().lower() for line in result.splitlines()]
    require(any(line.startswith(b'copyright ') and len(line) > len(b'copyright ') for line in comments),
            'copyright holder line absent')
    compact = b' '.join(comments)
    for marker in (b'copyright', b'spdx-license-identifier: mit',
                   b'permission is hereby granted, free of charge',
                   b'the above copyright notice and this permission notice',
                   b'included in all copies or substantial portions',
                   b'the software is provided "as is"',
                   b'without warranty of any kind',
                   b'out of or in connection with the software',
                   b'use or other dealings in the software.'):
        require(marker in compact, 'complete expected header marker absent')
    return result


def collect(source, loader=fetch):
    records = {(r['name'], r['version']): r for g, r in targets(json.loads(source)) if g == 'python_tools'}
    require(set(records) == set(SELECTED), 'exact Python tool gap identities required')
    findings, texts = [], {}
    for identity, member in SELECTED.items():
        record = records[identity]
        data = loader(record['artifact_url'], 'python_tools')
        verify(data, record['artifact_hash'])
        inspect_archive(data, 'python_tools')  # shared complete member/path/link/size validation
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            info = archive.getinfo(member)
            require(info.file_size <= 1024 * 1024, 'source member byte bound exceeded')
            with archive.open(info) as stream:
                content = stream.read(1024 * 1024 + 1)
            require(len(content) == info.file_size, 'source member length mismatch')
        retained = header(content)
        digest = sha256(retained)
        texts[digest] = retained
        findings.append({'name': identity[0], 'version': identity[1], 'artifact_url': record['artifact_url'],
                         'artifact_hash': record['artifact_hash'], 'observed_archive_sha256': sha256(data),
                         'archive_member': member, 'member_sha256': sha256(content),
                         'byte_start': 0, 'byte_end_exclusive': len(retained), 'text_sha256': digest,
                         'retained_path': 'embedded-licence-texts/' + digest + '.txt',
                         'status': 'embedded-MIT-header-observed-review-pending'})
    return {'schema_version': 1, 'source_licences_sha256': sha256(source),
            'evidence_class': 'exact-distribution-embedded-source-headers',
            'inventory_complete': False, 'legal_approval': False, 'package_wide_notice_review_complete': False,
            'scope': 'Two explicitly selected Python module leading comments; original twelve named-file findings unchanged',
            'findings': findings}, texts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    directory = ROOT / 'docs/evidence/t02'
    report, texts = collect((directory / 'licences.json').read_bytes())
    encoded = (json.dumps(report, indent=2) + '\n').encode()
    output = directory / 'embedded-licences.json'
    text_dir = directory / 'embedded-licence-texts'
    if args.write:
        require(not output.exists() and not text_dir.exists(), 'existing embedded evidence denied')
        text_dir.mkdir()
        for digest, content in texts.items():
            with (text_dir / (digest + '.txt')).open('xb') as stream:
                stream.write(content)
        with output.open('xb') as stream:
            stream.write(encoded)
    else:
        require(output.read_bytes() == encoded, 'embedded report mismatch')
        require({p.name for p in text_dir.iterdir()} == {d + '.txt' for d in texts}, 'embedded text set mismatch')
        for digest, content in texts.items():
            require((text_dir / (digest + '.txt')).read_bytes() == content, 'embedded text mismatch')
    print(f'EMBEDDED_LICENCE_EVIDENCE_PASS distributions={len(report["findings"])}; legal_and_full_inventory_pending=true')


if __name__ == '__main__':
    main()
