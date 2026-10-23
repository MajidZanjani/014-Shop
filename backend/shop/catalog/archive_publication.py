"""One selected local prepared publication/readback, fenced after unlocked I/O."""
from dataclasses import dataclass
import hashlib
import uuid
from django.db import connection,transaction
from shop.adapters.archive_destination import BoundPreparedArchive
from shop.adapters.evidence_archive import ArchiveError,PreparedReceipt,manifest
from . import archive_authority as authority
from .archive_claim import locked_claim
from .models import ArchivePreparedVerification
from .request_envelope import EnvelopeError

@dataclass(frozen=True)
class VerificationReference:
    verification_id: uuid.UUID
    intent_id: uuid.UUID
    created: bool


def destination_matches(intent,proof):
    destination=intent.destination
    if (destination.pk,destination.device,destination.inode,destination.manifest_sha256,destination.profile)!=(
        proof.id,proof.device,proof.inode,proof.manifest_sha256,'local-prepared-v1'):
        raise EnvelopeError('publication_destination_conflict')


def matching(row,intent,claim=None):
    envelope=intent.envelope
    if (row.intent_id!=intent.pk or row.envelope_id!=envelope.pk or row.destination_id!=intent.destination_id
        or row.evidence_id!=envelope.pk or row.sha256!=envelope.sha256 or row.byte_length!=envelope.byte_length
        or row.evidence_class!='local-synthetic' or row.evidence_kind!='prepared' or row.retention_qualified or row.effects_authorized
        or row.claim.intent_id!=intent.pk or row.claim.authorization_id!=row.authorization_id
        or row.claim.generation!=row.claim_generation or row.authorization.generation!=row.authorization_generation
        or row.authorization.intent_id!=intent.pk or row.authorization.destination_id!=intent.destination_id
        or row.authorization.envelope_sha256!=envelope.sha256 or row.authorization.byte_length!=envelope.byte_length
        or row.authorization.schema_version!=envelope.schema_version or row.authorization.owner_id!=envelope.owner_id
        or row.claim.retention_qualified or row.claim.effects_authorized or row.authorization.retention_qualified or row.authorization.effects_authorized
        or (claim is not None and row.claim_id!=claim.pk)):
        raise EnvelopeError('publication_conflict')


def publish_request_archive(claim_id,token,archive):
    if connection.in_atomic_block or not connection.get_autocommit():raise EnvelopeError('publication_transaction_active')
    if type(archive) is not BoundPreparedArchive:raise EnvelopeError('publication_unavailable')
    try:proof=archive.attest()
    except ArchiveError:raise EnvelopeError('publication_unavailable') from None
    with transaction.atomic(durable=True):
        claim,intent=locked_claim(claim_id,token)
        destination_matches(intent,proof)
        existing=ArchivePreparedVerification.objects.filter(intent=intent).first()
        if existing:
            matching(existing,intent,claim)
            return VerificationReference(existing.pk,intent.pk,False)
        envelope=intent.envelope
        raw=bytes(envelope.payload)
        receipt=PreparedReceipt(envelope.pk,envelope.sha256,envelope.byte_length)
        if hashlib.sha256(raw).hexdigest()!=receipt.sha256 or len(raw)!=receipt.size:raise EnvelopeError('publication_conflict')
    # Actual files and root attestations never run under a database transaction.
    try:
        observed=archive.publish(receipt.evidence_id,raw)
        manifest(observed)
        if observed!=receipt:raise EnvelopeError('publication_conflict')
        with BoundPreparedArchive(archive.directory,proof) as reopened:
            if reopened.recover(receipt)!=raw:raise EnvelopeError('publication_conflict')
        if archive.attest()!=proof:raise EnvelopeError('publication_destination_conflict')
    except ArchiveError:raise EnvelopeError('publication_unavailable') from None
    with transaction.atomic(durable=True):
        claim,intent=locked_claim(claim_id,token)
        destination_matches(intent,proof)
        envelope=intent.envelope
        if (envelope.pk!=receipt.evidence_id or envelope.sha256!=receipt.sha256
            or envelope.byte_length!=receipt.size or bytes(envelope.payload)!=raw):raise EnvelopeError('publication_conflict')
        existing=ArchivePreparedVerification.objects.filter(intent=intent).first()
        if existing:
            matching(existing,intent,claim)
            return VerificationReference(existing.pk,intent.pk,False)
        grant=claim.authorization
        now=authority.db_now()
        if now>=claim.expires_at or now>=grant.not_after:raise EnvelopeError('publication_unavailable')
        row=ArchivePreparedVerification.objects.create(intent=intent,envelope=envelope,destination_id=proof.id,
            claim=claim,authorization=grant,claim_generation=claim.generation,authorization_generation=grant.generation,
            evidence_id=receipt.evidence_id,sha256=receipt.sha256,byte_length=receipt.size,verified_at=now)
        return VerificationReference(row.pk,intent.pk,True)


def inspect_prepared_verification(request,intent_id):
    """Currently authorized historical safe metadata; no fresh work permission."""
    authority.check_call(intent_id)
    with transaction.atomic(durable=True):
        _,intent=authority.locked_scope(request,intent_id)
        row=ArchivePreparedVerification.objects.filter(intent=intent).first()
        if row is None:raise EnvelopeError('publication_unavailable')
        matching(row,intent)
        return VerificationReference(row.pk,intent.pk,False)
