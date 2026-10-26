"""Exact-pair local investigation of independent captures. No refund or fulfilment API."""
import hashlib
import uuid
from django.db import transaction
from shop.catalog import checkout,checkout_payment as payment,support_ledger as ledger
from shop.catalog.models import SyntheticCheckoutAcceptance as Acceptance
from . import attempts,synthetic_bank,notifications
from .bank_contract import correlates
from .models import (SyntheticPaymentAttempt as Attempt,SyntheticPurchase,
    SyntheticOverpaymentStaffGrant as StaffGrant,SyntheticOverpaymentCase as Case,SyntheticOverpaymentReview as Review)

DECISIONS=('needs_information','not_attributable','ready_for_financial_review')
PENDING=dict.fromkeys(('actual_attribution','refund_eligibility','refund_amount_minor','refund_currency','seller_approval','bank_operation','credit_document'))
FLAGS={'evidence_class':'local-synthetic','financial_confirmation':False,'effects_authorized':False,
       'refund_authorized':False,'additional_fulfilment_authorized':False}


def fail():raise checkout.CheckoutError('overpayment_review_hold',409)


def authorize(request,acceptance_id,extra_id):
    ledger.authorize(request)
    grant=StaffGrant.objects.select_for_update().filter(user=request.user,acceptance_id=acceptance_id,extra_attempt_id=extra_id).first()
    if grant is None:raise checkout.CheckoutError('not_found',404)
    return {'staff_id':request.user.pk,'credential_generation':request.session['shop_staff_mfa']['generation'],
            'mfa_verified_at':request.session['shop_staff_mfa']['verified_at'],'pair_grant_id':grant.pk}


def locked(request,acceptance_id,extra_id,archive):
    actor=authorize(request,acceptance_id,extra_id)
    accepted=Acceptance.objects.select_related('checkout').get(pk=acceptance_id)
    payment.locked(accepted.checkout.owner,accepted.checkout_id)
    accepted=Acceptance.objects.select_for_update().select_related('checkout').get(pk=acceptance_id)
    payment.retained(accepted,archive)
    if accepted.attempt_id is None or accepted.attempt_id==extra_id:fail()
    rows=list(Attempt.objects.select_for_update().filter(pk__in=[accepted.attempt_id,extra_id]).order_by('id'))
    if len(rows)!=2:fail()
    indexed={row.pk:row for row in rows};original=indexed[accepted.attempt_id];extra=indexed[extra_id]
    if (Acceptance.objects.filter(attempt=extra).exists() or SyntheticPurchase.objects.filter(attempt=extra).exists()
            or Case.objects.filter(extra_attempt=extra).exclude(acceptance=accepted).exists()):fail()
    if attempts.request_for(original)!=payment.request_for(accepted):fail()
    for row in (original,extra):
        attempts.retained(row,archive)
        if row.state!='observed' or row.provider_status!='captured':fail()
    if ((original.merchant,original.currency,original.amount_minor)!=(extra.merchant,extra.currency,extra.amount_minor)
            or original.reference==extra.reference or original.provider_operation_id==extra.provider_operation_id):fail()
    return accepted,original,extra,actor


def capture(request,acceptance_id,extra_id,archive):
    notifications.guard()
    if type(acceptance_id) is not uuid.UUID or type(extra_id) is not uuid.UUID:fail()
    # Exact pair authorization and retained scope before lookup; no row lock spans adapter I/O.
    with transaction.atomic(durable=True):
        accepted,original,extra,_=locked(request,acceptance_id,extra_id,archive)
        requests=[attempts.request_for(row) for row in (original,extra)]
    observed=[synthetic_bank.lookup(item.merchant,item.reference) for item in requests]
    for item,value in zip(requests,observed):
        if not correlates(item,value) or value.status!='captured':fail()
    with transaction.atomic(durable=True):
        accepted,original,extra,actor=locked(request,acceptance_id,extra_id,archive)
        if requests!=[attempts.request_for(row) for row in (original,extra)]:fail()
        for row,value in zip((original,extra),observed):
            if row.provider_operation_id!=value.provider_operation_id:fail()
        identity=uuid.uuid5(extra.pk,'overpayment-case-v1')
        facts=[{'attempt_id':str(row.pk),'attempt_sha256':hashlib.sha256(attempts.payload(row)).hexdigest(),
                'observation':notifications.observation_value(value)} for row,value in zip((original,extra),observed)]
        prior=Case.objects.filter(extra_attempt=extra).first()
        if prior:
            verify(prior,accepted,original,extra,archive)
            if prior.payload['captures']!=facts:fail()
            return prior
        if Case.objects.filter(acceptance=accepted).count()>=1000:fail()
        value={'case_id':str(identity),'acceptance_id':str(accepted.pk),'acceptance_sha256':accepted.sha256,
               'captures':facts,'assignment':actor,'attribution':'explicit_local_pair_requires_financial_review',
               'financial_policy':PENDING,**FLAGS}
        result=Case.objects.create(id=identity,acceptance=accepted,extra_attempt=extra,**notifications.evidence(identity,value,archive))
        authorize(request,acceptance_id,extra_id)
        return result


