#!/usr/bin/env python3
"""Candidate evaluation only; image build/runtime/host acceptance remain separate."""
import argparse
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


def run(args,timeout=60):
    return subprocess.run(args,cwd=ROOT,capture_output=True,text=True,timeout=timeout,check=True).stdout


def evaluate():
    start=time.monotonic()
    metadata=json.loads(run(['nix','eval','--json','./ops/nixos#deploymentMetadata.x86_64-linux']))
    if metadata['productionActivation'] is not False or len(metadata['imageDerivations'])!=4:raise ValueError('candidate metadata invalid')
    expr='let f = builtins.getFlake (toString ./ops/nixos); in import ./ops/nixos/tests/shop.nix { inherit (f.inputs) nixpkgs; shopModule = f.nixosModules.shop; }'
    fixture=json.loads(run(['nix','eval','--json','--impure','--expr',expr]))
    if not all(fixture['disabled'].values()):raise ValueError('default module changes protected scope')
    candidate=fixture['syntheticCandidate']
    failed=[x['message'] for x in candidate['assertions'] if not x['assertion']]
    if failed:raise ValueError('synthetic module assertions failed: '+str(failed))
    bounds=candidate['bounds']
    if any(bounds.get(k)!=v for k,v in {'CPUQuota':'200%','MemoryHigh':'6G','MemoryMax':'8G','TasksMax':1024}.items()):raise ValueError('aggregate resource contract invalid')
    if not candidate['automaticGlobalLingerUnchanged'] or not candidate['shopLingerUnmanagedByGlobalService']:
        raise ValueError('global linger policy changed or new shop enrolled into shared management')
    suite=unittest.TestLoader().discover(str(ROOT/'tests'),pattern='test_deployment.py');stream=io.StringIO()
    result=unittest.TextTestRunner(stream=stream).run(suite)
    if result.testsRun<4 or not result.wasSuccessful() or result.skipped:raise ValueError('guard tests failed: '+stream.getvalue())
    print(f'DEPLOYMENT_EVAL_PASS checks=9 tests={result.testsRun} duration_seconds={time.monotonic()-start:.3f}')
    print('Candidate evaluation only; unbuilt images, generator/runtime/bootstrap/review/off-host evidence pending')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('lane',choices=['deployment-eval','deployment-build','deployment-boot','deployment-profiles']);p.add_argument('--runner-authorization',type=Path);a=p.parse_args()
    if a.lane=='deployment-eval':evaluate();return
    if a.lane=='deployment-boot':
        from check_backend import runner_authorization
        runner_authorization(a.runner_authorization,action='owned-synthetic-rootless-lifecycle')
        raise ValueError('PENDING_RUNTIME_FIXTURES: off-host driver/bootstrap/images not yet qualified; no lifecycle pass')
    if a.lane=='deployment-build':raise ValueError('PENDING_EXACT_RUNTIME_REVIEW: candidate definitions evaluated only; exact image/transitive review and build resource qualification required')
    raise ValueError('deployment profile producer is pending 02-15')

if __name__=='__main__':
    try:main()
    except (ValueError,OSError,subprocess.SubprocessError) as error:
        print('DEPLOYMENT_FAIL: '+str(error),file=sys.stderr);raise SystemExit(1)
