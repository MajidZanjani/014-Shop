import copy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import audit_licence_gaps as original
import audit_licence_names as extended


class ExtendedNameTests(unittest.TestCase):
    def fixture(self):
        stream=io.BytesIO()
        with zipfile.ZipFile(stream,'w') as archive:
            archive.writestr('synthetic.dist-info/mit.LICENSE',b'SYNTHETIC EXACT NOTICE\r\n')
            archive.writestr('synthetic.py',b'# synthetic code\n')
        data=stream.getvalue()
        record={'name':'synthetic','version':'1','licence_texts':[],
            'artifact_url':'https://files.pythonhosted.org/synthetic.whl',
            'artifact_hash':'sha256:'+original.sha256(data)}
        source=json.dumps({'npm':[],'python_runtime':[],'python_tools':[record]}).encode()
        loader=lambda *_:data
        baseline,_=original.audit(source,loader)
        return source,json.dumps(baseline).encode(),loader

    def test_explicit_prefixed_names_and_original_policy_unchanged(self):
        for name in ('mit.LICENSE','MIT-LICENSE.txt','apache_2.0-LICENCE','bsd.COPYRIGHT','vendor.NOTICE.txt','LICENSE','COPYING'):
            with self.subTest(name=name):self.assertTrue(extended.extended_candidate('package/'+name))
        for name in ('licensing.js','mylicense.js','README.md','fooLICENSE','source.c','mit.LICENSEfile'):
            with self.subTest(name=name):self.assertFalse(extended.extended_candidate(name))
        self.assertFalse(original.candidate('mit.LICENSE'))

    def test_exact_bytes_and_baseline_archive_bindings(self):
        source,baseline,loader=self.fixture();report,texts=extended.collect(source,baseline,loader)
        self.assertEqual(list(texts.values()),[b'SYNTHETIC EXACT NOTICE\r\n'])
        text=report['findings'][0]['candidate_notice_texts'][0]
        self.assertEqual(text['sha256'],original.sha256(b'SYNTHETIC EXACT NOTICE\r\n'))
        self.assertEqual(text['retained_path'],'licence-name-texts/'+text['sha256']+'.txt')
        self.assertEqual(report['baseline_audit_sha256'],original.sha256(baseline))
        for flag in ('inventory_complete','legal_approval','package_wide_notice_review_complete'):self.assertIs(report[flag],False)
        self.assertEqual(json.loads(baseline)['findings'][0]['candidate_notice_texts'],[])

    def test_baseline_substitution_omission_and_duplicates_denied(self):
        source,baseline,loader=self.fixture()
        for kind in ('source','identity','archive','members','duplicate'):
            with self.subTest(kind=kind):
                value=json.loads(baseline)
                if kind=='source':value['source_licences_sha256']='0'*64
                elif kind=='identity':value['findings']=[]
                elif kind=='archive':value['findings'][0]['observed_archive_sha256']='0'*64
                elif kind=='members':value['findings'][0]['archive_members']=[]
                else:value['findings'].append(copy.deepcopy(value['findings'][0]))
                with self.assertRaises(ValueError):extended.collect(source,json.dumps(value).encode(),loader)

    def test_new_predicate_keeps_shared_archive_bounds(self):
        source,baseline,loader=self.fixture()
        with patch.object(original,'MAX_TEXT',3),self.assertRaises(ValueError):extended.collect(source,baseline,loader)
        with patch.object(original,'MAX_MEMBERS',1),self.assertRaises(ValueError):extended.collect(source,baseline,loader)

    def test_retention_is_exclusive_and_recheck_detects_tampering(self):
        source,baseline,loader=self.fixture();report,texts=extended.collect(source,baseline,loader)
        with tempfile.TemporaryDirectory() as name:
            directory=Path(name);extended.retain(directory,report,texts,write=True)
            extended.retain(directory,report,texts)
            with self.assertRaises(ValueError):extended.retain(directory,report,texts,write=True)
            file=next((directory/'licence-name-texts').iterdir());file.write_bytes(b'changed')
            with self.assertRaises(ValueError):extended.retain(directory,report,texts)
            self.assertEqual(file.read_bytes(),b'changed')

    def test_preexisting_or_symlink_outputs_are_never_adopted(self):
        source,baseline,loader=self.fixture();report,texts=extended.collect(source,baseline,loader)
        for kind in ('file','directory','dangling'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as name:
                directory=Path(name)
                if kind=='file':(directory/'licence-name-audit.json').write_bytes(b'protected')
                elif kind=='directory':(directory/'licence-name-texts').mkdir()
                else:(directory/'licence-name-audit.json').symlink_to('missing')
                with self.assertRaises(ValueError):extended.retain(directory,report,texts,write=True)
                if kind=='file':self.assertEqual((directory/'licence-name-audit.json').read_bytes(),b'protected')

    def test_digest_mismatch_precedes_archive_inspection(self):
        source,baseline,_=self.fixture()
        with patch.object(original,'inspect_archive') as inspect,self.assertRaises(ValueError):
            extended.collect(source,baseline,lambda *_:b'wrong artifact')
        inspect.assert_not_called()
