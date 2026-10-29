#!/usr/bin/env python3
"""Reconcile raw maintained image/Nix SBOMs with actual image and store bytes.

No SBOM is synthesized here. Raw Syft and sbomnix documents remain unchanged;
the separate inventory binds their claims and records unresolved notice findings.
"""
import argparse
import base64
import collections
from contextlib import contextmanager
import datetime
import gzip
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from urllib.parse import unquote

import check_native_closure as native
import check_image_layout as layout
from audit_licence_names import extended_candidate
from audit_licence_gaps import ROOT, require, sha256
from inspect_image_archive import CANDIDATE_IMAGES, inspect, unique

MAX_DOCUMENT = 64 * 1024**2
MAX_NOTICE = 10 * 1024**2
MAX_EXPANDED = 4 * 1024**3


def image_store_paths(entries):
    result = set()
    for row in entries:
        name = row['path']
        require(layout.canonical(name) == name, 'noncanonical observed image path')
        if name.startswith('nix/store/'):
            result.add(native.store_path('/' + '/'.join(PurePosixPath(name).parts[:3])))
    require(0 < len(result) <= native.MAX_PATHS, 'nonempty bounded image store inventory required')
    return result


def select_output_recipe(path, value, registered_deriver):
    """Use Nix's first valid recipe as sbomnix does, without claiming build origin."""
    native.store_path(path)
    native.store_path(registered_deriver)
    require(set(value) == {'version', 'derivations'} and value['version'] == 4
            and bool(value['derivations']), 'actual compatible recipe required')
    candidates = []
    recipes = {}
    for name, definition in value['derivations'].items():
        drv = native.store_path('/nix/store/' + name)
        require(drv.endswith('.drv'), 'actual derivation identity required')
        recipes[drv] = native.derivation_record(drv, {'version': 4, 'derivations': {name: definition}}, path)
        candidates.append(drv)
    selected = candidates[0]
    # Match the pinned maintained tool's env-field projection. Structured Nix
    # attributes stay authoritative in recipe and are never replaced by this view.
    recipe = recipes[selected]
    environment = value['derivations'][Path(selected).name]['env']
    pname = environment.get('pname', recipe['name'])
    require(type(pname) is str and bool(pname), 'bounded tool recipe name required')
    projection = {'name': recipe['name'].partition(pname)[0] + pname,
                  'version': environment.get('version', '')}
    return {'deriver': selected, 'registered_deriver': registered_deriver,
            'compatible_derivations': candidates, 'recipe': recipe,
            'sbomnix_recipe_projection': projection,
            'build_origin_proven': False,
            'recipe_binding': 'Nix valid-deriver output binding; registered build origin retained separately'}


def validate_native_nodes(paths, nodes):
    require(type(nodes) is dict and set(nodes) == set(paths), 'omitted/invented native object')
    for path, node in nodes.items():
        native.store_path(path)
        native.nar_hash(node['nar_hash'])
        require(type(node['nar_size']) is int and node['nar_size'] > 0, 'native NAR size missing')
        require(type(node['references']) is list and len(node['references']) == len(set(node['references']))
                and set(node['references']) <= set(paths), 'native reference closure incomplete')
        require(native.store_path(node['deriver']).endswith('.drv')
                and re.fullmatch(r'[0-9a-f]{64}', node['derivation_sha256']), 'actual recipe identity required')
        require(path in node['recipe']['outputs'].values(), 'native output/recipe substitution')


def resolve_observed(entries, name):
    """Resolve only retained image metadata; never follow a host absolute link."""
    require(type(name) is str and name.startswith('/') and len(name) <= 4096
            and '\\' not in name and all(32 <= ord(c) < 127 for c in name), 'unsafe SBOM location')
    objects = {row['path']: row for row in entries}
    pending, resolved, links = name.split('/')[1:], [], 0
    while pending:
        part = pending.pop(0)
        if part in ('', '.'):
            continue
        if part == '..':
            require(bool(resolved), 'SBOM location escapes image')
            resolved.pop()
            continue
        path = '/'.join([*resolved, part])
        require(path in objects, 'SBOM location absent from actual image: ' + path)
        row = objects[path]
        if row['type'] == 'symlink':
            links += 1
            require(links <= 40, 'SBOM location link cycle')
            target = row['link_target']
            if target.startswith('/'):
                resolved = []
            pending = target.split('/') + pending
        else:
            require(row['type'] == 'directory' or not pending, 'SBOM location parent is not a directory')
            resolved.append(part)
    path = '/'.join(resolved) or '.'
    require(path in objects, 'SBOM location not observed')
    return objects[path]


