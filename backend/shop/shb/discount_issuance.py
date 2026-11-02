"""Protected synthetic discount issuance; the raw code appears in one response only."""
import re,secrets,uuid
from datetime import timedelta
from django.db import transaction
from django.views.decorators.debug import sensitive_variables
from shop.catalog import checkout_payment as payment
from shop.payments import attempts,notifications
from . import catalog,checkout,invitations,discount_admin
from .discounts import POLICY,verifier
from .errors import ShbError
from .models import DiscountCode,DiscountIssuanceScope,DiscountIssueGrant,DiscountIssue,DiscountStaffGrant
from .staff_orders import credential

FLAGS=discount_admin.FLAGS
SCOPE_FIELDS=('customer_id','percentage_bps','fpga_allowed','asic_allowed','use_limit','claim_period_days')
CODE_ALPHABET='ABCDEFGHJKLMNPQRSTUVWXYZ23456789'


def register_fixture(*,customer,registered_by,percentage_bps,fpga_allowed=False,asic_allowed=False,
        use_limit=1,claim_period_days=30):
    """Internal explicit fixture, never derived from invitation eligibility or a form."""
    invitations.fixture_guard()
    if (not customer.is_active or customer.is_staff or not registered_by.is_active or not registered_by.is_staff
            or type(percentage_bps) is not int or not 1<=percentage_bps<=9999
            or type(use_limit) is not int or not 1<=use_limit<=100
            or type(claim_period_days) is not int or not 1<=claim_period_days<=365
            or type(fpga_allowed) is not bool or type(asic_allowed) is not bool
            or not (fpga_allowed or asic_allowed)):
        raise ValueError('invalid_fixture_scope')
    return DiscountIssuanceScope.objects.create(customer=customer,registered_by=registered_by,
        percentage_bps=percentage_bps,fpga_allowed=fpga_allowed,asic_allowed=asic_allowed,
        use_limit=use_limit,claim_period_days=claim_period_days)


def scope_snapshot(scope):
    return {'id':str(scope.pk),**{key:getattr(scope,key) for key in SCOPE_FIELDS},
        'registered_by_id':scope.registered_by_id,'created_at':scope.created_at.isoformat(),
        'evidence_class':scope.evidence_class}


def authorized(request,identity):
    credential(request)
    scope=DiscountIssuanceScope.objects.select_for_update().filter(pk=identity).first()
    if scope is None or not DiscountIssueGrant.objects.select_for_update().filter(user=request.user,scope=scope).exists():
        raise ShbError('not_found',404)
    from django.contrib.auth import get_user_model
    customer=get_user_model().objects.select_for_update().get(pk=scope.customer_id)
    if not scope.enabled or not customer.is_active or customer.is_staff:raise ShbError('discount_scope_unavailable',409)
    return scope


def prospective(event):
    return DiscountCode(id=event.pk,customer_id=event.scope.customer_id,
        issuer_id=event.payload['actor']['staff_id'],code_digest=event.payload['code_digest'],
        percentage_bps=event.scope.percentage_bps,fpga_allowed=event.scope.fpga_allowed,
        asic_allowed=event.scope.asic_allowed,use_limit=event.scope.use_limit,
        policy_revision=POLICY,issued_at=event.created_at,starts_at=event.created_at,
        expires_at=event.created_at+timedelta(days=event.scope.claim_period_days))


def retained(event,archive=None):
    value=event.payload;actor=value.get('actor',{});reason=value.get('reason')
    try:
        generation=uuid.UUID(actor['credential_generation']);stamp=actor['mfa_verified_at']
        valid_actor=(set(actor)=={'staff_id','credential_generation','mfa_verified_at'}
            and type(actor['staff_id']) is int and actor['staff_id']>0
            and str(generation)==actor['credential_generation'] and type(stamp) in (int,float)
            and 0<=event.created_at.timestamp()-stamp<=300)
        digest=value['code_digest'];prospect=prospective(event)
        expected={'schema':1,'kind':'shb-discount-issue','scope':scope_snapshot(event.scope),
            'discount':discount_admin.snapshot(prospect),'code_digest':digest,
            'request_id':str(event.request_id),'reason':reason,'actor':actor,**FLAGS}
        valid=(valid_actor and type(reason) is str and 1<=len(reason)<=512 and reason==reason.strip()
            and chr(0) not in reason and type(digest) is str and re.fullmatch('[a-f0-9]{64}',digest)
            and event.pk==uuid.uuid5(event.scope_id,'shb-discount-issue:'+str(event.request_id))
            and value==expected and event.sha256==catalog.digest(value)
            and (event.discount_id is None and event.archive_receipt=={} or event.discount_id==event.pk
                and event.discount.code_digest==digest and discount_admin.snapshot(event.discount)==expected['discount']))
    except (ValueError,KeyError,TypeError,AttributeError):valid=False
    if not valid:raise ShbError('shb_discount_issue_evidence_required',503)
    if archive is not None and event.discount_id is not None:
        payment.recover(archive,event.archive_receipt,event.pk,catalog.canonical(value))


@sensitive_variables()
def prepare(request,identity,value):
    key=checkout.identity(value['request_id']);reason=value['reason']
    if type(reason) is not str or not 1<=len(reason.strip())<=512 or chr(0) in reason:
        raise ShbError('invalid_request',400)
    reason=reason.strip()
    with transaction.atomic(durable=True):
        scope=authorized(request,identity)
        event=DiscountIssue.objects.select_related('scope','discount').filter(scope=scope,request_id=key).first()
        if event:
            if (event.payload['reason']!=reason or event.payload['actor']['staff_id']!=request.user.pk):
                raise ShbError('request_conflict')
            retained(event)
            return event,None
        stamp=attempts.database_now()
        code='SLL-'+''.join(secrets.choice(CODE_ALPHABET) for _ in range(24))
        marker=request.session['shop_staff_mfa']
        event=DiscountIssue(id=uuid.uuid5(scope.pk,'shb-discount-issue:'+str(key)),scope=scope,
            request_id=key,created_at=stamp,payload={'code_digest':verifier(code),
            'actor':{'staff_id':request.user.pk,'credential_generation':marker['generation'],
                'mfa_verified_at':marker['verified_at']}})
        event.payload={**event.payload,'schema':1,'kind':'shb-discount-issue','scope':scope_snapshot(scope),
            'discount':discount_admin.snapshot(prospective(event)),
            'request_id':str(key),'reason':reason,**FLAGS}
        event.sha256=catalog.digest(event.payload);event.save(force_insert=True)
        return event,code


@sensitive_variables()
def record(request,identity,value,archive):
    checkout.guard();event,code=prepare(request,identity,value)
    with transaction.atomic(durable=True):
        authorized(request,identity)
        event=DiscountIssue.objects.select_related('scope','discount').select_for_update(of=('self',)).get(pk=event.pk)
        retained(event,archive)
        if event.discount_id is not None:return event,code
        if event.payload['actor']['credential_generation']!=request.session['shop_staff_mfa']['generation']:
            raise ShbError('discount_issue_credential_changed',409)
        evidence=notifications.evidence(event.pk,event.payload,archive)
        authorized(request,identity)  # Recheck MFA, epoch, assignment and eligibility after archive I/O.
        row=prospective(event);row.save(force_insert=True)
        event.discount=row;event.archive_receipt=evidence['archive_receipt']
        event.save(update_fields=['discount','archive_receipt'])
        DiscountStaffGrant.objects.get_or_create(user=request.user,discount=row)
        return event,code
