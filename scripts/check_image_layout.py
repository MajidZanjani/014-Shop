#!/usr/bin/env python3
"""Convert inspected local archives and verify umoci reconstruction; run no payload.

This deliberately accepts only the candidate subset observed by the layer
inventory. It is not a general OCI validator or a runtime qualification driver.
"""
import argparse
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

from inspect_image_archive import CANDIDATE_IMAGES, inspect, unique
from inventory_image_payload import MAX_ENTRIES, MAX_MANIFEST, canonical
from audit_licence_gaps import ROOT, require, sha256

MAX_JSON = 1024**2
MAX_EXPANDED = 4 * 1024**3
MANIFEST_MEDIA = 'application/vnd.oci.image.manifest.v1+json'
CONFIG_MEDIA = 'application/vnd.oci.image.config.v1+json'
LAYER_MEDIA = 'application/vnd.oci.image.layer.v1.tar'
IDENTITY = ('st_dev', 'st_ino', 'st_mode', 'st_size', 'st_mtime_ns', 'st_ctime_ns')


@contextmanager
def beneath(root, name):
    """Open each directory separately, without following any host symlink."""
    parts = PurePosixPath(name).parts
    require(parts and not name.startswith('/') and '..' not in parts, 'unsafe relative input')
    descriptor = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        for part in parts[:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                            dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        child = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
                        dir_fd=descriptor)
        with os.fdopen(child, 'rb') as stream:
            before = os.fstat(stream.fileno())
            require(stat.S_ISREG(before.st_mode), 'regular file required')
            yield stream, before
            after = os.fstat(stream.fileno())
            named = os.stat(parts[-1], dir_fd=descriptor, follow_symlinks=False)
            require(all(getattr(before, key) == getattr(after, key) == getattr(named, key)
                        for key in IDENTITY), 'input changed during read')
    finally:
        os.close(descriptor)


def read_small(root, name, maximum=MAX_JSON):
    with beneath(root, name) as (stream, info):
        require(0 < info.st_size <= maximum, 'metadata byte bound exceeded')
        data = stream.read(maximum + 1)
        require(len(data) == info.st_size, 'metadata length mismatch')
    return data


def json_bytes(data):
    return json.loads(data, object_pairs_hook=unique,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError('nonfinite JSON')))


def descriptor_name(descriptor, media_types, *, reference=False):
    fields = {'mediaType', 'digest', 'size'} | ({'annotations'} if reference else set())
    require(type(descriptor) is dict and set(descriptor) == fields, 'closed local descriptor required')
    require(descriptor['mediaType'] in media_types and type(descriptor['size']) is int
            and 0 < descriptor['size'] <= MAX_EXPANDED, 'descriptor media/size invalid')
    require(type(descriptor['digest']) is str
            and re.fullmatch(r'sha256:[0-9a-f]{64}', descriptor['digest']), 'descriptor digest invalid')
    if reference:
        require(descriptor['annotations'] == {'org.opencontainers.image.ref.name': 'candidate'},
                'exact candidate reference required')
    return 'blobs/sha256/' + descriptor['digest'][7:]


def metadata_blob(root, descriptor, media, *, reference=False):
    name = descriptor_name(descriptor, {media}, reference=reference)
    data = read_small(root, name)
    require(len(data) == descriptor['size'] and 'sha256:' + sha256(data) == descriptor['digest'],
            'descriptor byte/hash mismatch')
    return data


