"""Versioned inert private package rehearsal. No real RTL, key, encryption or rights."""
from datetime import timedelta
import hashlib
import re
import secrets
import uuid
from django.db import transaction
from shop.access.models import StaffCredential
from shop.access.staff_auth import staff_credential
from shop.access.recovery import current_session_epoch
from shop.access.views import digest
from shop.adapters.evidence_archive import manifest
from shop.payments import synthetic_bank,attempts
from . import checkout,checkout_payment as payment,fulfilment,delivery_controls as controls
from .models import (SyntheticLineEntitlement,SyntheticLineDelivery,SyntheticDeliveryStaffGrant,
                     SyntheticPackageRevision,SyntheticPackageAccess)

FIXTURES=('synthetic-materials-v1','synthetic-materials-v2')
LIFETIME=120


def fail(code='package_mismatch',status=409):raise checkout.CheckoutError(code,status)


def staff_locked(request,line=None):
    candidate=staff_credential(request,recent=True)
    if candidate is None:fail('recent_staff_mfa_required',403)
    credential=StaffCredential.objects.select_for_update().select_related('user').get(pk=candidate.pk)
    if (staff_credential(request,recent=True) is None or not credential.user.is_active
            or not credential.user.is_staff or not credential.enabled):fail('recent_staff_mfa_required',403)
    if line is not None and not SyntheticDeliveryStaffGrant.objects.select_for_update().filter(user=credential.user,entitlement=line).exists():
        fail('delivery_scope_required',403)
    return {'staff_id':credential.user_id,'credential_generation':str(credential.generation),
            'mfa_verified_at':request.session['shop_staff_mfa']['verified_at']}


def line_locked(owner,checkout_id,line_id,archive):
    payment.locked(owner,checkout_id)
    line=SyntheticLineEntitlement.objects.select_for_update(of=('self',)).select_related(
        'fulfilment__acceptance__checkout','fulfilment__acceptance__attempt').filter(
        pk=line_id,fulfilment__acceptance__checkout_id=checkout_id).first()
    if line is None:fail('not_found',404)
    grant=line.fulfilment;row=grant.acceptance
    fulfilment.retained(grant,row,archive)
    expected=next((entry for entry in grant.payload['entitlements'] if entry['id']==str(line.pk)),None)
    if expected is None or expected['offer']!=line.snapshot or expected['line_id']!=str(line.line_id):fail()
    if row.attempt.state!='observed' or row.attempt.provider_status not in ('captured','refunded'):fail('synthetic_captured_payment_required',422)
    return line


def material_bytes(line,stage,fixture):
    if fixture not in FIXTURES or stage not in ('initial','reference'):fail('invalid_synthetic_package',400)
    names=['rtl','key-placeholder','manual'] if stage=='initial' else ['reference-design']
    if stage=='initial' and not line.snapshot['later_reference_design']:names.append('reference-design')
    return {f'sll-synthetic-{name}.txt':(
        f'LOCAL SYNTHETIC MATERIAL ONLY\n{fixture}\n{name}\n'
        'Inert text placeholder. No executable RTL, real key, encrypted content, compatibility approval or licence rights.\n').encode()
        for name in names}


def retained(package,line,archive):
    value=package.payload
    if (checkout.digest(value)!=package.sha256 or value.get('package_id')!=str(package.identity)
            or value.get('entitlement_id')!=str(line.pk) or value.get('stage')!=package.stage
            or value.get('version')!=package.version or value.get('request_id')!=str(package.request_id)
            or value.get('grant_sha256')!=line.fulfilment.sha256 or value.get('effects_authorized') is not False
            or value.get('evidence_class')!='local-synthetic'):fail()
    payment.recover(archive,package.archive_receipt,package.identity,checkout.canonical(value))
    expected=material_bytes(line,package.stage,value['fixture'])
    if set(value['artifacts'])!=set(expected):fail()
    for name,body in expected.items():
        item=value['artifacts'][name]
        if item['sha256']!=hashlib.sha256(body).hexdigest() or item['size']!=len(body):fail()
        payment.recover(archive,item['receipt'],uuid.uuid5(package.identity,name),body)


