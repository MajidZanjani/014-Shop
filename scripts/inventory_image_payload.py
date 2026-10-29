#!/usr/bin/env python3
"""Inventory inner tar entries/bytes, never extract, follow links or run images."""
import argparse
import gzip
import hashlib
import json
import math
import os
import stat
from pathlib import Path,PurePosixPath
import tarfile
from audit_licence_gaps import ROOT,require,sha256
from audit_licence_names import extended_candidate
from inspect_image_archive import inspect,unique,CANDIDATE_IMAGES

MAX_ENTRIES=200000
MAX_PATH=4096
MAX_MANIFEST=128*1024**2


def canonical(name):
    require(type(name) is str and 0<len(name)<=MAX_PATH and not name.startswith('//')
            and '\\' not in name and '..' not in PurePosixPath(name).parts
            and all(ord(c)>=32 and ord(c)!=127 for c in name),'unsafe inner member path')
    return str(PurePosixPath(name.lstrip('/')))


def layer_entries(reader,totals):
    result=[];seen=set()
    with tarfile.open(fileobj=reader,mode='r|') as archive:
        for member in archive:
            name=canonical(member.name)
            require(name not in seen,'duplicate inner member path');seen.add(name)
            totals['entries']+=1;require(totals['entries']<=MAX_ENTRIES,'image entry bound exceeded')
            require(member.isfile() or member.isdir() or member.issym() or member.islnk(),
                    'inner special member denied')
            require(type(member.uid) is int and 0<=member.uid<2**32
                    and type(member.gid) is int and 0<=member.gid<2**32
                    and 0<=member.mode<=0o7777 and 0<=member.size<=4*1024**3,'inner numeric metadata bound exceeded')
            require(member.sparse is None,'sparse layer entries unsupported')
            require(type(member.mtime) in (int,float) and math.isfinite(member.mtime),'invalid inner mtime')
            require(len(member.pax_headers)<=128 and sum(len(k)+len(v) for k,v in member.pax_headers.items())<=8192,
                    'PAX metadata bound exceeded')
            kind='file' if member.isfile() else 'directory' if member.isdir() else 'symlink' if member.issym() else 'hardlink'
            entry={'path':name,'raw_archive_path':member.name,'absolute_archive_path':member.name.startswith('/'),'type':kind,'mode':member.mode,'uid':member.uid,'gid':member.gid,
                'mtime':member.mtime,'size':member.size,'pax_headers':dict(member.pax_headers)}
            if kind=='file':
                digest=hashlib.sha256();size=0
                with archive.extractfile(member) as content:
                    while chunk:=content.read(1024**2):
                        size+=len(chunk);require(size<=member.size,'inner file size exceeded');digest.update(chunk)
                require(size==member.size,'inner file size mismatch')
                entry['sha256']=digest.hexdigest();totals['regular_files']+=1;totals['file_bytes']+=size
                if extended_candidate(name):entry['notice_filename_candidate']=True
                if PurePosixPath(name).name.startswith('.wh.'):entry['whiteout_marker_unapplied']=True
            elif kind in ('symlink','hardlink'):
                require(type(member.linkname) is str and len(member.linkname)<=MAX_PATH
                        and all(ord(c)>=32 and ord(c)!=127 for c in member.linkname),'invalid recorded link target')
                entry['link_target_unresolved']=member.linkname
            result.append(entry)
    return result


