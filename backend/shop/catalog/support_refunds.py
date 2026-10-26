"""Archived synthetic refund review only; no credit hold, balance mutation or bank call."""
import uuid
from django.db import transaction
from shop.adapters.evidence_archive import manifest
from shop.payments import synthetic_bank
from . import checkout,checkout_payment as payment,fulfilment,support_ledger as ledger
from .models import (SyntheticFulfilment,SyntheticSupportEvent,SyntheticSupportRefundCase as Case,
    SyntheticSupportRefundReview as Review,SyntheticSupportRefundStaffGrant as StaffGrant)

DECISIONS=('needs_information','declined','ready_for_financial_review')
PENDING=('amount_minor','currency','eligible_seconds','refund_policy','seller_approval','bank_operation','credit_document')


def fail(code='support_refund_mismatch',status=409):raise checkout.CheckoutError(code,status)


def grant_locked(owner,checkout_id,archive):
    payment.locked(owner,checkout_id)
    grant=SyntheticFulfilment.objects.select_for_update(of=('self',)).select_related('acceptance__checkout','acceptance__attempt').filter(acceptance__checkout_id=checkout_id).first()
    if grant is None:fail('not_found',404)
    if grant.acceptance.attempt is None or grant.acceptance.attempt.state!='observed' or grant.acceptance.attempt.provider_status!='captured':fail('captured_payment_required',422)
    fulfilment.retained(grant,grant.acceptance,archive)
    events=list(SyntheticSupportEvent.objects.filter(fulfilment=grant).order_by('revision'))
    state=ledger.replay(grant,events,archive)
    if grant.support_seconds<=0:fail('support_grant_required',422)
    return grant,credit(state)


def credit(state):
    return {key:state[key] for key in ('grant_id','revision','sha256','granted_seconds','available_seconds','reserved_seconds','spent_seconds')}


def retained(row,identity,archive):
    if (row.sha256!=checkout.digest(row.payload) or row.payload.get('identity')!=str(identity)
            or row.payload.get('evidence_class')!='local-synthetic' or row.payload.get('effects_authorized') is not False):fail()
    payment.recover(archive,row.archive_receipt,identity,checkout.canonical(row.payload))


def persist(model,evidence_id,value,archive,**fields):
    body=checkout.canonical(value);receipt=manifest(archive.publish(evidence_id,body))
    payment.recover(archive,receipt,evidence_id,body)
    return model.objects.create(payload=value,sha256=checkout.digest(value),archive_receipt=receipt,**fields)


def capture(owner,checkout_id,request_id,seconds,archive):
    synthetic_bank.guard()
    if type(request_id) is not uuid.UUID or type(seconds) is not int or not 1<=seconds<=ledger.MAX_SECONDS:fail('invalid_refund_request',400)
    with transaction.atomic(durable=True):
        grant,state=grant_locked(owner,checkout_id,archive)
        prior=Case.objects.filter(fulfilment=grant,request_id=request_id).first()
        if prior:
            retained(prior,prior.identity,archive)
            if prior.payload['requested_seconds']!=seconds:fail('refund_request_conflict')
            return prior
        if seconds>grant.support_seconds:fail('refund_request_exceeds_grant',422)
        if Case.objects.filter(fulfilment=grant).count()>=1000:fail('refund_case_limit',422)
        identity=uuid.uuid5(grant.pk,'support-refund-'+str(request_id))
        value={'identity':str(identity),'request_id':str(request_id),'requested_seconds':seconds,'credit':state,
               'grant_sha256':grant.sha256,'review_required':True,'financial_policy':dict.fromkeys(PENDING),
               'evidence_class':'local-synthetic','effects_authorized':False,'refund_authorized':False}
        return persist(Case,identity,value,archive,identity=identity,fulfilment=grant,request_id=request_id)


def staff_locked(request,case=None):
    ledger.authorize(request)
    if case is not None and not StaffGrant.objects.select_for_update().filter(user=request.user,case=case).exists():fail('refund_scope_required',403)
    # The support ledger's unscoped authorization locks/rechecks recent staff identity.
    return {'staff_id':request.user.pk,'credential_generation':request.session['shop_staff_mfa']['generation'],
            'mfa_verified_at':request.session['shop_staff_mfa']['verified_at']}


