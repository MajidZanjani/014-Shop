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
            def opened(*,writable=False):
                fd=real_open(path,(os.O_RDWR if writable else os.O_RDONLY)|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC)
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

    def authority(self,path):
        from datetime import datetime,timedelta,timezone
        return {'schema_version':1,'action':'block-control-admission','authorization_id':'b'*32,
                'current_admission_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                'expires_at':(datetime.now(timezone.utc)+timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%SZ')}

    def test_authorized_block_preserves_inode_and_denies_readers_and_repeat(self):
        with self.fixture() as (parent,path,fd):
            authority=self.authority(path);before=path.stat()
            with patch.object(control,'load_block_authority',return_value=authority):
                result=control.block_admission()
                with self.assertRaises(ValueError):control.block_admission()
            self.assertEqual(result['status'],'admission_blocked')
            self.assertTrue(result['local_fsync_readback_completed'])
            for flag in ('durability_qualified','publication_authorized','retry_authorized','reopening_authorized'):
                self.assertFalse(result[flag])
            blocked=json.loads(path.read_bytes());self.assertEqual(blocked['state'],'blocked')
            self.assertEqual(blocked['block_authorization_id'],authority['authorization_id'])
            after=path.stat()
            self.assertEqual((before.st_dev,before.st_ino,before.st_uid,before.st_gid,before.st_mode),
                             (after.st_dev,after.st_ino,after.st_uid,after.st_gid,after.st_mode))
            with self.assertRaises(ValueError):
                with control.admission():self.fail('blocked state admitted')
            self.assertEqual(self.child_lock(path,True),0)

    def test_block_authority_closed_expiry_and_exact_bytes(self):
        with self.fixture() as (parent,path,fd):
            valid=self.authority(path)
            self.assertEqual(control.validate_block_authority(valid),valid)
            for change in ({'schema_version':True},{'action':'publish-control-generation'},
                           {'authorization_id':'bad'},{'expires_at':'2000-01-01T00:00:00Z'},
                           {'extra':True},{'current_admission_sha256':'bad'}):
                with self.subTest(change=change),self.assertRaises(ValueError):
                    control.validate_block_authority(dict(valid,**change))
            before=path.read_bytes()
            wrong=dict(valid,current_admission_sha256='c'*64)
            with patch.object(control,'load_block_authority',return_value=wrong):
                with self.assertRaises(ValueError):control.block_admission()
            self.assertEqual(path.read_bytes(),before)
            with patch.object(control.os,'geteuid',return_value=9909),patch.object(control,'load_block_authority') as loader:
                with self.assertRaises(ValueError):control.block_admission()
                loader.assert_not_called()

    def test_block_denied_while_reader_holds_lease(self):
        with self.fixture() as (parent,path,fd),control.admission():
            before=path.read_bytes()
            # A separate logical publisher context still cannot acquire EX.
            token=control._ADMISSION.set(None)
            try:
                with patch.object(control,'load_block_authority',return_value=self.authority(path)):
                    with self.assertRaises(BlockingIOError):control.block_admission()
            finally:control._ADMISSION.reset(token)
            self.assertEqual(path.read_bytes(),before)
            control.check_admission()

    def test_block_revocation_before_write_and_after_sync(self):
        for changed_at in (2,3):
            with self.subTest(changed_at=changed_at),self.fixture() as (parent,path,fd):
                authority=self.authority(path);before=path.read_bytes()
                changed=dict(authority,authorization_id='d'*32)
                with patch.object(control,'load_block_authority',side_effect=[authority]*(changed_at-1)+[changed]):
                    with self.assertRaises(ValueError):control.block_admission()
                if changed_at==2:self.assertEqual(path.read_bytes(),before)
                else:
                    self.assertEqual(json.loads(path.read_bytes())['state'],'blocked')
                    with self.assertRaises(ValueError):
                        with control.admission():self.fail('uncertain block admitted')
                self.assertEqual(self.child_lock(path,True),0)

    def test_block_short_write_and_failure_retain_denied_state(self):
        actual_pwrite=os.pwrite
        with self.fixture() as (parent,path,fd), \
             patch.object(control,'load_block_authority',side_effect=lambda:self.authority_original), \
             patch.object(control.os,'pwrite',side_effect=lambda fd,data,offset:actual_pwrite(fd,data[:7],offset)):
            self.authority_original=self.authority(path)
            self.assertEqual(control.block_admission()['status'],'admission_blocked')
        for operation,result in (('pwrite',0),('fsync',OSError('synthetic-sync-failure'))):
            with self.subTest(operation=operation),self.fixture() as (parent,path,fd):
                authority=self.authority(path)
                with patch.object(control,'load_block_authority',return_value=authority), \
                     patch.object(control.os,operation,**({'side_effect':result} if isinstance(result,Exception) else {'return_value':result})):
                    with self.assertRaises((ValueError,OSError)):control.block_admission()
                with self.assertRaises(ValueError):
                    with control.admission():self.fail('failed block admitted')
                with patch.object(control,'load_block_authority',return_value=authority):
                    with self.assertRaises(ValueError):control.block_admission()
                self.assertEqual(self.child_lock(path,True),0)

    def inspection_authority(self,original,block_id='b'*32):
        from datetime import datetime,timedelta,timezone
        return {'schema_version':1,'action':'inspect-control-admission-block',
                'authorization_id':'c'*32,'block_authorization_id':block_id,
                'original_admission_sha256':hashlib.sha256(original).hexdigest(),
                'expires_at':(datetime.now(timezone.utc)+timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%SZ')}

    def test_block_inspection_observes_original_exact_block_and_partial_without_writes(self):
        for kind,status in (('original','original_matches'),('blocked','blocked_matches'),
                            ('empty','different_bytes'),('partial','different_bytes'),
                            ('other_id','different_bytes')):
            with self.subTest(kind=kind),self.fixture() as (parent,path,fd):
                original=path.read_bytes();authority=self.inspection_authority(original)
                if kind=='blocked':
                    with patch.object(control,'load_block_authority',return_value=self.authority(path)):
                        control.block_admission()
                elif kind=='empty':path.write_bytes(b'')
                elif kind=='partial':path.write_bytes(b'{"state":"blo')
                elif kind=='other_id':path.write_bytes(control._blocked_bytes(original,'d'*32))
                before=path.read_bytes();metadata=path.stat()
                with patch.object(control,'load_block_inspection',return_value=authority), \
                     patch.object(control,'load_block_authority',side_effect=AssertionError('old write authority unused')), \
                     patch.object(control.os,'fsync',side_effect=AssertionError('no sync')), \
                     patch.object(control.os,'ftruncate',side_effect=AssertionError('no truncate')), \
                     patch.object(control.os,'pwrite',side_effect=AssertionError('no writes')):
                    result=control.inspect_admission_block(original)
                self.assertEqual(result['status'],status)
                self.assertEqual(result['observed_sha256'],hashlib.sha256(before).hexdigest())
                for flag in ('durability_qualified','completion_confirmed','publication_authorized',
                             'retry_authorized','reopening_authorized'):self.assertFalse(result[flag])
                self.assertEqual(path.read_bytes(),before)
                after=path.stat()
                self.assertEqual((metadata.st_ino,metadata.st_size,metadata.st_mtime_ns,metadata.st_ctime_ns),
                                 (after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns))
                self.assertEqual(self.child_lock(path,True),0)

    def test_block_inspection_authority_and_exact_original_required_before_open(self):
        with self.fixture() as (parent,path,fd):
            original=path.read_bytes();valid=self.inspection_authority(original)
            self.assertEqual(control.validate_block_inspection(valid),valid)
            for change in ({'action':'block-control-admission'},{'schema_version':True},
                           {'expires_at':'2000-01-01T00:00:00Z'},{'block_authorization_id':'invalid'},
                           {'original_admission_sha256':'invalid'},{'extra':True}):
                with self.subTest(change=change),self.assertRaises(ValueError):
                    control.validate_block_inspection(dict(valid,**change))
            with patch.object(control,'load_block_inspection',return_value=valid), \
                 patch.object(control,'_admission_file',side_effect=AssertionError('invalid original must not open')):
                for data in (original+b' ',b'',b'{}',b'x'*8193):
                    with self.assertRaises(ValueError):control.inspect_admission_block(data)
            with patch.object(control.os,'geteuid',return_value=9909),patch.object(control,'load_block_inspection') as loader:
                with self.assertRaises(ValueError):control.inspect_admission_block(original)
                loader.assert_not_called()

    def test_block_inspection_denies_writer_revocation_changed_bytes_and_replacement(self):
        import fcntl
        with self.fixture() as (parent,path,fd):
            original=path.read_bytes();authority=self.inspection_authority(original)
            writer=os.open(path,os.O_RDONLY)
            try:
                fcntl.flock(writer,fcntl.LOCK_EX|fcntl.LOCK_NB)
                with patch.object(control,'load_block_inspection',return_value=authority):
                    with self.assertRaises(BlockingIOError):control.inspect_admission_block(original)
            finally:os.close(writer)
        for kind in ('revoke','change','replace'):
            with self.subTest(kind=kind),self.fixture() as (parent,path,fd):
                original=path.read_bytes();authority=self.inspection_authority(original);calls=[]
                def recheck():
                    calls.append(True)
                    if len(calls)==2:
                        if kind=='revoke':return dict(authority,authorization_id='d'*32)
                        if kind=='change':path.write_bytes(b'{"partial":')
                        else:
                            other=parent/'replacement';other.write_bytes(original);other.chmod(0o440);os.replace(other,path)
                    return authority
                with patch.object(control,'load_block_inspection',side_effect=recheck):
                    with self.assertRaises(ValueError):control.inspect_admission_block(original)
                self.assertEqual(self.child_lock(path,True),0)

    def test_block_inspection_of_uncertain_sync_has_no_completion_or_retry_authority(self):
        with self.fixture() as (parent,path,fd):
            original=path.read_bytes();write=self.authority(path)
            with patch.object(control,'load_block_authority',return_value=write), \
                 patch.object(control.os,'fsync',side_effect=OSError('synthetic-sync-failure')):
                with self.assertRaises(OSError):control.block_admission()
            with patch.object(control,'load_block_inspection',return_value=self.inspection_authority(original)):
                result=control.inspect_admission_block(original)
            self.assertEqual(result['status'],'blocked_matches')
            self.assertFalse(result['completion_confirmed']);self.assertFalse(result['retry_authorized'])
            self.assertFalse(result['reopening_authorized'])
            with self.assertRaises(ValueError):
                with control.admission():self.fail('observed block must remain blocked')