def verify_syft_source(raw, outer, image, version):
    require(raw['descriptor']['name'] == 'syft' and raw['descriptor']['version'] == version,
            'actual pinned Syft identity required')
    require(raw['source']['type'] == 'image', 'actual image scan required')
    source = raw['source']['metadata']
    require(source['imageID'] == outer['config_image_id'] and source['tags'] == [image + ':candidate']
            and source['architecture'] in ('', 'amd64') and source['os'] in ('', 'linux'), 'SBOM source substitution')
    try:
        config = base64.b64decode(source['config'], validate=True)
    except (ValueError, TypeError):
        raise ValueError('raw image configuration bytes required') from None
    require(len(config) <= layout.MAX_JSON and 'sha256:' + sha256(config) == outer['config_image_id']
            and json.loads(config, object_pairs_hook=unique) == outer['config'], 'SBOM raw config byte substitution')
    require(outer['config']['architecture'] == 'amd64' and outer['config']['os'] == 'linux',
            'actual image platform mismatch')
    return {'platform_fields_omitted_by_tool': [key for key in ('architecture', 'os') if source[key] == ''],
            'platform_authority': 'exact original configuration bytes and SHA256; raw tool omissions retained'}


def verify_syft_claims(raw, entries, nodes, *, allow_inferred_findings=False):
    seen = set()
    native_claims = 0
    unversioned, findings = [], []
    for artifact in raw['artifacts']:
        require(type(artifact['id']) is str and artifact['id'] not in seen, 'duplicate/missing Syft artifact ID')
        seen.add(artifact['id'])
        require(bool(artifact['locations']), 'actual component location required')
        for location in artifact['locations']:
            resolve_observed(entries, location['path'])
        if artifact['type'] != 'nix':
            continue
        path = native.store_path(artifact['metadata']['path'])
        require(path in image_store_paths(entries) and path in nodes, 'invented native package location')
        recipe = nodes[path]['recipe']
        version = recipe['declared_version']
        if version:
            names = {recipe['declared_pname']}
            if recipe['name'].endswith('-' + version):
                names.add(recipe['name'][:-len(version) - 1])
            matches = artifact['version'] == version and artifact['name'] in names
            if not matches:
                require(allow_inferred_findings and artifact.get('foundBy') == 'nix-cataloger'
                        and artifact['metadata'].get('derivation') == {},
                        'inferred native name/version differs from actual recipe: ' + path)
                findings.append({'path': path, 'observed_name': artifact['name'],
                                 'observed_version': artifact['version'], 'recipe_names': sorted(n for n in names if n),
                                 'recipe_version': version, 'accepted_as_authority': False,
                                 'status': 'raw-tool-inference-differs-from-output-bound-recipe-review-pending'})
        else:
            unversioned.append(path)
        native_claims += 1
    require(bool(seen) and native_claims > 0, 'positive actual package counts required')
    return {'artifacts': len(seen), 'native_claims': native_claims,
            'claims_without_declared_recipe_version': sorted(unversioned),
            'native_inference_findings': findings, 'native_inferences_match_recipes': not findings}


