"""Bootstrap tests run as an existing unprivileged development UID, never mx1."""
from datetime import datetime,timezone,timedelta
import json
import os
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'ops/runtime'))
import bootstrap
from guard import CATEGORIES,validate_expected


def fixture():
    return {'schema_version':1,'storage':{'schema_version':1,'evidence_class':'actual-offhost-runtime',
        'machine_id_sha256':'a'*64,'uid':9909,'gid':9909,'parent_dataset':'synthetic/shop',
        'database_dataset':'synthetic/shop/postgres','paths':{key:'/srv/shop/'+('containers/storage' if key=='graphroot' else key) for key in CATEGORIES}},
        'action':'initialize-new-shop-cluster','authorization_id':'a'*32,
        'expires_at':(datetime.now(timezone.utc)+timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'postgres_bin':os.environ['SHOP_POSTGRES_BIN'],'initdb_sha256':'a'*64}


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.assertGreater(os.geteuid(),0,'bootstrap fixture must execute as an existing unprivileged user')
        self.temp=tempfile.TemporaryDirectory(prefix='case-',dir=os.environ['SHOP_BOOTSTRAP_TEST_ROOT'])
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.data=self.root/'data';self.spool=self.root/'spool'
        self.data.mkdir(mode=0o700);self.spool.mkdir(mode=0o700)

    def initialize(self):
        return bootstrap.initialize_empty(self.data,self.spool,os.environ['SHOP_POSTGRES_BIN'],'a'*32)

    def test_real_initdb_checksums_utf8_reject_auth_and_no_server(self):
        result=self.initialize()
        self.assertEqual(result['status'],'initialized-offline')
        self.assertRegex(result['pg_system_identifier'],r'^[0-9]{10,20}$')
        self.assertTrue(result['data_checksums']);self.assertFalse(result['server_started'])
        self.assertFalse((self.data/'postmaster.pid').exists())
        hba=[line.split() for line in (self.data/'pg_hba.conf').read_text().splitlines() if line.strip() and not line.lstrip().startswith('#')]
        self.assertGreater(len(hba),0)
        self.assertTrue(all(line[-1]=='reject' for line in hba))
        catalog=subprocess.run([str(Path(os.environ['SHOP_POSTGRES_BIN'])/'postgres'),'--single','-D',str(self.data),'postgres'],
            input="SELECT datname, pg_encoding_to_char(encoding) FROM pg_database;\n",text=True,
            capture_output=True,timeout=10,check=True,env={'PATH':os.defpath,'HOME':'/nonexistent','LANG':'C','LC_ALL':'C'})
        self.assertEqual(catalog.stdout.count('"UTF8"'),3)
        self.assertNotIn('SQL_ASCII',catalog.stdout)
        self.assertFalse((self.data/'postmaster.pid').exists())
        self.assertEqual(json.loads((self.spool/'bootstrap-attempt.json').read_text())['status'],'attempted')
        self.assertEqual(json.loads((self.spool/'bootstrap-result.json').read_text()),result)
        with patch.object(bootstrap,'run_tool') as run:
            with self.assertRaises((ValueError,FileExistsError)):self.initialize()
            run.assert_not_called()

    def test_existing_or_partial_directory_never_invokes_initdb(self):
        (self.data/'synthetic-existing').write_text('retain')
        with patch.object(bootstrap,'run_tool') as run:
            with self.assertRaises(ValueError):self.initialize()
            run.assert_not_called()
        self.assertEqual((self.data/'synthetic-existing').read_text(),'retain')
        self.assertEqual(list(self.spool.iterdir()),[])

    def test_existing_attempt_blocks_even_empty_directory(self):
        (self.spool/bootstrap.ATTEMPT).write_text('uncertain prior attempt')
        with patch.object(bootstrap,'run_tool') as run:
            with self.assertRaises(FileExistsError):self.initialize()
            run.assert_not_called()
        self.assertEqual((self.spool/bootstrap.ATTEMPT).read_text(),'uncertain prior attempt')

    def test_failed_tool_preserves_attempt_and_partial_files(self):
        def fail(argv):
            self.assertTrue((self.spool/bootstrap.ATTEMPT).is_file())
            (self.data/'partial').write_text('synthetic partial')
            raise ValueError('synthetic tool failure')
        with patch.object(bootstrap,'run_tool',side_effect=fail):
            with self.assertRaises(ValueError):self.initialize()
        self.assertEqual((self.data/'partial').read_text(),'synthetic partial')
        self.assertTrue((self.spool/bootstrap.ATTEMPT).is_file())
        self.assertFalse((self.spool/'bootstrap-result.json').exists())

    def test_prior_receipt_blocks_before_attempt_or_tool(self):
        (self.spool/'bootstrap-result.json').write_text('retain')
        with patch.object(bootstrap,'run_tool') as run:
            with self.assertRaises(ValueError):self.initialize()
            run.assert_not_called()
        self.assertFalse((self.spool/bootstrap.ATTEMPT).exists())

    def test_wrong_permissions_symlink_and_same_directory_rejected(self):
        self.data.chmod(0o755)
        with self.assertRaises(ValueError):self.initialize()
        self.data.chmod(0o700)
        link=self.root/'alias';link.symlink_to(self.data,target_is_directory=True)
        with self.assertRaises(ValueError):bootstrap.directory(link)
        with self.assertRaises(ValueError):bootstrap.initialize_empty(self.data,self.data,os.environ['SHOP_POSTGRES_BIN'],'a'*32)
        self.assertEqual(list(self.data.iterdir()),[])

    def test_closed_authority_scope_and_expiry(self):
        record=fixture();self.assertEqual(bootstrap.validate_record(record),record)
        for key,value in [('schema_version',True),('action','start-server'),('authorization_id',''),
                          ('expires_at','2020-01-01T00:00:00Z'),('postgres_bin','/usr/bin'),('extra',True)]:
            bad=fixture();bad[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):bootstrap.validate_record(bad)

    def test_bootstrap_identity_cannot_satisfy_normal_startup(self):
        storage=fixture()['storage']
        with self.assertRaises(ValueError):validate_expected(storage)
        with self.assertRaises(ValueError):validate_expected(dict(storage,pg_system_identifier=None))

    def test_command_cannot_enable_trust_or_disable_durability(self):
        command=bootstrap.command(os.environ['SHOP_POSTGRES_BIN'],self.data)
        for arg in ('--auth-local=reject','--auth-host=reject','--data-checksums','--encoding=UTF8','--no-clean'):
            self.assertIn(arg,command)
        self.assertNotIn('--no-sync',command)
        self.assertNotIn('--waldir',command)
        self.assertNotIn('--allow-group-access',command)

    def test_absent_control_record_prevents_every_mutation(self):
        with patch.object(bootstrap,'load_control',side_effect=ValueError('no authorization')),patch.object(bootstrap,'initialize_empty') as initialize:
            with self.assertRaises(ValueError):bootstrap.execute('/nix/store/unused/bin/zfs',apply=True)
            initialize.assert_not_called()

    def test_failed_attempt_fsync_prevents_initdb(self):
        with patch.object(bootstrap.os,'fsync',side_effect=OSError('synthetic fsync failure')),patch.object(bootstrap,'run_tool') as run:
            with self.assertRaises(OSError):self.initialize()
            run.assert_not_called()
        self.assertTrue((self.spool/bootstrap.ATTEMPT).exists())
        self.assertEqual(list(self.data.iterdir()),[])

    def test_preflight_never_initializes_even_with_valid_synthetic_authority(self):
        import hashlib
        record=fixture();record['initdb_sha256']=hashlib.sha256((Path(record['postgres_bin'])/'initdb').read_bytes()).hexdigest()
        actual_directory=bootstrap.directory
        def fixture_directory(path):
            return actual_directory(self.data if str(path)=='/srv/shop/postgres' else self.spool)
        with patch.object(bootstrap,'load_control',return_value=record),patch.object(bootstrap,'inspect_storage') as inspect,patch.object(bootstrap,'directory',side_effect=fixture_directory),patch.object(bootstrap,'initialize_empty') as initialize:
            self.assertIsNone(bootstrap.execute(str(Path(record['postgres_bin'])/'pg_controldata'),apply=False))
            inspect.assert_called_once();initialize.assert_not_called()
        self.assertEqual(list(self.data.iterdir()),[])
        self.assertEqual(list(self.spool.iterdir()),[])

    def test_changed_authority_before_apply_prevents_initialization(self):
        import hashlib
        record=fixture();record['initdb_sha256']=hashlib.sha256((Path(record['postgres_bin'])/'initdb').read_bytes()).hexdigest()
        actual_directory=bootstrap.directory
        def fixture_directory(path):
            return actual_directory(self.data if str(path)=='/srv/shop/postgres' else self.spool)
        changed=dict(record,authorization_id='b'*32)
        with patch.object(bootstrap,'load_control',side_effect=[record,changed]),patch.object(bootstrap,'inspect_storage') as inspect,patch.object(bootstrap,'directory',side_effect=fixture_directory),patch.object(bootstrap,'initialize_empty') as initialize:
            with self.assertRaises(ValueError):bootstrap.execute(str(Path(record['postgres_bin'])/'pg_controldata'),apply=True)
            inspect.assert_called_once();initialize.assert_not_called()
        self.assertEqual(list(self.data.iterdir()),[])
