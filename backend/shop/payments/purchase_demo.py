"""Owned local purchase rehearsal; no actual order, acceptance, credits or delivery."""
import hashlib,json,uuid
from django.contrib.auth import get_user_model
from django.db import transaction,IntegrityError
from shop.access.models import CustomerIdentity
from shop.adapters.evidence_archive import PreparedArchive,PreparedReceipt,manifest
from shop.catalog.models import ConfigurationDraft
from shop.catalog.rules import CATALOG
from shop.catalog.purchase_policy import quote
from . import attempts,synthetic_bank
from .bank_contract import BankStart,BankError
from .models import SyntheticPurchase,SyntheticCreditReservation,SyntheticPaymentAttempt


def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')


def owner_locked(owner):
    user=get_user_model().objects.select_for_update().filter(pk=owner.pk,is_active=True,is_staff=False,is_superuser=False).first()
    if user is None or CustomerIdentity.objects.select_for_update().filter(user=user,verified_at__isnull=False).first() is None:
        raise BankError('synthetic_purchase_unavailable')
    return user


def read_locked(identity,owner):
    owner_locked(owner)
    row=SyntheticPurchase.objects.select_for_update().filter(pk=identity,owner_id=owner.pk).first()
    if row is None:raise BankError('synthetic_purchase_unavailable')
    return row


def prepare(owner,request_id,*,draft_id=None,offer_id=None,support_packages=None):
    synthetic_bank.guard()
    if type(request_id) is not uuid.UUID:raise BankError('invalid_synthetic_purchase')
    with transaction.atomic(durable=True):
        owner_locked(owner)
        if draft_id is not None:
            draft=ConfigurationDraft.objects.select_for_update().filter(pk=draft_id,owner_id=owner.pk).first()
            if draft is None or draft.revision!=CATALOG['revision'] or support_packages is not None:
                raise BankError('synthetic_purchase_unavailable')
            evaluated=quote(draft.configuration,offer_id)
            if evaluated['status']!='synthetic_purchasable':raise BankError('synthetic_offer_unavailable')
            snapshot=evaluated['snapshot']|{'kind':'ip','catalog_revision':draft.revision,'product_id':CATALOG['product_id']}
            reference=draft.pk
        else:
            if offer_id is not None or type(support_packages) is not int or not 1<=support_packages<=1000000:
                raise BankError('invalid_synthetic_purchase')
            draft=None;reference=uuid.uuid5(request_id,str(owner.pk))
            snapshot={'schema':1,'kind':'support','product_id':CATALOG['support_product_id'],
                'support_scope':CATALOG['product_id'],'support_packages':support_packages,'total_minor':support_packages*2345,
                'currency':'EUR','evidence_class':'local-synthetic','financial_confirmation':False,'effects_authorized':False}
    bank_request=BankStart('synthetic-purchase',reference,uuid.uuid5(reference,'purchase-key'),'EUR',snapshot['total_minor'])
    attempt=attempts.prepare(bank_request)
    try:
        with transaction.atomic(durable=True):
            owner_locked(owner)
            if draft is not None:
                current=ConfigurationDraft.objects.select_for_update().filter(pk=draft.pk,owner_id=owner.pk).first()
                if current is None or current.configuration!=draft.configuration or current.revision!=draft.revision:
                    raise BankError('synthetic_purchase_unavailable')
                row,_=SyntheticPurchase.objects.get_or_create(draft=current,defaults={'owner':owner,'request_id':request_id,'attempt':attempt,'snapshot':snapshot})
            else:
                row,_=SyntheticPurchase.objects.get_or_create(owner=owner,request_id=request_id,defaults={'attempt':attempt,'snapshot':snapshot})
            if row.owner_id!=owner.pk or row.snapshot!=snapshot or row.attempt_id!=attempt.pk:raise BankError('synthetic_purchase_conflict')
            return row
    except IntegrityError:raise BankError('synthetic_purchase_conflict') from None


def retained(row,archive):
    if type(archive) is not PreparedArchive:raise BankError('synthetic_archive_required')
    try:
        raw=row.archive_receipt
        receipt=PreparedReceipt(uuid.UUID(raw['evidence_id']),raw['sha256'],raw['size'])
        if manifest(receipt)!=raw or receipt.evidence_id!=row.pk:raise ValueError()
    except (KeyError,ValueError,TypeError):raise BankError('synthetic_archive_mismatch') from None
    if archive.recover(receipt)!=canonical(row.snapshot):raise BankError('synthetic_archive_mismatch')


