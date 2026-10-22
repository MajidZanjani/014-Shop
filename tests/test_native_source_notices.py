import copy
import hashlib
import io
from pathlib import Path
import sys
import tarfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import check_native_source_notices as notices


def archive(entries):
    stream=io.BytesIO()
    with tarfile.open(fileobj=stream,mode='w:xz') as tar:
        for name,content,kind in entries:
            member=tarfile.TarInfo(name);member.size=len(content);member.type=kind
            tar.addfile(member,io.BytesIO(content))
    data=stream.getvalue()
    return data,hashlib.sha256(data).hexdigest()


class SourceNoticeTests(unittest.TestCase):
    def fixture(self):return archive([('synthetic/LICENSE',b'synthetic\r\nnotice\n',tarfile.REGTYPE)])

    def test_exact_source_bytes_retained(self):
        data,digest=self.fixture()
        found,counts=notices.scan(data,digest,'synthetic/LICENSE')
        self.assertEqual(found,{'synthetic/LICENSE':b'synthetic\r\nnotice\n'})
        self.assertEqual(counts['members_scanned'],1)

    def test_digest_denied_before_archive_parse(self):
        data,_=self.fixture()
        with patch.object(notices.tarfile,'open') as opened:
            with self.assertRaises(ValueError):notices.scan(data,'0'*64,'synthetic/LICENSE')
            opened.assert_not_called()

    def test_required_notice_not_inferred(self):
        data,digest=self.fixture()
        with self.assertRaises(ValueError):notices.scan(data,digest,'synthetic/COPYRIGHT')

    def test_unsafe_duplicate_and_link_notice_denied(self):
        for entries in ([('../LICENSE',b'x',tarfile.REGTYPE)],
                        [('synthetic/LICENSE',b'x',tarfile.REGTYPE)]*2,
                        [('synthetic/LICENSE',b'',tarfile.SYMTYPE)]):
            data,digest=archive(entries)
            with self.assertRaises(ValueError):notices.scan(data,digest,'synthetic/LICENSE')

    def test_compressed_expanded_member_and_notice_bounds(self):
        data,digest=self.fixture()
        for name,limit in (('MAX_ARCHIVE',1),('MAX_TOTAL',1),('MAX_MEMBERS',0),('MAX_NOTICE',1)):
            with self.subTest(name=name),patch.object(notices,name,limit),self.assertRaises(ValueError):notices.scan(data,digest,'synthetic/LICENSE')

    def test_exact_source_output_binding_and_missing_identity(self):
        nodes={}
        for i,(name,(version,digest,required)) in enumerate(notices.EXPECTED.items()):
            output='/nix/store/'+str(i)*32+'-synthetic'
            nodes[output]={'recipe':{'declared_pname':name,'declared_version':version,'source_store_path':output+'-source','outputs':{'out':output}},'derivation_sha256':'a'*64}
        report={'nodes':nodes}
        self.assertEqual(set(notices.select_sources(report)),set(notices.EXPECTED))
        bad=copy.deepcopy(report);next(iter(bad['nodes'].values()))['recipe']['declared_version']='invented'
        with self.assertRaises(ValueError):notices.select_sources(bad)
        bad=copy.deepcopy(report);bad['nodes'].pop(next(iter(nodes)))
        with self.assertRaises(ValueError):notices.select_sources(bad)

    def test_changed_binding_uses_revision_without_replacing_history(self):
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            baseline=Path(directory)/'native-source-notices.json'
            first=b'original';changed=b'new binding'
            self.assertEqual(notices.evidence_path(baseline,first),baseline)
            baseline.write_bytes(first)
            self.assertEqual(notices.evidence_path(baseline,first),baseline)
            revision=notices.evidence_path(baseline,changed)
            self.assertEqual(revision,baseline.parent/'native-source-notices-revisions'/
                (hashlib.sha256(changed).hexdigest()+'.json'))
            self.assertEqual(baseline.read_bytes(),first)
