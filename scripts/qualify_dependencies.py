"""Inert artifact review: never extract, import, install or execute downloads."""
import argparse
import base64
import datetime
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import sys
import tarfile
import unittest
import urllib.parse
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / 'docs/build/dependency-candidates.json'
REVIEW = ROOT / 'docs/evidence/t02/dependency-review.json'
MARKDOWN = REVIEW.with_suffix('.md')
HOSTS = {'registry.npmjs.org', 'pypi.org', 'files.pythonhosted.org', 'nodejs.org',
         'www.python.org', 'ftp.postgresql.org', 'www.postgresql.org', 'github.com',
         'docs.astro.build', 'react.dev', 'docs.djangoproject.com', 'gunicorn.org',
         'www.psycopg.org', 'pip.pypa.io', 'pip-tools.readthedocs.io',
         'python-jsonschema.readthedocs.io', 'cyclonedx-bom-tool.readthedocs.io',
         'www.typescriptlang.org', 'www.djangoproject.com'}
UPSTREAMS = dict(zip(
    ['astro', '@astrojs/react', '@astrojs/check', 'react', 'react-dom', 'typescript',
     '@types/react', '@types/react-dom', 'npm', 'Django', 'gunicorn', 'psycopg',
     'pip', 'pip-tools', 'jsonschema', 'cyclonedx-bom', 'node', 'python', 'postgresql', 'libpq'],
    ['withastro/astro', 'withastro/astro', 'withastro/astro', 'react/react', 'react/react',
     'microsoft/TypeScript', 'DefinitelyTyped/DefinitelyTyped', 'DefinitelyTyped/DefinitelyTyped',
     'npm/cli', 'django/django', 'benoitc/gunicorn', 'psycopg/psycopg', 'pypa/pip',
     'jazzband/pip-tools', 'python-jsonschema/jsonschema', 'CycloneDX/cyclonedx-python',
     'nodejs/node', 'python/cpython', 'postgres/postgres', 'postgres/postgres']))


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()


def safe_url(url):
    p = urllib.parse.urlsplit(url)
    require(p.scheme == 'https' and p.hostname in HOSTS and not p.username
            and not p.password and p.port in (None, 443), 'untrusted HTTPS URL')
    return url


class Redirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        safe_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch(url):
    req = urllib.request.Request(safe_url(url), headers={'User-Agent': 'xspi-inert-review/1'})
    with urllib.request.build_opener(Redirects()).open(req, timeout=45) as response:
        safe_url(response.url)
        data = response.read(128 * 1024 * 1024 + 1)
    require(0 < len(data) <= 128 * 1024 * 1024, 'empty/oversized download')
    return data


def version(value):
    require(bool(re.fullmatch(r'\d+(?:\.\d+){0,2}', value)), 'unsupported version ' + value)
    parts = tuple(map(int, value.split('.')))
    return parts + (0,) * (3 - len(parts))


def satisfies(value, declaration):
    """Observed numeric semver/PEP440 subset only; unknown syntax fails closed."""
    v = version(value)
    if declaration.strip() == '*':
        return True
    results = []
    for alternative in declaration.split('||'):
        tokens = alternative.replace(',', ' ').split()
        require(bool(tokens), 'empty range')
        result = True
        for token in tokens:
            m = re.fullmatch(r'(>=|<=|==|!=|>|<|\^|~|=)?(\d+(?:\.\d+){0,2})(?:\.(x|\*))?', token)
            require(m is not None, 'unsupported range syntax ' + declaration)
            op, raw, wildcard = m.groups()
            t = version(raw)
            if wildcard:
                n = len(raw.split('.'))
                passed = v[:n] == t[:n]
            elif op == '^':
                i = next((i for i, part in enumerate(t) if part), 2)
                upper = t[:i] + (t[i] + 1,) + (0,) * (2 - i)
                passed = t <= v < upper
            elif op == '~':
                passed = t <= v < (t[0], t[1] + 1, 0)
            else:
                passed = {None: v == t, '=': v == t, '==': v == t, '!=': v != t,
                          '>=': v >= t, '<=': v <= t, '>': v > t, '<': v < t}[op]
            result = result and passed
        results.append(result)
    return any(results)


