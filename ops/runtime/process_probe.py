"""Read-only process half of database runtime attestation; no Podman commands.

The attestation is provisioned separately after actual reviewed inventory. This
module never discovers a target, refreshes a stale PID or repairs storage.
"""
import os
from pathlib import Path
import re
import stat
from guard import inspect, require, validate_database_identity, validate_expected
from control import load_control, unique_fields



def bounded_read(directory, name, limit=32768):
    fd = os.open(name, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
    try:
        data = os.read(fd, limit + 1)
        require(len(data) <= limit)
        return data.decode('ascii')
    finally:
        os.close(fd)


def validate_record(value):
    require(type(value) is dict and set(value) == {'schema_version','startup','database','process'})
    require(type(value['schema_version']) is int and value['schema_version'] == 1)
    startup = validate_expected(value['startup'])
    database = value['database']
    validate_database_identity(database, database)
    require(database['account_uid'] == startup['uid']
            and database['system_identifier'] == startup['pg_system_identifier'])
    process = value['process']
    require(type(process) is dict and set(process) == {'pid','start_ticks','executable','cgroup'})
    require(type(process['pid']) is int and process['pid'] > 1)
    require(type(process['start_ticks']) is int and process['start_ticks'] > 0)
    require(isinstance(process['executable'],str) and re.fullmatch(
        r'/nix/store/[a-z0-9]{32}-[^/]+/bin/postgres',process['executable']))
    ancestor = '/user.slice/user-' + str(startup['uid']) + '.slice/'
    group = process['cgroup']
    require(isinstance(group,str) and group.startswith(ancestor)
            and not any(part in ('', '.', '..') for part in group.split('/')[1:]))
    # The exact path is observed during qualification, not inferred from a name.
    require('libpod-' + database['container_id'] + '.scope' in group.split('/'))
    return value


def load_record():
    return load_control('database-process.json',validate_record)


def start_ticks(raw, expected_pid):
    # comm can contain spaces and closing parentheses; field 3 follows final ') '.
    opening = raw.find(' ('); closing = raw.rfind(') ')
    require(opening > 0 and closing > opening and raw[:opening] == str(expected_pid))
    fields = raw[closing+2:].split()
    require(len(fields) >= 20 and fields[0] not in ('Z','X','x'))
    return int(fields[19])  # field 22, with field 3 at index zero


def validate_mapping(raw, host_id):
    rows = [tuple(map(int,line.split())) for line in raw.splitlines()]
    require(rows and len(rows) <= 16 and all(len(row) == 3 for row in rows))
    inside_ranges = []; outside_ranges = []; matched = 0
    for inside,outside,count in rows:
        require(inside >= 0 and outside > 0 and count > 0)
        require(inside + count <= 2**32-1 and outside + count <= 2**32-1)
        for start,end in inside_ranges:require(inside+count <= start or end <= inside)
        for start,end in outside_ranges:require(outside+count <= start or end <= outside)
        inside_ranges.append((inside,inside+count));outside_ranges.append((outside,outside+count))
        if inside <= 10001 < inside+count:
            require(outside + 10001-inside == host_id)
            matched += 1
    require(matched == 1)


def validate_process(record, observed):
    """Pure validation of a bounded /proc snapshot; fixtures do not prove a runtime."""
    validate_record(record)
    process = record['process']; startup = record['startup']
    require(type(observed) is dict and set(observed) == {
        'stat_before','stat_after','status','uid_map','gid_map','cgroup','exe','data_identity','host_data_identity'})
    require(start_ticks(observed['stat_before'],process['pid']) == process['start_ticks']
            and start_ticks(observed['stat_after'],process['pid']) == process['start_ticks'])
    status = {}
    for line in observed['status'].splitlines():
        if ':' in line:
            key,value = line.split(':',1)
            require(key not in status);status[key] = value.strip()
    require(status.get('Uid','').split() == [str(startup['uid'])]*4
            and status.get('Gid','').split() == [str(startup['gid'])]*4)
    require(status.get('NoNewPrivs') == '1')
    for key in ('CapInh','CapPrm','CapEff','CapBnd','CapAmb'):
        require(key in status and int(status[key],16) == 0)
    validate_mapping(observed['uid_map'],startup['uid'])
    validate_mapping(observed['gid_map'],startup['gid'])
    require(observed['cgroup'].strip() == '0::'+process['cgroup'])
    require(observed['exe'] == process['executable'])
    require(observed['data_identity'] == observed['host_data_identity'])
    require(type(observed['data_identity']) is tuple and len(observed['data_identity']) == 3
            and all(type(n) is int and n > 0 for n in observed['data_identity']))
    return {key:record['database'][key] for key in ('container_id','account_uid')}


def probe(record, zfs, pg_control):
    """Read fresh startup and exact pinned-process evidence for one SQL guard call."""
    validate_record(record)
    for executable in (zfs,pg_control):
        require(isinstance(executable,str) and executable.startswith('/nix/store/')
                and Path(executable).is_file())
    inspect(record['startup'],zfs,pg_control)
    process = record['process']
    directory = os.open('/proc/'+str(process['pid']), os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        observed = {'stat_before':bounded_read(directory,'stat')}
        for name in ('status','uid_map','gid_map','cgroup'):
            observed[name] = bounded_read(directory,name)
        observed['exe'] = os.readlink('exe',dir_fd=directory)
        host = os.stat('/srv/shop/postgres',follow_symlinks=False)
        data = os.stat('root/var/lib/shop/postgres',dir_fd=directory)
        require(stat.S_ISDIR(host.st_mode) and stat.S_ISDIR(data.st_mode))
        observed['host_data_identity'] = (host.st_dev,host.st_ino,host.st_uid)
        observed['data_identity'] = (data.st_dev,data.st_ino,data.st_uid)
        require(host.st_uid == record['startup']['uid'])
        observed['stat_after'] = bounded_read(directory,'stat')
        return validate_process(record,observed)
    finally:
        os.close(directory)


def authorized_probe(zfs, pg_control):
    """Load approved evidence afresh; suitable callback for execute_mutation."""
    record = load_record()
    return probe(record,zfs,pg_control)


def execute_operator_mutation(connection, zfs, pg_control, statement, parameters=()):
    """Host-side primitive; never expose host /proc or control mounts to the app.

    Operator entrypoints still need their command-specific authority/credential
    plumbing. Django/worker writes, bootstrap and migrations are not integrated.
    """
    from database import execute_mutation
    approved = load_record()
    def fresh():
        current = load_record()
        require(current == approved)
        return probe(current,zfs,pg_control)
    return execute_mutation(connection,approved['database'],fresh,statement,parameters)


def execute_operator_schema_batch(connection, zfs, pg_control, statements):
    """Host-side schema primitive; exact migration authority is still separate.

    The root-owned process record must remain identical across the whole batch.
    Never mount host process/control evidence into application containers.
    """
    from database import execute_schema_batch
    approved = load_record()
    def fresh():
        current = load_record()
        require(current == approved)
        return probe(current,zfs,pg_control)
    return execute_schema_batch(connection,approved['database'],fresh,statements)
