"""Actual scratch filesystem publication; all authority/custody inputs synthetic."""
import contextlib
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'ops/runtime'))
import control
import publication
import record_bundle
import test_control_admission as admission_tests
import test_process_probe as process_tests


class PublicationTests(unittest.TestCase):
    @contextlib.contextmanager
    def fixture(self):
        barrier_fixture=admission_tests.ControlAdmissionTests()
        with barrier_fixture.fixture() as (base,path,parent):
            old_value=process_tests.candidate_bundle()
            old_payloads,_=record_bundle.prepare_records(json.dumps(old_value).encode())
            gid=old_value['records']['expected.json']['gid']
            original=json.dumps({'schema_version':1,'state':'admitted','generation':'a'*64,
                'record_sha256':{name:hashlib.sha256(raw).hexdigest() for name,raw in old_payloads.items()}}).encode()
            blocked=control._blocked_bytes(original,'b'*32);path.write_bytes(blocked)
            old=base/'control';old.mkdir(mode=0o750);os.chown(old,-1,gid)
            for name,raw in old_payloads.items():
                file=old/name;file.write_bytes(raw);file.chmod(0o440);os.chown(file,-1,gid)
            new_value=copy.deepcopy(old_value);new_value['records']['database-process.json']['process']['pid']+=10
            data=json.dumps(new_value).encode();payloads,_=record_bundle.prepare_records(data)
            evidence=b'SYNTHETIC_REVIEWED_CUSTODY_EVIDENCE'
            info=old.stat();parent_info=os.fstat(parent)
            authority={'schema_version':1,'action':'publish-control-generation','authorization_id':'f'*32,
                'expires_at':barrier_fixture.authority(path)['expires_at'],
                'bundle_sha256':hashlib.sha256(data).hexdigest(),
                'original_admission_sha256':hashlib.sha256(original).hexdigest(),
                'blocked_admission_sha256':hashlib.sha256(blocked).hexdigest(),
                'custody_evidence_sha256':hashlib.sha256(evidence).hexdigest(),
                'parent':{'device':parent_info.st_dev,'inode':parent_info.st_ino},
                'prior_directory':{'device':info.st_dev,'inode':info.st_ino,'gid':gid,'mode':0o750},
                'prior_files_sha256':{name:hashlib.sha256(raw).hexdigest() for name,raw in old_payloads.items()},
                'read_gid':gid}
            file=base/'control-publication.json';file.write_bytes(json.dumps(authority).encode());file.chmod(0o440)
            actual_open=os.open
            def adapt(name,flags,*args,**kwargs):
                if name in ('/','srv','shop'):return os.dup(parent)
                return actual_open(name,flags,*args,**kwargs)
            with patch.object(control.os,'open',side_effect=adapt):
                yield dict(base=base,barrier=path,parent=parent,authority=authority,authority_file=file,
                    original=original,blocked=blocked,data=data,payloads=payloads,old=old,
                    old_payloads=old_payloads,evidence=evidence,gid=gid,barrier_fixture=barrier_fixture)

    def publish(self,case):
        return publication.publish_control_generation(case['data'],case['original'],case['evidence'])

    def test_actual_publication_preserves_whole_prior_directory_and_blocked_barrier(self):
        with self.fixture() as case:
            prior_inode=case['old'].stat().st_ino;barrier_before=case['barrier'].stat()
            result=self.publish(case)
            self.assertEqual(result['status'],'control_published_blocked')
            previous=case['base']/('control-previous-'+case['authority']['original_admission_sha256'])
            self.assertEqual(previous.stat().st_ino,prior_inode)
            self.assertEqual(set(p.name for p in previous.iterdir()),set(case['old_payloads']))
            for name,raw in case['old_payloads'].items():self.assertEqual((previous/name).read_bytes(),raw)
            for name,raw in case['payloads'].items():
                file=case['old']/name
                self.assertEqual(file.read_bytes(),raw);self.assertEqual(file.stat().st_uid,0)
                self.assertEqual(file.stat().st_gid,case['gid']);self.assertEqual(file.stat().st_mode&0o777,0o440)
            self.assertEqual(case['old'].stat().st_mode&0o777,0o750)
            self.assertEqual(case['barrier'].read_bytes(),case['blocked'])
            self.assertEqual(case['barrier'].stat().st_ino,barrier_before.st_ino)
            for flag in ('durability_qualified','publication_authorized','retry_authorized','reopening_authorized'):
                self.assertFalse(result[flag])
            with self.assertRaises(ValueError):
                with control.admission():self.fail('publisher must not reopen admission')
            with self.assertRaises((ValueError,FileExistsError)):self.publish(case)

    def test_exact_scope_custody_candidate_and_block_required(self):
        for kind in ('candidate','original','evidence','admitted','authority','root'):
            with self.subTest(kind=kind),self.fixture() as case:
                before=case['old'].stat().st_ino
                if kind=='candidate':case['data']+=b' '
                elif kind=='original':case['original']+=b' '
                elif kind=='evidence':case['evidence']+=b' '
                elif kind=='admitted':case['barrier'].write_bytes(case['original'])
                elif kind=='authority':
                    changed=dict(case['authority'],expires_at='2000-01-01T00:00:00Z')
                    case['authority_file'].write_bytes(json.dumps(changed).encode())
                manager=patch.object(publication.os,'geteuid',return_value=9909) if kind=='root' else contextlib.nullcontext()
                with manager,self.assertRaises(ValueError):self.publish(case)
                self.assertEqual(case['old'].stat().st_ino,before)
                self.assertFalse(any(p.name.startswith('control-next-') for p in case['base'].iterdir()))

    def test_unknown_or_changed_prior_files_denied_without_staging(self):
        for kind in ('extra','bytes','linked','mode'):
            with self.subTest(kind=kind),self.fixture() as case:
                file=case['old']/'expected.json'
                if kind=='extra':(case['old']/'unknown.json').write_bytes(b'protected')
                elif kind=='bytes':file.write_bytes(b'{}')
                elif kind=='linked':os.link(file,case['base']/'protected-link')
                else:case['old'].chmod(0o700)
                with self.assertRaises(ValueError):self.publish(case)
                self.assertFalse(any(p.name.startswith('control-next-') for p in case['base'].iterdir()))
                self.assertEqual(case['barrier'].read_bytes(),case['blocked'])

    def test_preexisting_stage_or_previous_object_preserved(self):
        for label,kind in (('next','file'),('next','symlink'),('previous','directory')):
            with self.subTest(label=label,kind=kind),self.fixture() as case:
                digest=case['authority']['bundle_sha256' if label=='next' else 'original_admission_sha256']
                target=case['base']/('control-'+label+'-'+digest)
                if kind=='file':target.write_bytes(b'protected')
                elif kind=='symlink':target.symlink_to('unrelated')
                else:target.mkdir()
                with self.assertRaises(FileExistsError):self.publish(case)
                if kind=='file':self.assertEqual(target.read_bytes(),b'protected')
                elif kind=='symlink':self.assertEqual(os.readlink(target),'unrelated')
                else:self.assertEqual(list(target.iterdir()),[])

    def test_publication_excludes_reader_and_retains_block_on_stage_failure(self):
        with self.fixture() as case:
            actual_stage=record_bundle._stage_file
            def stage(*args,**kwargs):
                self.assertEqual(case['barrier_fixture'].child_lock(case['barrier'],False),3)
                return actual_stage(*args,**kwargs)
            with patch.object(record_bundle,'_stage_file',side_effect=stage):self.publish(case)
        with self.fixture() as case,patch.object(publication.os,'fsync',side_effect=OSError('synthetic-sync-failure')):
            with self.assertRaises(OSError):self.publish(case)
            self.assertTrue(case['old'].is_dir())
            self.assertTrue(any(p.name.startswith('control-next-') for p in case['base'].iterdir()))
            self.assertEqual(case['barrier'].read_bytes(),case['blocked'])

    def test_failure_between_renames_retains_previous_and_stage_without_repair(self):
        with self.fixture() as case:
            actual_rename=publication._rename_no_replace;calls=[]
            def rename(parent,source,destination):
                calls.append(source)
                if len(calls)==2:raise OSError('synthetic-second-rename-failure')
                return actual_rename(parent,source,destination)
            with patch.object(publication,'_rename_no_replace',side_effect=rename):
                with self.assertRaises(OSError):self.publish(case)
            self.assertFalse(case['old'].exists())
            previous=case['base']/('control-previous-'+case['authority']['original_admission_sha256'])
            self.assertTrue(previous.is_dir())
            self.assertTrue(any(p.name.startswith('control-next-') for p in case['base'].iterdir()))
            self.assertEqual(case['barrier'].read_bytes(),case['blocked'])
            with self.assertRaises(FileNotFoundError):self.publish(case)

    def test_no_replace_protects_unknown_control_inserted_between_renames(self):
        with self.fixture() as case:
            actual_rename=publication._rename_no_replace;calls=[]
            def rename(parent,source,destination):
                result=actual_rename(parent,source,destination);calls.append(source)
                if len(calls)==1:
                    case['old'].mkdir();(case['old']/'protected').write_bytes(b'unknown-owner-object')
                return result
            with patch.object(publication,'_rename_no_replace',side_effect=rename):
                with self.assertRaises(OSError):self.publish(case)
            self.assertEqual((case['old']/'protected').read_bytes(),b'unknown-owner-object')
            self.assertEqual(case['barrier'].read_bytes(),case['blocked'])

    def test_late_authority_revocation_never_reopens_or_rolls_back_records(self):
        with self.fixture() as case:
            actual_rename=publication._rename_no_replace
            def rename(parent,source,destination):
                result=actual_rename(parent,source,destination)
                if destination=='control':
                    changed=dict(case['authority'],authorization_id='a'*32)
                    case['authority_file'].write_bytes(json.dumps(changed).encode())
                return result
            with patch.object(publication,'_rename_no_replace',side_effect=rename):
                with self.assertRaises(ValueError):self.publish(case)
            self.assertEqual((case['old']/'expected.json').read_bytes(),case['payloads']['expected.json'])
            self.assertEqual(case['barrier'].read_bytes(),case['blocked'])
