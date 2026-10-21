#!/usr/bin/env python3
"""Two independent actual public/backend builds; OCI comparison remains separate."""
import argparse
from contextlib import contextmanager
import secrets
import datetime
import hashlib
import io
import json
import os
import shutil
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import time
import unittest
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
from check_frontend import manifest,copy_inputs,safe_env,command,scan_output
from check_python import require,frozen_environment


def file_identity(path,name):
    return {'path':name,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}


def payload_manifest(root):
    files=sorted(root.rglob('*'))
    require(len(files)<2000,'bounded release payload required')
    result=[]
    for path in files:
        require(not path.is_symlink(),'payload symlink forbidden')
        if path.is_file():result.append(file_identity(path,path.relative_to(root).as_posix()))
    require(bool(result),'empty release payload')
    return result


def compare(left,right):
    require(bool(left) and bool(right),'empty build manifest')
    require(left==right,'actual release payload byte/path/size mismatch: '+json.dumps({'left':left,'right':right}))
    return True


def backend_package(root,epoch):
    source=root/'backend';source.mkdir()
    for path in sorted((ROOT/'backend').rglob('*')):
        relative=path.relative_to(ROOT/'backend')
        if not (path.suffix=='.py' or (relative.parts[0]=='requirements' and path.suffix in {'.txt','.in'})):continue
        require(path.is_file() and not path.is_symlink() and path.stat().st_size<1048576,'unsafe backend source input')
        target=source/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(path.read_bytes())
    output=root/'payload/backend.tar';output.parent.mkdir(exist_ok=True)
    # Packaging contract fixes metadata only; source and generated payload bytes are never normalized.
    with tarfile.open(output,'w',format=tarfile.PAX_FORMAT) as archive:
        for path in sorted(source.rglob('*')):
            if not path.is_file():continue
            info=tarfile.TarInfo(path.relative_to(source).as_posix());content=path.read_bytes()
            info.size=len(content);info.mtime=epoch;info.mode=0o644;info.uid=info.gid=0;info.uname=info.gname=''
            archive.addfile(info,io.BytesIO(content))
    require(output.stat().st_size>10240,'nonempty backend payload required')
    return payload_manifest(source)


CANONICAL_BUILD_PATH=Path('/tmp/shop-reproducible-build')


@contextmanager
def canonical_build_root():
    """Own an empty target; bind only inside each new private mount namespace."""
    root=CANONICAL_BUILD_PATH
    root.mkdir(mode=0o700,exist_ok=False) # Existing/unknown target is never reused.
    marker=root/'.owned';token=secrets.token_hex(32)
    marker.write_text(token);marker.chmod(0o600)
    try:
        yield root
    finally:
        require(not root.is_symlink() and marker.is_file() and not marker.is_symlink()
                and marker.read_text()==token and set(root.iterdir())=={marker},'canonical target ownership changed; cleanup refused')
        require(not any(line.split(' - ',1)[0].split()[4]==str(root) for line in Path('/proc/self/mountinfo').read_text().splitlines()),'parent mount namespace unexpectedly changed')
        marker.unlink();root.rmdir()


