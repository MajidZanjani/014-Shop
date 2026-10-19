# Roadmap: Synaptic Laboratories IP Shop

**Status:** Planning baseline retained by user on 2026-10-19: autonomous workflow, 14 phases, parallel independent plans, commit and sync.

The 14 phases preserve handoff T01–T14 (40–65 engineer-days, scoped tests included). Phases are dependency ordered, not a requirement to idle behind external blockers. Phase 9 may wait while 10/11 and local 12 preparation proceed. Phase 4 frontend and Phase 5 backend join for full inquiry proof; their UI/API contract is established in Phase 2. No phase is implemented.

## Execution Policy

Keep the source task structure and dependency graph. Parallel execution applies only to independent work. Use the current session model, retain plan checking, verification and source grounding, and perform targeted phase research where evidence needs updating. Reuse the supplied project research rather than repeating its source audit. Planning approval does not authorize real external operations.

## Phases

- [ ] **Phase 1: Evidence, scope and decisions** — handoff T01
- [ ] **Phase 2: Reproducible development foundation** — handoff T02
- [ ] **Phase 3: Markdown catalog and rule authority** — handoff T03
- [ ] **Phase 4: Static discovery and configuration** — handoff T04
- [ ] **Phase 5: Durable inquiry and backend validation** — handoff T05
- [ ] **Phase 6: Verified guest and staff access** — handoff T06
- [ ] **Phase 7: Approved quotes and authoritative orders** — handoff T07
- [ ] **Phase 8: Durable payments and fault injection** — handoff T08
- [ ] **Phase 9: Selected-bank qualification** — handoff T09
- [ ] **Phase 10: Manual fulfilment and finance** — handoff T10
- [ ] **Phase 11: Isolated hosting and publication** — handoff T11
- [ ] **Phase 12: Recovery and operational readiness** — handoff T12
- [ ] **Phase 13: Integrated release acceptance** — handoff T13
- [ ] **Phase 14: Release package and controlled activation** — handoff T14

## Phase Details

### Phase 1: Evidence, scope and decisions

**Goal:** Deliver the T01 capability with the source-defined acceptance evidence.
**Depends on:** Implementation instruction
**Requirements:** EVID-01, EVID-02, EVID-03
**Source:** Handoff §4 T01; proposal §13; full task acceptance remains normative.
**Estimate:** 2–3 engineer-days
**UI hint:** no
**Plans:** Not created — phase planning pending

**Success Criteria:**

1. Retain the dated audit of all 53 fields, 16 lists/127 values, 242 paired country/phone entries and nine exercised branch predicates, including exact ordering, source IDs and observed versus unverified properties.
2. Keep immutable sll-trial-form-2026-10-19 separate from sll-shop-form-v1 and pending sll-source-to-shop-v1; map every F-01–F-14 change without implying business approval.
3. Maintain one decision register with D-01–D-09 owners, affected capabilities and blocking phase; reuse evidence and make only targeted delta checks.

### Phase 2: Reproducible development foundation

**Goal:** Deliver the T02 capability with the source-defined acceptance evidence.
**Depends on:** Phase 1
**Requirements:** BUILD-01, BUILD-02, BUILD-03
**Source:** Handoff §4 T02; proposal §13; full task acceptance remains normative.
**Estimate:** 3–5 engineer-days
**UI hint:** no
**Plans:** Not created — phase planning pending

**Success Criteria:**

1. Build isolated storefront/backend/worker development environments with real PostgreSQL 18 and synthetic bank/mail/storage fixtures; exclude production data and credentials.
2. Lock verified compatible dependency patches and reproducible application/Nix artifacts with hashes, SBOM and transitive licence notices; verify supported OS at deployment.
3. Define versioned OpenAPI/shared catalog contracts, CI commands and separate runtime/migration/publisher/delivery/evidence/backup identities using the handoff repository layout.

### Phase 3: Markdown catalog and rule authority

**Goal:** Deliver the T03 capability with the source-defined acceptance evidence.
**Depends on:** Phases 1–2
**Requirements:** CAT-01, CAT-02, CAT-03, CAT-04
**Source:** Handoff §4 T03; proposal §13; full task acceptance remains normative.
**Estimate:** 3–4 engineer-days
**UI hint:** no
**Plans:** Not created — phase planning pending