def compare_config(source, converted, path='', changes=None):
    """Retain and explain only Skopeo's observed UTC timestamp serialization."""
    changes = {} if changes is None else changes
    require(type(source) is type(converted), 'converted configuration type substitution: ' + path)
    if source == converted:
        return changes
    if type(source) is dict:
        require(source.keys() == converted.keys(), 'converted configuration field substitution: ' + path)
        for key in source:
            compare_config(source[key], converted[key], path + '/' + key if path else key, changes)
    elif type(source) is list:
        require(len(source) == len(converted), 'converted configuration list substitution: ' + path)
        for number, (left, right) in enumerate(zip(source, converted, strict=True)):
            compare_config(left, right, path + '/' + str(number), changes)
    else:
        require(type(source) is str and (path == 'created' or re.fullmatch(r'history/[0-9]+/created', path))
                and re.fullmatch(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?\+00:00', source)
                and converted == source[:-6] + 'Z', 'converted configuration value substitution: ' + path)
        # Preserve both spellings and the complete raw documents/digests. This is
        # an explained format conversion, never payload mismatch normalization.
        changes[path] = {'source': source, 'converted': converted}
    return changes


def verify_layout(layout, outer):
    """Hash every local descriptor and ordered uncompressed layer, independently."""
    layout_raw = read_small(layout, 'oci-layout')
    require(json_bytes(layout_raw) == {'imageLayoutVersion': '1.0.0'}, 'unsupported local layout')
    index_raw = read_small(layout, 'index.json')
    index = json_bytes(index_raw)
    require(type(index) is dict and set(index) <= {'schemaVersion', 'mediaType', 'manifests'}
            and type(index.get('schemaVersion')) is int and index['schemaVersion'] == 2
            and index.get('mediaType', 'application/vnd.oci.image.index.v1+json') == 'application/vnd.oci.image.index.v1+json'
            and type(index.get('manifests')) is list and len(index['manifests']) == 1,
            'one closed local image index required')
    image = index['manifests'][0]
    manifest_raw = metadata_blob(layout, image, MANIFEST_MEDIA, reference=True)
    manifest = json_bytes(manifest_raw)
    require(type(manifest) is dict and set(manifest) == {'schemaVersion', 'mediaType', 'config', 'layers'}
            and type(manifest['schemaVersion']) is int and manifest['schemaVersion'] == 2
            and manifest['mediaType'] == MANIFEST_MEDIA, 'unsupported local image manifest')
    config_raw = metadata_blob(layout, manifest['config'], CONFIG_MEDIA)
    config = json_bytes(config_raw)
    config_changes = compare_config(outer['config'], config)
    layers = manifest['layers']
    require(type(layers) is list and 0 < len(layers) == len(outer['layers']), 'ordered layer count mismatch')
    observed = []
    total = 0
    for descriptor, original in zip(layers, outer['layers'], strict=True):
        name = descriptor_name(descriptor, {LAYER_MEDIA, LAYER_MEDIA + '+gzip'})
        with beneath(layout, name) as (source, info):
            require(info.st_size == descriptor['size'], 'layer descriptor size mismatch')
            digest = hashlib.sha256()
            while chunk := source.read(1024**2):
                digest.update(chunk)
            require('sha256:' + digest.hexdigest() == descriptor['digest'], 'layer descriptor hash mismatch')
            source.seek(0)
            magic = source.read(2)
            source.seek(0)
            require((magic == b'\x1f\x8b') == descriptor['mediaType'].endswith('+gzip'),
                    'compression/media mismatch for ' + descriptor['digest'] + ' media=' + descriptor['mediaType']
                    + ' header_hex=' + magic.hex())
            reader = gzip.GzipFile(fileobj=source) if descriptor['mediaType'].endswith('+gzip') else source
            diff = hashlib.sha256()
            size = 0
            try:
                while chunk := reader.read(1024**2):
                    size += len(chunk)
                    total += len(chunk)
                    require(total <= MAX_EXPANDED, 'expanded layer byte bound exceeded')
                    diff.update(chunk)
            finally:
                if reader is not source:
                    reader.close()
            require('sha256:' + diff.hexdigest() == original['diff_id'], 'ordered layer DiffID mismatch')
            observed.append({**descriptor, 'diff_id': original['diff_id'], 'uncompressed_bytes': size})
    require(config['rootfs']['diff_ids'] == [row['diff_id'] for row in observed], 'config/layer DiffID mismatch')
    return {'manifest_digest': image['digest'], 'config_digest': manifest['config']['digest'],
            'config': config, 'configuration_conversion': config_changes, 'layers': observed,
            'documents': {'oci-layout': layout_raw.decode(), 'index.json': index_raw.decode(),
                          'manifest.json': manifest_raw.decode(), 'config.json': config_raw.decode()}}


def resolve_in_root(root, name):
    """Resolve image absolute/relative symlinks without host-root path resolution."""
    require(type(name) is str and name.startswith('/') and len(name) <= 4096
            and '\\' not in name and all(32 <= ord(c) < 127 for c in name), 'unsafe image path')
    pending = name.split('/')[1:]
    resolved = []
    links = 0
    root_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        while pending:
            component = pending.pop(0)
            if component in ('', '.'):
                continue
            if component == '..':
                require(bool(resolved), 'image link escapes root')
                resolved.pop()
                continue
            parent = os.dup(root_fd)
            try:
                for part in resolved:
                    child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                                    dir_fd=parent)
                    os.close(parent)
                    parent = child
                info = os.stat(component, dir_fd=parent, follow_symlinks=False)
                if stat.S_ISLNK(info.st_mode):
                    links += 1
                    require(links <= 40, 'image symlink cycle/depth exceeded')
                    target = os.readlink(component, dir_fd=parent)
                    require(0 < len(target) <= 4096 and '\\' not in target
                            and all(32 <= ord(c) < 127 for c in target), 'unsafe image link target')
                    if target.startswith('/'):
                        resolved = []
                    pending = target.split('/') + pending
                    require(sum(map(len, pending)) <= 16384, 'image link expansion exceeded')
                else:
                    require(stat.S_ISDIR(info.st_mode) or not pending, 'image non-directory path parent')
                    resolved.append(component)
            finally:
                os.close(parent)
        require(bool(resolved), 'image root is not a regular resource')
        return '/'.join(resolved)
    finally:
        os.close(root_fd)


