"""Ordinary customer/request mail on the existing worker; durable fake capture only."""
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
import uuid

from django.conf import settings
from django.db import connection, transaction
from django.db.models import Q
from django.db.models.functions import Now

from shop.access.effects import local_effect
from shop.adapters.evidence_archive import PreparedArchive, manifest
from shop.catalog import checkout_payment as payment
from . import catalog, checkout
from .errors import ShbError
from .models import TransactionNotice as Notice, TransactionNoticeDelivery as Delivery, TransactionNoticeCapture as Capture

FLAGS = {'evidence_class':'local-synthetic','financial_confirmation':False,'effects_authorized':False}


def guard():
    checkout.guard()
    if settings.MAIL_ADAPTER != 'fake': raise ShbError('synthetic_transaction_notice_required',503)


def value(event, source):
    if event == 'request-received':
        row=source; customer=row.invitation.customer_id; recipient=row.payload['details']['contact_email']
        sha=row.sha256
        body={'reference':str(row.pk),'status':'Request received; no charge or engineering availability reserved.'}
    elif event in ('request-question','request-declined'):
        row=source.request; customer=row.invitation.customer_id; recipient=row.payload['details']['contact_email']
        sha=row.sha256
        body={'reference':str(row.pk),'review_version':source.review.version,'message':source.message,
            'status':'More information requested.' if event=='request-question' else 'Request declined.'}
    elif event == 'offer-issued':
        row=source.request; customer=row.invitation.customer_id; recipient=row.payload['details']['contact_email']
        sha=source.sha256
        body={'reference':str(source.pk),'request_reference':str(row.pk),'status':'Reviewed ASIC offer issued.',
            'path':'/purchase/shb/offer/'+str(source.pk)+'/','expires_at':source.payload['expires_at']}
    elif event == 'request-closed':
        row=source.request; customer=row.invitation.customer_id; recipient=row.payload['details']['contact_email']
        sha=source.sha256
        body={'reference':str(row.pk),'offer_reference':source.payload['offer_id'],'action':source.payload['action'],
            'status':{'withdraw':'Request withdrawn.','expire':'Unaccepted offer expired.',
                'replace':'Old offer closed for fresh review and reissue.'}[source.payload['action']]}
    elif event == 'checkout-closed':
        row=source.acceptance.checkout; customer=row.owner_id; recipient=row.snapshot['details']['contact_email']
        sha=source.sha256
        body={'reference':str(source.acceptance_id),'action':source.payload['reason'],
            'status':'Unpaid checkout cancelled or expired.'}
    elif event == 'purchase-confirmed':
        customer=source.payload['customer_id']; recipient=source.payload['details']['contact_email']; sha=source.sha256
        p=source.payload['purchase']
        body={'reference':source.payload['order_reference'],'status':'Accepted paid purchase recorded.',
            **{key:p[key] for key in ('variant_label','quantity','hours_per_bundle','hours_purchased','total_minor','currency')},
            'support_tracking':'manual-outside-shop'}
    else: raise ShbError('invalid_transaction_notice')
    return {'schema':1,'kind':'shb-transaction-notice','event':event,'source_id':str(source.pk),'source_sha256':sha,
        'customer_id':customer,'recipient':recipient,'recipient_scope':'this-transaction-only',
        'named_identity_verified':False,'actual_email_sent':False,'body':body,**FLAGS}


def queue(event, source):
    guard()
    if not connection.in_atomic_block: raise ShbError('transaction_notice_requires_source_transaction')
    payload=value(event,source); key=uuid.uuid5(uuid.NAMESPACE_URL,'sll-shb-transaction:'+event+':'+str(source.pk))
    saved,created=Notice.objects.get_or_create(id=key,defaults={'event':event,'source_id':str(source.pk),
        'payload':payload,'sha256':catalog.digest(payload)})
    if saved.payload != payload or saved.sha256 != catalog.digest(payload): raise ShbError('transaction_notice_changed')
    if created: Delivery.objects.create(notice=saved)
    return saved


@dataclass(frozen=True)
class Claim:
    notice_id: uuid.UUID
    token: uuid.UUID