**Success Criteria:**

1. Compile ordinary Markdown/YAML into immutable public/private manifests with shared revision/hash, explicit public allowlist and protected approval records; reject pending/excerpt/test records in prohibited production modes.
2. Validate all frontmatter with a complete strict JSON Schema, generated types, stable IDs, reference integrity, bounded rules and no executable content or conflicting outcomes.
3. Evaluate exactly all/any/not/selected/equals/in/is_present identically in Python and TypeScript using three-valued logic; unknown negation never matches an offer.
4. Validate strict known/unknown/not_applicable tagged answers under approved field-specific rules, Unicode limits and exact integer/decimal/date parsing; retain website/bandwidth text and avoid invented chronology or business limits.

### Phase 4: Static discovery and configuration

**Goal:** Deliver the T04 capability with the source-defined acceptance evidence.
**Depends on:** Phase 3
**Requirements:** SHOP-01, SHOP-02, SHOP-03, SHOP-04
**Source:** Handoff §4 T04; proposal §13; full task acceptance remains normative.
**Estimate:** 4–6 engineer-days
**UI hint:** yes
**Plans:** Not created — phase planning pending

**Success Criteria:**

1. Browse static product/docs pages without personal data or JavaScript, and configure one candidate product with exact source choices/cardinality and explicitly mapped proposed shop changes.
2. Use accessible mobile/keyboard configuration, project/contact, review and action stages with error focus, F-12 clear-with-notice and preservation of unrelated valid answers.
3. Review editable cart lines at quantity 1 per licence scope, with current revision differences requiring reconfirmation; preserve issued quote scope by requesting revisions.
4. Show truthful backend-offline and no-JavaScript assistance through Django /inquiry/simple/; keep contact/confidential drafts out of default browser persistence and keep unsupported Pay actions disabled.

### Phase 5: Durable inquiry and backend validation

**Goal:** Deliver the T05 capability with the source-defined acceptance evidence.
**Depends on:** Phases 2–3
**Requirements:** INQ-01, INQ-02, INQ-03
**Source:** Handoff §4 T05; proposal §13; full task acceptance remains normative.
**Estimate:** 2–4 engineer-days
**UI hint:** yes
**Plans:** Not created — phase planning pending

**Success Criteria:**

1. Persist organizations, contacts, immutable catalog/configuration snapshots, carts and inquiries in PostgreSQL; API validation recomputes applicable profiles and rejects stale hidden/unknown values.
2. Commit inquiry and notification outbox atomically before returning its reference; mail failures retain accessible records, bounded retries and staff ownership/next-action lifecycle.
3. Submit accessible server-rendered /inquiry/simple/ inquiries using the same profiles, response unions, CSRF and validation; enforce spam/request bounds and fixed notification recipients.

### Phase 6: Verified guest and staff access

**Goal:** Deliver the T06 capability with the source-defined acceptance evidence.
**Depends on:** Phase 5
**Requirements:** AUTH-01, AUTH-02, AUTH-03
**Source:** Handoff §4 T06; proposal §13; full task acceptance remains normative.
**Estimate:** 3–5 engineer-days
**UI hint:** yes
**Plans:** Not created — phase planning pending

**Success Criteria:**

1. Exchange expiring rate-limited single-use email challenges for rotated host-only Secure/HttpOnly resource-scoped sessions; GET scanners cannot consume credentials or accept terms.
2. Require explicit grants for each quote/order/invoice/download; IDs, email knowledge and shared domains grant no unrelated access; use CSRF and non-enumerating responses.
3. Enforce TOTP and role/resource permissions on every staff/admin action, with offline recovery and audited session revocation; deny alternate-login bypasses and return 404 for staff routes on the customer host.

### Phase 7: Approved quotes and authoritative orders

**Goal:** Deliver the T07 capability with the source-defined acceptance evidence.
**Depends on:** Phases 3, 5–6
**Requirements:** COM-01, COM-02, COM-03, COM-04
**Source:** Handoff §4 T07; proposal §13; full task acceptance remains normative.
**Estimate:** 3–5 engineer-days
**UI hint:** yes
**Plans:** Not created — phase planning pending

