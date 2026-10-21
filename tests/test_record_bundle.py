"""Offline unverified record candidates, never host publication evidence."""
import copy
import hashlib
import json
import os
import tempfile
import contextlib
import stat
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'ops/runtime'))
import record_bundle as bundle
import operator_inspect
import process_probe
import schema_reconciliation
from test_process_probe import candidate_bundle


class RecordBundleTests(unittest.TestCase):
    def prepare(self,value):
        return bundle.prepare_records(json.dumps(value).encode())

    def test_exact_candidate_returns_only_unverified_hash_report_and_canonical_bytes(self):
        value=candidate_bundle();data=json.dumps(value).encode()
        payloads,report=bundle.prepare_records(data)
        self.assertEqual(set(payloads),bundle.FILENAMES)
        self.assertEqual(report['bundle_sha256'],hashlib.sha256(data).hexdigest())
        self.assertEqual(report['status'],'candidate_validated')
        self.assertEqual(report['evidence_class'],'unverified-candidate')
        for flag in ('publication_authorized','retry_authorized','reopening_authorized'):
            self.assertIs(report[flag],False)
        for name,payload in payloads.items():
            self.assertEqual(json.loads(payload),value['records'][name])
            self.assertEqual(report['record_sha256'][name],hashlib.sha256(payload).hexdigest())
            self.assertTrue(payload.endswith(b'\n'))
        self.assertNotIn('synthetic_shop',json.dumps(report))
        self.assertNotIn('CREATE TABLE',json.dumps(report))

    def test_no_observed_evidence_or_publication_claim_accepted(self):
        for change in ({'evidence_class':'actual-mx1-qualified'},{'schema_version':True},
                       {'publication_authorized':True},{'credential':'synthetic-private'}):
            with self.subTest(change=change),self.assertRaises(ValueError):
                self.prepare(dict(candidate_bundle(),**change))

    def test_missing_or_extra_record_denied(self):
        for change in ('missing','extra'):
            value=candidate_bundle()
            if change=='missing':value['records'].pop('expected.json')
            else:value['records']['.env']={'password':'synthetic-private'}
            with self.subTest(change=change),self.assertRaises(ValueError):self.prepare(value)

    def test_mixed_startup_database_or_control_binary_denied(self):
        changes=(('expected.json','machine_id_sha256','b'*64),
                 ('operator-connection.json','pg_control','/nix/store/'+'c'*32+'-postgresql/bin/pg_controldata'))
        for name,key,replacement in changes:
            value=candidate_bundle();value['records'][name][key]=replacement
            with self.subTest(key=key),self.assertRaises(ValueError):self.prepare(value)
        for name in ('operator-connection.json','schema-reconciliation.json'):
            value=candidate_bundle();value['records'][name]['database']['role']='decoy'
            with self.subTest(name=name),self.assertRaises(ValueError):self.prepare(value)

    def test_expired_or_write_authority_is_not_inspection_candidate(self):
        for key,value in (('expires_at','2000-01-01T00:00:00Z'),('action','apply-reviewed-schema')):
            candidate=candidate_bundle();candidate['records']['schema-reconciliation.json'][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.prepare(candidate)

    def test_exact_original_artifact_required(self):
        for artifact in ('!!','e30='):
            value=candidate_bundle();value['artifact_base64']=artifact
            with self.subTest(artifact=artifact),self.assertRaises(ValueError):self.prepare(value)

    def test_duplicate_fields_invalid_encoding_and_bundle_bound_denied(self):
        data=json.dumps(candidate_bundle()).encode()
        duplicate=data.replace(b'"schema_version": 1',b'"schema_version": 1,"schema_version": 1',1)
        for raw in (duplicate,b'\xff',b' ',b' '* (bundle.MAX_BUNDLE+1)):
            with self.assertRaises(ValueError):bundle.prepare_records(raw)

    def test_individual_record_bound_and_unknown_nested_properties_denied(self):
        candidate=candidate_bundle();candidate['records']['database-process.json']['process']['executable']='x'*32769
        with self.assertRaises(ValueError):self.prepare(candidate)
        candidate=candidate_bundle();candidate['records']['operator-connection.json']['database']['password']='synthetic-private'
        with self.assertRaises(ValueError):self.prepare(candidate)

    def test_validation_never_loads_records_probes_or_connects(self):
        value=candidate_bundle()
        with patch.object(operator_inspect,'load_connection',side_effect=AssertionError), \
             patch.object(process_probe,'load_record',side_effect=AssertionError), \
             patch.object(process_probe,'probe',side_effect=AssertionError), \
             patch.object(schema_reconciliation,'load_authorization',side_effect=AssertionError), \
             patch.object(operator_inspect.psycopg,'connect',side_effect=AssertionError):
            _,report=self.prepare(value)
            self.assertIs(report['publication_authorized'],False)


class CandidateStagingTests(unittest.TestCase):
    @contextlib.contextmanager
    def parent(self):
        scratch=Path(os.environ.get('SHOP_TEST_SCRATCH',Path(__file__).resolve().parents[1]/'.scratch'))
        with tempfile.TemporaryDirectory(prefix='candidate-',dir=scratch) as directory:
            fd=os.open(directory,os.O_RDONLY|os.O_DIRECTORY|os.O_CLOEXEC)
            try:yield Path(directory),fd
            finally:os.close(fd)

    def candidate(self):
        return json.dumps(candidate_bundle()).encode()

    def test_actual_exclusive_private_files_preserve_bytes_and_unverified_report(self):
        data=self.candidate();payloads,_=bundle.prepare_records(data)
        with self.parent() as (parent,fd):
            with patch.object(operator_inspect.psycopg,'connect',side_effect=AssertionError), \
                 patch.object(process_probe,'probe',side_effect=AssertionError):
                report=bundle.stage_candidate(data,fd)
            staged=parent/('candidate-'+report['bundle_sha256'])
            self.assertEqual(stat.S_IMODE(staged.stat().st_mode),0o700)
            self.assertEqual(set(p.name for p in staged.iterdir()),bundle.FILENAMES|{'bundle.json','artifact.bin','prepared.json'})
            expected={**payloads,'bundle.json':data,'artifact.bin':__import__('base64').b64decode(json.loads(data)['artifact_base64'])}
            for name,payload in expected.items():
                self.assertEqual((staged/name).read_bytes(),payload)
                self.assertEqual(report['file_sha256'][name],hashlib.sha256(payload).hexdigest())
            for child in staged.iterdir():
                self.assertEqual(stat.S_IMODE(child.stat().st_mode),0o400)
                self.assertEqual(child.stat().st_uid,os.geteuid())
                self.assertEqual(child.stat().st_nlink,1)
            self.assertEqual(json.loads((staged/'prepared.json').read_bytes()),report)
            self.assertEqual(report['evidence_class'],'unverified-candidate')
            self.assertEqual(report['status'],'candidate_staged')
            for flag in ('publication_authorized','retry_authorized','reopening_authorized'):self.assertIs(report[flag],False)
            with self.assertRaises(FileExistsError):bundle.stage_candidate(data,fd)
            self.assertEqual((staged/'bundle.json').read_bytes(),data)
            os.fstat(fd)  # Caller descriptor remains open.

    def test_invalid_candidate_or_nonprivate_parent_creates_nothing(self):
        with self.parent() as (parent,fd):
            for data in (b'{}',b'invalid'):
                with self.assertRaises(ValueError):bundle.stage_candidate(data,fd)
                self.assertEqual(list(parent.iterdir()),[])
            os.fchmod(fd,0o750)
            with self.assertRaises(ValueError):bundle.stage_candidate(self.candidate(),fd)
            self.assertEqual(list(parent.iterdir()),[])
            os.fchmod(fd,0o700)
            with patch.object(bundle.os,'geteuid',return_value=os.geteuid()+1):
                with self.assertRaises(ValueError):bundle.stage_candidate(self.candidate(),fd)
            self.assertEqual(list(parent.iterdir()),[])

    def test_preexisting_directory_file_or_symlink_never_adopted(self):
        data=self.candidate();name='candidate-'+hashlib.sha256(data).hexdigest()
        for kind in ('directory','file','symlink'):
            with self.subTest(kind=kind),self.parent() as (parent,fd):
                target=parent/name
                if kind=='directory':target.mkdir()
                elif kind=='file':target.write_bytes(b'protected-synthetic')
                else:target.symlink_to('unrelated-missing')
                with self.assertRaises(FileExistsError):bundle.stage_candidate(data,fd)
                self.assertEqual(list(parent.iterdir()),[target])
                if kind=='file':self.assertEqual(target.read_bytes(),b'protected-synthetic')
                if kind=='directory':self.assertEqual(list(target.iterdir()),[])
                if kind=='symlink':self.assertEqual(os.readlink(target),'unrelated-missing')

    def test_short_writes_complete_and_required_sync_calls_execute(self):
        real_write=os.write;real_sync=os.fsync
        with self.parent() as (parent,fd),patch.object(bundle.os,'write',side_effect=lambda fd,data:real_write(fd,data[:7])), \
             patch.object(bundle.os,'fsync',wraps=real_sync) as synced:
            report=bundle.stage_candidate(self.candidate(),fd)
            self.assertEqual(report['status'],'candidate_staged')
            self.assertEqual(synced.call_count,10)  # Seven files, twice stage dir, parent.

    def test_failed_sync_retains_partial_and_denies_blind_repeat(self):
        data=self.candidate();name='candidate-'+hashlib.sha256(data).hexdigest()
        with self.parent() as (parent,fd):
            with patch.object(bundle.os,'fsync',side_effect=OSError('synthetic-sync-failure')):
                with self.assertRaises(OSError):bundle.stage_candidate(data,fd)
            self.assertTrue((parent/name).is_dir())
            self.assertTrue(any((parent/name).iterdir()))
            self.assertFalse((parent/name/'prepared.json').exists())
            with self.assertRaises(FileExistsError):bundle.stage_candidate(data,fd)

    def test_zero_write_or_corrupt_readback_never_returns_success(self):
        for operation,result in (('write',0),('pread',b'corrupt-synthetic')):
            with self.subTest(operation=operation),self.parent() as (parent,fd):
                with patch.object(bundle.os,operation,return_value=result):
                    with self.assertRaises(ValueError):bundle.stage_candidate(self.candidate(),fd)
                self.assertEqual(len(list(parent.iterdir())),1)

    def test_last_parent_sync_failure_leaves_marker_but_not_success_or_retry(self):
        data=self.candidate();name='candidate-'+hashlib.sha256(data).hexdigest();real_sync=os.fsync
        with self.parent() as (parent,fd):
            def fail_parent(descriptor):
                info=os.fstat(descriptor)
                if (info.st_dev,info.st_ino)==(os.fstat(fd).st_dev,os.fstat(fd).st_ino):raise OSError('synthetic-parent-sync')
                real_sync(descriptor)
            with patch.object(bundle.os,'fsync',side_effect=fail_parent):
                with self.assertRaises(OSError):bundle.stage_candidate(data,fd)
            self.assertTrue((parent/name/'prepared.json').is_file())
            with self.assertRaises(FileExistsError):bundle.stage_candidate(data,fd)

    def test_final_readback_detects_replaced_file(self):
        data=self.candidate();real_sync=os.fsync
        with self.parent() as (parent,fd):
            staged=parent/('candidate-'+hashlib.sha256(data).hexdigest())
            def replace_after_parent_sync(descriptor):
                real_sync(descriptor)
                if os.fstat(descriptor).st_ino==os.fstat(fd).st_ino:
                    target=staged/'bundle.json';target.unlink();target.symlink_to('artifact.bin')
            with patch.object(bundle.os,'fsync',side_effect=replace_after_parent_sync):
                with self.assertRaises(OSError):bundle.stage_candidate(data,fd)


    def test_inspection_matches_exact_files_without_writes_or_action_authority(self):
        data=self.candidate()
        with self.parent() as (parent,fd):
            staged=bundle.stage_candidate(data,fd);real_open=os.open
            with patch.object(bundle.os,'write',side_effect=AssertionError('no writes')), \
                 patch.object(bundle.os,'mkdir',side_effect=AssertionError('no mkdir')), \
                 patch.object(bundle.os,'unlink',side_effect=AssertionError('no cleanup')), \
                 patch.object(bundle.os,'fsync',side_effect=AssertionError('no durability action')), \
                 patch.object(bundle.os,'open',wraps=real_open) as opened:
                report=bundle.inspect_candidate(data,fd)
                self.assertTrue(all(call.args[1]&os.O_ACCMODE==os.O_RDONLY for call in opened.call_args_list))
            self.assertEqual(report,dict(staged,status='candidate_matches',durability_confirmed=False))
            for key in ('publication_authorized','retry_authorized','reopening_authorized','durability_confirmed'):
                self.assertIs(report[key],False)
            os.fstat(fd)

    def test_inspection_denies_partial_or_extra_files_without_repair(self):
        for kind in ('missing','extra'):
            data=self.candidate()
            with self.subTest(kind=kind),self.parent() as (parent,fd):
                report=bundle.stage_candidate(data,fd);stage=parent/('candidate-'+report['bundle_sha256'])
                if kind=='missing':(stage/'prepared.json').unlink()
                else:(stage/'unknown').write_bytes(b'synthetic')
                before=set(stage.iterdir())
                with self.assertRaises(ValueError):bundle.inspect_candidate(data,fd)
                self.assertEqual(set(stage.iterdir()),before)

    def test_inspection_denies_tampered_payload_or_forged_marker(self):
        for name in ('bundle.json','artifact.bin','expected.json','prepared.json'):
            data=self.candidate()
            with self.subTest(name=name),self.parent() as (parent,fd):
                report=bundle.stage_candidate(data,fd);target=parent/('candidate-'+report['bundle_sha256'])/name
                payload=target.read_bytes();target.chmod(0o600);target.write_bytes(b'X'+payload[1:]);target.chmod(0o400)
                with self.assertRaises(ValueError):bundle.inspect_candidate(data,fd)
                self.assertEqual(target.read_bytes(),b'X'+payload[1:])

    def test_inspection_denies_link_fifo_directory_or_changed_mode(self):
        for kind in ('symlink','hardlink','fifo','directory','mode'):
            data=self.candidate()
            with self.subTest(kind=kind),self.parent() as (parent,fd):
                report=bundle.stage_candidate(data,fd);stage=parent/('candidate-'+report['bundle_sha256']);target=stage/'bundle.json'
                if kind=='mode':target.chmod(0o600)
                elif kind=='hardlink':os.link(target,parent/'external-link')
                else:
                    target.unlink()
                    if kind=='symlink':target.symlink_to('artifact.bin')
                    elif kind=='fifo':os.mkfifo(target,0o400)
                    else:target.mkdir()
                with self.assertRaises((ValueError,OSError)):bundle.inspect_candidate(data,fd)

    def test_inspection_requires_original_input_and_private_parent(self):
        data=self.candidate()
        with self.parent() as (parent,fd):
            bundle.stage_candidate(data,fd)
            with self.assertRaises(FileNotFoundError):bundle.inspect_candidate(data+b' ',fd)
            os.fchmod(fd,0o750)
            with self.assertRaises(ValueError):bundle.inspect_candidate(data,fd)
            os.fchmod(fd,0o700)
            with patch.object(bundle.os,'geteuid',return_value=os.geteuid()+1):
                with self.assertRaises(ValueError):bundle.inspect_candidate(data,fd)

    def test_inspection_after_uncertain_parent_sync_never_confirms_durability(self):
        data=self.candidate();real_sync=os.fsync
        with self.parent() as (parent,fd):
            def fail_parent(descriptor):
                if os.fstat(descriptor).st_ino==os.fstat(fd).st_ino:raise OSError('synthetic-sync')
                real_sync(descriptor)
            with patch.object(bundle.os,'fsync',side_effect=fail_parent):
                with self.assertRaises(OSError):bundle.stage_candidate(data,fd)
            report=bundle.inspect_candidate(data,fd)
            self.assertEqual(report['status'],'candidate_matches')
            self.assertIs(report['durability_confirmed'],False)
            self.assertIs(report['retry_authorized'],False)
            with self.assertRaises(FileExistsError):bundle.stage_candidate(data,fd)

    def test_inspection_denies_file_replaced_after_descriptor_read(self):
        data=self.candidate();real_read=os.pread
        with self.parent() as (parent,fd):
            report=bundle.stage_candidate(data,fd);target=parent/('candidate-'+report['bundle_sha256'])/'bundle.json'
            inode=target.stat().st_ino
            def replace(descriptor,count,offset):
                result=real_read(descriptor,count,offset)
                if os.fstat(descriptor).st_ino==inode:
                    target.unlink();target.write_bytes(result);target.chmod(0o400)
                return result
            with patch.object(bundle.os,'pread',side_effect=replace):
                with self.assertRaises(ValueError):bundle.inspect_candidate(data,fd)

    def test_inspection_denies_named_generation_replaced_during_readback(self):
        data=self.candidate();real_readback=bundle._readback_files
        with self.parent() as (parent,fd):
            report=bundle.stage_candidate(data,fd);target=parent/('candidate-'+report['bundle_sha256'])
            def replace(directory,files):
                real_readback(directory,files)
                target.rename(parent/'retained-original');target.mkdir(mode=0o700)
            with patch.object(bundle,'_readback_files',side_effect=replace):
                with self.assertRaises(ValueError):bundle.inspect_candidate(data,fd)
            self.assertTrue((parent/'retained-original'/'prepared.json').is_file())
