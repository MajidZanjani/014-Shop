"""Offline mutation tests against exact retained repository evidence."""
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import reconcile_licence_evidence as reconcile
from inventory_artifacts import reconcile as inventory_reconcile


class EvidenceReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.directory=Path(self.temp.name)
        source=reconcile.ROOT/'docs/evidence/t02'
        for name in reconcile.SOURCES:shutil.copyfile(source/name,self.directory/name)
        for folder in ('licence-name-texts','embedded-licence-texts','npm-notice-marker-texts'):
            shutil.copytree(source/folder,self.directory/folder)

    def change(self,name,edit):
        file=self.directory/name;value=json.loads(file.read_bytes());edit(value)
        file.write_text(json.dumps(value))

    def test_all_original_gaps_reconciled_but_none_accepted(self):
        value=reconcile.collect(self.directory)
        self.assertEqual(value['counts'],{'original_gap_distributions':12,'with_named_text':1,
            'with_embedded_header':2,'with_marker_lines':10,'pending_package_wide_review':12})
        for flag in ('inventory_accepted','legal_approval','package_wide_notice_review_complete'):self.assertIs(value[flag],False)
        for record in value['findings']:self.assertFalse(record['legal_approval'])

    def test_source_bindings_and_approval_promotion_are_denied(self):
        name='licence-name-audit.json';original=(self.directory/name).read_bytes()
        for key,replacement in [('source_licences_sha256','0'*64),('baseline_audit_sha256','0'*64),
                                ('legal_approval',True),('inventory_complete',True),
                                ('package_wide_notice_review_complete',True),('schema_version',2)]:
            with self.subTest(key=key):
                (self.directory/name).write_bytes(original)
                self.change(name,lambda v:v.update({key:replacement}))
                with self.assertRaises(ValueError):reconcile.collect(self.directory)

    def test_missing_duplicate_and_cross_package_substitution_are_denied(self):
        name='npm-notice-markers.json';original=(self.directory/name).read_bytes()
        for kind in ('missing','duplicate','artifact'):
            with self.subTest(kind=kind):
                (self.directory/name).write_bytes(original)
                def edit(value):
                    if kind=='missing':value['findings'].pop()
                    elif kind=='duplicate':value['findings'].append(value['findings'][0])
                    else:value['findings'][0]['artifact_hash']='sha256:'+'0'*64
                self.change(name,edit)
                with self.assertRaises(ValueError):reconcile.collect(self.directory)

    def test_text_digest_size_and_range_mutations_are_denied(self):
        name='embedded-licences.json';original=(self.directory/name).read_bytes()
        for key,replacement in [('text_sha256','0'*64),('byte_start',1),('byte_end_exclusive',99999999),('member_sha256','bad')]:
            with self.subTest(key=key):
                (self.directory/name).write_bytes(original)
                self.change(name,lambda v:v['findings'][0].update({key:replacement}))
                with self.assertRaises(ValueError):reconcile.collect(self.directory)
        (self.directory/name).write_bytes(original)
        file=next((self.directory/'embedded-licence-texts').iterdir());file.write_bytes(b'tampered')
        with self.assertRaises(ValueError):reconcile.collect(self.directory)

    def test_path_symlink_and_hardlink_substitutions_are_denied(self):
        name='licence-name-audit.json'
        value=json.loads((self.directory/name).read_bytes())
        record=next(r for r in value['findings'] if r['candidate_notice_texts'])
        record['candidate_notice_texts'][0]['retained_path']='../secret'
        (self.directory/name).write_text(json.dumps(value))
        with self.assertRaises(ValueError):reconcile.collect(self.directory)
        file=self.directory/'licences.json';file.unlink();file.symlink_to('/nonexistent')
        with self.assertRaises(OSError):reconcile.collect(self.directory)
        with self.assertRaises(ValueError):reconcile.read_file(self.directory,'../secret')
        file.unlink();file.write_bytes(b'{}');__import__('os').link(file,self.directory/'second')
        with self.assertRaises(ValueError):reconcile.read_file(self.directory,'licences.json')

    def test_marker_coverage_and_retained_range_must_match(self):
        name='npm-notice-markers.json';original=(self.directory/name).read_bytes()
        for kind in ('member','range','status'):
            with self.subTest(kind=kind):
                (self.directory/name).write_bytes(original)
                def edit(value):
                    record=next(r for r in value['findings'] if any(m.get('observations') for m in r['member_observations']))
                    if kind=='member':record['member_observations'].pop()
                    else:
                        member=next(m for m in record['member_observations'] if m.get('observations'))
                        if kind=='range':member['observations'][0]['byte_end_exclusive']+=1
                        else:member['status']='invented-complete'
                self.change(name,edit)
                with self.assertRaises(ValueError):reconcile.collect(self.directory)

    def test_source_change_at_final_recheck_is_denied(self):
        actual=reconcile.read_file;calls=[]
        def read(directory,name):
            calls.append(name)
            raw=actual(directory,name)
            if name=='licences.json' and calls.count(name)>1:return raw+b' '
            return raw
        with patch.object(reconcile,'read_file',side_effect=read),self.assertRaises(ValueError):reconcile.collect(self.directory)

    def test_supplements_do_not_satisfy_raw_inventory_required_text_gate(self):
        reconcile.collect(self.directory)
        value=json.loads((self.directory/'licences.json').read_bytes())
        record=next(r for r in value['python_tools'] if r['name']=='pip-requirements-parser')
        self.assertEqual(record['licence_texts'],[])
        bom={'components':[{'name':record['name'],'version':record['version'],'bom-ref':'synthetic'}],
             'dependencies':[{'ref':'synthetic','dependsOn':[]}]}
        with self.assertRaises(ValueError):inventory_reconcile([record],bom,'python',require_text=True)
