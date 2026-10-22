#!/usr/bin/env python3
"""Verify and retain the actual cached operator closure; not a standard SBOM."""
import argparse
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import time
import unittest
from audit_licence_gaps import candidate
from check_operator_runtime import validate_metadata
from check_python import require

ROOT = Path(__file__).resolve().parents[1]
STORE = '/nix/store/'
STORE_PATH = re.compile(r'/nix/store/[0-9a-df-np-sv-z]{32}-[^/\x00-\x20]+')
MAX_PATHS = 512
MAX_NOTICE = 10 * 1024 * 1024
RECIPE_FILES = ('ops/nixos/flake.nix', 'ops/nixos/flake.lock', 'ops/nixos/operator-runtime.nix',
                'ops/nixos/database-tools.nix', 'ops/runtime/wheels.json')


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def store_path(value):
    require(type(value) is str and STORE_PATH.fullmatch(value) is not None, 'exact store object path required')
    return value


def nar_hash(value):
    require(type(value) is str and value.startswith('sha256-'), 'SHA256 NAR hash required')
    try:
        decoded = base64.b64decode(value[7:], validate=True)
    except ValueError:
        raise ValueError('invalid NAR digest') from None
    require(len(decoded) == 32 and base64.b64encode(decoded).decode() == value[7:], 'invalid NAR digest')


def validate_graph(root, nodes):
    store_path(root)
    require(type(nodes) is dict and 0 < len(nodes) <= MAX_PATHS and root in nodes, 'bounded complete closure required')
    for path, item in nodes.items():
        store_path(path)
        require(set(item) == {'nar_hash', 'nar_size', 'references', 'deriver'}, 'closed closure node required')
        nar_hash(item['nar_hash'])
        require(type(item['nar_size']) is int and item['nar_size'] > 0, 'positive NAR byte count required')
        require(type(item['references']) is list and len(item['references']) == len(set(item['references']))
                and all(ref in nodes for ref in item['references']), 'complete unique native references required')
        require(store_path(item['deriver']).endswith('.drv'), 'actual deriver required')
    seen, pending = set(), [root]
    while pending:
        path = pending.pop()
        if path not in seen:
            seen.add(path)
            pending.extend(nodes[path]['references'])
    require(seen == set(nodes), 'unreachable or invented closure object')


def normalise_paths(raw, root):
    require(type(raw) is dict, 'version1 Nix path-info object required')
    nodes = {path: {'nar_hash': item['narHash'], 'nar_size': item['narSize'],
                    'references': sorted(item['references']), 'deriver': item['deriver']} for path, item in raw.items()}
    validate_graph(root, nodes)
    return nodes


def derivation_record(path, value, output_path):
    store_path(path)
    require(set(value) == {'version', 'derivations'} and value['version'] == 4,
            'observed Nix derivation format4 required')
    require(set(value['derivations']) == {Path(path).name}, 'exact derivation identity required')
    item = value['derivations'][Path(path).name]
    outputs = {name: STORE + output['path'] for name, output in item['outputs'].items()}
    require(output_path in outputs.values(), 'native output/deriver mismatch')
    for output in outputs.values():
        store_path(output)
    attrs = item.get('structuredAttrs') or item['env']
    source = attrs.get('src')
    if source is not None:
        store_path(source)
    return {'name': item['name'], 'system': item['system'],
            'declared_pname': attrs.get('pname'), 'declared_version': attrs.get('version'),
            'source_store_path': source,
            'source_provenance_status': 'recipe-source-pointer-only' if source else 'no-source-attribute-in-recipe',
            'outputs': outputs}


