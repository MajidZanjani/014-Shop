"""Explicit local authorization/revocation and locked source checks."""
from dataclasses import dataclass
from datetime import datetime,timedelta,timezone
import hashlib
import uuid
from django.db import connection,transaction
from django.db.models import Max
from .models import RequestEnvelope,RequestArchiveIntent,ArchiveWorkAuthorization,ArchiveWorkRevocation,ArchivePreparedVerification
from .request_envelope import prepare_request_envelope,EnvelopeError

@dataclass(frozen=True)
class AuthorizationReference:
    authorization_id: uuid.UUID
    generation: int
    created: bool


def db_now():
    with connection.cursor() as cursor:
        cursor.execute('SELECT statement_timestamp()')
        return cursor.fetchone()[0]


def locked_scope(request,intent_id):
    # Initial lookup discovers scope only; authority and facts are checked under locks.
    discovered=RequestArchiveIntent.objects.filter(pk=intent_id).values('envelope_id','envelope__quotation_id','envelope__business_version').first()
    if discovered is None:raise EnvelopeError('authorization_unavailable')
    raw=prepare_request_envelope(request,discovered['envelope__quotation_id'],discovered['envelope__business_version'])
    envelope=RequestEnvelope.objects.select_for_update().get(pk=discovered['envelope_id'])
    intent=RequestArchiveIntent.objects.select_for_update().get(pk=intent_id)
    if (intent.envelope_id!=envelope.pk or bytes(envelope.payload)!=raw or envelope.sha256!=hashlib.sha256(raw).hexdigest()
        or envelope.byte_length!=len(raw) or intent.destination_id is None or intent.destination_profile!='local-prepared-v1'
        or intent.evidence_class!='local-synthetic' or intent.evidence_kind!='prepared' or intent.effects_authorized or intent.retention_qualified):
        raise EnvelopeError('authorization_unavailable')
    # Producer already compared the original owner through the reconstructed bytes.
    import json
    if envelope.owner_id!=json.loads(raw)['request']['owner_id']:raise EnvelopeError('authorization_unavailable')
    return envelope,intent


def check_call(intent_id):
    if connection.in_atomic_block:raise EnvelopeError('authorization_transaction_active')
    if type(intent_id) is not uuid.UUID:raise EnvelopeError('authorization_unavailable')


def authorize_request_archive(request,intent_id,expected_destination_id,command_id,expected_generation):
    check_call(intent_id)
    if (type(expected_destination_id) is not uuid.UUID or type(command_id) is not uuid.UUID
        or type(expected_generation) is not int or not 0<=expected_generation<1000000000):raise EnvelopeError('authorization_unavailable')
    with transaction.atomic(durable=True):
        envelope,intent=locked_scope(request,intent_id)
        if intent.destination_id!=expected_destination_id:raise EnvelopeError('authorization_conflict')
        existing=ArchiveWorkAuthorization.objects.filter(intent=intent,command_id=command_id).first()
        if existing:
            if (existing.generation!=expected_generation+1 or existing.destination_id!=intent.destination_id
                or existing.envelope_sha256!=envelope.sha256 or existing.byte_length!=envelope.byte_length
                or existing.owner_id!=envelope.owner_id or existing.schema_version!=envelope.schema_version):raise EnvelopeError('authorization_conflict')
            # Historical retry is not an active-work decision and never extends a deadline.
            return AuthorizationReference(existing.pk,existing.generation,False)
        latest=ArchiveWorkAuthorization.objects.filter(intent=intent).aggregate(value=Max('generation'))['value'] or 0
        if ArchivePreparedVerification.objects.filter(intent=intent).exists():raise EnvelopeError('authorization_already_verified')
        if intent.state!='pending' or latest!=expected_generation:raise EnvelopeError('authorization_conflict')
        now=db_now();marker=request.session.get('shop_staff_mfa') if request.user.is_staff else None
        grant=ArchiveWorkAuthorization.objects.create(intent=intent,command_id=command_id,generation=latest+1,
            destination_id=intent.destination_id,envelope_sha256=envelope.sha256,byte_length=envelope.byte_length,
            schema_version=envelope.schema_version,owner_id=envelope.owner_id,authorized_by=request.user,
            staff_generation=uuid.UUID(marker['generation']) if marker else None,
            mfa_verified_at=datetime.fromtimestamp(marker['verified_at'],tz=timezone.utc) if marker else None,
            issued_at=now,not_after=now+timedelta(minutes=5))
        return AuthorizationReference(grant.pk,grant.generation,True)


def revoke_request_archive(request,intent_id,authorization_id):
    check_call(intent_id)
    if type(authorization_id) is not uuid.UUID:raise EnvelopeError('authorization_unavailable')
    with transaction.atomic(durable=True):
        _,intent=locked_scope(request,intent_id)
        grant=ArchiveWorkAuthorization.objects.select_for_update().filter(pk=authorization_id,intent=intent).first()
        if grant is None:raise EnvelopeError('authorization_unavailable')
        _,created=ArchiveWorkRevocation.objects.get_or_create(authorization=grant,defaults={'revoked_by':request.user,'revoked_at':db_now()})
        return AuthorizationReference(grant.pk,grant.generation,created)


