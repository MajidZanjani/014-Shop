#!/usr/bin/env python3
"""Retain standard installed-graph SBOMs; never invent unbuilt image evidence."""
import argparse
from contextlib import ExitStack
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import urllib.request
import unittest
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
from check_python import frozen_environment,require,canonical,inspect_environment,validate_environment
from check_frontend import manifest,copy_inputs,safe_env,command


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sbom_identities(value,kind):
    require(value.get('bomFormat')=='CycloneDX' and value.get('specVersion') in {'1.5','1.6','1.7'},'standard SBOM required')
    require(bool(value.get('components')) and bool(value.get('dependencies')),'nonempty component and dependency evidence required')
    result=set()
    for component in value['components']:
        name=component.get('name','')
        if kind=='npm' and component.get('group'):name=component['group']+'/'+name
        if kind=='python':name=canonical(name)
        require(bool(component.get('version')) and bool(component.get('bom-ref')),'SBOM identity absent')
        result.add((name,component['version']))
    return result


def reconcile(records,bom,kind,*,require_text=False):
    require(bool(records),'empty artifact inventory')
    identities={(canonical(x['name']) if kind=='python' else x['name'],x['version']) for x in records}
    require(identities==sbom_identities(bom,kind),'installed/SBOM component coverage mismatch')
    for item in records:
        require(isinstance(item['artifact_url'],str) and item['artifact_url'].startswith('https://') and isinstance(item['artifact_hash'],str),'distribution identity/hash absent')
        require(re.fullmatch(r'(sha256:[0-9a-f]{64}|sha(?:256|384|512)-[A-Za-z0-9+/]+={0,2})',item['artifact_hash']) is not None,'distribution digest malformed or unsupported')
        if require_text:require(bool(item['licence_texts']),'incorporated licence text missing')
        for text in item['licence_texts']:
            require(isinstance(text['sha256'],str) and re.fullmatch('[0-9a-f]{64}',text['sha256']),'licence text hash missing')
    return len(identities)


def texts(root,files):
    results=[]
    for name in files:
        path=root/name
        require(path.resolve().is_relative_to(root.resolve()),'licence path escapes installed distribution')
        if path.is_file() and not path.is_symlink():
            require(path.stat().st_size<10485760,'bounded licence file required')
            results.append({'path':str(name),'sha256':digest(path)})
    return results


def npm_inventory(project,env):
    command(['npm','ci','--ignore-scripts=false','--no-audit','--no-fund'],project,env)
    raw=command(['npm','sbom','--sbom-format','cyclonedx'],project,env)
    bom=json.loads(raw)
    installed=json.loads((project/'node_modules/.package-lock.json').read_text())['packages']
    locked=json.loads((project/'package-lock.json').read_text())['packages']
    records=[]
    for relative,meta in installed.items():
        path=project/relative
        require(path.is_dir() and not path.is_symlink() and (path/'package.json').is_file(),'actual installed package absent')
        package=json.loads((path/'package.json').read_text())
        require(relative in locked and package['version']==locked[relative]['version'],'installed lock identity mismatch')
        require(meta.get('integrity')==locked[relative].get('integrity') and bool(meta.get('integrity')),'installed artifact integrity mismatch')
        names=[]
        for child in path.rglob('*'):
            name=child.relative_to(path)
            if 'node_modules' in name.parts or child.is_symlink():continue
            if child.is_file() and re.match(r'(?i)^(licen[cs]e|copying|notice)([._-].*)?$',child.name):names.append(name)
        evidence=texts(path,names)
        records.append({'name':package['name'],'version':package['version'],'artifact_url':locked[relative].get('resolved'),
            'artifact_hash':meta['integrity'],'dependencies':package.get('dependencies',{}),
            'licence_expression':package.get('license'),'licence_texts':evidence,
            'findings':[] if evidence else ['No incorporated licence text found; review pending']})
    count=reconcile(records,bom,'npm')
    absent=[{'path':name,'version':item.get('version'),'optional':item.get('optional',False),'status':'not installed on qualified platform'} for name,item in locked.items() if name and name not in installed]
    require(all(item['optional'] for item in absent),'nonoptional lock component absent')
    return raw,records,absent,count


def python_inventory(python,env,wheels):
    source='''import importlib.metadata as m,json,pathlib,re
items=[]
for dist in m.distributions():
 files=[]
 for f in dist.files or []:
  p=pathlib.Path(str(f)); n=p.name
  if re.match(r'(?i)^(licen[cs]e|copying|notice)([._-].*)?$',n) or '.dist-info/licenses/' in str(p):
   if dist.locate_file(f).is_file():files.append(str(f))
 items.append({'name':dist.metadata['Name'],'version':dist.version,'root':str(dist.locate_file('')),
 'licence_expression':dist.metadata.get('License-Expression') or dist.metadata.get('License'),
 'dependencies':dist.requires or [],'files':files})
print(json.dumps(items))
'''
    import check_python
    actual=json.loads(check_python.run([python,'-I','-c',source],env=env))
    records=[]
    for item in actual:
        matches=[]
        for wheel in wheels.glob('*.whl'):
            # The hash-installed wheel filename has canonical PEP427 name/version.
            parts=wheel.name.split('-')
            if canonical(parts[0])==canonical(item['name']) and parts[1]==item['version']:matches.append(wheel)
        require(len(matches)==1,'installed distribution wheel provenance absent')
        wheel=matches[0];sha=digest(wheel)
        url='https://pypi.org/pypi/'+item['name']+'/'+item['version']+'/json'
        with urllib.request.urlopen(url,timeout=10) as response:raw=response.read(5000001)
        require(len(raw)<5000001,'bounded registry metadata required')
        candidates=[x for x in json.loads(raw)['urls'] if x['filename']==wheel.name and x['digests']['sha256']==sha]
        require(len(candidates)==1,'official artifact metadata/hash mismatch')
        evidence=texts(Path(item['root']),map(Path,item['files']))
        records.append({'name':item['name'],'version':item['version'],'artifact_url':candidates[0]['url'],'artifact_hash':'sha256:'+sha,
            'dependencies':item['dependencies'],'licence_expression':item['licence_expression'],'licence_texts':evidence,
            'findings':[] if evidence else ['No incorporated licence text found; review pending']})
    return records