**Success Criteria:**

1. Prepare, approve, issue and supersede immutable quote revisions with entity, configuration/release, rights, price/tax/currency, expiry and terms snapshots; quoted edits require a new revision.
2. Record one attributable quote acceptance with exact terms hashes, verified person, organization, authority and time; atomically map an accepted revision to at most one order across sessions/keys.
3. Compute exact server totals and one-scope quantity; null price/tax/terms prohibit payment; enforce awaiting_review/quote_only/unsupported/purchasable evidence distinctions.
4. Route quote/cart/order checkout through one guarded service with request-bound idempotency, frozen payment_start_deadline and separate bank-session expiry; browser totals never control money.

### Phase 8: Durable payments and fault injection

**Goal:** Deliver the T08 capability with the source-defined acceptance evidence.
**Depends on:** Phase 7
**Requirements:** PAY-01, PAY-02, PAY-03, PAY-04
**Source:** Handoff §4 T08; proposal §13; full task acceptance remains normative.
**Estimate:** 4–6 engineer-days
**UI hint:** yes
**Plans:** Not created — phase planning pending

**Success Criteria:**

1. Claim short PostgreSQL outbox leases, release transactions before network I/O, recover abandoned work and expose retries/dead jobs without Redis or Celery.
2. Persist attempts and verified recoverable prepared archives before payment/capture/refund calls; recheck cancellation/deadline/approval/activation under an order lock immediately before single dispatch.
3. Distinguish preparing from possibly-dispatched uncertain outcomes; callbacks/returns never bypass bank verification, and duplicates/out-of-order events cannot duplicate financial effects or entitlements.
4. Exercise a fault-injectable fake bank for forged returns, wrong context/money, archive failure, cancellation races, lost responses after success, worker crashes and different-key double clicks.

### Phase 9: Selected-bank qualification

**Goal:** Deliver the T09 capability with the source-defined acceptance evidence.
**Depends on:** Phase 8 plus D-04 bank inputs
**Requirements:** BANK-01, BANK-02, BANK-03
**Source:** Handoff §4 T09; proposal §13; full task acceptance remains normative.
**Estimate:** 4–6 engineer-days
**UI hint:** yes
**Plans:** Not created — phase planning pending

**Success Criteria:**

1. Implement only the selected bank documented hosted checkout, raw-body authentication, state mapping, fixed endpoints, allowlisted URLs and supported retry/capture/refund capabilities.
2. Reconcile complete transaction/statement windows including transactions absent locally, with audited export fallback and finance queues for ambiguous/orphan/duplicate outcomes.
3. Record real sandbox evidence for supported protocol/failure scenarios separately from fake-bank tests; live merchant/PCI/fees and transaction authorization remain external gates.

### Phase 10: Manual fulfilment and finance

**Goal:** Deliver the T10 capability with the source-defined acceptance evidence.
**Depends on:** Phases 6–8; independent of Phase 9 while bank inputs wait
**Requirements:** FUL-01, FUL-02, FUL-03, FUL-04
**Source:** Handoff §4 T10; proposal §13; full task acceptance remains normative.
**Estimate:** 3–5 engineer-days
**UI hint:** yes
**Plans:** Not created — phase planning pending

**Success Criteria:**

1. Assign/provision/release manual packages only after technical/NDA/contract/payment prerequisites; enforce unique entitlements and distinguish licence, support and update rights.
2. Archive document number reservations and exact versions before issuance, and archive delivery-grant manifests plus off-region artifact copies before activation; distinguish prepared/completed evidence.
3. Authorize every private invoice/artifact download, use short-lived version-bound bearer URLs with private/no-store metadata and safe filenames, and redact full URLs from logs.
4. Apply approved role/recent-auth/reason refund/dispute/hold policies without rewriting capture history or claiming to retrieve previously downloaded bytes.

### Phase 11: Isolated hosting and publication

**Goal:** Deliver the T11 capability with the source-defined acceptance evidence.
**Depends on:** Phases 2–4; deployed proof requires scoped cloud authorization
**Requirements:** HOST-01, HOST-02, HOST-03, HOST-04
**Source:** Handoff §4 T11; proposal §13; full task acceptance remains normative.
**Estimate:** 2–4 engineer-days
**UI hint:** no
**Plans:** Not created — phase planning pending