def reconcile_syft_cdx(raw, bom, entries):
    require(bom.get('bomFormat') == 'CycloneDX' and bom.get('specVersion') == '1.6', 'raw Syft CycloneDX1.6 required')
    artifacts = {row['id']: row for row in raw['artifacts']}
    require(len(artifacts) == len(raw['artifacts']), 'duplicate raw artifacts')
    matched, files, refs, artifact_refs = set(), 0, set(), {}
    for component in bom['components']:
        ref = component['bom-ref']
        require(ref not in refs, 'duplicate standard component ref')
        refs.add(ref)
        package_id = re.search(r'(?:[?&])package-id=([^&]+)', ref)
        identity = unquote(package_id[1]) if package_id else ref
        if package_id or identity in artifacts:
            require(identity in artifacts and identity not in matched, 'omitted/invented standard package')
            original = artifacts[identity]
            name = component['name']
            if component.get('group'):
                name = component['group'] + '/' + name
            require(name == original['name'] and component.get('version') == original.get('version'),
                    'standard package identity substitution')
            if original.get('purl'):
                require(component.get('purl') == original['purl'], 'standard package PURL substitution')
            matched.add(identity)
            artifact_refs[identity] = ref
        else:
            require(component['type'] == 'file', 'unbound additional standard component')
            entry = resolve_observed(entries, component['name'])
            hashes = {row['alg']: row['content'] for row in component.get('hashes', [])}
            require(entry['type'] == 'file' and hashes.get('SHA-256') == entry['sha256'], 'standard file hash substitution')
            files += 1
    require(matched == set(artifacts), 'standard SBOM omitted an actual package')
    expected_edges = set()
    for relation in raw.get('artifactRelationships', []):
        if relation['type'] == 'dependency-of':
            require(relation['parent'] in artifact_refs and relation['child'] in artifact_refs,
                    'raw dependency has an unbound endpoint')
            expected_edges.add((artifact_refs[relation['child']], artifact_refs[relation['parent']]))
    actual_edges, dependency_refs = set(), set()
    for dependency in bom.get('dependencies', []):
        parent, children = dependency['ref'], dependency.get('dependsOn', [])
        require(parent in artifact_refs.values() and parent not in dependency_refs
                and len(children) == len(set(children)) and set(children) <= set(artifact_refs.values()),
                'standard dependency endpoint omission/substitution')
        dependency_refs.add(parent)
        actual_edges.update((parent, child) for child in children)
    require(actual_edges == expected_edges, 'standard dependency edge omission/substitution')
    return {'packages': len(matched), 'files': files, 'dependency_edges': len(actual_edges)}


def reconcile_native_cdx(bom, nodes, inventory_drv):
    require(bom.get('bomFormat') == 'CycloneDX' and bom.get('specVersion') == '1.4'
            and bom['metadata']['component']['bom-ref'] == inventory_drv, 'raw native SBOM/root binding required')
    expected = collections.defaultdict(list)
    for path, node in nodes.items():
        expected[node['deriver']].append(path)
    components = {row['bom-ref']: row for row in bom['components']}
    require(len(components) == len(bom['components']) and set(components) == set(expected), 'native standard component coverage mismatch')
    declared, findings = set(), []
    for drv, paths in expected.items():
        component = components[drv]
        outputs = {row['value'] for row in component.get('properties', []) if row['name'] == 'nix:output_path'}
        recipe = nodes[paths[0]]['recipe']
        require(set(paths) <= outputs <= set(recipe['outputs'].values()), 'native standard output/recipe mismatch')
        declared_identity = {'name': recipe['declared_pname'] or recipe['name'],
                             'version': recipe['declared_version'] or ''}
        tool_identity = nodes[paths[0]].get('sbomnix_recipe_projection', declared_identity)
        require(component['name'] == tool_identity['name'] and component.get('version', '') == tool_identity['version'],
                'native standard name/version mismatch')
        if tool_identity != declared_identity:
            findings.append({'deriver': drv, 'tool_identity': tool_identity, 'declared_identity': declared_identity,
                             'accepted_as_declared_version': False,
                             'status': 'maintained-tool-env-projection-differs-from-recipe-attributes-review-pending'})
        declared.update(outputs)
    expected_edges = {(node['deriver'], nodes[ref]['deriver']) for node in nodes.values()
                      for ref in node['references'] if node['deriver'] != nodes[ref]['deriver']}
    expected_edges.update((inventory_drv, node['deriver']) for node in nodes.values())
    dependencies = {row['ref']: row.get('dependsOn', []) for row in bom['dependencies']}
    require(len(dependencies) == len(bom['dependencies']) and set(dependencies) == set(expected) | {inventory_drv},
            'native dependency node coverage mismatch')
    edges = {(parent, child) for parent, children in dependencies.items() for child in children}
    require(edges == expected_edges, 'native dependency edge omission/substitution')
    return {'actual_outputs': sorted(nodes), 'declared_sibling_outputs_not_observed': sorted(declared - set(nodes)),
            'components': len(components), 'dependency_edges': len(edges),
            'identity_projection_findings': findings,
            'inventory_root_is_not_an_image_component': True}


def verify_notice(entry, data):
    require(type(data) is bytes and 0 < len(data) == entry['size'] <= MAX_NOTICE
            and sha256(data) == entry['sha256'], 'actual incorporated notice bytes mismatch')
    return sha256(data)