@local_effect('shb-notice-claim',guard=guard,held_result=None)
def claim(*,lease_seconds=10,max_attempts=3):
    if type(lease_seconds) is not int or not 1<=lease_seconds<=60 or type(max_attempts) is not int or not 1<=max_attempts<=5:
        raise ShbError('invalid_transaction_notice_bounds')
    with transaction.atomic(durable=True):
        row=Delivery.objects.select_for_update(skip_locked=True).filter(
            Q(state='pending')|Q(state='claimed',lease_until__lte=Now())).order_by('notice_id').first()
        if row is None: return None
        if row.attempts >= max_attempts:
            row.state='held'; row.token=None; row.lease_until=None; row.save(); return None
        token=uuid.uuid4()
        Delivery.objects.filter(pk=row.pk).update(state='claimed',token=token,
            lease_until=Now()+timedelta(seconds=lease_seconds),attempts=row.attempts+1)
        return Claim(row.pk,token)


def owned(claimed):
    return Delivery.objects.select_for_update().filter(pk=claimed.notice_id,state='claimed',
        token=claimed.token,lease_until__gt=Now()).first()


def proof(notice):
    if catalog.digest(notice.payload) != notice.sha256: raise ShbError('transaction_notice_changed')
    return {'schema':1,'kind':'shb-transaction-notice-capture','notice_id':str(notice.pk),
        'notice_sha256':notice.sha256,'recipient':notice.payload['recipient'],
        'status':'durably-captured','actual_email_sent':False,**FLAGS}


def retained(saved,notice,archive):
    if (saved.pk != uuid.uuid5(notice.pk,'shb-transaction-capture-v1') or saved.notice_id != notice.pk
            or saved.payload != proof(notice) or saved.sha256 != catalog.digest(saved.payload)):
        raise ShbError('transaction_notice_capture_changed')
    payment.recover(archive,saved.notice_archive_receipt,notice.pk,catalog.canonical(notice.payload))
    payment.recover(archive,saved.archive_receipt,saved.pk,catalog.canonical(saved.payload))


@local_effect('shb-notice-capture',guard=guard,held_result=False)
def capture(claimed,archive):
    with transaction.atomic(durable=True):
        if owned(claimed) is None: return False
        notice=Notice.objects.get(pk=claimed.notice_id)
        saved=Capture.objects.filter(notice=notice).first()
        if saved: retained(saved,notice,archive); return True
    # Archive stable envelope/proof outside claim locks. Expired owners cannot commit.
    raw=catalog.canonical(notice.payload); receipt=manifest(archive.publish(notice.pk,raw))
    payment.recover(archive,receipt,notice.pk,raw)
    payload=proof(notice); key=uuid.uuid5(notice.pk,'shb-transaction-capture-v1')
    raw=catalog.canonical(payload); capture_receipt=manifest(archive.publish(key,raw))
    payment.recover(archive,capture_receipt,key,raw)
    with transaction.atomic(durable=True):
        if owned(claimed) is None: return False
        saved=Capture.objects.filter(notice=notice).first()
        if saved: retained(saved,notice,archive)
        else: Capture.objects.create(id=key,notice=notice,payload=payload,sha256=catalog.digest(payload),
            notice_archive_receipt=receipt,archive_receipt=capture_receipt)
        return True


def complete(claimed,archive):
    guard()
    with transaction.atomic(durable=True):
        row=owned(claimed)
        if row is None: return False
        saved=Capture.objects.select_related('notice').filter(notice_id=claimed.notice_id).first()
        if saved is None: raise ShbError('transaction_notice_capture_required')
        retained(saved,saved.notice,archive)
        row.state='captured'; row.token=None; row.lease_until=None; row.save(); return True


@local_effect('shb-notice-run',guard=guard,held_result=False)
def execute_once(*,lease_seconds=10,max_attempts=3):
    if not settings.LOCAL_CHECKOUT_ARCHIVE_ROOT: return False
    claimed=claim(lease_seconds=lease_seconds,max_attempts=max_attempts)
    if claimed is None: return False
    with PreparedArchive(Path(settings.LOCAL_CHECKOUT_ARCHIVE_ROOT)) as archive:
        if capture(claimed,archive): complete(claimed,archive)
    return True
