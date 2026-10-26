"""Internal local hints and typed lookup, no public callback or real authentication claim."""
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
import uuid
import hashlib
from django.conf import settings
from django.db import connection,transaction
from django.db.models import Q
from django.db.models.functions import Now
from shop.adapters.evidence_archive import PreparedArchive,manifest
from shop.catalog import checkout,checkout_payment as payment
from . import synthetic_bank,attempts,observations
from .bank_contract import BankError,BankObservation,correlates
from .models import (SyntheticPaymentAttempt as Attempt,SyntheticBankNotification as Notification,
    SyntheticNotificationDelivery as Delivery,SyntheticNotificationResult as Result)


def guard():
    synthetic_bank.guard()
    if connection.vendor!='postgresql':raise BankError('synthetic_notification_unavailable')


def fail():raise BankError('synthetic_notification_hold')


def retained(row,archive):
    if row.sha256!=checkout.digest(row.payload):fail()
    if (row.payload.get('evidence_class')!='local-synthetic' or row.payload.get('effects_authorized') is not False
            or row.payload.get('financial_confirmation') is not False):fail()
    payment.recover(archive,row.archive_receipt,row.pk,checkout.canonical(row.payload))


def evidence(identity,value,archive):
    body=checkout.canonical(value);receipt=manifest(archive.publish(identity,body))
    payment.recover(archive,receipt,identity,body)
    return {'payload':value,'sha256':checkout.digest(value),'archive_receipt':receipt}


def hint(row,identity):
    return {'kind':'synthetic-notification-hint','notification_id':str(identity),'attempt_id':str(row.pk),
            'attempt_sha256':hashlib.sha256(attempts.payload(row)).hexdigest(),
            'evidence_class':'local-synthetic','effects_authorized':False,'financial_confirmation':False}


def enqueue(attempt_id,notification_id,archive):
    guard()
    if type(attempt_id) is not uuid.UUID or type(notification_id) is not uuid.UUID:fail()
    with transaction.atomic(durable=True):
        row=Attempt.objects.select_for_update().filter(pk=attempt_id,state__in=['uncertain','observed']).first()
        if row is None:fail()
        attempts.retained(row,archive);value=hint(row,notification_id)
        prior=Notification.objects.filter(pk=notification_id).first()
        if prior:
            if prior.attempt_id!=row.pk or prior.payload!=value:fail()
            retained(prior,archive)
            if not Delivery.objects.filter(notification=prior).exists():fail()
            return prior
        if Notification.objects.filter(attempt=row).count()>=1000:fail()
        note=Notification.objects.create(id=notification_id,attempt=row,**evidence(notification_id,value,archive))
        Delivery.objects.create(notification=note)
        return note


@dataclass(frozen=True)
class Claim:
    notification_id:uuid.UUID
    token:uuid.UUID


def claim(*,lease_seconds=10,max_attempts=3):
    guard()
    if type(lease_seconds) is not int or not 1<=lease_seconds<=60 or type(max_attempts) is not int or not 1<=max_attempts<=5:fail()
    with transaction.atomic(durable=True):
        row=Delivery.objects.select_for_update(skip_locked=True).filter(Q(state='pending')|Q(state='claimed',lease_until__lte=Now())).order_by('notification_id').first()
        if row is None:return None
        if row.attempts>=max_attempts:
            row.state='held';row.token=None;row.lease_until=None;row.save();return None
        token=uuid.uuid4()
        Delivery.objects.filter(pk=row.pk).update(state='claimed',token=token,lease_until=Now()+timedelta(seconds=lease_seconds),attempts=row.attempts+1)
        return Claim(row.pk,token)


def observation_value(observed):
    return None if observed is None else {'provider_operation_id':str(observed.provider_operation_id),
        'merchant':observed.merchant,'reference':str(observed.reference),'currency':observed.currency,
        'amount_minor':observed.amount_minor,'status':observed.status}


