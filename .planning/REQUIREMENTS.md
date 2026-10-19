# Requirements: Synaptic Laboratories IP Shop

**Defined:** 2026-10-19
**Status:** Source-derived planning baseline retained with the 14-phase roadmap; no implementation or business approval implied.
**Core Value:** Turn a reviewed IP configuration into an attributable agreement, verified payment and authorized delivery without losing commercial evidence or duplicating financial/licence effects.

## v1 Requirements

### Evidence, scope and decisions

- [ ] **EVID-01**: Retain the dated audit of all 53 fields, 16 lists/127 values, 242 paired country/phone entries and nine exercised branch predicates, including exact ordering, source IDs and observed versus unverified properties.
- [ ] **EVID-02**: Keep immutable sll-trial-form-2026-10-19 separate from sll-shop-form-v1 and pending sll-source-to-shop-v1; map every F-01–F-14 change without implying business approval.
- [ ] **EVID-03**: Maintain one decision register with D-01–D-09 owners, affected capabilities and blocking phase; reuse evidence and make only targeted delta checks.

### Reproducible development foundation

- [ ] **BUILD-01**: Build isolated storefront/backend/worker development environments with real PostgreSQL 18 and synthetic bank/mail/storage fixtures; exclude production data and credentials.
- [ ] **BUILD-02**: Lock verified compatible dependency patches and reproducible application/Nix artifacts with hashes, SBOM and transitive licence notices; verify supported OS at deployment.
- [ ] **BUILD-03**: Define versioned OpenAPI/shared catalog contracts, CI commands and separate runtime/migration/publisher/delivery/evidence/backup identities using the handoff repository layout.

### Markdown catalog and rule authority

- [ ] **CAT-01**: Compile ordinary Markdown/YAML into immutable public/private manifests with shared revision/hash, explicit public allowlist and protected approval records; reject pending/excerpt/test records in prohibited production modes.
- [ ] **CAT-02**: Validate all frontmatter with a complete strict JSON Schema, generated types, stable IDs, reference integrity, bounded rules and no executable content or conflicting outcomes.
- [ ] **CAT-03**: Evaluate exactly all/any/not/selected/equals/in/is_present identically in Python and TypeScript using three-valued logic; unknown negation never matches an offer.
- [ ] **CAT-04**: Validate strict known/unknown/not_applicable tagged answers under approved field-specific rules, Unicode limits and exact integer/decimal/date parsing; retain website/bandwidth text and avoid invented chronology or business limits.

### Static discovery and configuration

- [ ] **SHOP-01**: Browse static product/docs pages without personal data or JavaScript, and configure one candidate product with exact source choices/cardinality and explicitly mapped proposed shop changes.
- [ ] **SHOP-02**: Use accessible mobile/keyboard configuration, project/contact, review and action stages with error focus, F-12 clear-with-notice and preservation of unrelated valid answers.
- [ ] **SHOP-03**: Review editable cart lines at quantity 1 per licence scope, with current revision differences requiring reconfirmation; preserve issued quote scope by requesting revisions.
- [ ] **SHOP-04**: Show truthful backend-offline and no-JavaScript assistance through Django /inquiry/simple/; keep contact/confidential drafts out of default browser persistence and keep unsupported Pay actions disabled.

### Durable inquiry and backend validation

- [ ] **INQ-01**: Persist organizations, contacts, immutable catalog/configuration snapshots, carts and inquiries in PostgreSQL; API validation recomputes applicable profiles and rejects stale hidden/unknown values.
- [ ] **INQ-02**: Commit inquiry and notification outbox atomically before returning its reference; mail failures retain accessible records, bounded retries and staff ownership/next-action lifecycle.
- [ ] **INQ-03**: Submit accessible server-rendered /inquiry/simple/ inquiries using the same profiles, response unions, CSRF and validation; enforce spam/request bounds and fixed notification recipients.

### Verified guest and staff access

- [ ] **AUTH-01**: Exchange expiring rate-limited single-use email challenges for rotated host-only Secure/HttpOnly resource-scoped sessions; GET scanners cannot consume credentials or accept terms.
- [ ] **AUTH-02**: Require explicit grants for each quote/order/invoice/download; IDs, email knowledge and shared domains grant no unrelated access; use CSRF and non-enumerating responses.
- [ ] **AUTH-03**: Enforce TOTP and role/resource permissions on every staff/admin action, with offline recovery and audited session revocation; deny alternate-login bypasses and return 404 for staff routes on the customer host.

### Approved quotes and authoritative orders

