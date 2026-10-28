"""Durable local statement capture, never SMTP delivery or another support debit."""
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
import uuid
from django.conf import settings
from django.db import connection, transaction
from django.db.models import Q
from django.db.models.functions import Now
from shop.access.effects import local_effect
from shop.access.models import StaffCredential
from shop.adapters.evidence_archive import PreparedArchive, manifest
from shop.catalog import checkout, checkout_payment as payment, fulfilment, support_ledger as ledger
from shop.catalog.models import (SyntheticSupportEvent, SyntheticSupportStaffGrant, SyntheticFulfilment,
    SyntheticStatementMail as Mail, SyntheticStatementDelivery as Delivery, SyntheticStatementCapture as Capture)


def fail():raise checkout.CheckoutError('synthetic_statement_mail_hold',409)


def guard(*,entry=False):
    if (settings.SHOP_ENV not in ('local','synthetic') or settings.MAIL_ADAPTER!='fake' or settings.STORAGE_ADAPTER!='fake'
            or settings.PAYMENT_ADAPTER!='fake' or settings.LIVE_PAYMENTS_ENABLED
            or connection.vendor!='postgresql'):fail()
    if entry and (connection.in_atomic_block or not connection.get_autocommit()):fail()


def message(statement):
    if statement.kind!='statement':fail()
    state=statement.payload['statement']
    # Fixed fixture address; no customer email, bearer or private staff attribution in mail.
    return {'schema':1,'effect_id':str(uuid.uuid5(statement.pk,'synthetic-statement-mail-v1')),
            'statement_id':str(statement.pk),'statement_sha256':statement.sha256,
            'recipient':'support-statement@synthetic.invalid','body':state,
            'evidence_class':'local-synthetic','effects_authorized':False,'actual_email_sent':False}


def retained(row,archive):
    if row.sha256!=checkout.digest(row.payload):fail()
    payment.recover(archive,row.archive_receipt,row.pk,checkout.canonical(row.payload))


def persist(model,identity,value,archive,**fields):
    body=checkout.canonical(value);receipt=manifest(archive.publish(identity,body))
    payment.recover(archive,receipt,identity,body)
    return model.objects.create(id=identity,payload=value,sha256=checkout.digest(value),archive_receipt=receipt,**fields)


def enqueue(statement,archive):
    """Called only under the authorized grant transaction; intent and ledger commit together."""
    guard()
    if not connection.in_atomic_block:fail()
    value=message(statement);identity=uuid.UUID(value['effect_id'])
    prior=Mail.objects.filter(statement=statement).first()
    if prior:
        if prior.pk!=identity or prior.payload!=value:fail()
        retained(prior,archive)
        if not Delivery.objects.filter(mail=prior).exists():fail()
        return prior
    row=persist(Mail,identity,value,archive,statement=statement)
    Delivery.objects.create(mail=row)
    return row


@dataclass(frozen=True)
class Claim:
    effect_id: uuid.UUID
    token: uuid.UUID


@local_effect('statement-claim',guard=lambda:guard(entry=True),held_result=None)
def claim(*,lease_seconds=10,max_attempts=3):
    guard(entry=True)
    if type(lease_seconds) is not int or not 1<=lease_seconds<=60 or type(max_attempts) is not int or not 1<=max_attempts<=5:fail()
    eligible=Q(state='pending')|Q(state='claimed',lease_until__lte=Now())
    with transaction.atomic(durable=True):
        row=Delivery.objects.select_for_update(skip_locked=True).filter(eligible).order_by('mail_id').first()
        if row is None:return None
        if row.attempts>=max_attempts:
            row.state='held';row.token=None;row.lease_until=None;row.save();return None
        token=uuid.uuid4()
        Delivery.objects.filter(pk=row.pk).update(state='claimed',token=token,
            lease_until=Now()+timedelta(seconds=lease_seconds),attempts=row.attempts+1)
        return Claim(row.pk,token)


