"""Negative controls for the inert source manifest admission contract."""
import importlib.util
import json
from pathlib import Path
import unittest
SPEC=importlib.util.spec_from_file_location('check_database_tools',Path(__file__).resolve().parents[1]/'scripts/check_database_tools.py')
checks=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(checks)


class DatabaseToolsTests(unittest.TestCase):
    def fixture(self):
        return {'schema_version':1,'artifact_kind':'inert-database-tools-source',
                'executable':False,'runtime_qualified':False,'production_activation':False,
                'files':{name:'a'*64 for name in checks.FILES}}

    def decode(self,value):
        return checks.decode_manifest(json.dumps(value).encode())

    def test_closed_inert_manifest_accepted(self):
        self.assertEqual(self.decode(self.fixture()),self.fixture())

    def test_claimed_runtime_or_activation_or_executable_denied(self):
        for key in ('executable','runtime_qualified','production_activation'):
            value=self.fixture();value[key]=True
            with self.subTest(key=key),self.assertRaises(ValueError):self.decode(value)

    def test_missing_or_extra_private_file_denied(self):
        for change in ('missing','extra'):
            value=self.fixture()
            if change=='missing':value['files'].pop(next(iter(checks.FILES)))
            else:value['files']['.env']='a'*64
            with self.subTest(change=change),self.assertRaises(ValueError):self.decode(value)

    def test_version_unknown_fields_and_hashes_denied(self):
        values=[]
        for changes in ({'schema_version':True},{'extra':True},{'artifact_kind':'runtime'}):
            values.append(dict(self.fixture(),**changes))
        value=self.fixture();value['files'][next(iter(checks.FILES))]='not-a-hash';values.append(value)
        for value in values:
            with self.assertRaises(ValueError):self.decode(value)

    def test_duplicate_keys_and_unbounded_manifest_denied(self):
        for data in (b'{"schema_version":1,"schema_version":1}',b'',b' '*32769):
            with self.assertRaises(ValueError):checks.decode_manifest(data)
