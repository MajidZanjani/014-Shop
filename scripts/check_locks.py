#!/usr/bin/env python3
"""Actual installer clean controls and bounded offline hash/lock rejection tests."""
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.request
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
from check_frontend import manifest,copy_inputs,safe_env,command
from check_python import frozen_environment,require,inspect_environment,validate_environment,DIRECT


def reject(result,diagnostics):
    text=result.stdout+result.stderr
    require(result.returncode!=0 and any(item.lower() in text.lower() for item in diagnostics),'installer did not reject for expected hash/lock reason '+str(diagnostics)+': '+text[-2500:])
    require(not any(item in text for item in ('ENOTCACHED','ENETUNREACH','CERTIFICATE_VERIFY_FAILED','No matching distribution found')),'network/missing artifact is not a valid negative control')


def invoke(args,cwd,env):return subprocess.run(list(map(str,args)),cwd=cwd,env=env,capture_output=True,text=True,timeout=45)


def npm_controls(scratch):
    project=scratch/'frontend';copy_inputs(ROOT/'frontend',project,manifest(json.loads((ROOT/'frontend/build-inputs.json').read_text())))
    env=safe_env(scratch)
    command(['npm','ci','--no-audit','--no-fund'],project,env)
    # Populate metadata cache, then require the actual offline lock-sync diagnostic.
    command(['npm','view','react@19.3.1','version'],project,env)
    package=project/'package.json';value=json.loads(package.read_text());value['dependencies']['react']='19.3.0';package.write_text(json.dumps(value))
    reject(invoke(['npm','ci','--offline','--ignore-scripts','--no-audit','--no-fund'],project,env),['EUSAGE','package.json and package-lock.json'])
    locked=json.loads((ROOT/'frontend/package-lock.json').read_text())['packages']['node_modules/react']
    fixture=scratch/'npm-artifact';fixture.mkdir()
    with urllib.request.urlopen(locked['resolved'],timeout=15) as response:artifact=response.read(10485761)
    require(len(artifact)<10485761 and 'sha512-'+base64.b64encode(hashlib.sha512(artifact).digest()).decode()==locked['integrity'],'qualified React archive identity mismatch')
    archive=fixture/'react.tgz';archive.write_bytes(artifact)
    (fixture/'package.json').write_text(json.dumps({'name':'synthetic-lock-control','version':'1.0.0','private':True,'dependencies':{'react':'file:./react.tgz'}}))
    command(['npm','install','--package-lock-only','--offline','--ignore-scripts','--no-audit','--no-fund'],fixture,env)
    command(['npm','ci','--offline','--ignore-scripts','--no-audit','--no-fund'],fixture,env)
    lock=fixture/'package-lock.json';original=lock.read_text()
    value=json.loads(original);value['packages']['node_modules/react']['integrity']='sha512-'+base64.b64encode(b'\x00'*64).decode();lock.write_text(json.dumps(value))
    fresh=dict(env,NPM_CONFIG_CACHE=str(scratch/'negative-cache-1'))
    reject(invoke(['npm','ci','--offline','--ignore-scripts','--no-audit','--no-fund'],fixture,fresh),['EINTEGRITY'])
    lock.write_text(original);bad=bytearray(artifact);require(bad[:2]==b'\x1f\x8b' and not bad[3]&2,'known gzip header without header CRC required');bad[4]^=1;archive.write_bytes(bad)
    fresh=dict(env,NPM_CONFIG_CACHE=str(scratch/'negative-cache-2'))
    reject(invoke(['npm','ci','--offline','--ignore-scripts','--no-audit','--no-fund'],fixture,fresh),['EINTEGRITY'])
    return 3


def pip_controls(scratch):
    with frozen_environment('runtime',scratch/'runtime') as (python,env,expected):
        validate_environment(inspect_environment(python,env,'runtime'),expected,DIRECT['runtime'])
        wheels=scratch/'runtime/wheels';original=ROOT/'backend/requirements/runtime-linux-py313.txt'
        # Fresh destinations force actual archive verification; no installed/cache shortcut.
        def download(lock,source,name):
            return invoke([sys.executable,'-I','-m','pip','download','--no-index','--no-cache-dir','--only-binary=:all:',
                '--find-links',source,'--require-hashes','-r',lock,'--dest',scratch/name],ROOT,env)
        clean=download(original,wheels,'pip-clean');require(clean.returncode==0,'pip local positive control failed')
        wrong=scratch/'wrong-hash.txt';wrong.write_text(re.sub(r'--hash=sha256:[0-9a-f]{64}','--hash=sha256:'+'0'*64,original.read_text()))
        reject(download(wrong,wheels,'pip-negative-hash'),['THESE PACKAGES DO NOT MATCH THE HASHES'])
        missing=scratch/'missing-hash.txt';missing.write_text(re.sub(r'\s+--hash=sha256:[0-9a-f]{64}','',original.read_text()).replace('\\\n','\n'))
        reject(download(missing,wheels,'pip-negative-missing'),['Hashes are required in --require-hashes mode'])
        corrupt=scratch/'corrupt-wheels';shutil.copytree(wheels,corrupt)
        chosen=sorted(corrupt.glob('*.whl'))[0];data=bytearray(chosen.read_bytes());require(data[:4]==b'PK\x03\x04','known ZIP local header required');data[10]^=1;chosen.write_bytes(data)
        reject(download(original,corrupt,'pip-negative-archive'),['THESE PACKAGES DO NOT MATCH THE HASHES'])
    return 3


def main():
    from check import tool_identities
    tool_identities()
    start=time.monotonic();owned=ROOT/'.scratch';owned.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='locks-',dir=owned) as directory:
        scratch=Path(directory);tests=npm_controls(scratch)+pip_controls(scratch)
        suite=unittest.TestLoader().discover(str(ROOT/'tests'),pattern='test_lock_enforcement.py');stream=io.StringIO();result=unittest.TextTestRunner(stream=stream).run(suite)
        require(result.wasSuccessful() and result.testsRun>=2 and not result.skipped,'lock diagnostic controls failed: '+stream.getvalue())
    print(f'LOCKS_PASS checks=3 tests={tests+result.testsRun} duration_seconds={time.monotonic()-start:.3f}')

if __name__=='__main__':
    try:main()
    except (ValueError,OSError,subprocess.SubprocessError) as error:
        print('LOCKS_FAIL: '+str(error),file=sys.stderr);raise SystemExit(1)
