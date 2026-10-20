# Roadmap: SLL xSPI-MC Shop

**Baseline:** 2026-10-20, fully rebuilt from the new proposal/handoff. All phases pending; no old task completion carries forward.

## Scope and execution policy

The new T01–T14 structure is retained because its dependencies and acceptance define the supplied project. This is a source-defined dependency plan. All requirements map to exactly one primary phase; cross-cutting integration is proved in T13. Detailed executable PLAN.md files are created by plan-phase before implementation; this roadmap does not claim execution.

Current authorization covers planning/documentation. Begin application implementation only under its instruction. Thereafter complete unaffected local/synthetic work while particular bank/cloud/legal inputs wait. T09 can wait while T10 and T11 proceed after their prerequisites. T04 supplies the UI contract and fallback presentation; T05 provides persistence; T06 provides private host access; T07 proves their joined checkout. Do not expose a private editor before its authorization boundary exists.

Preserve actual dependencies rather than forcing sequential task order or unrestricted parallelism. Pin current verified software at T02, qualify actual bank at T09, quote/DNS/TLS/storage at T11, retained recovery at T12 and activation readiness at T14. Synthetic proof never closes an external gate.

**Estimate:** Supplied implementation range 46–74 engineer-days, excluding external waiting/ongoing operations. No implementation tests have run.

## Phases

- [ ] **Phase 1: Product authority, repository review and decision register** — new handoff T01
- [ ] **Phase 2: Reproducible application and deployment skeleton** — new handoff T02
- [ ] **Phase 3: Markdown catalog, schemas and approved price calculations** — new handoff T03
- [ ] **Phase 4: Static product, configurator, support page and accessible fallback** — new handoff T04
- [ ] **Phase 5: Transactional records, durable work and private evidence primitives** — new handoff T05
- [ ] **Phase 6: Verified customer access, staff MFA and private host editing** — new handoff T06
- [ ] **Phase 7: Multi-line cart, quotations, business checkout and acceptance** — new handoff T07
- [ ] **Phase 8: Payment domain and fault-injectable fake bank** — new handoff T08
- [ ] **Phase 9: Selected-bank sandbox integration and complete reconciliation** — new handoff T09
- [ ] **Phase 10: Licence delivery, renewal/rehosting and support-hours workflows** — new handoff T10
- [ ] **Phase 11: OVH deployment, Route 53, dedicated TLS and static publication** — new handoff T11
- [ ] **Phase 12: Backups, operating alerts and financial/licensing restore rehearsal** — new handoff T12
- [ ] **Phase 13: Integrated product, access, payment and deployment acceptance** — new handoff T13
- [ ] **Phase 14: Release handover and separately scoped live activation** — new handoff T14

## Phase Details

### Phase 1: Product authority, repository review and decision register

**Goal:** Operators can verify the exact embedded product snapshot by filename, 23,969-byte length and SHA-256, using only the October 20 package as new product authority.
**Depends on:** An implementation instruction
**Requirements:** SRC-01, SRC-02, SRC-03, SRC-04
**Source:** SLL-xSPI-MC-Shop-Codex-Handoff-2026-10-20.md T01; companion proposal.
**Estimate:** 1–2 engineer-days
**UI hint:** no
**Plans:** 2/2 executed; clean independent code review; four human-verification items pending in 01-UAT.md.

**Wave 1**

- [x] 01-01-PLAN.md — Source provenance tracer and repository scope (Wave 1; SRC-01, SRC-02, SRC-04).

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 01-02-PLAN.md — Complete source traceability, decision-register repair and T01 evidence (Wave 2; depends on 01-01; SRC-01–SRC-04).

**Success Criteria:**

1. Operators can verify the exact embedded product snapshot by filename, 23,969-byte length and SHA-256, using only the October 20 package as new product authority.
2. Reviewers can trace all three ordered vendors, thirteen families, thirteen logical controls, nineteen checkout groups, two helpers, four IP declarations and separate marketing control to source locations.
3. Operators can inspect one P-01–P-12 register with status, owner, evidence and the exact affected live operation; pending decisions do not block unrelated planning.
4. Reviewers can identify repository scope, new product/profile IDs, superseded assumptions and customer hostname without treating old task completion as new acceptance.

**Required outputs:** Record the supplied product definition and embedded source hash; inventory the three vendors, 13 families, terms, bands, access controls, 19 business-checkout groups, four required declarations and separate marketing choice. Establish sll-xspi-mc, sll-xspi-mc-support-10h and sll-xspi-mc-v1. Inspect any existing repository/worktree, instructions and implementation before changes; document the new scope and one decision register with approval status and affected phase.