- [ ] **COM-01**: Prepare, approve, issue and supersede immutable quote revisions with entity, configuration/release, rights, price/tax/currency, expiry and terms snapshots; quoted edits require a new revision.
- [ ] **COM-02**: Record one attributable quote acceptance with exact terms hashes, verified person, organization, authority and time; atomically map an accepted revision to at most one order across sessions/keys.
- [ ] **COM-03**: Compute exact server totals and one-scope quantity; null price/tax/terms prohibit payment; enforce awaiting_review/quote_only/unsupported/purchasable evidence distinctions.
- [ ] **COM-04**: Route quote/cart/order checkout through one guarded service with request-bound idempotency, frozen payment_start_deadline and separate bank-session expiry; browser totals never control money.

### Durable payments and fault injection

- [ ] **PAY-01**: Claim short PostgreSQL outbox leases, release transactions before network I/O, recover abandoned work and expose retries/dead jobs without Redis or Celery.
- [ ] **PAY-02**: Persist attempts and verified recoverable prepared archives before payment/capture/refund calls; recheck cancellation/deadline/approval/activation under an order lock immediately before single dispatch.
- [ ] **PAY-03**: Distinguish preparing from possibly-dispatched uncertain outcomes; callbacks/returns never bypass bank verification, and duplicates/out-of-order events cannot duplicate financial effects or entitlements.
- [ ] **PAY-04**: Exercise a fault-injectable fake bank for forged returns, wrong context/money, archive failure, cancellation races, lost responses after success, worker crashes and different-key double clicks.

### Selected-bank qualification

- [ ] **BANK-01**: Implement only the selected bank documented hosted checkout, raw-body authentication, state mapping, fixed endpoints, allowlisted URLs and supported retry/capture/refund capabilities.
- [ ] **BANK-02**: Reconcile complete transaction/statement windows including transactions absent locally, with audited export fallback and finance queues for ambiguous/orphan/duplicate outcomes.
- [ ] **BANK-03**: Record real sandbox evidence for supported protocol/failure scenarios separately from fake-bank tests; live merchant/PCI/fees and transaction authorization remain external gates.

### Manual fulfilment and finance

- [ ] **FUL-01**: Assign/provision/release manual packages only after technical/NDA/contract/payment prerequisites; enforce unique entitlements and distinguish licence, support and update rights.
- [ ] **FUL-02**: Archive document number reservations and exact versions before issuance, and archive delivery-grant manifests plus off-region artifact copies before activation; distinguish prepared/completed evidence.
- [ ] **FUL-03**: Authorize every private invoice/artifact download, use short-lived version-bound bearer URLs with private/no-store metadata and safe filenames, and redact full URLs from logs.
- [ ] **FUL-04**: Apply approved role/recent-auth/reason refund/dispute/hold policies without rewriting capture history or claiming to retrieve previously downloaded bytes.

### Isolated hosting and publication

- [ ] **HOST-01**: Prepare new-VM NixOS/native hardened systemd services with pinned supported OS and separated identities; preserve existing-host isolation and document optional Podman fallback.
- [ ] **HOST-02**: Route customer API/simple form to Django, deny staff paths on customer host, and expose staff-only hostname without S3 fallback; proxy public objects over verified HTTPS Host/SNI with credential/header stripping.
- [ ] **HOST-03**: Publish complete immutable prefixes and permanent content-addressed assets, verify route/MIME/hash completeness and switch one validated Caddy manifest; interruption/rollback preserve cached-page assets.
- [ ] **HOST-04**: Prove actual OVH object ACL denials, region/retention behavior, 308/404/502 distinctions, GET/HEAD/304/compression and traversal rejection on an authorized test deployment.

### Recovery and operational readiness

- [ ] **OPS-01**: Configure encrypted off-region pgBackRest base/differential backups and continuous WAL/PITR with separate mutable backup/evidence namespaces and independent key/artifact recovery.
- [ ] **OPS-02**: Establish recovery controls before exposing restored DB: block mutating bank/SMTP/ordinary workers, invalidate recovered sessions and permit controlled read-only reconciliation only.
- [ ] **OPS-03**: Restore past later payment/refund/document/delivery events; reconcile complete bank windows and archived prepared/completed records, recover exact acceptances and numbering high-water marks without duplicate grants or reused numbers.
- [ ] **OPS-04**: Measure proposed 15-minute DB RPO and four-hour operator-start restore target separately from outage detection/response and safe reopening; hold ambiguous cases and downloads until relevant reconciliation.
- [ ] **OPS-05**: Expose activity-aware WAL backlog, payment/mail/job/fulfilment/certificate/capacity alarms and named-owner incident/restore runbooks; no idle-DB false alarm or implicit existing-monitoring changes.