def rooted_file(root, name):
    resolved = resolve_in_root(root, name)
    with beneath(root, resolved) as (stream, info):
        require(info.st_size <= MAX_EXPANDED, 'image file byte bound exceeded')
        digest = hashlib.sha256()
        size = 0
        while chunk := stream.read(1024**2):
            size += len(chunk)
            require(size <= info.st_size, 'image file changed length')
            digest.update(chunk)
        require(size == info.st_size, 'image file length mismatch')
        return {'path': name, 'resolved_path': '/' + resolved, 'bytes': size, 'sha256': digest.hexdigest(),
                'mode': stat.S_IMODE(info.st_mode), 'file_identity': [info.st_dev, info.st_ino]}


def validate_reconstruction(counts):
    require(type(counts) is dict and set(counts) == {'files', 'directories', 'symlinks', 'bytes'}
            and all(type(value) is int and value >= 0 for value in counts.values())
            and counts['files'] > 0 and counts['directories'] > 0 and counts['bytes'] > 0,
            'nonempty actual reconstruction required')


def inventory_root(root):
    root_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        root_info = os.fstat(root_fd)
        entries = [{'path': '.', 'type': 'directory', 'mode': stat.S_IMODE(root_info.st_mode),
                    'mtime_ns': root_info.st_mtime_ns, 'observed_uid': root_info.st_uid,
                    'observed_gid': root_info.st_gid}]
        counts = {'files': 0, 'directories': 1, 'symlinks': 0, 'bytes': 0}
        for current, directories, files, descriptor in os.fwalk('.', follow_symlinks=False, dir_fd=root_fd):
            for name in sorted(directories + files):
                path = str(PurePosixPath(current) / name)
                require(canonical(path) == path and len(entries) < MAX_ENTRIES, 'reconstruction path/count bound')
                info = os.stat(name, dir_fd=descriptor, follow_symlinks=False)
                row = {'path': path, 'mode': stat.S_IMODE(info.st_mode), 'mtime_ns': info.st_mtime_ns,
                       'observed_uid': info.st_uid, 'observed_gid': info.st_gid}
                if stat.S_ISREG(info.st_mode):
                    item = rooted_file(root, '/' + path)
                    row.update(type='file', size=item['bytes'], sha256=item['sha256'])
                    counts['files'] += 1
                    counts['bytes'] += item['bytes']
                    require(counts['bytes'] <= MAX_EXPANDED, 'reconstructed byte bound exceeded')
                elif stat.S_ISDIR(info.st_mode):
                    row['type'] = 'directory'
                    counts['directories'] += 1
                elif stat.S_ISLNK(info.st_mode):
                    row.update(type='symlink', link_target=os.readlink(name, dir_fd=descriptor))
                    counts['symlinks'] += 1
                else:
                    raise ValueError('unexpected reconstructed special file')
                entries.append(row)
    finally:
        os.close(root_fd)
    validate_reconstruction(counts)
    return counts, sorted(entries, key=lambda row: row['path'])


