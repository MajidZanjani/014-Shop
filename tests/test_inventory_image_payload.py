import copy
import gzip
import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import inspect_image_archive as outer
import inventory_image_payload as payload
from test_inspect_image_archive import fixture,tar_bytes


def inner_bytes(entries):
    stream=io.BytesIO()
    with tarfile.open(fileobj=stream,mode='w') as archive:
        for specification in entries:
            name,kind,content,target,*extra=specification
            member=tarfile.TarInfo(name);member.type=kind;member.size=len(content) if kind==tarfile.REGTYPE else 0
            member.linkname=target
            if extra:member.pax_headers=extra[0]
            archive.addfile(member,io.BytesIO(content))
    return stream.getvalue()


def image(entries):
    layer=inner_bytes(entries);digest=outer.sha256(layer)
    config=json.loads(fixture()[1][1]);config['rootfs']['diff_ids']=['sha256:'+digest]
    raw=json.dumps(config).encode();name=outer.sha256(raw)+'.json'
    manifest=[{'Config':name,'RepoTags':['shop-postgres:candidate'],'Layers':[digest+'/layer.tar']}]
    return tar_bytes([(digest+'/layer.tar',layer,tarfile.REGTYPE),(name,raw,tarfile.REGTYPE),
        ('manifest.json',json.dumps(manifest).encode(),tarfile.REGTYPE)],gzip=True)


class PayloadTests(unittest.TestCase):
    def fixture(self,entries=None):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        path=Path(self.temp.name)/'candidate.tar.gz'
        path.write_bytes(image(entries or [('/nix/store/synthetic/LICENSE',tarfile.REGTYPE,b'SYNTHETIC EXACT NOTICE\r\n','')]))
        report=outer.inspect(path)
        return path,json.dumps(report).encode()

    def test_exact_hashes_raw_absolute_names_and_compressed_manifest(self):
        path,prior=self.fixture();report,data=payload.collect(path,prior)
        self.assertEqual(report['layer_count'],1);self.assertEqual(report['counts']['regular_files'],1)
        entries=json.loads(gzip.decompress(data))['layers'][0]['entries'];entry=entries[0]
        self.assertEqual(entry['raw_archive_path'],'/nix/store/synthetic/LICENSE')
        self.assertTrue(entry['absolute_archive_path']);self.assertEqual(entry['path'],'nix/store/synthetic/LICENSE')
        self.assertEqual(entry['sha256'],hashlib.sha256(b'SYNTHETIC EXACT NOTICE\r\n').hexdigest())
        self.assertEqual(report['absolute_archive_member_names'],1)
        self.assertEqual(report['payload_manifest']['uncompressed_sha256'],outer.sha256(gzip.decompress(data)))
        self.assertEqual(len(report['notice_filename_candidates']),1)
        for key in ('merged_rootfs_qualified','links_resolved','native_notice_inventory_complete','legal_approval',
                    'container_execution_qualified','reproducibility_qualified','production_activation'):self.assertIs(report[key],False)

    def test_links_are_recorded_without_reading_their_targets(self):
        path,prior=self.fixture([('link',tarfile.SYMTYPE,b'','/outside/never-read'),
            ('hard',tarfile.LNKTYPE,b'','../outside')])
        report,data=payload.collect(path,prior);entries=json.loads(gzip.decompress(data))['layers'][0]['entries']
        self.assertEqual([e['link_target_unresolved'] for e in entries],['/outside/never-read','../outside'])
        self.assertEqual(report['symlink_count'],1);self.assertEqual(report['hardlink_count'],1)
        self.assertEqual(report['counts']['file_bytes'],0)

    def test_whiteout_observed_not_applied(self):
        path,prior=self.fixture([('etc/.wh.previous',tarfile.REGTYPE,b'','')])
        report,data=payload.collect(path,prior)
        self.assertEqual(report['whiteout_markers_unapplied'],1)
        self.assertTrue(json.loads(gzip.decompress(data))['layers'][0]['entries'][0]['whiteout_marker_unapplied'])
        self.assertFalse(report['merged_rootfs_qualified'])

    def test_traversal_alias_duplicates_and_special_members_denied(self):
        for entries in ([('../escape',tarfile.REGTYPE,b'x','')],
                        [('x/../escape',tarfile.REGTYPE,b'x','')],
                        [('//ambiguous',tarfile.REGTYPE,b'x','')],
                        [('bad\\path',tarfile.REGTYPE,b'x','')],
                        [('a',tarfile.REGTYPE,b'x',''),('./a',tarfile.REGTYPE,b'y','')],
                        [('/a',tarfile.REGTYPE,b'x',''),('a',tarfile.REGTYPE,b'y','')],
                        [('fifo',tarfile.FIFOTYPE,b'','')]):
            with self.subTest(entries=entries):
                path,prior=self.fixture(entries)
                with self.assertRaises(ValueError):payload.collect(path,prior)

    def test_entry_path_and_manifest_bounds(self):
        path,prior=self.fixture()
        for key,value in (('MAX_ENTRIES',0),('MAX_PATH',3),('MAX_MANIFEST',1)):
            with self.subTest(key=key),patch.object(payload,key,value),self.assertRaises(ValueError):payload.collect(path,prior)

    def test_outer_hashes_account_for_observer_consumption_and_unread_padding(self):
        path,prior=self.fixture();seen=[]
        def observe(name,reader):seen.append(reader.read(1))
        self.assertEqual(outer.inspect(path,layer_observer=observe),json.loads(prior));self.assertEqual(len(seen),1)
        path.write_bytes(path.read_bytes()[:-8])
        # The outer compressed archive hash is exact even for uninspected trailing bytes.
        with self.assertRaises((ValueError,EOFError,tarfile.TarError)):payload.collect(path,prior)

    def test_outer_report_substitution_is_denied(self):
        path,prior=self.fixture()
        for key,value in (('archive_sha256','0'*64),('container_execution_qualified',True),('config_image_id','sha256:'+'0'*64)):
            with self.subTest(key=key):
                changed=json.loads(prior);changed[key]=value
                with self.assertRaises(ValueError):payload.collect(path,json.dumps(changed).encode())

    def test_exclusive_retention_and_manifest_tamper_detection(self):
        path,prior=self.fixture();report,data=payload.collect(path,prior)
        directory=path.parent;payload.retain(directory,report,data,write=True)
        payload.retain(directory,report,data)
        with self.assertRaises(ValueError):payload.retain(directory,report,data,write=True)
        manifest=directory/report['payload_manifest']['path'];manifest.write_bytes(b'changed')
        with self.assertRaises(ValueError):payload.retain(directory,report,data)
        self.assertEqual(manifest.read_bytes(),b'changed')

    def test_pax_metadata_is_preserved_but_oversize_and_nonfinite_values_deny(self):
        path,prior=self.fixture([('file',tarfile.REGTYPE,b'x','',{'comment':'synthetic','mtime':'1.5'})])
        report,data=payload.collect(path,prior)
        entry=json.loads(gzip.decompress(data))['layers'][0]['entries'][0]
        self.assertEqual(entry['pax_headers'],{'comment':'synthetic','mtime':'1.5'})
        self.assertEqual(entry['mtime'],1.5)
        for headers in ({'comment':'x'*9000},{'mtime':'nan'}):
            path,prior=self.fixture([('file',tarfile.REGTYPE,b'x','',headers)])
            with self.assertRaises(ValueError):payload.collect(path,prior)
