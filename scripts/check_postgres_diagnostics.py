#!/usr/bin/env python3
"""Owned synthetic console tests and one offline native PostgreSQL error."""
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
    start=time.monotonic();parent=Path(os.environ.get('SHOP_TEST_SCRATCH',ROOT/'.scratch'))
    require(parent.is_dir() and not parent.is_symlink(),'owned scratch required')
    root=Path(tempfile.mkdtemp(prefix='shop-diagnostics-',dir=parent)).resolve()
    token=secrets.token_hex(32);(root/'owned').write_text(token);prefix=[]
    try:
        if os.geteuid()==0:
            user=pwd.getpwnam('claude');require(user.pw_uid>0,'existing unprivileged identity required')
            runner=shutil.which('runuser');require(runner is not None,'existing runuser required')
            prefix=[runner,'--preserve-environment','-u',user.pw_name,'--']
            os.chown(root,user.pw_uid,user.pw_gid);os.chown(root/'owned',user.pw_uid,user.pw_gid)
        env={'PATH':os.defpath,'HOME':str(root),'LANG':'C','LC_ALL':'C','PYTHONDONTWRITEBYTECODE':'1',
             'SHOP_DIAGNOSTIC_TEST_ROOT':str(root),'SHOP_POSTGRES_BIN':os.environ['SHOP_POSTGRES_BIN'],'SHOP_PYTHON':os.environ['SHOP_PYTHON']}
        script="import sys,unittest;sys.dont_write_bytecode=True;s=unittest.TestLoader().discover('tests',pattern='test_postgres_diagnostics.py');r=unittest.TextTestRunner().run(s);sys.exit(0 if r.testsRun>=8 and r.wasSuccessful() and not r.skipped else 1)"
        result=run([*prefix,os.environ['SHOP_PYTHON'],'-I','-c',script],cwd=ROOT,env=env,timeout=60)
        count=re.search(r'Ran (\d+) tests?',result.stderr);require(count is not None,'required test count missing')
        print(f'POSTGRES_DIAGNOSTICS_PASS checks=3 tests={int(count[1])} duration_seconds={time.monotonic()-start:.3f}')
        print('Local console-stream privacy only; real container lifecycle/helper containment and other log paths pending')
    finally:
        require(root.parent==parent.resolve() and root.name.startswith('shop-diagnostics-') and not root.is_symlink()
            and not (root/'owned').is_symlink() and (root/'owned').read_text()==token,'unsafe fixture cleanup')
        shutil.rmtree(root)

if __name__=='__main__':
    try:main()
    except (ValueError,OSError,subprocess.SubprocessError) as error:
        if isinstance(error,subprocess.CalledProcessError):print(error.stdout+error.stderr,file=sys.stderr)
        print('POSTGRES_DIAGNOSTICS_FAIL: local verification failed',file=sys.stderr)
        raise SystemExit(1) from None
