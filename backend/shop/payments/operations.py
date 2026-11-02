"""Explicit staff-scoped synthetic capture/full-refund lifecycle; no actual finance authority."""
from dataclasses import asdict
import uuid
from django.db import transaction
from shop.access.effects import local_effect
from shop.catalog import checkout,checkout_payment as payment,support_ledger as ledger
from shop.catalog.models import SyntheticCheckoutAcceptance as Acceptance
from . import synthetic_bank,attempts,observations,notifications
from .bank_contract import BankMutation,BankMutationResult,BankError,correlates,validate_mutation
from .models import (SyntheticPaymentStaffGrant as StaffGrant,SyntheticPaymentOperation as Operation,
    SyntheticOperationDispatch as Dispatch,SyntheticOperationResult as Result,SyntheticPaymentAttempt as Attempt)

FLAGS={'evidence_class':'local-synthetic','financial_confirmation':False,'effects_authorized':False,
       'actual_financial_authority':False,'rights_or_support_mutated':False}
POLICY=dict.fromkeys(('actual_capture_authority','refund_eligibility','seller_approval','tax_credit_document','provider_qualification'))


def fail():raise checkout.CheckoutError('payment_operation_hold',409)


def staff_locked(request,accepted_id,kind):
    from shop.access.recovery import current_session_epoch
    if not current_session_epoch(request,lock=True):raise checkout.CheckoutError('recent_staff_mfa_required',403)
    ledger.authorize(request)
    if kind not in ('capture','refund') or not StaffGrant.objects.select_for_update().filter(user=request.user,acceptance_id=accepted_id,kind=kind).exists():
        raise checkout.CheckoutError('not_found',404)
    return {'staff_id':request.user.pk,'credential_generation':request.session['shop_staff_mfa']['generation'],
            'mfa_verified_at':request.session['shop_staff_mfa']['verified_at']}


def scope_locked(request,accepted_id,kind,archive):
    actor=staff_locked(request,accepted_id,kind)
    accepted=Acceptance.objects.select_related('checkout__owner').get(pk=accepted_id)
    payment.locked(accepted.checkout.owner,accepted.checkout_id)
    accepted=Acceptance.objects.select_for_update().select_related('checkout').get(pk=accepted_id)
    payment.retained(accepted,archive)
    if accepted.simulated_accepted_at is None or accepted.attempt_id is None:fail()
    attempt=Attempt.objects.select_for_update().get(pk=accepted.attempt_id)
    if attempts.request_for(attempt)!=payment.request_for(accepted) or attempt.state!='observed':fail()
    attempts.retained(attempt,archive);observations.history_locked(attempt,archive)
    return accepted,attempt,actor


def mutation(row):
    value=row.payload['mutation']
    try:result=BankMutation(value['merchant'],uuid.UUID(value['reference']),uuid.UUID(value['provider_operation_id']),
            uuid.UUID(value['idempotency_key']),value['currency'],value['amount_minor'],value['kind'])
    except (KeyError,ValueError,TypeError):fail()
    validate_mutation(result)
    return result


def mutation_value(value):
    raw=asdict(value)
    for key in ('reference','provider_operation_id','idempotency_key'):raw[key]=str(raw[key])
    return raw


def retained(row,accepted,attempt,archive):
    value=row.payload;notifications.retained(row,archive);command=mutation(row)
    if (row.pk!=uuid.uuid5(attempt.pk,'operation-'+row.kind) or row.attempt_id!=attempt.pk or row.acceptance_id!=accepted.pk
            or value.get('identity')!=str(row.pk) or value.get('request_id')!=str(row.request_id)
            or value.get('acceptance_sha256')!=accepted.sha256 or value.get('financial_policy')!=POLICY
            or any(value.get(key)!=flag for key,flag in FLAGS.items())
            or (command.merchant,command.reference,command.provider_operation_id,command.currency,command.amount_minor,command.kind)!=
               (attempt.merchant,attempt.reference,attempt.provider_operation_id,attempt.currency,attempt.amount_minor,row.kind)
            or command.idempotency_key!=uuid.uuid5(row.pk,'provider-key')):fail()
    from shop.shb.refunds import verify_operation
    verify_operation(row,accepted,archive)
    return command


