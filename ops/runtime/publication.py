"""Library-only control publication/reopening lifecycle; no CLI or installation."""
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


def validate_authority(value, *, require_fresh=True):
    require(type(value) is dict and set(value) == {
        'schema_version','action','authorization_id','expires_at','bundle_sha256',
        'original_admission_sha256','blocked_admission_sha256','custody_evidence_sha256',
        'parent','prior_directory','prior_files_sha256','read_gid'})
    require(value['action'] == 'publish-control-generation')
    control.validate_block_authority({key:value[key] for key in
        ('schema_version','authorization_id','expires_at')} | {
        'action':'block-control-admission','current_admission_sha256':value['bundle_sha256']},
        require_fresh=require_fresh)
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



def validate_inspection(value):
    require(type(value) is dict and set(value)=={
        'schema_version','action','authorization_id','expires_at','publication_authority_sha256'}
        and value['action']=='inspect-control-publication')
    control.validate_block_authority({key:value[key] for key in
        ('schema_version','authorization_id','expires_at')} | {
        'action':'block-control-admission','current_admission_sha256':value['publication_authority_sha256']})
    return value


def load_inspection():
    raw=control._load_control_data('control-publication-inspection.json',outside_control=True)
    return validate_inspection(json.loads(raw,object_pairs_hook=control.unique_fields))


def _observe_directory(parent,name,authority,payloads):
    """Bounded current bytes only; unknown contents never grant adoption."""
    try:named=os.stat(name,dir_fd=parent,follow_symlinks=False)
    except FileNotFoundError:return 'absent',None
    require(stat.S_ISDIR(named.st_mode) and named.st_uid==0
            and stat.S_IMODE(named.st_mode)==0o750 and named.st_gid==authority['read_gid'])
    directory=os.open(name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=parent)
    try:
        before=os.fstat(directory)
        require(all(getattr(before,key)==getattr(named,key) for key in bundle.STABLE_FIELDS))
        names=set(os.listdir(directory));require(len(names)<=16)
        known=set(authority['prior_files_sha256'])|set(payloads)
        files={};fingerprints=[];new_permissions=True
        for filename in sorted(names & known):
            fd=os.open(filename,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC,dir_fd=directory)
            try:
                info=os.fstat(fd)
                require(stat.S_ISREG(info.st_mode) and info.st_uid==0 and info.st_nlink==1
                        and not info.st_mode&0o022 and 0<=info.st_size<=32768)
                raw=os.pread(fd,32769,0);after=os.fstat(fd)
                node=os.stat(filename,dir_fd=directory,follow_symlinks=False)
                require(len(raw)==info.st_size
                        and all(getattr(info,key)==getattr(after,key)==getattr(node,key)
                                for key in bundle.STABLE_FIELDS))
                files[filename]=hashlib.sha256(raw).hexdigest()
                fingerprints.append((filename,tuple(getattr(info,key) for key in bundle.STABLE_FIELDS),files[filename]))
                new_permissions &= stat.S_IMODE(info.st_mode)==0o440 and info.st_gid==authority['read_gid']
            finally:os.close(fd)
        final=os.fstat(directory);node=os.stat(name,dir_fd=parent,follow_symlinks=False)
        require(names==set(os.listdir(directory))
                and all(getattr(before,key)==getattr(final,key)==getattr(node,key) for key in bundle.STABLE_FIELDS))
        prior=authority['prior_directory']
        old_identity=(before.st_dev,before.st_ino)==(prior['device'],prior['inode'])
        if old_identity and names==set(authority['prior_files_sha256']) and files==authority['prior_files_sha256']:
            status='original_matches'
        elif names==set(payloads) and new_permissions and files=={
            key:hashlib.sha256(raw).hexdigest() for key,raw in payloads.items()}:
            status='new_matches'
        else:status='different'
        return status,(tuple(getattr(before,key) for key in bundle.STABLE_FIELDS),tuple(sorted(names)),tuple(fingerprints))
    finally:os.close(directory)


def inspect_publication(data, original_admission, historical_authority):
    require(os.geteuid()==0 and control._ADMISSION.get() is None)
    with control._admission_file() as lease:
        fcntl.flock(lease[1],fcntl.LOCK_SH|fcntl.LOCK_NB)
        return _inspect_publication_locked(data,original_admission,historical_authority,lease)


