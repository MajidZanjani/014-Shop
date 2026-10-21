"""Exact reversible metadata omission; raw output and inventory stay intact."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from derive_npm_sbom import derive,BAD_REFERENCE


class DerivationTests(unittest.TestCase):
    def setUp(self):
        self.raw=(Path(__file__).resolve().parents[1]/'docs/evidence/t02/npm-sbom.json').read_bytes()
        self.value=json.loads(self.raw)

    def encode(self,value):return json.dumps(value).encode()

    def test_only_exact_reference_removed_and_reversible(self):
        output,receipt=derive(self.raw);value=json.loads(output)
        self.assertEqual(len(receipt['changes']),2)
        self.assertEqual(receipt['changes'][0]['removed_value'],BAD_REFERENCE)
        for change in reversed(receipt['changes']):
            parts=change['json_pointer'].split('/')
            value['components'][int(parts[2])]['externalReferences'].insert(int(parts[4]),change['removed_value'])
        self.assertEqual(value,self.value)
        self.assertEqual(receipt['raw_sha256'],hashlib.sha256(self.raw).hexdigest())
        self.assertEqual(receipt['derived_sha256'],hashlib.sha256(output).hexdigest())
        for flag in ('software_approval','legal_approval','inventory_complete','raw_upstream_metadata_resolved'):
            self.assertIs(receipt[flag],False)

    def test_no_implicit_schema_validation_claim_from_pure_transform(self):
        _,receipt=derive(self.raw)
        self.assertNotIn('schema_validation',receipt)
        self.assertEqual(receipt['evidence_class'],'local-synthetic')

    def test_missing_or_duplicate_target_denied(self):
        target=next(c for c in self.value['components'] if c['bom-ref']=='am-i-vibing@0.5.0')
        for components in ([c for c in self.value['components'] if c is not target],self.value['components']+[target]):
            with self.assertRaises(ValueError):derive(self.encode(dict(self.value,components=components)))

    def test_changed_identity_or_unknown_bad_reference_denied(self):
        for field,replacement in (('name','unrelated'),('version','0.5.1'),('purl','pkg:npm/unrelated@0.5.0')):
            value=copy.deepcopy(self.value);target=next(c for c in value['components'] if c['bom-ref']=='am-i-vibing@0.5.0')
            target[field]=replacement
            with self.subTest(field=field),self.assertRaises(ValueError):derive(self.encode(value))
        value=copy.deepcopy(self.value);target=next(c for c in value['components'] if c['bom-ref']=='am-i-vibing@0.5.0')
        target['externalReferences']=[dict(BAD_REFERENCE,url='https://example.invalid/unknown')]
        with self.assertRaises(ValueError):derive(self.encode(value))

    def test_duplicate_bad_reference_denied(self):
        target=next(c for c in self.value['components'] if c['bom-ref']=='am-i-vibing@0.5.0')
        target['externalReferences'].append(dict(BAD_REFERENCE))
        with self.assertRaises(ValueError):derive(self.encode(self.value))

    def test_invalid_duplicate_schema_or_oversized_input_denied(self):
        duplicate=self.raw.replace(b'"bomFormat": "CycloneDX"',b'"bomFormat": "CycloneDX", "bomFormat": "CycloneDX"',1)
        for value in (b'bad',b'\xff',duplicate,b' '*8388609,self.encode(dict(self.value,specVersion='1.6'))):
            with self.assertRaises(ValueError):derive(value)

    def test_all_component_hashes_licences_and_dependency_edges_unchanged(self):
        output,_=derive(self.raw);derived=json.loads(output)
        self.assertEqual(derived['dependencies'],self.value['dependencies'])
        for before,after in zip(self.value['components'],derived['components']):
            for key in ('bom-ref','name','version','purl','hashes','licenses'):
                self.assertEqual(before.get(key),after.get(key))
