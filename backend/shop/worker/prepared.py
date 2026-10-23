"""One explicitly authorized local prepared job; no probe effects or queue loop."""
from django.conf import settings
from django.db import connection
from shop.adapters.archive_destination import BoundPreparedArchive
from shop.adapters.evidence_archive import ArchiveError
from shop.catalog.archive_claim import claim_request_archive
from shop.catalog.archive_publication import publish_request_archive
from shop.catalog.models import ArchiveDestination
from shop.catalog.request_envelope import EnvelopeError


def execute_prepared_once(authorization_id,archive):
    if connection.in_atomic_block or not connection.get_autocommit():raise EnvelopeError('worker_transaction_active')
    if (connection.vendor!='postgresql' or settings.SHOP_ENV not in ('local','synthetic')
        or settings.STORAGE_ADAPTER!='fake' or type(archive) is not BoundPreparedArchive):raise EnvelopeError('worker_unavailable')
    try:proof=archive.attest()
    except ArchiveError:raise EnvelopeError('worker_unavailable') from None
    # Fail before allocating a lease for an obviously mismatched physical root.
    # Publication rechecks the binding under the actual claim's locked scope.
    if not ArchiveDestination.objects.filter(pk=proof.id,device=proof.device,inode=proof.inode,
        manifest_sha256=proof.manifest_sha256,profile='local-prepared-v1').exists():raise EnvelopeError('worker_destination_unavailable')
    claim=claim_request_archive(authorization_id,proof.id)
    # A failure retains the lease/files for explicit reconciliation; never retry
    # automatically, switch targets, fabricate a session or renew work authority.
    return publish_request_archive(claim.claim_id,claim.token,archive)