def validate_graph(rows, runtimes):
    selected = {r['name']: r['version'] for r in rows}
    checks = []
    for row in rows:
        for peer, declared in row.get('peers', {}).items():
            if peer not in selected and row.get('optional_peers', {}).get(peer, {}).get('optional'):
                checks.append(f"{row['name']}: optional peer {peer} absent; transitive resolution pending")
                continue
            require(peer in selected and satisfies(selected[peer], declared), f"{row['name']}: missing/incompatible peer {peer} {declared}")
            checks.append(f"{row['name']}: {peer} {selected[peer]} satisfies declared {declared}")
        for runtime, declared in row.get('engines', {}).items():
            if runtime in ('node', 'npm'):
                actual = selected.get(runtime, runtimes.get(runtime))
                require(actual and satisfies(actual, declared), f"{row['name']}: incompatible {runtime} {declared}")
                checks.append(f"{row['name']}: {runtime} {actual} satisfies declared {declared}")
        if row.get('requires_python'):
            require(satisfies(runtimes['python'], row['requires_python']), row['name'] + ': incompatible Python range')
            checks.append(f"{row['name']}: Python {runtimes['python']} satisfies declared {row['requires_python']}")
    return checks


def licence(name):
    return bool(re.match(r'(?i)^(licen[sc]e|copying|copyright|notice)(?:[._-].*)?$', PurePosixPath(name).name))


def relevant(name):
    return licence(name) or name == 'package/package.json' or PurePosixPath(name).name in ('pyproject.toml', 'setup.py', 'configure', 'Makefile')


def archive_evidence(data, filename):
    members = []
    if filename.endswith('.whl'):
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            for item in archive.infolist():
                if item.file_size <= 2 * 1024 * 1024 and relevant(item.filename):
                    members.append((item.filename, archive.read(item)))
    else:
        with tarfile.open(fileobj=io.BytesIO(data), mode='r:*') as archive:
            for item in archive:
                if item.isfile() and item.size <= 2 * 1024 * 1024 and relevant(item.name):
                    members.append((item.name, archive.extractfile(item).read()))
    require(len(members) <= 2000, 'too many review members')
    licences = [{'path': n, 'text': b.decode('utf-8', 'replace'), 'sha256': sha(b.decode('utf-8', 'replace').encode())}
                for n, b in members if licence(n)]
    manifests = [json.loads(b) for n, b in members if n == 'package/package.json']
    build = [{'path': n, 'sha256': sha(b)} for n, b in members
             if PurePosixPath(n).name in ('pyproject.toml', 'setup.py', 'configure', 'Makefile')]
    return licences, manifests[0] if manifests else None, build


def normalize_repo(url):
    return url.removeprefix('git+').removesuffix('.git').rstrip('/')


def validate_artifact(row):
    for field in ('name', 'version', 'url', 'sha256', 'upstream', 'licence_evidence', 'hooks'):
        require(field in row and row[field] is not None, 'missing ' + field)
    require(row['name'] in UPSTREAMS and row['upstream'] == 'https://github.com/' + UPSTREAMS[row['name']], 'mismatched upstream')
    safe_url(row['url'])
    version(row['version'])
    require(bool(re.fullmatch(r'[0-9a-f]{64}', row['sha256'])), 'missing hash')
    require(bool(row['licence_evidence']), 'missing licence evidence')
    for e in row['licence_evidence']:
        require(e.get('text') and sha(e['text'].encode()) == e['sha256'], 'licence text hash mismatch')
    require(isinstance(row['hooks'], dict), 'missing hook inspection')
    return 1


def fixture():
    return dict(name='astro', version='7.4.1', url='https://registry.npmjs.org/astro/-/astro-7.4.1.tgz',
                sha256='a' * 64, upstream='https://github.com/withastro/astro', hooks={},
                licence_evidence=[dict(path='LICENSE', text='synthetic MIT fixture', sha256=sha(b'synthetic MIT fixture'))])


def packet(rows):
    return dict(schema_version=1, observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                candidate_set_sha256=sha(canonical(rows)), artifacts=rows, human_response=None,
                status='awaiting-human-review', evidence_class='local-inert-public-artifact-inspection')


def validate_packet(value, candidates):
    rows = value.get('artifacts', [])
    require(bool(rows) and len(rows) == len(candidates), 'empty/incomplete packet')
    require(value.get('candidate_set_sha256') == sha(canonical(rows)), 'candidate-set digest mismatch')
    require(len({r['name'] for r in rows}) == len(rows), 'duplicate identity')
    require([(r['name'], r['version']) for r in rows] == [(r['name'], r['version']) for r in candidates], 'candidate identities changed')
    return sum(validate_artifact(row) for row in rows)