@dataclass(frozen=True)
class ActiveAuthorizationReference:
    authorization_id: uuid.UUID
    intent_id: uuid.UUID
    destination_id: uuid.UUID
    generation: int


def locked_active_authorization(authorization_id,expected_destination_id):
    """Internal: all authority/source locks remain held by the caller transaction."""
    from django.conf import settings
    from django.contrib.auth import get_user_model
    from django.db.models import F
    from shop.access.models import CustomerIdentity,StaffCredential,StaffQuotationGrant
    from .models import QuotationRequest
    from .request_envelope import source_bytes
    if not connection.in_atomic_block:raise EnvelopeError('authorization_transaction_required')
    if (type(authorization_id) is not uuid.UUID or type(expected_destination_id) is not uuid.UUID
        or settings.SHOP_ENV not in ('local','synthetic') or settings.STORAGE_ADAPTER!='fake'):
        raise EnvelopeError('authorization_unavailable')
    discovered=ArchiveWorkAuthorization.objects.filter(pk=authorization_id).values('authorized_by_id','staff_generation','owner_id','intent_id','intent__envelope_id','intent__envelope__quotation_id').first()
    if discovered is None:raise EnvelopeError('authorization_unavailable')
    if discovered['staff_generation'] is not None:
        credential=StaffCredential.objects.select_for_update().filter(user_id=discovered['authorized_by_id'],
            enabled=True,generation=discovered['staff_generation'],user__is_active=True,user__is_staff=True).first()
        if credential is None:raise EnvelopeError('authorization_unavailable')
    elif discovered['authorized_by_id']!=discovered['owner_id']:raise EnvelopeError('authorization_unavailable')
    # Allow audit foreign-key inserts while blocking account changes.
    owner=get_user_model().objects.select_for_update(no_key=True).filter(pk=discovered['owner_id'],is_active=True,is_staff=False,is_superuser=False).first()
    if owner is None or not CustomerIdentity.objects.filter(user=owner).exists():raise EnvelopeError('authorization_unavailable')
    quotation=QuotationRequest.objects.select_related('cart','snapshot').select_for_update(of=('self','cart')).filter(
        pk=discovered['intent__envelope__quotation_id'],snapshot__cart_id=F('cart_id'),cart__owner=owner).first()
    envelope=RequestEnvelope.objects.select_for_update().filter(pk=discovered['intent__envelope_id']).first()
    intent=RequestArchiveIntent.objects.select_for_update().filter(pk=discovered['intent_id']).first()
    grant=ArchiveWorkAuthorization.objects.select_for_update().filter(pk=authorization_id).first()
    if quotation is None or envelope is None or intent is None or grant is None:raise EnvelopeError('authorization_unavailable')
    if (grant.intent_id!=intent.pk or intent.envelope_id!=envelope.pk or envelope.quotation_id!=quotation.pk
        or grant.authorized_by_id!=discovered['authorized_by_id'] or grant.staff_generation!=discovered['staff_generation']
        or grant.owner_id!=owner.pk or envelope.owner_id!=owner.pk or envelope.business_version>quotation.business_version
        or intent.state!='pending' or intent.destination_id!=expected_destination_id or grant.destination_id!=expected_destination_id
        or intent.destination_profile!='local-prepared-v1' or intent.evidence_class!='local-synthetic' or intent.evidence_kind!='prepared'
        or intent.retention_qualified or intent.effects_authorized or grant.retention_qualified or grant.effects_authorized
        or grant.schema_version!=envelope.schema_version or grant.envelope_sha256!=envelope.sha256 or grant.byte_length!=envelope.byte_length):
        raise EnvelopeError('authorization_unavailable')
    if discovered['staff_generation'] is not None:
        if not StaffQuotationGrant.objects.filter(user_id=grant.authorized_by_id,quotation=quotation,
            **({'business_scope_version':envelope.business_version} if envelope.business_version else {})).exists():raise EnvelopeError('authorization_unavailable')
    latest=ArchiveWorkAuthorization.objects.filter(intent=intent).aggregate(value=Max('generation'))['value']
    now=db_now()
    if (latest!=grant.generation or now<grant.issued_at or now>=grant.not_after
        or ArchiveWorkRevocation.objects.filter(authorization=grant).exists()):raise EnvelopeError('authorization_unavailable')
    raw=source_bytes(quotation,envelope.business_version)
    if bytes(envelope.payload)!=raw or envelope.sha256!=hashlib.sha256(raw).hexdigest() or envelope.byte_length!=len(raw):raise EnvelopeError('authorization_unavailable')
    return grant,intent


def inspect_active_authorization(authorization_id,expected_destination_id):
    """Point-in-time detached check; no payload return or future authority."""
    if connection.in_atomic_block:raise EnvelopeError("authorization_transaction_active")
    with transaction.atomic(durable=True):
        grant,intent=locked_active_authorization(authorization_id,expected_destination_id)
        return ActiveAuthorizationReference(grant.pk,intent.pk,expected_destination_id,grant.generation)
