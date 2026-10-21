#!/usr/bin/env python3
"""Compose actual frontend/backend privacy controls, with synthetic inputs only."""
import io
import json
import os
from pathlib import Path
import sys
import time
import unittest
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
from check import positive_counts
from dev_postgres import run


def child_counts(output,marker):
    if marker not in output:raise ValueError('required boundary producer marker missing')
    return positive_counts(output)


def main():
    start=time.monotonic();checks=tests=0
    for argv,marker in [(['python3','scripts/check_frontend.py'],'FRONTEND_PASS'),
                        (['python3','scripts/check_backend.py','core-local'],'CORE_LOCAL_PASS')]:
        result=run(argv,cwd=ROOT,env=dict(os.environ),timeout=180)
        count,verified=child_counts(result.stdout+result.stderr,marker)
        tests+=count;checks+=verified
    suite=unittest.TestLoader().discover(str(ROOT/'tests'),pattern='test_boundaries.py')
    stream=io.StringIO();result=unittest.TextTestRunner(stream=stream).run(suite)
    if result.testsRun<3 or not result.wasSuccessful() or result.skipped:raise ValueError('boundary controls failed: '+stream.getvalue())
    print(f'BOUNDARIES_PASS checks={checks} tests={tests+result.testsRun} duration_seconds={time.monotonic()-start:.3f}')
    print('Local/synthetic privacy only; off-host runtime and human source-fidelity review pending')

if __name__=='__main__':main()