**Normative acceptance:** Use this revision's product authority exclusively. Earlier task completion does not establish compliance with this task list. Retire superseded implementation assumptions in the authorized checkout, without deleting unrelated work or historical business records. All source placeholders/provisional assumptions remain explicitly pending; recording mapping/approval status does not block local implementation. The authoritative customer hostname is shop.xspi.pro.

**Verification/evidence:** Source filename/hash and new requirement matrix; repository status and isolated working branch; recorded decisions P-01–P-12; exact product/profile IDs; scope/delta note.

### Phase 2: Reproducible application and deployment skeleton

**Goal:** Developers can reproduce static frontend, Django/worker and real-PostgreSQL development builds from compatible pinned dependencies, hashes and CI commands.
**Depends on:** T01
**Requirements:** BUILD-01, BUILD-02, BUILD-03, BUILD-04
**Source:** SLL-xSPI-MC-Shop-Codex-Handoff-2026-10-20.md T02; companion proposal.
**Estimate:** 3–5 engineer-days
**UI hint:** no
**Plans:** Not created; detailed planning pending.

**Success Criteria:**

1. Developers can reproduce static frontend, Django/worker and real-PostgreSQL development builds from compatible pinned dependencies, hashes and CI commands.
2. Reviewers can inspect component/transitive licences and SBOM for the actual locked artifacts; exact patches are verified when lockfiles are created.
3. Developers can run isolated synthetic bank/mail/storage fixtures and versioned OpenAPI/schema contracts without production credentials or external provisioning.
4. Operators can review native hardened service, image/bootstrap, secret and environment templates for isolated B2-7 deployment and configurable B3-8 fallback.

**Required outputs:** Static Astro/React project, Django/application/worker skeleton, PostgreSQL development service, supported dependency lockfiles and licence inventory, CI checks, synthetic mail/bank/storage boundaries, OpenAPI and full-schema scaffolding, native NixOS service modules and environment/secret templates. Prepare the OVH image/bootstrap qualification plan without provisioning.

**Normative acceptance:** Clean local build reproduces artifacts from pinned versions; no runtime Astro/Node server or mandatory Redis/Celery/CMS/IdP. Keep the new VM independent of existing production state. B2-7 monthly is a planning selection, not permission to spend; support the documented B3-8 fallback through configuration. A supported OS and exact Nixpkgs revision are chosen at actual deployment. No secrets in Git, Nix store derivations or static output.

**Verification/evidence:** Build commands/results, lockfile/artifact identities, component and transitive licence/SBOM record, environment/service-boundary diagram and actual dependency compatibility checks.

### Phase 3: Markdown catalog, schemas and approved price calculations

**Goal:** Editors can compile one reviewed Markdown/YAML catalog into immutable public/private manifests with the same revision; incomplete approvals cannot be activated through editable content.
**Depends on:** T01–T02
**Requirements:** CAT-01, CAT-02, CAT-03, CAT-04, CAT-05
**Source:** SLL-xSPI-MC-Shop-Codex-Handoff-2026-10-20.md T03; companion proposal.
**Estimate:** 4–6 engineer-days
**UI hint:** no
**Plans:** Not created; detailed planning pending.

**Success Criteria:**

1. Editors can compile one reviewed Markdown/YAML catalog into immutable public/private manifests with the same revision; incomplete approvals cannot be activated through editable content.
2. Both browser and backend validate exact vendor/family/term/band relationships through strict schemas, cross-file checks and bounded predicates/named validators with shared conformance cases.
3. Customers receive draft, invalid, requires_quote, awaiting_review or purchasable results with structured reasons; unknown necessary coverage/rights/access/prices remain unpurchasable.
4. Price calculations use bounded exact minor-unit integers, approved per-licence allowances and distinct family coverage, with annual/one-time/tax components and recurrence; provisional five-plus-five/€50 values never become live rates.
5. Public output excludes private approvals, host instances, implementation comments and unresolved production placeholders; labelled synthetic examples remain distinguishable.

**Required outputs:** One versioned Markdown/YAML catalog; full strict schemas and cross-file integrity checks; public/private immutable manifests; exact new option taxonomy; bounded declarative predicates/named validators; approved access/coverage/rate/terms profiles; consistent browser/backend conformance fixtures. Complete the proposal examples into production schemas rather than treating the examples as complete validators.

**Normative acceptance:** Validate vendor-family/term/band relationships, unique coverage, enabled-mode counts, disabled-mode reset, host-row cardinality and non-Altera profile gating. Distinguish source draft, approval and production eligibility. No arbitrary executable content. Reject missing rates instead of using zero; apply allowances per configured licence, never per family, and only if approved. Separate annual and one-time components, support quantity and tax category. Public output excludes private approvals/host IDs/internal comments and unresolved placeholders. Unapproved examples may run only in labelled local/synthetic mode.

