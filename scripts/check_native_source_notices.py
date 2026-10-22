#!/usr/bin/env python3
"""Retain upstream notice candidates from two exact cached native sources."""
import argparse
import io
import json
from pathlib import Path, PurePosixPath
import tarfile
import time
import unittest
import check_native_closure as native
from audit_licence_gaps import candidate
from check_python import require

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    'python3': ('3.13.16', 'f4b1bfb3c79b5bb11b8d228a12504163b4c0dab4d679828d8f5f26b6cb6ab35d', 'Python-3.13.16/LICENSE'),
    'postgresql': ('18.6', '555610c24d53e4316da5b7d3fc25c279d96856d5e0e23ee308c328c5fa881d9f', 'postgresql-18.6/COPYRIGHT'),
}
MAX_ARCHIVE = 64 * 1024 * 1024
MAX_TOTAL = 1024 * 1024 * 1024
MAX_NOTICE = 10 * 1024 * 1024
MAX_MEMBERS = 100000


def select_sources(report):
    selected = {}
    for output, node in report['nodes'].items():
        recipe = node.get('recipe') or {}
        name = recipe.get('declared_pname')
        if name in EXPECTED:
            require(name not in selected, 'unique exact source component required')
            version, digest, required = EXPECTED[name]
            require(recipe['declared_version'] == version and output in recipe['outputs'].values(), 'source/output version binding required')
            native.store_path(recipe['source_store_path'])
            selected[name] = {'output': output, 'source': recipe['source_store_path'], 'version': version,
                              'sha256': digest, 'required_notice': required, 'derivation_sha256': node['derivation_sha256']}
    require(set(selected) == set(EXPECTED), 'both exact cached native sources required')
    return selected


def scan(data, expected_digest, required_notice):
    require(0 < len(data) <= MAX_ARCHIVE and native.sha256(data) == expected_digest, 'exact bounded upstream archive required')
    names, notices = set(), {}
    total, links = 0, 0
    with tarfile.open(fileobj=io.BytesIO(data), mode='r|*') as archive:
        for member in archive:
            name = member.name
            path = PurePosixPath(name)
            require(name and not path.is_absolute() and '..' not in path.parts and '\\' not in name
                    and all(ord(c) >= 32 and ord(c) != 127 for c in name), 'unsafe source member')
            require(str(path) not in names, 'duplicate source member')
            names.add(str(path))
            require(len(names) <= MAX_MEMBERS and 0 <= member.size <= MAX_TOTAL, 'source member bound exceeded')
            total += member.size
            require(total <= MAX_TOTAL, 'source expanded bound exceeded')
            if member.issym() or member.islnk():
                links += 1
            if candidate(name) and not member.isdir():
                require(member.isfile() and member.size <= MAX_NOTICE, 'regular bounded source notice required')
                with archive.extractfile(member) as stream:
                    content = stream.read(MAX_NOTICE + 1)
                require(len(content) == member.size and bool(content), 'exact nonempty source notice required')
                notices[name] = content
    require(required_notice in notices, 'required top-level source notice absent')
    return notices, {'members_scanned': len(names), 'declared_expanded_bytes': total, 'links_not_followed': links}


def collect():
    observed = native.collect()
    encoded = (json.dumps(observed, indent=2, sort_keys=True) + '\n').encode()
    baseline = ROOT / 'docs/evidence/t02/operator-native-closure.json'
    retained = native.evidence_path(baseline, encoded)
    require(retained.read_bytes() == encoded, 'current retained native observation required')
    sources = select_sources(observed)
    findings, payloads = [], {}
    for name, source in sorted(sources.items()):
        path = Path(source['source'])
        require(path.is_file() and not path.is_symlink() and path.stat().st_size <= MAX_ARCHIVE, 'existing bounded cached source archive required')
        with path.open('rb') as stream:
            data = stream.read(MAX_ARCHIVE + 1)
        notices, counts = scan(data, source['sha256'], source['required_notice'])
        texts = []
        for member, content in sorted(notices.items()):
            digest = native.sha256(content)
            payloads[digest] = content
            texts.append({'archive_member': member, 'size': len(content), 'sha256': digest,
                          'retained_path': 'native-source-notice-texts/' + digest + '.txt'})
        findings.append({'name': name, **source, **counts, 'notice_candidates': texts,
                         'status': 'upstream-source-candidates-only-output-and-legal-review-pending'})
    return {'schema_version': 1, 'evidence_class': 'cached-exact-upstream-source-notices',
            'native_evidence_path': str(retained.relative_to(ROOT)), 'native_evidence_sha256': native.sha256(encoded),
            'inventory_complete': False, 'legal_approval': False, 'output_notice_incorporation_confirmed': False,
            'source_offer_obligations_satisfied': False, 'findings': findings}, payloads


def main():
    start = time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    report, payloads = collect()
    encoded = (json.dumps(report, indent=2, sort_keys=True) + '\n').encode()
    directory = ROOT / 'docs/evidence/t02'
    output, text_dir = directory / 'native-source-notices.json', directory / 'native-source-notice-texts'
    if args.write:
        require(not output.exists() and not text_dir.exists(), 'existing source evidence denied')
        text_dir.mkdir()
        for digest, content in sorted(payloads.items()):
            with (text_dir / (digest + '.txt')).open('xb') as stream:
                stream.write(content)
        with output.open('xb') as stream:
            stream.write(encoded)
    else:
        require(output.read_bytes() == encoded, 'source notice report mismatch')
        require({p.name for p in text_dir.iterdir()} == {d + '.txt' for d in payloads}, 'exact source text set required')
        for digest, content in payloads.items():
            require((text_dir / (digest + '.txt')).read_bytes() == content, 'source notice bytes mismatch')
    suite = unittest.defaultTestLoader.discover(str(ROOT / 'tests'), pattern='test_native_source_notices.py')
    stream = io.StringIO(); result = unittest.TextTestRunner(stream=stream).run(suite)
    require(result.testsRun >= 6 and result.wasSuccessful() and not result.skipped, 'source notice controls failed: ' + stream.getvalue())
    count = sum(len(f['notice_candidates']) for f in report['findings'])
    print(f'NATIVE_SOURCE_NOTICES_PASS checks={count} tests={result.testsRun} duration_seconds={time.monotonic()-start:.3f}')
    print('Two cached exact upstream sources only; output incorporation/native/legal/OCI/full inventory pending')


if __name__ == '__main__':
    main()