def notice_files(root, closure):
    """Hash named regular files only. Do not follow directory or file symlinks."""
    root = Path(root)
    result = []
    if not root.is_dir():
        return result
    visited = 0
    for directory, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = sorted(d for d in dirs if not (Path(directory) / d).is_symlink())
        for name in sorted(files):
            visited += 1
            require(visited <= 200000, 'bounded notice walk required')
            path = Path(directory) / name
            if not candidate(name) or path.is_symlink():
                continue
            require(path.is_file() and path.stat().st_size <= MAX_NOTICE, 'bounded regular notice required')
            resolved = path.resolve()
            require(any(str(resolved) == p or str(resolved).startswith(p + '/') for p in closure), 'notice escapes closure')
            data = path.read_bytes()
            require(0 < len(data) <= MAX_NOTICE, 'nonempty bounded notice required')
            result.append({'path': str(path.relative_to(root)), 'size': len(data), 'sha256': sha256(data)})
    return sorted(result, key=lambda x: x['path'])


def run(args, timeout=30):
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True, check=True, timeout=timeout).stdout


def collect():
    metadata = validate_metadata(json.loads(run(['nix', 'eval', '--offline', '--json',
        './ops/nixos#deploymentMetadata.x86_64-linux.operatorInspection'])))
    root = metadata['package']
    raw = json.loads(run(['nix', 'path-info', '--json', '--json-format', '1', '--recursive', root]))
    nodes = normalise_paths(raw, root)
    # Hash actual stored bytes; no trust/signature acceptance or automatic repair.
    run(['nix', 'store', 'verify', '--no-trust', '--recursive', root], timeout=120)
    records = {}
    missing_derivations = []
    cache = {}
    for path, node in sorted(nodes.items()):
        drv = node['deriver']
        if not Path(drv).exists():
            missing_derivations.append(drv)
            records[path] = {**node, 'derivation_status': 'missing-local-recipe-review-pending',
                             'derivation_sha256': None, 'recipe': None, 'named_notices': notice_files(path, nodes)}
            continue
        if drv not in cache:
            data = Path(drv).read_bytes()
            require(0 < len(data) < 16 * 1024 * 1024, 'bounded derivation required')
            cache[drv] = (sha256(data), json.loads(run(['nix', 'derivation', 'show', drv])))
        drv_hash, value = cache[drv]
        recipe = derivation_record(drv, value, path)
        notices = notice_files(path, nodes)
        records[path] = {**node, 'derivation_status': 'local-recipe-output-bound', 'derivation_sha256': drv_hash, 'recipe': recipe, 'named_notices': notices,
                         'notice_status': 'candidates-found-review-pending' if notices else 'no-named-notices-in-output-review-pending'}
    return {'schema_version': 1, 'evidence_class': 'local-realized-nix-closure',
            'scope': 'Standalone operator runtime reference closure only; not a standard SBOM or build/source closure',
            'nix_version': run(['nix', '--version']).strip(), 'root': root,
            'flake_lock_sha256': sha256((ROOT / 'ops/nixos/flake.lock').read_bytes()),
            'recipe_hashes': {p: sha256((ROOT / p).read_bytes()) for p in RECIPE_FILES},
            'store_bytes_verified': True, 'trust_signatures_verified': False,
            'inventory_complete': False, 'legal_approval': False, 'runtime_qualified': False,
            'oci_images_included': False, 'missing_local_derivations': sorted(set(missing_derivations)), 'nodes': records}


def main():
    start = time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    report = collect()
    encoded = (json.dumps(report, indent=2, sort_keys=True) + '\n').encode()
    output = ROOT / 'docs/evidence/t02/operator-native-closure.json'
    if args.write:
        with output.open('xb') as stream:
            stream.write(encoded)
    else:
        require(output.read_bytes() == encoded, 'retained native closure evidence mismatch')
    suite = unittest.defaultTestLoader.discover(str(ROOT / 'tests'), pattern='test_native_closure.py')
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream).run(suite)
    require(result.testsRun >= 7 and result.wasSuccessful() and not result.skipped, 'native closure controls failed: ' + stream.getvalue())
    print(f'NATIVE_CLOSURE_PASS checks={len(report["nodes"])} tests={result.testsRun} duration_seconds={time.monotonic()-start:.3f}')
    print('Actual cached operator reference closure only; full inventory/notices/source/OCI/qualification pending')


if __name__ == '__main__':
    main()
