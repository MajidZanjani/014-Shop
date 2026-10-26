"""Archived normalized local facts, not authenticated bank events or financial confirmation."""
import hashlib
import uuid
from django.db import connection
from shop.adapters.evidence_archive import manifest
from shop.catalog import checkout,checkout_payment as payment
from . import attempts
from .bank_contract import BankObservation,correlates,BankError,precedes
from .models import SyntheticPaymentObservation as Receipt

FLAGS={'evidence_class':'local-synthetic','financial_confirmation':False,'effects_authorized':False}


def fail():raise BankError('synthetic_observation_journal_hold')


def normalized(value):
    return None if value is None else {'provider_operation_id':str(value.provider_operation_id),
        'merchant':value.merchant,'reference':str(value.reference),'currency':value.currency,
        'amount_minor':value.amount_minor,'status':value.status}


def typed(value):
    if value is None:return None
    if not isinstance(value,dict):fail()
    try:
        result=BankObservation(uuid.UUID(value['provider_operation_id']),value['merchant'],uuid.UUID(value['reference']),
                               value['currency'],value['amount_minor'],value['status'])
        if normalized(result)!=value:fail()
        return result
    except (KeyError,ValueError,TypeError):fail()


def identity(row,value):return uuid.uuid5(row.pk,'normalized-observation-v1-'+checkout.digest(value))


def history_locked(row,archive):
    if not connection.in_atomic_block:fail()
    attempts.retained(row,archive)
    rows=list(Receipt.objects.filter(attempt=row).order_by('revision')[:1001])
    if len(rows)>1000:fail()
    original=hashlib.sha256(attempts.payload(row)).hexdigest();previous=original;seen=set()
    for revision,event in enumerate(rows,1):
        value=event.payload
        if not isinstance(value,dict):fail()
        raw=value.get('observation');observation=typed(raw)
        if observation is not None and not correlates(attempts.request_for(row),observation):fail()
        expected={'kind':'synthetic-normalized-observation','schema':1,'observation_id':str(event.pk),
                  'attempt_id':str(row.pk),'attempt_sha256':original,'revision':revision,'previous_sha256':previous,
                  'observation':raw,**FLAGS}
        if (event.revision!=revision or event.pk!=identity(row,raw) or event.pk in seen or value!=expected
                or event.sha256!=checkout.digest(value)):fail()
        payment.recover(archive,event.archive_receipt,event.pk,checkout.canonical(value))
        if observation is not None and (row.state!='observed' or
                (row.provider_operation_id!=observation.provider_operation_id or not (row.provider_status==observation.status or precedes(observation.status,row.provider_status)))):fail()
        previous=event.sha256;seen.add(event.pk)
    return rows,previous


def record_locked(row,observation,archive):
    # Callers hold the exact attempt lock; provider I/O must already have completed.
    if not connection.in_atomic_block:fail()
    attempts._validate_observation(row,observation)
    rows,previous=history_locked(row,archive);raw=normalized(observation);key=identity(row,raw)
    prior=next((item for item in rows if item.pk==key),None)
    if prior:return prior
    if len(rows)>=1000:fail()
    value={'kind':'synthetic-normalized-observation','schema':1,'observation_id':str(key),'attempt_id':str(row.pk),
           'attempt_sha256':hashlib.sha256(attempts.payload(row)).hexdigest(),'revision':len(rows)+1,
           'previous_sha256':previous,'observation':raw,**FLAGS}
    body=checkout.canonical(value);receipt=manifest(archive.publish(key,body))
    payment.recover(archive,receipt,key,body)
    return Receipt.objects.create(id=key,attempt=row,revision=len(rows)+1,payload=value,
                                  sha256=checkout.digest(value),archive_receipt=receipt)


def inspect_locked(row,archive):
    rows,_=history_locked(row,archive)
    return {'retained_observations':len(rows),'retained_lookup_miss':any(item.payload['observation'] is None for item in rows),
            'retained_statuses':sorted({item.payload['observation']['status'] for item in rows if item.payload['observation']}),
            'original_response_coverage':'not_established','retry_authorized':False,**FLAGS}