def publish_validated(report, payloads, validate):
    require(type(payloads) is dict and payloads and all(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]+', name)
            and name != 'report.json' and type(data) is bytes for name, data in payloads.items()), 'closed evidence filenames required')
    validate(payloads)
    encoded = (json.dumps(report, indent=2) + '\n').encode()
    directory = ROOT / 'docs/evidence/t02/image-sbom-revisions'
    require(not directory.is_symlink(), 'evidence symlink denied')
    directory.mkdir(exist_ok=True)
    destination = directory / sha256(encoded)
    destination.mkdir(exist_ok=False)
    for name, data in [*sorted(payloads.items()), ('report.json', encoded)]:
        with (destination / name).open('xb') as stream:
            stream.write(data)
        require((destination / name).read_bytes() == data, 'retained evidence readback mismatch')
    return destination / 'report.json'


def run(command, *, timeout=30, env=None, cwd=None):
    result = subprocess.run(command, cwd=cwd or ROOT, env=env, capture_output=True, text=True, timeout=timeout)
    require(result.returncode == 0, 'native inspection command failed: ' + json.dumps({
        'command': command, 'exit_code': result.returncode, 'stdout': result.stdout[-4000:], 'stderr': result.stderr[-8000:]}))
    return result.stdout


def load_inputs(build_path, filesystem_path):
    raw = layout.read_small(build_path.parent, build_path.name)
    require(build_path.name == sha256(raw) + '.json', 'build index content address mismatch')
    build = layout.json_bytes(raw)
    raw_fs = layout.read_small(filesystem_path.parent, filesystem_path.name, MAX_DOCUMENT)
    require(filesystem_path.parent.name == sha256(raw_fs), 'filesystem report content address mismatch')
    observed = layout.json_bytes(raw_fs)
    require([image['image'] for image in build['images']] == list(CANDIDATE_IMAGES)
            and [image['image'] for image in observed['images']] == list(CANDIDATE_IMAGES), 'all four exact candidates required')
    images = []
    for item, fs in zip(build['images'], observed['images'], strict=True):
        outer_path = ROOT / item['outer_report']['path']
        outer_raw = layout.read_small(outer_path.parent, outer_path.name)
        require(sha256(outer_raw) == item['outer_report']['sha256'], 'outer report identity mismatch')
        outer = layout.json_bytes(outer_raw)
        require(inspect(Path(item['archive_path']), expected_image=item['image']) == outer, 'actual archive substitution')
        require(fs['source_archive']['sha256'] == outer['archive_sha256'], 'filesystem source mismatch')
        path = filesystem_path.parent / fs['filesystem_manifest']['path']
        compressed = layout.read_small(path.parent, path.name, MAX_DOCUMENT)
        require(sha256(compressed) == fs['filesystem_manifest']['sha256'], 'filesystem manifest hash mismatch')
        with gzip.GzipFile(fileobj=io.BytesIO(compressed)) as stream:
            data = stream.read(layout.MAX_MANIFEST + 1)
        require(len(data) <= layout.MAX_MANIFEST and sha256(data) == fs['filesystem_manifest']['uncompressed_sha256'],
                'bounded exact filesystem manifest required')
        entries = layout.json_bytes(data)['entries']
        images.append({'image': item['image'], 'archive': Path(item['archive_path']), 'outer': outer,
                       'entries': entries, 'store_paths': image_store_paths(entries)})
    return images