def local_inventory():
    start=time.monotonic();owned=ROOT/'.scratch';owned.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='inventory-',dir=owned) as directory:
        scratch=Path(directory)
        project=scratch/'frontend';copy_inputs(ROOT/'frontend',project,manifest(json.loads((ROOT/'frontend/build-inputs.json').read_text())))
        env=safe_env(scratch);npm_raw,npm,absent,npm_count=npm_inventory(project,env)
        data={};counts={}
        with ExitStack() as stack:
            environments={}
            for kind in ('runtime','tools'):
                python,env,expected=stack.enter_context(frozen_environment(kind,scratch/kind))
                validate_environment(inspect_environment(python,env,kind),expected,__import__('check_python').DIRECT[kind])
                environments[kind]=(python,env)
                data[kind]=python_inventory(python,env,scratch/kind/'wheels')
            tool_python,tool_env=environments['tools']
            for kind,(python,env) in environments.items():
                output=scratch/(kind+'-sbom.json')
                import check_python
                check_python.run([tool_python,'-m','cyclonedx_py','environment',python,'--gather-license-texts','--validate','--sv','1.6','--of','JSON','-o',output],env=tool_env)
                raw=output.read_text();bom=json.loads(raw);counts[kind]=reconcile(data[kind],bom,'python')
                data[kind+'-raw']=raw
            # Validate npm's standard raw SBOM with the maintained CycloneDX validator.
            npm_path=scratch/'npm.json';npm_path.write_text(npm_raw)
            code='from pathlib import Path;import sys;from cyclonedx.validation.json import JsonStrictValidator;from cyclonedx.schema import SchemaVersion;v=JsonStrictValidator(SchemaVersion.V1_5 if sys.argv[2]=="1.5" else SchemaVersion.V1_6);e=v.validate_str(Path(sys.argv[1]).read_text());assert e is None,str(e)'
            schema_findings=[]
            try:
                check_python.run([tool_python,'-c',code,npm_path,json.loads(npm_raw)['specVersion']],env=tool_env)
            except ValueError as error:
                schema_findings.append({'artifact':'npm-sbom.json','status':'invalid raw standard output',
                    'diagnostic':str(error)[-7000:],'resolution':'pending; raw output retained unchanged'})
        provenance={'schema_version':1,'evidence_class':'local-synthetic','scope':'actual installed npm/runtime-Python/tool-Python only',
            'npm':npm,'python_runtime':data['runtime'],'python_tools':data['tools'],'not_installed_optional':absent,
            'native_and_images':'pending actual incorporated notices, image digests and complete closure review',
            'legal_acceptability':'unresolved; automation does not grant redistribution approval',
            'schema_validation_findings':schema_findings}
        output=ROOT/'docs/evidence/t02'
        (output/'npm-sbom.json').write_text(npm_raw)
        (output/'python-sbom.json').write_text(data['runtime-raw'])
        (output/'python-tools-sbom.json').write_text(data['tools-raw'])
        (output/'licences.json').write_text(json.dumps(provenance,indent=2)+'\n')
        runtime={'schema_version':1,'evidence_class':'candidate-evaluation-only','images':[],
            'actual_image_manifest_and_layers':'pending unbuilt images; no digest invented',
            'runtime_candidates':json.loads((ROOT/'docs/evidence/t02/runtime-review.json').read_text()),
            'native_incorporated_notices':'pending complete Node/Python/PostgreSQL/libpq/OpenSSL/systemd/Caddy/Podman/helper/backup closure review',
            'compatibility':'pending generator/build/off-host evidence'}
        (output/'runtime-image-inventory.json').write_text(json.dumps(runtime,indent=2)+'\n')
        suite=unittest.TestLoader().discover(str(ROOT/'tests'),pattern='test_inventory_artifacts.py');stream=io.StringIO();result=unittest.TextTestRunner(stream=stream).run(suite)
        require(result.testsRun>=4 and result.wasSuccessful() and not result.skipped,'inventory controls failed: '+stream.getvalue())
    print(json.dumps({'installed_unique_components':{'npm':npm_count,**counts},'not_installed_optional':len(absent)}))
    print(f'INVENTORY_LOCAL_RECORDED checks={npm_count+sum(counts.values())} tests={result.testsRun} duration_seconds={time.monotonic()-start:.3f}')
    print('PENDING_FULL_INVENTORY: raw npm schema finding, native/OCI closure/notice/compatibility and legal findings unresolved')
    if schema_findings:raise SystemExit(2)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--local',action='store_true');a=p.parse_args()
    require(a.local,'PENDING_FULL_INVENTORY: complete native/image/notice coverage unavailable; use --local for explicitly scoped SBOM collection')
    local_inventory()

if __name__=='__main__':
    try:main()
    except (OSError,ValueError,subprocess.SubprocessError) as error:
        print('INVENTORY_FAIL: '+str(error),file=sys.stderr);raise SystemExit(1)
