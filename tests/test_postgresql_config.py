import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(ROOT/'ops/runtime'))
import check_postgresql_config as check
import bootstrap


class PostgreSQLConfigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.geteuid()==0:raise ValueError('existing unprivileged fixture identity required')
        cls.temp=tempfile.TemporaryDirectory(prefix='native-',dir=os.environ['SHOP_PG_CONFIG_TEST_ROOT'])
        try:
            cls.root=Path(cls.temp.name);data=cls.root/'data';spool=cls.root/'spool'
            data.mkdir(mode=0o700);spool.mkdir(mode=0o700)
            bootstrap.initialize_empty(data,spool,os.environ['SHOP_POSTGRES_BIN'],'b'*32)
            cls.config=(ROOT/'ops/postgresql/postgresql.conf').read_text()
            cls.hba=(ROOT/'ops/postgresql/pg_hba.conf').read_text()
            config=cls.root/'postgresql.conf';config.write_text(cls.config)
            hba=cls.root/'pg_hba.conf';hba.write_text(cls.hba)
            # Test-only explicit path adaptations: no production path is created.
            sql="SELECT json_build_object('settings',(SELECT json_object_agg(name,setting) FROM pg_settings),'hba',(SELECT json_agg(json_build_object('auth',auth_method,'error',error)) FROM pg_hba_file_rules));\n"
            result=subprocess.run([str(Path(os.environ['SHOP_POSTGRES_BIN'])/'postgres'),'--single','-D',str(data),
                '-c','config_file='+str(config),'-c','data_directory='+str(data),'-c','hba_file='+str(hba),'postgres'],
                input=sql,text=True,capture_output=True,check=True,timeout=10,
                env={'PATH':os.defpath,'HOME':'/nonexistent','LANG':'C','LC_ALL':'C'})
            cls.observed=json.JSONDecoder().raw_decode(result.stdout[result.stdout.index('{'):])[0]
            cls.data=data
        except BaseException:cls.temp.cleanup();raise

    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def test_actual_native_configuration_has_no_tcp_and_private_socket(self):
        settings=self.observed['settings']
        self.assertEqual(settings['listen_addresses'],'')
        self.assertEqual(settings['unix_socket_directories'],'/tmp')
        self.assertEqual(settings['unix_socket_permissions'],'0700')
        self.assertFalse((self.data/'postmaster.pid').exists())
        self.assertEqual(settings['server_encoding'],'UTF8')

    def test_actual_hba_parser_rejects_all_without_errors(self):
        rules=self.observed['hba'];self.assertEqual(len(rules),6)
        self.assertTrue(all(row=={'auth':'reject','error':None} for row in rules))

    def test_actual_durability_and_archive_failure_placeholder(self):
        settings=self.observed['settings']
        for key in ('fsync','synchronous_commit','full_page_writes','data_checksums','archive_mode'):
            self.assertEqual(settings[key],'on')
        self.assertEqual(settings['wal_level'],'replica')
        self.assertEqual(settings['archive_timeout'],'300')
        self.assertEqual(settings['archive_command'],'exit 1')

    def test_actual_resource_and_logging_settings(self):
        settings=self.observed['settings']
        for key,value in {'max_connections':'20','shared_buffers':'32768','work_mem':'4096',
                          'maintenance_work_mem':'65536','max_worker_processes':'2','max_parallel_workers':'0',
                          'log_statement':'none','log_min_error_statement':'panic','log_parameter_max_length':'0',
                          'log_parameter_max_length_on_error':'0','logging_collector':'off'}.items():
            with self.subTest(key=key):self.assertEqual(settings[key],value)
        self.assertTrue(check.validate_candidate(self.config,self.hba))

    def test_weakened_durability_or_open_connections_rejected(self):
        for before,after in [('fsync = on','fsync = off'),("listen_addresses = ''","listen_addresses = '*'"),
                             ("archive_command = 'exit 1'","archive_command = 'true'"),
                             ('max_connections = 20','max_connections = 100')]:
            with self.subTest(after=after),self.assertRaises(ValueError):
                check.validate_candidate(self.config.replace(before,after),self.hba)
        with self.assertRaises(ValueError):check.validate_candidate(self.config,self.hba.replace('reject','trust'))

    def test_sql_logging_or_external_include_rejected(self):
        for before,after in [("log_statement = 'none'","log_statement = 'all'"),
                             ('log_parameter_max_length_on_error = 0','log_parameter_max_length_on_error = -1')]:
            with self.subTest(after=after),self.assertRaises(ValueError):
                check.validate_candidate(self.config.replace(before,after),self.hba)
        with self.assertRaises(ValueError):check.validate_candidate(self.config+"include = '/tmp/unreviewed.conf'\n",self.hba)

    def test_no_shared_host_database_mount_or_published_port(self):
        unit=(ROOT/'ops/quadlet/shop-postgres.container').read_text()
        self.assertNotIn('PublishPort=',unit)
        self.assertIn('Volume=/etc/xspi-shop/postgresql.conf:/var/lib/shop/config/postgresql.conf:ro',unit)
        self.assertIn('Volume=/etc/xspi-shop/pg_hba.conf:/var/lib/shop/config/pg_hba.conf:ro',unit)
        self.assertIn('Volume=/srv/shop/postgres:/var/lib/shop/postgres:rw',unit)