@local_effect('statement-capture',guard=lambda:guard(entry=True),held_result=False)
def capture(claimed,archive):
    """Atomic durable fake sink, after claim commit. A lost response can safely reuse identity."""
    guard(entry=True)
    mail=Mail.objects.select_related('statement').get(pk=claimed.effect_id)
    event=mail.statement;actor=event.payload['actor']
    with transaction.atomic(durable=True):
        # Match staff revocation/ledger lock order, then lock delivery. No network I/O.
        credential=StaffCredential.objects.select_for_update().select_related('user').filter(user_id=actor.get('staff_id')).first()
        if credential is None:fail()
        current_user=type(credential.user).objects.select_for_update().get(pk=credential.user_id)
        if (not credential.enabled or not current_user.is_active or not current_user.is_staff
                or str(credential.generation)!=actor.get('credential_generation')):fail()
        grant=SyntheticFulfilment.objects.select_related('acceptance__checkout__owner','acceptance__attempt').get(pk=event.fulfilment_id)
        payment.locked(grant.acceptance.checkout.owner,grant.acceptance.checkout_id)
        grant=SyntheticFulfilment.objects.select_for_update(of=('self',)).select_related('acceptance__checkout','acceptance__attempt').get(pk=grant.pk)
        if not SyntheticSupportStaffGrant.objects.select_for_update().filter(user_id=credential.user_id,fulfilment=grant).exists():fail()
        row=Delivery.objects.select_for_update().filter(pk=claimed.effect_id,state='claimed',token=claimed.token,lease_until__gt=Now()).first()
        if row is None:return False
        fulfilment.retained(grant,grant.acceptance,archive)
        if grant.acceptance.attempt is None or grant.acceptance.attempt.provider_status!='captured' or grant.acceptance.attempt.state!='observed':fail()
        events=list(SyntheticSupportEvent.objects.filter(fulfilment=grant,revision__lte=event.revision).order_by('revision'))
        ledger.replay(grant,events,archive)
        if not events or events[-1].pk!=event.pk or mail.payload!=message(event):fail()
        retained(mail,archive)
        value={'effect_id':str(mail.pk),'mail_sha256':mail.sha256,'statement_sha256':event.sha256,
               'evidence_class':'local-synthetic','effects_authorized':False,'actual_email_sent':False,'status':'durably-captured'}
        prior=Capture.objects.filter(mail=mail).first()
        if prior:
            if prior.payload!=value:fail()
            retained(prior,archive)
        else:persist(Capture,uuid.uuid5(mail.pk,'durable-capture-v1'),value,archive,mail=mail)
        return True


def complete(claimed,archive):
    guard(entry=True)
    with transaction.atomic(durable=True):
        row=Delivery.objects.select_for_update().filter(pk=claimed.effect_id,state='claimed',token=claimed.token,lease_until__gt=Now()).first()
        if row is None:return False
        receipt=Capture.objects.select_related('mail').filter(mail_id=claimed.effect_id).first()
        if receipt is None:fail()
        retained(receipt,archive)
        if receipt.payload.get('mail_sha256')!=receipt.mail.sha256:fail()
        row.state='captured';row.token=None;row.lease_until=None;row.save()
        return True


@local_effect('statement-run',guard=lambda:guard(entry=True),held_result=False)
def execute_once(*,lease_seconds=10,max_attempts=3):
    guard(entry=True)
    root=settings.LOCAL_CHECKOUT_ARCHIVE_ROOT
    if not root:return False
    # Existing configured private root only; never initialize/adopt an archive path.
    with PreparedArchive(Path(root)) as archive:
        owned=claim(lease_seconds=lease_seconds,max_attempts=max_attempts)
        if owned is None:return False
        if capture(owned,archive):complete(owned,archive)
        return True


def status(statement,archive):
    mail=Mail.objects.filter(statement=statement).first()
    if mail is None:return 'not-queued'
    if mail.payload!=message(statement):fail()
    retained(mail,archive)
    row=Delivery.objects.filter(mail=mail).first()
    if row and row.state=='captured':
        receipt=Capture.objects.filter(mail=mail).first()
        if receipt is None:fail()
        retained(receipt,archive)
        if receipt.payload.get('mail_sha256')!=mail.sha256:fail()
    return row.state if row else 'held'
