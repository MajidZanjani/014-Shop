#!/usr/bin/env python3
"""Supplement original named-file audit with prefixed names; no legal conclusions."""
import argparse
import json
from pathlib import PurePosixPath
import re
from audit_licence_gaps import ROOT,audit,candidate,fetch,require,sha256

POLICY=r'(?i)^(?:[a-z0-9]+[._-])+(?:licen[cs]es?|copying|copyright|notice)(?:[._-][a-z0-9._-]+)?$'


def extended_candidate(name):
    return candidate(name) or bool(re.fullmatch(POLICY,PurePosixPath(name).name))


def collect(source, baseline, loader=fetch):
    prior=json.loads(baseline)
    require(prior['source_licences_sha256']==sha256(source)
            and prior['evidence_class']=='exact-distribution-archive-audit', 'baseline source binding mismatch')
    report,texts=audit(source,loader,notice_candidate=extended_candidate)
    old={(r['group'],r['name'],r['version']):r for r in prior['findings']}
    new={(r['group'],r['name'],r['version']):r for r in report['findings']}
    require(len(old)==len(prior['findings']) and set(old)==set(new), 'baseline identity set mismatch')
    for identity,record in new.items():
        for key in ('artifact_url','artifact_hash','observed_archive_sha256','archive_members'):
            require(record[key]==old[identity][key], 'baseline archive evidence mismatch')
        for text in record['candidate_notice_texts']:
            text['retained_path']='licence-name-texts/'+text['sha256']+'.txt'
    report.update(evidence_class='exact-distribution-extended-name-audit',
        baseline_audit_sha256=sha256(baseline),candidate_filename_policy=POLICY,
        package_wide_notice_review_complete=False,
        scope='Original named-file policy plus bounded prefixed notice names; exact distribution bytes only, no legal/native/package-wide completeness')
    return report,texts


def retain(directory,report,texts,*,write=False):
    output=directory/'licence-name-audit.json';text_dir=directory/'licence-name-texts'
    encoded=(json.dumps(report,indent=2)+'\n').encode()
    if write:
        require(not output.exists() and not output.is_symlink()
                and not text_dir.exists() and not text_dir.is_symlink(), 'existing supplemental evidence denied')
        if texts:text_dir.mkdir()
        for digest,content in sorted(texts.items()):
            with (text_dir/(digest+'.txt')).open('xb') as stream:stream.write(content)
        with output.open('xb') as stream:stream.write(encoded)
    else:
        require(not output.is_symlink() and output.read_bytes()==encoded, 'supplemental report mismatch')
        require(not text_dir.is_symlink(), 'supplemental text directory symlink denied')
        retained={p.name for p in text_dir.iterdir()} if text_dir.exists() else set()
        require(retained=={d+'.txt' for d in texts}, 'supplemental text set mismatch')
        for digest,content in texts.items():
            file=text_dir/(digest+'.txt')
            require(not file.is_symlink() and file.read_bytes()==content, 'supplemental text mismatch')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write',action='store_true')
    args=parser.parse_args();directory=ROOT/'docs/evidence/t02'
    report,texts=collect((directory/'licences.json').read_bytes(),(directory/'licence-gap-audit.json').read_bytes())
    retain(directory,report,texts,write=args.write)
    found=sum(bool(r['candidate_notice_texts']) for r in report['findings'])
    print(f'LICENCE_NAME_AUDIT_PASS distributions={len(report["findings"])} with_named_text={found} texts={len(texts)}; legal_and_full_inventory_pending=true')


if __name__=='__main__':main()
