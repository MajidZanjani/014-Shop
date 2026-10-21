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
