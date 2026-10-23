"""Bind one explicitly attested local root. No claim, publication or worker authority."""
from dataclasses import dataclass
from datetime import datetime,timezone as utc_timezone
import hashlib
import uuid
from django.db import connection,transaction,IntegrityError
from django.utils import timezone
from shop.adapters.archive_destination import BoundPreparedArchive
from shop.adapters.evidence_archive import ArchiveError
from .models import RequestEnvelope,RequestArchiveIntent,ArchiveDestination
from .request_envelope import prepare_request_envelope,validate_envelope,identity,EnvelopeError

@dataclass(frozen=True)
class DestinationReference:
    intent_id: uuid.UUID
    destination_id: uuid.UUID
    created: bool


def bind_request_destination(request,quotation_id,business_version,archive):
    if connection.in_atomic_block or not connection.get_autocommit():raise EnvelopeError('binding_transaction_active')
    if type(archive) is not BoundPreparedArchive:raise EnvelopeError('destination_unavailable')
    try:proof=archive.attest()
    except ArchiveError:raise EnvelopeError('destination_unavailable') from None
    try:
        with transaction.atomic(durable=True):
            raw=prepare_request_envelope(request,quotation_id,business_version)
            value=validate_envelope(raw)
            row=RequestEnvelope.objects.select_for_update().filter(pk=identity(quotation_id,business_version),quotation_id=quotation_id,business_version=business_version,schema_version=1).first()
            if row is None or row.owner_id!=value['request']['owner_id'] or bytes(row.payload)!=raw or row.sha256!=hashlib.sha256(raw).hexdigest() or row.byte_length!=len(raw):raise EnvelopeError('capture_unavailable')
            intent=RequestArchiveIntent.objects.select_for_update().filter(envelope=row).first()
            if (intent is None or intent.state not in ('pending','held') or intent.effects_authorized or intent.retention_qualified
                or intent.destination_profile!='local-prepared-v1' or intent.evidence_class!='local-synthetic' or intent.evidence_kind!='prepared'):raise EnvelopeError('binding_unavailable')
            if intent.destination_id is None:
                if intent.state!='pending':raise EnvelopeError('binding_unavailable')
                destination,_=ArchiveDestination.objects.get_or_create(pk=proof.id,defaults={
                    'device':proof.device,'inode':proof.inode,'manifest_sha256':proof.manifest_sha256,'created_by':request.user})
                if (destination.device,destination.inode,destination.manifest_sha256,destination.profile)!=(proof.device,proof.inode,proof.manifest_sha256,'local-prepared-v1'):raise EnvelopeError('destination_conflict')
                marker=request.session.get('shop_staff_mfa') if request.user.is_staff else None
                intent.destination=destination;intent.destination_bound_by=request.user;intent.destination_bound_at=timezone.now()
                intent.binding_staff_generation=uuid.UUID(marker['generation']) if marker else None
                intent.binding_mfa_verified_at=datetime.fromtimestamp(marker['verified_at'],tz=utc_timezone.utc) if marker else None
                intent.save(update_fields=['destination','destination_bound_by','destination_bound_at','binding_staff_generation','binding_mfa_verified_at'])
                created=True
            else:
                destination=intent.destination
                if (destination.pk,destination.device,destination.inode,destination.manifest_sha256,destination.profile)!=(proof.id,proof.device,proof.inode,proof.manifest_sha256,'local-prepared-v1'):raise EnvelopeError('destination_conflict')
                created=False
            reference=DestinationReference(intent.pk,proof.id,created)
    except IntegrityError:raise EnvelopeError('destination_conflict') from None
    # A lost/failed acknowledgement preserves the binding; never choose a new root.
    try:
        if archive.attest()!=proof:raise EnvelopeError('destination_unavailable')
    except ArchiveError:raise EnvelopeError('destination_unavailable') from None
    if prepare_request_envelope(request,quotation_id,business_version)!=raw:raise EnvelopeError('binding_unavailable')
    return reference