**Verification/evidence:** Parsed catalog and schema checks, exact vendor/family list comparison, valid/invalid/quote/review cases in both runtimes, provisional node-price boundary cases and annual-versus-one-time calculation evidence.

### Phase 4: Static product, configurator, support page and accessible fallback

**Goal:** Customers can read static product/support/legal pages and select only the exact ordered vendor/family/term/band options, including Altera-only RDP and higher-volume quotation.
**Depends on:** T03
**Requirements:** SHOP-01, SHOP-02, SHOP-03, SHOP-04, SHOP-05
**Source:** SLL-xSPI-MC-Shop-Codex-Handoff-2026-10-20.md T04; companion proposal.
**Estimate:** 4–6 engineer-days
**UI hint:** yes
**Plans:** Not created; detailed planning pending.

**Success Criteria:**

1. Customers can read static product/support/legal pages and select only the exact ordered vendor/family/term/band options, including Altera-only RDP and higher-volume quotation.
2. Customers can change vendor, term, access modes and counts with the specified notice/reset behavior while unrelated details/support persist; fixed-row reductions allow choice/cancel and cleared host data never revives.
3. Customers see accessible labelled controls, keyboard/mobile behavior, error focus and state-appropriate actions with separate annual/one-time prices and optional unticked marketing.
4. Customers can use Django /purchase/simple/ without JavaScript under the same domain rules; backend failure gives truthful status and does not claim persistence or payment.
5. Customers see masked host summaries and no raw host IDs, private links, business/tax records or keys in public bundles, URLs or default browser storage.

**Required outputs:** Static product/support/document pages, React configuration and price summary, separate licence/support cart presentation, quote request entry, country-aware checkout presentation, accessible errors and no-JavaScript Django purchase/simple flow using shared rules. Protected host editing integrates with T06.

**Normative acceptance:** Match all approved source options and declared requiredness; vendor/term/access changes clear only affected configuration and host data with notice. Show RDP only for Altera, exact nonoverlapping volume bands, higher-volume quotation, and permitted fixed/floating controls. Preserve unrelated business details and recoverable selections. Mask host IDs in summaries. Show annual and one-time costs separately, the correct action for eligibility state and useful offline behavior. Marketing is optional and unticked; implementation notes never become customer copy.

**Verification/evidence:** Representative mobile/keyboard/screen-reader checks, all conditional/reset branches, state-specific screenshots or sanitized captures, no-JavaScript path, public bundle inspection and customer-facing copy review.

### Phase 5: Transactional records, durable work and private evidence primitives

**Goal:** Business records for contacts, configuration/host revisions, quotes/orders, acceptance, money, licensing, support and evidence are persisted with reconstructable immutable snapshots.
**Depends on:** T02–T03
**Requirements:** DATA-01, DATA-02, DATA-03, DATA-04
**Source:** SLL-xSPI-MC-Shop-Codex-Handoff-2026-10-20.md T05; companion proposal.
**Estimate:** 3–5 engineer-days
**UI hint:** no
**Plans:** Not created; detailed planning pending.

**Success Criteria:**

1. Business records for contacts, configuration/host revisions, quotes/orders, acceptance, money, licensing, support and evidence are persisted with reconstructable immutable snapshots.
2. Committed domain work and notification outbox entries survive crashes through short leases and bounded retries; uniqueness and idempotency protect all intended effect identities.
3. Workers release database transactions before network calls and recover abandoned work without duplicate domain effects, demonstrated with real PostgreSQL.
4. Archive primitives verify recoverable object version/hash/retention and distinguish prepared from completed evidence; error/log paths redact sensitive values.

**Required outputs:** Migrations/domain services for organizations, contacts, configured lines/host-binding revisions, quotes/orders, acceptance, financial records, licensing, support and evidence references; durable outbox/inbox, idempotency records, bounded leases/retry rules and synthetic notifications.

**Normative acceptance:** Persist business records before scheduling notification. Concurrency/uniqueness constraints protect line, quote, order, payment, document, licence and support identities. Worker crashes do not lose committed work; lease recovery cannot duplicate a domain effect. No long transaction spans network calls. Source configuration and acceptance snapshots are immutable and reconstructable. Host identifiers and credentials are redacted in error/log paths.

**Verification/evidence:** Migration/reversal plan, focused transactional and lease-crash checks, schema/constraint evidence, redaction verification and clear prepared-versus-completed evidence semantics.

### Phase 6: Verified customer access, staff MFA and private host editing

