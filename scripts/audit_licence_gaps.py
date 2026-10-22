#!/usr/bin/env python3
"""Audit exact retained missing-text distributions without extracting or executing them."""
import argparse
import base64
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import tarfile
import urllib.parse
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
MAX_ARCHIVE = 64 * 1024 * 1024
MAX_TOTAL = 256 * 1024 * 1024
MAX_TEXT = 10 * 1024 * 1024
MAX_MEMBERS = 20000
GROUPS = ('npm', 'python_runtime', 'python_tools')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def targets(value):
    result = []
    for group in GROUPS:
        for record in value[group]:
            if not record['licence_texts']:
                result.append((group, record))
    identities = [(g, r['name'], r['version']) for g, r in result]
    require(len(identities) == len(set(identities)) and bool(result), 'duplicate or empty gap identities')
    return result


def artifact_url(url, group):
    parts = urllib.parse.urlsplit(url)
    host = 'registry.npmjs.org' if group == 'npm' else 'files.pythonhosted.org'
    require(parts.scheme == 'https' and parts.netloc == host and not parts.query and not parts.fragment,
            'official distribution HTTPS URL required')
    return url


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('distribution redirect denied')


def fetch(url, group):
    # No proxy credentials, redirects or user configuration enter this request.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    with opener.open(artifact_url(url, group), timeout=30) as response:
        data = response.read(MAX_ARCHIVE + 1)
    require(len(data) <= MAX_ARCHIVE, 'archive byte bound exceeded')
    return data


def verify(data, expected):
    require(len(data) <= MAX_ARCHIVE, 'archive byte bound exceeded')
    if expected.startswith('sha256:'):
        require(re.fullmatch(r'sha256:[0-9a-f]{64}', expected), 'malformed SHA256')
        actual = 'sha256:' + sha256(data)
    else:
        algorithm, encoded = expected.split('-', 1)
        require(algorithm in {'sha256', 'sha384', 'sha512'}, 'unsupported distribution digest')
        decoded = base64.b64decode(encoded, validate=True)
        require(len(decoded) == hashlib.new(algorithm).digest_size, 'malformed SRI digest')
        actual = algorithm + '-' + base64.b64encode(hashlib.new(algorithm, data).digest()).decode()
    require(actual == expected, 'distribution digest mismatch')


def candidate(name):
    # Includes established collector names plus names such as COPYRIGHT and LICENSES.txt.
    return bool(re.match(r'(?i)^(licen[cs]es?|copying|copyright|notice)([._-].*)?$', PurePosixPath(name).name))


def inspect_archive(data, group):
    members = []
    found = {}
    total = 0
    names = set()

    def add(name, size, kind, read):
        nonlocal total
        path = PurePosixPath(name)
        require(name and not path.is_absolute() and '..' not in path.parts and '\\' not in name
                and all(ord(c) >= 32 and ord(c) != 127 for c in name), 'unsafe archive member')
        canonical = str(path)
        require(canonical not in names, 'duplicate archive member')
        names.add(canonical)
        require(len(names) <= MAX_MEMBERS and 0 <= size <= MAX_TOTAL, 'archive member bound exceeded')
        require(kind in {'file', 'directory'}, 'archive links/special members denied')
        total += size
        require(total <= MAX_TOTAL, 'expanded archive bound exceeded')
        members.append({'path': name, 'size': size, 'kind': kind})
        if kind == 'file' and candidate(name):
            require(size <= MAX_TEXT, 'notice byte bound exceeded')
            content = read(MAX_TEXT + 1)
            require(len(content) == size and bool(content), 'invalid notice length')
            found[name] = content

    if group == 'npm':
        with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as archive:
            for member in archive:
                kind = 'file' if member.isfile() else 'directory' if member.isdir() else 'special'
                def read(limit, member=member):
                    with archive.extractfile(member) as stream:
                        return stream.read(limit)
                add(member.name, member.size, kind, read)
    else:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            for member in archive.infolist():
                mode = member.external_attr >> 16
                kind = 'directory' if member.is_dir() else 'special' if mode & 0o170000 not in {0, 0o100000} else 'file'
                def read(limit, member=member):
                    with archive.open(member) as stream:
                        return stream.read(limit)
                add(member.filename, member.file_size, kind, read)
    require(bool(members), 'empty archive')
    return sorted(members, key=lambda x: x['path']), found


def audit(source, loader=fetch):
    findings = []
    payloads = {}
    for group, record in targets(json.loads(source)):
        data = loader(record['artifact_url'], group)
        verify(data, record['artifact_hash'])
        members, found = inspect_archive(data, group)
        texts = []
        for name, content in sorted(found.items()):
            digest = sha256(content)
            payloads[digest] = content
            texts.append({'archive_path': name, 'sha256': digest, 'size': len(content),
                          'retained_path': 'licence-gap-texts/' + digest + '.txt'})
        findings.append({'group': group, 'name': record['name'], 'version': record['version'],
                         'artifact_url': record['artifact_url'], 'artifact_hash': record['artifact_hash'],
                         'observed_archive_sha256': sha256(data), 'archive_members': members,
                         'candidate_notice_texts': texts,
                         'status': 'candidate-text-found-review-pending' if texts else 'no-named-notice-found-review-pending'})
    return {'schema_version': 1, 'evidence_class': 'exact-distribution-archive-audit',
            'source_licences_sha256': sha256(source), 'distributions_checked': len(findings),
            'inventory_complete': False, 'legal_approval': False,
            'scope': 'Named notice candidates in exact retained missing-text distribution archives; no source fallback, binary scan, install or native closure proof',
            'findings': findings}, payloads


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true', help='exclusively create new audit evidence')
    args = parser.parse_args()
    directory = ROOT / 'docs/evidence/t02'
    report, payloads = audit((directory / 'licences.json').read_bytes())
    encoded = (json.dumps(report, indent=2) + '\n').encode()
    output = directory / 'licence-gap-audit.json'
    text_dir = directory / 'licence-gap-texts'
    if args.write:
        require(not output.exists() and not text_dir.exists(), 'existing audit evidence denied')
        if payloads:
            text_dir.mkdir()
        for digest, content in sorted(payloads.items()):
            with (text_dir / (digest + '.txt')).open('xb') as stream:
                stream.write(content)
        with output.open('xb') as stream:
            stream.write(encoded)
    else:
        require(output.read_bytes() == encoded, 'retained audit mismatch')
        retained = {p.name for p in text_dir.iterdir()} if text_dir.exists() else set()
        require(retained == {d + '.txt' for d in payloads}, 'retained text set mismatch')
        for digest, content in payloads.items():
            require((text_dir / (digest + '.txt')).read_bytes() == content, 'retained text mismatch')
    found = sum(bool(x['candidate_notice_texts']) for x in report['findings'])
    print(f'LICENCE_GAP_AUDIT_PASS distributions={len(report["findings"])} with_named_text={found} without_named_text={len(report["findings"])-found}; full_inventory_pending=true')


if __name__ == '__main__':
    main()
