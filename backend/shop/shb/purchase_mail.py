"""Ordinary purchase notice on the existing leased worker; fake durable sink only."""
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
import uuid
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.db.models.functions import Now
from shop.access.effects import local_effect
from shop.adapters.evidence_archive import PreparedArchive,manifest
from shop.catalog import checkout as shared,checkout_payment as payment
from . import checkout,paid_orders
from .models import PaidOrder,PurchaseNoticeDelivery as Delivery,PurchaseNoticeCapture as Capture


def guard():
    checkout.guard()
    if settings.MAIL_ADAPTER!='fake':paid_orders.fail()


@dataclass(frozen=True)
class Claim:
    order_id:uuid.UUID
    token:uuid.UUID


@local_effect('shb-notice-claim',guard=guard,held_result=None)
def claim(*,lease_seconds=10,max_attempts=3):
    if type(lease_seconds) is not int or not 1<=lease_seconds<=60 or type(max_attempts) is not int or not 1<=max_attempts<=5:paid_orders.fail()
    eligible=Q(state='pending')|Q(state='claimed',lease_until__lte=Now())
    with transaction.atomic(durable=True):
        row=Delivery.objects.select_for_update(skip_locked=True).filter(eligible).order_by('order_id').first()
        if row is None:return None
        if row.attempts>=max_attempts:
            row.state='held';row.token=None;row.lease_until=None;row.save();return None
        token=uuid.uuid4()
        Delivery.objects.filter(pk=row.pk).update(state='claimed',token=token,
            lease_until=Now()+timedelta(seconds=lease_seconds),attempts=row.attempts+1)
        return Claim(row.pk,token)


def receipt_value(order):
    return {'schema':1,'kind':'shb-purchase-notice-capture','order_id':str(order.pk),
        'order_reference':order.payload['order_reference'],'order_sha256':order.sha256,
        'effect_id':order.payload['notice']['effect_id'],'notice_sha256':shared.digest(order.payload['notice']),
        'recipient':order.payload['notice']['recipient'],'actual_email_sent':False,
        'status':'durably-captured',**paid_orders.FLAGS}


def retained(captured,order,archive):
    if captured.payload!=receipt_value(order) or captured.sha256!=shared.digest(captured.payload):paid_orders.fail()
    payment.recover(archive,captured.archive_receipt,captured.pk,shared.canonical(captured.payload))


@local_effect('shb-notice-capture',guard=guard,held_result=False)
def capture(claimed,archive):
    order=PaidOrder.objects.select_related('acceptance__checkout__owner').get(pk=claimed.order_id)
    with transaction.atomic(durable=True):
        accepted,event=paid_orders.accepted_locked(order.acceptance.checkout.owner,order.acceptance.checkout_id,archive)
        paid_orders.retained(order,accepted,event,archive)
        row=Delivery.objects.select_for_update().filter(pk=claimed.order_id,state='claimed',token=claimed.token,lease_until__gt=Now()).first()
        if row is None:return False
        previous=Capture.objects.filter(order=order).first()
        if previous:retained(previous,order,archive)
        else:
            key=uuid.uuid5(order.pk,'shb-notice-capture-v1');value=receipt_value(order)
            raw=shared.canonical(value);receipt=manifest(archive.publish(key,raw))
            payment.recover(archive,receipt,key,raw)
            Capture.objects.create(id=key,order=order,payload=value,sha256=shared.digest(value),archive_receipt=receipt)
        return True


def complete(claimed,archive):
    guard()
    with transaction.atomic(durable=True):
        row=Delivery.objects.select_for_update().filter(pk=claimed.order_id,state='claimed',token=claimed.token,lease_until__gt=Now()).first()
        if row is None:return False
        captured=Capture.objects.select_related('order').filter(order_id=claimed.order_id).first()
        if captured is None:paid_orders.fail()
        retained(captured,captured.order,archive)
        row.state='captured';row.token=None;row.lease_until=None;row.save()
        return True


@local_effect('shb-notice-run',guard=guard,held_result=False)
def execute_once(*,lease_seconds=10,max_attempts=3):
    root=settings.LOCAL_CHECKOUT_ARCHIVE_ROOT
    if not root:return False
    owned=claim(lease_seconds=lease_seconds,max_attempts=max_attempts)
    if owned is None:return False
    with PreparedArchive(Path(root)) as archive:
        if capture(owned,archive):complete(owned,archive)
    return True
