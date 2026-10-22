"""Library-only physical generation publication. No CLI or reopening operation."""
import fcntl
import hashlib
import json
import os
import re
import stat
import control
import record_bundle as bundle
from guard import require

PRIOR_FILES = control.ADMISSION_RECORDS | {
    'record-publication.json','publication-inspection.json','generation-custody.json','custody-inspection.json'}


def validate_authority(value):
    require(type(value) is dict and set(value) == {
        'schema_version','action','authorization_id','expires_at','bundle_sha256',
        'original_admission_sha256','blocked_admission_sha256','custody_evidence_sha256',
        'parent','prior_directory','prior_files_sha256','read_gid'})
    require(value['action'] == 'publish-control-generation')
    control.validate_block_authority({key:value[key] for key in
        ('schema_version','authorization_id','expires_at')} | {
        'action':'block-control-admission','current_admission_sha256':value['bundle_sha256']})
    for key in ('original_admission_sha256','blocked_admission_sha256','custody_evidence_sha256'):
        require(type(value[key]) is str and re.fullmatch(r'[a-f0-9]{64}',value[key]))
    parent=value['parent'];prior=value['prior_directory']
    require(type(parent) is dict and set(parent)=={'device','inode'}
            and all(type(n) is int and n>0 for n in parent.values()))
    require(type(prior) is dict and set(prior)=={'device','inode','gid','mode'}
            and all(type(n) is int and n>0 for n in prior.values())
            and prior['mode']==0o750)
    require(type(value['read_gid']) is int and 0<value['read_gid']<2**32-1
            and prior['gid']==value['read_gid'])
    files=value['prior_files_sha256']
    require(type(files) is dict and {'expected.json','database-process.json','operator-connection.json'}
            <=set(files)<=PRIOR_FILES)
    for digest in files.values():require(type(digest) is str and re.fullmatch(r'[a-f0-9]{64}',digest))
    return value


def load_authority():
    raw=control._load_control_data('control-publication.json',outside_control=True)
    return validate_authority(json.loads(raw,object_pairs_hook=control.unique_fields))


def _rename_no_replace(parent, source, destination):
    # Fixed Linux/glibc ABI; no replacement fallback on unsupported systems.
    import ctypes
    libc=ctypes.CDLL(None,use_errno=True)
    rename=libc.renameat2
    rename.argtypes=(ctypes.c_int,ctypes.c_char_p,ctypes.c_int,ctypes.c_char_p,ctypes.c_uint)
    rename.restype=ctypes.c_int
    if rename(parent,source.encode('ascii'),parent,destination.encode('ascii'),1)!=0:
        raise OSError(ctypes.get_errno(),'shop control no-replace rename denied')


def _prior_snapshot(parent, directory, authority):
    info=os.fstat(directory);expected=authority['prior_directory']
    named=os.stat('control',dir_fd=parent,follow_symlinks=False)
    require(stat.S_ISDIR(info.st_mode) and info.st_uid==0
            and (info.st_dev,info.st_ino,info.st_gid,stat.S_IMODE(info.st_mode)) ==
                (expected['device'],expected['inode'],expected['gid'],expected['mode'])
            and all(getattr(info,key)==getattr(named,key) for key in bundle.STABLE_FIELDS))
    require(set(os.listdir(directory))==set(authority['prior_files_sha256']))
    files={}
    for name,digest in sorted(authority['prior_files_sha256'].items()):
        fd=os.open(name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC,dir_fd=directory)
        try:
            before=os.fstat(fd)
            require(stat.S_ISREG(before.st_mode) and before.st_uid==0 and before.st_nlink==1
                    and not before.st_mode&0o022 and 0<before.st_size<=32768)
            raw=os.pread(fd,32769,0);after=os.fstat(fd)
            named_file=os.stat(name,dir_fd=directory,follow_symlinks=False)
            require(len(raw)==before.st_size and hashlib.sha256(raw).hexdigest()==digest
                    and all(getattr(before,key)==getattr(after,key)==getattr(named_file,key)
                            for key in bundle.STABLE_FIELDS))
            files[name]=raw
        finally:os.close(fd)
    require(set(os.listdir(directory))==set(files))
    return files