def collect_one(candidate):
    name, selected, ecosystem = (candidate[k] for k in ('name', 'version', 'ecosystem'))
    row = dict(candidate, upstream='https://github.com/' + UPSTREAMS[name], findings=[], peers={}, engines={})
    if ecosystem == 'npm':
        row['registry_url'] = 'https://registry.npmjs.org/' + urllib.parse.quote(name, safe='') + '/' + selected
        raw = fetch(row['registry_url'])
        meta = json.loads(raw)
        require(meta['name'] == name and meta['version'] == selected, 'registry identity mismatch')
        require(normalize_repo(meta['repository']['url']) == row['upstream'], 'registry upstream mismatch')
        row.update(url=meta['dist']['tarball'], peers=meta.get('peerDependencies', {}), optional_peers=meta.get('peerDependenciesMeta', {}),
                   engines=meta.get('engines', {}), declared_licence=meta.get('license'), registry_scripts=meta.get('scripts', {}))
        row['published_integrity'] = meta['dist'].get('integrity')
        require(row['published_integrity'] and row['published_integrity'].startswith('sha512-'), 'missing registry integrity')
    elif ecosystem == 'pypi':
        row['registry_url'] = f'https://pypi.org/pypi/{name}/{selected}/json'
        raw = fetch(row['registry_url'])
        meta = json.loads(raw)
        info = meta['info']
        require(info['version'] == selected and info['name'].lower() == name.lower(), 'registry identity mismatch')
        require(any(normalize_repo(u) == row['upstream'] for u in (info.get('project_urls') or {}).values()), 'registry upstream mismatch')
        wheels = [u for u in meta['urls'] if u['filename'].endswith('py3-none-any.whl') and not u.get('yanked')]
        require(bool(wheels), 'no non-yanked pure Python wheel')
        artifact = sorted(wheels, key=lambda u: u['filename'])[0]
        row.update(url=artifact['url'], published_sha256=artifact['digests']['sha256'], requires_python=info.get('requires_python'),
                   declared_licence=info.get('license_expression') or info.get('license'), requires_dist=info.get('requires_dist'), upload_time=artifact['upload_time_iso_8601'])
    else:
        raw = fetch(candidate['release_index'])
        require(selected.encode() in raw, 'release absent from official index')
        row['registry_url'] = candidate['release_index']
        if candidate.get('checksum_url'):
            checksum = fetch(candidate['checksum_url']).decode()
            filename = row['url'].rsplit('/', 1)[1]
            matches = [line.split()[0] for line in checksum.splitlines() if filename in line]
            require(len(matches) == 1 and re.fullmatch(r'[0-9a-f]{64}', matches[0]), 'missing official checksum')
            row['published_sha256'] = matches[0]
        row['findings'].append('Source artifact; native build/closure identity remains producing-plan work')
    row['metadata_sha256'] = sha(raw)
    data = fetch(row['url'])
    row.update(sha256=sha(data), bytes=len(data))
    if row.get('published_sha256'):
        require(row['sha256'] == row['published_sha256'], 'published SHA-256 mismatch')
    if row.get('published_integrity'):
        require(base64.b64encode(hashlib.sha512(data).digest()).decode() == row['published_integrity'][7:], 'published SHA-512 mismatch')
    licences, manifest, build = archive_evidence(data, row['url'].rsplit('/', 1)[1])
    row['licence_evidence'] = licences
    if manifest:
        require(manifest['name'] == name and manifest['version'] == selected, 'archive identity mismatch')
        if manifest.get('scripts', {}) != row['registry_scripts']:
            row['findings'].append('REGISTRY/ARCHIVE SCRIPT DISCREPANCY: compare registry_scripts with hooks.archive_scripts; unresolved human review finding')
    row['hooks'] = dict(archive_scripts=manifest.get('scripts', {}) if manifest else {}, build_files=build,
                        executed=False, scope='Direct manifests only; not a code security audit or transitive hook review')
    row['findings'].append('Not installed, built or tested compatible; inspect hooks before use')
    if name == 'gunicorn':
        row['findings'].append('Registry Python >=3.10 vs docs Python 3.12+; selected 3.13 meets both; runtime tests pending')
    row['release_notes_sha256'] = sha(fetch(candidate['release_notes']))
    row['findings'].append('Release/security page captured by hash; no vulnerability-free or legal approval claim')
    validate_artifact(row)
    print(f"COLLECTED {name} {selected} {row['bytes']} bytes", flush=True)
    return row


