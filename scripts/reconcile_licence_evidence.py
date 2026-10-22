#!/usr/bin/env python3
"""Reconcile retained observations only; never grant licence/inventory acceptance."""
import argparse
import os
import json
from pathlib import Path
import re
import stat
from audit_licence_gaps import ROOT,targets,require,sha256

SOURCES=('licences.json','licence-gap-audit.json','licence-name-audit.json',
         'embedded-licences.json','npm-notice-markers.json')
LIMIT=16*1024*1024
DIGEST=re.compile(r'[0-9a-f]{64}')


def read_file(directory,name):
    parts=Path(name).parts
    require(parts and not Path(name).is_absolute() and all(p not in ('','..','.') for p in parts),'unsafe evidence path')
    parent=os.open(directory,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
    try:
        for part in parts[:-1]:
            child=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=parent)
            os.close(parent);parent=child
        fd=os.open(parts[-1],os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC,dir_fd=parent)
        try:
            before=os.fstat(fd)
            require(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and 0<before.st_size<=LIMIT,
                    'bounded singly linked evidence required')
            chunks=[];remaining=before.st_size
            while remaining:
                chunk=os.read(fd,remaining);require(bool(chunk),'short evidence read')
                chunks.append(chunk);remaining-=len(chunk)
            raw=b''.join(chunks);after=os.fstat(fd)
            named=os.stat(parts[-1],dir_fd=parent,follow_symlinks=False)
            fields=('st_dev','st_ino','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns')
            require(all(getattr(before,k)==getattr(after,k)==getattr(named,k) for k in fields),
                    'evidence changed during read')
            return raw
        finally:os.close(fd)
    finally:os.close(parent)


def unique(pairs):
    value={}
    for key,item in pairs:
        require(key not in value,'duplicate JSON field');value[key]=item
    return value


def identity(record,group=None):
    return (record['group'] if group is None else group,record['name'],record['version'])


def indexed(records,group=None):
    result={identity(r,group):r for r in records}
    require(len(result)==len(records),'duplicate evidence identity')
    return result


def text(directory,value,prefix):
    digest=value.get('text_sha256',value.get('sha256'))
    require(type(digest) is str and DIGEST.fullmatch(digest),'invalid text digest')
    name=prefix+'/'+digest+'.txt'
    require(value['retained_path']==name,'text path substitution denied')
    raw=read_file(directory,name);require(sha256(raw)==digest,'retained text digest mismatch')
    return raw