def verify(case,accepted,original,extra,archive):
    notifications.retained(case,archive);value=case.payload
    if (case.pk!=uuid.uuid5(extra.pk,'overpayment-case-v1') or case.acceptance_id!=accepted.pk or case.extra_attempt_id!=extra.pk
            or value.get('case_id')!=str(case.pk) or value.get('acceptance_id')!=str(accepted.pk)
            or value.get('acceptance_sha256')!=accepted.sha256 or value.get('financial_policy')!=PENDING
            or any(value.get(key)!=flag for key,flag in FLAGS.items())):fail()
    facts=value.get('captures')
    if not isinstance(facts,list) or len(facts)!=2:fail()
    for fact,row in zip(facts,(original,extra)):
        expected={'attempt_id':str(row.pk),'attempt_sha256':hashlib.sha256(attempts.payload(row)).hexdigest(),
                  'observation':{'provider_operation_id':str(row.provider_operation_id),'merchant':row.merchant,
                    'reference':str(row.reference),'currency':row.currency,'amount_minor':row.amount_minor,'status':'captured'}}
        if fact!=expected:fail()


def history(case,archive):
    rows=list(Review.objects.filter(case=case).order_by('revision'));previous=case.sha256
    for revision,row in enumerate(rows,1):
        notifications.retained(row,archive);value=row.payload
        if (row.revision!=revision or value.get('revision')!=revision or value.get('review_id')!=str(row.pk)
                or row.pk!=uuid.uuid5(case.pk,'review-'+str(row.request_id)) or value.get('request_id')!=str(row.request_id)
                or value.get('case_sha256')!=case.sha256 or value.get('previous_sha256')!=previous
                or value.get('command',{}).get('expected_revision')!=revision-1
                or value['command'].get('decision') not in DECISIONS or value.get('financial_policy')!=PENDING
                or any(value.get(key)!=flag for key,flag in FLAGS.items())):fail()
        previous=row.sha256
    return rows,previous


def review(request,acceptance_id,extra_id,request_id,expected_revision,decision,archive):
    notifications.guard()
    if (type(request_id) is not uuid.UUID or type(expected_revision) is not int
            or not 0<=expected_revision<1000 or decision not in DECISIONS):fail()
    with transaction.atomic(durable=True):
        accepted,original,extra,actor=locked(request,acceptance_id,extra_id,archive)
        case=Case.objects.select_for_update().filter(acceptance=accepted,extra_attempt=extra).first()
        if case is None:fail()
        verify(case,accepted,original,extra,archive);rows,previous=history(case,archive)
        command={'expected_revision':expected_revision,'decision':decision}
        prior=next((row for row in rows if row.request_id==request_id),None)
        if prior:
            if prior.payload['command']!=command or prior.payload['actor']['staff_id']!=actor['staff_id']:fail()
            return prior
        if len(rows)!=expected_revision:fail()
        identity=uuid.uuid5(case.pk,'review-'+str(request_id))
        value={'review_id':str(identity),'request_id':str(request_id),'revision':len(rows)+1,'command':command,
               'case_sha256':case.sha256,'previous_sha256':previous,'actor':actor,'financial_policy':PENDING,**FLAGS}
        result=Review.objects.create(id=identity,case=case,request_id=request_id,revision=len(rows)+1,
                                     **notifications.evidence(identity,value,archive))
        authorize(request,acceptance_id,extra_id)
        return result


def inspect(request,acceptance_id,extra_id,archive,before=None):
    notifications.guard()
    with transaction.atomic(durable=True):
        accepted,original,extra,_=locked(request,acceptance_id,extra_id,archive)
        case=Case.objects.filter(acceptance=accepted,extra_attempt=extra).first()
        if case is None:fail()
        verify(case,accepted,original,extra,archive);rows,_=history(case,archive)
        visible=[row for row in reversed(rows) if before is None or row.revision<before]
        authorize(request,acceptance_id,extra_id)
        return {'captures':[{'amount_minor':row.amount_minor,'currency':row.currency,'status':'captured'} for row in (original,extra)],
                'history':[{'revision':row.revision,'decision':row.payload['command']['decision']} for row in visible[:20]],
                'next_before':visible[19].revision if len(visible)>20 else None,
                'revision':len(rows),'decision':rows[-1].payload['command']['decision'] if rows else 'awaiting_review',
                'capture_count':2,'financial_policy':PENDING.copy(),**FLAGS}
