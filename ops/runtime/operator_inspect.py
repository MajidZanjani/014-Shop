"""Prepared read-only operator command; runtime packaging/qualification pending.

Only inspect and --help exist. No DSN, credential, path or mutation arguments.
Artifact input is private regular FD0; credential input is private regular FD3.
"""
import json
import os
import re
import stat
import sys
sys.dont_write_bytecode=True
import psycopg
from control import load_control
from guard import require, validate_database_identity
import process_probe
import schema_reconciliation

SAFE_ENV={'LANG':'C','LC_ALL':'C','HOME':'/nonexistent'}
SOCKET_DIRECTORY='/srv/shop/tmp/postgres-socket'
ERROR=b'{"event":"operator.inspection_denied"}\n'
HELP=b'Prepared read-only command: inspect (private artifact FD0, credential FD3). Runtime qualification pending.\n'


def validate_connection(value):
    require(type(value) is dict and set(value)=={
        'schema_version','database','socket_directory','zfs','pg_control'})
    require(type(value['schema_version']) is int and value['schema_version']==1
            and value['socket_directory']==SOCKET_DIRECTORY)
    validate_database_identity(value['database'],value['database'])
    require(value['database']['server_address']=='unix-socket')
    for field,name in (('zfs','zfs'),('pg_control','pg_controldata')):
        require(type(value[field]) is str and re.fullmatch(
            r'/nix/store/[a-z0-9]{32}-[^/]+/bin/'+name,value[field]))
    return value


def load_connection():
    return load_control('operator-connection.json',validate_connection)


def read_private_fd(fd, maximum, minimum=1):
    before=os.fstat(fd)
    require(stat.S_ISREG(before.st_mode) and before.st_uid==os.geteuid()
            and stat.S_IMODE(before.st_mode) in (0o400,0o600)
            and minimum<=before.st_size<=maximum)
    os.set_inheritable(fd,False)
    data=os.pread(fd,maximum+1,0)
    after=os.fstat(fd)
    stable=('st_dev','st_ino','st_uid','st_gid','st_mode','st_size','st_mtime_ns','st_ctime_ns')
    require(all(getattr(before,key)==getattr(after,key) for key in stable)
            and len(data)==before.st_size)
    return data


def socket_identity(uid,port):
    """Reject redirected or writable socket ancestors; no directory creation."""
    directory=os.open('/',os.O_RDONLY|os.O_DIRECTORY|os.O_CLOEXEC)
    try:
        for part in SOCKET_DIRECTORY.split('/')[1:]:
            child=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=directory)
            os.close(directory);directory=child
            info=os.fstat(directory)
            require(info.st_uid in (0,uid) and not info.st_mode & 0o022)
        require(info.st_uid==uid and stat.S_IMODE(info.st_mode)==0o700)
        node=os.stat('.s.PGSQL.'+str(port),dir_fd=directory,follow_symlinks=False)
        require(stat.S_ISSOCK(node.st_mode) and node.st_uid==uid
                and stat.S_IMODE(node.st_mode)==0o700)
        return (node.st_dev,node.st_ino,node.st_uid)
    finally:
        os.close(directory)


def validate_report(value):
    require(type(value) is dict and set(value)=={
        'schema_version','status','retry_authorized','reopening_authorized'})
    require(type(value['schema_version']) is int and value['schema_version']==1
            and value['status'] in ('recorded','not_recorded','conflict','ledger_absent')
            and value['retry_authorized'] is False and value['reopening_authorized'] is False)
    return value


def inspect_from_fds():
    """Single-process CLI only; never invoke inside an application server."""
    require(dict(os.environ)==SAFE_ENV and os.geteuid()>0)
    connection_record=load_connection();expected=connection_record['database']
    require(os.geteuid()==expected['account_uid'])
    approved=process_probe.load_record()
    require(approved['database']==expected)
    authorization=schema_reconciliation.load_authorization()
    require(authorization['database']==expected)
    artifact=read_private_fd(0,2097152)
    schema_reconciliation.validate_artifact(artifact,authorization)
    process_probe.probe(approved,connection_record['zfs'],connection_record['pg_control'])
    socket_before=socket_identity(expected['account_uid'],expected['server_port'])
    password=read_private_fd(3,4096,16).decode('utf8')
    require('\x00' not in password)
    connection=psycopg.connect(host=SOCKET_DIRECTORY,port=expected['server_port'],
        dbname=expected['database'],user=expected['role'],password=password,
        autocommit=True,connect_timeout=2,client_encoding='utf8',passfile='/dev/null',
        require_auth='scram-sha-256',sslmode='disable',gssencmode='disable',
        options='-c default_transaction_read_only=on -c search_path=pg_catalog -c statement_timeout=2000 -c lock_timeout=1000')
    del password
    try:
        require(load_connection()==connection_record
                and socket_identity(expected['account_uid'],expected['server_port'])==socket_before)
        result=schema_reconciliation.inspect_authorized_schema(connection,
            connection_record['zfs'],connection_record['pg_control'],artifact)
        require(load_connection()==connection_record
                and socket_identity(expected['account_uid'],expected['server_port'])==socket_before)
        return validate_report(result)
    finally:
        connection.close()


def main(argv):
    if argv==['--help']:
        os.write(1,HELP);return 0
    if argv!=['inspect']:
        os.write(2,ERROR);return 2
    try:
        result=inspect_from_fds()
        os.write(1,json.dumps(result,sort_keys=True,separators=(',',':')).encode('ascii')+b'\n')
        return 0
    except BaseException:
        # Never serialize exception/traceback/argv/libpq details or input bytes.
        try:os.write(2,ERROR)
        except OSError:pass
        return 1


def entrypoint():
    os.environ.clear();os.environ.update(SAFE_ENV)
    return main(sys.argv[1:])


if __name__=='__main__':
    raise SystemExit(entrypoint())
