"""Private local prepared bytes only. No retention or domain-effect qualification."""
from contextlib import contextmanager
from dataclasses import dataclass
import fcntl
import hashlib
import json
import os
import re
import stat
from threading import Lock
import uuid
from .local_storage import LocalStorage

MAX_BYTES=1048576

class ArchiveError(ValueError):pass
class ArchiveConflict(ArchiveError):pass

@dataclass(frozen=True)
class PreparedReceipt:
    evidence_id: uuid.UUID
    sha256: str
    size: int
    evidence_class: str='local-synthetic'
    evidence_kind: str='prepared'
    retention_qualified: bool=False
    effects_authorized: bool=False


def manifest(receipt):
    if (type(receipt) is not PreparedReceipt or type(receipt.evidence_id) is not uuid.UUID
        or not isinstance(receipt.sha256,str) or re.fullmatch('[0-9a-f]{64}',receipt.sha256) is None
        or type(receipt.size) is not int or not 1<=receipt.size<=MAX_BYTES
        or receipt.evidence_class!='local-synthetic' or receipt.evidence_kind!='prepared'
        or receipt.retention_qualified is not False or receipt.effects_authorized is not False):
        raise ArchiveError('invalid_receipt')
    return {'schema':1,'evidence_id':str(receipt.evidence_id),'sha256':receipt.sha256,'size':receipt.size,
            'evidence_class':'local-synthetic','evidence_kind':'prepared',
            'retention_qualified':False,'effects_authorized':False}


def encoded(receipt):return json.dumps(manifest(receipt),sort_keys=True,separators=(',',':')).encode('ascii')


class PreparedArchive:
    def __init__(self,directory):
        try:self.storage=LocalStorage(directory)
        except (OSError,ValueError):raise ArchiveError('archive_unavailable') from None
        self.fd=self.storage.fd
        self.lock=Lock()
        self.closed=False

    def __enter__(self):return self
    def __exit__(self,*args):
        if not self.closed:self.storage.__exit__(*args);self.closed=True

    @contextmanager
    def operation(self):
        if self.closed or not self.lock.acquire(blocking=False):raise ArchiveError('archive_unavailable')
        locked=False
        try:
            fcntl.flock(self.fd,fcntl.LOCK_EX|fcntl.LOCK_NB);locked=True
            yield
        except OSError:raise ArchiveError('archive_unavailable') from None
        finally:
            if locked:fcntl.flock(self.fd,fcntl.LOCK_UN)
            self.lock.release()

    def read_file(self,name,limit):
        fd=os.open(name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=self.fd)
        with os.fdopen(fd,'rb') as source:
            info=os.fstat(fd)
            if (not stat.S_ISREG(info.st_mode) or info.st_uid!=os.geteuid()
                or stat.S_IMODE(info.st_mode)!=0o600 or info.st_nlink!=1 or not 1<=info.st_size<=limit):
                raise ArchiveError('archive_corrupt')
            value=source.read(limit+1)
            after=os.fstat(fd)
            if len(value)!=info.st_size or (info.st_size,info.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):
                raise ArchiveError('archive_corrupt')
            return value

    def publish_file(self,name,value):
        temporary='.pending-'+uuid.uuid4().hex
        fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=self.fd)
        try:
            with os.fdopen(fd,'wb') as output:
                output.write(value);output.flush();os.fsync(output.fileno())
            try:os.link(temporary,name,src_dir_fd=self.fd,dst_dir_fd=self.fd,follow_symlinks=False)
            except FileExistsError:
                if self.read_file(name,MAX_BYTES)!=value:raise ArchiveError('archive_corrupt')
        finally:
            # Only this invocation's unpublished temporary name is removed.
            os.unlink(temporary,dir_fd=self.fd)
        os.fsync(self.fd)

    def verify(self,receipt):
        expected=encoded(receipt)
        stored=self.read_file('receipt-'+receipt.evidence_id.hex+'.json',2048)
        if stored!=expected:raise ArchiveError('archive_corrupt')
        value=self.read_file('blob-'+receipt.sha256,MAX_BYTES)
        if len(value)!=receipt.size or hashlib.sha256(value).hexdigest()!=receipt.sha256:
            raise ArchiveError('archive_corrupt')
        return value

    def recover(self,receipt):
        # The caller retains this exact reference independently; files cannot
        # redefine its expected object hash, identity or evidence classification.
        manifest(receipt)
        with self.operation():return self.verify(receipt)

    def publish(self,evidence_id,value):
        if type(evidence_id) is not uuid.UUID or type(value) is not bytes or not 1<=len(value)<=MAX_BYTES:
            raise ArchiveError('invalid_prepared_evidence')
        receipt=PreparedReceipt(evidence_id,hashlib.sha256(value).hexdigest(),len(value))
        with self.operation():
            name='receipt-'+evidence_id.hex+'.json'
            try:stored=self.read_file(name,2048)
            except FileNotFoundError:stored=None
            if stored is not None:
                # Same identity always means the same exact prepared bytes.
                if stored!=encoded(receipt):raise ArchiveConflict('evidence_conflict')
                self.verify(receipt)
                # A previous acknowledgement may have failed after publication.
                os.fsync(self.fd)
                return receipt
            self.publish_file('blob-'+receipt.sha256,value)
            self.publish_file(name,encoded(receipt))
            self.verify(receipt)
            return receipt
