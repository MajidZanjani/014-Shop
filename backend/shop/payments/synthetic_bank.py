"""Durable fake-provider result/lost-response simulator, without commerce effects."""
from django.conf import settings
from django.db import connection,transaction,IntegrityError
from .bank_contract import BankError,BankObservation,SyntheticCapabilities,identity,validate
from .models import SyntheticBankOperation,SyntheticBankKey,SYNTHETIC_STATUSES

CAPABILITIES=SyntheticCapabilities()


def guard():
    if (settings.SHOP_ENV not in ('local','synthetic') or settings.PAYMENT_ADAPTER!='fake'
        or settings.LIVE_PAYMENTS_ENABLED):raise BankError('synthetic_bank_unavailable')
    if connection.in_atomic_block or not connection.get_autocommit():raise BankError('bank_transaction_active')


def observe(row):
    return BankObservation(row.pk,row.merchant,row.reference,row.currency,row.amount_minor,row.status)


def start(request,*,outcome='captured',fault=None):
    guard();validate(request)
    if type(outcome) is not str or outcome not in SYNTHETIC_STATUSES or fault not in (None,'before_commit','after_commit'):
        raise BankError('invalid_synthetic_scenario')
    if fault=='before_commit':raise TimeoutError('synthetic_bank_timeout')
    try:
        with transaction.atomic(durable=True):
            row,_=SyntheticBankOperation.objects.get_or_create(merchant=request.merchant,reference=request.reference,
                defaults={'currency':request.currency,'amount_minor':request.amount_minor,'status':outcome})
            if (row.currency,row.amount_minor,row.status)!=(request.currency,request.amount_minor,outcome):
                raise BankError('synthetic_bank_conflict')
            key,_=SyntheticBankKey.objects.get_or_create(pk=request.idempotency_key,defaults={'operation':row})
            if key.operation_id!=row.pk:raise BankError('synthetic_bank_conflict')
            result=observe(row)
    except IntegrityError:raise BankError('synthetic_bank_conflict') from None
    # The fake-provider transaction has actually committed before response loss.
    if fault=='after_commit':raise TimeoutError('synthetic_bank_timeout')
    return result


def lookup(merchant,reference):
    guard();identity(merchant,reference)
    row=SyntheticBankOperation.objects.filter(merchant=merchant,reference=reference).first()
    return observe(row) if row else None
