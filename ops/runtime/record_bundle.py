"""Offline unverified control-record preparation; never publishes or attests host.

Input is a private candidate bundle, not proof or authority. Hashes identify the
exact canonical record bytes a separately authorized publisher would review.
"""
import base64
import control
import hashlib
import json
import os
import re
import stat
from control import unique_fields
from guard import require,validate_expected
import operator_inspect
import process_probe
import schema_reconciliation

MAX_BUNDLE=3145728
FILENAMES={'expected.json','database-process.json','operator-connection.json','schema-reconciliation.json'}


def prepare_records(data):
    require(type(data) is bytes and 0<len(data)<=MAX_BUNDLE)
    value=json.loads(data.decode('utf8'),object_pairs_hook=unique_fields)
    require(type(value) is dict and set(value)=={'schema_version','evidence_class','records','artifact_base64'})
    require(type(value['schema_version']) is int and value['schema_version']==1
            and value['evidence_class']=='unverified-candidate')
    records=value['records']
    require(type(records) is dict and set(records)==FILENAMES)
    payloads={name:json.dumps(record,sort_keys=True,separators=(',',':'),ensure_ascii=True,
                           allow_nan=False).encode('ascii')+b'\n' for name,record in records.items()}
    require(all(len(payload)<=32768 for payload in payloads.values()))
    expected=validate_expected(records['expected.json'])
    process=process_probe.validate_record(records['database-process.json'])
    connection=operator_inspect.validate_connection(records['operator-connection.json'])
    authorization=schema_reconciliation.validate_authorization(records['schema-reconciliation.json'])
    require(process['startup']==expected)
    operator_inspect.validate_bindings(connection,process,authorization)
    encoded=value['artifact_base64']
    require(type(encoded) is str and len(encoded)<=2796204)
    artifact=base64.b64decode(encoded,validate=True)
    schema_reconciliation.validate_artifact(artifact,authorization)
    report={'schema_version':1,'status':'candidate_validated','evidence_class':'unverified-candidate',
        'publication_authorized':False,'retry_authorized':False,'reopening_authorized':False,
        'bundle_sha256':hashlib.sha256(data).hexdigest(),
        'record_sha256':{name:hashlib.sha256(payloads[name]).hexdigest() for name in sorted(FILENAMES)}}
    return payloads,report


STABLE_FIELDS=('st_dev','st_ino','st_uid','st_gid','st_mode','st_size','st_mtime_ns','st_ctime_ns')


def _stage_file(directory, name, payload, *, mode=0o400, gid=None):
    """New private regular file only; retain every created object on failure."""
    fd=os.open(name,os.O_RDWR|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,
               mode,dir_fd=directory)
    try:
        if gid is not None:os.fchown(fd,-1,gid)
        info=os.fstat(fd)
        require(stat.S_ISREG(info.st_mode) and stat.S_IMODE(info.st_mode)==mode
                and info.st_uid==os.geteuid() and info.st_nlink==1 and info.st_size==0)
        remaining=memoryview(payload)
        while remaining:
            written=os.write(fd,remaining)
            require(0<written<=len(remaining))
            remaining=remaining[written:]
        os.fsync(fd)
        before=os.fstat(fd)
        actual=os.pread(fd,len(payload)+1,0)
        after=os.fstat(fd)
        named=os.stat(name,dir_fd=directory,follow_symlinks=False)
        require((info.st_dev,info.st_ino,info.st_uid,info.st_gid,info.st_mode)==
                (after.st_dev,after.st_ino,after.st_uid,after.st_gid,after.st_mode)
                and (named.st_dev,named.st_ino)==(after.st_dev,after.st_ino)
                and actual==payload and before.st_size==len(payload) and after.st_nlink==1
                and all(getattr(before,key)==getattr(after,key) for key in STABLE_FIELDS))
    finally:
        os.close(fd)


def _candidate_material(data):
    payloads,report=prepare_records(data)
    artifact=base64.b64decode(json.loads(data)['artifact_base64'],validate=True)
    files=dict(payloads,**{'bundle.json':data,'artifact.bin':artifact})
    report=dict(report,status='candidate_staged',
        file_sha256={name:hashlib.sha256(payload).hexdigest() for name,payload in sorted(files.items())})
    return files,report