def publish_control_generation(data, original_admission, custody_evidence):
    """Keep admission blocked across two no-replace renames; never auto-retry.

    Exact external custody evidence is separately approved by root authority;
    this helper does not create or independently qualify that approval.
    Failed stages/old generations remain for explicit reconciliation.
    """
    require(os.geteuid()==0 and control._ADMISSION.get() is None)
    authority=load_authority()
    require(type(custody_evidence) is bytes and 0<len(custody_evidence)<=1048576
            and hashlib.sha256(custody_evidence).hexdigest()==authority['custody_evidence_sha256'])
    require(type(data) is bytes and hashlib.sha256(data).hexdigest()==authority['bundle_sha256'])
    original=control._validate_admitted(original_admission)
    require(hashlib.sha256(original_admission).hexdigest()==authority['original_admission_sha256'])
    payloads,report=bundle.prepare_records(data)
    candidate=json.loads(data,object_pairs_hook=control.unique_fields)
    gid=authority['read_gid']
    require(candidate['records']['expected.json']['gid']==gid)
    stage='control-next-'+authority['bundle_sha256']
    previous='control-previous-'+authority['original_admission_sha256']
    with control._admission_file() as (parent,barrier):
        fcntl.flock(barrier,fcntl.LOCK_EX|fcntl.LOCK_NB)
        parent_info=os.fstat(parent)
        require(parent_info.st_uid==0 and not parent_info.st_mode&0o022
                and (parent_info.st_dev,parent_info.st_ino)==
                    (authority['parent']['device'],authority['parent']['inode']))
        blocked,barrier_meta=control._admission_bytes(parent,barrier)
        require(hashlib.sha256(blocked).hexdigest()==authority['blocked_admission_sha256'])
        state=json.loads(blocked,object_pairs_hook=control.unique_fields)
        block_id=state.get('block_authorization_id')
        require(type(block_id) is str and re.fullmatch(r'[a-f0-9]{32}',block_id)
                and blocked==control._blocked_bytes(original_admission,block_id))
        old=os.open('control',os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=parent)
        try:
            prior=_prior_snapshot(parent,old,authority)
            require(all(hashlib.sha256(prior[name]).hexdigest()==digest
                        for name,digest in original['record_sha256'].items()))
            previous_startup=json.loads(prior['expected.json'],object_pairs_hook=control.unique_fields)
            require(previous_startup['uid']==candidate['records']['expected.json']['uid']
                    and previous_startup['gid']==gid)
            # Exclusive stage and previous names: no adoption of any unknown object.
            for name in (stage,previous):
                try:os.stat(name,dir_fd=parent,follow_symlinks=False)
                except FileNotFoundError:pass
                else:raise FileExistsError('shop publication object already exists')
            require(load_authority()==authority)
            os.mkdir(stage,0o750,dir_fd=parent)
            directory=os.open(stage,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=parent)
            try:
                info=os.fstat(directory)
                require(info.st_uid==0 and stat.S_IMODE(info.st_mode)==0o750)
                os.fchown(directory,-1,gid)
                for name,payload in sorted(payloads.items()):
                    require(load_authority()==authority)
                    bundle._stage_file(directory,name,payload,mode=0o440,gid=gid)
                os.fsync(directory);os.fsync(parent)
                bundle._readback_files(directory,payloads,mode=0o440,gid=gid)
                staged=os.fstat(directory)
                named=os.stat(stage,dir_fd=parent,follow_symlinks=False)
                require(all(getattr(staged,key)==getattr(named,key) for key in bundle.STABLE_FIELDS))
                require(_prior_snapshot(parent,old,authority)==prior
                        and control._admission_bytes(parent,barrier)==(blocked,barrier_meta)
                        and load_authority()==authority)
                _rename_no_replace(parent,'control',previous)
                os.fsync(parent)
                require(load_authority()==authority
                        and control._admission_bytes(parent,barrier)==(blocked,barrier_meta))
                _rename_no_replace(parent,stage,'control')
                os.fsync(parent)
                bundle._readback_files(directory,payloads,mode=0o440,gid=gid)
                named=os.stat('control',dir_fd=parent,follow_symlinks=False)
                require((named.st_dev,named.st_ino)==(staged.st_dev,staged.st_ino)
                        and named.st_uid==0 and named.st_gid==gid and stat.S_IMODE(named.st_mode)==0o750
                        and control._admission_bytes(parent,barrier)==(blocked,barrier_meta)
                        and load_authority()==authority)
                return {'schema_version':1,'status':'control_published_blocked',
                        'bundle_sha256':report['bundle_sha256'],'record_sha256':report['record_sha256'],
                        'local_fsync_readback_completed':True,'durability_qualified':False,
                        'publication_authorized':False,'retry_authorized':False,'reopening_authorized':False}
            finally:os.close(directory)
        finally:os.close(old)