def collect_native(images, tools, scratch, build_parent):
    paths = set().union(*(item['store_paths'] for item in images))
    nix = tools['nix']['executable']
    # Refuse missing local inputs before a maintained tool can force-realise one.
    raw_paths = layout.json_bytes(run([nix, 'path-info', '--offline', '--json', '--json-format', '1', *sorted(paths)]))
    require(set(raw_paths) == paths, 'actual image store inputs unavailable')
    expression = scratch / 'native-root.nix'
    # The source is fixed program text; data enters as JSON in a separate file.
    data_file = scratch / 'store-paths.json'
    data_file.write_text(json.dumps(sorted(paths)))
    source = '''let
      f = builtins.getFlake (builtins.getEnv "SHOP_SBOM_FLAKE");
      p = import f.inputs.nixpkgs { system = "x86_64-linux"; };
      paths = builtins.fromJSON (builtins.readFile (builtins.getEnv "SHOP_SBOM_PATHS"));
    in p.linkFarm "shop-observed-image-native-inventory-root" (map (path: {
      name = builtins.baseNameOf path; path = builtins.storePath path;
    }) paths)
    '''
    expression.write_text(source)
    env = dict(os.environ, SHOP_SBOM_FLAKE='git+file://' + str(ROOT) + '?dir=ops/nixos', SHOP_SBOM_PATHS=str(data_file))
    command = [nix, 'build', '--offline', '--impure', '--file', str(expression), '--max-jobs', '1', '--cores', '2',
               '--option', 'builders', '', '--option', 'build-dir', str(build_parent), '--no-link', '--json']
    result = layout.json_bytes(run(command, timeout=120, env=env))
    require(type(result) is list and len(result) == 1, 'one native inventory root required')
    inventory_root = native.store_path(result[0]['outputs']['out'])
    inventory_drv = native.store_path(result[0]['drvPath'])
    raw = layout.json_bytes(run([nix, 'path-info', '--offline', '--json', '--json-format', '1', '--recursive', inventory_root]))
    nodes = native.normalise_paths(raw, inventory_root)
    require(set(nodes) == paths | {inventory_root}, 'actual image/native reference closure mismatch')
    run([nix, 'store', 'verify', '--no-trust', '--recursive', inventory_root], timeout=120)
    nodes.pop(inventory_root)
    evaluation_command = [nix, 'derivation', 'show', '--offline', '--recursive',
                          *['./ops/nixos#' + name for name in CANDIDATE_IMAGES]]
    evaluation = run(evaluation_command, timeout=120).encode()
    require(0 < len(evaluation) <= MAX_DOCUMENT, 'bounded locked recipe evaluation required')
    graph = layout.json_bytes(evaluation)
    require(set(graph) == {'version', 'derivations'} and graph['version'] == 4,
            'actual evaluated Nix recipe graph required')
    with (scratch / 'locked-recipes.json').open('xb') as output:
        output.write(evaluation)
    records, recipes = {}, {}
    for path, node in sorted(nodes.items()):
        value = layout.json_bytes(run([nix, 'derivation', 'show', '--offline', path]))
        binding = select_output_recipe(path, value, node['deriver'])
        drv = binding['deriver']
        require(Path(drv).name in graph['derivations']
                and value['derivations'][Path(drv).name] == graph['derivations'][Path(drv).name],
                'selected output recipe absent from the locked image graph')
        if drv not in recipes:
            data = layout.read_small(Path(drv).parent, Path(drv).name, 16 * 1024**2)
            recipes[drv] = sha256(data)
        records[path] = {**node, **binding, 'derivation_sha256': recipes[drv]}
    validate_native_nodes(paths, records)
    return records, {'path': inventory_root, 'deriver': inventory_drv, 'build_command': command,
                     'expression': source, 'input_paths_sha256': sha256(data_file.read_bytes()),
                     'store_bytes_verified': True, 'trust_signatures_verified': False,
                     'recipe_evaluation': {'command': evaluation_command, 'sha256': sha256(evaluation),
                                           'bytes': len(evaluation), 'derivations': len(graph['derivations']),
                                           'retained_file': 'locked-recipes.json'},
                     'scope': 'Inspection reference root only; this root is absent from all runtime images'}


def verify_host_image_bytes(images, nodes):
    expected = {}
    for image in images:
        for row in image['entries']:
            if not row['path'].startswith('nix/store/'):
                continue
            path = '/' + '/'.join(PurePosixPath(row['path']).parts[:3])
            relative = str(PurePosixPath(row['path']).relative_to(path[1:]))
            previous = expected.setdefault(path, {}).get(relative)
            if previous:
                for key in ('type', 'mode', 'sha256', 'size', 'link_target'):
                    require(previous.get(key) == row.get(key), 'shared native image bytes differ')
            expected[path][relative] = row
    notices, payloads, checked = {}, {}, 0
    for path in sorted(nodes):
        root = Path(path)
        require(root.is_dir() and not root.is_symlink(), 'current candidate native directory required')
        _, entries = layout.inventory_root(root)
        actual = {row['path']: row for row in entries}
        require(set(actual) == set(expected[path]), 'image/native path set mismatch: ' + path)
        found = []
        for name, row in actual.items():
            image_row = expected[path][name]
            for key in ('type', 'mode', 'sha256', 'size', 'link_target'):
                require(row.get(key) == image_row.get(key), 'actual image/native bytes or mode mismatch: ' + path + '/' + name)
            checked += 1
            if row['type'] == 'file' and extended_candidate(name):
                data = layout.read_small(root, name, MAX_NOTICE)
                digest = verify_notice(image_row, data)
                filename = digest + '.notice.txt'
                payloads[filename] = data
                found.append({'image_path': path + '/' + name, 'size': len(data), 'sha256': digest,
                              'retained_file': filename, 'classification': 'filename-candidate-not-legal-approval'})
        notices[path] = found
    return {'store_objects': len(nodes), 'entries_compared': checked, 'notice_candidates': notices}, payloads