def render(value):
    lines = ['# T02 direct-artifact review — awaiting human response', '',
             'Candidate-set SHA-256: `' + value['candidate_set_sha256'] + '`', '',
             'No downloaded code was executed or installed. No candidate is tested compatible. SUS is a research heuristic, not compromise evidence.',
             'Full licence texts and hook commands are in the JSON. Hash consistency is not signer verification.', '',
             '| Package | Version | Research heuristic | SHA-256 | Upstream / release / artifact | Hooks / licences |',
             '|---|---|---|---|---|---|']
    for r in value['artifacts']:
        lifecycle = [s for s in r['hooks']['archive_scripts'] if s in ('preinstall', 'install', 'postinstall', 'prepare', 'prepublish', 'prepack', 'postpack')]
        lines.append(f"| {r['name']} | {r['version']} | {r['research_heuristic']} | `{r['sha256']}` | [upstream]({r['upstream']}) / [release/security]({r['release_notes']}) / [artifact]({r['url']}) | lifecycle: {', '.join(lifecycle) or 'none in direct manifest'}; build files: {len(r['hooks']['build_files'])}; licence texts: {len(r['licence_evidence'])} |")
    lines += ['', '## Declared range observations', ''] + ['- ' + c for c in value['graph_checks']]
    lines += ['', '## Decisions and unresolved findings', '',
              '- TypeScript 6.0.3 selected: checker 0.9.11 declares ^5.0.0 || ^6.0.0; latest 7.0.2 excluded.',
              '- Node 24.22.0 bundles npm 11.19.1. Python 3.13.16, pip and pip-tools are explicit bootstrap candidates; no downloaded bootstrap executed.',
              '- PostgreSQL/libpq share official 18.6 source bytes; Psycopg uses system libpq, no binary bundle.',
              '- Signer authenticity, native closure, complete transitive hashes/hooks/licences/SBOM and runtime/build tests remain pending producing-plan obligations.',
              '- Optional absent peers are reported; no peer conflicts suppressed. pnpm is not selected.',
              '- Release/security links were fetched and hashed, not an assertion that all advisories are resolved. Legal assessment remains pending.', '']
    lines += ['- ' + r['name'] + ': ' + '; '.join(r['findings']) +
              ('; Release assessment: ' + r['release_assessment'] if r.get('release_assessment') else '')
              for r in value['artifacts']]
    lines += ['', '## Human gate', '', 'Review this exact digest, JSON hook commands/licence texts and upstream release links. Supply attributable explicit approval of the digest or concrete changes. human_response remains null. No bank, cloud, commercial or operational approval is implied.', '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    for flag in ('collect', 'check-review', 'self-test'):
        group.add_argument('--' + flag, action='store_true')
    args = parser.parse_args()
    if args.self_test:
        suite = unittest.defaultTestLoader.discover(str(ROOT / 'tests'), pattern='test_qualify_dependencies.py')
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        require(result.testsRun > 0 and result.wasSuccessful(), 'failed or zero tests')
        print(f'QUALIFIER_TESTS_PASS tests={result.testsRun}')
        return
    config = json.loads(CANDIDATES.read_text())
    candidates = config['candidates']
    require({r['name'] for r in candidates} == set(UPSTREAMS), 'incomplete direct candidate set')
    if args.collect:
        rows = [collect_one(c) for c in candidates]
        value = packet(rows)
        value['candidate_manifest_sha256'] = sha(CANDIDATES.read_bytes())
        value['graph_checks'] = validate_graph(rows, config['runtimes'])
        validate_packet(value, candidates)
        REVIEW.parent.mkdir(parents=True, exist_ok=True)
        REVIEW.write_text(json.dumps(value, indent=2, ensure_ascii=True) + '\n')
        MARKDOWN.write_text(render(value))
    value = json.loads(REVIEW.read_text())
    count = validate_packet(value, candidates)
    require(value['candidate_manifest_sha256'] == sha(CANDIDATES.read_bytes()), 'candidate manifest changed')
    require(validate_graph(value['artifacts'], config['runtimes']) == value['graph_checks'], 'graph evidence changed')
    require(MARKDOWN.read_text() == render(value), 'Markdown/JSON mismatch')
    print(f"REVIEW_READY candidate_set_sha256={value['candidate_set_sha256']} artifacts={count}; integrity only, no approval")


if __name__ == '__main__':
    sys.dont_write_bytecode = True
    try:
        main()
    except (ValueError, OSError, KeyError, TypeError, tarfile.TarError, zipfile.BadZipFile) as exc:
        print(f'FAIL dependency-review: {exc}', file=sys.stderr)
        sys.exit(1)