def case_locked(owner,checkout_id,identity,archive):
    grant,state=grant_locked(owner,checkout_id,archive)
    row=Case.objects.select_for_update().filter(identity=identity,fulfilment=grant).first()
    if row is None:fail('not_found',404)
    retained(row,row.identity,archive)
    if (row.payload.get('grant_sha256')!=grant.sha256 or row.payload.get('request_id')!=str(row.request_id)
            or row.payload.get('credit',{}).get('grant_id')!=str(grant.pk)):fail()
    return row,state


def replay(case,archive):
    rows=list(Review.objects.filter(case=case).order_by('revision'));previous=case.sha256
    for revision,row in enumerate(rows,1):
        retained(row,row.pk,archive);value=row.payload
        if (row.revision!=revision or value.get('revision')!=revision or value.get('case_sha256')!=case.sha256
                or value.get('previous_sha256')!=previous or value.get('request_id')!=str(row.request_id)
                or value.get('command',{}).get('expected_revision')!=revision-1
                or value['command'].get('decision') not in DECISIONS
                or value['command'].get('ledger_revision')!=value.get('credit',{}).get('revision')
                or value.get('financial_policy')!=dict.fromkeys(PENDING) or value.get('refund_authorized') is not False):fail()
        previous=row.sha256
    return rows,previous


def review(request,owner,checkout_id,identity,request_id,expected_revision,ledger_revision,decision,archive):
    synthetic_bank.guard()
    if (type(request_id) is not uuid.UUID or type(expected_revision) is not int or not 0<=expected_revision<1000
            or type(ledger_revision) is not int or not 0<=ledger_revision<=10000 or decision not in DECISIONS):fail('invalid_refund_review',400)
    command={'expected_revision':expected_revision,'ledger_revision':ledger_revision,'decision':decision}
    with transaction.atomic(durable=True):
        staff_locked(request)
        if not StaffGrant.objects.filter(user=request.user,case__identity=identity).exists():fail('not_found',404)
        case,state=case_locked(owner,checkout_id,identity,archive);actor=staff_locked(request,case)
        rows,previous=replay(case,archive)
        prior=next((row for row in rows if row.request_id==request_id),None)
        if prior:
            if prior.payload['command']!=command or prior.payload['actor']['staff_id']!=actor['staff_id']:fail('refund_review_conflict')
            return prior
        if len(rows)!=expected_revision:fail('refund_review_revision_changed')
        if state['revision']!=ledger_revision:fail('refund_ledger_revision_changed')
        event_id=uuid.uuid5(case.identity,'review-'+str(request_id))
        value={'identity':str(event_id),'request_id':str(request_id),'revision':len(rows)+1,'command':command,
               'case_sha256':case.sha256,'previous_sha256':previous,'credit':state,'actor':actor,
               'financial_policy':dict.fromkeys(PENDING),'refund_authorized':False,
               'evidence_class':'local-synthetic','effects_authorized':False}
        row=persist(Review,event_id,value,archive,id=event_id,case=case,request_id=request_id,revision=len(rows)+1)
        staff_locked(request,case)
        return row


def summary(case,state,archive,before=None):
    rows,_=replay(case,archive);latest=rows[-1] if rows else None
    visible=[row for row in reversed(rows) if before is None or row.revision<before]
    return {'case_id':str(case.identity),'checkout_id':str(case.fulfilment.acceptance.checkout_id),
            'requested_seconds':case.payload['requested_seconds'],'captured_credit':case.payload['credit'],'current_credit':state,
            'revision':len(rows),'decision':latest.payload['command']['decision'] if latest else 'awaiting_review',
            'review_current':bool(latest and latest.payload['credit']==state),
            'consumed_support_present':state['spent_seconds']>0,'reserved_support_present':state['reserved_seconds']>0,
            'request_exceeds_available':case.payload['requested_seconds']>state['available_seconds'],
            'financial_policy':dict.fromkeys(PENDING),'refund_authorized':False,'balance_hold_created':False,
            'effects_authorized':False,'evidence_class':'local-synthetic',
            'history':[{'revision':row.revision,'decision':row.payload['command']['decision'],'credit':row.payload['credit']} for row in visible[:20]],
            'next_before':visible[19].revision if len(visible)>20 else None}
