"""Archive-before-release for proved never-dispatched synthetic checkouts."""
from datetime import datetime
from pathlib import Path
import uuid
from django.conf import settings
from django.db import transaction
from django.db.models import Q,DateTimeField
from django.db.models.functions import Cast,Now
from django.db.models.fields.json import KeyTextTransform
from shop.access.effects import local_effect
from shop.adapters.evidence_archive import PreparedArchive,manifest
from shop.catalog import checkout as shared,checkout_payment as payment
from shop.catalog.models import SyntheticCheckoutAcceptance
from shop.payments import attempts
from shop.payments.models import SyntheticPaymentAttempt
from . import checkout,paid_orders
from .models import CheckoutClosure,DiscountReservation


def fail():raise shared.CheckoutError('shb_closure_requires_proved_undispatched_payment',409)


def locked(owner,identity,archive,request=None):
    saved=payment.locked(owner,identity,customer_request=request)
    if saved.snapshot.get('release')!='shb-1.1':fail()
    row=SyntheticCheckoutAcceptance.objects.select_for_update(of=('self',)).select_related('checkout','attempt').filter(checkout=saved).first()
    if row is None or row.simulated_accepted_at is None or hasattr(row,'paidorder'):fail()
    payment.retained(row,archive)
    if row.attempt_id:
        row.attempt=SyntheticPaymentAttempt.objects.select_for_update().get(pk=row.attempt_id)
        if attempts.request_for(row.attempt)!=payment.request_for(row) or row.attempt.state not in ('prepared','cancelled','expired'):fail()
    return row


def deadline(row):
    return row.attempt.expires_at if row.attempt_id else datetime.fromisoformat(row.checkout.snapshot['order_payment_expires_at'])


def verify(closure,row):
    if (closure.acceptance_id!=row.pk or closure.pk!=uuid.uuid5(row.pk,'shb-checkout-closure-v1')
            or closure.sha256!=shared.digest(closure.payload)
            or closure.payload.get('acceptance_sha256')!=row.sha256
            or closure.payload.get('checkout_sha256')!=row.checkout.sha256
            or closure.payload.get('attempt_id')!=(str(row.attempt_id) if row.attempt_id else None)):fail()


def intent(owner,identity,archive,reason,request=None):
    with transaction.atomic(durable=True):
        row=locked(owner,identity,archive,request)
        old=CheckoutClosure.objects.filter(acceptance=row).first()
        if old:verify(old,row);return old
        if reason=='expired' and (deadline(row) is None or attempts.database_now()<deadline(row)):fail()
        value={'schema':1,'kind':'shb-checkout-closure','checkout_id':str(row.checkout_id),
            'checkout_sha256':row.checkout.sha256,'acceptance_id':str(row.pk),'acceptance_sha256':row.sha256,
            'attempt_id':str(row.attempt_id) if row.attempt_id else None,'reason':reason,
            'requested_at':attempts.database_now().isoformat(),'customer_id':row.checkout.owner_id,
            'invitation_id':row.checkout.snapshot['invitation_id'],**paid_orders.FLAGS}
        return CheckoutClosure.objects.create(id=uuid.uuid5(row.pk,'shb-checkout-closure-v1'),acceptance=row,
            payload=value,sha256=shared.digest(value))


def apply(owner,identity,archive,closure):
    raw=shared.canonical(closure.payload);receipt=manifest(archive.publish(closure.pk,raw))
    payment.recover(archive,receipt,closure.pk,raw)
    # Continuation of the saved deliberate action may finish after invite expiry.
    with transaction.atomic(durable=True):
        row=locked(owner,identity,archive)
        current=CheckoutClosure.objects.select_for_update().get(pk=closure.pk);verify(current,row)
        if current.sha256!=closure.sha256:fail()
        if current.applied_at is not None:
            payment.recover(archive,current.archive_receipt,current.pk,shared.canonical(current.payload))
            hold=DiscountReservation.objects.filter(checkout_id=identity).first()
            if hold and (hold.state!='released' or hold.release_closure_id!=current.pk):fail()
            return current
        hold=paid_orders.concession_locked(row)
        if row.attempt_id and row.attempt.state=='prepared':
            at=attempts.database_now()
            expired=row.attempt.expires_at is not None and row.attempt.expires_at<=at
            if current.payload['reason']=='expired' and not expired:fail()
            row.attempt.state='expired' if expired else 'cancelled';row.attempt.stopped_at=at
            row.attempt.save(update_fields=['state','stopped_at'])
        current.archive_receipt=receipt;current.applied_at=attempts.database_now()
        current.save(update_fields=['archive_receipt','applied_at'])
        if hold:
            hold.state='released';hold.release_closure=current;hold.save(update_fields=['state','release_closure'])
        return current


@local_effect('shb-close',guard=checkout.guard,error=shared.CheckoutError)
def cancel(request,owner,identity,archive):
    return apply(owner,identity,archive,intent(owner,identity,archive,'cancelled',request))


@local_effect('shb-close',guard=checkout.guard,error=shared.CheckoutError)
def expire(owner,identity,archive):
    return apply(owner,identity,archive,intent(owner,identity,archive,'expired'))


def pending():return CheckoutClosure.objects.filter(applied_at__isnull=True)


def expired_pending():
    rows=SyntheticCheckoutAcceptance.objects.filter(checkout__supportcheckout__isnull=False,
        simulated_accepted_at__isnull=False,checkoutclosure__isnull=True,paidorder__isnull=True)
    return rows.annotate(order_deadline=Cast(KeyTextTransform('order_payment_expires_at','checkout__snapshot'),DateTimeField())).filter(
        Q(attempt__isnull=True,order_deadline__lte=Now())|Q(attempt__state='expired')|
        Q(attempt__state='prepared',attempt__expires_at__lte=Now()))


def recover_once():
    saved=pending().select_related('acceptance__checkout__owner').order_by('pk').first()
    with PreparedArchive(Path(settings.LOCAL_CHECKOUT_ARCHIVE_ROOT)) as archive:
        if saved:
            apply(saved.acceptance.checkout.owner,saved.acceptance.checkout_id,archive,saved);return True
        row=expired_pending().select_related('checkout__owner').order_by('pk').first()
        if row is None:return False
        expire(row.checkout.owner,row.checkout_id,archive);return True
