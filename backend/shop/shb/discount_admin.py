"""Exact-scope synthetic staff revocation, with archive-before-state-change."""
import uuid
from django.db import transaction
from shop.catalog import checkout_payment as payment
from shop.payments import attempts,notifications
from . import catalog,checkout
from .errors import ShbError
from .models import DiscountCode,DiscountStaffGrant,DiscountRevocation
from .staff_orders import credential

FLAGS={'evidence_class':'local-synthetic','effects_authorized':False,
    'actual_discount_authority':False,'actual_email_sent':False}


def snapshot(row):
    return {'id':str(row.pk),'customer_id':row.customer_id,'issuer_id':row.issuer_id,
        'percentage_bps':row.percentage_bps,'fpga_allowed':row.fpga_allowed,'asic_allowed':row.asic_allowed,
        'use_limit':row.use_limit,'policy_revision':row.policy_revision,'evidence_class':row.evidence_class,
        'issued_at':row.issued_at.isoformat(),'starts_at':row.starts_at.isoformat(),'expires_at':row.expires_at.isoformat()}


def authorized(request,identity):
    credential(request)
    grant=DiscountStaffGrant.objects.select_for_update().filter(user=request.user,discount_id=identity).first()
    if grant is None:raise ShbError('not_found',404)
    row=DiscountCode.objects.select_for_update().get(pk=identity)
    return row


def retained(event,archive):
    value=event.payload
    actor=value.get('actor',{})
    try:
        generation=uuid.UUID(actor['credential_generation'])
        stamp=actor['mfa_verified_at']
        valid_actor=(set(actor)=={'staff_id','credential_generation','mfa_verified_at'}
            and type(actor['staff_id']) is int and actor['staff_id']>0
            and str(generation)==actor['credential_generation'] and type(stamp) in (int,float)
            and 0<=event.revoked_at.timestamp()-stamp<=300)
    except (ValueError,KeyError,TypeError,AttributeError):valid_actor=False
    expected={'schema':1,'kind':'shb-discount-revocation','discount':snapshot(event.discount),
        'request_id':str(event.request_id),'revoked_at':event.revoked_at.isoformat(),
        'actor':actor,'reason':value.get('reason'),**FLAGS}
    reason=value.get('reason')
    if (not valid_actor or type(reason) is not str or not 1<=len(reason)<=512 or reason!=reason.strip()
            or value!=expected or event.pk!=uuid.uuid5(event.discount_id,'shb-discount-revocation-v1')
            or event.sha256!=catalog.digest(value) or event.discount.revoked_at!=event.revoked_at):
        raise ShbError('shb_discount_revocation_evidence_required',503)
    payment.recover(archive,event.archive_receipt,event.pk,catalog.canonical(value))


def record(request,identity,value,archive):
    checkout.guard()
    key=checkout.identity(value['request_id']);reason=value['reason']
    if type(reason) is not str or not 1<=len(reason.strip())<=512 or chr(0) in reason:raise ShbError('invalid_request',400)
    reason=reason.strip()
    with transaction.atomic(durable=True):
        row=authorized(request,identity)
        previous=DiscountRevocation.objects.select_related('discount').filter(discount=row).first()
        if previous:
            retained(previous,archive)
            if (previous.request_id!=key or previous.payload['reason']!=reason
                    or previous.payload['actor']['staff_id']!=request.user.pk):raise ShbError('request_conflict')
            return previous,False
        if row.revoked_at is not None:raise ShbError('discount_already_revoked')
        stamp=attempts.database_now();identity=uuid.uuid5(row.pk,'shb-discount-revocation-v1')
        marker=request.session['shop_staff_mfa']
        value={'schema':1,'kind':'shb-discount-revocation','discount':snapshot(row),
            'request_id':str(key),'revoked_at':stamp.isoformat(),'reason':reason,
            'actor':{'staff_id':request.user.pk,'credential_generation':marker['generation'],
                'mfa_verified_at':marker['verified_at']},**FLAGS}
        evidence=notifications.evidence(identity,value,archive)
        authorized(request,row.pk)  # Recheck current MFA, epoch and exact grant after I/O.
        event=DiscountRevocation.objects.create(id=identity,discount=row,request_id=key,revoked_at=stamp,**evidence)
        row.revoked_at=stamp;row.save(update_fields=['revoked_at'])
        return event,True
