#!/usr/bin/env python3
"""Explicit derivative of retained npm evidence; raw bytes are never rewritten."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
from check_python import frozen_environment,require
from inventory_artifacts import reconcile

BAD_REFERENCE={'type':'vcs','url':'git+https://github.com:ascorbic/am-i-vibing.git'}
RAW='npm-sbom.json'
DERIVED='npm-sbom-derived.json'
RECEIPT='npm-sbom-derivation.json'


def unique_fields(pairs):
    value={}
    for key,item in pairs:
        require(key not in value,'duplicate JSON field')
        value[key]=item
    return value


def derive(raw):
    require(type(raw) is bytes and 0<len(raw)<=8388608,'bounded raw bytes required')
    value=json.loads(raw.decode('utf8'),object_pairs_hook=unique_fields)
    require(type(value) is dict and value.get('bomFormat')=='CycloneDX'
            and value.get('specVersion')=='1.5','exact raw schema version required')
    result=copy.deepcopy(value)
    targets=(('am-i-vibing','0.5.0',BAD_REFERENCE),
             ('common-ancestor-path','2.0.0',{'type':'vcs','url':'git@github.com:isaacs/common-ancestor-path'}))
    changes=[]
    for name,version,bad_reference in targets:
        ref=name+'@'+version
        matches=[(i,c) for i,c in enumerate(result.get('components',[])) if c.get('bom-ref')==ref]
        require(len(matches)==1,'one exact component required')
        index,component=matches[0]
        require(component.get('name')==name and component.get('version')==version
                and component.get('purl')=='pkg:npm/'+ref,'exact component identity required')
        refs=component.get('externalReferences',[])
        positions=[i for i,r in enumerate(refs) if r==bad_reference]
        require(len(positions)==1,'one exact known malformed reference required')
        position=positions[0];removed=refs.pop(position)
        changes.append({'operation':'remove','json_pointer':f'/components/{index}/externalReferences/{position}',
            'component_ref':ref,'removed_value':removed,
            'reason':'Malformed repository URI rejected by strict schema validation; no replacement asserted.'})
    # Only disclosed omissions; no replacement URLs are inferred.
    restored=copy.deepcopy(result)
    for change in reversed(changes):
        parts=change['json_pointer'].split('/')
        restored['components'][int(parts[2])]['externalReferences'].insert(int(parts[4]),change['removed_value'])
    require(restored==value,'only disclosed reference removals permitted')
    derived=(json.dumps(result,indent=2,ensure_ascii=True,allow_nan=False)+'\n').encode('ascii')
    receipt={'schema_version':1,'evidence_class':'local-synthetic',
        'artifact_kind':'explicit-npm-sbom-derivative','raw_artifact':RAW,'derived_artifact':DERIVED,
        'raw_sha256':hashlib.sha256(raw).hexdigest(),'derived_sha256':hashlib.sha256(derived).hexdigest(),
        'changes':changes,
        'raw_upstream_metadata_resolved':False,'software_approval':False,
        'legal_approval':False,'inventory_complete':False}
    return derived,receipt


def execute(write=False):
    start=time.monotonic();evidence=ROOT/'docs/evidence/t02'
    raw=(evidence/RAW).read_bytes();derived,receipt=derive(raw)
    original=json.loads(raw);value=json.loads(derived)
    records=json.loads((evidence/'licences.json').read_bytes())['npm']
    raw_count=reconcile(records,original,'npm');count=reconcile(records,value,'npm')
    require(count==raw_count,'component coverage changed')
    parent=Path(os.environ.get('SHOP_TEST_SCRATCH',ROOT/'.scratch'))
    require(parent.is_dir() and not parent.is_symlink(),'owned scratch parent required')
    with tempfile.TemporaryDirectory(prefix='sbom-derive-',dir=parent) as directory:
        scratch=Path(directory);source=scratch/'raw.json';target=scratch/'derived.json'
        source.write_bytes(raw);target.write_bytes(derived)
        with frozen_environment('tools',scratch/'tools') as (python,env,expected):
            program="""import importlib.metadata,json,pathlib,sys
from cyclonedx.validation.json import JsonStrictValidator
from cyclonedx.schema import SchemaVersion
validator=JsonStrictValidator(SchemaVersion.V1_5)
raw_error=validator.validate_str(pathlib.Path(sys.argv[1]).read_text())
derived_error=validator.validate_str(pathlib.Path(sys.argv[2]).read_text())
print(json.dumps({'validator':'cyclonedx-python-lib','validator_version':importlib.metadata.version('cyclonedx-python-lib'),
 'schema_version':'1.5','raw_valid':raw_error is None,'derived_valid':derived_error is None,
 'raw_diagnostic':str(raw_error)[:3000] if raw_error is not None else None,
 'derived_diagnostic':str(derived_error)[:3000] if derived_error is not None else None}))
"""
            result=subprocess.run([str(python),'-I','-c',program,str(source),str(target)],
                env=env,capture_output=True,text=True,check=True,timeout=20)
            validation=json.loads(result.stdout)
            require(validation['raw_valid'] is False and validation['derived_valid'] is True,
                    'actual strict raw rejection and derivative acceptance required: '+repr(validation))
            receipt['schema_validation']=validation
    receipt['installed_unique_components']=count
    receipt_data=(json.dumps(receipt,indent=2,sort_keys=True)+'\n').encode()
    require((evidence/RAW).read_bytes()==raw,'raw evidence changed during validation')
    if write:
        # Exclusive new evidence only. A partial write is retained for review.
        for name,data in ((DERIVED,derived),(RECEIPT,receipt_data)):
            with (evidence/name).open('xb') as file:file.write(data)
    else:
        require((evidence/DERIVED).read_bytes()==derived
                and (evidence/RECEIPT).read_bytes()==receipt_data,'retained derivation mismatch')
    print(f'NPM_SBOM_DERIVATION_PASS checks=4 components={count} duration_seconds={time.monotonic()-start:.3f}')
    print('Explicit derived schema evidence only; unchanged raw invalid; licences/native/OCI and complete inventory pending')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write',action='store_true',help='create new derivative/receipt exclusively; default checks retained files')
    execute(parser.parse_args().write)

if __name__=='__main__':
    try:main()
    except (ValueError,OSError,subprocess.SubprocessError):
        print('NPM_SBOM_DERIVATION_FAIL: explicit derivation or retained evidence invalid',file=sys.stderr)
        raise SystemExit(1) from None