def _inspect_publication_locked(data, original_admission, historical_authority, lease):
    """Observe fixed publication states, never complete/retry/repair/reopen."""
    require(os.geteuid()==0 and control._ADMISSION.get() is None)
    inspection=load_inspection()
    require(type(historical_authority) is bytes and 0<len(historical_authority)<=32768
            and hashlib.sha256(historical_authority).hexdigest()==inspection['publication_authority_sha256'])
    authority=validate_authority(json.loads(historical_authority,object_pairs_hook=control.unique_fields),require_fresh=False)
    require(type(data) is bytes and hashlib.sha256(data).hexdigest()==authority['bundle_sha256'])
    # Historical byte comparison only: expired inner records are not renewed or
    # admitted. Live publication/reopening must still validate fresh authorities.
    _,payloads=bundle._candidate_bytes(data)
    control._validate_admitted(original_admission)
    require(hashlib.sha256(original_admission).hexdigest()==authority['original_admission_sha256'])
    stage='control-next-'+authority['bundle_sha256']
    previous='control-previous-'+authority['original_admission_sha256']
    parent,barrier=lease
    info=os.fstat(parent)
    require(info.st_uid==0 and not info.st_mode&0o022 and (info.st_dev,info.st_ino)==
            (authority['parent']['device'],authority['parent']['inode']))
    blocked,metadata=control._admission_bytes(parent,barrier)
    require(hashlib.sha256(blocked).hexdigest()==authority['blocked_admission_sha256'])
    value=json.loads(blocked,object_pairs_hook=control.unique_fields)
    block_id=value.get('block_authorization_id')
    require(type(block_id) is str and re.fullmatch(r'[a-f0-9]{32}',block_id)
            and blocked==control._blocked_bytes(original_admission,block_id))
    def snapshot():
        return tuple(_observe_directory(parent,name,authority,payloads) for name in ('control',stage,previous))
    observed=snapshot();pattern=tuple(item[0] for item in observed)
    status={('original_matches','absent','absent'):'original_matches',
            ('original_matches','new_matches','absent'):'stage_matches',
            ('absent','new_matches','original_matches'):'prior_moved_matches',
            ('new_matches','absent','original_matches'):'published_matches'}.get(pattern,'conflicting')
    require(load_inspection()==inspection and snapshot()==observed
            and control._admission_bytes(parent,barrier)==(blocked,metadata))
    return {'schema_version':1,'status':status,'completion_confirmed':False,
            'durability_qualified':False,'publication_authorized':False,
            'retry_authorized':False,'reopening_authorized':False}


def validate_reopening_preparation(value):
    require(type(value) is dict and set(value)=={
        'schema_version','action','authorization_id','expires_at',
        'publication_authority_sha256','proposed_admission_sha256','qualification_evidence_sha256'}
        and value['action']=='prepare-control-admission')
    control.validate_block_authority({key:value[key] for key in
        ('schema_version','authorization_id','expires_at')} | {
        'action':'block-control-admission','current_admission_sha256':value['publication_authority_sha256']})
    for key in ('proposed_admission_sha256','qualification_evidence_sha256'):
        require(type(value[key]) is str and re.fullmatch(r'[a-f0-9]{64}',value[key]))
    return value


def load_reopening_preparation():
    raw=control._load_control_data('control-admission-preparation.json',outside_control=True)
    return validate_reopening_preparation(json.loads(raw,object_pairs_hook=control.unique_fields))


def prepare_reopening(data, original_admission, historical_authority, qualification_evidence):
    require(os.geteuid()==0 and control._ADMISSION.get() is None)
    with control._admission_file() as lease:
        fcntl.flock(lease[1],fcntl.LOCK_SH|fcntl.LOCK_NB)
        return _prepare_reopening_locked(data,original_admission,historical_authority,qualification_evidence,lease)


