#!/usr/bin/env python3
"""Inspect one Docker save archive without extraction/import/execution.

Config ImageID and uncompressed layer DiffIDs are not an OCI registry manifest.
This collector does not validate inner layer filesystem semantics or runtime.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path,PurePosixPath
import re
import stat
import tarfile
from audit_licence_gaps import ROOT,require,sha256

MAX_ARCHIVE=1024**3
MAX_EXPANDED=4*1024**3
MAX_MEMBERS=2048
MAX_JSON=1024**2
MAX_METADATA=8*1024**2
META=('st_dev','st_ino','st_mode','st_size','st_mtime_ns','st_ctime_ns')
CANDIDATE_IMAGES=('shop-app','shop-worker','shop-postgres','shop-gateway')


def unique(pairs):
    value={}
    for key,item in pairs:
        require(key not in value,'duplicate JSON field');value[key]=item
    return value


class DigestReader:
    """Account every streamed layer byte, including bytes consumed by an observer."""
    def __init__(self,stream,maximum):
        self.stream=stream;self.maximum=maximum;self.size=0;self.digest=hashlib.sha256()
    def read(self,size):
        require(type(size) is int and size>=0,'bounded layer read required')
        data=self.stream.read(size);self.size+=len(data)
        require(self.size<=self.maximum,'layer reader byte bound exceeded')
        self.digest.update(data)
        return data


def inspect(path, *, layer_observer=None, expected_image='shop-postgres'):
    require(type(expected_image) is str and expected_image in CANDIDATE_IMAGES,'unsupported candidate image')
    path=Path(path)
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC)
    with os.fdopen(fd,'rb') as stream:
        before=os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode) and 0<before.st_size<=MAX_ARCHIVE,'archive byte/type bound exceeded')
        compressed=hashlib.sha256()
        while chunk:=stream.read(1024**2):compressed.update(chunk)
        stream.seek(0);members={};json_bytes={};total=0;metadata_total=0
        with tarfile.open(fileobj=stream,mode='r|gz') as archive:
            for member in archive:
                name=member.name;canonical=str(PurePosixPath(name))
                require(name==canonical and not name.startswith('/') and '..' not in PurePosixPath(name).parts
                        and '\\' not in name and all(32<=ord(c)<127 for c in name),'unsafe outer archive path')
                require(name not in members and len(members)<MAX_MEMBERS,'duplicate/member bound exceeded')
                require(member.isfile() or member.isdir(),'outer archive links/special members denied')
                require(0<=member.size<=MAX_EXPANDED,'member byte bound exceeded')
                total+=member.size;require(total<=MAX_EXPANDED,'expanded archive bound exceeded')
                item={'path':name,'size':member.size,'kind':'file' if member.isfile() else 'directory'}
                if member.isfile():
                    capture=name.endswith('.json') or name=='repositories'
                    require(not capture or member.size<=MAX_JSON,'metadata JSON bound exceeded')
                    if capture:
                        metadata_total+=member.size
                        require(metadata_total<=MAX_METADATA,'total metadata byte bound exceeded')
                    digest=hashlib.sha256();chunks=[];size=0
                    with archive.extractfile(member) as payload:
                        if layer_observer is not None and name.endswith('/layer.tar'):
                            reader=DigestReader(payload,member.size)
                            layer_observer(name,reader)
                            while reader.read(1024**2):pass
                            size=reader.size;digest=reader.digest
                        else:
                            while chunk:=payload.read(1024**2):
                                size+=len(chunk);require(size<=member.size,'member byte length exceeded')
                                digest.update(chunk)
                                if capture:chunks.append(chunk)
                    require(size==member.size,'member byte length mismatch')
                    item['sha256']=digest.hexdigest()
                    if capture:json_bytes[name]=b''.join(chunks)
                members[name]=item
        after=os.fstat(stream.fileno());named=os.stat(path,follow_symlinks=False)
        require(all(getattr(before,k)==getattr(after,k)==getattr(named,k) for k in META),'archive changed during inspection')
    require('manifest.json' in json_bytes,'Docker archive manifest absent')
    manifest=json.loads(json_bytes['manifest.json'],object_pairs_hook=unique)
    require(type(manifest) is list and len(manifest)==1,'exactly one image required')
    image=manifest[0]
    require(type(image) is dict and set(image)=={'Config','RepoTags','Layers'},'unsupported archive manifest fields')
    config_name=image['Config'];layers=image['Layers'];tags=image['RepoTags']
    require(type(config_name) is str and config_name in json_bytes
            and type(layers) is list and 1<=len(layers)<=MAX_MEMBERS
            and all(type(p) is str for p in layers) and len(set(layers))==len(layers)
            and type(tags) is list and len(tags)==1 and tags[0]==expected_image+':candidate',
            'candidate manifest references invalid')
    config_raw=json_bytes[config_name];config=json.loads(config_raw,object_pairs_hook=unique)
    image_id=sha256(config_raw)
    require(config_name==image_id+'.json','config filename/image ID mismatch')
    require(config['architecture']=='amd64' and config['os']=='linux'
            and config['created']=='1970-01-01T00:00:01+00:00'
            and config['config']['User']=='10001:10001' and config['config']['WorkingDir']=='/app'
            and config['config']['Env']==['PYTHONDONTWRITEBYTECODE=1','PYTHONNOUSERSITE=1']
            and type(config['config']['Cmd']) is list and bool(config['config']['Cmd'])
            and all(type(v) is str for v in config['config']['Cmd']), 'candidate execution metadata mismatch')
    rootfs=config['rootfs']
    require(type(rootfs) is dict and set(rootfs)=={'type','diff_ids'} and rootfs['type']=='layers'
            and type(rootfs['diff_ids']) is list and len(rootfs['diff_ids'])==len(layers),'layer/config count mismatch')
    observed=[]
    for name,diff_id in zip(layers,rootfs['diff_ids'],strict=True):
        require(type(diff_id) is str and re.fullmatch(r'sha256:[0-9a-f]{64}',diff_id)
                and name==diff_id[7:]+'/layer.tar' and name in members
                and members[name]['kind']=='file' and members[name]['size']>0
                and members[name]['sha256']==diff_id[7:],'layer DiffID/reference mismatch')
        observed.append({'archive_member':name,'uncompressed_tar_bytes':members[name]['size'],'diff_id':diff_id})
    require({name for name in members if name.endswith('/layer.tar')}==set(layers),'unreferenced layer member')
    return {'schema_version':1,'evidence_class':'local-built-docker-archive-inspection',
        'archive_path':str(path),'archive_bytes':before.st_size,'archive_sha256':compressed.hexdigest(),
        'archive_format':'Docker save archive (gzip-compressed outer tar)',
        'archive_manifest_sha256':sha256(json_bytes['manifest.json']),
        'config_image_id':'sha256:'+image_id,'config_archive_member':config_name,
        'config':config,'layers':observed,'outer_members':sorted(members.values(),key=lambda x:x['path']),
        'oci_distribution_manifest_digest':None,'registry_push_performed':False,
        'container_execution_qualified':False,'inner_layer_semantics_reviewed':False,
        'native_notice_inventory_complete':False,'reproducibility_qualified':False,'production_activation':False,
        'scope':'Exact archive/config/ordered uncompressed layer byte hashes only; no inner extraction, import, runtime or OCI manifest construction'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive',required=True,type=Path);parser.add_argument('--write',action='store_true')
    parser.add_argument('--image',choices=CANDIDATE_IMAGES,default='shop-postgres')
    args=parser.parse_args();report=inspect(args.archive,expected_image=args.image)
    encoded=(json.dumps(report,indent=2)+'\n').encode()
    directory=ROOT/'docs/evidence/t02/image-archive-revisions'
    output=directory/(sha256(encoded)+'.json')
    if args.write:
        if not directory.exists():directory.mkdir()
        require(not directory.is_symlink() and not output.exists() and not output.is_symlink(),'existing archive inspection evidence denied')
        with output.open('xb') as stream:stream.write(encoded)
    else:
        require(not directory.is_symlink() and not output.is_symlink() and output.read_bytes()==encoded,'archive inspection report mismatch')
    print(f'IMAGE_ARCHIVE_INSPECTION_PASS layers={len(report["layers"])} archive_bytes={report["archive_bytes"]} image={args.image}; runtime_reproducibility_oci_manifest_pending=true')


if __name__=='__main__':main()