def unpack_archive(source, target, expected):
    with layout.beneath(source.parent, source.name) as (stream, info):
        digest = hashlib.sha256()
        while data := stream.read(1024**2):
            digest.update(data)
        require(digest.hexdigest() == expected, 'archive bytes changed before scan')
        stream.seek(0)
        expanded, digest = 0, hashlib.sha256()
        with gzip.GzipFile(fileobj=stream) as compressed, target.open('xb') as output:
            while data := compressed.read(1024**2):
                expanded += len(data)
                require(expanded <= MAX_EXPANDED, 'outer archive expansion bound exceeded')
                digest.update(data)
                output.write(data)
    return {'sha256': digest.hexdigest(), 'bytes': expanded,
            'scope': 'Lossless outer gzip decompression only; no layer/config bytes changed'}


def tools_manifest(path):
    require(re.fullmatch(r'/nix/store/[0-9a-df-np-sv-z]{32}-shop-sbom-tool-manifest.json', str(path)),
            'immutable pinned SBOM tool manifest required')
    raw = layout.read_small(path.parent, path.name)
    tools = layout.json_bytes(raw)
    require(set(tools) == {'schema_version', 'syft', 'sbomnix', 'nix', 'unshare'} and tools['schema_version'] == 1,
            'closed SBOM tool manifest required')
    records = {}
    for name, expected in (('syft', 'syft {version}'), ('sbomnix', '{version}'), ('nix', 'nix (Nix) {version}')):
        entry = tools[name]
        require(set(entry) == {'executable', 'version'} and entry['executable'].startswith('/nix/store/')
                and entry['executable'].endswith('/bin/' + name), 'exact pinned tool executable required')
        version = run([entry['executable'], '--version'], timeout=10).strip()
        require(version == expected.format(version=entry['version']), 'actual pinned SBOM tool version mismatch')
        records[name] = {**entry, 'actual_version': version, 'sha256': sha256(Path(entry['executable']).read_bytes())}
    return tools, {'manifest': str(path), 'sha256': sha256(raw), 'tools': records}


def isolated_tool(command, tools, scratch, records):
    env = {'HOME': str(scratch / 'home'), 'TMPDIR': str(scratch / 'tmp'),
           'XDG_RUNTIME_DIR': str(scratch / 'run'), 'XDG_CONFIG_HOME': str(scratch / 'config'),
           'XDG_CACHE_HOME': str(scratch / 'cache'), 'PATH': str(Path(tools['nix']['executable']).parent),
           'LANG': 'C', 'LC_ALL': 'C', 'TZ': 'UTC', 'GOMAXPROCS': '2', 'SYFT_CHECK_FOR_APP_UPDATE': 'false',
           'NIX_CONFIG': 'experimental-features = nix-command flakes\nsubstituters =\nmax-jobs = 0\nbuilders =\n'}
    isolated = [tools['unshare'], '--user', '--map-user=1000', '--map-group=1000', '--net', '--', *command]
    start = time.monotonic()
    result = subprocess.run(isolated, env=env, cwd=scratch, capture_output=True, text=True, timeout=120)
    record = {'command': isolated, 'exit_code': result.returncode, 'duration_seconds': time.monotonic() - start,
              'stdout': result.stdout, 'stderr': result.stderr}
    records.append(record)
    with (scratch / ('command-' + str(len(records)) + '.json')).open('x') as output:
        json.dump(record, output, indent=2)
        output.write('\n')
    require(result.returncode == 0, 'standard SBOM command failed: ' + json.dumps(record))


