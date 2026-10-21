"""Explicit one-use offline cluster initialization; never starts a DB server.

No operation runs merely by importing this module. Actual execution requires a
separately provisioned root-owned action authorization and an explicit --apply.
"""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import stat
import subprocess
from control import load_control
from guard import capture, inspect_storage, require, validate_storage_expected

ATTEMPT='bootstrap-attempt.json'


def validate_record(value):
    require(type(value) is dict and set(value) == {'schema_version','storage','action',
        'authorization_id','expires_at','postgres_bin','initdb_sha256'})
    require(type(value['schema_version']) is int and value['schema_version']==1)
    validate_storage_expected(value['storage'])
    require(value['action']=='initialize-new-shop-cluster')
    require(isinstance(value['authorization_id'],str) and re.fullmatch('[0-9a-f]{32}',value['authorization_id']))
    require(isinstance(value['expires_at'],str) and re.fullmatch(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ',value['expires_at']))
    require(datetime.strptime(value['expires_at'],'%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)>datetime.now(timezone.utc))
    require(isinstance(value['postgres_bin'],str) and re.fullmatch(r'/nix/store/[a-z0-9]{32}-[^/]+/bin',value['postgres_bin']))
    require(isinstance(value['initdb_sha256'],str) and re.fullmatch('[0-9a-f]{64}',value['initdb_sha256']))
    return value


def directory(path):
    path=Path(path)
    require(path.is_absolute() and path.resolve()==path)
    fd=os.open(path,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
    try:
        info=os.fstat(fd)
        require(info.st_uid==os.geteuid() and os.geteuid()>0 and not info.st_mode & 0o077)
        return fd
    except BaseException:
        os.close(fd);raise


def run_tool(argv,timeout=60):
    # No credentials/ambient PGDATA, connection service or library overrides.
    env={'PATH':os.defpath,'HOME':'/nonexistent','LANG':'C','LC_ALL':'C'}
    process=subprocess.Popen(argv,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
        text=True,start_new_session=True)
    try:
        output,error=process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        try:os.killpg(process.pid,signal.SIGKILL)
        except ProcessLookupError:pass
        process.communicate(timeout=5)
        raise ValueError('bootstrap result uncertain; retain attempt and partial data') from None
    require(process.returncode==0 and len(output)+len(error)<65536)
    return output


def command(binaries,data):
    return [str(Path(binaries)/'initdb'),'--pgdata',str(data),'--username=shop_bootstrap',
        '--encoding=UTF8','--locale=C','--data-checksums','--auth-local=reject',
        '--auth-host=reject','--no-clean','--no-instructions']


def initialize_empty(data,spool,binaries,authorization_id):
    """Filesystem/command core; caller must first authorize actual storage identity.

    Accepts explicit paths for token-owned local tests. Production execute() fixes
    them to /srv/shop. Does not create, discover or clean either directory.
    """
    require(isinstance(authorization_id,str) and re.fullmatch('[0-9a-f]{32}',authorization_id))
    data=Path(data);spool=Path(spool)
    data_fd=directory(data)
    try:
        spool_fd=directory(spool)
        try:
            require(not os.listdir(data_fd) and 'bootstrap-result.json' not in os.listdir(spool_fd))
            require((os.fstat(data_fd).st_dev,os.fstat(data_fd).st_ino)!=(os.fstat(spool_fd).st_dev,os.fstat(spool_fd).st_ino))
            # One durable reservation per cluster, shared by all authorization IDs.
            # Every subsequent attempt is denied, including after an uncertain exit.
            attempt=os.open(ATTEMPT,os.O_RDWR|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,
                            0o600,dir_fd=spool_fd)
            try:
                record={'schema_version':1,'authorization_id':authorization_id,'status':'attempted'}
                payload=json.dumps(record).encode('ascii')+b'\n'
                require(os.write(attempt,payload)==len(payload));os.fsync(attempt);os.fsync(spool_fd)
                # Refuse path replacement after reservation, before tool invocation.
                require((os.stat(data).st_dev,os.stat(data).st_ino)==(os.fstat(data_fd).st_dev,os.fstat(data_fd).st_ino)
                        and not os.listdir(data_fd))
                run_tool(command(binaries,data))
                require((data/'PG_VERSION').read_text().strip()=='18')
                result=run_tool([str(Path(binaries)/'pg_controldata'),str(data)],timeout=5)
                fields={key.strip():value.strip() for line in result.splitlines() if ':' in line for key,value in [line.split(':',1)]}
                system=fields.get('Database system identifier')
                require(isinstance(system,str) and re.fullmatch('[0-9]{10,20}',system)
                        and fields.get('Data page checksum version')=='1')
                # Never replace the durable attempt reservation. A separate receipt
                # avoids truncating uncertainty evidence if publication fails.
                receipt={'schema_version':1,'status':'initialized-offline','authorization_id':authorization_id,
                         'pg_system_identifier':system,'data_checksums':True,'server_started':False}
                receipt_fd=os.open('bootstrap-result.json',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,
                                   0o600,dir_fd=spool_fd)
                try:
                    payload=json.dumps(receipt).encode('ascii')+b'\n'
                    require(os.write(receipt_fd,payload)==len(payload));os.fsync(receipt_fd)
                finally:os.close(receipt_fd)
                os.fsync(spool_fd)
                return receipt
            finally:os.close(attempt)
        finally:os.close(spool_fd)
    finally:os.close(data_fd)


def execute(zfs,apply=False):
    record=load_control('bootstrap.json',validate_record)
    require(isinstance(zfs,str) and zfs.startswith('/nix/store/') and Path(zfs).is_file())
    binaries=Path(record['postgres_bin']);initdb=binaries/'initdb'
    require(initdb.is_file() and str(initdb.resolve()).startswith('/nix/store/') and hashlib.sha256(initdb.read_bytes()).hexdigest()==record['initdb_sha256'])
    require(capture([str(initdb),'--version'])=='initdb (PostgreSQL) 18.6')
    inspect_storage(record['storage'],zfs)
    data=Path('/srv/shop/postgres');spool=Path('/srv/shop/spool')
    for path in (data,spool):
        fd=directory(path)
        try:
            if path==data:require(not os.listdir(fd))
            else:require(ATTEMPT not in os.listdir(fd) and 'bootstrap-result.json' not in os.listdir(fd))
        finally:os.close(fd)
    if not apply:return None
    # Re-read authority and the mount/resource evidence immediately before mutation.
    require(load_control('bootstrap.json',validate_record)==record)
    inspect_storage(record['storage'],zfs)
    validate_record(record)
    return initialize_empty(data,spool,binaries,record['authorization_id'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--zfs',required=True);parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    execute(args.zfs,args.apply)
    print('SHOP_CLUSTER_INITIALIZED_OFFLINE' if args.apply else 'SHOP_BOOTSTRAP_PREFLIGHT_ONLY')

if __name__=='__main__':
    try:main()
    except Exception:
        raise SystemExit('SHOP_BOOTSTRAP_DENIED_OR_UNCERTAIN: preserve attempt/partial data; no automatic retry') from None
