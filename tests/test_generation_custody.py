"""Actual private scratch custody; root paths/authority fixture-adapted."""
import contextlib
import hashlib
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'ops/runtime'))
import control
import record_bundle as bundle
import test_control_admission as admission_tests


class GenerationCustodyTests(unittest.TestCase):
    @contextlib.contextmanager
    def fixture(self):
        barrier=admission_tests.ControlAdmissionTests()
        with barrier.fixture() as (base,path,basefd):
            parent=base/'custody';parent.mkdir(mode=0o700)
            fd=os.open(parent,os.O_RDONLY|os.O_DIRECTORY|os.O_CLOEXEC)
            try:
                manifest=json.loads(path.read_bytes())
                for name in manifest['record_sha256']:
                    record=base/name;record.write_bytes(b'{}');record.chmod(0o440)
                info=os.fstat(fd)
                authority={'schema_version':1,'action':'retain-control-generation',
                    'authorization_id':'d'*32,'expires_at':barrier.authority(path)['expires_at'],
                    'admission_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                    'parent':{'device':info.st_dev,'inode':info.st_ino}}
                auth=base/'generation-custody.json';auth.write_bytes(json.dumps(authority).encode());auth.chmod(0o440)
                real_open=os.open
                def adapted(name,flags,*args,**kwargs):
                    if name in ('/','srv','shop','control'):return os.dup(basefd)
                    return real_open(name,flags,*args,**kwargs)
                with patch.object(control.os,'open',side_effect=adapted):
                    yield base,path,parent,fd,auth,authority,barrier
            finally:os.close(fd)

    def test_actual_exact_generation_and_authority_retained_exclusively(self):
        with self.fixture() as (base,path,parent,fd,auth,authority,barrier):
            original=path.read_bytes();authority_raw=auth.read_bytes()
            with patch.object(bundle.operator_inspect.psycopg,'connect',side_effect=AssertionError('no database')):
                result=bundle.retain_control_generation(fd)
            target=parent/('generation-'+authority['admission_sha256'])
            self.assertEqual(result['status'],'generation_retained')
            self.assertEqual((target/'admission.json').read_bytes(),original)
            self.assertEqual((target/'custody-authorization.json').read_bytes(),authority_raw)
            self.assertEqual(json.loads((target/'retained.json').read_bytes()),result)
            self.assertEqual(set(item.name for item in target.iterdir()),set(result['file_sha256'])|{'retained.json'})
            for name,digest in result['file_sha256'].items():
                self.assertEqual(hashlib.sha256((target/name).read_bytes()).hexdigest(),digest)
            for item in target.iterdir():
                self.assertEqual(item.stat().st_uid,0);self.assertEqual(item.stat().st_mode & 0o777,0o400)
            self.assertTrue(result['local_fsync_readback_completed'])
            for flag in ('durability_qualified','publication_authorized','retry_authorized','reopening_authorized'):
                self.assertFalse(result[flag])
            with self.assertRaises(FileExistsError):bundle.retain_control_generation(fd)
            self.assertEqual(path.read_bytes(),original)
            os.fstat(fd)

    def test_capture_holds_lease_and_exact_hash_missing_or_changed_records_deny(self):
        with self.fixture() as (base,path,parent,fd,auth,authority,barrier):
            real_read=control.load_control_bytes
            def read(name):
                if name!='generation-custody.json':
                    self.assertEqual(barrier.child_lock(path,True),3)
                return real_read(name)
            with patch.object(control,'load_control_bytes',side_effect=read):
                bundle.retain_control_generation(fd)
        for kind in ('changed','missing'):
            with self.subTest(kind=kind),self.fixture() as (base,path,parent,fd,auth,authority,barrier):
                record=base/'expected.json'
                if kind=='changed':record.write_bytes(b'{ }')
                else:record.unlink()
                with self.assertRaises((ValueError,FileNotFoundError)):bundle.retain_control_generation(fd)
                self.assertEqual(list(parent.iterdir()),[])

    def test_authority_expiry_parent_and_nonroot_denied_before_writes(self):
        with self.fixture() as (base,path,parent,fd,auth,authority,barrier):
            for change in ({'schema_version':True},{'action':'publish-control-generation'},
                           {'admission_sha256':'e'*64},{'expires_at':'2000-01-01T00:00:00Z'},
                           {'parent':{'device':authority['parent']['device'],'inode':authority['parent']['inode']+1}}):
                auth.write_bytes(json.dumps(dict(authority,**change)).encode())
                with self.subTest(change=change),self.assertRaises(ValueError):bundle.retain_control_generation(fd)
                self.assertEqual(list(parent.iterdir()),[])
            auth.write_bytes(json.dumps(authority).encode())
            with patch.object(bundle.os,'geteuid',return_value=9909):
                with self.assertRaises(ValueError):bundle.retain_control_generation(fd)
            parent.chmod(0o750)
            with self.assertRaises(ValueError):bundle.retain_control_generation(fd)
            self.assertEqual(list(parent.iterdir()),[])

    def test_preexisting_unknown_file_symlink_or_directory_is_not_adopted(self):
        for kind in ('file','symlink','directory'):
            with self.subTest(kind=kind),self.fixture() as (base,path,parent,fd,auth,authority,barrier):
                target=parent/('generation-'+authority['admission_sha256'])
                if kind=='file':target.write_bytes(b'protected')
                elif kind=='symlink':target.symlink_to('unrelated')
                else:target.mkdir()
                with self.assertRaises(FileExistsError):bundle.retain_control_generation(fd)
                if kind=='file':self.assertEqual(target.read_bytes(),b'protected')
                elif kind=='symlink':self.assertEqual(os.readlink(target),'unrelated')
                else:self.assertEqual(list(target.iterdir()),[])

    def test_short_writes_work_and_sync_failure_retains_partial_without_repeat(self):
        real_write=os.write
        with self.fixture() as (base,path,parent,fd,auth,authority,barrier), \
             patch.object(bundle.os,'write',side_effect=lambda fd,data:real_write(fd,data[:11])):
            self.assertEqual(bundle.retain_control_generation(fd)['status'],'generation_retained')
        with self.fixture() as (base,path,parent,fd,auth,authority,barrier):
            with patch.object(bundle.os,'fsync',side_effect=OSError('synthetic-sync-failure')):
                with self.assertRaises(OSError):bundle.retain_control_generation(fd)
            self.assertEqual(len(list(parent.iterdir())),1)
            with self.assertRaises(FileExistsError):bundle.retain_control_generation(fd)
            self.assertEqual(json.loads(path.read_bytes())['state'],'admitted')

    def test_authority_revocation_before_and_after_local_retention(self):
        for changed_at in (2,3):
            with self.subTest(changed_at=changed_at),self.fixture() as (base,path,parent,fd,auth,authority,barrier):
                raw=auth.read_bytes();calls=[]
                def authority_read():
                    calls.append(True)
                    if len(calls)==changed_at:raise ValueError('synthetic-authority-revoked')
                    return raw,authority
                with patch.object(bundle,'load_custody_authority',side_effect=authority_read):
                    with self.assertRaises(ValueError):bundle.retain_control_generation(fd)
                self.assertEqual(len(list(parent.iterdir())),0 if changed_at==2 else 1)
                self.assertEqual(barrier.child_lock(path,True),0)

    def test_receipt_left_after_parent_sync_failure_is_not_success_or_retry(self):
        with self.fixture() as (base,path,parent,fd,auth,authority,barrier):
            actual_sync=os.fsync;calls=[]
            def sync(descriptor):
                calls.append(True)
                if len(calls)==9:raise OSError('synthetic-parent-sync-failure')
                return actual_sync(descriptor)
            with patch.object(bundle.os,'fsync',side_effect=sync):
                with self.assertRaises(OSError):bundle.retain_control_generation(fd)
            target=parent/('generation-'+authority['admission_sha256'])
            self.assertTrue((target/'retained.json').is_file())
            self.assertEqual(json.loads((target/'retained.json').read_bytes())['status'],'generation_retained')
            with self.assertRaises(FileExistsError):bundle.retain_control_generation(fd)
            self.assertEqual(json.loads(path.read_bytes())['state'],'admitted')

    def original_material(self,parent,authority):
        target=parent/('generation-'+authority['admission_sha256'])
        report=json.loads((target/'retained.json').read_bytes())
        files={name:(target/name).read_bytes() for name in report['file_sha256']}
        inspection={key:value for key,value in authority.items()}
        inspection.update(action='inspect-control-generation',authorization_id='e'*32,
                          retained_authority_sha256=hashlib.sha256(files['custody-authorization.json']).hexdigest())
        return target,files,inspection

    def test_readonly_inspection_matches_and_never_writes_syncs_or_reads_live_authority(self):
        with self.fixture() as (base,path,parent,fd,auth,authority,barrier):
            bundle.retain_control_generation(fd)
            target,files,inspection=self.original_material(parent,authority)
            before={p.name:(p.read_bytes(),p.stat().st_mtime_ns,p.stat().st_ctime_ns) for p in target.iterdir()}
            with patch.object(bundle,'load_custody_inspection',return_value=inspection), \
                 patch.object(bundle,'load_custody_authority',side_effect=AssertionError('old/live write authority unused')), \
                 patch.object(bundle.os,'fsync',side_effect=AssertionError('no sync')), \
                 patch.object(bundle.os,'write',side_effect=AssertionError('no write')), \
                 patch.object(bundle.os,'mkdir',side_effect=AssertionError('no create')):
                result=bundle.inspect_retained_generation(files,fd)
            self.assertEqual(result['status'],'generation_matches')
            for flag in ('completion_confirmed','durability_qualified','publication_authorized',
                         'retry_authorized','reopening_authorized','local_fsync_readback_completed'):
                self.assertFalse(result[flag])
            self.assertEqual(before,{p.name:(p.read_bytes(),p.stat().st_mtime_ns,p.stat().st_ctime_ns) for p in target.iterdir()})
            os.fstat(fd)

    def test_inspection_accepts_expired_historical_write_authority_with_fresh_independent_authority(self):
        from datetime import datetime,timezone
        with self.fixture() as (base,path,parent,fd,auth,authority,barrier):
            bundle.retain_control_generation(fd)
            target,files,inspection=self.original_material(parent,authority)
            inspection['expires_at']='2028-01-01T00:00:00Z'
            with patch.object(control,'datetime',wraps=datetime) as clock, \
                 patch.object(bundle,'load_custody_inspection',side_effect=lambda:bundle.validate_custody_inspection(inspection)):
                clock.now.return_value=datetime(2027,1,1,tzinfo=timezone.utc)
                with self.assertRaises(ValueError):bundle.validate_custody_authority(authority)
                self.assertEqual(bundle.inspect_retained_generation(files,fd)['status'],'generation_matches')

    def test_inspection_after_uncertain_parent_sync_never_confirms_completion(self):
        with self.fixture() as (base,path,parent,fd,auth,authority,barrier):
            real_sync=os.fsync;calls=[]
            def sync(descriptor):
                calls.append(True)
                if len(calls)==9:raise OSError('synthetic-parent-sync-failure')
                return real_sync(descriptor)
            with patch.object(bundle.os,'fsync',side_effect=sync):
                with self.assertRaises(OSError):bundle.retain_control_generation(fd)
            target,files,inspection=self.original_material(parent,authority)
            with patch.object(bundle,'load_custody_inspection',return_value=inspection):
                result=bundle.inspect_retained_generation(files,fd)
            self.assertEqual(result['status'],'generation_matches')
            self.assertFalse(result['completion_confirmed']);self.assertFalse(result['retry_authorized'])
            with self.assertRaises(FileExistsError):bundle.retain_control_generation(fd)

    def test_inspection_exact_original_authority_parent_and_closed_files(self):
        with self.fixture() as (base,path,parent,fd,auth,authority,barrier):
            bundle.retain_control_generation(fd)
            target,files,inspection=self.original_material(parent,authority)
            self.assertEqual(bundle.validate_custody_inspection(inspection),inspection)
            for change in ({'action':'retain-control-generation'},{'expires_at':'2000-01-01T00:00:00Z'},
                           {'retained_authority_sha256':'bad'},{'extra':True}):
                with self.subTest(change=change),self.assertRaises(ValueError):bundle.validate_custody_inspection(dict(inspection,**change))
            for original in (dict(files,**{'expected.json':b'{ }'}),dict(files,**{'extra':b'{}'}),
                             {name:data for name,data in files.items() if name!='expected.json'},
                             dict(files,**{'custody-authorization.json':files['custody-authorization.json']+b' '})):
                with patch.object(bundle,'load_custody_inspection',return_value=inspection):
                    with self.assertRaises(ValueError):bundle.inspect_retained_generation(original,fd)
            wrong=dict(inspection,parent=dict(inspection['parent'],inode=inspection['parent']['inode']+1))
            with patch.object(bundle,'load_custody_inspection',return_value=wrong):
                with self.assertRaises(ValueError):bundle.inspect_retained_generation(files,fd)

    def test_inspection_denies_tampered_incomplete_extra_or_linked_archive(self):
        for kind in ('bytes','missing','extra','mode','symlink','hardlink','fifo','receipt'):
            with self.subTest(kind=kind),self.fixture() as (base,path,parent,fd,auth,authority,barrier):
                bundle.retain_control_generation(fd)
                target,files,inspection=self.original_material(parent,authority)
                file=target/'expected.json'
                if kind=='bytes':file.write_bytes(b'{ }')
                elif kind=='missing':file.unlink()
                elif kind=='extra':(target/'extra').write_bytes(b'{}')
                elif kind=='mode':file.chmod(0o600)
                elif kind=='symlink':file.unlink();file.symlink_to(base/'expected.json')
                elif kind=='hardlink':os.link(file,base/'linked')
                elif kind=='fifo':file.unlink();os.mkfifo(file)
                else:(target/'retained.json').write_bytes(b'{}')
                with patch.object(bundle,'load_custody_inspection',return_value=inspection):
                    with self.assertRaises((ValueError,OSError)):bundle.inspect_retained_generation(files,fd)

    def test_inspection_denies_authority_revocation_and_generation_replacement(self):
        for kind in ('revoke','replace'):
            with self.subTest(kind=kind),self.fixture() as (base,path,parent,fd,auth,authority,barrier):
                bundle.retain_control_generation(fd)
                target,files,inspection=self.original_material(parent,authority)
                reads=[];real_read=bundle._readback_files
                def read(directory,payloads):
                    real_read(directory,payloads)
                    if kind=='replace':
                        target.rename(parent/'moved');target.mkdir(mode=0o700)
                def recheck():
                    reads.append(True)
                    return dict(inspection,authorization_id='f'*32) if len(reads)>1 else inspection
                with patch.object(bundle,'load_custody_inspection',side_effect=recheck), \
                     patch.object(bundle,'_readback_files',side_effect=read):
                    with self.assertRaises(ValueError):bundle.inspect_retained_generation(files,fd)