def process(owned,archive):
    guard()
    note=Notification.objects.select_related('attempt').get(pk=owned.notification_id)
    retained(note,archive);attempts.retained(note.attempt,archive)
    if note.payload!=hint(note.attempt,note.pk):fail()
    # No database transaction/row lock spans the provider lookup. A hint supplies no status.
    observed=synthetic_bank.lookup(note.attempt.merchant,note.attempt.reference)
    if observed is not None and not correlates(attempts.request_for(note.attempt),observed):fail()
    normalized=observation_value(observed)
    identity=uuid.uuid5(note.pk,'typed-lookup-result-v1')
    value={'result_id':str(identity),'notification_sha256':note.sha256,'observation':normalized,
           'evidence_class':'local-synthetic','effects_authorized':False,'financial_confirmation':False}
    prepared=evidence(identity,value,archive)
    with transaction.atomic(durable=True):
        row=Attempt.objects.select_for_update().get(pk=note.attempt_id)
        delivery=Delivery.objects.select_for_update().filter(pk=note.pk,state='claimed',token=owned.token,lease_until__gt=Now()).first()
        if delivery is None:return False
        attempts.retained(row,archive)
        if note.payload!=hint(row,note.pk):fail()
        prior=Result.objects.filter(notification=note).first()
        if prior:
            if prior.pk!=identity or prior.payload!=value:fail()
            retained(prior,archive)
        observations.record_locked(row,observed,archive)
        # Recheck wall-clock expiry after every row-lock/archive/journal wait.
        if delivery.lease_until<=attempts.database_now():
            transaction.set_rollback(True)
            return False
        if prior is None:Result.objects.create(id=identity,notification=note,**prepared)
        attempts._apply_locked(row,observed)
        delivery.state='checked';delivery.token=None;delivery.lease_until=None;delivery.save()
        return True


def execute_once(*,lease_seconds=10,max_attempts=3):
    guard()
    if not settings.LOCAL_CHECKOUT_ARCHIVE_ROOT:return False
    with PreparedArchive(Path(settings.LOCAL_CHECKOUT_ARCHIVE_ROOT)) as archive:
        owned=claim(lease_seconds=lease_seconds,max_attempts=max_attempts)
        if owned is None:return False
        process(owned,archive)
        return True


def inspect(identity,archive):
    guard()
    with transaction.atomic(durable=True):
        note=Notification.objects.select_related('attempt').get(pk=identity)
        attempt=Attempt.objects.select_for_update().get(pk=note.attempt_id)
        attempts.retained(attempt,archive);retained(note,archive)
        if note.payload!=hint(attempt,note.pk):fail()
        delivery=Delivery.objects.select_for_update().get(notification=note)
        result=Result.objects.filter(notification=note).first()
        if delivery.state=='checked' and result is None:fail()
        if result:
            retained(result,archive)
            if (result.pk!=uuid.uuid5(note.pk,'typed-lookup-result-v1') or result.payload.get('result_id')!=str(result.pk)
                    or result.payload.get('notification_sha256')!=note.sha256):fail()
            raw=result.payload.get('observation')
            if raw is not None:
                try:observed=BankObservation(uuid.UUID(raw['provider_operation_id']),raw['merchant'],uuid.UUID(raw['reference']),raw['currency'],raw['amount_minor'],raw['status'])
                except (KeyError,ValueError,TypeError):fail()
                if (not correlates(attempts.request_for(attempt),observed) or observation_value(observed)!=raw
                        or attempt.state!='observed' or (attempt.provider_operation_id,attempt.provider_status)!=(observed.provider_operation_id,observed.status)):fail()
        return {'state':delivery.state,'attempts':delivery.attempts,
            'lookup_status':result.payload['observation']['status'] if result and result.payload['observation'] else None,
            'evidence_class':'local-synthetic','financial_confirmation':False,'effects_authorized':False,
            'actual_callbacks_enabled':False,'dispatch_authorized':False}
