import copy
import json
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import audit_licence_gaps as audit
import audit_npm_notice_markers as markers
from test_audit_licence_gaps import tar


class NpmMarkerTests(unittest.TestCase):
    def fixture(self,entries=None):
        data=tar(entries or [('package/index.js',b'// Copyright SYNTHETIC\r\n// Permission is hereby granted SYNTHETIC\ncode\n',tarfile.REGTYPE)])
        record={'name':'synthetic','version':'1','licence_texts':[],
            'artifact_url':'https://registry.npmjs.org/synthetic.tgz','artifact_hash':'sha256:'+audit.sha256(data)}
        source=json.dumps({'npm':[record],'python_runtime':[],'python_tools':[]}).encode()
        baseline,_=audit.audit(source,lambda *_:data)
        return source,json.dumps(baseline).encode(),lambda *_:data

    def test_exact_crlf_lines_offsets_and_same_line_markers(self):
        content=b'code\n// Copyright SYNTHETIC; SPDX-License-Identifier: SYNTHETIC\r\ncode\n'
        lines,texts=markers.marker_lines(content)
        self.assertEqual(len(lines),1);line=lines[0]
        self.assertEqual(line['byte_start'],5)
        self.assertEqual(texts[line['text_sha256']],content[line['byte_start']:line['byte_end_exclusive']])
        self.assertTrue(texts[line['text_sha256']].endswith(b'\r\n'))
        self.assertEqual(line['markers'],['copyright','spdx-license-identifier'])

    def test_file_marker_and_retained_line_bounds(self):
        with patch.object(markers,'MAX_FILE',2),self.assertRaises(ValueError):markers.marker_lines(b'copyright')
        with patch.object(markers,'MAX_MARKERS',1),self.assertRaises(ValueError):markers.marker_lines(b'copyright copyright')
        with patch.object(markers,'MAX_LINE',3):
            lines,texts=markers.marker_lines(b'copyright\n')
        self.assertEqual(lines[0]['retention'],'line-too-long');self.assertEqual(texts,{})
        with self.assertRaises(UnicodeDecodeError):markers.marker_lines(b'\xff copyright')

    def test_binary_invalid_utf8_oversized_and_no_match_are_explicit(self):
        entries=[('package/binary.node',b'copyright',tarfile.REGTYPE),
            ('package/invalid.js',b'\xff copyright',tarfile.REGTYPE),
            ('package/nul.js',b'\x00 copyright',tarfile.REGTYPE),
            ('package/large.js',b'c'*50,tarfile.REGTYPE),
            ('package/small.js',b'code',tarfile.REGTYPE)]
        with patch.object(markers,'MAX_FILE',20):observed,texts=markers.scan(tar(entries))
        states={x['archive_member']:x['status'] for x in observed}
        self.assertEqual(states,{'package/binary.node':'skipped-unselected-suffix',
            'package/invalid.js':'skipped-invalid-utf8','package/nul.js':'skipped-nul-containing',
            'package/large.js':'skipped-file-byte-bound','package/small.js':'no-markers-in-selected-text'})
        self.assertEqual(texts,{})

    def test_cumulative_bytes_and_shared_archive_guards_apply(self):
        source,baseline,loader=self.fixture()
        with patch.object(markers,'MAX_SCANNED',1),self.assertRaises(ValueError):markers.collect(source,baseline,loader)
        with patch.object(audit,'MAX_MEMBERS',0),self.assertRaises(ValueError):markers.collect(source,baseline,loader)

    def test_source_baseline_digest_and_archive_substitutions_denied(self):
        source,baseline,loader=self.fixture()
        for kind in ('source','identity','archive','members','duplicate'):
            with self.subTest(kind=kind):
                value=json.loads(baseline)
                if kind=='source':value['source_licences_sha256']='0'*64
                elif kind=='identity':value['findings']=[]
                elif kind=='archive':value['findings'][0]['observed_archive_sha256']='0'*64
                elif kind=='members':value['findings'][0]['archive_members']=[]
                else:value['findings'].append(copy.deepcopy(value['findings'][0]))
                with self.assertRaises(ValueError):markers.collect(source,json.dumps(value).encode(),loader)
        with patch.object(markers,'inspect_archive') as inspect,self.assertRaises(ValueError):
            markers.collect(source,baseline,lambda *_:b'wrong artifact')
        inspect.assert_not_called()

    def test_exact_attribution_and_no_completeness_grants(self):
        source,baseline,loader=self.fixture();report,texts=markers.collect(source,baseline,loader)
        self.assertEqual(report['source_licences_sha256'],audit.sha256(source))
        self.assertEqual(report['baseline_audit_sha256'],audit.sha256(baseline))
        member=report['findings'][0]['member_observations'][0]
        self.assertEqual(member['status'],'markers-observed')
        with tarfile.open(fileobj=__import__('io').BytesIO(loader()),mode='r:gz') as archive:
            with archive.extractfile('package/index.js') as stream:content=stream.read()
        self.assertEqual(member['member_sha256'],audit.sha256(content))
        for line in member['observations']:
            self.assertEqual(texts[line['text_sha256']],content[line['byte_start']:line['byte_end_exclusive']])
        for flag in ('legal_approval','inventory_complete','package_wide_notice_review_complete'):self.assertIs(report[flag],False)

    def test_exclusive_retention_tampering_and_symlinks(self):
        source,baseline,loader=self.fixture();report,texts=markers.collect(source,baseline,loader)
        with tempfile.TemporaryDirectory() as name:
            directory=Path(name);markers.retain(directory,report,texts,write=True)
            markers.retain(directory,report,texts)
            with self.assertRaises(ValueError):markers.retain(directory,report,texts,write=True)
            file=next((directory/'npm-notice-marker-texts').iterdir());file.write_bytes(b'changed')
            with self.assertRaises(ValueError):markers.retain(directory,report,texts)
        with tempfile.TemporaryDirectory() as name:
            directory=Path(name);(directory/'npm-notice-markers.json').symlink_to('missing')
            with self.assertRaises(ValueError):markers.retain(directory,report,texts,write=True)

    def test_marker_observations_do_not_invent_missing_grants(self):
        source,baseline,loader=self.fixture([('package/README.md',b'# License\nSee upstream license\n',tarfile.REGTYPE),
            ('package/package.json',b'{"license":"SYNTHETIC"}\n',tarfile.REGTYPE)])
        report,texts=markers.collect(source,baseline,loader)
        self.assertEqual(len(report['findings'][0]['member_observations']),2)
        self.assertEqual(len(texts),3)
        self.assertFalse(report['package_wide_notice_review_complete'])