def compare_reconstruction(entries, payload):
    """This candidate subset has only additive files/links and repeated directories."""
    expected = {}
    for layer in payload['layers']:
        for entry in layer['entries']:
            path = entry['path']
            require(entry['type'] in {'directory', 'file', 'symlink'}
                    and not PurePosixPath(path).name.startswith('.wh.')
                    and set(entry['pax_headers']) <= {'path', 'linkpath'}, 'unsupported candidate layer semantics')
            require(path not in expected or entry['type'] == expected[path]['type'] == 'directory',
                    'non-directory overlay needs separate qualification')
            expected[path] = entry
    actual = {entry['path']: entry for entry in entries}
    require(len(actual) == len(entries), 'duplicate reconstruction path')
    implicit = {str(parent) for name in expected for parent in PurePosixPath(name).parents if str(parent) != '.'}
    missing = (set(expected) | implicit) - set(actual)
    extra = set(actual) - (set(expected) | implicit)
    require(not missing and not extra, 'reconstructed path set mismatch: ' + json.dumps({
        'missing_count': len(missing), 'extra_count': len(extra),
        'missing_sample': [name[:256] for name in sorted(missing)[:10]],
        'extra_sample': [name[:256] for name in sorted(extra)[:10]]}))
    for path in implicit - set(expected):
        require(actual[path]['type'] == 'directory', 'implicit parent is not a directory')
    for path, original in expected.items():
        item = actual[path]
        require(item['type'] == original['type'] and item['mode'] == original['mode'],
                'reconstructed type/mode mismatch: ' + path)
        require(item['mtime_ns'] == int(original['mtime'] * 10**9), 'reconstructed mtime mismatch: ' + path)
        if item['type'] == 'file':
            require(item['size'] == original['size'] and item['sha256'] == original['sha256'],
                    'reconstructed file bytes mismatch: ' + path)
        elif item['type'] == 'symlink':
            require(item['link_target'] == original['link_target_unresolved'], 'reconstructed link target mismatch')
    return len(expected)


def critical_paths(root, image, outer, entries):
    paths = ['/etc/passwd', '/etc/group', outer['config']['config']['Cmd'][0]]
    if image in ('shop-app', 'shop-worker'):
        source_prefixes = {row['path'].split('/app/', 1)[0] + '/app/' for row in entries
                           if '-shop-python-source/app/' in row['path']}
        require(len(source_prefixes) == 1, 'one exact packaged application source required')
        prefix = next(iter(source_prefixes))
        files = [row for row in entries if row['type'] == 'file' and row['path'].startswith(prefix)]
        require(len(files) > 0, 'packaged application source missing')
        for row in files:
            path = '/app/' + row['path'][len(prefix):]
            require(rooted_file(root, path)['sha256'] == row['sha256'], 'application alias source mismatch')
            paths.append(path)
    elif image == 'shop-postgres':
        paths.extend(outer['config']['config']['Cmd'][2:4])
    else:
        paths.append('/etc/shop/Caddyfile')
    result = []
    for name in dict.fromkeys(paths):
        row = rooted_file(root, name)
        row.pop('file_identity')
        result.append(row)
    command = result[2]
    require(command['bytes'] > 0 and command['mode'] & 0o111, 'candidate command not executable')
    return result


