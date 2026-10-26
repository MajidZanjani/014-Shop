"""Durable fake-provider result/lost-response simulator, without commerce effects."""
from django.conf import settings
from django.db import connection,transaction,IntegrityError
from .bank_contract import BankError,BankObservation,SyntheticCapabilities,identity,validate,BankMutationResult,validate_mutation
from .models import SyntheticBankOperation,SyntheticBankKey,SYNTHETIC_STATUSES,SyntheticBankTransition

CAPABILITIES=SyntheticCapabilities()


def guard():
    if (settings.SHOP_ENV not in ('local','synthetic') or settings.PAYMENT_ADAPTER!='fake'
        or settings.LIVE_PAYMENTS_ENABLED):raise BankError('synthetic_bank_unavailable')
    if connection.in_atomic_block or not connection.get_autocommit():raise BankError('bank_transaction_active')


def observe(row):
    return BankObservation(row.pk,row.merchant,row.reference,row.currency,row.amount_minor,row.status)


def start(request,*,outcome='captured',fault=None):
    guard();validate(request)
    if type(outcome) is not str or outcome not in ('pending','authorized','captured','declined') or fault not in (None,'before_commit','after_commit'):
        raise BankError('invalid_synthetic_scenario')
    if fault=='before_commit':raise TimeoutError('synthetic_bank_timeout')
    try:
        with transaction.atomic(durable=True):
            row,_=SyntheticBankOperation.objects.get_or_create(merchant=request.merchant,reference=request.reference,
                defaults={'currency':request.currency,'amount_minor':request.amount_minor,'status':outcome})
            row=SyntheticBankOperation.objects.select_for_update().get(pk=row.pk)
            if (row.currency,row.amount_minor)!=(request.currency,request.amount_minor):raise BankError('synthetic_bank_conflict')
            prior=SyntheticBankKey.objects.filter(pk=request.idempotency_key).first()
            if (prior.status if prior and prior.status else row.status)!=outcome:raise BankError('synthetic_bank_conflict')
            key,_=SyntheticBankKey.objects.get_or_create(pk=request.idempotency_key,defaults={'operation':row,'status':outcome})
            if key.operation_id!=row.pk:raise BankError('synthetic_bank_conflict')
            result=BankObservation(row.pk,row.merchant,row.reference,row.currency,row.amount_minor,key.status or row.status)
    except IntegrityError:raise BankError('synthetic_bank_conflict') from None
    # The fake-provider transaction has actually committed before response loss.
    if fault=='after_commit':raise TimeoutError('synthetic_bank_timeout')
    return result


def lookup(merchant,reference):
    guard();identity(merchant,reference)
    row=SyntheticBankOperation.objects.filter(merchant=merchant,reference=reference).first()
    return observe(row) if row else None


def mutation_result(row,request):
    operation=row.operation
    return BankMutationResult(request,BankObservation(operation.pk,operation.merchant,operation.reference,
        row.currency,row.amount_minor,row.after))


def mutate(request,*,fault=None):
    guard();validate_mutation(request)
    if fault not in (None,'before_commit','after_commit'):raise BankError('invalid_synthetic_scenario')
    if fault=='before_commit':raise TimeoutError('synthetic_bank_timeout')
    with transaction.atomic(durable=True):
        row=SyntheticBankOperation.objects.select_for_update().filter(merchant=request.merchant,reference=request.reference).first()
        if row is None or (row.pk,row.currency,row.amount_minor)!=(request.provider_operation_id,request.currency,request.amount_minor):raise BankError('synthetic_bank_conflict')
        prior=SyntheticBankTransition.objects.filter(pk=request.idempotency_key).first()
        if prior:
            if (prior.operation_id,prior.kind,prior.currency,prior.amount_minor)!=(row.pk,request.kind,request.currency,request.amount_minor):raise BankError('synthetic_bank_conflict')
            result=mutation_result(prior,request)
        else:
            before,after=('authorized','captured') if request.kind=='capture' else ('captured','refunded')
            if row.status!=before or SyntheticBankTransition.objects.filter(operation=row,kind=request.kind).exists():raise BankError('synthetic_bank_conflict')
            event=SyntheticBankTransition.objects.create(id=request.idempotency_key,operation=row,kind=request.kind,
                before=before,after=after,currency=row.currency,amount_minor=row.amount_minor)
            row.status=after;row.save(update_fields=['status']);result=mutation_result(event,request)
    if fault=='after_commit':raise TimeoutError('synthetic_bank_timeout')
    return result


def lookup_mutation(request):
    guard();validate_mutation(request)
    row=SyntheticBankTransition.objects.select_related('operation').filter(pk=request.idempotency_key).first()
    if row is None:return None
    if ((row.operation.merchant,row.operation.reference,row.operation_id,row.currency,row.amount_minor,row.kind)!=
            (request.merchant,request.reference,request.provider_operation_id,request.currency,request.amount_minor,request.kind)):
        raise BankError('synthetic_bank_conflict')
    return mutation_result(row,request)
