# Next local capture/intent slice — proposed design

This narrows07-EVIDENCE-CONTRACT to the implemented request-only schema. It is not a migration, live approval or completed07-02. Request envelope implementation2048a57 supplies authorized immutable bytes and stable semantic UUID identity; it does not yet commit a durable domain record or outbox intent.

## Proposed records

Request-envelope record: stable envelope UUID primary key; protected quotation FK; explicit business-scope version/schema version; canonical byte payload, hash and byte length; retained owning customer identity; capture attribution/time separate from immutable fact identity. Uniqueness on quotation/business-scope/schema, not only browser request keys. The UUID must equal the existing schema/request/scope-derived identity. Payload is private bounded binary content, not an ordinary summary. Keep original request IDs from the envelope; later alias/review/counter facts need separate evidence identities. Schema/version migration never silently rewrites old bytes.

Archive-intent record: one-to-one protected envelope reference, local-synthetic/prepared classification, pending/leased/local-verified/held technical state, bounded attempt count, lease token/generation/deadline and immutable destination identity. Local-verified means exact prepared bytes verified only; it cannot mean acceptance/completion/provider-retention qualification. Effects/retention qualification remain false by constraints. Do not reuse Probe/FakeReceipt. Defer actual worker implementation until lease/fencing tests and its exact caller contract exist.

Persist independent receipt/reference fields only after archive readback verifies expected identity/hash/size/classification. Never include raw path/error/secret data in ordinary responses/logs. Physical database immutability/privileges and qualified destination/custody remain separate release tasks; append-only-by-service alone is not a production guarantee.

## Proposed capture transaction

1. Authorize verified owner or recent staff verification with quotation/exact private-scope grant, using existing credential-first and quotation/cart lock ordering. Require explicit scope/schema selection; no fallback to a newer attachment.
2. Build and validate bytes from retained models using prepare_request_envelope within the same outer transaction. This function performs no archive I/O. Do not accept arbitrary payload bytes from an HTTP client. No export/capture endpoint is part of this next slice.
3. Arbitrate the stable semantic envelope identity under the parent lock and database uniqueness. Existing exact bytes/hash return the same record and one existing intent; inconsistent bytes for the same semantic identity cause a fixed conflict/hold, never overwrite. Unknown source/schema is held without inventing migration assumptions.
4. Insert immutable envelope and one archive intent atomically, then commit. A failed insert/validation/permission check leaves neither half. No storage/provider call occurs on any capture path. Preserve committed records after an uncertain response; retry reconciles the same semantic identity across different request keys.

Capture attribution is not part of semantic payload identity: a second authorized actor can reconcile the same exact record without changing its original attribution. It cannot gain private scope by knowing the UUID/hash. Every later read must authorize the recorded owner/current valid historical scope; source-owner mismatch fails closed.

## Subsequent leased archive boundary

Later, claim token/generation and the exact immutable destination/reference in a short transaction, release the transaction, then publish/readback. Post-I/O completion compares claim generation/token, payload identity/hash, destination and current authorization/hold state. Expired/stolen/revoked claims cannot mark readiness. Lost acknowledgement is reconciled by the original identity, not a fresh key or object deletion. Local receipts only permit local-verified technical state; all commercial effects remain disabled. Provider retention qualification and actual domain completion require their own implemented contracts/evidence, never a boolean supplied by the caller.

## Required first capture tests

Use actual PostgreSQL for same-scope two-key/two-actor races: one envelope and one intent. Verify same-scope changed bytes conflict, different business scopes remain separate, historical private grant revocation blocks return, stale source/ownership is held, insert failure rolls back both records and retry after a lost response returns the same identities. Patch storage adapters to fail if called during capture. Assert payloads/private hashes do not appear in ordinary quotation responses/logs. Require migrations/constraints checks and existing197-test baseline plus new targeted tests. Worker lease expiry/steal/post-I/O cases remain subsequent tests, not covered by merely adding the records.

Country/tax choices and source-approved commercial inputs stay pending throughout. No offer, acceptance/order, bank, licence/support, provider/host or deployment effect follows from this design.
