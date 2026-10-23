"""Atomic local request fact+intent. No storage calls, endpoints or worker claims."""
from dataclasses import dataclass
from datetime import datetime,timezone
import hashlib
import uuid
from django.db import IntegrityError,transaction,connection
from .models import RequestEnvelope,RequestArchiveIntent
from .request_envelope import prepare_request_envelope,validate_envelope,identity,EnvelopeError

@dataclass(frozen=True)
class CaptureReference:
    envelope_id: uuid.UUID
    intent_id: uuid.UUID
    created: bool


def capture_request_envelope(request,quotation_id,business_version):
    if connection.in_atomic_block or not connection.get_autocommit():raise EnvelopeError('capture_transaction_active')
    try:
        with transaction.atomic(durable=True):
            # Nested producer authorization acquires credential/parent/cart locks
            # which remain held through this outer fact+intent commit.
            raw=prepare_request_envelope(request,quotation_id,business_version)
            value=validate_envelope(raw)
            digest=hashlib.sha256(raw).hexdigest()
            envelope_id=identity(quotation_id,business_version)
            row=RequestEnvelope.objects.select_for_update().filter(quotation_id=quotation_id,business_version=business_version,schema_version=1).first()
            if row is not None:
                if (row.pk!=envelope_id or row.owner_id!=value['request']['owner_id']
                    or bytes(row.payload)!=raw or row.sha256!=digest or row.byte_length!=len(raw)):
                    raise EnvelopeError('capture_conflict')
                intent=RequestArchiveIntent.objects.filter(envelope=row).first()
                if (intent is None or intent.state not in ('pending','held')
                    or intent.destination_profile!='local-prepared-v1' or intent.evidence_class!='local-synthetic'
                    or intent.evidence_kind!='prepared' or intent.retention_qualified is not False or intent.effects_authorized is not False):
                    raise EnvelopeError('capture_unavailable')
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
