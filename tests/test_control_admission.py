"""Actual scratch-file locks; fixed-path/root custody remains fixture-adapted."""
import contextlib
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'ops/runtime'))
import control


class ControlAdmissionTests(unittest.TestCase):
    def manifest(self):
        return {'schema_version':1,'state':'admitted','generation':'a'*64,
                'record_sha256':{name:hashlib.sha256(b'{}').hexdigest() for name in
                    ('expected.json','database-process.json','operator-connection.json')}}

    @contextlib.contextmanager
    def fixture(self,value=None):
        scratch=Path(os.environ.get('SHOP_TEST_SCRATCH',Path(__file__).resolve().parents[1]/'.scratch'))
        with tempfile.TemporaryDirectory(prefix='admission-',dir=scratch) as name:
            parent=Path(name);path=parent/control.ADMISSION_NAME
            path.write_bytes(json.dumps(value if value is not None else self.manifest()).encode())
            path.chmod(0o440)
            directory=os.open(parent,os.O_RDONLY|os.O_DIRECTORY|os.O_CLOEXEC)
            real_open=os.open
            @contextlib.contextmanager
            def opened():
                fd=real_open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC)
                try:yield directory,fd
                finally:os.close(fd)
            try:
                with patch.object(control,'_admission_file',opened):
                    yield parent,path,directory
            finally:os.close(directory)

    def child_lock(self,path,exclusive):
        # Fresh process and open description; never wait for another owner.
        program='''import fcntl,os,sys
fd=os.open(sys.argv[1],os.O_RDONLY)
try:
    fcntl.flock(fd,(fcntl.LOCK_EX if sys.argv[2]=='exclusive' else fcntl.LOCK_SH)|fcntl.LOCK_NB)
except BlockingIOError:
    sys.exit(3)
finally:
    os.close(fd)
'''
        return subprocess.run([sys.executable,'-I','-c',program,str(path),
            'exclusive' if exclusive else 'shared'],capture_output=True,timeout=5).returncode

    def test_shared_lifetime_blocks_independent_publisher_and_releases(self):
        with self.fixture() as (parent,path,fd):
            with control.admission():
                control.check_admission()
                self.assertEqual(self.child_lock(path,False),0)
                self.assertEqual(self.child_lock(path,True),3)
            self.assertEqual(self.child_lock(path,True),0)
            with self.assertRaises(ValueError):control.check_admission()

    def test_exclusive_writer_denies_reader_without_waiting(self):
        import fcntl
        with self.fixture() as (parent,path,fd):
            writer=os.open(path,os.O_RDONLY)
            try:
                fcntl.flock(writer,fcntl.LOCK_EX|fcntl.LOCK_NB)
                with self.assertRaises(BlockingIOError):
                    with control.admission():self.fail('admitted while writer held lock')
            finally:os.close(writer)
            with control.admission():control.check_admission()

    def test_blocked_persists_after_writer_releases_and_reader_never_repairs(self):
        import fcntl
        value=self.manifest();value['state']='blocked'
        with self.fixture() as (parent,path,fd):
            writer=os.open(path,os.O_RDWR)
            try:
                fcntl.flock(writer,fcntl.LOCK_EX|fcntl.LOCK_NB)
                raw=json.dumps(value).encode();os.ftruncate(writer,0);os.write(writer,raw);os.fsync(writer)
            finally:os.close(writer)
            before=path.read_bytes()
            with self.assertRaises(ValueError):
                with control.admission():self.fail('admitted blocked state')
            self.assertEqual(path.read_bytes(),before)
            self.assertEqual(self.child_lock(path,True),0)

    def test_missing_malformed_unknown_or_unbounded_state_denies(self):
        for change in ({'schema_version':True},{'state':'blocked'},{'generation':'invalid'},
                       {'unknown':True},{'record_sha256':{}},
                       {'record_sha256':dict(self.manifest()['record_sha256'],**{'.env':'a'*64})}):
            with self.subTest(change=change),self.fixture(dict(self.manifest(),**change)):
                with self.assertRaises(ValueError):
                    with control.admission():self.fail('invalid state admitted')
        for raw in (b'{}',b'\xff',b'x'*8193,b'{"state":"admitted","state":"blocked"}'):
            with self.fixture() as (parent,path,fd):
                path.write_bytes(raw)
                with self.assertRaises(ValueError):
                    with control.admission():self.fail('invalid raw state admitted')
        with self.fixture() as (parent,path,fd):
            path.unlink()
            with self.assertRaises(FileNotFoundError):
                with control.admission():self.fail('missing state admitted')

    def test_changed_replaced_or_linked_lock_denied_and_no_descriptor_leak(self):
        for kind in ('bytes','replace','unlink','mode','hardlink'):
            with self.subTest(kind=kind),self.fixture() as (parent,path,fd):
                with self.assertRaises((ValueError,FileNotFoundError)):
                    with control.admission():
                        if kind=='bytes':path.write_bytes(json.dumps(dict(self.manifest(),generation='b'*64)).encode())
                        elif kind=='replace':
                            other=parent/'other';other.write_bytes(path.read_bytes());other.chmod(0o440);os.replace(other,path)
                        elif kind=='unlink':path.unlink()
                        elif kind=='mode':path.chmod(0o640)
                        else:os.link(path,parent/'linked')
                        control.check_admission()
                with self.assertRaises(ValueError):control.check_admission()

    def test_operation_exception_releases_lock_and_nested_context_denied(self):
        with self.fixture() as (parent,path,fd):
            with self.assertRaises(RuntimeError):
                with control.admission():
                    with self.assertRaises(ValueError):
                        with control.admission():pass
                    raise RuntimeError('synthetic-operation-failure')
            self.assertEqual(self.child_lock(path,True),0)
            with control.admission():control.check_admission()

    def test_active_manifest_binds_exact_control_record_bytes(self):
        with self.fixture() as (parent,path,directory):
            record=parent/'expected.json';record.write_bytes(b'{}');record.chmod(0o440)
            other=parent/'schema-authorization.json';other.write_bytes(b'{}');other.chmod(0o440)
            actual_open=os.open
            def fixed_path_adapter(name,flags,*args,**kwargs):
                if name in ('/','srv','shop','control'):return os.dup(directory)
                return actual_open(name,flags,*args,**kwargs)
            with control.admission(),patch.object(control.os,'open',side_effect=fixed_path_adapter):
                self.assertEqual(control.load_control('expected.json',lambda value:value),{})
                with self.assertRaises(ValueError):control.load_control('schema-authorization.json',lambda value:value)
                record.write_bytes(b'{ }')
                with self.assertRaises(ValueError):control.load_control('expected.json',lambda value:value)

    def test_symlink_and_invalid_permissions_denied(self):
        for mode in (0o400,0o600,0o644,0o666):
            with self.subTest(mode=mode),self.fixture() as (parent,path,fd):
                path.chmod(mode)
                with self.assertRaises(ValueError):
                    with control.admission():self.fail('bad mode admitted')
        with self.fixture() as (parent,path,fd):
            other=parent/'other';path.rename(other);path.symlink_to(other)
            with self.assertRaises(OSError):
                with control.admission():self.fail('symlink admitted')

    def test_final_barrier_change_suppresses_schema_success_report(self):
        import operator_schema as command
        value=self.manifest();value['state']='blocked'
        with self.fixture() as (parent,path,fd):
            def completed_operation():
                # Synthetic postcommit-return fixture, not a real crash.
                path.write_bytes(json.dumps(value).encode())
                return {'schema_version':1,'status':'applied','retry_authorized':False,'reopening_authorized':False}
            output=[]
            with patch.dict(os.environ,command.transport.SAFE_ENV,clear=True), \
                 patch.object(command.os,'geteuid',return_value=9909), \
                 patch.object(command,'_apply_admitted',side_effect=completed_operation), \
                 patch.object(command.os,'write',side_effect=lambda fd,data:output.append((fd,data))):
                self.assertEqual(command.main(['apply-reviewed-schema']),1)
            self.assertEqual(output,[(2,command.ERROR)])
            self.assertIsNone(control._ADMISSION.get())
            self.assertEqual(self.child_lock(path,True),0)