**Goal:** Customers exchange deliberate single-use email verification for rotated resource-scoped host-only secure sessions; GET scanners/replay do not consume credentials or accept contracts.
**Depends on:** T04–T05
**Requirements:** AUTH-01, AUTH-02, AUTH-03, AUTH-04, AUTH-05, AUTH-06
**Source:** SLL-xSPI-MC-Shop-Codex-Handoff-2026-10-20.md T06; companion proposal.
**Estimate:** 3–5 engineer-days
**UI hint:** yes
**Plans:** Not created; detailed planning pending.

**Success Criteria:**

1. Customers exchange deliberate single-use email verification for rotated resource-scoped host-only secure sessions; GET scanners/replay do not consume credentials or accept contracts.
2. Purchasing, invoice and technical contacts receive explicit verified memberships; cross-customer/domain equality grants no unrelated resource access.
3. Every staff/admin/custom privileged route requires MFA and role/resource permission, with recent verification for sensitive actions and safe recovery; customer hostname returns 404 for staff aliases.
4. Authorized customers edit encrypted key-versioned host bindings under revision control, using actual manager-specific normalization and duplicate rules; fixed rows match nodes and floating seats use the approved server model.
5. Private raw-host access, CSRF/origin controls, key recovery and revocation are audited; unknown manager profiles hold qualification without inventing a universal MAC format. Customers can independently withdraw marketing preference without affecting service messages or paid rights.

**Required outputs:** Resource-scoped verified-email sessions, staff MFA/recovery and role enforcement, separate customer/staff host boundaries, protected configuration/host editor, raw-host encryption/key-version handling, explicit purchaser/invoice/technical contact membership and marketing withdrawal.

**Normative acceptance:** Use shop.xspi.pro and proposed shop-admin.xspi.pro with separate host-only cookies and no wildcard CORS. Customer host rejects all staff aliases. Email-domain equality grants no organization access; scanners cannot consume access credentials by GET alone. All privileged custom routes require MFA. Validate host IDs using an approved actual-manager profile rather than a universal MAC regex. Fixed rows match selected nodes; floating seats use the approved server model. Unknown formats block key qualification, not generic UI development. Mask ordinary responses, avoid host values in browser storage/URLs/logs, and qualify reauthentication for sensitive changes.

**Verification/evidence:** Cross-customer/contact/role denial cases, scanner/replay/session/CSRF checks, raw-host data-flow inspection, canonicalization/duplicate cases for the actual supplied profile, private encryption/recovery key-version checks using synthetic values.

### Phase 7: Multi-line cart, quotations, business checkout and acceptance

**Goal:** Customers retain separate configured IP lines at quantity one across vendors and explicit duplicate scopes; support has positive real package quantity and zero selector value omits its line.
**Depends on:** T03,T05–T06
**Requirements:** COM-01, COM-02, COM-03, COM-04, COM-05, COM-06
**Source:** SLL-xSPI-MC-Shop-Codex-Handoff-2026-10-20.md T07; companion proposal.
**Estimate:** 4–6 engineer-days
**UI hint:** yes
**Plans:** Not created; detailed planning pending.

**Success Criteria:**

1. Customers retain separate configured IP lines at quantity one across vendors and explicit duplicate scopes; support has positive real package quantity and zero selector value omits its line.
2. Customers review exactly the selected line IDs/revisions; any review/quote-only line blocks combined payment until explicit cart editing or a combined quote, with no silent dropping/splitting/merging.
3. Quotes freeze immutable scope, host, component price, tax, document and validity versions; one accepted revision produces one acceptance/order across browser sessions and idempotency keys.
4. Business checkout preserves nineteen source groups with country-aware applicability and approved tax/status options; same-as helpers resolve final values and purchaser/licensee differences enter review.
5. IP orders capture all four exact versioned declarations, support-only orders capture applicable general/support/refund terms and owner/quantity without IP fields, and mixed orders accept both document sets. One guarded review/acceptance service rejects tampered totals and stale catalog/host/terms/entity revisions, records signatory/authority/hashes/time and separates quote validity, order payment-start deadline and bank-session expiry.

**Required outputs:** Multi-vendor carts with one licence scope per line, real support package quantities/support-only carts, immutable quotes, backend totals and tax decision adapter, country-aware business fields, exact document/declaration acceptance, one order conversion and separate quote/payment deadlines.

**Normative acceptance:** Never merge/double configured licence entitlements through generic quantity. A basket with an unapproved line cannot silently drop it or charge a partial basket. Verify the same reviewed scope and host-binding revision at acceptance/payment. Reject price tampering and stale changes; no silent repricing. One quote revision produces one acceptance/order across sessions and keys. The acknowledgements required by the applicable checkout profile remain separate from optional marketing; IP-containing orders preserve the four source declarations. Invoice/technical contacts and differing licensed entities follow approved review rules. Approved live tax/legal values can remain pending while synthetic flows work. Support-only checkout uses applicable support terms and owner/quantity confirmation with no IP configuration or new IP entitlement; mixed orders accept both applicable document sets.