def _prepare_reopening_locked(data, original_admission, historical_authority, qualification_evidence, lease):
    """Return reviewed proposed bytes only; never write or open admission.

    Evidence is opaque and hash-bound to separate root review, not qualified by
    this function. Actual reopening needs separate authority and qualification.
    """
    require(os.geteuid()==0 and control._ADMISSION.get() is None)
    approval=load_reopening_preparation()
    require(type(historical_authority) is bytes and 0<len(historical_authority)<=32768
            and hashlib.sha256(historical_authority).hexdigest()==approval['publication_authority_sha256']
            and type(qualification_evidence) is bytes and 0<len(qualification_evidence)<=1048576
            and hashlib.sha256(qualification_evidence).hexdigest()==approval['qualification_evidence_sha256'])
    authority=validate_authority(json.loads(historical_authority,object_pairs_hook=control.unique_fields),require_fresh=False)
    original=control._validate_admitted(original_admission)
    require(hashlib.sha256(original_admission).hexdigest()==authority['original_admission_sha256']
            and all(authority['prior_files_sha256'].get(name)==digest
                    for name,digest in original['record_sha256'].items()))
    payloads,report=bundle.prepare_records(data)
    require(report['bundle_sha256']==authority['bundle_sha256'])
    candidate=json.loads(data,object_pairs_hook=control.unique_fields)
    require(candidate['records']['expected.json']['gid']==authority['read_gid'])
    proposed=json.dumps({'schema_version':1,'state':'admitted',
        'generation':report['bundle_sha256'],'record_sha256':report['record_sha256']},
        sort_keys=True,separators=(',',':')).encode('ascii')+b'\n'
    control._validate_admitted(proposed)
    require(hashlib.sha256(proposed).hexdigest()==approval['proposed_admission_sha256'])
    parent,barrier=lease
    blocked,metadata=control._admission_bytes(parent,barrier)
    require(hashlib.sha256(blocked).hexdigest()==authority['blocked_admission_sha256'])
    # Independent inspection checks exact parent/block/previous/stage state.
    require(_inspect_publication_locked(data,original_admission,historical_authority,lease)['status']=='published_matches')
    observed=_observe_directory(parent,'control',authority,payloads)
    require(observed[0]=='new_matches' and load_reopening_preparation()==approval)
    # Revalidate all expiring inner records before returning proposed bytes.
    require(bundle.prepare_records(data)==(payloads,report)
            and _inspect_publication_locked(data,original_admission,historical_authority,lease)['status']=='published_matches'
            and _observe_directory(parent,'control',authority,payloads)==observed
            and control._admission_bytes(parent,barrier)==(blocked,metadata)
            and load_reopening_preparation()==approval)
    return proposed,{'schema_version':1,'status':'admission_bytes_prepared',
        'proposed_admission_sha256':approval['proposed_admission_sha256'],
        'completion_confirmed':False,'durability_qualified':False,
        'publication_authorized':False,'retry_authorized':False,'reopening_authorized':False}


def validate_reopening_authority(value, *, require_fresh=True):
    require(type(value) is dict and set(value)=={
        'schema_version','action','authorization_id','expires_at','preparation_authority_sha256',
        'blocked_admission_sha256','proposed_admission_sha256','recovery_evidence_sha256'}
        and value['action']=='reopen-control-admission')
    control.validate_block_authority({key:value[key] for key in
        ('schema_version','authorization_id','expires_at')} | {
        'action':'block-control-admission','current_admission_sha256':value['blocked_admission_sha256']},
        require_fresh=require_fresh)
    for key in ('preparation_authority_sha256','proposed_admission_sha256','recovery_evidence_sha256'):
        require(type(value[key]) is str and re.fullmatch(r'[a-f0-9]{64}',value[key]))
    return value


def load_reopening_authority():
    raw=control._load_control_data('control-admission-reopening.json',outside_control=True)
    return validate_reopening_authority(json.loads(raw,object_pairs_hook=control.unique_fields))


