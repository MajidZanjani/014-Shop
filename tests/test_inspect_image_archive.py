import copy
import io
import json
import os
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import inspect_image_archive as scanner


def tar_bytes(entries,gzip=False):
    out=io.BytesIO()
    with tarfile.open(fileobj=out,mode='w:gz' if gzip else 'w') as archive:
        for name,data,kind in entries:
            member=tarfile.TarInfo(name);member.type=kind;member.size=len(data)
            archive.addfile(member,io.BytesIO(data))
    return out.getvalue()


def fixture(edit_config=None):
    layer=tar_bytes([('synthetic.txt',b'synthetic image payload',tarfile.REGTYPE)])
    digest=scanner.sha256(layer);layer_name=digest+'/layer.tar'
    config={'created':'1970-01-01T00:00:01+00:00','architecture':'amd64','os':'linux',
        'config':{'User':'10001:10001','WorkingDir':'/app','Env':['PYTHONDONTWRITEBYTECODE=1','PYTHONNOUSERSITE=1'],
                  'Cmd':['/synthetic/candidate']},'rootfs':{'type':'layers','diff_ids':['sha256:'+digest]}}
    if edit_config:edit_config(config)
    config_raw=json.dumps(config).encode();config_name=scanner.sha256(config_raw)+'.json'
    manifest=[{'Config':config_name,'RepoTags':['shop-postgres:candidate'],'Layers':[layer_name]}]
    return [(layer_name,layer,tarfile.REGTYPE),(config_name,config_raw,tarfile.REGTYPE),
            ('manifest.json',json.dumps(manifest).encode(),tarfile.REGTYPE)]


class ImageArchiveTests(unittest.TestCase):
    def inspect(self,entries):
        with tempfile.TemporaryDirectory() as name:
            path=Path(name)/'candidate.tar.gz';path.write_bytes(tar_bytes(entries,gzip=True))
            return scanner.inspect(path)

    def test_exact_config_layer_and_archive_hashes_without_runtime_grants(self):
        entries=fixture();report=self.inspect(entries)
        self.assertEqual(len(report['layers']),1)
        self.assertEqual(report['layers'][0]['diff_id'],'sha256:'+scanner.sha256(entries[0][1]))
        self.assertEqual(report['config_image_id'],'sha256:'+scanner.sha256(entries[1][1]))
        self.assertNotEqual(report['config_image_id'][7:],report['archive_manifest_sha256'])
        self.assertIsNone(report['oci_distribution_manifest_digest'])
        for flag in ('registry_push_performed','container_execution_qualified','inner_layer_semantics_reviewed',
                     'native_notice_inventory_complete','reproducibility_qualified','production_activation'):
            self.assertIs(report[flag],False)

    def test_changed_layer_and_config_filename_are_denied(self):
        for kind in ('layer','config'):
            with self.subTest(kind=kind):
                entries=fixture();index=0 if kind=='layer' else 1
                name,data,type_=entries[index];entries[index]=(name,data+b' ',type_)
                with self.assertRaises(ValueError):self.inspect(entries)

    def test_duplicate_traversal_links_and_absolute_outer_members_denied(self):
        for entry in [('..//escape',b'x',tarfile.REGTYPE),('/absolute',b'x',tarfile.REGTYPE),
                      ('unsafe\\path',b'x',tarfile.REGTYPE),('link',b'',tarfile.SYMTYPE),fixture()[0]]:
            with self.subTest(name=entry[0]),self.assertRaises(ValueError):self.inspect(fixture()+[entry])

    def test_archive_member_json_and_expanded_bounds(self):
        for bound,value in (('MAX_ARCHIVE',1),('MAX_MEMBERS',1),('MAX_JSON',1),('MAX_METADATA',1),('MAX_EXPANDED',1)):
            with self.subTest(bound=bound),patch.object(scanner,bound,value),self.assertRaises(ValueError):self.inspect(fixture())

    def test_candidate_user_environment_and_layer_count_are_checked(self):
        for kind in ('user','environment','count','architecture'):
            with self.subTest(kind=kind):
                def edit(config):
                    if kind=='user':config['config']['User']='0:0'
                    elif kind=='environment':config['config']['Env'].append('SYNTHETIC_PRIVATE=denied')
                    elif kind=='count':config['rootfs']['diff_ids']=[]
                    else:config['architecture']='unqualified'
                with self.assertRaises(ValueError):self.inspect(fixture(edit))

    def test_missing_unreferenced_and_multiple_images_are_denied(self):
        for kind in ('missing','unreferenced','multiple'):
            with self.subTest(kind=kind):
                entries=fixture()
                if kind=='missing':entries.pop(0)
                elif kind=='unreferenced':entries.append(('0'*64+'/layer.tar',b'unreferenced',tarfile.REGTYPE))
                else:
                    name,data,type_=entries[-1];image=json.loads(data);image.append(copy.deepcopy(image[0]))
                    entries[-1]=(name,json.dumps(image).encode(),type_)
                with self.assertRaises(ValueError):self.inspect(entries)

    def test_duplicate_json_fields_and_symlink_input_denied(self):
        entries=fixture();name,data,type_=entries[-1]
        entries[-1]=(name,data.replace(b'"Config":',b'"Config":"invented","Config":'),type_)
        with self.assertRaises(ValueError):self.inspect(entries)
        with tempfile.TemporaryDirectory() as name:
            path=Path(name)/'link';path.symlink_to('missing')
            with self.assertRaises(OSError):scanner.inspect(path)

    def test_named_archive_replacement_is_detected(self):
        with tempfile.TemporaryDirectory() as name:
            path=Path(name)/'candidate.tar.gz';data=tar_bytes(fixture(),gzip=True);path.write_bytes(data)
            actual=scanner.os.stat
            def replaced(target,*args,**kwargs):
                if Path(target)==path:
                    path.rename(path.with_suffix('.prior'));path.write_bytes(data)
                return actual(target,*args,**kwargs)
            with patch.object(scanner.os,'stat',side_effect=replaced),self.assertRaises(ValueError):scanner.inspect(path)