**Verification/evidence:** Full direct and quoted multi-line journeys, two-browser acceptance race, stale catalog/host/price/terms cases, synthetic tax/rounding and annual/one-time component tests, support-only purchase review. Include a support-only top-up with no vendor/family/host data and mixed-cart term applicability.

### Phase 8: Payment domain and fault-injectable fake bank

**Goal:** Payment preparation commits order/acceptance/attempt/reference identities, archives recoverable snapshots, then rechecks cancellation/deadline/holds/activation before one dispatch claim.
**Depends on:** T05,T07
**Requirements:** PAY-01, PAY-02, PAY-03, PAY-04, PAY-05
**Source:** SLL-xSPI-MC-Shop-Codex-Handoff-2026-10-20.md T08; companion proposal.
**Estimate:** 4–6 engineer-days
**UI hint:** yes
**Plans:** Not created; detailed planning pending.

**Success Criteria:**

1. Payment preparation commits order/acceptance/attempt/reference identities, archives recoverable snapshots, then rechecks cancellation/deadline/holds/activation before one dispatch claim.
2. A potentially dispatched timeout is uncertain and cannot trigger a blind second charge; preparing means no known dispatch and browser navigation cannot confirm money.
3. Only authenticated matched merchant/currency/amount/reference observations can confirm financial facts; durable bounded callbacks distinguish notification hints from payment evidence.
4. Retries, different keys, reordered callbacks and two successful captures preserve both money events, one intended fulfilment and a finance overpayment case.
5. Capture/refund intents are archived before supported effects and preserve requested/uncertain/confirmed history; fake-bank fault injection covers crashes, archive failure, cancellation and ambiguous success.

**Required outputs:** Typed bank-adapter boundary/capability record, hosted-payment preparation, protected archive-before-dispatch ordering, normalized financial observations, durable callback inbox, reconciliation and finance exception workflows, fake-bank scenarios for uncertain/missing/duplicate outcomes.

**Normative acceptance:** Commit order/attempt/reference then archive recoverable snapshots before bank calls. Recheck cancellation/deadline/approval/live state after archive waits before claiming dispatch. Treat network ambiguity as uncertain; browser return is never payment proof. Enforce exact order/merchant/currency/amount matches and supported authorization/capture distinctions. Different idempotency keys cannot cause concurrent blind charges. Duplicate captured attempts create one intended entitlement and an overpayment case. Preserve original financial history and archive refund/capture intents too.

**Verification/evidence:** Injected pre/post-bank crashes, delayed/replayed/reordered notifications, wrong amount/currency/merchant, timeout-with-bank-success, two successful attempts, archive outage, cancellation race and refund ambiguity. Fake-bank evidence is labelled synthetic.

### Phase 9: Selected-bank sandbox integration and complete reconciliation

**Goal:** One selected eligible merchant adapter implements only documented hosted domains, callback verification, key rotation and normalized authorization/capture states with distinct sandbox/production controls.
**Depends on:** T08 plus supplied bank/merchant inputs
**Requirements:** BANK-01, BANK-02, BANK-03, BANK-04
**Source:** SLL-xSPI-MC-Shop-Codex-Handoff-2026-10-20.md T09; companion proposal.
**Estimate:** 4–7 engineer-days
**UI hint:** yes
**Plans:** Not created; detailed planning pending.

**Success Criteria:**

1. One selected eligible merchant adapter implements only documented hosted domains, callback verification, key rotation and normalized authorization/capture states with distinct sandbox/production controls.
2. Operators can reconcile complete transaction/statement windows including payments/refunds missing locally, preserving pagination/cutoff/completeness evidence and audited export fallback.
3. Each creation/refund/capture/void capability has dated primary evidence for recovery/idempotency/reference behavior; unqualified operations remain disabled.
4. Activation evidence records actual product/territory/currency/method eligibility, fees and acquirer PCI/ASV obligations and sanitized sandbox cases separately from synthetic tests.

**Required outputs:** One actual bank adapter, documented callback verification/status mapping, idempotency/reference recovery behavior, hosted-domain allowlist, distinct sandbox/production configuration, usable full-window transaction/statement reconciliation and supported finance operations.

**Normative acceptance:** Prove the actual bank protocol, including original-body verification when required, credential/key rotation, amount/currency/reference correlation and ambiguous-call recovery. Discover transactions absent from local attempt lists; a reference parameter is not proof of lookup/idempotency support. Confirm merchant product/territory/currency/method eligibility, fee quote and actual PCI/ASV expectations before activation. Disable unqualified operations. No real charge/refund without scoped authorization.