**Success Criteria:**

1. Prepare new-VM NixOS/native hardened systemd services with pinned supported OS and separated identities; preserve existing-host isolation and document optional Podman fallback.
2. Route customer API/simple form to Django, deny staff paths on customer host, and expose staff-only hostname without S3 fallback; proxy public objects over verified HTTPS Host/SNI with credential/header stripping.
3. Publish complete immutable prefixes and permanent content-addressed assets, verify route/MIME/hash completeness and switch one validated Caddy manifest; interruption/rollback preserve cached-page assets.
4. Prove actual OVH object ACL denials, region/retention behavior, 308/404/502 distinctions, GET/HEAD/304/compression and traversal rejection on an authorized test deployment.

### Phase 12: Recovery and operational readiness

**Goal:** Deliver the T12 capability with the source-defined acceptance evidence.
**Depends on:** Phases 8, 10–11; Phase 9 for real-bank proof
**Requirements:** OPS-01, OPS-02, OPS-03, OPS-04, OPS-05
**Source:** Handoff §4 T12; proposal §13; full task acceptance remains normative.
**Estimate:** 3–5 engineer-days
**UI hint:** no
**Plans:** Not created — phase planning pending

**Success Criteria:**

1. Configure encrypted off-region pgBackRest base/differential backups and continuous WAL/PITR with separate mutable backup/evidence namespaces and independent key/artifact recovery.
2. Establish recovery controls before exposing restored DB: block mutating bank/SMTP/ordinary workers, invalidate recovered sessions and permit controlled read-only reconciliation only.
3. Restore past later payment/refund/document/delivery events; reconcile complete bank windows and archived prepared/completed records, recover exact acceptances and numbering high-water marks without duplicate grants or reused numbers.
4. Measure proposed 15-minute DB RPO and four-hour operator-start restore target separately from outage detection/response and safe reopening; hold ambiguous cases and downloads until relevant reconciliation.
5. Expose activity-aware WAL backlog, payment/mail/job/fulfilment/certificate/capacity alarms and named-owner incident/restore runbooks; no idle-DB false alarm or implicit existing-monitoring changes.

### Phase 13: Integrated release acceptance

**Goal:** Deliver the T13 capability with the source-defined acceptance evidence.
**Depends on:** Phases 4, 6–12; external evidence conditional
**Requirements:** UAT-01, UAT-02, UAT-03
**Source:** Handoff §4 T13; proposal §13; full task acceptance remains normative.
**Estimate:** 2–4 engineer-days
**UI hint:** yes
**Plans:** Not created — phase planning pending

**Success Criteria:**

1. Exercise complete inquiry/mail-outage, quote/payment/delivery and approved-fixture direct-purchase journeys across components, including archive/worker failure and cross-customer/MFA/refund controls.
2. Check mobile/keyboard/no-JavaScript/backend-down behavior, all source/value/branch mappings and F-01–F-14 change coverage, plus representative load and publication rollback.
3. Scan static output/maps/bundles/public objects and sensitive logs for private material; report executed commands, environment-specific evidence, residual risks and pending bank/cloud proofs.

### Phase 14: Release package and controlled activation

**Goal:** Deliver the T14 capability with the source-defined acceptance evidence.
**Depends on:** Prior applicable tasks plus D-01–D-09 activation inputs
**Requirements:** REL-01, REL-02, REL-03
**Source:** Handoff §4 T14; proposal §13; full task acceptance remains normative.
**Estimate:** 2–3 engineer-days
**UI hint:** no
**Plans:** Not created — phase planning pending

**Success Criteria:**

1. Produce reviewable release commit/artifact hashes, supported OS/runtime lock, migrations, approved catalog/legal/offer references, operators, scoped deployment/DNS/cutover and rollback plans.
2. Prevent live activation with fake adapters, synthetic prices/terms, unapproved profiles or missing bank/recovery/archive/operational proof; expose unresolved readiness items.
3. Execute production, old-trial-page changes or real payment/refund tests only under their separately scoped instructions; report actual checks and rollback readiness without marking pending activation complete.

