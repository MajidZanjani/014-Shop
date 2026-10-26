"""Local delivery access controls, separate from immutable licence/support rights."""
import uuid
from django.db import transaction
from shop.adapters.evidence_archive import manifest
from shop.payments import synthetic_bank
from . import checkout,checkout_payment as payment
from .models import SyntheticDeliveryControl as Control


def fail(code='delivery_control_mismatch',status=409):raise checkout.CheckoutError(code,status)


def state(line,archive):
    rows=list(Control.objects.filter(entitlement=line).order_by('revision'))
    held=False;previous=line.fulfilment.sha256
    for revision,row in enumerate(rows,1):
        value=row.payload;command=value.get('command',{})
        if (row.revision!=revision or value.get('revision')!=revision or value.get('identity')!=str(row.pk)
                or value.get('request_id')!=str(row.request_id) or value.get('entitlement_id')!=str(line.pk)
                or value.get('grant_sha256')!=line.fulfilment.sha256 or value.get('previous_sha256')!=previous
                or command.get('expected_revision')!=revision-1 or command.get('action')!=('clear' if held else 'hold')
                or value.get('held') is not (not held) or checkout.digest(value)!=row.sha256
                or value.get('effects_authorized') is not False or value.get('evidence_class')!='local-synthetic'):fail()
        payment.recover(archive,row.archive_receipt,row.pk,checkout.canonical(value))
        held=not held;previous=row.sha256
    return {'held':held,'revision':len(rows),'sha256':previous},rows


def require_open(line,archive):
    value,_=state(line,archive)
    if value['held']:fail('delivery_held',423)
    return value['revision']


def record(request,owner,checkout_id,line_id,request_id,expected_revision,action,archive):
    synthetic_bank.guard()
    if (type(request_id) is not uuid.UUID or type(expected_revision) is not int or not 0<=expected_revision<1000
            or action not in ('hold','clear')):fail('invalid_delivery_control',400)
    from . import private_packages as packages
    command={'expected_revision':expected_revision,'action':action}
    with transaction.atomic(durable=True):
        packages.staff_locked(request)
        line=packages.line_locked(owner,checkout_id,line_id,archive);actor=packages.staff_locked(request,line)
        value,rows=state(line,archive)
        prior=next((row for row in rows if row.request_id==request_id),None)
        if prior:
            if prior.payload['command']!=command or prior.payload['actor']['staff_id']!=actor['staff_id']:fail('delivery_control_retry_conflict')
            return prior
        if value['revision']!=expected_revision:fail('delivery_control_revision_changed')
        if action!=('clear' if value['held'] else 'hold'):fail('delivery_control_state_changed')
        identity=uuid.uuid5(line.pk,'delivery-control-'+str(request_id))
        payload={'identity':str(identity),'entitlement_id':str(line.pk),'request_id':str(request_id),
                 'revision':value['revision']+1,'grant_sha256':line.fulfilment.sha256,'previous_sha256':value['sha256'],
                 'command':command,'held':action=='hold','actor':actor,'evidence_class':'local-synthetic','effects_authorized':False}
        body=checkout.canonical(payload);receipt=manifest(archive.publish(identity,body))
        payment.recover(archive,receipt,identity,body)
        packages.staff_locked(request,line)
        return Control.objects.create(id=identity,entitlement=line,revision=payload['revision'],request_id=request_id,
            payload=payload,sha256=checkout.digest(payload),archive_receipt=receipt)