### Integrated release acceptance

- [ ] **UAT-01**: Exercise complete inquiry/mail-outage, quote/payment/delivery and approved-fixture direct-purchase journeys across components, including archive/worker failure and cross-customer/MFA/refund controls.
- [ ] **UAT-02**: Check mobile/keyboard/no-JavaScript/backend-down behavior, all source/value/branch mappings and F-01–F-14 change coverage, plus representative load and publication rollback.
- [ ] **UAT-03**: Scan static output/maps/bundles/public objects and sensitive logs for private material; report executed commands, environment-specific evidence, residual risks and pending bank/cloud proofs.

### Release package and controlled activation

- [ ] **REL-01**: Produce reviewable release commit/artifact hashes, supported OS/runtime lock, migrations, approved catalog/legal/offer references, operators, scoped deployment/DNS/cutover and rollback plans.
- [ ] **REL-02**: Prevent live activation with fake adapters, synthetic prices/terms, unapproved profiles or missing bank/recovery/archive/operational proof; expose unresolved readiness items.
- [ ] **REL-03**: Execute production, old-trial-page changes or real payment/refund tests only under their separately scoped instructions; report actual checks and rollback readiness without marking pending activation complete.

## v2 / Deferred Scope

No additional features committed. Reconsider organization accounts, more products, currencies or automated licensing only through a later scoped decision.

## Out of Scope

| Feature | Reason |
|---|---|
| Automated licences, recurring billing, saved cards, FX, complex discounts | Explicit v1 exclusions |
| Full WordPress migration or historical Monday import/deletion | Separate website/data-lifecycle scope |
| Customer uploads, analytics, external identity/queue/CMS | Not required for selected first-release design |
| Manual bank transfer | Optional separately reconciled method; not required |

## Traceability

| Requirement | Phase | Status |
|---|---|---|
| EVID-01 | Phase 1 | Pending |
| EVID-02 | Phase 1 | Pending |
| EVID-03 | Phase 1 | Pending |
| BUILD-01 | Phase 2 | Pending |
| BUILD-02 | Phase 2 | Pending |
| BUILD-03 | Phase 2 | Pending |
| CAT-01 | Phase 3 | Pending |
| CAT-02 | Phase 3 | Pending |
| CAT-03 | Phase 3 | Pending |
| CAT-04 | Phase 3 | Pending |
| SHOP-01 | Phase 4 | Pending |
| SHOP-02 | Phase 4 | Pending |
| SHOP-03 | Phase 4 | Pending |
| SHOP-04 | Phase 4 | Pending |
| INQ-01 | Phase 5 | Pending |
| INQ-02 | Phase 5 | Pending |
| INQ-03 | Phase 5 | Pending |
| AUTH-01 | Phase 6 | Pending |
| AUTH-02 | Phase 6 | Pending |
| AUTH-03 | Phase 6 | Pending |
| COM-01 | Phase 7 | Pending |
| COM-02 | Phase 7 | Pending |
| COM-03 | Phase 7 | Pending |
| COM-04 | Phase 7 | Pending |
| PAY-01 | Phase 8 | Pending |
| PAY-02 | Phase 8 | Pending |
| PAY-03 | Phase 8 | Pending |
| PAY-04 | Phase 8 | Pending |
| BANK-01 | Phase 9 | Pending |
| BANK-02 | Phase 9 | Pending |
| BANK-03 | Phase 9 | Pending |
| FUL-01 | Phase 10 | Pending |
| FUL-02 | Phase 10 | Pending |
| FUL-03 | Phase 10 | Pending |
| FUL-04 | Phase 10 | Pending |
| HOST-01 | Phase 11 | Pending |
| HOST-02 | Phase 11 | Pending |
| HOST-03 | Phase 11 | Pending |
| HOST-04 | Phase 11 | Pending |
| OPS-01 | Phase 12 | Pending |
| OPS-02 | Phase 12 | Pending |
| OPS-03 | Phase 12 | Pending |
| OPS-04 | Phase 12 | Pending |
| OPS-05 | Phase 12 | Pending |
| UAT-01 | Phase 13 | Pending |
| UAT-02 | Phase 13 | Pending |
| UAT-03 | Phase 13 | Pending |
| REL-01 | Phase 14 | Pending |
| REL-02 | Phase 14 | Pending |
| REL-03 | Phase 14 | Pending |

**Coverage:** 50 v1 requirements; 50 mapped exactly once; 0 unmapped.

*Last updated: 2026-10-19 after draft roadmap mapping.*