def schema_validation(payloads, scratch, unshare):
    from check_python import frozen_environment
    names = sorted(name for name in payloads if name.endswith('.cdx.json'))
    require(len(names) == 5, 'four image plus one native standard SBOM required')
    candidate = scratch / 'validation'
    candidate.mkdir()
    for name in names:
        (candidate / name).write_bytes(payloads[name])
    program = '''import hashlib,importlib.metadata,json,pathlib,sys
from cyclonedx.validation.json import JsonStrictValidator
from cyclonedx.schema import SchemaVersion
versions={'1.4':SchemaVersion.V1_4,'1.6':SchemaVersion.V1_6}
rows=[]
for name in sys.argv[1:]:
 raw=pathlib.Path(name).read_bytes();value=json.loads(raw)
 validator=JsonStrictValidator(versions[value['specVersion']]);error=validator.validate_str(raw.decode())
 rows.append({'name':pathlib.Path(name).name,'sha256':hashlib.sha256(raw).hexdigest(),'schema_version':value['specVersion'],'valid':error is None,'diagnostic':str(error)[:3000] if error else None})
 changed=json.loads(raw);changed.pop('bomFormat',None)
 negative=validator.validate_str(json.dumps(changed))
 assert negative is not None,'actual invalid-control schema rejection absent'
print(json.dumps({'validator':'cyclonedx-python-lib','version':importlib.metadata.version('cyclonedx-python-lib'),'documents':rows,'invalid_controls_rejected':len(rows)}))
'''
    with frozen_environment('tools', scratch / 'validator-tools') as (python, env, expected):
        result = subprocess.run([unshare, '--net', '--', str(python), '-I', '-c', program,
                                 *[str(candidate / name) for name in names]], cwd=ROOT, env=env,
                                capture_output=True, text=True, timeout=30, check=True)
    receipt = layout.json_bytes(result.stdout)
    require(all(row['valid'] for row in receipt['documents']), 'raw standard SBOM schema invalid: ' + json.dumps(receipt))
    return receipt