**Verification/evidence:** Primary bank documentation and dated capability matrix, sanitized sandbox outcomes, complete-window evidence/cutoffs and explicit gaps. Missing bank details block only this integration and its dependent real proof.

### Phase 10: Licence delivery, renewal/rehosting and support-hours workflows

**Goal:** Staff manually release one approved encrypted RTL/manual/reference design/key package per intended paid/accepted scope after checking entity, release/tool/coverage, host, term, production and holds.
**Depends on:** T05–T08; actual access/rights profiles for real fulfilment
**Requirements:** FUL-01, FUL-02, FUL-03, FUL-04, FUL-05, FUL-06
**Source:** SLL-xSPI-MC-Shop-Codex-Handoff-2026-10-20.md T10; companion proposal.
**Estimate:** 5–8 engineer-days
**UI hint:** yes
**Plans:** Not created; detailed planning pending.

**Success Criteria:**

1. Staff manually release one approved encrypted RTL/manual/reference design/key package per intended paid/accepted scope after checking entity, release/tool/coverage, host, term, production and holds.
2. Private artifacts/delivery manifests and invoice/credit-number reservations are archived before activation/issue; every artifact/document download checks resource entitlement and uses short-lived version-bound bearer access.
3. Renewal, rehosting and family/node/production upgrades create reviewed cases and applicable new revisions/orders without rewriting historical rights, promising physical recall or automatically charging.
4. Each paid/accepted support package credits exactly 36,000 seconds once after archival and never expires or renews IP rights; standalone top-ups require no new IP configuration.
5. Support reservations/authority are archived before work; concurrent task posting cannot overspend or duplicate debits, completion is archived before publication, and corrections reverse/replace history. Committed task statements show task/cumulative/remaining usage; mail retry never debits again and refunds of consumed credit require review without erasing work or negative usable balances.

**Required outputs:** Manual key/package release, artifact/version/entitlement checks, private download authorization, approved term/production/node records, rehosting/renewal/upgrade cases, invoice/credit numbering, support-only top-ups and non-expiring support purchase/consumption ledger with usage email statements.

**Normative acceptance:** One approved release/key per intended scope; all four declared deliverables and exact host/term/coverage are checked. Archive private artifacts/delivery and document reservations before issue. 10-hour support packages grant 36,000 seconds once; concurrent task posting cannot overspend or debit twice; task emails show task/cumulative/remaining usage. Corrections preserve history. Support remains after annual IP expiry and does not renew IP rights. Refunds distinguish available from consumed credit. Resource authorization protects both packages and balances. Rehosting/renewal cannot silently mutate old rights or automatically charge a card. Archive credit grants before spendability, approved task/reservation identities before chargeable work, and actual completion before final balance/statement publication; pending reservations cannot be spent twice.

**Verification/evidence:** Synthetic manual fulfilment and unauthorized-download checks; term-boundary and rehosting cases; support 0/1/multiple packages, standalone top-up, concurrent debits, reversal, refund-after-consumption, mail retry and annual-expiry independence; reserved-document uniqueness.

### Phase 11: OVH deployment, Route 53, dedicated TLS and static publication

**Goal:** Operators can qualify a new B2-7 GRA11 image/workload and current account quote, monthly conversion, IPv4/disks/volume/buckets/identities and B3-8 fallback within authorized scope.
**Depends on:** T02–T04; cloud/DNS authorization for deployed proof
**Requirements:** HOST-01, HOST-02, HOST-03, HOST-04, HOST-05
**Source:** SLL-xSPI-MC-Shop-Codex-Handoff-2026-10-20.md T11; companion proposal.
**Estimate:** 3–5 engineer-days
**UI hint:** no
**Plans:** Not created; detailed planning pending.

**Success Criteria:**

1. Operators can qualify a new B2-7 GRA11 image/workload and current account quote, monthly conversion, IPv4/disks/volume/buckets/identities and B3-8 fallback within authorized scope.
2. Prepared Route 53 changes target only approved xspi.pro records; customer shop.xspi.pro uses dedicated new TLS, staff name remains proposed, AAAA requires end-to-end proof and DNS-01 is conditional/scoped.
3. Caddy routes API/private/simple purchases before static matching, isolates staff, and fetches only manifest-listed GET/HEAD objects over verified fixed HTTPS Host/SNI with sensitive headers/query metadata stripped.
4. Immutable publication verifies hash/MIME/route/ACL completeness before one validated route switch; interrupted upload/failed load/rollback and cached two-release assets remain safe.
5. Actual authorized OVH tests distinguish public-object access/private listing and object denials, canonical 308, true 404, origin 502/503, HEAD/304/compression/cache behavior and certificate renewal.

