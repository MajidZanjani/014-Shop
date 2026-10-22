#!/usr/bin/env python3
"""Discover bounded textual notice markers in exact archives; no licence approval."""
import argparse
import io
import json
from pathlib import PurePosixPath
import re
import tarfile
from audit_licence_gaps import ROOT,targets,fetch,verify,inspect_archive,require,sha256

MAX_FILE=1024*1024
MAX_SCANNED=16*1024*1024
MAX_LINE=16384
MAX_MARKERS=512
SUFFIXES={'.md','.markdown','.rst','.txt','.js','.cjs','.mjs','.ts','.h','.c','.cpp','.json'}
PATTERNS={
    'copyright':rb'copyright',
    'spdx-license-identifier':rb'spdx-license-identifier',
    'permission-grant':rb'permission is hereby granted',
    'warranty-phrase':rb'the software is provided',
    'redistribution-phrase':rb'redistribution and use',
    'gnu-license-reference':rb'gnu (?:lesser )?general public license',
    'license-reference':rb'licensed under|see[^\r\n]{0,120}(?:licen[cs]e|copying)',
    'license-section':rb'^#{1,6}[ \t]+licen[cs]e\b',
    'declared-license-field':rb'"licen[cs]e"[ \t]*:',
}


def marker_lines(content):
    require(len(content)<=MAX_FILE, 'text file byte bound exceeded')
    content.decode('utf8')  # exact bytes retained; never replacement decoding
    spans={};matches=0
    for marker,pattern in PATTERNS.items():
        for match in re.finditer(pattern,content,re.IGNORECASE|re.MULTILINE):
            matches+=1;require(matches<=MAX_MARKERS,'marker count exceeded')
            start=content.rfind(b'\n',0,match.start())+1
            end=content.find(b'\n',match.end());end=len(content) if end<0 else end+1
            spans.setdefault((start,end),set()).add(marker)
    result=[];texts={}
    for (start,end),markers in sorted(spans.items()):
        observation={'byte_start':start,'byte_end_exclusive':end,'markers':sorted(markers),
            'retention':'line-too-long' if end-start>MAX_LINE else 'exact-line-retained'}
        if end-start<=MAX_LINE:
            raw=content[start:end];digest=sha256(raw);texts[digest]=raw
            observation.update(text_sha256=digest,retained_path='npm-notice-marker-texts/'+digest+'.txt')
        result.append(observation)
    return result,texts


def scan(data):
    observations=[];texts={};scanned=0
    with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz') as archive:
        for member in archive:
            if not member.isfile():continue
            item={'archive_member':member.name,'size':member.size}
            if PurePosixPath(member.name).suffix.lower() not in SUFFIXES:
                item['status']='skipped-unselected-suffix'
            elif member.size>MAX_FILE:
                item['status']='skipped-file-byte-bound'
            else:
                scanned+=member.size;require(scanned<=MAX_SCANNED,'selected text total exceeded')
                with archive.extractfile(member) as stream:content=stream.read(MAX_FILE+1)
                require(len(content)==member.size,'text member length mismatch')
                item['member_sha256']=sha256(content)
                try:
                    content.decode('utf8')
                    require(b'\x00' not in content,'NUL-containing text denied')
                except UnicodeDecodeError:item['status']='skipped-invalid-utf8'
                except ValueError:item['status']='skipped-nul-containing'
                else:
                    lines,retained=marker_lines(content);texts.update(retained)
                    item.update(status='markers-observed' if lines else 'no-markers-in-selected-text',observations=lines)
            observations.append(item)
    return sorted(observations,key=lambda x:x['archive_member']),texts


def collect(source,baseline,loader=fetch):
    prior=json.loads(baseline)
    require(prior['source_licences_sha256']==sha256(source)
            and prior['evidence_class']=='exact-distribution-archive-audit','baseline source binding mismatch')
    old={(r['group'],r['name'],r['version']):r for r in prior['findings']}
    require(len(old)==len(prior['findings']),'duplicate baseline identity')
    records=[r for group,r in targets(json.loads(source)) if group=='npm']
    require({('npm',r['name'],r['version']) for r in records}=={key for key in old if key[0]=='npm'},
            'baseline npm identity set mismatch')
    findings=[];texts={}
    for record in records:
        data=loader(record['artifact_url'],'npm');verify(data,record['artifact_hash'])
        members,_=inspect_archive(data,'npm')
        previous=old[('npm',record['name'],record['version'])]
        require(previous['artifact_url']==record['artifact_url'] and previous['artifact_hash']==record['artifact_hash']
                and previous['observed_archive_sha256']==sha256(data) and previous['archive_members']==members,
                'baseline archive evidence mismatch')
        observations,retained=scan(data);texts.update(retained)
        findings.append({'name':record['name'],'version':record['version'],'artifact_url':record['artifact_url'],
            'artifact_hash':record['artifact_hash'],'observed_archive_sha256':sha256(data),
            'member_observations':observations,'status':'bounded-marker-discovery-review-pending'})
    return {'schema_version':1,'evidence_class':'exact-distribution-bounded-text-marker-discovery',
        'source_licences_sha256':sha256(source),'baseline_audit_sha256':sha256(baseline),
        'inventory_complete':False,'legal_approval':False,'package_wide_notice_review_complete':False,
        'policy':{'suffixes':sorted(SUFFIXES),'max_file_bytes':MAX_FILE,'max_scanned_bytes_per_archive':MAX_SCANNED,
            'max_retained_line_bytes':MAX_LINE,'max_markers_per_member':MAX_MARKERS,
            'patterns':{key:value.decode('ascii') for key,value in PATTERNS.items()}},
        'scope':'Exact marker lines only, not complete notices; skipped/binary/oversize/non-UTF8 members unreviewed; no code execution or legal classification',
        'findings':findings},texts


def retain(directory,report,texts,*,write=False):
    output=directory/'npm-notice-markers.json';text_dir=directory/'npm-notice-marker-texts'
    encoded=(json.dumps(report,indent=2)+'\n').encode()
    if write:
        require(not output.exists() and not output.is_symlink()
                and not text_dir.exists() and not text_dir.is_symlink(),'existing marker evidence denied')
        if texts:text_dir.mkdir()
        for digest,content in sorted(texts.items()):
            with (text_dir/(digest+'.txt')).open('xb') as stream:stream.write(content)
        with output.open('xb') as stream:stream.write(encoded)
    else:
        require(not output.is_symlink() and output.read_bytes()==encoded,'marker report mismatch')
        require(not text_dir.is_symlink(),'marker text directory symlink denied')
        names={p.name for p in text_dir.iterdir()} if text_dir.exists() else set()
        require(names=={digest+'.txt' for digest in texts},'marker text set mismatch')
        for digest,content in texts.items():
            file=text_dir/(digest+'.txt')
            require(not file.is_symlink() and file.read_bytes()==content,'marker text mismatch')


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--write',action='store_true')
    args=parser.parse_args();directory=ROOT/'docs/evidence/t02'
    report,texts=collect((directory/'licences.json').read_bytes(),(directory/'licence-gap-audit.json').read_bytes())
    retain(directory,report,texts,write=args.write)
    markers=sum(bool(m.get('observations')) for f in report['findings'] for m in f['member_observations'])
    print(f'NPM_NOTICE_MARKERS_PASS distributions={len(report["findings"])} members_with_markers={markers} texts={len(texts)}; legal_and_full_inventory_pending=true')


if __name__=='__main__':main()
