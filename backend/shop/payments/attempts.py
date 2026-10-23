"""Local fixture orchestration. No order, acceptance or financial effects."""
import json
from uuid import UUID
from django.db import transaction,IntegrityError
from shop.adapters.evidence_archive import PreparedArchive,PreparedReceipt,manifest
from . import synthetic_bank
from .bank_contract import BankStart,BankError,validate,correlates
from .models import SyntheticPaymentAttempt


def request_for(row):
    return BankStart(row.merchant,row.reference,row.idempotency_key,row.currency,row.amount_minor)


def payload(row):
    request=request_for(row);validate(request)
    return json.dumps({'schema':1,'kind':'synthetic-payment-attempt','attempt':str(row.pk),
        'merchant':request.merchant,'reference':str(request.reference),'key':str(request.idempotency_key),
        'currency':request.currency,'amount_minor':request.amount_minor,'evidence_class':'local-synthetic',
        'financial_confirmation':False,'effects_authorized':False},sort_keys=True,separators=(',',':')).encode('ascii')


def prepare(request):
    synthetic_bank.guard();validate(request)
    try:
        with transaction.atomic(durable=True):
            row,_=SyntheticPaymentAttempt.objects.get_or_create(merchant=request.merchant,reference=request.reference,
                defaults={'idempotency_key':request.idempotency_key,'currency':request.currency,'amount_minor':request.amount_minor})
            if request_for(row)!=request:raise BankError('synthetic_attempt_conflict')
            return row
    except IntegrityError:raise BankError('synthetic_attempt_conflict') from None


def retained(row,archive):
    if type(archive) is not PreparedArchive:raise BankError('synthetic_archive_required')
    receipt=row.archive_receipt
    try:
        value=PreparedReceipt(UUID(receipt['evidence_id']),receipt['sha256'],receipt['size'])
        if manifest(value)!=receipt or value.evidence_id!=row.pk:raise ValueError()
    except (KeyError,ValueError,TypeError):raise BankError('synthetic_archive_mismatch') from None
    if archive.recover(value)!=payload(row):raise BankError('synthetic_archive_mismatch')


def dispatch(attempt_id,archive,*,outcome='captured',fault=None):
    synthetic_bank.guard()
    row=SyntheticPaymentAttempt.objects.get(pk=attempt_id)
    if row.state!='prepared':return row
    if type(archive) is not PreparedArchive:raise BankError('synthetic_archive_required')
    receipt=archive.publish(row.pk,payload(row))
    # Recover actual bytes before committing permission to call the fake provider.
    row.archive_receipt=manifest(receipt);retained(row,archive)
    with transaction.atomic(durable=True):
        current=SyntheticPaymentAttempt.objects.select_for_update().get(pk=row.pk)
        if current.state!='prepared':return current
        if payload(current)!=payload(row):raise BankError('synthetic_attempt_conflict')
        current.archive_receipt=row.archive_receipt;current.state='uncertain'
        current.save(update_fields=['archive_receipt','state'])
    # A crash at any point after the claim requires lookup, never another start.
    observation=synthetic_bank.start(request_for(current),outcome=outcome,fault=fault)
    return _record(current.pk,observation)


def _record(attempt_id,observation):
    synthetic_bank.guard()
    with transaction.atomic(durable=True):
        row=SyntheticPaymentAttempt.objects.select_for_update().get(pk=attempt_id)
        if row.state=='prepared':raise BankError('synthetic_attempt_not_dispatched')
        if observation is None:return row
        if not correlates(request_for(row),observation):raise BankError('synthetic_observation_mismatch')
        if row.state=='observed' and (row.provider_operation_id,row.provider_status)!=(observation.provider_operation_id,observation.status):
            raise BankError('synthetic_observation_conflict')
        row.state='observed';row.provider_operation_id=observation.provider_operation_id;row.provider_status=observation.status
        row.save(update_fields=['state','provider_operation_id','provider_status'])
        return row


def reconcile(attempt_id,archive):
    synthetic_bank.guard()
    row=SyntheticPaymentAttempt.objects.get(pk=attempt_id)
    if row.state=='prepared':raise BankError('synthetic_attempt_not_dispatched')
    retained(row,archive)
    return _record(row.pk,synthetic_bank.lookup(row.merchant,row.reference))