def checked_tool_manifest(path):
    require(re.fullmatch(r'/nix/store/[0-9a-df-np-sv-z]{32}-shop-image-tool-manifest.json', str(path)),
            'immutable pinned tool manifest required')
    raw = read_small(path.parent, path.name)
    value = json_bytes(raw)
    require(set(value) == {'schema_version', 'skopeo', 'umoci', 'unshare'}
            and type(value['schema_version']) is int and value['schema_version'] == 1, 'closed tool manifest required')
    records = {}
    for name in ('skopeo', 'umoci'):
        entry = value[name]
        require(set(entry) == {'executable', 'version'}
                and re.fullmatch(r'/nix/store/[0-9a-df-np-sv-z]{32}-' + name + r'-[^/]+/bin/' + name,
                                 entry['executable']), 'exact pinned executable required')
        version = subprocess.check_output([entry['executable'], '--version'], text=True, timeout=5,
                                          env={'LANG': 'C', 'LC_ALL': 'C'})
        require(version.splitlines()[0] == name + ' version ' + entry['version'], 'actual tool version mismatch')
        records[name] = {**entry, 'actual_version': version, 'sha256': sha256(Path(entry['executable']).read_bytes())}
    require(re.fullmatch(r'/nix/store/[0-9a-df-np-sv-z]{32}-util-linux-[^/]+-bin/bin/unshare', value['unshare'])
            or re.fullmatch(r'/nix/store/[0-9a-df-np-sv-z]{32}-util-linux-[^/]+/bin/unshare', value['unshare']),
            'pinned namespace tool required')
    records['unshare'] = {'executable': value['unshare'], 'sha256': sha256(Path(value['unshare']).read_bytes())}
    return value, {'path': str(path), 'sha256': sha256(raw), 'tools': records}


def run_tool(command, tools, scratch, commands, *, timeout):
    isolated = [tools['unshare'], '--user', '--map-user=1000', '--map-group=1000', '--net', '--', *command]
    env = {'HOME': str(scratch / 'home'), 'TMPDIR': str(scratch / 'tmp'),
           'XDG_RUNTIME_DIR': str(scratch / 'run'), 'XDG_CONFIG_HOME': str(scratch / 'config'),
           'REGISTRY_AUTH_FILE': str(scratch / 'auth.json'),
           'CONTAINERS_REGISTRIES_CONF': str(scratch / 'registries.conf'),
           'LANG': 'C', 'LC_ALL': 'C', 'TZ': 'UTC', 'GOMAXPROCS': '2'}
    started = time.monotonic()
    result = subprocess.run(isolated, env=env, cwd=scratch, capture_output=True, text=True, timeout=timeout)
    observation = {'command': isolated, 'exit_code': result.returncode,
                   'duration_seconds': time.monotonic() - started,
                   'stdout': result.stdout, 'stderr': result.stderr}
    require(len(result.stdout) + len(result.stderr) <= MAX_JSON, 'tool output bound exceeded')
    commands.append(observation)
    require(result.returncode == 0, 'local image tool failed: ' + json.dumps(observation))


