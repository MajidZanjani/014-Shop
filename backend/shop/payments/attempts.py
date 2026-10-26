"""Local fixture orchestration. No order, acceptance or financial effects."""
import json
from dataclasses import dataclass,field
from datetime import datetime, timezone
from uuid import UUID
from django.db import connection,transaction,IntegrityError
from shop.adapters.evidence_archive import PreparedArchive,PreparedReceipt,manifest
from . import synthetic_bank
from .bank_contract import BankStart,BankError,validate,correlates
from .models import SyntheticPaymentAttempt,SyntheticAttemptControl


def request_for(row):
    return BankStart(row.merchant,row.reference,row.idempotency_key,row.currency,row.amount_minor)


def payload(row):
    request=request_for(row);validate(request)
    value={'schema':1,'kind':'synthetic-payment-attempt','attempt':str(row.pk),
        'merchant':request.merchant,'reference':str(request.reference),'key':str(request.idempotency_key),
        'currency':request.currency,'amount_minor':request.amount_minor,'evidence_class':'local-synthetic',
        'financial_confirmation':False,'effects_authorized':False}
    if row.expires_at is not None:value['expires_at']=row.expires_at.astimezone(timezone.utc).isoformat()
    return json.dumps(value,sort_keys=True,separators=(',',':')).encode('ascii')


def prepare(request,*,expires_at=None):
    synthetic_bank.guard();validate(request)
    if expires_at is not None:
        if type(expires_at) is not datetime or expires_at.tzinfo is None or expires_at.utcoffset() is None:
            raise BankError('invalid_synthetic_deadline')
        expires_at=expires_at.astimezone(timezone.utc)
    try:
        with transaction.atomic(durable=True):
            row,_=SyntheticPaymentAttempt.objects.get_or_create(merchant=request.merchant,reference=request.reference,
                defaults={'idempotency_key':request.idempotency_key,'currency':request.currency,'amount_minor':request.amount_minor,'expires_at':expires_at})
            if request_for(row)!=request or row.expires_at!=expires_at:raise BankError('synthetic_attempt_conflict')
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


def database_now():
    # Called after row lock acquisition; transaction-start time can precede a wait.
    with connection.cursor() as cursor:
        cursor.execute('SELECT clock_timestamp()')
        return cursor.fetchone()[0]


def expire_locked(row,now):
    if row.state=='prepared' and row.expires_at is not None and row.expires_at<=now:
        row.state='expired';row.stopped_at=now
        row.save(update_fields=['state','stopped_at'])
    return row


def cancel(attempt_id):
    synthetic_bank.guard()
    with transaction.atomic(durable=True):
        row=SyntheticPaymentAttempt.objects.select_for_update().get(pk=attempt_id)
        expire_locked(row,database_now())
        if row.state in ('cancelled','expired'):return row
        if row.state!='prepared':raise BankError('synthetic_attempt_already_dispatched')
        row.state='cancelled';row.stopped_at=database_now()
        row.save(update_fields=['state','stopped_at'])
        return row


def set_hold(attempt_id,*,held,expected_revision,command_id):
    """Retain a fixture control event, never live staff/approval authority."""
    synthetic_bank.guard()
    if (type(held) is not bool or type(expected_revision) is not int
        or not 0<=expected_revision<2147483647 or type(command_id) is not UUID):
        raise BankError('invalid_synthetic_control')
    with transaction.atomic(durable=True):
        row=SyntheticPaymentAttempt.objects.select_for_update().get(pk=attempt_id)
        previous=SyntheticAttemptControl.objects.filter(attempt=row,command_id=command_id).first()
        if previous is not None:
            if previous.held!=held or previous.revision!=expected_revision+1:
                raise BankError('synthetic_control_conflict')
            return previous
        if row.state!='prepared':raise BankError('synthetic_attempt_not_prepared')
        if row.control_revision!=expected_revision:raise BankError('synthetic_control_conflict')
        event=SyntheticAttemptControl.objects.create(attempt=row,revision=expected_revision+1,
            command_id=command_id,held=held)
        row.dispatch_held=held;row.control_revision=event.revision
        row.save(update_fields=['dispatch_held','control_revision'])
        return event


def expire(attempt_id):
    synthetic_bank.guard()
    with transaction.atomic(durable=True):
        row=SyntheticPaymentAttempt.objects.select_for_update().get(pk=attempt_id)
        return expire_locked(row,database_now())


@dataclass(frozen=True)
class RecoveryInspection:
    state: str
    expires_at: datetime | None
    stopped_at: datetime | None
    dispatch_held: bool
    control_revision: int
    expiry_due: bool
    provider_status: str
    lookup_required: bool
    evidence_class: str=field(default='local-synthetic',init=False)
    retry_authorized: bool=field(default=False,init=False)
    financial_confirmation: bool=field(default=False,init=False)
    effects_authorized: bool=field(default=False,init=False)


def inspect(attempt_id):
    """Point-in-time local metadata; no archive/provider I/O or mutations."""
    synthetic_bank.guard()
    with transaction.atomic(durable=True):
        row=SyntheticPaymentAttempt.objects.select_for_update().get(pk=attempt_id)
        now=database_now()
        return RecoveryInspection(row.state,row.expires_at,row.stopped_at,row.dispatch_held,row.control_revision,
            row.state=='prepared' and row.expires_at is not None and row.expires_at<=now,
            row.provider_status,row.state in ('uncertain','observed'))


def dispatch(attempt_id,archive,*,outcome='captured',fault=None):
    synthetic_bank.guard()
    with transaction.atomic(durable=True):
        row=SyntheticPaymentAttempt.objects.select_for_update().get(pk=attempt_id)
        expire_locked(row,database_now())
        if row.state!='prepared' or row.dispatch_held:return row
    if type(archive) is not PreparedArchive:raise BankError('synthetic_archive_required')
    receipt=archive.publish(row.pk,payload(row))
    # Recover actual bytes before committing permission to call the fake provider.
    row.archive_receipt=manifest(receipt);retained(row,archive)
    with transaction.atomic(durable=True):
        current=SyntheticPaymentAttempt.objects.select_for_update().get(pk=row.pk)
        expire_locked(current,database_now())
        if current.state!='prepared' or current.dispatch_held:return current
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
        if row.state not in ('uncertain','observed'):raise BankError('synthetic_attempt_not_dispatched')
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
    if row.state not in ('uncertain','observed'):raise BankError('synthetic_attempt_not_dispatched')
    retained(row,archive)
    return _record(row.pk,synthetic_bank.lookup(row.merchant,row.reference))
