import copy
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import check_native_closure as native

A = '/nix/store/' + '0' * 32 + '-operator'
B = '/nix/store/' + '1' * 32 + '-native'
DRV = A + '.drv'
HASH = 'sha256-' + 'A' * 43 + '='


class NativeTests(unittest.TestCase):
    def setUp(self):
        self.nodes = {A: {'nar_hash': HASH, 'nar_size': 1, 'references': [A, B], 'deriver': DRV},
                      B: {'nar_hash': HASH, 'nar_size': 2, 'references': [], 'deriver': B + '.drv'}}

    def test_complete_positive_cycles(self):
        native.validate_graph(A, self.nodes)

    def test_missing_native_and_dangling_reference(self):
        del self.nodes[B]
        with self.assertRaises(ValueError): native.validate_graph(A, self.nodes)

    def test_invented_unreachable_node(self):
        self.nodes[A]['references'] = [A]
        with self.assertRaises(ValueError): native.validate_graph(A, self.nodes)

    def test_hash_size_deriver_and_reference_denial(self):
        for key, value in [('nar_hash', 'invented'), ('nar_hash', 'sha256-AAAA'), ('nar_size', 0),
                           ('nar_size', True), ('deriver', '/tmp/fake'), ('references', [B, B]),
                           ('nar_hash', 'sha256-' + '!' * 43 + '=')]:
            nodes = copy.deepcopy(self.nodes); nodes[A][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError): native.validate_graph(A, nodes)

    def test_store_paths_and_closed_nodes(self):
        for path in ('/nix/store/../../tmp', '/tmp/native', A + '/file', '/nix/store/' + 'e' * 32 + '-bad'):
            with self.assertRaises(ValueError): native.store_path(path)
        self.nodes[A]['qualified'] = True
        with self.assertRaises(ValueError): native.validate_graph(A, self.nodes)

    def test_output_derivation_binding_and_source(self):
        value = {'version': 4, 'derivations': {Path(DRV).name: {
            'name': 'synthetic', 'system': 'x86_64-linux', 'outputs': {'out': {'path': Path(A).name}},
            'structuredAttrs': {'pname': 'synthetic', 'version': '1', 'src': B}, 'env': {}}}}
        record = native.derivation_record(DRV, value, A)
        self.assertEqual(record['source_store_path'], B)
        with self.assertRaises(ValueError): native.derivation_record(DRV, value, B)
        value['version'] = 1
        with self.assertRaises(ValueError): native.derivation_record(DRV, value, A)

    def test_notice_hashes_and_symlink_nontraversal(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'LICENSE').write_bytes(b'synthetic notice')
            (root / 'README').write_bytes(b'not a named notice')
            (root / 'NOTICE').symlink_to('/unread')
            (root / 'linked-dir').symlink_to('/unread')
            result = native.notice_files(root, [str(root)])
            self.assertEqual(result, [{'path': 'LICENSE', 'size': 16, 'sha256': native.sha256(b'synthetic notice')}])
            with patch.object(native, 'MAX_NOTICE', 1), self.assertRaises(ValueError): native.notice_files(root, [str(root)])
            with self.assertRaises(ValueError): native.notice_files(root, [A])

    def test_graph_bound_and_empty(self):
        with self.assertRaises(ValueError): native.validate_graph(A, {})
        with patch.object(native, 'MAX_PATHS', 1), self.assertRaises(ValueError): native.validate_graph(A, self.nodes)

    def test_new_evidence_uses_content_addressed_revision_without_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            base=Path(directory)/'operator-native-closure.json'
            self.assertEqual(native.evidence_path(base,b'first'),base)
            base.write_bytes(b'first')
            self.assertEqual(native.evidence_path(base,b'first'),base)
            revision=native.evidence_path(base,b'second')
            self.assertEqual(revision.name,native.sha256(b'second')+'.json')
            self.assertEqual(revision.parent.name,'operator-native-closure-revisions')
            self.assertEqual(base.read_bytes(),b'first')


if __name__ == '__main__': unittest.main()
