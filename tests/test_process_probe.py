from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'ops/runtime'))
import process_probe as probe
from guard import CATEGORIES


def fixture():
    group='/user.slice/user-9909.slice/user@9909.service/app.slice/libpod-'+'a'*64+'.scope/container'
    record={'schema_version':1,'startup':{
        'schema_version':1,'evidence_class':'actual-offhost-runtime','machine_id_sha256':'a'*64,
        'uid':9909,'gid':9910,'parent_dataset':'fixture/shop','database_dataset':'fixture/shop/postgres',
        'pg_system_identifier':'1234567890123456789',
        'paths':{key:'/srv/shop/'+('containers/storage' if key=='graphroot' else key) for key in CATEGORIES}},
        'database':{'container_id':'a'*64,'account_uid':9909,'system_identifier':'1234567890123456789',
            'pgdata':'/var/lib/shop/postgres','database':'synthetic_shop','role':'synthetic_shop',
            'server_address':'unix-socket','server_port':5432},
        'process':{'pid':4321,'start_ticks':123456,
            'executable':'/nix/store/'+'a'*32+'-postgresql-18.6/bin/postgres','cgroup':group}}
    raw='4321 (synthetic ) postgres) '+' '.join(['S']+['0']*18+['123456']+['0']*4)
    snapshot={'stat_before':raw,'stat_after':raw,'status':'Uid:\t9909 9909 9909 9909\nGid:\t9910 9910 9910 9910\nNoNewPrivs:\t1\n'+''.join(key+':\t0000000000000000\n' for key in ('CapInh','CapPrm','CapEff','CapBnd','CapAmb')),
        'uid_map':'0 200000 10001\n10001 9909 1\n10002 210002 55534\n',
        'gid_map':'0 300000 10001\n10001 9910 1\n10002 310002 55534\n',
        'cgroup':'0::'+group+'\n','exe':record['process']['executable'],
        'data_identity':(99,1234,9909),'host_data_identity':(99,1234,9909)}
    return record,snapshot