def prepare(request,accepted_id,kind,request_id,archive):
    synthetic_bank.guard()
    if type(request_id) is not uuid.UUID or type(accepted_id) is not uuid.UUID:fail()
    with transaction.atomic(durable=True):
        accepted,attempt,actor=scope_locked(request,accepted_id,kind,archive)
        prior=Operation.objects.filter(attempt=attempt,kind=kind).first()
        if prior:
            retained(prior,accepted,attempt,archive)
            if prior.request_id!=request_id or prior.payload['actor']['staff_id']!=actor['staff_id']:fail()
            return prior
        if Operation.objects.filter(attempt=attempt,request_id=request_id).exists():fail()
        if attempt.provider_status!=('authorized' if kind=='capture' else 'captured'):fail()
        key=uuid.uuid5(attempt.pk,'operation-'+kind)
        command=BankMutation(attempt.merchant,attempt.reference,attempt.provider_operation_id,uuid.uuid5(key,'provider-key'),
                             attempt.currency,attempt.amount_minor,kind)
        value={'identity':str(key),'request_id':str(request_id),'acceptance_sha256':accepted.sha256,
               'mutation':mutation_value(command),'actor':actor,'financial_policy':POLICY,**FLAGS}
        if kind=='refund' and accepted.checkout.snapshot.get('release')=='shb-1.1':
            from shop.shb.refunds import required_reference
            from shop.shb.models import PaidOrderGrant
            if not PaidOrderGrant.objects.select_for_update().filter(user=request.user,order__acceptance=accepted).exists():
                raise checkout.CheckoutError('not_found',404)
            value['shb_refund_review']=required_reference(accepted,archive)
        row=Operation.objects.create(id=key,attempt=attempt,acceptance=accepted,kind=kind,request_id=request_id,
                                    **notifications.evidence(key,value,archive))
        Dispatch.objects.create(operation=row);staff_locked(request,accepted_id,kind)
        return row


def locked(request,identity,archive):
    # No raw reference lookup or scope inferred from money values.
    row=Operation.objects.get(pk=identity)
    accepted,attempt,_=scope_locked(request,row.acceptance_id,row.kind,archive)
    command=retained(row,accepted,attempt,archive)
    delivery=Dispatch.objects.select_for_update().get(operation=row)
    return row,attempt,delivery,command


@local_effect('finance-dispatch',guard=synthetic_bank.guard,error=BankError)
def dispatch(request,identity,archive,*,fault=None):
    synthetic_bank.guard()
    with transaction.atomic(durable=True):
        row,attempt,delivery,command=locked(request,identity,archive)
        if delivery.state!='prepared':return row
        from shop.shb.refunds import verify_operation
        verify_operation(row,Acceptance.objects.select_related('checkout').get(pk=row.acceptance_id),archive,dispatch=True)
        if attempt.provider_status!=('authorized' if row.kind=='capture' else 'captured'):fail()
        delivery.state='uncertain';delivery.save(update_fields=['state'])
        staff_locked(request,row.acceptance_id,row.kind)
    # The durable one-way claim is permission for exactly one call, outside DB locks.
    result=synthetic_bank.mutate(command,fault=fault)
    return record(request,identity,result,archive)


def record(request,identity,result,archive):
    synthetic_bank.guard()
    with transaction.atomic(durable=True):
        row,attempt,delivery,command=locked(request,identity,archive)
        if delivery.state not in ('uncertain','observed'):fail()
        if result is None:return row
        expected='captured' if row.kind=='capture' else 'refunded'
        if (type(result) is not BankMutationResult or result.request!=command or not correlates(attempts.request_for(attempt),result.observation)
                or result.observation.provider_operation_id!=command.provider_operation_id or result.observation.status!=expected):fail()
        value={'intent_sha256':row.sha256,'observation':observations.normalized(result.observation),'financial_policy':POLICY,**FLAGS}
        result_id=uuid.uuid5(row.pk,'operation-result-v1');prior=Result.objects.filter(operation=row).first()
        if prior:
            if prior.payload!=value or prior.sha256!=checkout.digest(value):fail()
            payment.recover(archive,prior.archive_receipt,result_id,checkout.canonical(value))
        else:Result.objects.create(operation=row,**notifications.evidence(result_id,value,archive))
        observations.record_locked(attempt,result.observation,archive)
        attempts._apply_locked(attempt,result.observation)
        delivery.state='observed';delivery.save(update_fields=['state']);staff_locked(request,row.acceptance_id,row.kind)
        return row


def reconcile(request,identity,archive):
    synthetic_bank.guard()
    with transaction.atomic(durable=True):
        row,_,delivery,command=locked(request,identity,archive)
        if delivery.state not in ('uncertain','observed'):fail()
    # A miss never releases the original claim or permits a blind second mutation.
    return record(request,identity,synthetic_bank.lookup_mutation(command),archive)


def inspect(request,identity,archive):
    synthetic_bank.guard()
    with transaction.atomic(durable=True):
        row,attempt,delivery,command=locked(request,identity,archive)
        result=Result.objects.filter(operation=row).first()
        if delivery.state=='observed' and result is None:fail()
        if result:retained_result(row,command,result,archive)
        return {'state':delivery.state,'kind':row.kind,'lookup_required':delivery.state=='uncertain',
                'status':attempt.provider_status,'financial_policy':POLICY.copy(),'retry_authorized':False,**FLAGS}


def retained_result(row,command,result,archive):
    expected={'intent_sha256':row.sha256,'observation':{'provider_operation_id':str(command.provider_operation_id),
        'merchant':command.merchant,'reference':str(command.reference),'currency':command.currency,
        'amount_minor':command.amount_minor,'status':'captured' if row.kind=='capture' else 'refunded'},'financial_policy':POLICY,**FLAGS}
    if result.operation_id!=row.pk or result.payload!=expected or result.sha256!=checkout.digest(expected):fail()
    payment.recover(archive,result.archive_receipt,uuid.uuid5(row.pk,'operation-result-v1'),checkout.canonical(expected))
