# Quotation evidence and domain archive contract — proposed local design

This is a repository design for the next07-02 tasks, not an implemented database schema or approved commercial policy. It follows source handoffT05/T07/T08 and DATA01–04/COM02–06. Country/tax remains user-deferred. Plan07-01 proves bounded local prepared bytes only; its receipts cannot satisfy provider retention or authorize any business effect.

## Exact private envelope

A future domain envelope is an immutable, schema-versioned canonical UTF8 JSON byte sequence, bounded before persistence/publication. Its stable UUID identifies a domain fact and its revision; a new semantic revision always gets a new identity. A digest must never substitute for retaining recoverable content. Envelope identity, bytes/hash, operation kind and all referenced revisions are committed together before scheduling archive work. Exact retry compares bytes/hash and all semantic identifiers, not a caller-selected fresh idempotency key alone.

Required content for an offer candidate:

- Domain envelope schema/identity, quotation/request/offer-revision identities and retained creation time. Current QuotationRequest is an unpriced request, not an offer revision.
- Complete selected immutable cart lines and their stable identities, configuration/profile/catalog/source revisions, support quantities and line-type document applicability. No silent line omission, merge, quantity multiplication or split payment.
- Exact attached business scope and business-draft revision/source schema, including recoverable resolved private business values and separately attributable licensed-entity review. Ordinary summaries remain masked; all historical references must still belong to the authorized owner/scope.
- IP host-binding references only to an implemented encrypted key-versioned snapshot, with approved actual-manager normalization profile and configuration revision. No plaintext raw hosts, keys or secrets. Missing host/profile/encryption evidence blocks IP qualification; support-only has no invented IP/host fields.
- Component price/recurrence/rights/access/coverage versions, approved currency/tax/policy/document version references and exact approved document text bytes or independent recoverable content references. Unknown fields remain null with fixed pending reasons. Source declaration labels/previews and EUR draft intent do not approve live terms, tax or amounts.
- Separate quote validity, order payment-start deadline and eventual bank-session expiry semantics. No arbitrary default durations. Unknown deadlines block affected operations. No bank-session identity exists before its own payment preparation.
- Protected approval actor/resource-role/MFA audit references and decision revision, separate from ordinary internal review/preparation. Never retain passwords, challenge codes, recovery credentials, session cookies, bearer URLs or raw request headers/bodies.

An internal request-only producer/validator now implements a closed131072-byte canonical UTF8 schema over the existing retained records (07-02-ENVELOPE-PARTIAL). It is not the offer-candidate producer described above. Original immutable request IDs are retained; later alias-key/review/counter facts require separate envelopes. Atomic RequestEnvelope/RequestArchiveIntent capture now exists; no leased archive worker or qualified destination exists. Before implementing offer evidence, bind its exact closed schema and privacy classifications to actual approved inputs. Unknown commercial fields cannot be filled from test fixtures or staff free text.

## Persist first, archive second, qualify explicitly

Proposed local domain states are pending archive, verified archive and held. These names are conceptual until a migration/service design is tested. They are not financial or completion states.

1. In one short PostgreSQL transaction, authorize the exact current/historical resource scope, lock the operation aggregate, freeze the envelope and create a unique archive intent/outbox record. Commit before filesystem/network work. Do not repurpose worker Probe/FakeReceipt as real domain records.
2. A worker claims a bounded lease with token/generation and exact envelope revision. Release the transaction before calling storage. Every retry retains the same semantic envelope identity/hash and destination identity. Contention or missing custody evidence remains pending/held; it never causes a business effect.
3. Publish exact bytes, then verify destination/object version/hash/length and required retention evidence against the actual adapter contract. Retain the receipt and independently recoverable content reference. Local-synthetic receipts always fail the retention/effect qualification check even when byte verification succeeds.
4. In a new short transaction, compare lease token/generation, envelope identity/hash and intended domain revision. A stale worker cannot mark a changed/revoked operation verified. Unacknowledged publication is reconciled by the same identity and readback; never delete/rewrite committed evidence to retry.
5. Before any later issue/publication/dispatch/activation, recheck exact approved commercial/host/entity/document revisions, permissions, cancellation, deadlines, holds and runtime/live activation. A qualified archive is necessary but never sufficient authorization. External calls must not run while database locks are held.

Archive intents need uniqueness on the semantic domain operation/revision, not only on arbitrary browser keys. Leases need fencing, bounded attempts/backoff and explicit held/reconciliation states. Provider uncertainty preserves all observations and the original operation identity. Database restoration must reconcile independently retained receipts/objects and externally completed facts before reopening effects.

## Prepared, accepted and completed facts are separate

An internal review, preparation assessment, draft envelope or prepared archive receipt cannot manufacture signatory authority, accepted text, payment, delivered key or performed support work. Future acceptance must persist exact selected revision/declarations/signatory/authority/time with one acceptance/order per approved offer revision, including concurrent sessions/different keys. Its actual committed fact then needs its own domain archive identity/evidence contract. No bank dispatch follows until the separately scoped payment preparation and archive/recheck/claim protocol exists. Actual support completion has a separate producer/fact/archive; a prepared task cannot prove that work occurred.

## Failure and privacy verification before implementation completion

Require real PostgreSQL tests for atomic envelope/outbox commit, two-key semantic uniqueness, lease theft/expiry/stale completion fencing, owner/private-grant revocation, and changed revisions during archive waits. Use a bounded fake transport to assert no database transaction spans publication. Test missing/wrong destination/version/hash/retention, local receipt rejection, late successful publication with lost acknowledgement, cancellation/expiry/holds and restoration divergence. No real provider faults or mx1 operations follow from this design.

Private envelope reads/exports require their exact resource scope and recent staff verification where privileged; no generic archive-download route or bearer URL. Logs/metrics expose only fixed error categories and safe numeric counters. Avoid private values, envelope hashes, object paths and tokens in ordinary responses/logs/public bundles. Independent provider custody/retention, keys/configuration recovery, actual domain completions and off-host restore remain qualification gates.

## Next executable design task

Specify and validate a closed recoverable quotation-request/business-scope envelope using existing immutable local models and source schema, without creating an offer or selecting Country/tax. Define its domain-specific identity and owner/private-scope checks first. Then design durable intent/outbox/reference models and fencing. Approved offer publication, acceptance, payment and07-02 completion remain gated until their actual input and durability contracts are implemented and verified.

Current request-only API: prepare_request_envelope(request, quotation_uuid, business_scope_version) returns authorized prepared bytes; validate_envelope(bytes) validates current known source/schema; recover_request_envelope(request, quotation_uuid, business_scope_version, receipt, archive) binds exact receipt and reauthorizes after I/O outside database transactions. No HTTP export or automatic archive write is registered.

Current implementation boundary: Explicit private local destination identity and attributed intent binding are implemented; root replacement, copied/tampered markers and rebinding fail closed. Only pending/held intents exist; no claim, worker, publication service or durable worker authority exists. Retention/effect flags remain false. See07-02-DESTINATION-PARTIAL. Earlier proposal text does not add runtime capabilities.

Recorded local implementation3b9f6a1 synced0/0. Worker design now specifies a proposed explicit bounded authorization record/source reader before claims; it adds no runtime authority or completed-plan credit. Current214-test/141-file evidence unchanged.
