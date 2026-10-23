"""Currently authorized historical observations; never retry/work authority."""
from dataclasses import dataclass
import uuid
from django.db import transaction
from . import archive_authority as authority
from .archive_publication import matching
from .models import ArchiveWorkClaim,ArchivePreparedVerification
from .request_envelope import EnvelopeError

@dataclass(frozen=True)
class ReconciliationReference:
    intent_id: uuid.UUID
    claim_id: uuid.UUID
    verification_id: uuid.UUID | None
    status: str


def reconcile_archive_publication(request,intent_id,expected_claim_id):
    authority.check_call(intent_id)
    if type(expected_claim_id) is not uuid.UUID:raise EnvelopeError('reconciliation_unavailable')
    with transaction.atomic(durable=True):
        # Same quotation/cart/envelope/intent locks as publication completion:
        # an in-flight commit must settle before its record can be observed here.
        _,intent=authority.locked_scope(request,intent_id)
        claim=ArchiveWorkClaim.objects.select_for_update().filter(pk=expected_claim_id,intent=intent).first()
        if claim is None:raise EnvelopeError('reconciliation_unavailable')
        row=ArchivePreparedVerification.objects.filter(intent=intent).first()
        if row is None:
            # Absence of a DB record does not prove absence of physical bytes,
            # authorize retry, release holds, extend a lease or cancel a writer.
            return ReconciliationReference(intent.pk,claim.pk,None,'verification_not_recorded')
        matching(row,intent)
        status='verification_recorded' if row.claim_id==claim.pk else 'verification_recorded_by_other_claim'
        return ReconciliationReference(intent.pk,claim.pk,row.pk,status)
