#!/usr/bin/env python3
"""Compile one draft SHB Markdown source; no content edit can approve prices."""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'frontend/src/content/products/supporting-hours-bundle.md'
AUTHORITY=ROOT/'014-Shop-SHB-Proposal-Revision-2026-10-30.md'
SOURCE_SHA256='ba801dff4adbfdcfa0f1e43cfe1f2d6963780476867da1b5e6f737230a472b5e'


def require(value):
    if not value:raise ValueError('invalid_shb_source')


def unique(pairs):
    result={}
    for key,value in pairs:
        require(key not in result);result[key]=value
    return result


def read_source():
    text=SOURCE.read_text()
    require(text.startswith('---\n') and len(text.encode())<32768)
    return json.loads(text.split('---',2)[1],object_pairs_hook=unique,
        parse_constant=lambda _:require(False))


def validate(value):
    require(type(value) is dict and set(value)=={'schema_version','product_id','title','site','visibility','source_sha256','manual_time_tracking','variants','commercial'})
    require(type(value['schema_version']) is int and value['schema_version']==1
        and value['product_id']=='supporting-hours-bundle' and value['title']=='Supporting Hours Bundle'
        and value['site']=='https://shop.xspi.pro' and value['visibility']=='invitation-only'
        and value['source_sha256']==SOURCE_SHA256
        and hashlib.sha256(AUTHORITY.read_bytes()).hexdigest()==SOURCE_SHA256
        and value['manual_time_tracking'] is True)
    expected=[{'id':'shb-fpga-10h','label':'FPGA Supporting Hours Bundle','hours_per_bundle':10,'workflow':'checkout','hours_expire':False},
              {'id':'shb-asic-25h','label':'ASIC Supporting Hours Bundle','hours_per_bundle':25,'workflow':'request','hours_expire':None}]
    require(value['variants']==expected and all(type(v['hours_per_bundle']) is int for v in value['variants']))
    commercial=value['commercial']
    require(type(commercial) is dict and set(commercial)=={'currency','fpga_hourly_minor','asic_hourly_minor','approved_offer_revision','tax_policy_revision','terms_revision','privacy_revision','refund_revision','asic_supplement_revision','manual_charging_policy_revision'})
    require(all(v is None for v in commercial.values()))
    return value


def compile_catalog(check=False):
    value=validate(read_source())
    raw=json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
    revision=hashlib.sha256(raw).hexdigest();manifest=dict(value,revision=revision)
    encoded=json.dumps(manifest,ensure_ascii=False,indent=2)+'\n'
    outputs={ROOT/'catalog/shb-revisions'/f'{revision}.json':encoded,
        ROOT/'backend/shop/shb/revision.json':encoded,
        ROOT/'frontend/src/lib/shb.ts':'// Generated draft; private storefront delivery only.\nexport const shb = '+json.dumps(manifest,ensure_ascii=False,indent=2)+' as const;\n'}
    for path,content in outputs.items():
        if check:require(path.is_file() and path.read_text()==content)
        else:
            path.parent.mkdir(parents=True,exist_ok=True)
            if path.parent.name=='shb-revisions' and path.exists():require(path.read_text()==content)
            else:path.write_text(content)
    print(f'SHB_CATALOG_PASS revision={revision} checks=1 live_approved=false')
    return manifest


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true')
    compile_catalog(parser.parse_args().check)