def _readback_files(directory, files, *, mode=0o400, gid=None):
    require(set(os.listdir(directory))==set(files))
    for filename,payload in files.items():
        fd=os.open(filename,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC,dir_fd=directory)
        try:
            before=os.fstat(fd)
            require(stat.S_ISREG(before.st_mode) and before.st_uid==os.geteuid()
                    and stat.S_IMODE(before.st_mode)==mode and (gid is None or before.st_gid==gid) and before.st_nlink==1
                    and before.st_size==len(payload))
            require(os.pread(fd,len(payload)+1,0)==payload)
            after=os.fstat(fd)
            named=os.stat(filename,dir_fd=directory,follow_symlinks=False)
            require(all(getattr(before,key)==getattr(after,key) for key in STABLE_FIELDS)
                    and (named.st_dev,named.st_ino)==(after.st_dev,after.st_ino))
        finally:os.close(fd)
    require(set(os.listdir(directory))==set(files))


def stage_candidate(data, parent_fd):
    """Prepare private review files, never live control records or authority.

    Caller supplies an already-owned scratch directory FD, mode0700. The library
    has no path discovery, installer, root-record issuer or retry/cleanup logic.
    Any exception after mkdir leaves an uncertain partial candidate for review.
    """
    files,report=_candidate_material(data)  # Invalid candidates create nothing.
    name='candidate-'+report['bundle_sha256']
    parent=os.dup(parent_fd)
    os.set_inheritable(parent,False)
    try:
        parent_before=os.fstat(parent)
        require(stat.S_ISDIR(parent_before.st_mode) and parent_before.st_uid==os.geteuid()
                and stat.S_IMODE(parent_before.st_mode)==0o700)
        # Exclusive new directory: an existing full, partial, symlink or unknown
        # object is never adopted, overwritten, removed or automatically retried.
        os.mkdir(name,0o700,dir_fd=parent)
        directory=os.open(name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=parent)
        try:
            info=os.fstat(directory)
            require(info.st_uid==os.geteuid() and stat.S_IMODE(info.st_mode)==0o700)
            identity=(info.st_dev,info.st_ino,info.st_uid,info.st_gid,info.st_mode)
            for filename,payload in sorted(files.items()):_stage_file(directory,filename,payload)
            require(set(os.listdir(directory))==set(files))
            os.fsync(directory)
            # Final marker remains unverified and cannot authorize publication.
            receipt=json.dumps(report,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode('ascii')+b'\n'
            _stage_file(directory,'prepared.json',receipt)
            os.fsync(directory)
            os.fsync(parent)
            named=os.stat(name,dir_fd=parent,follow_symlinks=False)
            require(identity==(named.st_dev,named.st_ino,named.st_uid,named.st_gid,named.st_mode)
                    and set(os.listdir(directory))==set(files)|{'prepared.json'})
            _readback_files(directory,{**files,'prepared.json':receipt})
            current=os.fstat(parent)
            require(all(getattr(parent_before,key)==getattr(current,key)
                        for key in ('st_dev','st_ino','st_uid','st_gid','st_mode')))
            return report
        finally:os.close(directory)
    finally:os.close(parent)


def inspect_candidate(data, parent_fd):
    """Read back retained scratch files; matching bytes never prove durability.

    Original input must still pass validation. No write, fsync, publication,
    repair, expiry renewal or automatic retry is performed, even for a matching
    final marker left behind by an uncertain staging operation.
    """
    files,report=_candidate_material(data)
    receipt=json.dumps(report,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode('ascii')+b'\n'
    name='candidate-'+report['bundle_sha256']
    parent=os.dup(parent_fd)
    try:
        before=os.fstat(parent)
        require(stat.S_ISDIR(before.st_mode) and before.st_uid==os.geteuid()
                and stat.S_IMODE(before.st_mode)==0o700)
        directory=os.open(name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=parent)
        try:
            initial=os.fstat(directory)
            require(initial.st_uid==os.geteuid() and stat.S_IMODE(initial.st_mode)==0o700)
            _readback_files(directory,{**files,'prepared.json':receipt})
            after=os.fstat(directory)
            named=os.stat(name,dir_fd=parent,follow_symlinks=False)
            require(all(getattr(initial,key)==getattr(after,key)==getattr(named,key)
                        for key in STABLE_FIELDS))
            current=os.fstat(parent)
            require(all(getattr(before,key)==getattr(current,key)
                        for key in ('st_dev','st_ino','st_uid','st_gid','st_mode')))
            return dict(report,status='candidate_matches',durability_confirmed=False)
        finally:os.close(directory)
    finally:os.close(parent)



def validate_custody_authority(value, *, require_fresh=True):
    require(type(value) is dict and set(value) == {
        'schema_version','action','authorization_id','expires_at','admission_sha256','parent'})
    require(value['action'] == 'retain-control-generation')
    control.validate_block_authority({key:value[key] for key in
        ('schema_version','authorization_id','expires_at')} | {
        'action':'block-control-admission','current_admission_sha256':value['admission_sha256']},
        require_fresh=require_fresh)
    parent = value['parent']
    require(type(parent) is dict and set(parent) == {'device','inode'}
            and all(type(n) is int and n > 0 for n in parent.values()))
    return value


def load_custody_authority():
    raw = control.load_control_bytes('generation-custody.json')
    return raw,validate_custody_authority(json.loads(raw,object_pairs_hook=unique_fields))


def retain_control_generation(parent_fd):
    """Root-only exact-generation local custody, not publication or archive proof.

    Parent FD must be separately approved by exact device/inode and root0700.
    Trusted physical ancestry and independent archive qualification are external
    prerequisites; a matching leaf FD does not establish them.
    """
    require(os.geteuid() == 0 and control._ADMISSION.get() is None)
    authority_raw,authority = load_custody_authority()
    parent = os.dup(parent_fd)
    os.set_inheritable(parent,False)
    try:
        before = os.fstat(parent)
        require(stat.S_ISDIR(before.st_mode) and before.st_uid == 0
                and stat.S_IMODE(before.st_mode) == 0o700
                and (before.st_dev,before.st_ino) ==
                    (authority['parent']['device'],authority['parent']['inode']))
        with control.admission():
            active = control._ADMISSION.get()
            original = active['original']
            require(hashlib.sha256(original).hexdigest() == authority['admission_sha256'])
            files = {'admission.json':original,'custody-authorization.json':authority_raw}
            for filename in sorted(active['records']):
                files[filename] = control.load_control_bytes(filename)
            control.check_admission()
        # The source snapshot is complete under its lease. Authority lives outside
        # its hash graph, avoiding a self-referential manifest. Never infer that
        # this generation is still current after releasing the lease.
        require(load_custody_authority() == (authority_raw,authority))
        name = 'generation-'+authority['admission_sha256']
        os.mkdir(name,0o700,dir_fd=parent)
        directory = os.open(name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=parent)
        try:
            initial = os.fstat(directory)
            require(initial.st_uid == 0 and stat.S_IMODE(initial.st_mode) == 0o700)
            for filename,payload in sorted(files.items()):_stage_file(directory,filename,payload)
            os.fsync(directory)
            report = _custody_report(files,authority['admission_sha256'])
            receipt = json.dumps(report,sort_keys=True,separators=(',',':')).encode('ascii')+b'\n'
            _stage_file(directory,'retained.json',receipt)
            os.fsync(directory);os.fsync(parent)
            _readback_files(directory,{**files,'retained.json':receipt})
            named = os.stat(name,dir_fd=parent,follow_symlinks=False)
            require(all(getattr(initial,key) == getattr(named,key)
                        for key in ('st_dev','st_ino','st_uid','st_gid','st_mode')))
            current = os.fstat(parent)
            require(all(getattr(before,key) == getattr(current,key)
                        for key in ('st_dev','st_ino','st_uid','st_gid','st_mode')))
            require(load_custody_authority() == (authority_raw,authority))
            return report
        finally:os.close(directory)
    finally:os.close(parent)



def _custody_report(files, digest):
    return {'schema_version':1,'status':'generation_retained','admission_sha256':digest,
            'file_sha256':{name:hashlib.sha256(payload).hexdigest() for name,payload in sorted(files.items())},
            'local_fsync_readback_completed':True,'durability_qualified':False,
            'publication_authorized':False,'retry_authorized':False,'reopening_authorized':False}


def validate_custody_inspection(value):
    require(type(value) is dict and set(value) == {
        'schema_version','action','authorization_id','expires_at','admission_sha256',
        'parent','retained_authority_sha256'} and value['action'] == 'inspect-control-generation')
    validate_custody_authority({key:item for key,item in value.items()
        if key != 'retained_authority_sha256'} | {'action':'retain-control-generation'})
    digest = value['retained_authority_sha256']
    require(type(digest) is str and re.fullmatch(r'[a-f0-9]{64}',digest))
    return value


def load_custody_inspection():
    return control.load_control('custody-inspection.json',validate_custody_inspection)


def inspect_retained_generation(original_files, parent_fd):
    """Compare private original material, never confirm historical completion.

    Independent fresh inspection authority; no live admission, old authority
    lookup/renewal, file writes, fsync, cleanup, repair, retry or reopening.
    """
    require(os.geteuid() == 0 and control._ADMISSION.get() is None)
    authority = load_custody_inspection()
    require(type(original_files) is dict)
    files = dict(original_files)
    require({'admission.json','custody-authorization.json'} <= set(files)
            and set(files) <= control.ADMISSION_RECORDS | {'admission.json','custody-authorization.json'})
    require(all(type(payload) is bytes and 0 < len(payload) <= 32768 for payload in files.values()))
    manifest = control._validate_admitted(files['admission.json'])
    require(set(files) == set(manifest['record_sha256']) | {'admission.json','custody-authorization.json'}
            and hashlib.sha256(files['admission.json']).hexdigest() == authority['admission_sha256']
            and hashlib.sha256(files['custody-authorization.json']).hexdigest() == authority['retained_authority_sha256'])
    historical = validate_custody_authority(json.loads(files['custody-authorization.json'],
        object_pairs_hook=unique_fields),require_fresh=False)
    require(historical['admission_sha256'] == authority['admission_sha256']
            and historical['parent'] == authority['parent'])
    for name,digest in manifest['record_sha256'].items():
        require(hashlib.sha256(files[name]).hexdigest() == digest)
        json.loads(files[name],object_pairs_hook=unique_fields)
    report = _custody_report(files,authority['admission_sha256'])
    receipt = json.dumps(report,sort_keys=True,separators=(',',':')).encode('ascii')+b'\n'
    parent = os.dup(parent_fd)
    os.set_inheritable(parent,False)
    try:
        before = os.fstat(parent)
        require(stat.S_ISDIR(before.st_mode) and before.st_uid == 0
                and stat.S_IMODE(before.st_mode) == 0o700
                and (before.st_dev,before.st_ino) ==
                    (authority['parent']['device'],authority['parent']['inode']))
        name = 'generation-'+authority['admission_sha256']
        directory = os.open(name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=parent)
        try:
            initial = os.fstat(directory)
            require(initial.st_uid == 0 and stat.S_IMODE(initial.st_mode) == 0o700)
            _readback_files(directory,{**files,'retained.json':receipt})
            after = os.fstat(directory)
            named = os.stat(name,dir_fd=parent,follow_symlinks=False)
            require(all(getattr(initial,key) == getattr(after,key) == getattr(named,key) for key in STABLE_FIELDS))
            current = os.fstat(parent)
            require(all(getattr(before,key) == getattr(current,key)
                        for key in ('st_dev','st_ino','st_uid','st_gid','st_mode')))
            require(load_custody_inspection() == authority)
            return dict(report,status='generation_matches',local_fsync_readback_completed=False,
                        completion_confirmed=False)
        finally:os.close(directory)
    finally:os.close(parent)