def one_image(image, tools, scratch):
    name = image['image']
    outer_path = ROOT / image['outer_report']['path']
    outer_raw = read_small(outer_path.parent, outer_path.name)
    require(sha256(outer_raw) == image['outer_report']['sha256'] == outer_path.stem, 'outer report identity mismatch')
    outer = json_bytes(outer_raw)
    archive = Path(image['archive_path'])
    require(inspect(archive, expected_image=name) == outer, 'actual input archive/report substitution')
    report_path = ROOT / image['payload_report']['path']
    report_raw = read_small(report_path.parent, report_path.name)
    require(sha256(report_raw) == image['payload_report']['sha256'] == report_path.stem, 'payload report identity mismatch')
    prior = json_bytes(report_raw)
    require(prior['outer_report_sha256'] == sha256(outer_raw), 'payload/outer report mismatch')
    payload_path = ROOT / 'docs/evidence/t02' / prior['payload_manifest']['path']
    compressed = read_small(payload_path.parent, payload_path.name, MAX_MANIFEST)
    require(sha256(compressed) == prior['payload_manifest']['sha256'], 'payload manifest identity mismatch')
    with gzip.GzipFile(fileobj=io.BytesIO(compressed)) as stream:
        payload_raw = stream.read(MAX_MANIFEST + 1)
    require(len(payload_raw) <= MAX_MANIFEST and sha256(payload_raw) == prior['payload_manifest']['uncompressed_sha256'],
            'bounded payload manifest mismatch')
    payload = json_bytes(payload_raw)
    require(payload['archive_sha256'] == outer['archive_sha256'] == image['archive_sha256']
            and payload['config_image_id'] == outer['config_image_id'], 'candidate identity mismatch')
    commands = []
    for directory in ('home', 'tmp', 'run', 'config'):
        (scratch / directory).mkdir(mode=0o700)
    (scratch / 'auth.json').write_text('{}')
    (scratch / 'registries.conf').write_text('unqualified-search-registries=[]\n')
    policy = scratch / 'policy.json'
    policy.write_text(json.dumps({'default': [{'type': 'reject'}],
                                 'transports': {'docker-archive': {'': [{'type': 'insecureAcceptAnything'}]}}}))
    layout = scratch / 'layout'
    run_tool([tools['skopeo']['executable'], '--policy', str(policy), 'copy', '--format', 'oci',
              '--dest-compress-format', 'gzip', '--dest-force-compress-format',
              '--authfile', str(scratch / 'auth.json'),
              'docker-archive:' + str(archive), 'oci:' + str(layout) + ':candidate'], tools, scratch, commands, timeout=120)
    observed = verify_layout(layout, outer)
    bundle = scratch / 'bundle'
    run_tool([tools['umoci']['executable'], 'unpack', '--rootless', '--image', str(layout) + ':candidate', str(bundle)],
             tools, scratch, commands, timeout=120)
    counts, entries = inventory_root(bundle / 'rootfs')
    matched = compare_reconstruction(entries, payload)
    critical = critical_paths(bundle / 'rootfs', name, outer, entries)
    # Recheck immutable source after the tools finish; no caller-provided digest is
    # substituted for the actual archive bytes.
    require(inspect(archive, expected_image=name) == outer, 'input archive changed during conversion')
    filesystem = (json.dumps({'schema_version': 1, 'entries': entries}, sort_keys=True, separators=(',', ':')) + '\n').encode()
    compressed_filesystem = gzip.compress(filesystem, mtime=0)
    return {'image': name, 'source_archive': {'path': str(archive), 'sha256': outer['archive_sha256']},
            'source_outer_report': image['outer_report'], 'source_payload_report': image['payload_report'],
            'source_config_image_id': outer['config_image_id'], 'local_oci_manifest_digest': observed['manifest_digest'],
            'local_oci_config_digest': observed['config_digest'], 'layers': observed['layers'],
            'configuration_conversion': observed['configuration_conversion'],
            'documents': observed['documents'], 'commands': commands, 'reconstructed': counts,
            'matched_explicit_layer_paths': matched, 'critical_paths': critical,
            'filesystem_manifest': {'sha256': sha256(compressed_filesystem), 'compressed_bytes': len(compressed_filesystem),
                                    'uncompressed_sha256': sha256(filesystem), 'uncompressed_bytes': len(filesystem)},
            'rootless_uid_gid_metadata_qualified': False, 'runtime_qualified': False}, compressed_filesystem


def publish(report, payloads):
    unique_payloads = {}
    for name, data in payloads:
        require(type(name) is str and type(data) is bytes and name == sha256(data) + '.json.gz',
                'filesystem payload content address mismatch')
        require(name not in unique_payloads or unique_payloads[name] == data, 'conflicting shared payload identity')
        unique_payloads[name] = data
    directory = ROOT / 'docs/evidence/t02/image-layout-revisions'
    require(not directory.is_symlink(), 'evidence directory symlink denied')
    directory.mkdir(exist_ok=True)
    encoded = (json.dumps(report, indent=2) + '\n').encode()
    destination = directory / sha256(encoded)
    destination.mkdir(exist_ok=False)
    # Identical app/worker filesystems share one exact payload. Write the report
    # only after every unique payload is present and read back successfully.
    for name, data in [*sorted(unique_payloads.items()), ('report.json', encoded)]:
        require('/' not in name and '\\' not in name, 'unsafe evidence filename')
        with (destination / name).open('xb') as stream:
            stream.write(data)
        require((destination / name).read_bytes() == data, 'evidence readback mismatch')
    return destination / 'report.json'


