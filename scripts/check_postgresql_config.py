#!/usr/bin/env python3
"""Native parser/single-user checks of a closed draft; no network service."""
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

# Explicit security properties, independent of the native parser/type tests.
REQUIRED={
 'data_directory':"'/var/lib/shop/postgres'",'hba_file':"'/var/lib/shop/config/pg_hba.conf'",
 'listen_addresses':"''",'port':'5432','unix_socket_directories':"'/tmp'",'unix_socket_permissions':'0700',
 'password_encryption':"'scram-sha-256'",'fsync':'on','synchronous_commit':'on','full_page_writes':'on',
 'wal_level':'replica','archive_mode':'on','archive_timeout':"'300s'",'archive_command':"'exit 1'",'archive_library':"''",
 'logging_collector':'off','log_statement':"'none'",'log_min_error_statement':"'panic'",'log_error_verbosity':"'terse'",
 'log_parameter_max_length':'0','log_parameter_max_length_on_error':'0','log_min_duration_statement':'-1',
 'log_min_duration_sample':'-1','log_duration':'off','log_connections':'off','log_disconnections':'off',
 'log_hostname':'off','log_lock_waits':'off','log_temp_files':'-1','shared_preload_libraries':"''"}


def validate_candidate(config,hba):
    values={}
    for line in config.splitlines():
        if not line.strip() or line.lstrip().startswith('#'):continue
        match=re.fullmatch(r'([a-z_]+)\s*=\s*(.+)',line)
        require(match is not None,'unsupported candidate config directive')
        key,value=match.groups();require(key not in values,'duplicate candidate setting')
        values[key]=value
    extras={'superuser_reserved_connections':'2','reserved_connections':'1','wal_compression':'on',
        'max_wal_size':"'1GB'",'min_wal_size':"'80MB'",'log_destination':"'stderr'",'log_line_prefix':"'%m [%p] %e '"}
    resources={'max_connections','max_worker_processes','shared_buffers','work_mem','maintenance_work_mem','max_parallel_workers','max_parallel_workers_per_gather'}
    require(set(values)==set(REQUIRED)|set(extras)|resources,'unreviewed candidate setting')
    require(all(values.get(key)==value for key,value in (REQUIRED|extras).items()),'closed security/durability/logging contract changed')
    require(0<int(values['max_connections'])<=20 and 0<int(values['max_worker_processes'])<=2
        and values['shared_buffers']=="'256MB'" and values['work_mem']=="'4MB'"
        and values['maintenance_work_mem']=="'64MB'" and values['max_parallel_workers']=='0'
        and values['max_parallel_workers_per_gather']=='0','unqualified resource expansion')
    require(not any(key.startswith('include') for key in values),'external config inclusion forbidden')
    rows=[line.split() for line in hba.splitlines() if line.strip() and not line.lstrip().startswith('#')]
    require(rows==[['local','all','all','reject'],['local','replication','all','reject'],
        ['host','all','all','0.0.0.0/0','reject'],['host','all','all','::/0','reject'],
        ['host','replication','all','0.0.0.0/0','reject'],['host','replication','all','::/0','reject']],
        'candidate must reject every connection')
    return values


def main():
    start=time.monotonic();parent=Path(os.environ.get('SHOP_TEST_SCRATCH',ROOT/'.scratch'))
    require(parent.is_dir() and not parent.is_symlink(),'owned scratch parent required')
    root=Path(tempfile.mkdtemp(prefix='shop-pg-config-',dir=parent)).resolve()
    token=secrets.token_hex(32);(root/'owned').write_text(token);prefix=[]
    try:
        if os.geteuid()==0:
            user=pwd.getpwnam('claude');require(user.pw_uid>0,'existing nonroot identity required')
            runner=shutil.which('runuser');require(runner is not None,'existing runuser required')
            prefix=[runner,'--preserve-environment','-u',user.pw_name,'--']
            os.chown(root,user.pw_uid,user.pw_gid);os.chown(root/'owned',user.pw_uid,user.pw_gid)
        env={'PATH':os.defpath,'HOME':str(root),'LANG':'C','LC_ALL':'C','PYTHONDONTWRITEBYTECODE':'1',
             'SHOP_PG_CONFIG_TEST_ROOT':str(root),'SHOP_POSTGRES_BIN':os.environ['SHOP_POSTGRES_BIN']}
        script="import sys,unittest;sys.dont_write_bytecode=True;s=unittest.TestLoader().discover('tests',pattern='test_postgresql_config.py');r=unittest.TextTestRunner().run(s);sys.exit(0 if r.testsRun>=7 and r.wasSuccessful() and not r.skipped else 1)"
        result=run([*prefix,os.environ['SHOP_PYTHON'],'-I','-c',script],cwd=ROOT,env=env,timeout=60)
        count=re.search(r'Ran (\d+) tests?',result.stderr);require(count is not None,'positive native test count required')
        print(f'POSTGRESQL_CONFIG_PASS checks=3 tests={int(count[1])} duration_seconds={time.monotonic()-start:.3f}')
        print('Closed draft and local single-user parser evidence only; no container/network/archiver/production qualification')
    finally:
        require(root.parent==parent.resolve() and root.name.startswith('shop-pg-config-') and not root.is_symlink()
                and not (root/'owned').is_symlink() and (root/'owned').read_text()==token,'unsafe fixture cleanup')
        shutil.rmtree(root)

if __name__=='__main__':
    try:main()
    except (ValueError,OSError,subprocess.SubprocessError) as error:
        if isinstance(error,subprocess.CalledProcessError):print(error.stdout+error.stderr,file=sys.stderr)
        print('POSTGRESQL_CONFIG_FAIL: closed-draft verification failed',file=sys.stderr)
        raise SystemExit(1) from None
