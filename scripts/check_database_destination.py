#!/usr/bin/env python3
"""Ordinary local tests of same-connection SQL guard, never runtime fault tests."""
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
from check_python import frozen_environment, require
import dev_postgres


def main():
    start=time.monotonic()
    parent=Path(os.environ.get('SHOP_TEST_SCRATCH', ROOT/'.scratch'))
    require(parent.is_dir() and not parent.is_symlink(), 'owned scratch parent required')
    parent=parent.resolve()
    require(len(str(parent))+50<108, 'short owned scratch path required')
    with tempfile.TemporaryDirectory(prefix='destination-',dir=parent) as directory:
        with frozen_environment('runtime',Path(directory)/'runtime') as (python,env,expected):
            env['SHOP_POSTGRES_BIN']=os.environ['SHOP_POSTGRES_BIN']
            env['PYTHONPATH']=str(ROOT/'scripts')
            env['SHOP_TEST_SCRATCH']=str(parent)
            script = '''import os, pathlib, sys, unittest
sys.dont_write_bytecode=True
import dev_postgres
dev_postgres.SCRATCH_PARENT=pathlib.Path(os.environ['SHOP_TEST_SCRATCH'])
suite=unittest.TestLoader().discover('tests',pattern='test_database_destination.py')
suite.addTests(unittest.TestLoader().discover('tests',pattern='test_operator_inspect.py'))
suite.addTests(unittest.TestLoader().discover('tests',pattern='test_record_bundle.py'))
suite.addTests(unittest.TestLoader().discover('tests',pattern='test_operator_schema.py'))
suite.addTests(unittest.TestLoader().discover('tests',pattern='test_control_admission.py'))
suite.addTests(unittest.TestLoader().discover('tests',pattern='test_generation_custody.py'))
suite.addTests(unittest.TestLoader().discover('tests',pattern='test_publication.py'))
r=unittest.TextTestRunner(verbosity=2).run(suite)
if r.testsRun < 153 or r.skipped or not r.wasSuccessful(): sys.exit(1)
'''
            result=dev_postgres.run([str(python),'-c',script],env=env,cwd=ROOT,timeout=60)
            match=re.search(r'Ran (\d+) tests?', result.stderr)
            require(match is not None, 'missing actual SQL test count')
    print(f'DATABASE_DESTINATION_PASS checks=3 tests={int(match[1])} duration_seconds={time.monotonic()-start:.3f}')
    print('Local synthetic SQL evidence only; PGDATA comparison adapted to owned scratch path; no container/rootless/storage qualification or application integration')

if __name__=='__main__':
    try:main()
    except (ValueError,OSError,subprocess.SubprocessError) as error:
        # Test fixtures contain synthetic values only; avoid forwarding arbitrary SQL diagnostics.
        if isinstance(error,subprocess.CalledProcessError):print(error.stdout + error.stderr,file=sys.stderr)
        print('DATABASE_DESTINATION_FAIL: local verification failed',file=sys.stderr)
        raise SystemExit(1) from None