**Required outputs:** Qualified new-VM image and service configuration; B2-7 GRA11 monthly quote/qualification plan with fallback; separate volumes/buckets/credentials; exact Route 53 xspi.pro records; dedicated shop/staff ACME certificates; HTTPS S3 object-origin Caddy routing; staged immutable releases and rollback.

**Normative acceptance:** Verify current quote/stock, legacy monthly versus hourly/Savings Plan billing, IPv4 and disk line items; convert to monthly only within authorized scope. Use shop.xspi.pro A to the new VM and proposed shop-admin.xspi.pro; AAAA only after working IPv6. Standard HTTP-01/TLS-ALPN-01 needs no Route 53 credentials; DNS-01 requires the explicitly scoped alternative. Existing synaptic-labs.com certificate or wildcard is not assumed to cover xspi.pro. Keep public bytes in OVH Object Storage, serve them through HTTPS object API with fixed Host/SNI/TLS verification, strip credentials/query data and enforce actual routes/status/cache/MIME. No live-root deletion or partial-release activation. Preserve the existing main website and DNS records outside scope.

**Verification/evidence:** Actual authorized resource IDs/region/tariff/service privileges, public TLS/CAA and customer/staff boundaries, IPv4/IPv6 observations, anonymous-private-object denials, representative load, interrupted publication/two-release asset survival/rollback, certificate renewal staging qualification. Local mocks are not OVH proof.

### Phase 12: Backups, operating alerts and financial/licensing restore rehearsal

**Goal:** Operators can restore PostgreSQL from encrypted off-region pgBackRest full/differential/WAL backups with independent artifact/secret custody and separately qualified retained evidence namespaces.
**Depends on:** T08,T10–T11; T09 for actual-bank proof
**Requirements:** OPS-01, OPS-02, OPS-03, OPS-04, OPS-05, OPS-06
**Source:** SLL-xSPI-MC-Shop-Codex-Handoff-2026-10-20.md T12; companion proposal.
**Estimate:** 3–5 engineer-days
**UI hint:** no
**Plans:** Not created; detailed planning pending.

**Success Criteria:**

1. Operators can restore PostgreSQL from encrypted off-region pgBackRest full/differential/WAL backups with independent artifact/secret custody and separately qualified retained evidence namespaces.
2. Recovery mode blocks mutating bank/SMTP/workers before data exposure; restored sessions/challenges are invalidated, post-point grants/revocations reconciled and consumed MFA codes recovered/reset before access.
3. Restored financial/order/acceptance/host/document/key records reconcile complete external windows and retained versions under original identities; missing acceptance or ambiguous preparation holds affected operations.
4. Support credits/reservations/completed work reconcile after restore without restoring spent hours, including a debit committed before completion-archive acknowledgement; missing completion is never invented.
5. Drills measure proposed 15-minute DB RPO and four-hour operator-start technical restore separately from detection/response/safe reopening, with no accidental bank/email effects. Operators receive activity-aware WAL, backup, resource, certificate, job/mail/payment/fulfilment/support alerts and named ownership/runbooks, with measured ten-customer/two-staff workload and bounded concurrency.

**Required outputs:** pgBackRest base/differential/WAL backup, isolated recovery mode, protected evidence storage, secret custody/recovery, monitoring and ownership runbooks, full restoration/reconciliation rehearsal with orders, host revisions, documents, key delivery and support ledger state.

**Normative acceptance:** Before exposing restored data, stop effect workers and block mutating bank/SMTP access. Restore database/artifacts/keys; permit read-only complete-window bank reconciliation; reconstruct missing order/acceptance/host records, document reservations, delivered keys and support debits. Prepared evidence does not prove completion. Preserve identities, hold missing contract evidence and avoid duplicate licences/support credits or reused invoice numbers. Measure proposed 15-minute DB RPO and four-hour technical target after operator start; record full safe-reopen delay separately. SBG Object Lock, private ACLs and custody must be actually qualified. Invalidate restored sessions and verification challenges, reconcile resource revocations and recover/reset used MFA recovery codes before privileged access; hold unresolved prepared support work until reconciled.

**Verification/evidence:** Dated isolated drill with externally completed operations beyond the restore point, measured data-loss/technical/safe-reopen timestamps, retained versions/key recovery, no unintended bank/email effects, alert routing and named operator coverage. Prove denial of revoked/restored access and recovery of a debit committed before completion-archive acknowledgement.

### Phase 13: Integrated product, access, payment and deployment acceptance

**Goal:** Release reviewers can trace every source field/option/rule to exercised customer/staff journeys, exact new IDs/hostnames and source/profile/approval revisions.
**Depends on:** T04,T06–T12, with conditional external evidence
**Requirements:** UAT-01, UAT-02, UAT-03, UAT-04
**Source:** SLL-xSPI-MC-Shop-Codex-Handoff-2026-10-20.md T13; companion proposal.
**Estimate:** 3–5 engineer-days
**UI hint:** yes
**Plans:** Not created; detailed planning pending.