@contextmanager
def attempt_directory(parent):
    # A failed attempt's raw tool files/diagnostics remain for review. Successful
    # attempts remove only this exact new private child after retained readback.
    directory = Path(tempfile.mkdtemp(prefix='image-sbom-', dir=parent))
    try:
        yield directory
    except BaseException:
        print('IMAGE_SBOM_FAILED_ATTEMPT retained=' + str(directory), flush=True)
        raise
    else:
        shutil.rmtree(directory)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-index', type=Path, required=True)
    parser.add_argument('--filesystem-report', type=Path, required=True)
    parser.add_argument('--tool-manifest', type=Path, default=os.environ.get('SHOP_SBOM_TOOL_MANIFEST'))
    parser.add_argument('--scratch-parent', type=Path, required=True)
    parser.add_argument('--record-evidence', action='store_true')
    args = parser.parse_args()
    started = time.monotonic()
    require(args.tool_manifest is not None, 'pinned SBOM shell required')
    sources = ['scripts/check_image_sbom.py', 'tests/test_image_sbom.py', 'ops/nixos/flake.nix',
               'ops/nixos/flake.lock', 'scripts/check_native_closure.py', 'scripts/check_image_layout.py']
    hashes = {name: sha256((ROOT / name).read_bytes()) for name in sources}
    tools, tool_record = tools_manifest(args.tool_manifest)
    images = load_inputs(args.build_index, args.filesystem_report)
    parent = layout.owned_scratch_parent(args.scratch_parent)
    require(shutil.disk_usage(parent).free > 2 * 1024**3, 'two GiB free dedicated SBOM scratch required')
    with attempt_directory(parent) as scratch:
        for name in ('home', 'tmp', 'run', 'config', 'cache'):
            (scratch / name).mkdir(mode=0o700)
        nodes, native_root = collect_native(images, tools, scratch, parent)
        with (scratch / 'native-observation.json').open('x') as output:
            json.dump({'native_reference_root': native_root, 'nodes': nodes}, output, indent=2)
            output.write('\n')
        host_binding, payloads = verify_host_image_bytes(images, nodes)
        payloads['locked-recipes.json'] = layout.read_small(scratch, 'locked-recipes.json', MAX_DOCUMENT)
        config = scratch / 'syft.yaml'
        config.write_text('check-for-app-update: false\nparallelism: 2\nenrich: []\n')
        records, observations = [], []
        for image in images:
            name = image['image']
            archive = scratch / (name + '.docker.tar')
            unpacked = unpack_archive(image['archive'], archive, image['outer']['archive_sha256'])
            syft_name, cdx_name = name + '.syft.json', name + '.cdx.json'
            isolated_tool([tools['syft']['executable'], '-c', str(config), 'scan', 'docker-archive:' + str(archive),
                           '--parallelism', '2', '--override-default-catalogers', 'image', '--scope', 'squashed',
                           '-o', 'syft-json=' + str(scratch / syft_name), '-o', 'cyclonedx-json=' + str(scratch / cdx_name)],
                          tools, scratch, records)
            for output in (syft_name, cdx_name):
                payloads[output] = layout.read_small(scratch, output, MAX_DOCUMENT)
            raw, bom = layout.json_bytes(payloads[syft_name]), layout.json_bytes(payloads[cdx_name])
            source_binding = verify_syft_source(raw, image['outer'], name, tools['syft']['version'])
            claims = verify_syft_claims(raw, image['entries'], nodes, allow_inferred_findings=True)
            projection = reconcile_syft_cdx(raw, bom, image['entries'])
            observations.append({'image': name, 'archive': str(image['archive']),
                                 'archive_sha256': image['outer']['archive_sha256'],
                                 'config_image_id': image['outer']['config_image_id'], 'decompressed_outer_tar': unpacked,
                                 'source_binding': source_binding, 'syft_claims': claims, 'standard_projection': projection,
                                 'actual_store_paths': sorted(image['store_paths'])})
            archive.unlink()  # Only this exact newly created decompressed transport file.
            print('IMAGE_SBOM_IMAGE_RECORDED image=' + name + ' artifacts=' + str(claims['artifacts']), flush=True)
        isolated_tool([tools['sbomnix']['executable'], native_root['path'], '--exclude-meta', '--exclude-cpe-matching',
                       '--cdx', str(scratch / 'native.cdx.json'), '--spdx', str(scratch / 'native.spdx.json'),
                       '--csv', str(scratch / 'native.csv')], tools, scratch, records)
        for output in ('native.cdx.json', 'native.spdx.json', 'native.csv'):
            payloads[output] = layout.read_small(scratch, output, MAX_DOCUMENT)
        native_projection = reconcile_native_cdx(layout.json_bytes(payloads['native.cdx.json']), nodes, native_root['deriver'])
        receipt = schema_validation(payloads, scratch, tools['unshare'])
        suite = unittest.TestLoader().discover(str(ROOT / 'tests'), pattern='test_image_sbom.py')
        output = io.StringIO()
        result = unittest.TextTestRunner(stream=output).run(suite)
        require(result.testsRun >= 10 and result.wasSuccessful() and not result.skipped, 'image SBOM controls failed: ' + output.getvalue())
        require(hashes == {name: sha256((ROOT / name).read_bytes()) for name in sources}, 'SBOM source changed during observation')
        for image in images:
            require(inspect(image['archive'], expected_image=image['image']) == image['outer'], 'archive changed during SBOM observation')
        report = {'schema_version': 1, 'evidence_class': 'local-actual-image-and-nix-standard-sbom-inventory',
                  'observed_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  'source': {'commit': run(['git', 'rev-parse', 'HEAD']).strip(), 'dirty': bool(run(['git', 'status', '--porcelain']))},
                  'source_inputs': hashes, 'command': [sys.executable, *sys.argv], 'tools': tool_record,
                  'input_build_index': {'path': str(args.build_index), 'sha256': sha256(args.build_index.read_bytes())},
                  'input_filesystem_report': {'path': str(args.filesystem_report), 'sha256': sha256(args.filesystem_report.read_bytes())},
                  'images': observations, 'native_reference_root': native_root, 'native_nodes': nodes,
                  'image_store_byte_binding': host_binding, 'native_standard_projection': native_projection,
                  'commands': records, 'schema_validation': receipt,
                  'payloads': {name: {'sha256': sha256(data), 'bytes': len(data)} for name, data in sorted(payloads.items())},
                  'checks': len(images), 'tests': result.testsRun, 'duration_seconds': time.monotonic() - started,
                  'inventory_complete': False, 'native_notice_classification_complete': False,
                  'legal_approval': False, 'runtime_qualified': False, 'independent_offhost_qualified': False,
                  'production_activation': False,
                  'scope': 'Raw maintained Syft image/CycloneDX and sbomnix native CycloneDX/SPDX/CSV plus actual image-to-store bytes, NAR/recipe/output/reference reconciliation. Notices are exact filename candidates; licences, source offers, runtime/build/helper/backup and full inventory/phase qualification remain pending.'}
        def validated(data):
            for row in receipt['documents']:
                require(row['valid'] and sha256(data[row['name']]) == row['sha256'], 'schema receipt/input substitution')
        if args.record_evidence:
            target = publish_validated(report, payloads, validated)
            print('IMAGE_SBOM_EVIDENCE report=' + str(target.relative_to(ROOT)) + ' sha256=' + sha256(target.read_bytes()))
    print(f'IMAGE_SBOM_LOCAL_RECORDED checks=4 tests={result.testsRun} duration_seconds={time.monotonic() - started:.3f}')
    print('PENDING_FULL_INVENTORY: native notices/legal/runtime/build/helper/backup and complete acceptance remain unresolved')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        print('IMAGE_SBOM_FAIL: ' + str(error), file=sys.stderr)
        raise SystemExit(1)
