#!/usr/bin/env python3
"""Owned local offline initdb tests; no server startup or fault injection."""
import json
import os
from pathlib import Path
import pwd
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
import time
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
from check_python import require
from dev_postgres import run


def main():
    started=time.monotonic()
    parent=Path(os.environ.get('SHOP_TEST_SCRATCH',ROOT/'.scratch'))
    require(parent.is_dir() and not parent.is_symlink(),'owned scratch parent required')
    root=Path(tempfile.mkdtemp(prefix='shop-bootstrap-',dir=parent)).resolve()
    token=secrets.token_hex(32);(root/'owned').write_text(token)
    prefix=[]
    try:
        if os.geteuid()==0:
            identity=pwd.getpwnam('claude');require(identity.pw_uid>0,'existing unprivileged identity required')
            runner=shutil.which('runuser');require(runner is not None,'existing runuser required')
            prefix=[runner,'--preserve-environment','-u',identity.pw_name,'--']
            os.chown(root,identity.pw_uid,identity.pw_gid)
            os.chown(root/'owned',identity.pw_uid,identity.pw_gid)
        env={'PATH':os.defpath,'HOME':str(root),'LANG':'C','LC_ALL':'C','PYTHONDONTWRITEBYTECODE':'1',
             'SHOP_BOOTSTRAP_TEST_ROOT':str(root),'SHOP_POSTGRES_BIN':os.environ['SHOP_POSTGRES_BIN']}
        script="import sys,unittest;sys.dont_write_bytecode=True;s=unittest.TestLoader().discover('tests',pattern='test_bootstrap.py');r=unittest.TextTestRunner().run(s);sys.exit(0 if r.testsRun>=13 and r.wasSuccessful() and not r.skipped else 1)"
        result=run([*prefix,os.environ['SHOP_PYTHON'],'-I','-c',script],env=env,cwd=ROOT,timeout=60)
        count=re.search(r'Ran (\d+) tests?',result.stderr);require(count is not None,'missing positive actual test count')
        print(f'BOOTSTRAP_LOCAL_PASS checks=3 tests={int(count[1])} duration_seconds={time.monotonic()-started:.3f}')
        print('Actual isolated offline initdb and single-user catalog check only; production authorization/ZFS/mount/cgroup and container startup remain unqualified')
    finally:
        require(root.parent==parent.resolve() and root.name.startswith('shop-bootstrap-') and not root.is_symlink()
            and (root/'owned').is_file() and not (root/'owned').is_symlink() and (root/'owned').read_text()==token,
            'unsafe bootstrap fixture cleanup')
        shutil.rmtree(root)

if __name__=='__main__':
    try:main()
    except (ValueError,OSError,subprocess.SubprocessError) as error:
        if isinstance(error,subprocess.CalledProcessError):print(error.stdout+error.stderr,file=sys.stderr)
        print('BOOTSTRAP_LOCAL_FAIL: owned synthetic verification failed',file=sys.stderr)
        raise SystemExit(1) from None
