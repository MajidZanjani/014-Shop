#!/usr/bin/env python3
"""Read-only startup guard. Never initializes, mounts, repairs or mutates a DB."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess

PARENT_QUOTA = 80 * 1024**3
DB_QUOTA = 50 * 1024**3
CATEGORIES = {'graphroot','postgres','tmp','logs','certificates','spool','volumes','backups'}


def require(condition):
    if not condition:
        raise ValueError('shop identity/storage/resource attestation failed; no startup permitted')


def validate_expected(value):
    require(type(value) is dict and set(value) == {'schema_version','evidence_class','machine_id_sha256',
        'uid','gid','parent_dataset','database_dataset','pg_system_identifier','paths'})
    require(value['schema_version'] == 1 and value['evidence_class'] in {'actual-offhost-runtime','actual-mx1-qualified'})
    require(isinstance(value['machine_id_sha256'],str) and re.fullmatch('[0-9a-f]{64}',value['machine_id_sha256']))
    require(type(value['uid']) is int and value['uid'] > 0 and type(value['gid']) is int and value['gid'] > 0)
    require(isinstance(value['paths'],dict) and set(value['paths']) == CATEGORIES)
    for category,path in value['paths'].items():
        require(path == '/srv/shop/' + ('containers/storage' if category == 'graphroot' else category))
    for key in ('parent_dataset','database_dataset'):
        require(isinstance(value[key],str) and re.fullmatch('[A-Za-z0-9_./:-]+',value[key]) and '..' not in value[key])
    require(value['database_dataset'].startswith(value['parent_dataset']+'/'))
    require(isinstance(value['pg_system_identifier'],str) and re.fullmatch('[0-9]{10,20}',value['pg_system_identifier']))
    return value


def validate_database_identity(expected,observed):
    """For explicit future mutation wrappers; no trust in ambient DSN defaults."""
    fields={'container_id','account_uid','system_identifier','pgdata','database','role','server_address','server_port'}
    require(isinstance(expected,dict) and set(expected)==fields and isinstance(observed,dict) and set(observed)==fields)
    require(all(value is not None and value != '' for value in expected.values()))
    require(type(expected['account_uid']) is int and expected['account_uid'] > 0)
    require(type(expected['server_port']) is int and 1 <= expected['server_port'] <= 65535)
    require(expected==observed and expected['pgdata']=='/var/lib/shop/postgres')
    require(isinstance(expected['container_id'],str) and re.fullmatch('[0-9a-f]{64}',expected['container_id']))
    return True


def capture(argv):
    result=subprocess.run(argv,env={'PATH':os.defpath,'LANG':'C','HOME':'/nonexistent'},
        capture_output=True,text=True,timeout=5,check=True)
    require(len(result.stdout)<32768)
    return result.stdout.strip()


def inspect(expected,zfs,pg_control):
    require(os.geteuid()==expected['uid'] and os.getegid()==expected['gid'])
    require(hashlib.sha256(Path('/etc/machine-id').read_bytes().strip()).hexdigest()==expected['machine_id_sha256'])
    for path in expected['paths'].values():
        item=Path(path)
        require(item.is_dir() and not item.is_symlink() and item.resolve()==item and item.stat().st_uid==expected['uid'])
    mounts={}
    for line in Path('/proc/self/mountinfo').read_text().splitlines():
        left,right=line.split(' - ',1);a,b=left.split(),right.split()
        mounts[a[4]]=(b[0],b[1])
    require(mounts.get('/srv/shop')==('zfs',expected['parent_dataset']))
    require(mounts.get('/srv/shop/postgres')==('zfs',expected['database_dataset']))
    for dataset,quota in [(expected['parent_dataset'],PARENT_QUOTA),(expected['database_dataset'],DB_QUOTA)]:
        require(capture([zfs,'get','-Hp','-o','value','quota',dataset])==str(quota))
    require(Path('/srv/shop/postgres/PG_VERSION').read_text().strip()=='18')
    control=capture([pg_control,'/srv/shop/postgres'])
    fields={a.strip():b.strip() for line in control.splitlines() if ':' in line for a,b in [line.split(':',1)]}
    require(fields.get('Database system identifier')==expected['pg_system_identifier'])
    require(fields.get('Data page checksum version')=='1')
    # The guard itself must already be under the bounded shop ancestor.
    cgroup=Path('/proc/self/cgroup').read_text().strip()
    require(cgroup.startswith('0::/user.slice/user-'+str(expected['uid'])+'.slice/'))
    ancestor=Path('/sys/fs/cgroup/user.slice/user-'+str(expected['uid'])+'.slice')
    require((ancestor/'memory.max').read_text().strip()==str(8*1024**3))
    require((ancestor/'memory.high').read_text().strip()==str(6*1024**3))
    cpu,period=map(int,(ancestor/'cpu.max').read_text().split())
    require(cpu==period*2 and (ancestor/'pids.max').read_text().strip()=='1024')
    return True


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected',type=Path,required=True);parser.add_argument('--zfs',required=True);parser.add_argument('--pg-control',required=True)
    args=parser.parse_args();path=args.expected
    require(path==Path('/srv/shop/control/expected.json') and path.resolve()==path)
    info=path.stat();require(stat.S_ISREG(info.st_mode) and info.st_uid==0 and not info.st_mode & 0o022 and info.st_size<32768)
    for executable in (args.zfs,args.pg_control):require(executable.startswith('/nix/store/') and Path(executable).is_file())
    inspect(validate_expected(json.loads(path.read_text())),args.zfs,args.pg_control)

if __name__=='__main__':
    try:main()
    except Exception:
        raise SystemExit('SHOP_STARTUP_DENIED: required current identity/storage/resource evidence unavailable') from None