def collect(path,prior_bytes,*,expected_image='shop-postgres'):
    prior=json.loads(prior_bytes,object_pairs_hook=unique)
    require(prior['evidence_class']=='local-built-docker-archive-inspection'
            and type(prior['schema_version']) is int and prior['schema_version']==1,'unsupported outer report')
    entries={};totals={'entries':0,'regular_files':0,'file_bytes':0}
    def observe(name,reader):entries[name]=layer_entries(reader,totals)
    observed=inspect(path,layer_observer=observe,expected_image=expected_image)
    require(observed==prior,'outer report/archive substitution denied')
    layers=[{'archive_member':layer['archive_member'],'diff_id':layer['diff_id'],
             'entries':entries[layer['archive_member']]} for layer in observed['layers']]
    manifest={'schema_version':1,'archive_sha256':observed['archive_sha256'],
        'config_image_id':observed['config_image_id'],'layers':layers}
    raw=json.dumps(manifest,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()+b'\n'
    require(len(raw)<=MAX_MANIFEST,'payload manifest byte bound exceeded')
    compressed=gzip.compress(raw,mtime=0)
    digest=sha256(compressed)
    notices=[{'layer_index':index,'path':e['path'],'sha256':e['sha256'],'size':e['size']}
        for index,layer in enumerate(layers) for e in layer['entries'] if e.get('notice_filename_candidate')]
    return {'schema_version':1,'evidence_class':'local-image-inner-layer-entry-inventory',
        'archive_sha256':observed['archive_sha256'],'config_image_id':observed['config_image_id'],
        'outer_report_sha256':sha256(prior_bytes),'layer_count':len(layers),'counts':totals,
        'payload_manifest':{'path':'image-payload-manifests/'+digest+'.json.gz','sha256':digest,
            'compressed_bytes':len(compressed),'uncompressed_sha256':sha256(raw),'uncompressed_bytes':len(raw)},
        'notice_filename_candidates':notices,
        'symlink_count':sum(e['type']=='symlink' for layer in layers for e in layer['entries']),
        'hardlink_count':sum(e['type']=='hardlink' for layer in layers for e in layer['entries']),
        'absolute_archive_member_names':sum(e['absolute_archive_path'] for layer in layers for e in layer['entries']),
        'whiteout_markers_unapplied':sum(bool(e.get('whiteout_marker_unapplied')) for layer in layers for e in layer['entries']),
        'merged_rootfs_qualified':False,'links_resolved':False,'native_notice_inventory_complete':False,
        'legal_approval':False,'container_execution_qualified':False,'reproducibility_qualified':False,'production_activation':False,
        'scope':'Layer entry metadata and regular bytes hashed only; links recorded/unfollowed, overlays/whiteouts unapplied, notice filenames not licence classification'},compressed


def retain(directory,report,payload,*,write=False):
    encoded=(json.dumps(report,indent=2)+'\n').encode();report_dir=directory/'image-payload-revisions'
    payload_dir=directory/'image-payload-manifests'
    output=report_dir/(sha256(encoded)+'.json')
    payload_file=directory/report['payload_manifest']['path']
    require(payload_file.parent==payload_dir and payload_file.name==sha256(payload)+'.json.gz','manifest path binding mismatch')
    if write:
        for folder in (report_dir,payload_dir):
            require(not folder.is_symlink(),'payload evidence directory symlink denied')
            if not folder.exists():folder.mkdir()
        require(not output.exists() and not output.is_symlink() and not payload_file.exists()
                and not payload_file.is_symlink(),'existing payload evidence denied')
        with payload_file.open('xb') as stream:stream.write(payload)
        with output.open('xb') as stream:stream.write(encoded)
    else:
        require(not report_dir.is_symlink() and not payload_dir.is_symlink()
                and not output.is_symlink() and not payload_file.is_symlink()
                and output.read_bytes()==encoded and payload_file.read_bytes()==payload,'payload evidence mismatch')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive',required=True,type=Path);parser.add_argument('--outer-report',required=True,type=Path)
    parser.add_argument('--write',action='store_true')
    parser.add_argument('--image',choices=CANDIDATE_IMAGES,default='shop-postgres');args=parser.parse_args()
    descriptor=os.open(args.outer_report,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC)
    with os.fdopen(descriptor,'rb') as source:
        before=os.fstat(source.fileno())
        require(stat.S_ISREG(before.st_mode) and 0<before.st_size<=1024**2,'bounded outer report required')
        raw=source.read(1024**2+1);after=os.fstat(source.fileno());named=os.stat(args.outer_report,follow_symlinks=False)
        require(len(raw)==before.st_size and all(getattr(before,key)==getattr(after,key)==getattr(named,key)
                for key in ('st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns')),'outer report changed during read')
    require(args.outer_report.name==sha256(raw)+'.json','outer report content address mismatch')
    report,payload=collect(args.archive,raw,expected_image=args.image);retain(ROOT/'docs/evidence/t02',report,payload,write=args.write)
    print('IMAGE_PAYLOAD_INVENTORY_PASS '+json.dumps(report['counts'],sort_keys=True)+
          f' layers={report["layer_count"]} notice_filename_candidates={len(report["notice_filename_candidates"])} image={args.image}; runtime_legal_merged_rootfs_pending=true')


if __name__=='__main__':main()
