"""Selected local work leases only. No queue loop, storage I/O or completion."""
from dataclasses import dataclass,field
from datetime import timedelta
import uuid
from django.db import connection,transaction
from . import archive_authority as authority
from .models import ArchiveWorkClaim
from .request_envelope import EnvelopeError

@dataclass(frozen=True)
class ClaimReference:
    claim_id: uuid.UUID
    generation: int
    token: uuid.UUID=field(repr=False)

@dataclass(frozen=True)
class ClaimObservation:
    claim_id: uuid.UUID
    intent_id: uuid.UUID
    generation: int


def claim_request_archive(authorization_id,expected_destination_id):
    if connection.in_atomic_block:raise EnvelopeError('claim_transaction_active')
    with transaction.atomic(durable=True):
        grant,intent=authority.locked_active_authorization(authorization_id,expected_destination_id)
        # The authority routine holds the intent lock, serializing every claimant.
        latest=ArchiveWorkClaim.objects.filter(intent=intent).order_by('-generation').first()
        now=authority.db_now()
        if now>=grant.not_after:raise EnvelopeError('claim_unavailable')
        if latest and latest.expires_at>now:raise EnvelopeError('claim_busy')
        generation=latest.generation+1 if latest else 1
        if generation>1000000000:raise EnvelopeError('claim_unavailable')
        claim=ArchiveWorkClaim.objects.create(intent=intent,authorization=grant,generation=generation,
            started_at=now,expires_at=min(now+timedelta(seconds=30),grant.not_after))
        return ClaimReference(claim.pk,generation,claim.token)


def locked_claim(claim_id,token):
    """Internal point-in-time fence; caller owns the transaction and locks."""
    if not connection.in_atomic_block:raise EnvelopeError('claim_transaction_required')
    if type(claim_id) is not uuid.UUID or type(token) is not uuid.UUID:raise EnvelopeError('claim_unavailable')
    discovered=ArchiveWorkClaim.objects.filter(pk=claim_id).values('authorization_id','authorization__destination_id').first()
    if discovered is None:raise EnvelopeError('claim_unavailable')
    grant,intent=authority.locked_active_authorization(discovered['authorization_id'],discovered['authorization__destination_id'])
    claim=ArchiveWorkClaim.objects.select_for_update().filter(pk=claim_id).first()
    latest=ArchiveWorkClaim.objects.filter(intent=intent).order_by('-generation').first()
    now=authority.db_now()
    if (claim is None or latest is None or latest.pk!=claim.pk or claim.intent_id!=intent.pk or claim.authorization_id!=grant.pk
        or claim.token!=token or claim.retention_qualified or claim.effects_authorized
        or now<claim.started_at or now>=claim.expires_at or now>=grant.not_after):raise EnvelopeError('claim_unavailable')
    return claim,intent


def inspect_archive_claim(claim_id,token):
    """Safe metadata only; not permission for a later write or completion."""
    if connection.in_atomic_block:raise EnvelopeError('claim_transaction_active')
    with transaction.atomic(durable=True):
        claim,intent=locked_claim(claim_id,token)
        return ClaimObservation(claim.pk,intent.pk,claim.generation)
