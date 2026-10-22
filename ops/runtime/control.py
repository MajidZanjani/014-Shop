"""Bounded root-owned operator records; no record provisioning or refresh."""
import json
import contextlib
import contextvars
from datetime import datetime, timezone
import fcntl
import hashlib
import os
from pathlib import Path
import re
import stat
from guard import require


def unique_fields(pairs):
    result = {}
    for key,value in pairs:
        require(key not in result)
        result[key] = value
    return result


def load_control(filename, validator):
    """Walk root-owned, non-writable ancestors by FD; reject symlinks."""
    require(isinstance(filename,str) and re.fullmatch(r"[a-z][a-z0-9-]*\.json",filename))
    path = Path("/srv/shop/control")/filename
    directory = os.open('/', os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        for part in path.parts[1:-1]:
            next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                              dir_fd=directory)
            os.close(directory)
            directory = next_fd
            info = os.fstat(directory)
            require(info.st_uid == 0 and not info.st_mode & 0o022)
        fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK, dir_fd=directory)
        try:
            info = os.fstat(fd)
            require(stat.S_ISREG(info.st_mode) and info.st_uid == 0
                    and not info.st_mode & 0o022 and info.st_size <= 32768)
            data = os.read(fd, 32769)
            after = os.fstat(fd)
            fields = ('st_dev','st_ino','st_uid','st_gid','st_mode','st_size',
                      'st_mtime_ns','st_ctime_ns')
            require(all(getattr(info,key) == getattr(after,key) for key in fields)
                    and len(data) == info.st_size and 0 < len(data) <= 32768)
            active = _ADMISSION.get()
            if active is not None:
                active['verify']()
                require(filename in active['records']
                        and hashlib.sha256(data).hexdigest() == active['records'][filename])
            return validator(json.loads(data,object_pairs_hook=unique_fields))
        finally:
            os.close(fd)
    finally:
        os.close(directory)



_ADMISSION = contextvars.ContextVar('shop_control_admission', default=None)
ADMISSION_NAME = 'control-admission.json'
ADMISSION_RECORDS = {'expected.json','database-process.json','operator-connection.json',
                     'schema-reconciliation.json','schema-authorization.json',
                     'ledger-bootstrap.json','bootstrap.json'}
_META = ('st_dev','st_ino','st_uid','st_gid','st_mode','st_size','st_mtime_ns','st_ctime_ns')


@contextlib.contextmanager
def _admission_file(*, writable=False):
    """Fixed physical root custody; never create, repair or replace the lock."""
    directory = os.open('/', os.O_RDONLY|os.O_DIRECTORY|os.O_CLOEXEC)
    try:
        for part in ('srv','shop'):
            child = os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=directory)
            os.close(directory); directory = child
            info = os.fstat(directory)
            require(info.st_uid == 0 and not info.st_mode & 0o022)
        flags = os.O_RDWR if writable else os.O_RDONLY
        fd = os.open(ADMISSION_NAME,flags|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC,dir_fd=directory)
        try: yield directory,fd
        finally: os.close(fd)
    finally: os.close(directory)


def _admission_bytes(directory, fd):
    before = os.fstat(fd)
    require(stat.S_ISREG(before.st_mode) and before.st_uid == 0
            and stat.S_IMODE(before.st_mode) == 0o440 and before.st_nlink == 1
            and 0 < before.st_size <= 8192)
    raw = os.pread(fd,8193,0)
    after = os.fstat(fd)
    named = os.stat(ADMISSION_NAME,dir_fd=directory,follow_symlinks=False)
    require(len(raw) == before.st_size
            and all(getattr(before,key) == getattr(after,key) == getattr(named,key) for key in _META))
    return raw,tuple(getattr(after,key) for key in _META)


def _admission_snapshot(directory, fd):
    raw,metadata = _admission_bytes(directory,fd)
    value = json.loads(raw,object_pairs_hook=unique_fields)
    require(type(value) is dict and set(value) == {'schema_version','state','generation','record_sha256'}
            and type(value['schema_version']) is int and value['schema_version'] == 1
            and value['state'] == 'admitted'
            and type(value['generation']) is str and re.fullmatch(r'[a-f0-9]{64}',value['generation']))
    records = value['record_sha256']
    require(type(records) is dict
            and {'expected.json','database-process.json','operator-connection.json'} <= set(records) <= ADMISSION_RECORDS)
    for digest in records.values():
        require(type(digest) is str and re.fullmatch(r'[a-f0-9]{64}',digest))
    return raw,metadata,records


