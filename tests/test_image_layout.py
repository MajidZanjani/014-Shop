"""Descriptor and image-root checks use synthetic bytes, never a runtime daemon."""
import copy
import gzip
import hashlib
import importlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))


class LayoutTests(unittest.TestCase):
    def producer(self):
        try:
            return importlib.import_module('check_image_layout')
        except ModuleNotFoundError as error:
            if error.name != 'check_image_layout':
                raise
            self.fail('Pinned-tool OCI layout/filesystem verification is not implemented')

    def fixture(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        layout = root / 'layout'
        blobs = layout / 'blobs/sha256'
        blobs.mkdir(parents=True)
        layer = b'bounded synthetic uncompressed layer bytes'
        diff_id = 'sha256:' + hashlib.sha256(layer).hexdigest()
        config = {'architecture': 'amd64', 'os': 'linux',
                  'created': '1970-01-01T00:00:01+00:00',
                  'config': {'User': '10001:10001', 'WorkingDir': '/app',
                             'Cmd': ['/app/run'], 'Env': ['SYNTHETIC=1']},
                  'rootfs': {'type': 'layers', 'diff_ids': [diff_id]}}

        def blob(data, media):
            digest = hashlib.sha256(data).hexdigest()
            (blobs / digest).write_bytes(data)
            return {'mediaType': media, 'digest': 'sha256:' + digest, 'size': len(data)}

        manifest = {'schemaVersion': 2, 'mediaType': 'application/vnd.oci.image.manifest.v1+json',
                    'config': blob(json.dumps(config).encode(), 'application/vnd.oci.image.config.v1+json'),
                    'layers': [blob(gzip.compress(layer, mtime=0), 'application/vnd.oci.image.layer.v1.tar+gzip')]}
        descriptor = blob(json.dumps(manifest).encode(), manifest['mediaType'])
        descriptor['annotations'] = {'org.opencontainers.image.ref.name': 'candidate'}
        index = {'schemaVersion': 2, 'manifests': [descriptor]}
        (layout / 'oci-layout').write_text('{"imageLayoutVersion":"1.0.0"}')
        (layout / 'index.json').write_text(json.dumps(index))
        outer = {'config': copy.deepcopy(config), 'layers': [{'diff_id': diff_id}]}
        return root, layout, blobs, index, manifest, outer, layer

    def test_real_descriptor_bytes_sizes_config_and_ordered_diff_ids_are_verified(self):
        producer = self.producer()
        root, layout, blobs, index, manifest, outer, layer = self.fixture()
        result = producer.verify_layout(layout, outer)
        self.assertEqual(result['manifest_digest'], index['manifests'][0]['digest'])
        self.assertEqual(result['layers'][0]['diff_id'], outer['layers'][0]['diff_id'])
        self.assertEqual(result['layers'][0]['uncompressed_bytes'], len(layer))
        self.assertEqual(result['config'], outer['config'])

    def test_changed_layer_byte_is_rejected(self):
        producer = self.producer()
        root, layout, blobs, index, manifest, outer, layer = self.fixture()
        path = blobs / manifest['layers'][0]['digest'].split(':')[1]
        path.write_bytes(path.read_bytes()[:-1] + b'X')
        with self.assertRaises(ValueError):
            producer.verify_layout(layout, outer)

    def test_uncompressed_tar_cannot_be_labelled_as_gzip(self):
        producer = self.producer()
        root, layout, blobs, index, manifest, outer, layer = self.fixture()
        digest = hashlib.sha256(layer).hexdigest()
        (blobs / digest).write_bytes(layer)
        manifest['layers'][0].update(digest='sha256:' + digest, size=len(layer))
        raw = json.dumps(manifest).encode()
        digest = hashlib.sha256(raw).hexdigest()
        (blobs / digest).write_bytes(raw)
        index['manifests'][0].update(digest='sha256:' + digest, size=len(raw))
        (layout / 'index.json').write_text(json.dumps(index))
        with self.assertRaisesRegex(ValueError, 'compression/media mismatch'):
            producer.verify_layout(layout, outer)

    def test_wrong_descriptor_size_and_digest_traversal_are_rejected(self):
        producer = self.producer()
        for field, value in (('size', 1), ('digest', 'sha256:../../outside')):
            with self.subTest(field=field):
                root, layout, blobs, index, manifest, outer, layer = self.fixture()
                index['manifests'][0][field] = value
                (layout / 'index.json').write_text(json.dumps(index))
                with self.assertRaises(ValueError):
                    producer.verify_layout(layout, outer)

    def test_symlinked_blob_parent_or_blob_is_rejected(self):
        producer = self.producer()
        for kind in ('parent', 'file'):
            with self.subTest(kind=kind):
                root, layout, blobs, index, manifest, outer, layer = self.fixture()
                if kind == 'parent':
                    actual = root / 'outside-blobs'
                    blobs.rename(actual)
                    blobs.symlink_to(actual, target_is_directory=True)
                else:
                    path = blobs / manifest['config']['digest'].split(':')[1]
                    actual = root / 'outside-config'
                    path.rename(actual)
                    path.symlink_to(actual)
                with self.assertRaises((ValueError, OSError)):
                    producer.verify_layout(layout, outer)

    def test_config_or_ordered_diff_id_substitution_is_rejected(self):
        producer = self.producer()
        for kind in ('config', 'layer'):
            with self.subTest(kind=kind):
                root, layout, blobs, index, manifest, outer, layer = self.fixture()
                if kind == 'config':
                    outer['config']['config']['User'] = '0'
                else:
                    outer['layers'][0]['diff_id'] = 'sha256:' + '0' * 64
                with self.assertRaises(ValueError):
                    producer.verify_layout(layout, outer)

    def test_only_demonstrated_utc_timestamp_spelling_change_is_allowed_and_reported(self):
        producer = self.producer()
        for timestamp, accepted in (('1970-01-01T00:00:01Z', True),
                                    ('1970-01-01T00:00:02Z', False),
                                    ('1970-01-01 00:00:01Z', False)):
            with self.subTest(timestamp=timestamp):
                root, layout, blobs, index, manifest, outer, layer = self.fixture()
                converted = copy.deepcopy(outer['config'])
                converted['created'] = timestamp
                raw = json.dumps(converted).encode()
                digest = hashlib.sha256(raw).hexdigest()
                (blobs / digest).write_bytes(raw)
                manifest['config'].update(digest='sha256:' + digest, size=len(raw))
                raw = json.dumps(manifest).encode()
                digest = hashlib.sha256(raw).hexdigest()
                (blobs / digest).write_bytes(raw)
                index['manifests'][0].update(digest='sha256:' + digest, size=len(raw))
                (layout / 'index.json').write_text(json.dumps(index))
                if accepted:
                    result = producer.verify_layout(layout, outer)
                    self.assertEqual(result['configuration_conversion']['created'],
                                     {'source': outer['config']['created'], 'converted': timestamp})
                else:
                    with self.assertRaises(ValueError):
                        producer.verify_layout(layout, outer)

    def test_duplicate_json_unknown_media_external_urls_and_expansion_bound_reject(self):
        producer = self.producer()
        from unittest.mock import patch
        root, layout, blobs, index, manifest, outer, layer = self.fixture()
        with patch.object(producer, 'MAX_EXPANDED', 1), self.assertRaises(ValueError):
            producer.verify_layout(layout, outer)
        (layout / 'index.json').write_text('{"schemaVersion":2,"schemaVersion":2,"manifests":[]}')
        with self.assertRaises(ValueError):
            producer.verify_layout(layout, outer)
        for field, value in (('mediaType', 'application/unknown'), ('urls', ['https://invalid.example/blob'])):
            root, layout, blobs, index, manifest, outer, layer = self.fixture()
            index['manifests'][0][field] = value
            (layout / 'index.json').write_text(json.dumps(index))
            with self.assertRaises(ValueError):
                producer.verify_layout(layout, outer)

    def test_image_root_absolute_and_relative_links_resolve_inside_root(self):
        producer = self.producer()
        root, layout, blobs, index, manifest, outer, layer = self.fixture()
        filesystem = root / 'rootfs'
        target = filesystem / 'nix/store/synthetic/app'
        target.mkdir(parents=True)
        (target / 'run').write_bytes(b'synthetic executable')
        (filesystem / 'app').symlink_to('/nix/store/synthetic/app', target_is_directory=True)
        (target / 'alias').symlink_to('run')
        result = producer.rooted_file(filesystem, '/app/alias')
        self.assertEqual(result['resolved_path'], '/nix/store/synthetic/app/run')
        self.assertEqual(result['sha256'], hashlib.sha256(b'synthetic executable').hexdigest())

    def test_image_root_host_escape_cycle_and_missing_target_deny(self):
        producer = self.producer()
        root, layout, blobs, index, manifest, outer, layer = self.fixture()
        filesystem = root / 'rootfs'
        filesystem.mkdir()
        sentinel = root / 'private-host-canary'
        sentinel.write_bytes(b'HOST_PRIVATE_FIXTURE')
        (filesystem / 'escape').symlink_to('../private-host-canary')
        (filesystem / 'host-absolute').symlink_to(str(sentinel))
        (filesystem / 'cycle').symlink_to('cycle')
        for name in ('/escape', '/host-absolute', '/cycle', '/missing'):
            with self.subTest(name=name), self.assertRaises((ValueError, OSError)):
                producer.rooted_file(filesystem, name)

    def test_rooted_open_preserves_hardlink_identity_without_following_host_links(self):
        producer = self.producer()
        root, layout, blobs, index, manifest, outer, layer = self.fixture()
        filesystem = root / 'rootfs'
        filesystem.mkdir()
        (filesystem / 'file').write_bytes(b'synthetic')
        os.link(filesystem / 'file', filesystem / 'hard')
        first = producer.rooted_file(filesystem, '/file')
        second = producer.rooted_file(filesystem, '/hard')
        self.assertEqual(first['sha256'], second['sha256'])
        self.assertEqual(first['file_identity'], second['file_identity'])

    def test_failed_or_zero_count_reconstruction_cannot_publish_success(self):
        producer = self.producer()
        with self.assertRaises(ValueError):
            producer.validate_reconstruction({'files': 0, 'directories': 0, 'symlinks': 0, 'bytes': 0})
        with self.assertRaises(ValueError):
            producer.validate_reconstruction({'files': 1, 'directories': 1, 'symlinks': 0, 'bytes': 0})

    def test_scratch_parent_is_owned_nonsymlink_and_never_changes_existing_modes(self):
        producer = self.producer()
        root, layout, blobs, index, manifest, outer, layer = self.fixture()
        parent = root / 'owned'
        parent.mkdir(mode=0o711)
        self.assertEqual(producer.owned_scratch_parent(parent), parent)
        alias = root / 'alias'
        alias.symlink_to(parent, target_is_directory=True)
        with self.assertRaises(ValueError):
            producer.owned_scratch_parent(alias)
        parent.chmod(0o777)
        with self.assertRaises(ValueError):
            producer.owned_scratch_parent(parent)
        self.assertEqual(parent.stat().st_mode & 0o777, 0o777)

    def test_root_directory_metadata_is_part_of_complete_reconstruction(self):
        producer = self.producer()
        root, layout, blobs, index, manifest, outer, layer = self.fixture()
        filesystem = root / 'rootfs'
        filesystem.mkdir(mode=0o700)
        (filesystem / 'file').write_bytes(b'synthetic')
        os.utime(filesystem, ns=(1000000000, 1000000000))
        counts, entries = producer.inventory_root(filesystem)
        self.assertEqual(counts, {'files': 1, 'directories': 1, 'symlinks': 0, 'bytes': 9})
        directory = next(row for row in entries if row['path'] == '.')
        self.assertEqual(directory['mode'], 0o700)
        self.assertEqual(directory['mtime_ns'], 1000000000)

    def test_unsupported_overlay_whiteout_hardlink_and_pax_semantics_deny(self):
        producer = self.producer()
        entry = {'path': 'file', 'type': 'file', 'mode': 0o444, 'mtime': 1,
                 'size': 9, 'sha256': hashlib.sha256(b'synthetic').hexdigest(), 'pax_headers': {}}
        for kind in ('overlay', 'whiteout', 'hardlink', 'pax'):
            with self.subTest(kind=kind):
                candidate = copy.deepcopy(entry)
                if kind == 'whiteout':
                    candidate['path'] = '.wh.file'
                elif kind == 'hardlink':
                    candidate['type'] = 'hardlink'
                elif kind == 'pax':
                    candidate['pax_headers'] = {'SCHILY.xattr.synthetic': 'synthetic'}
                layers = [{'entries': [candidate]}]
                if kind == 'overlay':
                    layers.append({'entries': [copy.deepcopy(candidate)]})
                with self.assertRaises(ValueError):
                    producer.compare_reconstruction([], {'layers': layers})

    def test_history_conversion_does_not_accept_other_metadata_or_execution_changes(self):
        producer = self.producer()
        source = {'history': [{'created': '1970-01-01T00:00:01+00:00', 'created_by': 'synthetic'}]}
        converted = copy.deepcopy(source)
        converted['history'][0]['created'] = '1970-01-01T00:00:01Z'
        self.assertIn('history/0/created', producer.compare_config(source, converted))
        converted['history'][0]['created_by'] = 'changed'
        with self.assertRaises(ValueError):
            producer.compare_config(source, converted)
        with self.assertRaises(ValueError):
            producer.compare_config({'config': {'User': '10001:10001'}}, {'config': {'User': '0'}})

    def test_tool_failure_is_nonzero_and_scrubs_ambient_credentials(self):
        producer = self.producer()
        from types import SimpleNamespace
        from unittest.mock import patch
        root, layout, blobs, index, manifest, outer, layer = self.fixture()
        commands = []
        with patch.dict(os.environ, {'SYNTHETIC_PRIVATE_TOKEN': 'private-fixture'}), \
                patch.object(producer.subprocess, 'run', return_value=SimpleNamespace(returncode=7, stdout='', stderr='synthetic failure')) as invoked:
            with self.assertRaises(ValueError):
                producer.run_tool(['/synthetic/tool'], {'unshare': '/synthetic/unshare'}, root, commands, timeout=5)
        self.assertEqual(commands[0]['exit_code'], 7)
        self.assertNotIn('SYNTHETIC_PRIVATE_TOKEN', invoked.call_args.kwargs['env'])
        self.assertEqual(invoked.call_args.args[0][:5],
                         ['/synthetic/unshare', '--user', '--map-user=1000', '--map-group=1000', '--net'])

    def test_shared_app_worker_filesystem_payload_publishes_once(self):
        producer = self.producer()
        from unittest.mock import patch
        root, layout, blobs, index, manifest, outer, layer = self.fixture()
        (root / 'docs/evidence/t02').mkdir(parents=True)
        data = gzip.compress(b'{"synthetic":true}', mtime=0)
        name = hashlib.sha256(data).hexdigest() + '.json.gz'
        with patch.object(producer, 'ROOT', root):
            path = producer.publish({'synthetic': True}, [(name, data), (name, data)])
            self.assertEqual((path.parent / name).read_bytes(), data)
            self.assertEqual(len(list(path.parent.iterdir())), 2)
            original = path.read_bytes()
            with self.assertRaises(FileExistsError):
                producer.publish({'synthetic': True}, [(name, data)])
            self.assertEqual(path.read_bytes(), original)

    def test_conflicting_payload_identity_rejects_before_any_report_publication(self):
        producer = self.producer()
        from unittest.mock import patch
        root, layout, blobs, index, manifest, outer, layer = self.fixture()
        evidence = root / 'docs/evidence/t02'
        evidence.mkdir(parents=True)
        data = gzip.compress(b'{"synthetic":true}', mtime=0)
        name = hashlib.sha256(data).hexdigest() + '.json.gz'
        with patch.object(producer, 'ROOT', root), self.assertRaises(ValueError):
            producer.publish({'synthetic': True}, [(name, data), (name, data + b'changed')])
        self.assertFalse(list(evidence.rglob('report.json')))


if __name__ == '__main__':
    unittest.main()
