"""Atomic local request fact+intent. No storage calls, endpoints or worker claims."""
from dataclasses import dataclass
from datetime import datetime,timezone
import hashlib
import re
import uuid
from django.db import IntegrityError,transaction,connection
from .models import RequestEnvelope,RequestArchiveIntent
from .request_envelope import prepare_request_envelope,validate_envelope,identity,EnvelopeError

@dataclass(frozen=True)
class CaptureReference:
    envelope_id: uuid.UUID
    intent_id: uuid.UUID
    created: bool


def capture_request_envelope(request,quotation_id,business_version,expected_source_sha256=None):
    if connection.in_atomic_block or not connection.get_autocommit():raise EnvelopeError('capture_transaction_active')
    if expected_source_sha256 is not None and (not isinstance(expected_source_sha256,str) or re.fullmatch('[0-9a-f]{64}',expected_source_sha256) is None):
        raise EnvelopeError('invalid_capture_digest')
    try:
        with transaction.atomic(durable=True):
            # Nested producer authorization acquires credential/parent/cart locks
            # which remain held through this outer fact+intent commit.
            raw=prepare_request_envelope(request,quotation_id,business_version)
            value=validate_envelope(raw)
            digest=hashlib.sha256(raw).hexdigest()
            if expected_source_sha256 is not None and digest!=expected_source_sha256:
                raise EnvelopeError('capture_preview_changed')
            envelope_id=identity(quotation_id,business_version)
            row=RequestEnvelope.objects.select_for_update().filter(quotation_id=quotation_id,business_version=business_version,schema_version=1).first()
            if row is not None:
                intent=retained_intent(row,raw,value)
                return CaptureReference(row.pk,intent.pk,False)
            marker=request.session.get('shop_staff_mfa') if request.user.is_staff else None
            row=RequestEnvelope.objects.create(id=envelope_id,quotation_id=quotation_id,business_version=business_version,
                schema_version=1,owner_id=value['request']['owner_id'],captured_by=request.user,
                staff_generation=uuid.UUID(marker['generation']) if marker else None,
                mfa_verified_at=datetime.fromtimestamp(marker['verified_at'],tz=timezone.utc) if marker else None,
                payload=raw,sha256=digest,byte_length=len(raw))
            intent=RequestArchiveIntent.objects.create(envelope=row)
            return CaptureReference(row.pk,intent.pk,True)
    except IntegrityError:raise EnvelopeError('capture_conflict') from None


def retained_intent(row,raw,value):
    """Shared retained-fact validation; caller holds producer and envelope locks."""
    if (row.schema_version!=1 or row.pk!=identity(row.quotation_id,row.business_version)
        or row.owner_id!=value['request']['owner_id'] or bytes(row.payload)!=raw
        or row.sha256!=hashlib.sha256(raw).hexdigest() or row.byte_length!=len(raw)):
        raise EnvelopeError('capture_conflict')
    intent=RequestArchiveIntent.objects.select_for_update().filter(envelope=row).first()
    if (intent is None or intent.state not in ('pending','held')
        or intent.destination_profile!='local-prepared-v1' or intent.evidence_class!='local-synthetic'
        or intent.evidence_kind!='prepared' or intent.retention_qualified is not False or intent.effects_authorized is not False):
        raise EnvelopeError('capture_unavailable')
    return intent


def observe_request_capture(request,quotation_id,business_version):
    """Observe one committed retained capture. No writes, storage or work permission."""
    from shop.access.staff_auth import staff_credential
    if connection.in_atomic_block or not connection.get_autocommit():raise EnvelopeError('observation_transaction_active')
    with transaction.atomic(durable=True):
        if staff_credential(request,recent=True) is None:raise EnvelopeError('envelope_unavailable')
        raw=prepare_request_envelope(request,quotation_id,business_version)
        value=validate_envelope(raw)
        # Producer locks remain held here; a concurrent capture must settle first.
        row=RequestEnvelope.objects.select_for_update().filter(quotation_id=quotation_id,business_version=business_version).first()
        if row is None:return 'capture_not_recorded'
        retained_intent(row,raw,value)
        return 'capture_recorded'
