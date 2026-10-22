"""Owned FD tests and mocked operator transport; no host connection/credential."""
import contextlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch,Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'ops/runtime'))
import operator_inspect as cli


class OperatorInspectTests(unittest.TestCase):
    def record(self):
        expected={'container_id':'a'*64,'account_uid':9909,'system_identifier':'1234567890123456789',
            'pgdata':'/var/lib/shop/postgres','database':'synthetic','role':'synthetic',
            'server_address':'unix-socket','server_port':5432}
        return {'schema_version':1,'database':expected,'socket_directory':cli.SOCKET_DIRECTORY,
                'zfs':'/nix/store/'+'a'*32+'-zfs/bin/zfs',
                'pg_control':'/nix/store/'+'b'*32+'-postgresql/bin/pg_controldata'}

    def report(self):
        return {'schema_version':1,'status':'not_recorded','retry_authorized':False,'reopening_authorized':False}

    @contextlib.contextmanager
    def mocked_command(self):
        record=self.record();connection=Mock()
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(cli.control,'admission',contextlib.nullcontext))
            stack.enter_context(patch.dict(os.environ,cli.SAFE_ENV,clear=True))
            stack.enter_context(patch.object(cli.os,'geteuid',return_value=9909))
            loaded=stack.enter_context(patch.object(cli,'load_connection',return_value=record))
            stack.enter_context(patch.object(cli.process_probe,'load_record',return_value={'database':record['database'],'process':{'executable':record['pg_control'].replace('/pg_controldata','/postgres')}}))
            stack.enter_context(patch.object(cli.schema_reconciliation,'load_authorization',return_value={'database':record['database']}))
            stack.enter_context(patch.object(cli.schema_reconciliation,'validate_artifact'))
            stack.enter_context(patch.object(cli.process_probe,'probe',return_value={'container_id':'a'*64,'account_uid':9909}))
            socket=stack.enter_context(patch.object(cli,'socket_identity',return_value=(1,2,9909)))
            stack.enter_context(patch.object(cli,'read_private_fd',side_effect=[b'private-artifact',b'SYNTHETIC_PRIVATE_PASSWORD']))
            connect=stack.enter_context(patch.object(cli.psycopg,'connect',return_value=connection))
            stack.enter_context(patch.object(cli,'require_peer'))
            inspect=stack.enter_context(patch.object(cli.schema_reconciliation,'inspect_authorized_schema',return_value=self.report()))
            yield SimpleNamespace(record=record,connection=connection,loaded=loaded,socket=socket,connect=connect,inspect=inspect)

    def test_connection_record_is_closed_fixed_unix_transport(self):
        self.assertEqual(cli.validate_connection(self.record()),self.record())
        for changed in ({'schema_version':True},{'extra':True},{'socket_directory':'/tmp'},
                        {'zfs':'/bin/zfs'},{'pg_control':'/nix/store/'+'a'*32+'-bad/bin/sh'},
                        {'database':dict(self.record()['database'],server_address='127.0.0.1')}):
            with self.subTest(changed=changed),self.assertRaises(ValueError):
                cli.validate_connection(dict(self.record(),**changed))

    def test_reads_exact_private_regular_fd_without_advancing_offset(self):
        with tempfile.TemporaryFile() as file:
            file.write(b'SYNTHETIC_PRIVATE_PASSWORD');file.flush()
            os.fchmod(file.fileno(),0o600);os.lseek(file.fileno(),5,os.SEEK_SET)
            self.assertEqual(cli.read_private_fd(file.fileno(),4096,16),b'SYNTHETIC_PRIVATE_PASSWORD')
            self.assertEqual(os.lseek(file.fileno(),0,os.SEEK_CUR),5)
            self.assertFalse(os.get_inheritable(file.fileno()))
            for mode in (0o644,0o666,0o700):
                os.fchmod(file.fileno(),mode)
                with self.assertRaises(ValueError):cli.read_private_fd(file.fileno(),4096,16)

    def test_fd_pipe_size_owner_and_changed_metadata_denied(self):
        read,write=os.pipe()
        try:
            with self.assertRaises(ValueError):cli.read_private_fd(read,4096)
        finally:os.close(read);os.close(write)
        with tempfile.TemporaryFile() as file:
            file.write(b'x'*16);file.flush();os.fchmod(file.fileno(),0o600)
            with self.assertRaises(ValueError):cli.read_private_fd(file.fileno(),15)
            with self.assertRaises(ValueError):cli.read_private_fd(file.fileno(),4096,17)
            info=os.fstat(file.fileno())
            with patch.object(cli.os,'geteuid',return_value=info.st_uid+1):
                with self.assertRaises(ValueError):cli.read_private_fd(file.fileno(),4096)
            fields=('st_dev','st_ino','st_uid','st_gid','st_mode','st_size','st_mtime_ns','st_ctime_ns')
            changed=SimpleNamespace(**{key:getattr(info,key) for key in fields})
            changed.st_ctime_ns+=1
            with patch.object(cli.os,'fstat',side_effect=[info,changed]):
                with self.assertRaises(ValueError):cli.read_private_fd(file.fileno(),4096)

    def test_socket_walk_rejects_symlinks_writable_ancestors_or_wrong_socket(self):
        parent=SimpleNamespace(st_uid=0,st_mode=stat.S_IFDIR|0o755)
        leaf=SimpleNamespace(st_uid=9909,st_mode=stat.S_IFDIR|0o700)
        good=SimpleNamespace(st_uid=9909,st_mode=stat.S_IFSOCK|0o700,st_dev=1,st_ino=2)
        for node in (good,SimpleNamespace(**{**vars(good),'st_mode':stat.S_IFREG|0o700}),
                     SimpleNamespace(**{**vars(good),'st_uid':9910})):
            with patch.object(cli.os,'open',side_effect=[10,11,12,13,14]) as opened,patch.object(cli.os,'close'), \
                 patch.object(cli.os,'fstat',side_effect=[parent,parent,parent,leaf]),patch.object(cli.os,'stat',return_value=node):
                if node is good:self.assertEqual(cli.socket_identity(9909,5432),(1,2,9909))
                else:
                    with self.assertRaises(ValueError):cli.socket_identity(9909,5432)
                self.assertTrue(opened.call_args.args[1]&os.O_NOFOLLOW)
        bad=SimpleNamespace(st_uid=0,st_mode=stat.S_IFDIR|0o777)
        with patch.object(cli.os,'open',side_effect=[10,11]),patch.object(cli.os,'close'),patch.object(cli.os,'fstat',return_value=bad):
            with self.assertRaises(ValueError):cli.socket_identity(9909,5432)

    def test_command_uses_only_explicit_readonly_scram_options_and_closes(self):
        with self.mocked_command() as case:
            self.assertEqual(cli.inspect_from_fds(),self.report())
            options=case.connect.call_args.kwargs
            self.assertEqual(options['host'],cli.SOCKET_DIRECTORY)
            self.assertEqual(options['require_auth'],'scram-sha-256')
            self.assertEqual(options['passfile'],'/dev/null')
            self.assertEqual(options['password'],'SYNTHETIC_PRIVATE_PASSWORD')
            self.assertIn('default_transaction_read_only=on',options['options'])
            self.assertEqual(options['connect_timeout'],2)
            self.assertTrue(options['autocommit'])
            self.assertEqual(case.loaded.call_count,3)
            self.assertEqual(case.socket.call_count,3)
            case.connection.close.assert_called_once()
            case.inspect.assert_called_once()

    def test_connection_or_socket_record_change_denies_and_closes(self):
        for target in ('record','socket'):
            with self.subTest(target=target),self.mocked_command() as case:
                if target=='record':case.loaded.side_effect=[case.record,dict(case.record,socket_directory='/tmp')]
                else:case.socket.side_effect=[(1,2,9909),(1,3,9909)]
                with self.assertRaises(ValueError):cli.inspect_from_fds()
                case.connection.close.assert_called_once()
                case.inspect.assert_not_called()

    def test_ambient_environment_or_root_cannot_enter_transport(self):
        with patch.object(cli,'load_connection') as loaded,patch.dict(os.environ,{'PGPASSWORD':'SYNTHETIC_PRIVATE_PASSWORD'},clear=True):
            with self.assertRaises(ValueError):cli.inspect_from_fds()
            loaded.assert_not_called()
        with patch.dict(os.environ,cli.SAFE_ENV,clear=True),patch.object(cli.os,'geteuid',return_value=0):
            with self.assertRaises(ValueError):cli.inspect_from_fds()

    def test_closed_report_rejects_private_fields_and_action_permissions(self):
        for change in ({'extra':'SYNTHETIC_PRIVATE_PASSWORD'},{'retry_authorized':True},
                       {'reopening_authorized':True},{'schema_version':True},{'status':'unknown'}):
            with self.assertRaises(ValueError):cli.validate_report(dict(self.report(),**change))

    def test_main_never_serializes_arguments_or_exception_details(self):
        output=[]
        with patch.object(cli.os,'write',side_effect=lambda fd,data:output.append((fd,data))):
            self.assertEqual(cli.main(['--password','SYNTHETIC_PRIVATE_PASSWORD']),2)
            with patch.object(cli,'inspect_from_fds',side_effect=RuntimeError('SYNTHETIC_PRIVATE_PASSWORD')):
                self.assertEqual(cli.main(['inspect']),1)
        self.assertEqual(output,[(2,cli.ERROR),(2,cli.ERROR)])

    def test_entrypoint_scrubs_all_environment_before_main(self):
        with patch.dict(os.environ,{'PGPASSWORD':'SYNTHETIC_PRIVATE_PASSWORD','PGHOST':'synthetic.invalid'},clear=True), \
             patch.object(cli.sys,'argv',['operator','--help']),patch.object(cli,'main') as main:
            def inspect_env(argv):
                self.assertEqual(dict(os.environ),cli.SAFE_ENV);self.assertEqual(argv,['--help']);return 0
            main.side_effect=inspect_env
            self.assertEqual(cli.entrypoint(),0)

    def test_actual_isolated_process_help_and_argument_denial_have_no_echo(self):
        root=Path(__file__).resolve().parents[1]/'ops/runtime'
        program="import sys,runpy;sys.dont_write_bytecode=True;sys.path.insert(0,sys.argv.pop(1));runpy.run_module('operator_inspect',run_name='__main__')"
        for argv,code in ((['--help'],0),(['--password','SYNTHETIC_PRIVATE_PASSWORD'],2)):
            result=subprocess.run([sys.executable,'-I','-c',program,str(root),*argv],
                capture_output=True,timeout=5,env={'PGPASSWORD':'SYNTHETIC_PRIVATE_PASSWORD',
                    'LD_LIBRARY_PATH':os.environ['LD_LIBRARY_PATH'],'PSYCOPG_IMPL':'python',
                    'PATH':os.environ['PATH']})
            self.assertEqual(result.returncode,code,result.stderr.decode())
            self.assertNotIn(b'SYNTHETIC_PRIVATE_PASSWORD',result.stdout+result.stderr)
            self.assertEqual(result.stdout if code==0 else result.stderr,cli.HELP if code==0 else cli.ERROR)


    def test_actual_unix_peer_credentials_and_duplicate_fd_ownership(self):
        import socket
        approved={'process':{'pid':os.getpid()},'startup':{'uid':os.getuid(),'gid':os.getgid()}}
        first,second=socket.socketpair()
        try:
            cli.require_peer(first,approved)
            for field in ('pid','uid','gid'):
                bad=__import__('copy').deepcopy(approved)
                section='process' if field=='pid' else 'startup'
                bad[section][field]+=1
                with self.subTest(field=field),self.assertRaises(ValueError):cli.require_peer(first,bad)
            # Checking must neither consume bytes nor close libpq's original FD.
            second.sendall(b'peer-control')
            cli.require_peer(first,approved)
            self.assertEqual(first.recv(12),b'peer-control')
            self.assertGreaterEqual(first.fileno(),0)
        finally:first.close();second.close()

    def test_peer_denies_non_unix_stream_or_missing_descriptor(self):
        import socket
        approved={'process':{'pid':os.getpid()},'startup':{'uid':os.getuid(),'gid':os.getgid()}}
        for family,kind in ((socket.AF_INET,socket.SOCK_STREAM),(socket.AF_UNIX,socket.SOCK_DGRAM)):
            with socket.socket(family,kind) as connection:
                with self.assertRaises(ValueError):cli.require_peer(connection,approved)
                self.assertGreaterEqual(connection.fileno(),0)
        with tempfile.TemporaryFile() as file:
            with self.assertRaises(OSError):cli.require_peer(file,approved)


    def test_peer_denial_closes_before_readonly_observation(self):
        with self.mocked_command() as case, patch.object(cli,'require_peer',side_effect=ValueError):
            with self.assertRaises(ValueError):cli.inspect_from_fds()
            case.inspect.assert_not_called()
            case.connection.close.assert_called_once()
