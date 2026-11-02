"""Archived once-only per-purchase completion on shared synthetic payment records."""
from pathlib import Path
import uuid
from django.conf import settings
from django.db import transaction
from shop.access.effects import local_effect
from shop.adapters.evidence_archive import PreparedArchive,manifest
from shop.catalog import checkout as shared,checkout_payment as payment
from shop.catalog.models import SyntheticCheckoutAcceptance
from shop.payments import attempts,observations
from shop.payments.models import SyntheticPaymentAttempt
from . import checkout
from .models import PaidOrder,DiscountCode,DiscountReservation,PurchaseNoticeDelivery

FLAGS={'evidence_class':'local-synthetic','financial_confirmation':False,'effects_authorized':False}


def fail():raise shared.CheckoutError('shb_paid_order_evidence_required',409)


def accepted_locked(owner,identity,archive):
    """Trusted completion/reconciliation does not depend on invitation lifetime."""
    saved=payment.locked(owner,identity)
    if saved.snapshot.get('release')!='shb-1.1':fail()
    row=SyntheticCheckoutAcceptance.objects.select_for_update(of=('self',)).select_related('checkout','attempt').filter(checkout=saved).first()
    if row is None or row.simulated_accepted_at is None or row.attempt_id is None:fail()
    row.attempt=SyntheticPaymentAttempt.objects.select_for_update().get(pk=row.attempt_id)
    if attempts.request_for(row.attempt)!=payment.request_for(row):fail()
    payment.retained(row,archive)
    events,_=observations.history_locked(row.attempt,archive)
    captures=[event for event in events if event.payload['observation'] and event.payload['observation']['status']=='captured']
    if row.attempt.state!='observed' or not captures:fail()
    return row,captures[0]


def value(row,capture):
    saved=row.checkout.snapshot;purchase=saved['purchase']
    if (purchase['variant_id']!='shb-fpga-10h' or purchase['hours_per_bundle']!=10
            or type(purchase['quantity']) is not int or purchase['quantity']<1
            or purchase['hours_purchased']!=10*purchase['quantity']):fail()
    reference=str(row.pk)
    body={'order_reference':reference,'customer_id':row.checkout.owner_id,'details':saved['details'],
        'purchase':purchase,'accepted_documents':row.payload['review']['fixture_documents'],
        'support_scope':saved['eligibility_reference'],'support_tracking':'manual-outside-shop'}
    return {'schema':1,'kind':'shb-paid-order','order_reference':reference,
        'checkout_id':str(row.checkout_id),'checkout_sha256':row.checkout.sha256,
        'acceptance_id':reference,'acceptance_sha256':row.sha256,
        'accepted_at':row.simulated_accepted_at.isoformat(),'attempt_id':str(row.attempt_id),
        'capture_id':str(capture.pk),'capture_sha256':capture.sha256,**body,
        'notice':{'effect_id':str(uuid.uuid5(row.pk,'shb-purchase-notice-v1')),
            'recipient':'support-order@synthetic.invalid','body':body,'actual_email_sent':False},**FLAGS}


def concession_locked(row,order=None):
    hold=DiscountReservation.objects.filter(checkout_id=row.checkout_id).first()
    expected=row.checkout.snapshot['purchase'].get('discount_policy')
    if bool(hold)!=bool(expected):fail()
    if hold:
        DiscountCode.objects.select_for_update().get(pk=hold.discount_id)
        hold=DiscountReservation.objects.select_for_update().get(pk=hold.pk)
        if (hold.snapshot!=expected or hold.sha256!=shared.digest(expected)
                or hold.state!=('consumed' if order else 'reserved')
                or hold.consumed_order_id!=(order.pk if order else None)):fail()
    return hold


def retained(order,row,capture,archive):
    if (order.acceptance_id!=row.pk or order.capture_id!=capture.pk
            or order.pk!=uuid.uuid5(row.pk,'shb-paid-order-v1')
            or order.payload!=value(row,capture) or order.sha256!=shared.digest(order.payload)):fail()
    payment.recover(archive,order.archive_receipt,order.pk,shared.canonical(order.payload))
    concession_locked(row,order)
    if not PurchaseNoticeDelivery.objects.filter(order=order).exists():fail()


@local_effect('shb-finalize',guard=checkout.guard,error=shared.CheckoutError)
def finalize(owner,identity,archive):
    """Payment, coupon consumption and notice converge atomically; no ledger call."""
    with transaction.atomic(durable=True):
        row,capture=accepted_locked(owner,identity,archive)
        prior=PaidOrder.objects.filter(acceptance=row).first()
        if prior:
            retained(prior,row,capture,archive);return prior
        if row.attempt.provider_status!='captured':fail()
        hold=concession_locked(row)
        payload=value(row,capture);key=uuid.uuid5(row.pk,'shb-paid-order-v1')
        raw=shared.canonical(payload);receipt=manifest(archive.publish(key,raw))
        payment.recover(archive,receipt,key,raw)
        order=PaidOrder.objects.create(id=key,acceptance=row,capture=capture,payload=payload,
            sha256=shared.digest(payload),archive_receipt=receipt)
        if hold:
            hold.state='consumed';hold.consumed_order=order;hold.save(update_fields=['state','consumed_order'])
        PurchaseNoticeDelivery.objects.create(order=order)
        return order


def pending():
    return SyntheticCheckoutAcceptance.objects.filter(checkout__supportcheckout__isnull=False,
        simulated_accepted_at__isnull=False,attempt__state='observed',attempt__provider_status='captured',
        paidorder__isnull=True)


def recover_once():
    """Owned worker repairs observation-commit/completion interruption without charging."""
    row=pending().select_related('checkout__owner').order_by('pk').first()
    if row is None:return False
    with PreparedArchive(Path(settings.LOCAL_CHECKOUT_ARCHIVE_ROOT)) as archive:
        finalize(row.checkout.owner,row.checkout_id,archive)
    return True
