import copy
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from check_contracts import ROOT, contracts, load, validator, no_remote_refs
from jsonschema import ValidationError, SchemaError


class ContractTests(unittest.TestCase):
    def test_known_good_fixture(self):
        api,probe=contracts();probe.validate(load(ROOT/'tests/fixtures/contracts/valid.json'))

    def test_probe_closed_version_and_format(self):
        api,probe=contracts();good=load(ROOT/'tests/fixtures/contracts/valid.json')
        for location,key,value in [('request','payload_version',2),('request','extra',1),('request','payload_version',True),('result','effect_id','not-a-uuid'),('result','outcome','paid')]:
            bad=copy.deepcopy(good);bad[location][key]=value
            with self.subTest(key=key),self.assertRaises(ValidationError):probe.validate(bad)

    def test_response_closed_and_status_specific(self):
        api,probe=contracts()
        for path,item in api['paths'].items():
            for status,response in item['get']['responses'].items():
                check=validator(response['content']['application/json']['schema'])
                with self.assertRaises(ValidationError):check.validate({'status':'wrong'})
                with self.assertRaises(ValidationError):check.validate({'status':check.schema['properties']['status']['const'],'extra':'private'})

    def test_offline_remote_references_rejected(self):
        for ref in ('https://synthetic.invalid/schema','file:///etc/passwd'):
            with self.assertRaises(ValueError):validator({'$ref':ref})

    def test_missing_and_malformed_contract_fail(self):
        with self.assertRaises(FileNotFoundError):load(ROOT/'schemas/v1/absent.json')
        with self.assertRaises(SchemaError):validator({'type':'invalid-json-schema-type'})


class EnvironmentEvidenceTests(unittest.TestCase):
    def test_actual_environment_examples(self):
        from check_contracts import environment_examples
        self.assertEqual(environment_examples(),4)

    def test_environment_rejections(self):
        schema=validator(load(ROOT/'schemas/v1/environment.schema.json'))
        values=dict(line.split('=',1) for line in (ROOT/'ops/config/synthetic.example').read_text().splitlines() if line and not line.startswith('#'))
        for key,value in [('SHOP_ENV','unknown'),('LIVE_PAYMENTS_ENABLED','true'),('SECRET_KEY','secret'),('DEBUG','true'),('EXTRA','x')]:
            bad=dict(values);bad[key]=value
            with self.subTest(key=key),self.assertRaises(ValidationError):schema.validate({'schema_version':1,'values':bad})
        with self.assertRaises(ValidationError):schema.validate({'schema_version':2,'values':values})

    def test_artifact_manifest_rejections(self):
        from check_contracts import artifact_record
        record=artifact_record(['synthetic-schema-unit-control'],{'checks':1,'tests':1},'2026-10-21T00:00:00Z',0.1)
        schema=validator(load(ROOT/'schemas/v1/artifact-manifest.schema.json'));schema.validate(record)
        for key,value in [('schema_version',2),('evidence_class','production'),('started_at','yesterday'),('duration_seconds',-1),('tests',0),('unknown','x')]:
            bad=copy.deepcopy(record);bad[key]=value
            with self.subTest(key=key),self.assertRaises(ValidationError):schema.validate(bad)
        bad=copy.deepcopy(record);bad['artifacts'][0]['sha256']='wrong'
        with self.assertRaises(ValidationError):schema.validate(bad)
        _,probe=contracts()
        with self.assertRaises(ValidationError):probe.validate(load(ROOT/'tests/fixtures/contracts/invalid.json'))
