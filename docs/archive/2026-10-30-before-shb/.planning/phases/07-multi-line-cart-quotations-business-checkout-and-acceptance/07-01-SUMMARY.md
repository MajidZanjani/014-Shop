---
phase: 07-multi-line-cart-quotations-business-checkout-and-acceptance
plan: "01"
status: complete
implementation_commit: 3e1b811
---
# Local prepared archive prerequisite

Implemented internal PreparedArchive/PreparedReceipt over a canonical owned0700 local/synthetic fake-storage root. Closed UUID/hash/size references, bounded bytes,0600 regular single-link files, descriptor-relative/no-symlink operations; blob first and immutable receipt last, exclusive temporary files, file/directory fsync and no-overwrite publication. Exact retry verifies existing committed bytes; changed payload conflicts. Reopened recovery verifies the independently retained reference against receipt and blob. Fail-fast per-instance/directory locks arbitrate publishers. Failed writes/publication/sync never acknowledge a receipt or delete prior evidence; orphan prepared blobs and lost receipt acknowledgements reconcile on exact retry. Fixed errors exclude private values/paths.

Receipts are local-synthetic/prepared only, retention_qualified=false and effects_authorized=false. No domain routes, outbox, offers, acceptance/order, bank/provider, support/delivery or host changes. Actual completion envelopes, independent retention/custody/restore and production integration are pending. No DATA04/full COM acceptance claimed.

CORE_LOCAL_PASS checks5 tests188 duration39.798s:174 Django plus14 actual loopback observations, owned PostgreSQL18.6/UTF8. Ten new archive tests cover publish/reopen/exact retry/conflict, tampering/missing objects/receipt changes, unsafe root/modes/links/symlinks, invalid/classification/environment/privacy, blob-before-receipt failure, early/late fsync failure and uncertain acknowledgement, same/distinct identity contention/reconciliation and non-destructive failed publication. Existing domain/access/form/API concurrency suites pass.

Actual Nix source /nix/store/ll7jjhh24zfs6nn77mlwfk5l5dfwj0wg-shop-python-source:131 files19 templates, exact bytes/allowlist/no symlinks verified. Frontend/proxy unchanged, prior scoped evidence retained. Inline source/plan review; no independent review or off-host/browser/provider guarantee. Country/tax pending.

Phase7 local remaining plans1/4, full phase still In Progress/gaps_found. Overall11/24 planned records,1/14 completed phases, Phase02 8/18. Next: design exact private quotation evidence envelope and domain outbox/reference contract for07-02 before any protected offer publication.
