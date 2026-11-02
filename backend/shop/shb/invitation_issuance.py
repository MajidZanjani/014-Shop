"""Protected synthetic issuance from established scope; one response holds the bearer."""
import hashlib,re,secrets,uuid
from django.db import transaction
from django.views.decorators.debug import sensitive_variables
from shop.catalog import checkout_payment as payment
from shop.payments import attempts,notifications
from . import catalog,checkout,invitations,invitation_admin
from .errors import ShbError
from .models import Invitation,InvitationIssuanceScope,InvitationIssueGrant,InvitationIssue,InvitationStaffGrant
from .staff_orders import credential

FLAGS=invitation_admin.FLAGS
SCOPE_FIELDS=('customer_id','company_name','project_reference','eligibility_reference','fpga_eligible','asic_allowed')


def register_fixture(*,customer,registered_by,company_name,eligibility_reference,
        project_reference='',fpga_eligible=False,asic_allowed=False):
    """Internal explicit fixture, never derived from a customer-entered form."""
    invitations.fixture_guard()
    if (not customer.is_active or customer.is_staff or not registered_by.is_active or not registered_by.is_staff
            or type(fpga_eligible) is not bool or type(asic_allowed) is not bool or not (fpga_eligible or asic_allowed)
            or any(type(value) is not str or chr(0) in value or len(value)>maximum or (required and not value.strip())
                for value,maximum,required in ((company_name,200,True),(project_reference,160,False),(eligibility_reference,160,True)))):
        raise ValueError('invalid_fixture_scope')
    return InvitationIssuanceScope.objects.create(customer=customer,registered_by=registered_by,
        company_name=company_name,project_reference=project_reference,eligibility_reference=eligibility_reference,
        fpga_eligible=fpga_eligible,asic_allowed=asic_allowed)


def scope_snapshot(scope):
    return {'id':str(scope.pk),**{key:getattr(scope,key) for key in SCOPE_FIELDS},
        'registered_by_id':scope.registered_by_id,'created_at':scope.created_at.isoformat(),
        'evidence_class':scope.evidence_class}


def authorized(request,identity):
    credential(request)
    scope=InvitationIssuanceScope.objects.select_for_update().filter(pk=identity).first()
    if scope is None or not InvitationIssueGrant.objects.select_for_update().filter(user=request.user,scope=scope).exists():
        raise ShbError('not_found',404)
    # A copied company name, revoke grant or historical review is not eligibility.
    from django.contrib.auth import get_user_model
    customer=get_user_model().objects.select_for_update().get(pk=scope.customer_id)
    if not scope.enabled or not customer.is_active or customer.is_staff:raise ShbError('invitation_scope_unavailable',409)
    return scope


def replacement(scope,identity,stamp):
    if identity is None:return None
    row=Invitation.objects.select_for_update().filter(pk=identity).first()
    if row is None or any(getattr(row,key)!=getattr(scope,key) for key in SCOPE_FIELDS):raise ShbError('not_found',404)
    if row.expires_at>stamp and (row.revoked_at is None or row.revoked_at>stamp):raise ShbError('replacement_requires_inactive_invitation')
    return row


def prospective(event):
    return Invitation(id=event.pk,customer_id=event.scope.customer_id,
        issuer_id=event.payload['actor']['staff_id'],token_digest=event.payload['token_digest'],
        **{key:getattr(event.scope,key) for key in SCOPE_FIELDS if key!='customer_id'},
        created_at=event.created_at,expires_at=invitations.six_month_expiry(event.created_at))


