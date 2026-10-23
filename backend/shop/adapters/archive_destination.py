"""Explicit private local destination identity; no remote durability qualification."""
from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import stat
import uuid
from .evidence_archive import PreparedArchive,ArchiveError,ArchiveConflict

MARKER='.archive-destination.json'

@dataclass(frozen=True)
class LocalDestination:
    id: uuid.UUID
    device: int
    inode: int
    manifest_sha256: str


def description(identity,device,inode):
    if (type(identity) is not uuid.UUID or type(device) is not int or not 0<=device<=9223372036854775807
        or type(inode) is not int or not 1<=inode<=9223372036854775807):raise ArchiveError('invalid_destination')
    return json.dumps({'schema':1,'id':str(identity),'device':device,'inode':inode,
        'profile':'local-prepared-v1','evidence_class':'local-synthetic',
        'retention_qualified':False,'effects_authorized':False},sort_keys=True,separators=(',',':')).encode('ascii')


def expected(destination):
    if type(destination) is not LocalDestination:raise ArchiveError('invalid_destination')
    raw=description(destination.id,destination.device,destination.inode)
    if destination.manifest_sha256!=hashlib.sha256(raw).hexdigest():raise ArchiveError('invalid_destination')
    return raw


def verify(archive,directory,destination):
    raw=expected(destination)
    opened=os.fstat(archive.fd);named=os.stat(directory,follow_symlinks=False)
    if (not stat.S_ISDIR(opened.st_mode) or opened.st_uid!=os.geteuid() or stat.S_IMODE(opened.st_mode)!=0o700
        or (opened.st_dev,opened.st_ino)!=(destination.device,destination.inode)
        or not stat.S_ISDIR(named.st_mode) or (named.st_dev,named.st_ino)!=(opened.st_dev,opened.st_ino)
        or archive.read_file(MARKER,2048)!=raw):raise ArchiveError('destination_unavailable')


def initialize_destination(directory,identity):
    if type(identity) is not uuid.UUID:raise ArchiveError('invalid_destination')
    with PreparedArchive(directory) as archive:
        with archive.operation():
            info=os.fstat(archive.fd)
            raw=description(identity,info.st_dev,info.st_ino)
            destination=LocalDestination(identity,info.st_dev,info.st_ino,hashlib.sha256(raw).hexdigest())
            try:existing=archive.read_file(MARKER,2048)
            except FileNotFoundError:existing=None
            if existing is None:
                # Never adopt a directory containing prior unbound objects.
                if os.listdir(archive.fd):raise ArchiveError('destination_not_empty')
                archive.publish_file(MARKER,raw)
            elif existing!=raw:raise ArchiveConflict('destination_conflict')
            verify(archive,Path(directory),destination)
            # Reconcile a possible lost acknowledgement after marker publication.
            os.fsync(archive.fd)
            return destination


class BoundPreparedArchive(PreparedArchive):
    def __init__(self,directory,destination):
        expected(destination)
        self.directory=Path(directory)
        self.destination=destination
        super().__init__(directory)
        try:self.attest()
        except BaseException:
            self.__exit__();raise

    @contextmanager
    def operation(self):
        with super().operation():
            verify(self,self.directory,self.destination)
            yield
            # A changed/replaced marker or root during I/O cannot acknowledge success.
            verify(self,self.directory,self.destination)

    def attest(self):
        with self.operation():return self.destination