def check_admission():
    active = _ADMISSION.get()
    require(active is not None)
    active['verify']()


@contextlib.contextmanager
def admission():
    """Shared nonblocking lifetime lease; blocked state survives writer exit.

    Cooperating publishers must hold LOCK_EX on this same never-replaced inode,
    persist blocked state before writes and require separate reopening authority.
    This reader neither publishes state nor grants authority to open admission.
    """
    require(_ADMISSION.get() is None)
    with _admission_file() as (directory,fd):
        # A writer takes the exclusive lock on this exact physical file. Never
        # wait/retry: a held writer, missing record or blocked state denies.
        fcntl.flock(fd,fcntl.LOCK_SH|fcntl.LOCK_NB)
        original = _admission_snapshot(directory,fd)
        def verify():
            require(_admission_snapshot(directory,fd) == original)
        token = _ADMISSION.set({'records':original[2],'verify':verify})
        try:
            yield
            verify()
        finally:
            _ADMISSION.reset(token)
            # The containing context closes this FD and releases its lock even
            # when snapshot validation or the operation raises. No state repair.



def validate_block_authority(value):
    require(type(value) is dict and set(value) == {
        'schema_version','action','authorization_id','expires_at','current_admission_sha256'})
    require(type(value['schema_version']) is int and value['schema_version'] == 1
            and value['action'] == 'block-control-admission')
    for field,pattern in (('authorization_id',r'[a-f0-9]{32}'),
                          ('current_admission_sha256',r'[a-f0-9]{64}'),
                          ('expires_at',r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z')):
        require(type(value[field]) is str and re.fullmatch(pattern,value[field]))
    require(datetime.strptime(value['expires_at'],'%Y-%m-%dT%H:%M:%SZ').replace(
        tzinfo=timezone.utc) > datetime.now(timezone.utc))
    return value


def load_block_authority():
    return load_control('record-publication.json',validate_block_authority)


def block_admission():
    """Library-only publisher precursor; never publishes records or reopens.

    Only the separately scoped authority permits this fixed mutation. Any write
    failure leaves an uncertain denied state; no rollback, repair or retry.
    Actual root custody/authorization/installation must be qualified separately.
    """
    require(os.geteuid() == 0 and _ADMISSION.get() is None)
    authority = load_block_authority()
    with _admission_file(writable=True) as (directory,fd):
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        raw,metadata,_ = _admission_snapshot(directory,fd)
        require(hashlib.sha256(raw).hexdigest() == authority['current_admission_sha256'])
        require(load_block_authority() == authority)
        # Capture the existing admitted generation, not discovered target data.
        value = json.loads(raw,object_pairs_hook=unique_fields)
        value.update(state='blocked',block_authorization_id=authority['authorization_id'])
        blocked = json.dumps(value,sort_keys=True,separators=(',',':')).encode('ascii')+b'\n'
        require(0 < len(blocked) <= 8192)
        # Recheck named inode and exact input immediately before the first write.
        require(_admission_bytes(directory,fd) == (raw,metadata))
        os.ftruncate(fd,0)
        remaining = memoryview(blocked);offset = 0
        while remaining:
            written = os.pwrite(fd,remaining,offset)
            require(0 < written <= len(remaining))
            offset += written;remaining = remaining[written:]
        os.fsync(fd)
        os.fsync(directory)
        observed,after = _admission_bytes(directory,fd)
        require(observed == blocked and metadata[:5] == after[:5])
        require(load_block_authority() == authority)
        return {'schema_version':1,'status':'admission_blocked',
                'authorization_id':authority['authorization_id'],
                'previous_admission_sha256':hashlib.sha256(raw).hexdigest(),
                'blocked_admission_sha256':hashlib.sha256(blocked).hexdigest(),
                'local_fsync_readback_completed':True,'durability_qualified':False,
                'publication_authorized':False,'retry_authorized':False,'reopening_authorized':False}