def retained(event,archive=None):
    value=event.payload;actor=value.get('actor',{});reason=value.get('reason')
    try:
        generation=uuid.UUID(actor['credential_generation']);stamp=actor['mfa_verified_at']
        valid_actor=(set(actor)=={'staff_id','credential_generation','mfa_verified_at'}
            and type(actor['staff_id']) is int and actor['staff_id']>0
            and str(generation)==actor['credential_generation'] and type(stamp) in (int,float)
            and 0<=event.created_at.timestamp()-stamp<=300)
        digest=value['token_digest'];invite=prospective(event)
        prior=event.replaces
        original=None if prior is None else {**invitation_admin.snapshot(prior),'revoked_at':prior.revoked_at.isoformat() if prior.revoked_at else None}
        expected={'schema':1,'kind':'shb-invitation-issue','scope':scope_snapshot(event.scope),
            'invitation':invitation_admin.snapshot(invite),'token_digest':digest,'replacement':original,
            'request_id':str(event.request_id),'reason':reason,'actor':actor,**FLAGS}
        valid=(valid_actor and type(reason) is str and 1<=len(reason)<=512 and reason==reason.strip()
            and chr(0) not in reason and type(digest) is str and re.fullmatch('[a-f0-9]{64}',digest)
            and event.pk==uuid.uuid5(event.scope_id,'shb-invitation-issue:'+str(event.request_id))
            and value==expected and event.sha256==catalog.digest(value)
            and (prior is None or all(getattr(prior,key)==getattr(event.scope,key) for key in SCOPE_FIELDS)
                and (prior.expires_at<=event.created_at or prior.revoked_at is not None and prior.revoked_at<=event.created_at))
            and (event.invitation_id is None and event.archive_receipt=={} or event.invitation_id==event.pk
                and event.invitation.token_digest==digest and invitation_admin.snapshot(event.invitation)==expected['invitation']))
    except (ValueError,KeyError,TypeError,AttributeError):valid=False
    if not valid:raise ShbError('shb_invitation_issue_evidence_required',503)
    if archive is not None and event.invitation_id is not None:
        payment.recover(archive,event.archive_receipt,event.pk,catalog.canonical(value))


@sensitive_variables()
def prepare(request,identity,value):
    key=checkout.identity(value['request_id']);reason=value['reason'];replaces=value['replaces']
    if type(reason) is not str or not 1<=len(reason.strip())<=512 or chr(0) in reason or type(replaces) is not str:
        raise ShbError('invalid_request',400)
    reason=reason.strip();replaces=checkout.identity(replaces) if replaces else None
    with transaction.atomic(durable=True):
        scope=authorized(request,identity)
        event=InvitationIssue.objects.select_related('scope','replaces','invitation').filter(scope=scope,request_id=key).first()
        if event:
            if (event.payload['reason']!=reason or event.replaces_id!=replaces
                    or event.payload['actor']['staff_id']!=request.user.pk):raise ShbError('request_conflict')
            retained(event)
            return event,None
        stamp=attempts.database_now();prior=replacement(scope,replaces,stamp)
        if prior and InvitationIssue.objects.filter(replaces=prior).exists():raise ShbError('replacement_already_prepared')
        token=secrets.token_urlsafe(32);marker=request.session['shop_staff_mfa']
        event=InvitationIssue(id=uuid.uuid5(scope.pk,'shb-invitation-issue:'+str(key)),scope=scope,
            request_id=key,replaces=prior,created_at=stamp,payload={'token_digest':hashlib.sha256(token.encode('ascii')).hexdigest(),
            'actor':{'staff_id':request.user.pk,'credential_generation':marker['generation'],'mfa_verified_at':marker['verified_at']}})
        event.payload={**event.payload,'schema':1,'kind':'shb-invitation-issue','scope':scope_snapshot(scope),
            'invitation':invitation_admin.snapshot(prospective(event)),
            'replacement':None if prior is None else {**invitation_admin.snapshot(prior),'revoked_at':prior.revoked_at.isoformat() if prior.revoked_at else None},
            'request_id':str(key),'reason':reason,**FLAGS}
        event.sha256=catalog.digest(event.payload);event.save(force_insert=True)
        return event,token


@sensitive_variables()
def record(request,identity,value,archive):
    checkout.guard();event,token=prepare(request,identity,value)
    with transaction.atomic(durable=True):
        scope=authorized(request,identity)
        event=InvitationIssue.objects.select_related('scope','replaces','invitation').select_for_update(of=('self',)).get(pk=event.pk)
        retained(event,archive)
        if event.invitation_id is not None:return event,token
        if event.payload['actor']['credential_generation']!=request.session['shop_staff_mfa']['generation']:
            raise ShbError('invitation_issue_credential_changed',409)
        replacement(scope,event.replaces_id,event.created_at)
        evidence=notifications.evidence(event.pk,event.payload,archive)
        authorized(request,identity)  # Recheck MFA, epoch, assignment and eligibility after archive I/O.
        row=prospective(event);row.save(force_insert=True)
        event.invitation=row;event.archive_receipt=evidence['archive_receipt'];event.save(update_fields=['invitation','archive_receipt'])
        InvitationStaffGrant.objects.get_or_create(user=request.user,invitation=row)
        return event,token