**Success Criteria:**

1. Release reviewers can trace every source field/option/rule to exercised customer/staff journeys, exact new IDs/hostnames and source/profile/approval revisions.
2. Integrated cases cover multi-vendor direct/quote orders, higher-volume quote, support-only/mixed checkout, private host access, rehosting/renewal and support usage statements.
3. Risk-based regression checks cover payment uncertainty/duplicates, cross-resource/MFA denial, static/no-JS/offline accessibility, public/log leaks, restored support/document/grants and two-release rollback.
4. Evidence identifies reproducible release revisions, actual commands/environments and unexecuted bank/cloud gates, with no production claim inferred from a mock.

**Required outputs:** One integrated release-candidate check against the supplied definition and new domain: complete customer/admin journeys, exact source coverage, pricing/licensing/support behavior, accessibility, privacy, static HTTP/release behavior, performance and recovery evidence.

**Normative acceptance:** Use risk-based end-to-end cases instead of repeating every unit test. Fail on unapproved public placeholders, unintended product IDs/fields/routes, stale shop hostnames or mixed catalog/terms. Verify zero raw host IDs/keys/secrets in public outputs or ordinary logs. Exercise guest resource denial, multi-vendor quote/direct order, higher-volume quote, support-only top-up and usage statement, rehosting/renewal approval, bank uncertainty and restored support/document/grant history. Record any unexecuted real-bank/cloud gate without blocking unrelated local completion.

**Verification/evidence:** Traceability checklist, reproducible release identifiers, scoped commands/outcomes, sanitized screenshots where useful, unresolved risks and fixed-regression results. Stop optional repeated testing once the concrete risks and required gates are covered.

### Phase 14: Release handover and separately scoped live activation

**Goal:** Operators receive a concrete release/deploy/rollback package containing artifact/config/catalog/document identities, exact domains, bank capability/fee record and custody/operator/support/licensing runbooks.
**Depends on:** All applicable tasks plus affected commercial/operating decisions
**Requirements:** REL-01, REL-02, REL-03, REL-04
**Source:** SLL-xSPI-MC-Shop-Codex-Handoff-2026-10-20.md T14; companion proposal.
**Estimate:** 2–3 engineer-days
**UI hint:** no
**Plans:** Not created; detailed planning pending.

**Success Criteria:**

1. Operators receive a concrete release/deploy/rollback package containing artifact/config/catalog/document identities, exact domains, bank capability/fee record and custody/operator/support/licensing runbooks.
2. Live activation rejects missing prices/rights/host/seller/tax/legal/retention/bank/recovery/owner approvals, synthetic adapters and unqualified external proofs without blocking unaffected preparation.
3. Any authorized external change records observed DNS/TLS/mail/bank/production results and cost/cleanup scope; unexecuted activation remains pending and separately scoped.
4. The handover report separates completed work, conditional work, P-01–P-12 decisions, actual external changes and the precise next missing input.

**Required outputs:** Reviewable deployment plan, release/rollback artifacts, final approved catalog/documents, bank configuration and fee/obligation record, DNS/certificate/resource changes, operator and custody assignments, support/licensing runbooks and implementation evidence report. Execute only the external activation actually authorized.

**Normative acceptance:** No unknown live prices, rights, host mechanism, seller/tax terms or required operating owner is inferred. Confirm exact shop.xspi.pro URLs, bank return/callback domains, staff boundaries, source/profile/approval revisions and measured restore evidence. A real test transaction, notification and DNS/production switch need their actual scoped authority; do the necessary local preparation first. Report work completed, conditional work, remaining decisions and actual external actions without claiming an unexecuted system is live or tested.

**Verification/evidence:** Final status/evidence manifest, approved release and configuration identities, observed activation results if authorized, rollback instructions, resource billing/cleanup account and precise remaining phase-specific blockers.

## Progress

| Phase | Plans complete | Status |
|---|---|---|
| 1 | 2 / 2 | Executed — human verification pending (4 items) |
| 2 | 0 / not planned | Pending |
| 3 | 0 / not planned | Pending |
| 4 | 0 / not planned | Pending |
| 5 | 0 / not planned | Pending |
| 6 | 0 / not planned | Pending |
| 7 | 0 / not planned | Pending |
| 8 | 0 / not planned | Pending |
| 9 | 0 / not planned | Pending |
| 10 | 0 / not planned | Pending |
| 11 | 0 / not planned | Pending |
| 12 | 0 / not planned | Pending |
| 13 | 0 / not planned | Pending |
| 14 | 0 / not planned | Pending |