class ProcessProbeTests(unittest.TestCase):
    def test_exact_synthetic_snapshot(self):
        record,snapshot=fixture()
        self.assertEqual(probe.validate_process(record,snapshot),{'container_id':'a'*64,'account_uid':9909})

    def test_reused_pid_dead_process_and_changed_executable(self):
        record,snapshot=fixture()
        for key,value in [('stat_after',snapshot['stat_after'].replace('123456','123457')),
                          ('stat_before',snapshot['stat_before'].replace(') S ',') Z ')),
                          ('exe','/unexpected/postgres')]:
            bad=dict(snapshot,**{key:value})
            with self.subTest(key=key),self.assertRaises(ValueError):probe.validate_process(record,bad)

    def test_wrong_or_root_mapped_namespace(self):
        record,snapshot=fixture()
        for key in ('uid_map','gid_map'):
            for raw in ('0 0 4294967295\n','10001 0 1\n','10001 12345 1\n','0 200000 20000\n10001 9909 1\n','10001 9909 1\n10001 9909 1\n'):
                with self.subTest(key=key,raw=raw),self.assertRaises(ValueError):
                    probe.validate_process(record,dict(snapshot,**{key:raw}))

    def test_wrong_account_or_elevated_capabilities(self):
        record,snapshot=fixture()
        for status in (snapshot['status'].replace('9909','9911'),snapshot['status'].replace('9910','9911'),
                       snapshot['status'].replace('NoNewPrivs:\t1','NoNewPrivs:\t0'),
                       snapshot['status'].replace('CapEff:\t0000000000000000','CapEff:\t0000000000000001')):
            with self.subTest(status=status),self.assertRaises(ValueError):
                probe.validate_process(record,dict(snapshot,status=status))

    def test_cgroup_escape_or_other_container(self):
        record,snapshot=fixture()
        for raw in ('0::/other',snapshot['cgroup'].replace('a'*64,'b'*64),snapshot['cgroup']+'0::/second\n'):
            with self.subTest(raw=raw),self.assertRaises(ValueError):
                probe.validate_process(record,dict(snapshot,cgroup=raw))

    def test_replaced_or_different_database_mount(self):
        record,snapshot=fixture()
        for identity in ((99,1235,9909),(98,1234,9909),(99,1234,9911),None):
            with self.subTest(identity=identity),self.assertRaises(ValueError):
                probe.validate_process(record,dict(snapshot,data_identity=identity))

    def test_closed_record_and_cross_binding(self):
        for key,value in [('schema_version',True),('unknown',True)]:
            record,snapshot=fixture();record[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):probe.validate_record(record)
        record,snapshot=fixture();record['startup']['pg_system_identifier']='9876543210987654321'
        with self.assertRaises(ValueError):probe.validate_record(record)
        record,snapshot=fixture();record['process']['cgroup']=record['process']['cgroup'].replace('user-9909','user-9911')
        with self.assertRaises(ValueError):probe.validate_record(record)

    def test_capture_stops_on_startup_guard_failure(self):
        from unittest.mock import patch
        record,_=fixture()
        with patch.object(probe.Path,'is_file',return_value=True),patch.object(probe,'inspect',side_effect=ValueError('synthetic absent mount')) as guard,patch.object(probe.os,'open') as opened:
            with self.assertRaises(ValueError):probe.probe(record,'/nix/store/fixture-zfs/bin/zfs','/nix/store/fixture-pg/bin/pg_controldata')
            guard.assert_called_once();opened.assert_not_called()

    def test_duplicate_control_keys_rejected(self):
        import json
        with self.assertRaises(ValueError):
            json.loads('{"pid":4321,"pid":9999}',object_pairs_hook=probe.unique_fields)

    def test_control_loader_rejects_writable_parent_before_opening_leaf(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        with patch.object(probe.os,'open',side_effect=[10,11]) as opened,patch.object(probe.os,'close') as closed,patch.object(probe.os,'fstat',return_value=SimpleNamespace(st_uid=0,st_mode=0o40777)):
            with self.assertRaises(ValueError):probe.load_record()
            self.assertEqual(opened.call_count,2)
            self.assertEqual([c.args[0] for c in closed.call_args_list],[10,11])

    def test_control_loader_checks_leaf_owner_type_mode_and_size(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        import stat
        parent=SimpleNamespace(st_uid=0,st_mode=stat.S_IFDIR|0o755)
        for changes in ({'st_uid':9909},{'st_mode':stat.S_IFREG|0o666},
                        {'st_mode':stat.S_IFIFO|0o600},{'st_size':32769}):
            values={'st_uid':0,'st_mode':stat.S_IFREG|0o600,'st_size':100};values.update(changes)
            with self.subTest(changes=changes),patch.object(probe.os,'open',side_effect=[10,11,12,13,14]) as opened,patch.object(probe.os,'close'),patch.object(probe.os,'fstat',side_effect=[parent,parent,parent,SimpleNamespace(**values)]),patch.object(probe.os,'read') as read:
                with self.assertRaises(ValueError):probe.load_record()
                read.assert_not_called()
                self.assertTrue(opened.call_args.args[1] & probe.os.O_NOFOLLOW)
                self.assertTrue(opened.call_args.args[1] & probe.os.O_NONBLOCK)

    def test_control_loader_positive_bounded_record(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        import json,stat
        record,_=fixture();data=json.dumps(record).encode('ascii')
        parent=SimpleNamespace(st_uid=0,st_mode=stat.S_IFDIR|0o755)
        leaf=SimpleNamespace(st_uid=0,st_mode=stat.S_IFREG|0o600,st_size=len(data))
        with patch.object(probe.os,'open',side_effect=[10,11,12,13,14]),patch.object(probe.os,'close') as closed,patch.object(probe.os,'fstat',side_effect=[parent,parent,parent,leaf]),patch.object(probe.os,'read',return_value=data) as read:
            self.assertEqual(probe.load_record(),record)
            read.assert_called_once_with(14,32769)
            self.assertEqual(sorted(c.args[0] for c in closed.call_args_list),[10,11,12,13,14])

    def test_operator_wrapper_uses_one_authoritative_record_for_sql_and_probe(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        record,_=fixture();runtime={'container_id':'a'*64,'account_uid':9909}
        connection=object()
        def execute(actual_connection,expected,callback,statement,parameters):
            self.assertIs(actual_connection,connection)
            self.assertEqual(expected,record['database'])
            self.assertEqual(statement,'INSERT INTO public.synthetic VALUES (%s)')
            self.assertEqual(parameters,(1,))
            self.assertEqual(callback(),runtime)
            self.assertEqual(callback(),runtime)
            return 1
        with patch.dict(sys.modules,{'database':SimpleNamespace(execute_mutation=execute)}),patch.object(probe,'load_record',return_value=record) as loaded,patch.object(probe,'probe',return_value=runtime) as observed:
            self.assertEqual(probe.execute_operator_mutation(connection,'zfs','pg-control','INSERT INTO public.synthetic VALUES (%s)',(1,)),1)
            self.assertEqual(loaded.call_count,3)
            self.assertEqual(observed.call_count,2)

    def test_operator_wrapper_denies_changed_attestation(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        record,_=fixture()
        changed={**record,'process':{**record['process'],'start_ticks':123457}}
        def execute(connection,expected,callback,statement,parameters):
            callback()
            self.fail('changed attestation reached mutation')
        with patch.dict(sys.modules,{'database':SimpleNamespace(execute_mutation=execute)}),patch.object(probe,'load_record',side_effect=[record,changed]),patch.object(probe,'probe') as observed:
            with self.assertRaises(ValueError):probe.execute_operator_mutation(object(),'zfs','pg-control','DELETE FROM public.synthetic')
            observed.assert_not_called()


    def test_schema_wrapper_pins_record_for_whole_batch(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        record,_=fixture();runtime={'container_id':'a'*64,'account_uid':9909}
        connection=object();statements=('CREATE TABLE public.synthetic(id integer)',)
        def execute(actual_connection,expected,callback,actual_statements):
            self.assertIs(actual_connection,connection)
            self.assertIs(actual_statements,statements)
            self.assertEqual(expected,record['database'])
            self.assertEqual(callback(),runtime)
            self.assertEqual(callback(),runtime)
        with patch.dict(sys.modules,{'database':SimpleNamespace(execute_schema_batch=execute)}),patch.object(probe,'load_record',return_value=record) as loaded,patch.object(probe,'probe',return_value=runtime) as observed:
            probe.execute_operator_schema_batch(connection,'zfs','pg-control',statements)
            self.assertEqual(loaded.call_count,3)
            self.assertEqual(observed.call_count,2)

    def test_schema_wrapper_denies_record_change(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        record,_=fixture();changed={**record,'process':{**record['process'],'start_ticks':123457}}
        def execute(connection,expected,callback,statements):
            callback()
            self.fail('changed record reached schema operation')
        with patch.dict(sys.modules,{'database':SimpleNamespace(execute_schema_batch=execute)}),patch.object(probe,'load_record',side_effect=[record,changed]),patch.object(probe,'probe') as observed:
            with self.assertRaises(ValueError):
                probe.execute_operator_schema_batch(object(),'zfs','pg-control',('CREATE TABLE public.synthetic(id integer)',))
            observed.assert_not_called()
