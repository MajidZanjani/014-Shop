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

    def inspection(self,case):
        raw=case['authority_file'].read_bytes()
        value={'schema_version':1,'action':'inspect-control-publication',
            'authorization_id':'e'*32,'expires_at':case['authority']['expires_at'],
            'publication_authority_sha256':hashlib.sha256(raw).hexdigest()}
        file=case['base']/'control-publication-inspection.json'
        file.write_bytes(json.dumps(value).encode());file.chmod(0o440)
        return raw,file

    def observe(self,case,raw):
        return publication.inspect_publication(case['data'],case['original'],raw)

    def test_read_only_observation_of_each_interrupted_state(self):
        for state in ('original_matches','stage_matches','prior_moved_matches','published_matches','conflicting'):
            with self.subTest(state=state),self.fixture() as case:
                raw,_=self.inspection(case)
                if state in ('stage_matches','prior_moved_matches'):
                    actual=publication._rename_no_replace;calls=[]
                    def rename(*args):
                        calls.append(args)
                        if len(calls)==(1 if state=='stage_matches' else 2):raise OSError('synthetic interruption')
                        return actual(*args)
                    with patch.object(publication,'_rename_no_replace',side_effect=rename):
                        with self.assertRaises(OSError):self.publish(case)
                elif state=='published_matches':self.publish(case)
                elif state=='conflicting':(case['old']/'unknown').write_bytes(b'protected')
                before=case['barrier'].read_bytes()
                with patch.object(publication,'load_authority',side_effect=AssertionError('historical lookup')), \
                     patch.object(os,'write',side_effect=AssertionError('write')), \
                     patch.object(os,'pwrite',side_effect=AssertionError('pwrite')), \
                     patch.object(os,'fsync',side_effect=AssertionError('sync')), \
                     patch.object(os,'mkdir',side_effect=AssertionError('mkdir')), \
                     patch.object(publication,'_rename_no_replace',side_effect=AssertionError('rename')):
                    result=self.observe(case,raw)
                self.assertEqual(result['status'],state)
                for key,value in result.items():
                    if key not in ('status','schema_version'):self.assertIs(value,False)
                self.assertEqual(case['barrier'].read_bytes(),before)

    def test_inspection_requires_fresh_exact_independent_scope(self):
        for kind in ('expired','extra','digest','candidate','original','root'):
            with self.subTest(kind=kind),self.fixture() as case:
                raw,file=self.inspection(case)
                value=json.loads(file.read_bytes())
                if kind=='expired':value['expires_at']='2000-01-01T00:00:00Z'
                elif kind=='extra':value['extra']=True
                elif kind=='digest':value['publication_authority_sha256']='0'*64
                elif kind=='candidate':case['data']+=b' '
                elif kind=='original':case['original']+=b' '
                file.write_bytes(json.dumps(value).encode())
                manager=patch.object(os,'geteuid',return_value=9909) if kind=='root' else contextlib.nullcontext()
                with manager,self.assertRaises(ValueError):self.observe(case,raw)

    def test_inspection_shared_lease_excludes_writer(self):
        with self.fixture() as case:
            raw,_=self.inspection(case);actual=publication._observe_directory
            def observe(*args):
                self.assertEqual(case['barrier_fixture'].child_lock(case['barrier'],True),3)
                return actual(*args)
            with patch.object(publication,'_observe_directory',side_effect=observe):self.observe(case,raw)

    def test_inspection_denies_late_revocation_and_changed_bytes(self):
        for kind in ('revocation','bytes','symlink','hardlink'):
            with self.subTest(kind=kind),self.fixture() as case:
                raw,file=self.inspection(case);actual=publication.load_inspection;calls=[]
                target=case['old']/'expected.json'
                if kind=='symlink':target.unlink();target.symlink_to(case['authority_file'])
                elif kind=='hardlink':os.link(target,case['base']/'protected-link')
                def load():
                    calls.append(1)
                    if len(calls)==2:
                        if kind=='revocation':
                            value=json.loads(file.read_bytes());value['authorization_id']='d'*32
                            file.write_bytes(json.dumps(value).encode())
                        elif kind=='bytes':target.write_bytes(b'{}')
                    return actual()
                with patch.object(publication,'load_inspection',side_effect=load),self.assertRaises((ValueError,OSError)):
                    self.observe(case,raw)

    def test_historical_expiry_is_not_renewed_by_observation(self):
        with self.fixture() as case:
            case['authority']['expires_at']='2000-01-01T00:00:00Z'
            case['authority_file'].write_bytes(json.dumps(case['authority']).encode())
            raw,file=self.inspection(case)
            value=json.loads(file.read_bytes());value['expires_at']=case['barrier_fixture'].authority(case['barrier'])['expires_at']
            file.write_bytes(json.dumps(value).encode())
            self.assertEqual(self.observe(case,raw)['status'],'original_matches')
            with self.assertRaises(ValueError):publication.validate_authority(case['authority'])

    def test_partial_stage_and_replaced_original_remain_conflicting(self):
        for kind in ('partial','replacement'):
            with self.subTest(kind=kind),self.fixture() as case:
                raw,_=self.inspection(case)
                if kind=='partial':
                    with patch.object(os,'fsync',side_effect=OSError('synthetic-sync')):
                        with self.assertRaises(OSError):self.publish(case)
                else:
                    case['old'].rename(case['base']/'retained-original')
                    case['old'].mkdir(mode=0o750);os.chown(case['old'],-1,case['gid'])
                    for name,data in case['old_payloads'].items():
                        file=case['old']/name;file.write_bytes(data);file.chmod(0o440);os.chown(file,-1,case['gid'])
                self.assertEqual(self.observe(case,raw)['status'],'conflicting')

    def test_existing_exclusive_lease_denies_inspection(self):
        import fcntl
        with self.fixture() as case:
            raw,_=self.inspection(case)
            with case['barrier'].open('rb') as barrier:
                fcntl.flock(barrier,fcntl.LOCK_EX|fcntl.LOCK_NB)
                with self.assertRaises(BlockingIOError):self.observe(case,raw)
            self.assertEqual(self.observe(case,raw)['status'],'original_matches')

    def preparation(self,case):
        historical,_=self.inspection(case)
        _,report=record_bundle.prepare_records(case['data'])
        proposed=json.dumps({'schema_version':1,'state':'admitted',
            'generation':report['bundle_sha256'],'record_sha256':report['record_sha256']},
            sort_keys=True,separators=(',',':')).encode('ascii')+b'\n'
        evidence=b'SYNTHETIC_EXTERNAL_QUALIFICATION_REVIEW_ONLY'
        approval={'schema_version':1,'action':'prepare-control-admission','authorization_id':'c'*32,
            'expires_at':case['authority']['expires_at'],
            'publication_authority_sha256':hashlib.sha256(historical).hexdigest(),
            'proposed_admission_sha256':hashlib.sha256(proposed).hexdigest(),
            'qualification_evidence_sha256':hashlib.sha256(evidence).hexdigest()}
        file=case['base']/'control-admission-preparation.json'
        file.write_bytes(json.dumps(approval).encode());file.chmod(0o440)
        return historical,proposed,evidence,file

    def test_exact_preparation_returns_bytes_without_any_activation(self):
        with self.fixture() as case:
            historical,proposed,evidence,_=self.preparation(case);self.publish(case)
            with patch.object(os,'write',side_effect=AssertionError('write')), \
                 patch.object(os,'pwrite',side_effect=AssertionError('pwrite')), \
                 patch.object(os,'fsync',side_effect=AssertionError('sync')), \
                 patch.object(os,'mkdir',side_effect=AssertionError('mkdir')), \
                 patch.object(publication,'load_authority',side_effect=AssertionError('old authority')):
                raw,result=publication.prepare_reopening(case['data'],case['original'],historical,evidence)
            self.assertEqual(raw,proposed)
            self.assertEqual(control._validate_admitted(raw)['record_sha256'],
                {name:hashlib.sha256(data).hexdigest() for name,data in case['payloads'].items()})
            self.assertEqual(result['status'],'admission_bytes_prepared')
            for key,value in result.items():
                if key not in ('schema_version','status','proposed_admission_sha256'):self.assertIs(value,False)
            self.assertEqual(case['barrier'].read_bytes(),case['blocked'])
            with self.assertRaises(ValueError):
                with control.admission():self.fail('preparation must remain blocked')

    def test_preparation_denies_unpublished_partial_and_changed_generations(self):
        for kind in ('original','stage','moved','partial','changed'):
            with self.subTest(kind=kind),self.fixture() as case:
                historical,_,evidence,_=self.preparation(case)
                if kind in ('stage','moved'):
                    actual=publication._rename_no_replace;calls=[]
                    def rename(*args):
                        calls.append(1)
                        if len(calls)==(1 if kind=='stage' else 2):raise OSError('interrupted')
                        return actual(*args)
                    with patch.object(publication,'_rename_no_replace',side_effect=rename):
                        with self.assertRaises(OSError):self.publish(case)
                elif kind=='partial':
                    with patch.object(os,'fsync',side_effect=OSError('sync')):
                        with self.assertRaises(OSError):self.publish(case)
                elif kind=='changed':
                    self.publish(case);(case['old']/'expected.json').write_bytes(b'{}')
                with self.assertRaises(ValueError):
                    publication.prepare_reopening(case['data'],case['original'],historical,evidence)
                self.assertEqual(case['barrier'].read_bytes(),case['blocked'])

    def test_preparation_requires_exact_fresh_independent_approval(self):
        for kind in ('expired','extra','proposal','historical','evidence','candidate','original','root'):
            with self.subTest(kind=kind),self.fixture() as case:
                historical,_,evidence,file=self.preparation(case);self.publish(case)
                value=json.loads(file.read_bytes())
                if kind=='expired':value['expires_at']='2000-01-01T00:00:00Z'
                elif kind=='extra':value['extra']=True
                elif kind=='proposal':value['proposed_admission_sha256']='0'*64
                elif kind=='historical':historical+=b' '
                elif kind=='evidence':evidence+=b' '
                elif kind=='candidate':case['data']+=b' '
                elif kind=='original':case['original']+=b' '
                file.write_bytes(json.dumps(value).encode())
                manager=patch.object(os,'geteuid',return_value=9909) if kind=='root' else contextlib.nullcontext()
                with manager,self.assertRaises(ValueError):
                    publication.prepare_reopening(case['data'],case['original'],historical,evidence)
                self.assertEqual(case['barrier'].read_bytes(),case['blocked'])

    def test_preparation_revalidates_candidate_and_late_approval(self):
        for kind in ('candidate','approval'):
            with self.subTest(kind=kind),self.fixture() as case:
                historical,_,evidence,file=self.preparation(case);self.publish(case)
                actual=record_bundle.prepare_records;calls=[]
                def validate(data):
                    calls.append(1)
                    if len(calls)==2:
                        if kind=='candidate':raise ValueError('synthetic-expired-inner-authority')
                        value=json.loads(file.read_bytes());value['authorization_id']='d'*32
                        file.write_bytes(json.dumps(value).encode())
                    return actual(data)
                with patch.object(record_bundle,'prepare_records',side_effect=validate),self.assertRaises(ValueError):
                    publication.prepare_reopening(case['data'],case['original'],historical,evidence)
                self.assertEqual(case['barrier'].read_bytes(),case['blocked'])

    def test_preparation_excludes_writer_through_final_validation(self):
        with self.fixture() as case:
            historical,_,evidence,_=self.preparation(case);self.publish(case)
            actual=record_bundle.prepare_records;calls=[]
            def validate(data):
                calls.append(1)
                if len(calls)>1:self.assertEqual(case['barrier_fixture'].child_lock(case['barrier'],True),3)
                return actual(data)
            with patch.object(record_bundle,'prepare_records',side_effect=validate):
                publication.prepare_reopening(case['data'],case['original'],historical,evidence)

    def test_preparation_rejects_actually_expired_inner_authority(self):
        from datetime import datetime,timedelta,timezone
        import schema_authorization
        with self.fixture() as case:
            historical,_,evidence,_=self.preparation(case);self.publish(case)
            candidate=json.loads(case['data'])
            expiry=candidate['records']['schema-reconciliation.json']['expires_at']
            future=datetime.strptime(expiry,'%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)+timedelta(seconds=1)
            with patch.object(schema_authorization,'datetime',wraps=datetime) as clock:
                clock.now.return_value=future
                # Historical observation still compares bytes; preparation must
                # independently perform current semantic/expiry validation.
                self.assertEqual(self.observe(case,historical)['status'],'published_matches')
                with self.assertRaises(ValueError):
                    publication.prepare_reopening(case['data'],case['original'],historical,evidence)
            self.assertEqual(case['barrier'].read_bytes(),case['blocked'])

    def reopening(self,case):
        historical,proposed,qualification,preparation_file=self.preparation(case)
        recovery=b'SYNTHETIC_REOPENING_RECOVERY_REVIEW'
        authority={'schema_version':1,'action':'reopen-control-admission','authorization_id':'9'*32,
            'expires_at':case['authority']['expires_at'],
            'preparation_authority_sha256':hashlib.sha256(preparation_file.read_bytes()).hexdigest(),
            'blocked_admission_sha256':hashlib.sha256(case['blocked']).hexdigest(),
            'proposed_admission_sha256':hashlib.sha256(proposed).hexdigest(),
            'recovery_evidence_sha256':hashlib.sha256(recovery).hexdigest()}
        file=case['base']/'control-admission-reopening.json'
        raw=json.dumps(authority).encode();file.write_bytes(raw);file.chmod(0o440)
        inspection={'schema_version':1,'action':'inspect-control-admission-reopening','authorization_id':'8'*32,
            'expires_at':authority['expires_at'],'reopening_authority_sha256':hashlib.sha256(raw).hexdigest()}
        inspect_file=case['base']/'control-admission-reopening-inspection.json'
        inspect_file.write_bytes(json.dumps(inspection).encode());inspect_file.chmod(0o440)
        return dict(historical=historical,proposed=proposed,qualification=qualification,
            recovery=recovery,authority=authority,raw=raw,file=file,inspect_file=inspect_file)

    def reopen(self,case,setup):
        return publication.reopen_admission(case['data'],case['original'],setup['historical'],
            setup['qualification'],setup['recovery'])

    def observe_reopening(self,case,setup):
        return publication.inspect_reopening(case['blocked'],setup['proposed'],setup['raw'])

    def test_actual_reopening_keeps_permanent_inode_and_exact_manifest(self):
        with self.fixture() as case:
            setup=self.reopening(case);self.publish(case);before=case['barrier'].stat()
            result=self.reopen(case,setup)
            self.assertEqual(result['status'],'admission_opened')
            self.assertEqual(case['barrier'].read_bytes(),setup['proposed'])
            self.assertEqual(case['barrier'].stat().st_ino,before.st_ino)
            self.assertEqual(case['barrier'].stat().st_mode,before.st_mode)
            with control.admission():
                self.assertEqual(control.load_control_bytes('expected.json'),case['payloads']['expected.json'])
            self.assertEqual(self.observe_reopening(case,setup)['status'],'admitted_matches')
            with self.assertRaises(ValueError):self.reopen(case,setup)

    def test_reopening_exact_scope_required_before_first_write(self):
        for kind in ('expired','extra','preparation','blocked','proposed','recovery','qualification','root'):
            with self.subTest(kind=kind),self.fixture() as case:
                setup=self.reopening(case);self.publish(case)
                value=dict(setup['authority'])
                if kind=='expired':value['expires_at']='2000-01-01T00:00:00Z'
                elif kind=='extra':value['extra']=True
                elif kind in ('preparation','blocked','proposed'):value[kind+('_authority_sha256' if kind=='preparation' else '_admission_sha256')]='0'*64
                elif kind=='recovery':setup['recovery']+=b' '
                elif kind=='qualification':setup['qualification']+=b' '
                setup['file'].write_bytes(json.dumps(value).encode())
                manager=patch.object(os,'geteuid',return_value=9909) if kind=='root' else contextlib.nullcontext()
                with manager,patch.object(os,'ftruncate',side_effect=AssertionError('write before scope')),self.assertRaises(ValueError):
                    self.reopen(case,setup)
                self.assertEqual(case['barrier'].read_bytes(),case['blocked'])

    def test_reopening_exclusive_lease_excludes_all_readers(self):
        with self.fixture() as case:
            setup=self.reopening(case);self.publish(case);actual=os.pwrite
            def write(*args):
                self.assertEqual(case['barrier_fixture'].child_lock(case['barrier'],False),3)
                return actual(*args)
            with patch.object(os,'pwrite',side_effect=write):self.reopen(case,setup)
        import fcntl
        with self.fixture() as case:
            setup=self.reopening(case);self.publish(case)
            with case['barrier'].open('rb') as barrier:
                fcntl.flock(barrier,fcntl.LOCK_SH|fcntl.LOCK_NB)
                with self.assertRaises(BlockingIOError):self.reopen(case,setup)
            self.assertEqual(case['barrier'].read_bytes(),case['blocked'])

    def test_partial_reopening_is_denied_and_never_repaired_or_retried(self):
        for kind in ('truncate','partial','short'):
            with self.subTest(kind=kind),self.fixture() as case:
                setup=self.reopening(case);self.publish(case);actual=os.pwrite;calls=[]
                def write(fd,data,offset):
                    calls.append(1)
                    if kind=='truncate' or kind=='partial' and len(calls)>1:raise OSError('synthetic-write')
                    return actual(fd,data[:7] if kind!='truncate' else data,offset)
                with patch.object(os,'pwrite',side_effect=write):
                    if kind=='short':self.reopen(case,setup)
                    else:
                        with self.assertRaises(OSError):self.reopen(case,setup)
                if kind=='short':
                    self.assertGreater(len(calls),1);self.assertEqual(case['barrier'].read_bytes(),setup['proposed'])
                else:
                    raw=case['barrier'].read_bytes();self.assertEqual(len(raw),0 if kind=='truncate' else 7)
                    self.assertEqual(self.observe_reopening(case,setup)['status'],'different_bytes')
                    with self.assertRaises(ValueError):
                        with control.admission():self.fail('partial must deny')
                    with self.assertRaises(ValueError):self.reopen(case,setup)
                    self.assertEqual(case['barrier'].read_bytes(),raw)

    def test_late_failure_can_leave_admitted_bytes_without_completion_proof(self):
        for kind in ('file-sync','parent-sync','revoked'):
            with self.subTest(kind=kind),self.fixture() as case:
                setup=self.reopening(case);self.publish(case);actual=os.fsync;calls=[]
                def sync(fd):
                    calls.append(1)
                    if kind=='file-sync' and len(calls)==1 or kind=='parent-sync' and len(calls)==2:
                        raise OSError('synthetic-sync')
                    result=actual(fd)
                    if kind=='revoked' and len(calls)==2:
                        value=dict(setup['authority'],authorization_id='7'*32)
                        setup['file'].write_bytes(json.dumps(value).encode())
                    return result
                with patch.object(os,'fsync',side_effect=sync),self.assertRaises((ValueError,OSError)):
                    self.reopen(case,setup)
                self.assertEqual(case['barrier'].read_bytes(),setup['proposed'])
                with control.admission():pass  # Explicitly uncertain, not falsely denied.
                result=self.observe_reopening(case,setup)
                self.assertEqual(result['status'],'admitted_matches')
                for key,value in result.items():
                    if key not in ('schema_version','status'):self.assertIs(value,False)
                with self.assertRaises(ValueError):self.reopen(case,setup)

    def test_reopening_inspection_is_independently_scoped_and_read_only(self):
        with self.fixture() as case:
            setup=self.reopening(case)
            with patch.object(publication,'load_reopening_authority',side_effect=AssertionError('old authority')), \
                 patch.object(os,'write',side_effect=AssertionError('write')), \
                 patch.object(os,'pwrite',side_effect=AssertionError('pwrite')), \
                 patch.object(os,'fsync',side_effect=AssertionError('fsync')):
                self.assertEqual(self.observe_reopening(case,setup)['status'],'blocked_matches')
            original_inspection=setup['inspect_file'].read_bytes()
            for kind in ('expired','digest','extra'):
                value=json.loads(original_inspection)
                if kind=='expired':value['expires_at']='2000-01-01T00:00:00Z'
                elif kind=='digest':value['reopening_authority_sha256']='0'*64
                else:value['extra']=True
                setup['inspect_file'].write_bytes(json.dumps(value).encode())
                with self.assertRaises(ValueError):self.observe_reopening(case,setup)

    def test_reopening_revalidates_preflight_before_first_write(self):
        with self.fixture() as case:
            setup=self.reopening(case);self.publish(case)
            actual=publication._prepare_reopening_locked;calls=[]
            def prepare(*args):
                calls.append(1)
                if len(calls)==2:raise ValueError('synthetic-stale-preflight')
                return actual(*args)
            with patch.object(publication,'_prepare_reopening_locked',side_effect=prepare),self.assertRaises(ValueError):
                self.reopen(case,setup)
            self.assertEqual(case['barrier'].read_bytes(),case['blocked'])

    def test_reopening_inspection_rechecks_scope_bytes_and_lock(self):
        for kind in ('revoked','bytes','root','exclusive','shared'):
            with self.subTest(kind=kind),self.fixture() as case:
                setup=self.reopening(case);actual=publication.load_reopening_inspection;calls=[]
                def load():
                    calls.append(1)
                    if len(calls)==2:
                        if kind=='revoked':
                            value=json.loads(setup['inspect_file'].read_bytes());value['authorization_id']='6'*32
                            setup['inspect_file'].write_bytes(json.dumps(value).encode())
                        elif kind=='bytes':case['barrier'].write_bytes(b'partial')
                    if kind=='shared' and len(calls)>1:
                        self.assertEqual(case['barrier_fixture'].child_lock(case['barrier'],True),3)
                    return actual()
                manager=patch.object(os,'geteuid',return_value=9909) if kind=='root' else contextlib.nullcontext()
                with manager,patch.object(publication,'load_reopening_inspection',side_effect=load):
                    if kind=='exclusive':
                        import fcntl
                        with case['barrier'].open('rb') as barrier:
                            fcntl.flock(barrier,fcntl.LOCK_EX|fcntl.LOCK_NB)
                            with self.assertRaises(BlockingIOError):self.observe_reopening(case,setup)
                    elif kind=='shared':self.assertEqual(self.observe_reopening(case,setup)['status'],'blocked_matches')
                    else:
                        with self.assertRaises(ValueError):self.observe_reopening(case,setup)

    def test_historical_reopening_inspection_never_renews_write_authority(self):
        with self.fixture() as case:
            setup=self.reopening(case)
            value=dict(setup['authority'],expires_at='2000-01-01T00:00:00Z')
            setup['raw']=json.dumps(value).encode()
            inspection=json.loads(setup['inspect_file'].read_bytes())
            inspection['reopening_authority_sha256']=hashlib.sha256(setup['raw']).hexdigest()
            setup['inspect_file'].write_bytes(json.dumps(inspection).encode())
            with patch.object(publication,'load_reopening_authority',side_effect=AssertionError('historical live lookup')):
                self.assertEqual(self.observe_reopening(case,setup)['status'],'blocked_matches')
            with self.assertRaises(ValueError):publication.validate_reopening_authority(value)
