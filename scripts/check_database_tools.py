#!/usr/bin/env python3
"""Build/check only the inert source bundle; no images, runtime or deployment."""
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
import unittest
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
from check_python import frozen_environment, require

MODULES=('guard','control','database','process_probe','schema_authorization',
         'ledger_bootstrap','schema_reconciliation','operator_inspect','record_bundle')
FILES={**{f'libexec/shop/database/{name}.py':f'ops/runtime/{name}.py' for name in MODULES},
       'share/shop/schema-ledger.sql':'ops/postgresql/schema-ledger.sql'}
MANIFEST='share/shop/database-tools.json'


def unique_fields(pairs):
    value={}
    for key,item in pairs:
        require(key not in value,'duplicate manifest field')
        value[key]=item
    return value


def decode_manifest(data):
    require(type(data) is bytes and 0<len(data)<=32768,'bounded manifest required')
    value=json.loads(data,object_pairs_hook=unique_fields)
    require(type(value) is dict and set(value)=={'schema_version','artifact_kind',
        'executable','runtime_qualified','production_activation','files'},'closed manifest required')
    require(type(value['schema_version']) is int and value['schema_version']==1
        and value['artifact_kind']=='inert-database-tools-source'
        and value['executable'] is False and value['runtime_qualified'] is False
        and value['production_activation'] is False,'inert manifest required')
    require(type(value['files']) is dict and set(value['files'])==set(FILES),'exact source set required')
    require(all(type(item) is str and re.fullmatch('[a-f0-9]{64}',item)
                for item in value['files'].values()),'exact source hashes required')
    return value


def check_artifact(artifact):
    require(artifact.is_dir() and str(artifact).startswith('/nix/store/'),'immutable artifact required')
    files={str(path.relative_to(artifact)) for path in artifact.rglob('*') if not path.is_dir()}
    require(files==set(FILES)|{MANIFEST},'unexpected artifact content')
    manifest=decode_manifest((artifact/MANIFEST).read_bytes())
    for name,source in FILES.items():
        path=artifact/name
        require(path.is_file() and str(path.resolve()).startswith('/nix/store/')
                and not path.stat().st_mode & 0o333,'non-executable immutable source required')
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        require(digest==manifest['files'][name]
                and digest==hashlib.sha256((ROOT/source).read_bytes()).hexdigest(),'artifact source mismatch')
    return manifest


def main():
    start=time.monotonic()
    result=subprocess.run(['nix','build','--no-link','--print-out-paths','--max-jobs','1','--cores','4',
        './ops/nixos#shop-database-tools-source'],cwd=ROOT,capture_output=True,text=True,check=True,timeout=90)
    paths=result.stdout.strip().splitlines()
    require(len(paths)==1,'one built source artifact required')
    artifact=Path(paths[0]);check_artifact(artifact)
    evaluated=subprocess.run(['nix','eval','--json',
        './ops/nixos#deploymentMetadata.x86_64-linux.databaseTools'],cwd=ROOT,
        capture_output=True,text=True,check=True,timeout=30)
    require(json.loads(evaluated.stdout,object_pairs_hook=unique_fields)=={
        'source':str(artifact),'manifest':str(artifact/MANIFEST),
        'executable':False,'runtimeQualified':False,'productionActivation':False},
        'source metadata must name the actual inert artifact')
    references=subprocess.run(['nix-store','--query','--references',str(artifact)],
        cwd=ROOT,capture_output=True,text=True,check=True,timeout=15)
    require(set(references.stdout.splitlines())=={str((artifact/name).resolve())
                for name in set(FILES)|{MANIFEST}},'unexpected source-bundle closure reference')
    parent=Path(os.environ.get('SHOP_TEST_SCRATCH',ROOT/'.scratch'))
    require(parent.is_dir() and not parent.is_symlink(),'owned scratch parent required')
    with tempfile.TemporaryDirectory(prefix='database-tools-',dir=parent) as directory:
        with frozen_environment('runtime',Path(directory)/'runtime') as (python,env,expected):
            program = """import importlib,json,pathlib,sys
sys.dont_write_bytecode=True
root=pathlib.Path(sys.argv[1]);sys.path.insert(0,str(root/'libexec/shop/database'))
from unittest.mock import patch
import psycopg
with patch.object(psycopg,'connect',side_effect=AssertionError('no import-time connection')):
    import control
    with patch.object(control,'load_control',side_effect=AssertionError('no import-time control read')):
        for name in sys.argv[2:]:
            module=importlib.import_module(name)
            assert pathlib.Path(module.__file__).resolve()==(root/'libexec/shop/database'/ (name+'.py')).resolve()
import hashlib,ledger_bootstrap
assert ledger_bootstrap.ARTIFACT_SHA256==hashlib.sha256((root/'share/shop/schema-ledger.sql').read_bytes()).hexdigest()
assert sys.flags.isolated==1
print('DATABASE_TOOLS_IMPORT_PASS')
"""
            imported=subprocess.run([str(python),'-I','-c',program,str(artifact),*MODULES],
                env=env,capture_output=True,text=True,check=True,timeout=15)
            require(imported.stdout.strip()=='DATABASE_TOOLS_IMPORT_PASS','actual isolated import required')
            command="import sys,runpy;sys.dont_write_bytecode=True;sys.path.insert(0,sys.argv.pop(1));runpy.run_module('operator_inspect',run_name='__main__')"
            help_result=subprocess.run([str(python),'-I','-c',command,str(artifact/'libexec/shop/database'),'--help'],
                env=env,capture_output=True,timeout=10)
            require(help_result.returncode==0 and help_result.stdout.startswith(b'Prepared read-only commands:')
                and not help_result.stderr,'actual packaged help required')
            denied=subprocess.run([str(python),'-I','-c',command,str(artifact/'libexec/shop/database'),'apply'],
                env=env,capture_output=True,timeout=10)
            require(denied.returncode==2 and not denied.stdout
                and denied.stderr==b'{"event":"operator.inspection_denied"}\n','packaged mutation command must be absent')
    suite=unittest.TestLoader().discover(str(ROOT/'tests'),pattern='test_database_tools.py')
    stream=io.StringIO();tests=unittest.TextTestRunner(stream=stream).run(suite)
    require(tests.testsRun>=5 and tests.wasSuccessful() and not tests.skipped,'manifest controls failed')
    print(f'DATABASE_TOOLS_PASS checks=6 tests={tests.testsRun} duration_seconds={time.monotonic()-start:.3f}')
    print('Actual source build/import and packaged help/denial only; host installation/positive transport/runtime qualification pending')

if __name__=='__main__':
    try:main()
    except (ValueError,OSError,subprocess.SubprocessError):
        print('DATABASE_TOOLS_FAIL: source build/import verification failed',file=sys.stderr)
        raise SystemExit(1) from None