def release(request,owner,checkout_id,line_id,request_id,stage,fixture,archive):
    synthetic_bank.guard()
    if type(request_id) is not uuid.UUID or not isinstance(stage,str) or stage not in ('initial','reference') or not isinstance(fixture,str) or fixture not in FIXTURES:
        fail('invalid_synthetic_package',400)
    with transaction.atomic(durable=True):
        staff_locked(request)
        line=line_locked(owner,checkout_id,line_id,archive);actor=staff_locked(request,line)
        controls.require_open(line,archive)
        prior=SyntheticPackageRevision.objects.filter(entitlement=line,request_id=request_id).first()
        if prior:
            if prior.stage!=stage or prior.payload['fixture']!=fixture or prior.payload['actor']['staff_id']!=actor['staff_id']:fail('package_request_conflict')
            retained(prior,line,archive);return prior
        if stage=='reference':
            initial=SyntheticPackageRevision.objects.filter(entitlement=line,stage='initial').order_by('-version').first()
            if not line.snapshot['later_reference_design'] or initial is None:fail('initial_package_required',422)
            retained(initial,line,archive)
            completion=SyntheticLineDelivery.objects.filter(entitlement=line,stage='initial').first()
            if completion is None or completion.payload!=fulfilment.completion_value(line.fulfilment,line,line.line_id,'initial'):fail()
            payment.recover(archive,completion.archive_receipt,uuid.uuid5(line.pk,'initial-completion-v1'),checkout.canonical(completion.payload))
        previous=SyntheticPackageRevision.objects.filter(entitlement=line,stage=stage).order_by('-version').first()
        if previous:retained(previous,line,archive)
        version=previous.version+1 if previous else 1
        if version>1000:fail('package_revision_limit',422)
        identity=uuid.uuid5(line.pk,'private-package-'+str(request_id))
        artifacts={}
        for name,body in material_bytes(line,stage,fixture).items():
            receipt=archive.publish(uuid.uuid5(identity,name),body)
            payment.recover(archive,manifest(receipt),uuid.uuid5(identity,name),body)
            artifacts[name]={'sha256':hashlib.sha256(body).hexdigest(),'size':len(body),'receipt':manifest(receipt)}
        value={'schema':1,'kind':'synthetic-private-package','package_id':str(identity),'request_id':str(request_id),
            'entitlement_id':str(line.pk),'grant_sha256':line.fulfilment.sha256,'stage':stage,'version':version,
            'previous_sha256':previous.sha256 if previous else None,'fixture':fixture,'actor':actor,'artifacts':artifacts,
            'evidence_class':'local-synthetic','effects_authorized':False,'actual_delivery':False}
        body=checkout.canonical(value);receipt=archive.publish(identity,body)
        payment.recover(archive,manifest(receipt),identity,body)
        completion=fulfilment.completion_value(line.fulfilment,line,line.line_id,stage)
        completion_id=uuid.uuid5(line.pk,stage+'-completion-v1')
        completed=archive.publish(completion_id,checkout.canonical(completion))
        payment.recover(archive,manifest(completed),completion_id,checkout.canonical(completion))
        # Prepared materials are not a release. Recheck recent authority before committing both records.
        staff_locked(request,line)
        row=SyntheticPackageRevision.objects.create(identity=identity,entitlement=line,request_id=request_id,
            stage=stage,version=version,payload=value,sha256=checkout.digest(value),archive_receipt=manifest(receipt))
        event,_=SyntheticLineDelivery.objects.get_or_create(entitlement=line,stage=stage,
            defaults={'payload':completion,'sha256':checkout.digest(completion),'archive_receipt':manifest(completed)})
        if event.payload!=completion or event.sha256!=checkout.digest(completion) or event.archive_receipt!=manifest(completed):fail()
        return row


def package_locked(owner,checkout_id,identity,archive):
    candidate=SyntheticPackageRevision.objects.select_related('entitlement').filter(identity=identity).first()
    # Do not disclose whether another customer's package identity exists.
    if candidate is None:fail('not_found',404)
    line=line_locked(owner,checkout_id,candidate.entitlement_id,archive)
    retained(candidate,line,archive)
    candidate.entitlement=line
    return candidate


def session_binding(request):
    key=request.session.session_key
    if not isinstance(key,str) or not key:fail('verified_session_required',403)
    return digest('package-session',key)


def require_customer_epoch(request):
    # Lock before owner/resource work, matching recovery's epoch-first order.
    if (not callable(getattr(getattr(request,'session',None),'get',None))
            or not current_session_epoch(request,lock=True)):
        fail('download_unavailable',404)


def issue(request,checkout_id,identity,artifact,archive):
    synthetic_bank.guard()
    if not isinstance(artifact,str) or len(artifact)>64:fail('invalid_artifact',400)
    with transaction.atomic(durable=True):
        require_customer_epoch(request)
        payment.locked(request.user,checkout_id)
        package=package_locked(request.user,checkout_id,identity,archive)
        authority_revision=controls.require_open(package.entitlement,archive)
        if artifact not in package.payload['artifacts']:fail('not_found',404)
        now=attempts.database_now()
        if SyntheticPackageAccess.objects.filter(owner=request.user,expires_at__gt=now,consumed_at__isnull=True).count()>=20:
            fail('download_grant_limit',429)
        token=secrets.token_urlsafe(32)
        SyntheticPackageAccess.objects.create(package=package,owner=request.user,artifact=artifact,
            token_digest=digest('package-token',token),session_digest=session_binding(request),expires_at=now+timedelta(seconds=LIFETIME),authority_revision=authority_revision)
        return token


def download(request,checkout_id,identity,token,archive):
    synthetic_bank.guard()
    if not isinstance(token,str) or re.fullmatch(r'[A-Za-z0-9_-]{43}',token) is None:fail('download_unavailable',404)
    with transaction.atomic(durable=True):
        require_customer_epoch(request)
        payment.locked(request.user,checkout_id)
        package=package_locked(request.user,checkout_id,identity,archive)
        authority_revision=controls.require_open(package.entitlement,archive)
        now=attempts.database_now()
        access=SyntheticPackageAccess.objects.select_for_update().filter(package=package,owner=request.user,
            token_digest=digest('package-token',token),session_digest=session_binding(request),expires_at__gt=now,consumed_at__isnull=True).first()
        if access is None or access.authority_revision!=authority_revision:fail('download_unavailable',404)
        body=material_bytes(package.entitlement,package.stage,package.payload['fixture'])[access.artifact]
        payment.recover(archive,package.payload['artifacts'][access.artifact]['receipt'],uuid.uuid5(package.identity,access.artifact),body)
        completed_at=attempts.database_now()
        if completed_at>=access.expires_at:fail('download_unavailable',404)
        access.consumed_at=completed_at;access.save(update_fields=['consumed_at'])
        return access.artifact,body