def build(root,epoch,canonical):
    project=root/'frontend'
    copy_inputs(ROOT/'frontend',project,manifest(json.loads((ROOT/'frontend/build-inputs.json').read_text())))
    env=safe_env(root);env.update(SOURCE_DATE_EPOCH=str(epoch),TZ='UTC',LC_ALL='C')
    command(['npm','ci','--no-audit','--no-fund'],project,env)
    parent_namespace=os.readlink('/proc/self/ns/mnt')
    isolated='test "$(readlink /proc/self/ns/mnt)" != "$3" && mount --bind "$1" "$2" && cd "$2" && exec npm run build'
    command(['unshare','--mount','--net','--propagation','private','--','bash','-c',isolated,'shop-build',project,canonical,parent_namespace],project,env)
    scan_output(project/'dist')
    output=root/'payload';output.mkdir()
    public=output/'public';public.mkdir()
    for path in sorted((project/'dist').rglob('*')):
        require(not path.is_symlink(),'build symlink forbidden')
        if path.is_file():
            target=public/path.relative_to(project/'dist');target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(path.read_bytes())
    backend=backend_package(root,epoch)
    installed=json.loads((project/'node_modules/.package-lock.json').read_text())['packages']
    graph=[{'path':name,'version':value['version'],'integrity':value['integrity']} for name,value in sorted(installed.items())]
    return {'payload':payload_manifest(output),'backend_files':backend,'installed_graph':graph}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--local',action='store_true');parser.add_argument('--record-evidence',action='store_true');args=parser.parse_args()
    require(args.local,'PENDING_OCI_REPRODUCIBILITY: unbuilt/unqualified image payload/config comparison; use --local for public/backend scope')
    from check import tool_identities
    identities=tool_identities()
    started=time.monotonic();utc=datetime.datetime.now(datetime.timezone.utc).isoformat()
    epoch=int(subprocess.check_output(['git','show','-s','--format=%ct','HEAD'],cwd=ROOT,text=True,timeout=5))
    owned=ROOT/'.scratch';owned.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='repro-',dir=owned) as directory:
        scratch=Path(directory);results=[]
        with canonical_build_root() as canonical:
            for number in (1,2):
                target=scratch/str(number);target.mkdir();results.append(build(target,epoch,canonical))
        try:
            compare(results[0]['payload'],results[1]['payload']);compare(results[0]['backend_files'],results[1]['backend_files']);compare(results[0]['installed_graph'],results[1]['installed_graph'])
        except ValueError:
            failure=Path(tempfile.mkdtemp(prefix='repro-failure-',dir=owned))
            for number in (1,2):shutil.copytree(scratch/str(number)/'payload',failure/str(number))
            (failure/'manifests.json').write_text(json.dumps(results,indent=2)+'\n')
            print('REPRODUCIBILITY_DIAGNOSTICS '+str(failure),flush=True)
            raise
        suite=unittest.TestLoader().discover(str(ROOT/'tests'),pattern='test_reproducibility.py');stream=io.StringIO();result=unittest.TextTestRunner(stream=stream).run(suite)
        require(result.wasSuccessful() and result.testsRun>=3 and not result.skipped,'reproducibility controls failed: '+stream.getvalue())
        evidence={'schema_version':1,'scope':'public/backend only; OCI pending','evidence_class':'local-synthetic','build_count':2,
            'tool_identity':identities,'source_date_epoch':epoch,'canonical_build_path':str(CANONICAL_BUILD_PATH),'isolated_mount_namespaces':True,'locale':'C','timezone':'UTC','manifests':results,'oci_comparison':'pending unbuilt images'}
        if args.record_evidence:
            path=ROOT/'docs/evidence/t02/reproducibility.json';path.write_text(json.dumps(evidence,indent=2)+'\n')
            from check_contracts import artifact_record
            record=artifact_record([sys.executable,*sys.argv],{'checks':4,'tests':result.testsRun},utc,time.monotonic()-started)
            record['locks'] += [{'path':name,'sha256':hashlib.sha256((ROOT/name).read_bytes()).hexdigest()} for name in ('frontend/package-lock.json','ops/nixos/flake.lock')]
            record['artifacts']=[{'path':'docs/evidence/t02/reproducibility.json','sha256':hashlib.sha256(path.read_bytes()).hexdigest()},
                {'path':'scripts/check_reproducibility.py','sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}]
            path=ROOT/'docs/evidence/t02/manifest.json';path.write_text(json.dumps(record,indent=2)+'\n')
            with frozen_environment('tools',scratch/'tools') as (python,env,expected):
                code='import sys;sys.path.insert(0,sys.argv[1]);from check_contracts import ROOT,validator,load;validator(load(ROOT/"schemas/v1/artifact-manifest.schema.json")).validate(load(sys.argv[2]))'
                subprocess.run(['unshare','--net','--',str(python),'-c',code,str(ROOT/'scripts'),str(path)],env=env,cwd=ROOT,timeout=15,check=True)
            record['duration_seconds']=time.monotonic()-started
            path.write_text(json.dumps(record,indent=2)+'\n')
    print(f'REPRODUCIBILITY_LOCAL_PASS checks=4 tests={result.testsRun} builds=2 duration_seconds={time.monotonic()-started:.3f}')
    print('PENDING_OCI_REPRODUCIBILITY: two public/backend payloads matched; no image/runtime/full-phase claim')

if __name__=='__main__':
    try:main()
    except (ValueError,OSError,subprocess.SubprocessError) as error:
        print('REPRODUCIBILITY_FAIL: '+str(error),file=sys.stderr);raise SystemExit(1)
