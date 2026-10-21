import copy
import importlib.util
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('shop_guard',ROOT/'ops/runtime/guard.py')
guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)


def fixture():
    return {'schema_version':1,'evidence_class':'actual-offhost-runtime','machine_id_sha256':'a'*64,
        'uid':9909,'gid':9909,'parent_dataset':'fixture/shop','database_dataset':'fixture/shop/postgres',
        'pg_system_identifier':'1234567890123456789','paths':{key:'/srv/shop/'+('containers/storage' if key=='graphroot' else key) for key in guard.CATEGORIES}}


class DeploymentGuardTests(unittest.TestCase):
    def test_expected_closed_and_positive(self):
        self.assertEqual(guard.validate_expected(fixture()),fixture())
        for key,value in [('evidence_class','proposed'),('uid',0),('machine_id_sha256','unknown'),('database_dataset','other/db'),('extra',True)]:
            bad=fixture();bad[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):guard.validate_expected(bad)

    def test_all_storage_categories_bounded(self):
        for category in guard.CATEGORIES:
            bad=fixture();bad['paths'][category]='/tmp/escape'
            with self.subTest(category=category),self.assertRaises(ValueError):guard.validate_expected(bad)
        bad=fixture();del bad['paths']['spool']
        with self.assertRaises(ValueError):guard.validate_expected(bad)
        self.assertEqual(guard.PARENT_QUOTA,85899345920)
        self.assertEqual(guard.DB_QUOTA,53687091200)

    def test_destination_exact_and_decoy_denied(self):
        expected={'container_id':'a'*64,'account_uid':9909,'system_identifier':'1234567890123456789',
            'pgdata':'/var/lib/shop/postgres','database':'synthetic_shop','role':'synthetic_shop',
            'server_address':'synthetic-private','server_port':5432}
        self.assertTrue(guard.validate_database_identity(expected,dict(expected)))
        for key in expected:
            observed=dict(expected);observed[key]='decoy'
            with self.subTest(key=key),self.assertRaises(ValueError):guard.validate_database_identity(expected,observed)
        for key in expected:
            bad=dict(expected);bad[key]=''
            with self.assertRaises(ValueError):guard.validate_database_identity(bad,bad)

    def test_no_unknown_fields_or_proposed_ownership(self):
        bad=fixture();bad['observed']=True
        with self.assertRaises(ValueError):guard.validate_expected(bad)
        for key in ('uid','gid'):
            bad=fixture();bad[key]=True
            with self.assertRaises(ValueError):guard.validate_expected(bad)