def owned_scratch_parent(path):
    path = Path(path)
    require(path.is_absolute() and path.resolve() == path, 'absolute nonsymlink scratch parent required')
    info = path.lstat()
    require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.geteuid()
            and not stat.S_IMODE(info.st_mode) & 0o022, 'dedicated caller-owned scratch parent required')
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-index', type=Path, required=True)
    parser.add_argument('--tool-manifest', type=Path, default=os.environ.get('SHOP_IMAGE_TOOL_MANIFEST'))
    parser.add_argument('--scratch-parent', type=Path, default=ROOT / '.scratch',
                        help='existing dedicated owned parent traversable by the isolated tool; permissions are never changed')
    parser.add_argument('--record-evidence', action='store_true')
    args = parser.parse_args()
    require(args.tool_manifest is not None, 'pinned image-tool shell/manifest required')
    started = time.monotonic()
    sources = ['scripts/check_image_layout.py', 'tests/test_image_layout.py',
               'scripts/inspect_image_archive.py', 'scripts/inventory_image_payload.py',
               'ops/nixos/flake.nix', 'ops/nixos/flake.lock']
    source_hashes = {name: sha256((ROOT / name).read_bytes()) for name in sources}
    tools, tool_record = checked_tool_manifest(args.tool_manifest)
    index_raw = read_small(args.build_index.parent, args.build_index.name)
    require(args.build_index.name == sha256(index_raw) + '.json', 'build index content address mismatch')
    index = json_bytes(index_raw)
    images = index['images']
    require(index['evidence_class'] == 'local-four-candidate-image-build-and-inspection'
            and type(images) is list and [image['image'] for image in images] == list(CANDIDATE_IMAGES),
            'four exact ordered candidate images required')
    owned = owned_scratch_parent(args.scratch_parent)
    observations, payloads = [], []
    for image in images:
        require(shutil.disk_usage(owned).free > 1024**3, 'one GiB free owned scratch required')
        with tempfile.TemporaryDirectory(prefix='image-layout-', dir=owned) as temporary:
            result, payload = one_image(image, tools, Path(temporary))
            name = result['filesystem_manifest']['sha256'] + '.json.gz'
            result['filesystem_manifest']['path'] = name
            payloads.append((name, payload))
            observations.append(result)
            print('IMAGE_LAYOUT_IMAGE_PASS image=' + image['image'] + ' paths=' + str(result['matched_explicit_layer_paths']), flush=True)
    suite = unittest.TestLoader().discover(str(ROOT / 'tests'), pattern='test_image_layout.py')
    output = io.StringIO()
    result = unittest.TextTestRunner(stream=output).run(suite)
    require(result.testsRun >= 19 and result.wasSuccessful() and not result.skipped, 'image layout controls failed: ' + output.getvalue())
    require(source_hashes == {name: sha256((ROOT / name).read_bytes()) for name in sources},
            'producer/tooling source changed during observation')
    report = {'schema_version': 1, 'evidence_class': 'local-standard-tool-oci-conversion-and-rootless-reconstruction',
              'observed_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'source': {'commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                         'dirty': bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT))},
              'producer_sha256': sha256(Path(__file__).read_bytes()),
              'source_inputs': source_hashes, 'command': [sys.executable, *sys.argv],
              'flake_lock_sha256': sha256((ROOT / 'ops/nixos/flake.lock').read_bytes()),
              'build_index': {'path': str(args.build_index), 'sha256': sha256(index_raw)},
              'scratch_parent': str(owned),
              'tools': tool_record, 'images': observations, 'checks': len(observations), 'tests': result.testsRun,
              'duration_seconds': time.monotonic() - started, 'network_denied_for_conversion_and_unpack': True,
              'payload_execution_performed': False, 'registry_push_performed': False,
              'rootless_runtime_qualified': False, 'independent_offhost_qualified': False,
              'native_notice_inventory_complete': False, 'legal_approval': False,
              'two_independent_image_builds_compared': False, 'production_activation': False,
              'scope': 'Actual local OCI descriptors/DiffIDs and umoci rootless reconstruction match the additive candidate bytes, paths, modes, mtimes and links. Rootless uid/gid/xattr semantics and full runtime/independent/legal/build-comparison qualification remain pending.'}
    if args.record_evidence:
        path = publish(report, payloads)
        print('IMAGE_LAYOUT_EVIDENCE report=' + str(path.relative_to(ROOT)) + ' sha256=' + sha256(path.read_bytes()))
    print(f'IMAGE_LAYOUT_LOCAL_PASS checks={len(observations)} tests={result.testsRun} images={len(observations)} duration_seconds={time.monotonic() - started:.3f}')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        print('IMAGE_LAYOUT_FAIL: ' + str(error), file=sys.stderr)
        raise SystemExit(1)