def collect(directory):
    raw={name:read_file(directory,name) for name in SOURCES}
    values={name:json.loads(data,object_pairs_hook=unique) for name,data in raw.items()}
    require(all(type(v) is dict and type(v.get('schema_version')) is int and v['schema_version']==1
                for v in values.values()),'unsupported evidence schema')
    inventory=values['licences.json'];base=values['licence-gap-audit.json']
    gaps={(group,r['name'],r['version']):r for group,r in targets(inventory)}
    prior=indexed(base['findings'])
    require(set(prior)==set(gaps) and base['source_licences_sha256']==sha256(raw['licences.json'])
            and base['evidence_class']=='exact-distribution-archive-audit','baseline inventory mismatch')
    for key,record in gaps.items():
        require(all(prior[key][field]==record[field] for field in ('artifact_url','artifact_hash')),
                'baseline artifact mismatch')
    expected_classes={'licence-name-audit.json':'exact-distribution-extended-name-audit',
        'embedded-licences.json':'exact-distribution-embedded-source-headers',
        'npm-notice-markers.json':'exact-distribution-bounded-text-marker-discovery'}
    for name,kind in expected_classes.items():
        report=values[name]
        require(report['evidence_class']==kind and report['source_licences_sha256']==sha256(raw['licences.json'])
                and report['inventory_complete'] is False and report['legal_approval'] is False
                and report['package_wide_notice_review_complete'] is False,'supplemental scope/approval mismatch')
        if name!='embedded-licences.json':
            require(report['baseline_audit_sha256']==sha256(raw['licence-gap-audit.json']),'supplemental baseline mismatch')
    require(base['inventory_complete'] is False and base['legal_approval'] is False,'baseline approval mismatch')
    result={key:{'group':key[0],'name':key[1],'version':key[2],
        'artifact_url':r['artifact_url'],'artifact_hash':r['artifact_hash'],
        'named_texts':[],'embedded_headers':[],'marker_lines':[],
        'status':'observations-reconciled-review-pending',
        'package_wide_notice_review_complete':False,'legal_approval':False} for key,r in gaps.items()}
    def bind(record,key):
        require(key in gaps,'unknown supplemental identity')
        old=prior[key]
        require(all(record[field]==old[field] for field in ('artifact_url','artifact_hash','observed_archive_sha256')),
                'supplemental artifact substitution')
        members={m['path']:m for m in old['archive_members']}
        require(len(members)==len(old['archive_members']),'duplicate baseline member')
        return members
    named=indexed(values['licence-name-audit.json']['findings'])
    require(set(named)==set(gaps),'named evidence coverage mismatch')
    for key,record in named.items():
        members=bind(record,key)
        require(record['archive_members']==prior[key]['archive_members'],'named member inventory mismatch')
        seen=set()
        for item in record['candidate_notice_texts']:
            member=item['archive_path'];require(member not in seen,'duplicate named text');seen.add(member)
            require(member in members and members[member]['kind']=='file','unknown named member')
            content=text(directory,item,'licence-name-texts')
            require(len(content)==item['size']==members[member]['size'],'named text size mismatch')
            result[key]['named_texts'].append(item)
    headers=indexed(values['embedded-licences.json']['findings'],'python_tools')
    require(set(headers)=={key for key in gaps if key[0]=='python_tools'},'header evidence coverage mismatch')
    for key,record in headers.items():
        members=bind(record,key);member=record['archive_member']
        content=text(directory,record,'embedded-licence-texts')
        start,end=record['byte_start'],record['byte_end_exclusive']
        require(member in members and members[member]['kind']=='file'
                and type(start) is int and type(end) is int and start==0<end<=members[member]['size']
                and len(content)==end-start and DIGEST.fullmatch(record['member_sha256']),
                'header member/range mismatch')
        result[key]['embedded_headers'].append(record)
    markers=indexed(values['npm-notice-markers.json']['findings'],'npm')
    require(set(markers)=={key for key in gaps if key[0]=='npm'},'marker evidence coverage mismatch')
    for key,record in markers.items():
        members=bind(record,key);observed=record['member_observations']
        require(len({m['archive_member'] for m in observed})==len(observed)
                and {m['archive_member'] for m in observed}=={name for name,m in members.items() if m['kind']=='file'},
                'marker file coverage mismatch')
        for member in observed:
            name=member['archive_member'];require(member['size']==members[name]['size'],'marker member size mismatch')
            require(member['status'] in {'markers-observed','no-markers-in-selected-text',
                    'skipped-unselected-suffix','skipped-file-byte-bound','skipped-invalid-utf8','skipped-nul-containing'},
                    'unknown member observation status')
            observations=member.get('observations',[])
            require(bool(observations)==(member['status']=='markers-observed'),'marker observation status mismatch')
            if observations:require(member['status']=='markers-observed' and DIGEST.fullmatch(member['member_sha256']),
                                    'marker member hash/status mismatch')
            previous_end=0
            for item in observations:
                start,end=item['byte_start'],item['byte_end_exclusive']
                require(type(start) is int and type(end) is int and previous_end<=start<end<=member['size']
                        and type(item['markers']) is list and bool(item['markers']), 'marker range mismatch')
                previous_end=end
                if item['retention']=='exact-line-retained':
                    content=text(directory,item,'npm-notice-marker-texts')
                    require(len(content)==end-start,'marker retained range size mismatch')
                else:require(item['retention']=='line-too-long','unknown marker retention')
                result[key]['marker_lines'].append({'archive_member':name,'member_sha256':member['member_sha256'],**item})
    require(all(read_file(directory,name)==data for name,data in raw.items()),'source evidence changed during reconciliation')
    findings=[result[key] for key in sorted(result)]
    return {'schema_version':1,'evidence_class':'offline-retained-licence-observation-reconciliation',
        'source_sha256':{name:sha256(data) for name,data in raw.items()},
        'scope':'Reconciles retained reports/text hashes only; no archive recollection, completeness or legal classification',
        'inventory_accepted':False,'legal_approval':False,'package_wide_notice_review_complete':False,
        'findings':findings,
        'counts':{'original_gap_distributions':len(findings),
            'with_named_text':sum(bool(r['named_texts']) for r in findings),
            'with_embedded_header':sum(bool(r['embedded_headers']) for r in findings),
            'with_marker_lines':sum(bool(r['marker_lines']) for r in findings),
            'pending_package_wide_review':len(findings)}}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--write',action='store_true')
    args=parser.parse_args();directory=ROOT/'docs/evidence/t02'
    report=collect(directory);encoded=(json.dumps(report,indent=2)+'\n').encode()
    output=directory/'licence-evidence-review.json'
    if args.write:
        require(not output.exists() and not output.is_symlink(),'existing reconciliation evidence denied')
        with output.open('xb') as stream:stream.write(encoded)
    else:require(read_file(directory,output.name)==encoded,'reconciliation report mismatch')
    print('LICENCE_EVIDENCE_RECONCILIATION_PASS '+json.dumps(report['counts'],sort_keys=True)+'; inventory_accepted=false')


if __name__=='__main__':main()