def reopen_admission(data, original_admission, historical_authority, qualification_evidence, recovery_evidence):
    """Library-only exact reopening; late failure may leave admitted bytes.

    Never install/invoke without qualified storage/runtime and scoped authority.
    There is no automatic rollback, reblock, cleanup or retry after uncertainty.
    """
    require(os.geteuid()==0 and control._ADMISSION.get() is None)
    authority=load_reopening_authority()
    require(type(recovery_evidence) is bytes and 0<len(recovery_evidence)<=1048576
            and hashlib.sha256(recovery_evidence).hexdigest()==authority['recovery_evidence_sha256'])
    preparation=control._load_control_data('control-admission-preparation.json',outside_control=True)
    validate_reopening_preparation(json.loads(preparation,object_pairs_hook=control.unique_fields))
    require(hashlib.sha256(preparation).hexdigest()==authority['preparation_authority_sha256'])
    with control._admission_file(writable=True) as lease:
        parent,barrier=lease
        fcntl.flock(barrier,fcntl.LOCK_EX|fcntl.LOCK_NB)
        blocked,metadata=control._admission_bytes(parent,barrier)
        require(hashlib.sha256(blocked).hexdigest()==authority['blocked_admission_sha256'])
        proposed,_=_prepare_reopening_locked(data,original_admission,historical_authority,qualification_evidence,lease)
        require(hashlib.sha256(proposed).hexdigest()==authority['proposed_admission_sha256']
                and control._load_control_data('control-admission-preparation.json',outside_control=True)==preparation
                and load_reopening_authority()==authority
                and _prepare_reopening_locked(data,original_admission,historical_authority,qualification_evidence,lease)[0]==proposed
                and control._load_control_data('control-admission-preparation.json',outside_control=True)==preparation
                and control._admission_bytes(parent,barrier)==(blocked,metadata)
                and load_reopening_authority()==authority)
        # Truncation/partial bytes deny readers. Full bytes can be admitted even
        # if a subsequent sync/readback/authority check raises. Preserve evidence.
        os.ftruncate(barrier,0)
        offset=0;remaining=memoryview(proposed)
        while remaining:
            written=os.pwrite(barrier,remaining,offset)
            require(0<written<=len(remaining))
            offset+=written;remaining=remaining[written:]
        os.fsync(barrier);os.fsync(parent)
        observed,after=control._admission_bytes(parent,barrier)
        require(observed==proposed and metadata[:5]==after[:5]
                and control._load_control_data('control-admission-preparation.json',outside_control=True)==preparation
                and load_reopening_authority()==authority)
        return {'schema_version':1,'status':'admission_opened',
            'admission_sha256':authority['proposed_admission_sha256'],
            'local_fsync_readback_completed':True,'durability_qualified':False,
            'publication_authorized':False,'retry_authorized':False,'reopening_authorized':False}


def validate_reopening_inspection(value):
    require(type(value) is dict and set(value)=={
        'schema_version','action','authorization_id','expires_at','reopening_authority_sha256'}
        and value['action']=='inspect-control-admission-reopening')
    control.validate_block_authority({key:value[key] for key in
        ('schema_version','authorization_id','expires_at')} | {
        'action':'block-control-admission','current_admission_sha256':value['reopening_authority_sha256']})
    return value


def load_reopening_inspection():
    raw=control._load_control_data('control-admission-reopening-inspection.json',outside_control=True)
    return validate_reopening_inspection(json.loads(raw,object_pairs_hook=control.unique_fields))


def inspect_reopening(blocked, proposed, historical_reopening_authority):
    """Current-byte observation only, including partial/empty uncertain writes."""
    require(os.geteuid()==0 and control._ADMISSION.get() is None)
    inspection=load_reopening_inspection()
    require(type(historical_reopening_authority) is bytes and 0<len(historical_reopening_authority)<=32768
            and hashlib.sha256(historical_reopening_authority).hexdigest()==inspection['reopening_authority_sha256'])
    authority=validate_reopening_authority(json.loads(historical_reopening_authority,
        object_pairs_hook=control.unique_fields),require_fresh=False)
    require(type(blocked) is bytes and 0<len(blocked)<=8192
            and hashlib.sha256(blocked).hexdigest()==authority['blocked_admission_sha256'])
    control._validate_admitted(proposed)
    require(hashlib.sha256(proposed).hexdigest()==authority['proposed_admission_sha256'])
    with control._admission_file() as (parent,barrier):
        fcntl.flock(barrier,fcntl.LOCK_SH|fcntl.LOCK_NB)
        raw,metadata=control._admission_bytes(parent,barrier,allow_empty=True)
        status='blocked_matches' if raw==blocked else ('admitted_matches' if raw==proposed else 'different_bytes')
        require(load_reopening_inspection()==inspection
                and control._admission_bytes(parent,barrier,allow_empty=True)==(raw,metadata))
        return {'schema_version':1,'status':status,'completion_confirmed':False,
            'durability_qualified':False,'publication_authorized':False,
            'retry_authorized':False,'reopening_authorized':False}
