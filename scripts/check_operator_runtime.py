#!/usr/bin/env python3
"""Build and exercise only the standalone inspection runtime; no host install."""
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import unittest
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
from check_python import require,read_lock
from check_database_tools import check_artifact,unique_fields

ERROR=b'{"event":"operator.inspection_denied"}\n'
HELP=b'Prepared read-only commands: inspect (private artifact FD0, credential FD3); validate-records (private candidate FD0). Runtime qualification pending.\n'
FIELDS={'package','executable','driver','source','runtimeSite','python','libpq',
        'libc','pythonVersion','psycopgVersion','libpqVersion','readOnly','installed','runtimeQualified','productionActivation'}


def validate_metadata(value):
    require(type(value) is dict and set(value)==FIELDS,'closed operator metadata required')
    require(value['readOnly'] is True and value['installed'] is False
            and value['runtimeQualified'] is False and value['productionActivation'] is False,
            'installation and qualification must remain pending')
    require(value['pythonVersion']=='3.13.16' and value['psycopgVersion']=='3.3.6'
            and type(value['libpqVersion']) is int and value['libpqVersion']==180006,
            'exact existing native/Psycopg pins required')
    for key in ('package','executable','driver','source','runtimeSite','python','libpq','libc'):
        require(type(value[key]) is str and value[key].startswith('/nix/store/')
                and '..' not in value[key].split('/'),'immutable runtime path required')
    require(value['executable']==value['package']+'/bin/shop-operator-inspect'
            and value['python'].endswith('/bin/python3') and value['libpq'].endswith('/lib/libpq.so.5')
            and value['libc'].endswith('/lib/libc.so.6'),
            'closed launcher and library paths required')
    return value


def main():
    start=time.monotonic()
    built=subprocess.run(['nix','build','--no-link','--print-out-paths','--max-jobs','1','--cores','4',
        './ops/nixos#shop-operator-inspect','./ops/nixos#checks.x86_64-linux.operator-startup-denial'],
        cwd=ROOT,capture_output=True,text=True,check=True,timeout=100)
    paths=set(built.stdout.strip().splitlines());require(len(paths)==2,'actual main and failure-control builds required')
    evaluated=subprocess.run(['nix','eval','--json','./ops/nixos#deploymentMetadata.x86_64-linux.operatorInspection'],
        cwd=ROOT,capture_output=True,text=True,check=True,timeout=30)
    metadata=validate_metadata(json.loads(evaluated.stdout,object_pairs_hook=unique_fields))
    failure=subprocess.run(['nix','eval','--raw','./ops/nixos#checks.x86_64-linux.operator-startup-denial.outPath'],
        cwd=ROOT,capture_output=True,text=True,check=True,timeout=30).stdout
    require(paths=={metadata['package'],failure},'built output/metadata mismatch')
    check_artifact(Path(metadata['source']))
    lock=read_lock(ROOT/'backend/requirements/runtime-linux-py313.txt')
    require(lock['psycopg']['version']=='3.3.6' and
        'a1db9f7148b06a28606767efaca51fa6f9398c5c0a3810519be69d7000bdb631' in lock['psycopg']['hashes'],
        'operator wheel must remain an exact subset of existing runtime lock')
    previous={key:os.environ.get(key) for key in ('SHOP_OPERATOR_EXECUTABLE','SHOP_OPERATOR_FAILURE_EXECUTABLE')}
    os.environ['SHOP_OPERATOR_EXECUTABLE']=metadata['executable']
    os.environ['SHOP_OPERATOR_FAILURE_EXECUTABLE']=failure+'/bin/shop-operator-inspect'
    try:
        suite=unittest.TestLoader().discover(str(ROOT/'tests'),pattern='test_operator_runtime.py')
        stream=io.StringIO();result=unittest.TextTestRunner(stream=stream).run(suite)
        require(result.testsRun>=10 and result.wasSuccessful() and not result.skipped,
                'operator native startup/process controls failed: '+stream.getvalue())
    finally:
        for key,value in previous.items():
            if value is None:os.environ.pop(key,None)
            else:os.environ[key]=value
    print(f'OPERATOR_RUNTIME_PASS checks=4 tests={result.testsRun} duration_seconds={time.monotonic()-start:.3f}')
    print('Actual standalone startup/denial and offline record validation only; no host install, positive DB transport or runtime qualification')

if __name__=='__main__':
    try:main()
    except (ValueError,OSError,subprocess.SubprocessError):
        print('OPERATOR_RUNTIME_FAIL: launcher build/startup verification failed',file=sys.stderr)
        raise SystemExit(1) from None
