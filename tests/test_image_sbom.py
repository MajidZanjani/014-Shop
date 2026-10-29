"""Synthetic omission/substitution controls for actual image SBOM integration."""
import base64
import copy
import hashlib
import importlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
A = '/nix/store/' + '0' * 32 + '-libalpha-1.0'
B = '/nix/store/' + '1' * 32 + '-libbeta-2.0'
R = '/nix/store/' + '2' * 32 + '-synthetic-image-inventory-root'
HASH = 'sha256-' + 'A' * 43 + '='


class ImageSbomTests(unittest.TestCase):
    def producer(self):
        try:
            return importlib.import_module('check_image_sbom')
        except ModuleNotFoundError as error:
            if error.name != 'check_image_sbom':
                raise
            self.fail('Actual image/native standard SBOM integration is absent')

    def nodes(self):
        result = {}
        for path, name, version, refs in ((A, 'libalpha', '1.0', [A, B]), (B, 'libbeta', '2.0', [])):
            result[path] = {'nar_hash': HASH, 'nar_size': 1, 'references': refs, 'deriver': path + '.drv',
                            'derivation_sha256': '0' * 64,
                            'recipe': {'name': name + '-' + version, 'declared_pname': name,
                                       'declared_version': version, 'outputs': {'out': path, 'dev': path + '-dev'}}}
        return result

    def entries(self):
        return [{'path': '.', 'type': 'directory'}, {'path': 'nix', 'type': 'directory'},
                {'path': 'nix/store', 'type': 'directory'},
                {'path': A[1:], 'type': 'directory'}, {'path': B[1:], 'type': 'directory'},
                {'path': A[1:] + '/lib', 'type': 'directory'},
                {'path': A[1:] + '/lib/alpha.so', 'type': 'file', 'size': 9,
                 'sha256': hashlib.sha256(b'synthetic').hexdigest()}]

    def source(self):
        config = {'architecture': 'amd64', 'os': 'linux', 'config': {'User': '10001:10001'},
                  'rootfs': {'type': 'layers', 'diff_ids': ['sha256:' + '0' * 64]}}
        encoded = json.dumps(config).encode()
        image_id = 'sha256:' + hashlib.sha256(encoded).hexdigest()
        raw = {'descriptor': {'name': 'syft', 'version': '1.44.0'}, 'source': {'type': 'image', 'metadata': {
            'imageID': image_id, 'tags': ['shop-app:candidate'], 'os': 'linux', 'architecture': 'amd64',
            'config': base64.b64encode(encoded).decode()}},
            'artifacts': [{'id': 'a' * 16, 'name': 'libalpha', 'version': '1.0', 'type': 'nix',
                           'metadata': {'path': A}, 'locations': [{'path': A}]},
                          {'id': 'b' * 16, 'name': 'libbeta', 'version': '2.0', 'type': 'nix',
                           'metadata': {'path': B}, 'locations': [{'path': B}]}]}
        outer = {'config_image_id': image_id, 'config': config}
        return raw, outer

    def syft_cdx(self):
        raw, outer = self.source()
        components = [{'type': 'library', 'name': item['name'], 'version': item['version'],
                       'bom-ref': 'pkg:nix/' + item['name'] + '@' + item['version'] + '?package-id=' + item['id']}
                      for item in raw['artifacts']]
        components.append({'type': 'file', 'name': A + '/lib/alpha.so', 'bom-ref': 'c' * 16,
                           'hashes': [{'alg': 'SHA-256', 'content': hashlib.sha256(b'synthetic').hexdigest()}]})
        return raw, {'bomFormat': 'CycloneDX', 'specVersion': '1.6', 'components': components}

    def native_cdx(self):
        def component(path, node):
            return {'type': 'library', 'bom-ref': node['deriver'], 'name': node['recipe']['declared_pname'],
                    'version': node['recipe']['declared_version'], 'properties': [
                        {'name': 'nix:output_path', 'value': value} for value in node['recipe']['outputs'].values()]}
        nodes = self.nodes()
        return {'bomFormat': 'CycloneDX', 'specVersion': '1.4',
                'metadata': {'component': {'bom-ref': R + '.drv'}},
                'components': [component(path, node) for path, node in nodes.items()],
                'dependencies': [{'ref': R + '.drv', 'dependsOn': [A + '.drv', B + '.drv']},
                                 {'ref': A + '.drv', 'dependsOn': [B + '.drv']}, {'ref': B + '.drv'}]}

    def test_every_observed_store_object_is_selected(self):
        producer = self.producer()
        self.assertEqual(producer.image_store_paths(self.entries()), {A, B})
        with self.assertRaises(ValueError):
            producer.image_store_paths([{'path': 'nix/store/not-a-store-object/file', 'type': 'file'}])

    def test_complete_actual_graph_has_no_omitted_or_invented_objects(self):
        producer = self.producer()
        producer.validate_native_nodes({A, B}, self.nodes())
        for kind in ('missing', 'extra', 'reference', 'hash', 'deriver'):
            nodes = self.nodes()
            if kind == 'missing':
                nodes.pop(B)
            elif kind == 'extra':
                nodes[R] = copy.deepcopy(nodes[A])
            elif kind == 'reference':
                nodes[A]['references'].append(R)
            elif kind == 'hash':
                nodes[A]['nar_hash'] = 'not-a-content-hash'
            else:
                nodes[A]['recipe']['outputs']['out'] = R
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                producer.validate_native_nodes({A, B}, nodes)

    def test_output_bound_recipe_keeps_registered_build_origin_separate(self):
        producer = self.producer()
        selected = B + '.drv'
        value = {'version': 4, 'derivations': {Path(selected).name: {
            'name': 'libalpha-1.0', 'system': 'x86_64-linux', 'env': {
                'pname': 'libalpha', 'version': '1.0'}, 'outputs': {'out': {'path': A.removeprefix('/nix/store/')}}}}}
        result = producer.select_output_recipe(A, value, A + '.drv')
        self.assertEqual(result['deriver'], selected)
        self.assertEqual(result['registered_deriver'], A + '.drv')
        self.assertEqual(result['recipe']['outputs']['out'], A)
        self.assertEqual(result['build_origin_proven'], False)
        changed = copy.deepcopy(value)
        changed['derivations'][Path(selected).name]['outputs']['out']['path'] = R.removeprefix('/nix/store/')
        with self.assertRaises(ValueError):
            producer.select_output_recipe(A, changed, A + '.drv')
        with self.assertRaises(ValueError):
            producer.select_output_recipe(A, {'version': 4, 'derivations': {}}, A + '.drv')

    def test_multiple_output_recipes_are_reported_without_inventing_an_origin(self):
        producer = self.producer()
        definition = {'name': 'libalpha-1.0', 'system': 'x86_64-linux', 'env': {
            'pname': 'libalpha', 'version': '1.0'}, 'outputs': {'out': {'path': A.removeprefix('/nix/store/')}}}
        value = {'version': 4, 'derivations': {Path(B).name + '.drv': definition,
                                             Path(R).name + '.drv': copy.deepcopy(definition)}}
        result = producer.select_output_recipe(A, value, A + '.drv')
        self.assertEqual(result['compatible_derivations'], [B + '.drv', R + '.drv'])
        self.assertFalse(result['build_origin_proven'])

    def test_raw_image_config_bytes_and_exact_tag_bind_the_scan(self):
        producer = self.producer()
        raw, outer = self.source()
        producer.verify_syft_source(raw, outer, 'shop-app', '1.44.0')
        for kind in ('id', 'bytes', 'tag', 'tool'):
            changed = copy.deepcopy(raw)
            if kind == 'id':
                changed['source']['metadata']['imageID'] = 'sha256:' + '0' * 64
            elif kind == 'bytes':
                changed['source']['metadata']['config'] = base64.b64encode(b'{}').decode()
            elif kind == 'tag':
                changed['source']['metadata']['tags'] = ['shop-worker:candidate']
            else:
                changed['descriptor']['version'] = 'unqualified'
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                producer.verify_syft_source(changed, outer, 'shop-app', '1.44.0')

    def test_syft_empty_platform_fields_require_exact_raw_configuration(self):
        producer = self.producer()
        raw, outer = self.source()
        raw['source']['metadata']['architecture'] = ''
        raw['source']['metadata']['os'] = ''
        receipt = producer.verify_syft_source(raw, outer, 'shop-app', '1.44.0')
        self.assertEqual(receipt['platform_fields_omitted_by_tool'], ['architecture', 'os'])
        raw['source']['metadata']['architecture'] = 'arm64'
        with self.assertRaises(ValueError):
            producer.verify_syft_source(raw, outer, 'shop-app', '1.44.0')

    def test_nix_name_version_claims_bind_to_real_recipes_and_locations(self):
        producer = self.producer()
        raw, outer = self.source()
        self.assertEqual(producer.verify_syft_claims(raw, self.entries(), self.nodes())['native_claims'], 2)
        for kind in ('version', 'location', 'store'):
            changed = copy.deepcopy(raw)
            if kind == 'version':
                changed['artifacts'][0]['version'] = 'invented'
            elif kind == 'location':
                changed['artifacts'][0]['locations'][0]['path'] = '/private-host-file'
            else:
                changed['artifacts'][0]['metadata']['path'] = R
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                producer.verify_syft_claims(changed, self.entries(), self.nodes())

    def test_standard_component_projection_preserves_all_tool_artifacts(self):
        producer = self.producer()
        raw, bom = self.syft_cdx()
        self.assertEqual(producer.reconcile_syft_cdx(raw, bom, self.entries()), {'packages': 2, 'files': 1, 'dependency_edges': 0})
        for kind in ('missing', 'extra', 'version', 'file_hash'):
            changed = copy.deepcopy(bom)
            if kind == 'missing':
                changed['components'].pop(0)
            elif kind == 'extra':
                extra = copy.deepcopy(changed['components'][0])
                extra['bom-ref'] = 'pkg:nix/invented?package-id=' + 'd' * 16
                changed['components'].append(extra)
            elif kind == 'version':
                changed['components'][0]['version'] = 'invented'
            else:
                changed['components'][-1]['hashes'][0]['content'] = '0' * 64
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                producer.reconcile_syft_cdx(raw, changed, self.entries())

    def test_non_purl_binary_component_uses_the_actual_tool_artifact_id(self):
        producer = self.producer()
        raw, bom = self.syft_cdx()
        raw['artifacts'][0].pop('purl', None)
        bom['components'][0]['bom-ref'] = raw['artifacts'][0]['id']
        producer.reconcile_syft_cdx(raw, bom, self.entries())
        bom['components'][0]['bom-ref'] = 'invented-binary'
        with self.assertRaises(ValueError):
            producer.reconcile_syft_cdx(raw, bom, self.entries())

    def test_dependency_projection_rejects_omitted_or_invented_edges(self):
        producer = self.producer()
        raw, bom = self.syft_cdx()
        raw['artifactRelationships'] = [{'parent': 'a' * 16, 'child': 'b' * 16, 'type': 'dependency-of'}]
        bom['dependencies'] = [{'ref': bom['components'][1]['bom-ref'],
                                'dependsOn': [bom['components'][0]['bom-ref']]}]
        self.assertEqual(producer.reconcile_syft_cdx(raw, bom, self.entries())['dependency_edges'], 1)
        changed = copy.deepcopy(bom)
        changed['dependencies'] = []
        with self.assertRaises(ValueError):
            producer.reconcile_syft_cdx(raw, changed, self.entries())
        changed = copy.deepcopy(bom)
        changed['dependencies'][0]['dependsOn'].append('invented')
        with self.assertRaises(ValueError):
            producer.reconcile_syft_cdx(raw, changed, self.entries())

    def test_tool_inference_discrepancy_is_preserved_and_never_becomes_recipe_authority(self):
        producer = self.producer()
        raw, outer = self.source()
        artifact = raw['artifacts'][0]
        artifact['foundBy'] = 'nix-cataloger'
        artifact['metadata']['derivation'] = {}
        artifact['version'] = 'different-tool-inference'
        with self.assertRaises(ValueError):
            producer.verify_syft_claims(raw, self.entries(), self.nodes())
        receipt = producer.verify_syft_claims(raw, self.entries(), self.nodes(), allow_inferred_findings=True)
        self.assertFalse(receipt['native_inferences_match_recipes'])
        finding = receipt['native_inference_findings'][0]
        self.assertEqual(finding['observed_version'], 'different-tool-inference')
        self.assertEqual(finding['recipe_version'], '1.0')
        self.assertFalse(finding['accepted_as_authority'])
        artifact['locations'][0]['path'] = '/unbound'
        with self.assertRaises(ValueError):
            producer.verify_syft_claims(raw, self.entries(), self.nodes(), allow_inferred_findings=True)

    def test_native_sbom_covers_actual_outputs_and_edges_without_installing_siblings(self):
        producer = self.producer()
        result = producer.reconcile_native_cdx(self.native_cdx(), self.nodes(), R + '.drv')
        self.assertEqual(set(result['actual_outputs']), {A, B})
        self.assertNotIn(A + '-dev', result['actual_outputs'])
        self.assertIn(A + '-dev', result['declared_sibling_outputs_not_observed'])

    def test_native_tool_structured_attribute_omission_is_recorded_exactly(self):
        producer = self.producer()
        nodes, bom = self.nodes(), self.native_cdx()
        nodes[A]['sbomnix_recipe_projection'] = {'name': 'libalpha-1.0', 'version': ''}
        bom['components'][0]['name'] = 'libalpha-1.0'
        bom['components'][0]['version'] = ''
        receipt = producer.reconcile_native_cdx(bom, nodes, R + '.drv')
        self.assertEqual(len(receipt['identity_projection_findings']), 1)
        self.assertFalse(receipt['identity_projection_findings'][0]['accepted_as_declared_version'])
        bom['components'][0]['version'] = 'invented'
        with self.assertRaises(ValueError):
            producer.reconcile_native_cdx(bom, nodes, R + '.drv')

    def test_missing_native_component_edge_or_unbound_output_fails(self):
        producer = self.producer()
        for kind in ('component', 'edge', 'output'):
            changed = self.native_cdx()
            if kind == 'component':
                changed['components'].pop(1)
            elif kind == 'edge':
                changed['dependencies'][1]['dependsOn'] = []
            else:
                changed['components'][0]['properties'][0]['value'] = R
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                producer.reconcile_native_cdx(changed, self.nodes(), R + '.drv')

    def test_notice_bytes_are_exact_not_licence_approval(self):
        producer = self.producer()
        data = b'SYNTHETIC NOTICE\r\n'
        entry = {'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
        self.assertEqual(producer.verify_notice(entry, data), entry['sha256'])
        with self.assertRaises(ValueError):
            producer.verify_notice(entry, data.replace(b'\r\n', b'\n'))

    def test_failed_schema_validation_publishes_no_revision_and_preserves_originals(self):
        producer = self.producer()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = root / 'docs/evidence/t02'
            evidence.mkdir(parents=True)
            baseline = evidence / 'runtime-image-inventory.json'
            baseline.write_bytes(b'HISTORICAL RAW INVENTORY')
            def rejected(payloads):
                raise ValueError('synthetic maintained-validator rejection')
            with patch.object(producer, 'ROOT', root), self.assertRaises(ValueError):
                producer.publish_validated({'synthetic': True}, {'raw.cdx.json': b'{}'}, rejected)
            self.assertEqual(baseline.read_bytes(), b'HISTORICAL RAW INVENTORY')
            self.assertEqual(list(evidence.rglob('*.json')), [baseline])

    def test_exclusive_revision_never_overwrites_a_prior_observation(self):
        producer = self.producer()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'docs/evidence/t02').mkdir(parents=True)
            with patch.object(producer, 'ROOT', root):
                first = producer.publish_validated({'synthetic': True}, {'raw.cdx.json': b'{}'}, lambda payloads: None)
                original = first.read_bytes()
                with self.assertRaises(FileExistsError):
                    producer.publish_validated({'synthetic': True}, {'raw.cdx.json': b'{}'}, lambda payloads: None)
                self.assertEqual(first.read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