def _record_funding(identity,owner,attempt):
    synthetic_bank.guard()
    with transaction.atomic(durable=True):
        row=read_locked(identity,owner)
        if row.attempt_id!=attempt.pk:raise BankError('synthetic_purchase_conflict')
        attempt=SyntheticPaymentAttempt.objects.select_for_update().get(pk=row.attempt_id)
        if attempt.state=='observed' and attempt.provider_status=='captured' and not row.simulated_funded:
            row.simulated_funded=True
            row.simulated_credit_seconds=row.snapshot['support_packages']*36000
            row.simulated_entitlements=1 if row.snapshot['kind']=='ip' else 0
            row.save(update_fields=['simulated_funded','simulated_credit_seconds','simulated_entitlements'])
        return row


def fund(identity,owner,archive,*,fault=None):
    synthetic_bank.guard()
    with transaction.atomic(durable=True):row=read_locked(identity,owner)
    if type(archive) is not PreparedArchive:raise BankError('synthetic_archive_required')
    receipt=archive.publish(row.pk,canonical(row.snapshot))
    row.archive_receipt=manifest(receipt);retained(row,archive)
    with transaction.atomic(durable=True):
        current=read_locked(row.pk,owner)
        if current.snapshot!=row.snapshot:raise BankError('synthetic_purchase_conflict')
        current.archive_receipt=row.archive_receipt;current.save(update_fields=['archive_receipt'])
    result=attempts.dispatch(row.attempt_id,archive,fault=fault)
    return _record_funding(row.pk,owner,result)


def reconcile(identity,owner,archive):
    synthetic_bank.guard()
    with transaction.atomic(durable=True):row=read_locked(identity,owner)
    retained(row,archive)
    return _record_funding(row.pk,owner,attempts.reconcile(row.attempt_id,archive))


def deliver(identity,owner,archive,stage):
    synthetic_bank.guard()
    if stage not in ('initial','reference'):raise BankError('invalid_synthetic_delivery')
    with transaction.atomic(durable=True):
        row=read_locked(identity,owner)
        if (not row.simulated_funded or row.snapshot['kind']!='ip'
            or (stage=='reference' and (not row.initial_delivered or not row.snapshot['later_reference_design']))):
            raise BankError('synthetic_delivery_unavailable')
    retained(row,archive)
    if type(archive) is not PreparedArchive:raise BankError('synthetic_archive_required')
    evidence_id=uuid.uuid5(row.pk,'synthetic-delivery-'+stage)
    body=canonical({'purchase':str(row.pk),'stage':stage,'snapshot_sha256':hashlib.sha256(canonical(row.snapshot)).hexdigest(),
        'evidence_class':'local-synthetic','simulated_completion':True,'effects_authorized':False})
    receipt=archive.publish(evidence_id,body)
    if archive.recover(receipt)!=body:raise BankError('synthetic_archive_mismatch')
    with transaction.atomic(durable=True):
        current=read_locked(row.pk,owner)
        if current.snapshot!=row.snapshot or not current.simulated_funded:raise BankError('synthetic_delivery_unavailable')
        field='initial_delivered' if stage=='initial' else 'reference_delivered'
        setattr(current,field,True)
        fields=[field]
        if stage=='initial' and not current.snapshot['later_reference_design']:
            current.reference_delivered=True;fields.append('reference_delivered')
        current.save(update_fields=fields)
        return current


def reserve_credit(identity,owner,request_id,seconds):
    """Recorded same-owner SLL fixture allocation; no automatic cross-project pooling."""
    synthetic_bank.guard()
    if type(request_id) is not uuid.UUID or type(seconds) is not int or not 1<=seconds<=9223372036854775807:
        raise BankError('invalid_synthetic_reservation')
    with transaction.atomic(durable=True):
        row=read_locked(identity,owner)
        previous=SyntheticCreditReservation.objects.filter(purchase=row,request_id=request_id).first()
        if previous:
            if previous.seconds!=seconds:raise BankError('synthetic_reservation_conflict')
            return previous
        if not row.simulated_funded or seconds>row.simulated_credit_seconds-row.reserved_seconds:
            raise BankError('synthetic_credit_unavailable')
        reservation=SyntheticCreditReservation.objects.create(purchase=row,request_id=request_id,seconds=seconds)
        row.reserved_seconds+=seconds;row.save(update_fields=['reserved_seconds'])
        return reservation
