# Roadmap: SLL xSPI-MC Shop

**Baseline:** 2026-10-21 protected-services proposal/handoff, read in full. T01 documentation reconciled; T02 has two completed development plans retained with narrow evidence scope. New runtime/host criteria are unexecuted.

## Scope and execution policy

Selected production backend: rootless Podman directly on existing mx1, declared by NixOS/Quadlet under new proposed shopsvc. Separate app, one worker, new PostgreSQL cluster and internal Caddy containers; independently owned backup jobs. Static output remains in gra; off-host recovery/evidence/artifacts in sbg. No new production compute, block volume, public IP, automatic paid fallback or permanent staging VM.

All pre-existing services/resources in every owner/runtime/state remain protected, including native units, VMs and stopped/failed containers. Before the first mx1 deployment write, obtain sanitized read-only inventory, exact shop mutation/identity/database allowlist and complete evaluated NixOS activation-impact review. No blanket activation, protected reload/restart/change, host-generation rollback, global prune/GC or guest infrastructure change. Only later explicit service/action authorization can permit that particular protected action. On adverse effect stop shop activity and revert only verified shop additions while retaining business records.

Public activation requires a complete already working unchanged ingress/TLS path, or later explicit authorization for the precise deferred protected action. DNS-01 cannot supply a missing traffic route. No A/AAAA before complete path proof. Existing SMTP/monitoring/backup configuration remains unchanged. Runtime fault/exhaustion/restart/restore and burst/capacity tests are off-host; mx1 checks are bounded shop functional work and read-only comparison.

This request executes documentation replanning only. Earlier applicable local implementation permission remains recorded for a future execution instruction; no host/cloud/DNS/TLS/mail/bank activation is inferred. Preserve actual dependencies: T09 input gaps need not block independent T10/T11 preparation. T04 UI/fallback, T05 persistence and T06 access join at T07; do not expose private editing early. A missing off-host runner defers its runtime lane with nonzero blocked evidence, not a synthetic pass or automatic purchase.

**Estimate:** supplied 46–74 engineer-days excluding external waiting/ongoing operations. About £0.79/month ex VAT models incremental 130 GiB object storage only; existing server/capacity, bandwidth, DNS, merchant fees, retention growth and independent drills are excluded and unverified. Full retention is never reduced to fit that model.

## Phases

- [x] **Phase 1: Product authority, repository review and decision register** — October 21 handoff T01
- [ ] **Phase 2: Reproducible application and deployment skeleton** — October 21 handoff T02
- [ ] **Phase 3: Markdown catalog, schemas and approved price calculations** — October 21 handoff T03
- [ ] **Phase 4: Static product, configurator, support page and accessible fallback** — October 21 handoff T04
- [ ] **Phase 5: Transactional records, durable work and private evidence primitives** — October 21 handoff T05
- [ ] **Phase 6: Verified customer access, staff MFA and private host editing** — October 21 handoff T06
- [ ] **Phase 7: Multi-line cart, quotations, business checkout and acceptance** — October 21 handoff T07
- [ ] **Phase 8: Payment domain and fault-injectable fake bank** — October 21 handoff T08
- [ ] **Phase 9: Selected-bank sandbox integration and complete reconciliation** — October 21 handoff T09
- [ ] **Phase 10: Licence delivery, renewal/rehosting and support-hours workflows** — October 21 handoff T10
- [ ] **Phase 11: Protected-host qualification, shop-only deployment and conditional public activation** — October 21 handoff T11
- [ ] **Phase 12: Backups, operating alerts and financial/licensing restore rehearsal** — October 21 handoff T12
- [ ] **Phase 13: Integrated product, access, payment and deployment acceptance** — October 21 handoff T13
- [ ] **Phase 14: Release handover and separately scoped live activation** — October 21 handoff T14

## Phase Details

### Phase 1: Product authority, repository review and decision register

**Goal:** Operators can verify the exact embedded product snapshot by filename, 23,969-byte length and SHA-256, using only the October 21 package as new product authority.
**Depends on:** An implementation instruction
**Requirements:** SRC-01, SRC-02, SRC-03, SRC-04
**Source:** SLL-xSPI-MC-Shop-Codex-Handoff-2026-10-21.md T01; complete companion proposal remains normative.
**Estimate:** 1–2 engineer-days
**UI hint:** no
**Plans:** 2/2 documentation records reconciled; original human reviews remain historical, not approval of new hosting.

**Success Criteria:**

1. Operators can verify the exact embedded product snapshot by filename, 23,969-byte length and SHA-256, using only the October 21 package as new product authority. (SRC-01)
2. Reviewers can trace all three ordered vendors, thirteen families, thirteen logical controls, nineteen checkout groups, two helpers, four IP declarations and separate marketing control to source locations. (SRC-02)
3. Operators can inspect one P-01–P-12 register with status, owner, evidence and the exact affected live operation; pending decisions do not block unrelated planning. (SRC-03)
4. Reviewers can identify repository scope, new product/profile IDs, superseded assumptions and customer hostname without treating old task completion as new acceptance. (SRC-04)

**Required outputs:** Record the supplied product definition and embedded source hash; inventory the three vendors, 13 families, terms, bands, access controls, 19 business-checkout groups, four required declarations and separate marketing choice. Establish sll-xspi-mc, sll-xspi-mc-support-10h and sll-xspi-mc-v1. Inspect any existing repository/worktree, instructions and implementation before changes; document the new scope and one decision register with approval status and affected phase.

**Normative acceptance:** Use this revision's product authority exclusively. Earlier task completion does not establish compliance with this task list. Retire superseded implementation assumptions in the authorized checkout, without deleting unrelated work or historical business records. All source placeholders/provisional assumptions remain explicitly pending; recording mapping/approval status does not block local implementation. The authoritative customer hostname is shop.xspi.pro.

**Verification/evidence:** Source filename/hash and new requirement matrix; repository status and isolated working branch; recorded decisions P-01–P-12; exact product/profile IDs; scope/delta note.

### Phase 2: Reproducible application and deployment skeleton

**Goal:** Developers can reproduce static frontend, Django/worker and real-PostgreSQL development builds from compatible pinned dependencies, hashes and CI commands.
**Depends on:** T01
**Requirements:** BUILD-01, BUILD-02, BUILD-03, BUILD-04, BUILD-05, BUILD-06, BUILD-07, BUILD-08
**Source:** SLL-xSPI-MC-Shop-Codex-Handoff-2026-10-21.md T02; complete companion proposal remains normative.
**Estimate:** 3–5 engineer-days
**UI hint:** no
**Plans:** 5/18 complete (retained development evidence); 13 pending; 24 tasks/14 waves. 02-00/03/05 complete; next 02-04/06.

- [x] 02-01-PLAN.md — Concrete dependency review (Wave 1).
- [x] 02-02-PLAN.md — Pinned native development environment (Wave 2).
- [x] 02-00-PLAN.md — Current-source verification migration (Wave 3).
- [x] 02-03-PLAN.md — Static Astro collection and React island (Wave 4).
- [x] 02-05-PLAN.md — Frozen Python runtime and tools (Wave 4).
- [ ] 02-04-PLAN.md — Public frontend build boundary (Wave 5).
- [ ] 02-06-PLAN.md — Django real-PostgreSQL health path (Wave 5).
- [ ] 02-07-PLAN.md — Fail-closed Django environment configuration (Wave 6).
- [ ] 02-12-PLAN.md — Versioned actual-response API and probe contracts (Wave 6).
- [ ] 02-08-PLAN.md — Safe logs and developer environment examples (Wave 7).
- [ ] 02-09-PLAN.md — Migrated synthetic enqueue path (Wave 8).
- [ ] 02-13-PLAN.md — Environment/artifact schemas and cross-boundary proof (Wave 8).
- [ ] 02-10-PLAN.md — Leased worker and PostgreSQL ownership proof (Wave 9).
- [ ] 02-11-PLAN.md — Mail and storage fake-boundary expansion (Wave 10).
- [ ] 02-14-PLAN.md — Rootless shop containers, independent database and bounded off-host lifecycle (Wave 11).
- [ ] 02-15-PLAN.md — Protected-host inventory, selected profile and complete activation-impact preparation (Wave 12).
- [ ] 02-16-PLAN.md — Actual component licences and SBOM (Wave 13).
- [ ] 02-17-PLAN.md — Two clean builds and complete CI evidence (Wave 14).

**Success Criteria:**

1. Developers can reproduce static frontend, Django/worker and real-PostgreSQL development builds from compatible pinned dependencies, hashes and CI commands. Prepared host-controlled aggregate shop limits cover payload scopes, conmon, network helpers and backups: proposed CPUQuota=200%, MemoryHigh=6G, MemoryMax=8G, bounded TasksMax/concurrency; protected parent policies, cpusets and guest allocations remain unchanged. (BUILD-01, BUILD-06)
2. Reviewers can inspect component/transitive licences and SBOM for the actual locked artifacts; exact patches are verified when lockfiles are created. Prepared local ZFS shop storage enforces an 80 GiB aggregate cap including descendants/snapshots and a 50 GiB PostgreSQL allowance including indexes/WAL; GraphRoot/images/volumes/temp/certificates/logs/spool are accounted and shared journal/reserves/disks remain unchanged. (BUILD-02, BUILD-07)
3. Developers can run isolated synthetic bank/mail/storage fixtures and versioned OpenAPI/schema contracts without production credentials or external provisioning. Operators can review the complete evaluated NixOS closure, activation scripts, unit/user/mount/dependency and restart/reload impact before any host write; artifacts separate verified shop-only additions from deferred protected changes, without blanket activation. (BUILD-03, BUILD-08)
4. Operators can review pinned NixOS-declared rootless Podman Quadlet/user-systemd artifacts for separate Django, one worker, new shop PostgreSQL and internal Caddy containers directly on mx1 under the dedicated proposed shopsvc account, with one lifecycle per container. (BUILD-04)
5. Operators can review a shop identity/mutation map for UID/GID/subordinate mappings, rootless stores, units, networks, unused loopback ports, credentials and separate database cluster/PGDATA/roles/socket/backup identities; database mutations require positive destination checks. (BUILD-05)

**Required outputs:** Static Astro/React project, Django/application/worker skeleton, separately owned PostgreSQL development service, dependency lockfiles/licence inventory, CI, synthetic mail/bank/storage, OpenAPI and schemas. Prepare pinned artifacts and NixOS/rootless Quadlet templates for new shop account, services, storage, resources and secrets. Prepare the mandatory read-only inventory procedure, complete protected-resource register, shop-owned mutation allowlist, database/isolation identity map and full NixOS activation-impact plan before proposing any host write.

**Normative acceptance:** Clean builds reproduce pinned artifacts; no runtime Astro/Node server or mandatory Redis/Celery/CMS/IdP. A NixOS OCI backend named `podman` does not prove rootlessness. Give each new container one lifecycle and define limits/paths solely inside the shop ownership boundary. Provide a new shop PostgreSQL container/cluster/PGDATA, roles, credentials, private connection identity and backup namespace; no migration or maintenance command may target an existing PostgreSQL service. Templates must not mount protected data/management sockets, use privileged/host-network/host-PID modes, change shared slices/delegation/allocations or require a host/guest upgrade. Existing MicroVM project work may continue under its unchanged configuration, services, disks and allocation; runtime fault/exhaustion/restart tests run off-host. Inventory ownership ambiguity blocks only the affected mutation. No new compute/IP/block purchase, automatic fallback or secrets in Git/Nix-store/static output.

**Verification/evidence:** Build commands/results, artifact/lockfile identities, dependency compatibility and SBOM, prepared rootless cgroup/storage/database identity maps, inventory/allowlist templates and complete NixOS dependency/restart/reload impact plan. Separate executable shop-only additions from blocked protected-service proposals. Qualify fault/lifecycle behavior off-host; mark actual host enforcement unproven until T11's non-disruptive observations.

### Phase 3: Markdown catalog, schemas and approved price calculations

**Goal:** Editors can compile one reviewed Markdown/YAML catalog into immutable public/private manifests with the same revision; incomplete approvals cannot be activated through editable content.
**Depends on:** T01–T02
**Requirements:** CAT-01, CAT-02, CAT-03, CAT-04, CAT-05
**Source:** SLL-xSPI-MC-Shop-Codex-Handoff-2026-10-21.md T03; complete companion proposal remains normative.
**Estimate:** 4–6 engineer-days
**UI hint:** no
**Plans:** Detailed executable plans created at phase planning; no completion credit from earlier task numbers.

**Success Criteria:**

1. Editors can compile one reviewed Markdown/YAML catalog into immutable public/private manifests with the same revision; incomplete approvals cannot be activated through editable content. (CAT-01)
2. Both browser and backend validate exact vendor/family/term/band relationships through strict schemas, cross-file checks and bounded predicates/named validators with shared conformance cases. (CAT-02)
3. Customers receive draft, invalid, requires_quote, awaiting_review or purchasable results with structured reasons; unknown necessary coverage/rights/access/prices remain unpurchasable. (CAT-03)
4. Price calculations use bounded exact minor-unit integers, approved per-licence allowances and distinct family coverage, with annual/one-time/tax components and recurrence; provisional five-plus-five/€50 values never become live rates. (CAT-04)
5. Public output excludes private approvals, host instances, implementation comments and unresolved production placeholders; labelled synthetic examples remain distinguishable. (CAT-05)

**Required outputs:** One versioned Markdown/YAML catalog; full strict schemas and cross-file integrity checks; public/private immutable manifests; exact new option taxonomy; bounded declarative predicates/named validators; approved access/coverage/rate/terms profiles; consistent browser/backend conformance fixtures. Complete the proposal examples into production schemas rather than treating the examples as complete validators.

**Normative acceptance:** Validate vendor-family/term/band relationships, unique coverage, enabled-mode counts, disabled-mode reset, host-row cardinality and non-Altera profile gating. Distinguish source draft, approval and production eligibility. No arbitrary executable content. Reject missing rates instead of using zero; apply allowances per configured licence, never per family, and only if approved. Separate annual and one-time components, support quantity and tax category. Public output excludes private approvals/host IDs/internal comments and unresolved placeholders. Unapproved examples may run only in labelled local/synthetic mode.

**Verification/evidence:** Parsed catalog and schema checks, exact vendor/family list comparison, valid/invalid/quote/review cases in both runtimes, provisional node-price boundary cases and annual-versus-one-time calculation evidence.

### Phase 4: Static product, configurator, support page and accessible fallback

**Goal:** Customers can read static product/support/legal pages and select only the exact ordered vendor/family/term/band options, including Altera-only RDP and higher-volume quotation.
**Depends on:** T03
**Requirements:** SHOP-01, SHOP-02, SHOP-03, SHOP-04, SHOP-05
**Source:** SLL-xSPI-MC-Shop-Codex-Handoff-2026-10-21.md T04; complete companion proposal remains normative.
**Estimate:** 4–6 engineer-days
**UI hint:** yes
**Plans:** Detailed executable plans created at phase planning; no completion credit from earlier task numbers.

**Success Criteria:**

1. Customers can read static product/support/legal pages and select only the exact ordered vendor/family/term/band options, including Altera-only RDP and higher-volume quotation. (SHOP-01)
2. Customers can change vendor, term, access modes and counts with the specified notice/reset behavior while unrelated details/support persist; fixed-row reductions allow choice/cancel and cleared host data never revives. (SHOP-02)
3. Customers see accessible labelled controls, keyboard/mobile behavior, error focus and state-appropriate actions with separate annual/one-time prices and optional unticked marketing. (SHOP-03)
4. Customers can use Django /purchase/simple/ without JavaScript under the same domain rules; backend failure gives truthful status and does not claim persistence or payment. (SHOP-04)
5. Customers see masked host summaries and no raw host IDs, private links, business/tax records or keys in public bundles, URLs or default browser storage. (SHOP-05)

**Required outputs:** Static product/support/document pages, React configuration and price summary, separate licence/support cart presentation, quote request entry, country-aware checkout presentation, accessible errors and no-JavaScript Django purchase/simple flow using shared rules. Protected host editing integrates with T06.

**Normative acceptance:** Match all approved source options and declared requiredness; vendor/term/access changes clear only affected configuration and host data with notice. Show RDP only for Altera, exact nonoverlapping volume bands, higher-volume quotation, and permitted fixed/floating controls. Preserve unrelated business details and recoverable selections. Mask host IDs in summaries. Show annual and one-time costs separately, the correct action for eligibility state and useful offline behavior. Marketing is optional and unticked; implementation notes never become customer copy.

**Verification/evidence:** Representative mobile/keyboard/screen-reader checks, all conditional/reset branches, state-specific screenshots or sanitized captures, no-JavaScript path, public bundle inspection and customer-facing copy review.

### Phase 5: Transactional records, durable work and private evidence primitives

**Goal:** Business records for contacts, configuration/host revisions, quotes/orders, acceptance, money, licensing, support and evidence are persisted with reconstructable immutable snapshots.
**Depends on:** T02–T03
**Requirements:** DATA-01, DATA-02, DATA-03, DATA-04
**Source:** SLL-xSPI-MC-Shop-Codex-Handoff-2026-10-21.md T05; complete companion proposal remains normative.
**Estimate:** 3–5 engineer-days
**UI hint:** no
**Plans:** Detailed executable plans created at phase planning; no completion credit from earlier task numbers.

**Success Criteria:**

1. Business records for contacts, configuration/host revisions, quotes/orders, acceptance, money, licensing, support and evidence are persisted with reconstructable immutable snapshots. (DATA-01)
2. Committed domain work and notification outbox entries survive crashes through short leases and bounded retries; uniqueness and idempotency protect all intended effect identities. (DATA-02)
3. Workers release database transactions before network calls and recover abandoned work without duplicate domain effects, demonstrated with real PostgreSQL. (DATA-03)
4. Archive primitives verify recoverable object version/hash/retention and distinguish prepared from completed evidence; error/log paths redact sensitive values. (DATA-04)

**Required outputs:** Migrations/domain services for organizations, contacts, configured lines/host-binding revisions, quotes/orders, acceptance, financial records, licensing, support and evidence references; durable outbox/inbox, idempotency records, bounded leases/retry rules and synthetic notifications.

**Normative acceptance:** Persist business records before scheduling notification. Concurrency/uniqueness constraints protect line, quote, order, payment, document, licence and support identities. Worker crashes do not lose committed work; lease recovery cannot duplicate a domain effect. No long transaction spans network calls. Source configuration and acceptance snapshots are immutable and reconstructable. Host identifiers and credentials are redacted in error/log paths.

**Verification/evidence:** Migration/reversal plan, focused transactional and lease-crash checks, schema/constraint evidence, redaction verification and clear prepared-versus-completed evidence semantics.

### Phase 6: Verified customer access, staff MFA and private host editing

**Goal:** Customers exchange deliberate single-use email verification for rotated resource-scoped host-only secure sessions; GET scanners/replay do not consume credentials or accept contracts.
**Depends on:** T04–T05
**Requirements:** AUTH-01, AUTH-02, AUTH-03, AUTH-04, AUTH-05, AUTH-06
**Source:** SLL-xSPI-MC-Shop-Codex-Handoff-2026-10-21.md T06; complete companion proposal remains normative.
**Estimate:** 3–5 engineer-days
**UI hint:** yes
**Plans:** Detailed executable plans created at phase planning; no completion credit from earlier task numbers.

**Success Criteria:**

1. Customers exchange deliberate single-use email verification for rotated resource-scoped host-only secure sessions; GET scanners/replay do not consume credentials or accept contracts. Customers can independently withdraw marketing preference without affecting service messages or paid rights. (AUTH-01, AUTH-06)
2. Purchasing, invoice and technical contacts receive explicit verified memberships; cross-customer/domain equality grants no unrelated resource access. (AUTH-02)
3. Every staff/admin/custom privileged route requires MFA and role/resource permission, with recent verification for sensitive actions and safe recovery; customer hostname returns 404 for staff aliases. (AUTH-03)
4. Authorized customers edit encrypted key-versioned host bindings under revision control, using actual manager-specific normalization and duplicate rules; fixed rows match nodes and floating seats use the approved server model. (AUTH-04)
5. Private raw-host access, CSRF/origin controls, key recovery and revocation are audited; unknown manager profiles hold qualification without inventing a universal MAC format. (AUTH-05)

**Required outputs:** Resource-scoped verified-email sessions, staff MFA/recovery and role enforcement, separate customer/staff host boundaries, protected configuration/host editor, raw-host encryption/key-version handling, explicit purchaser/invoice/technical contact membership and marketing withdrawal.

**Normative acceptance:** Use shop.xspi.pro and proposed shop-admin.xspi.pro with separate host-only cookies and no wildcard CORS. Customer host rejects all staff aliases. Email-domain equality grants no organization access; scanners cannot consume access credentials by GET alone. All privileged custom routes require MFA. Validate host IDs using an approved actual-manager profile rather than a universal MAC regex. Fixed rows match selected nodes; floating seats use the approved server model. Unknown formats block key qualification, not generic UI development. Mask ordinary responses, avoid host values in browser storage/URLs/logs, and qualify reauthentication for sensitive changes.

**Verification/evidence:** Cross-customer/contact/role denial cases, scanner/replay/session/CSRF checks, raw-host data-flow inspection, canonicalization/duplicate cases for the actual supplied profile, private encryption/recovery key-version checks using synthetic values.

### Phase 7: Multi-line cart, quotations, business checkout and acceptance

**Goal:** Customers retain separate configured IP lines at quantity one across vendors and explicit duplicate scopes; support has positive real package quantity and zero selector value omits its line.
**Depends on:** T03,T05–T06
**Requirements:** COM-01, COM-02, COM-03, COM-04, COM-05, COM-06
**Source:** SLL-xSPI-MC-Shop-Codex-Handoff-2026-10-21.md T07; complete companion proposal remains normative.
**Estimate:** 4–6 engineer-days
**UI hint:** yes
**Plans:** Detailed executable plans created at phase planning; no completion credit from earlier task numbers.

**Success Criteria:**

1. Customers retain separate configured IP lines at quantity one across vendors and explicit duplicate scopes; support has positive real package quantity and zero selector value omits its line. One guarded review/acceptance service rejects tampered totals and stale catalog/host/terms/entity revisions, records signatory/authority/hashes/time and separates quote validity, order payment-start deadline and bank-session expiry. (COM-01, COM-06)
2. Customers review exactly the selected line IDs/revisions; any review/quote-only line blocks combined payment until explicit cart editing or a combined quote, with no silent dropping/splitting/merging. (COM-02)
3. Quotes freeze immutable scope, host, component price, tax, document and validity versions; one accepted revision produces one acceptance/order across browser sessions and idempotency keys. (COM-03)
4. Business checkout preserves nineteen source groups with country-aware applicability and approved tax/status options; same-as helpers resolve final values and purchaser/licensee differences enter review. (COM-04)
5. IP orders capture all four exact versioned declarations, support-only orders capture applicable general/support/refund terms and owner/quantity without IP fields, and mixed orders accept both document sets. (COM-05)

**Required outputs:** Multi-vendor carts with one licence scope per line, real support package quantities/support-only carts, immutable quotes, backend totals and tax decision adapter, country-aware business fields, exact document/declaration acceptance, one order conversion and separate quote/payment deadlines.

**Normative acceptance:** Never merge/double configured licence entitlements through generic quantity. A basket with an unapproved line cannot silently drop it or charge a partial basket. Verify the same reviewed scope and host-binding revision at acceptance/payment. Reject price tampering and stale changes; no silent repricing. One quote revision produces one acceptance/order across sessions and keys. The acknowledgements required by the applicable checkout profile remain separate from optional marketing; IP-containing orders preserve the four source declarations. Invoice/technical contacts and differing licensed entities follow approved review rules. Approved live tax/legal values can remain pending while synthetic flows work. Support-only checkout uses applicable support terms and owner/quantity confirmation with no IP configuration or new IP entitlement; mixed orders accept both applicable document sets.

**Verification/evidence:** Full direct and quoted multi-line journeys, two-browser acceptance race, stale catalog/host/price/terms cases, synthetic tax/rounding and annual/one-time component tests, support-only purchase review. Include a support-only top-up with no vendor/family/host data and mixed-cart term applicability.

### Phase 8: Payment domain and fault-injectable fake bank

**Goal:** Payment preparation commits order/acceptance/attempt/reference identities, archives recoverable snapshots, then rechecks cancellation/deadline/holds/activation before one dispatch claim.
**Depends on:** T05,T07
**Requirements:** PAY-01, PAY-02, PAY-03, PAY-04, PAY-05
**Source:** SLL-xSPI-MC-Shop-Codex-Handoff-2026-10-21.md T08; complete companion proposal remains normative.
**Estimate:** 4–6 engineer-days
**UI hint:** yes
**Plans:** Detailed executable plans created at phase planning; no completion credit from earlier task numbers.

**Success Criteria:**

1. Payment preparation commits order/acceptance/attempt/reference identities, archives recoverable snapshots, then rechecks cancellation/deadline/holds/activation before one dispatch claim. (PAY-01)
2. A potentially dispatched timeout is uncertain and cannot trigger a blind second charge; preparing means no known dispatch and browser navigation cannot confirm money. (PAY-02)
3. Only authenticated matched merchant/currency/amount/reference observations can confirm financial facts; durable bounded callbacks distinguish notification hints from payment evidence. (PAY-03)
4. Retries, different keys, reordered callbacks and two successful captures preserve both money events, one intended fulfilment and a finance overpayment case. (PAY-04)
5. Capture/refund intents are archived before supported effects and preserve requested/uncertain/confirmed history; fake-bank fault injection covers crashes, archive failure, cancellation and ambiguous success. (PAY-05)

**Required outputs:** Typed bank-adapter boundary/capability record, hosted-payment preparation, protected archive-before-dispatch ordering, normalized financial observations, durable callback inbox, reconciliation and finance exception workflows, fake-bank scenarios for uncertain/missing/duplicate outcomes.

**Normative acceptance:** Commit order/attempt/reference then archive recoverable snapshots before bank calls. Recheck cancellation/deadline/approval/live state after archive waits before claiming dispatch. Treat network ambiguity as uncertain; browser return is never payment proof. Enforce exact order/merchant/currency/amount matches and supported authorization/capture distinctions. Different idempotency keys cannot cause concurrent blind charges. Duplicate captured attempts create one intended entitlement and an overpayment case. Preserve original financial history and archive refund/capture intents too.

**Verification/evidence:** Injected pre/post-bank crashes, delayed/replayed/reordered notifications, wrong amount/currency/merchant, timeout-with-bank-success, two successful attempts, archive outage, cancellation race and refund ambiguity. Fake-bank evidence is labelled synthetic.

### Phase 9: Selected-bank sandbox integration and complete reconciliation

**Goal:** One selected eligible merchant adapter implements only documented hosted domains, callback verification, key rotation and normalized authorization/capture states with distinct sandbox/production controls.
**Depends on:** T08 plus supplied bank/merchant inputs
**Requirements:** BANK-01, BANK-02, BANK-03, BANK-04
**Source:** SLL-xSPI-MC-Shop-Codex-Handoff-2026-10-21.md T09; complete companion proposal remains normative.
**Estimate:** 4–7 engineer-days
**UI hint:** yes
**Plans:** Detailed executable plans created at phase planning; no completion credit from earlier task numbers.

**Success Criteria:**

1. One selected eligible merchant adapter implements only documented hosted domains, callback verification, key rotation and normalized authorization/capture states with distinct sandbox/production controls. (BANK-01)
2. Operators can reconcile complete transaction/statement windows including payments/refunds missing locally, preserving pagination/cutoff/completeness evidence and audited export fallback. (BANK-02)
3. Each creation/refund/capture/void capability has dated primary evidence for recovery/idempotency/reference behavior; unqualified operations remain disabled. (BANK-03)
4. Activation evidence records actual product/territory/currency/method eligibility, fees and acquirer PCI/ASV obligations and sanitized sandbox cases separately from synthetic tests. (BANK-04)

**Required outputs:** One actual bank adapter, documented callback verification/status mapping, idempotency/reference recovery behavior, hosted-domain allowlist, distinct sandbox/production configuration, usable full-window transaction/statement reconciliation and supported finance operations.

**Normative acceptance:** Prove the actual bank protocol, including original-body verification when required, credential/key rotation, amount/currency/reference correlation and ambiguous-call recovery. Discover transactions absent from local attempt lists; a reference parameter is not proof of lookup/idempotency support. Confirm merchant product/territory/currency/method eligibility, fee quote and actual PCI/ASV expectations before activation. Disable unqualified operations. No real charge/refund without scoped authorization.

**Verification/evidence:** Primary bank documentation and dated capability matrix, sanitized sandbox outcomes, complete-window evidence/cutoffs and explicit gaps. Missing bank details block only this integration and its dependent real proof.

### Phase 10: Licence delivery, renewal/rehosting and support-hours workflows

**Goal:** Staff manually release one approved encrypted RTL/manual/reference design/key package per intended paid/accepted scope after checking entity, release/tool/coverage, host, term, production and holds.
**Depends on:** T05–T08; actual access/rights profiles for real fulfilment
**Requirements:** FUL-01, FUL-02, FUL-03, FUL-04, FUL-05, FUL-06
**Source:** SLL-xSPI-MC-Shop-Codex-Handoff-2026-10-21.md T10; complete companion proposal remains normative.
**Estimate:** 5–8 engineer-days
**UI hint:** yes
**Plans:** Detailed executable plans created at phase planning; no completion credit from earlier task numbers.

**Success Criteria:**

1. Staff manually release one approved encrypted RTL/manual/reference design/key package per intended paid/accepted scope after checking entity, release/tool/coverage, host, term, production and holds. Committed task statements show task/cumulative/remaining usage; mail retry never debits again and refunds of consumed credit require review without erasing work or negative usable balances. (FUL-01, FUL-06)
2. Private artifacts/delivery manifests and invoice/credit-number reservations are archived before activation/issue; every artifact/document download checks resource entitlement and uses short-lived version-bound bearer access. (FUL-02)
3. Renewal, rehosting and family/node/production upgrades create reviewed cases and applicable new revisions/orders without rewriting historical rights, promising physical recall or automatically charging. (FUL-03)
4. Each paid/accepted support package credits exactly 36,000 seconds once after archival and never expires or renews IP rights; standalone top-ups require no new IP configuration. (FUL-04)
5. Support reservations/authority are archived before work; concurrent task posting cannot overspend or duplicate debits, completion is archived before publication, and corrections reverse/replace history. (FUL-05)

**Required outputs:** Manual key/package release, artifact/version/entitlement checks, private download authorization, approved term/production/node records, rehosting/renewal/upgrade cases, invoice/credit numbering, support-only top-ups and non-expiring support purchase/consumption ledger with usage email statements.

**Normative acceptance:** One approved release/key per intended scope; all four declared deliverables and exact host/term/coverage are checked. Archive private artifacts/delivery and document reservations before issue. 10-hour support packages grant 36,000 seconds once; concurrent task posting cannot overspend or debit twice; task emails show task/cumulative/remaining usage. Corrections preserve history. Support remains after annual IP expiry and does not renew IP rights. Refunds distinguish available from consumed credit. Resource authorization protects both packages and balances. Rehosting/renewal cannot silently mutate old rights or automatically charge a card. Archive credit grants before spendability, approved task/reservation identities before chargeable work, and actual completion before final balance/statement publication; pending reservations cannot be spent twice.

**Verification/evidence:** Synthetic manual fulfilment and unauthorized-download checks; term-boundary and rehosting cases; support 0/1/multiple packages, standalone top-up, concurrent debits, reversal, refund-after-consumption, mail retry and annual-expiry independence; reserved-document uniqueness.

### Phase 11: Protected-host qualification, shop-only deployment and conditional public activation

**Goal:** Before the first mx1 deployment write, operators record a sanitized read-only inventory of host/configuration identity and every pre-existing rootful/rootless/native/VM resource in all lifecycle states; unknown ownership remains protected.
**Depends on:** T02–T04; applicable shop-owned host/Object Storage/DNS authority, plus later explicit service/action authority for any otherwise blocked protected change
**Requirements:** HOST-01, HOST-02, HOST-03, HOST-04, HOST-05, HOST-06, HOST-07, HOST-08, HOST-09
**Source:** SLL-xSPI-MC-Shop-Codex-Handoff-2026-10-21.md T11; complete companion proposal remains normative.
**Estimate:** 3–5 engineer-days
**UI hint:** no
**Plans:** Detailed executable plans created at phase planning; no completion credit from earlier task numbers.

**Success Criteria:**

1. Before the first mx1 deployment write, operators record a sanitized read-only inventory of host/configuration identity and every pre-existing rootful/rootless/native/VM resource in all lifecycle states; unknown ownership remains protected. Operators prove every proposed mx1 mutation is within the current shop allowlist and actual authority; all pre-existing services, stopped/failed resources, shared proxies/TLS/firewall/monitoring/SMTP/backups and MicroVM infrastructure remain unchanged. (HOST-01, HOST-06)
2. Public ingress/TLS uses a complete already working unchanged route/certificate contract or stays deferred with an exact protected-service/action proposal; DNS A/AAAA activation requires end-to-end authorized path proof, Route 53 authority and staff-host approval. Operators observe effective shop ancestor/controller/path/quota enforcement and separate database destination read-only on mx1; missing support or capacity defers the step or qualifies smaller shop limits off-host without protected reallocations. (HOST-02, HOST-07)
3. Caddy routes API/private/simple purchases before static matching, isolates staff, and fetches only manifest-listed GET/HEAD objects over verified fixed HTTPS Host/SNI with sensitive headers/query metadata stripped. Before/after configuration fingerprints, identities, listeners, lifecycle/restart evidence and bounded health observations detect adverse impact; stop shop activity and safely revert only proved shop additions, preserving business records and never repairing protected services. (HOST-03, HOST-08)
4. Immutable publication verifies hash/MIME/route/ACL completeness before one validated route switch; interrupted upload/failed load/rollback and cached two-release assets remain safe. Storage project/bucket/credential/tariff/bandwidth scopes are qualified without modifying partner project 001-xspi-pro; no production compute/block/IP purchase, billing conversion, automatic paid fallback, disk restructuring or permanent staging VM is selected. (HOST-04, HOST-09)
5. Authorized Object Storage checks prove public approved objects/private listing/private-object denial and HTTP semantics; mx1 checks are bounded/read-only comparisons, with new-shop certificate evidence only on a qualified unchanged path. (HOST-05)

**Required outputs:** Mandatory read-only `mx1` inventory before its first deployment write; protected-resource register for all owners/states/service types; exact new shop resource/isolation map and mutation allowlist; complete NixOS activation impact; dedicated rootless shop artifacts and separate PostgreSQL cluster/persistent layout; `gra`/`sbg` shop storage; internal Caddy/static releases; and either evidence of a complete unchanged ingress/TLS path or a precise deferred service/action proposal. Prepare DNS records and shop-only rollback without implying permission to change protected resources.

**Normative acceptance:** Establish host/configuration identity, every rootful/rootless/native/VM resource and ownership state, effective CPU/delegation boundaries, persistent paths/pool accounting, listeners and existing proxy/TLS behavior read-only. Protect stopped/failed resources as well as running ones. Record the allowed new account, names, paths, images, cgroups, datasets, network/ports, credentials/certificates and exact mutations. Verify the new shop database's cluster/container/PGDATA/role/connection identity before migrations, restore or maintenance. Do not reuse or mutate an existing PostgreSQL cluster. Add only shop-owned resources whose complete effects fit the allowlist and actual authority; use proposed limits without changing protected allocations or shared cgroups. Confirm enforcement through read-only observations and bounded shop checks, using off-host lifecycle/containment test evidence. No blanket NixOS activation or host/guest upgrade, reload, restart, stop, prune, GC, reboot or disk alteration. Existing backup/monitoring/SMTP configuration remains unchanged; consume only already provisioned interfaces/credentials.

An already complete unchanged route/certificate contract is preferred. The pass-through/termination profiles are proposals only until that condition is proved or a later authorization names the protected service and exact action. Do not add/reload a proxy route, change PROXY-protocol settings, install a certificate into an existing terminator or modify an ACME unit under generic deployment approval. Zero-downtime reloads remain forbidden. If a protected change is necessary, defer that step and its public activation, present the precise alternative and continue unaffected implementation. DNS-01 does not supply a missing traffic path. Reject forged forwarded headers and private-port redirects within new shop components. Publish A/AAAA records only after the complete authorized path is proved; no placeholder A record while ingress is blocked. Existing main-domain certificates are not assumed to cover `xspi.pro`.

Keep public bytes in shop-owned OVH Object Storage through a fixed verified HTTPS object API, stripping credentials/client headers/query data. Enforce manifest routes/status/cache/MIME and two-release retention. No live-root deletion or partial-release activation. Routine releases may activate only the new shop gateway; no protected proxy reload is an exception. Preserve partner project `001-xspi-pro`, reserve datasets and all other protected resources. Record that the eventual custom-domain storefront depends on this host/pool/ingress.

**Verification/evidence:** Label operator-supplied versus freshly observed facts. Record the read-only inventory, complete protected register, allowlist and isolation/database identities; NixOS impact and actual shop-only mutations; unchanged protected configurations, identities, listeners and restart counters; observed resource limits/path coverage; storage/project credentials and billing scope. Qualify client identity, publication interruption, renewals, failure and rollback behavior off-host. Record only bounded shop checks/read-only comparison from `mx1`. Public TLS/DNS/IPv4/IPv6 evidence is required before claiming public activation; missing protected-service authority is a precise deferred step, not a reason to abandon local completion.

### Phase 12: Backups, operating alerts and financial/licensing restore rehearsal

**Goal:** Operators restore only the independent shop PostgreSQL cluster from encrypted off-host sbg pgBackRest full/differential/WAL backups with separate namespaces and independently recoverable artifacts/secrets; existing PostgreSQL instances are never targets.
**Depends on:** T08,T10–T11; T09 for actual-bank proof
**Requirements:** OPS-01, OPS-02, OPS-03, OPS-04, OPS-05, OPS-06, OPS-07, OPS-08
**Source:** SLL-xSPI-MC-Shop-Codex-Handoff-2026-10-21.md T12; complete companion proposal remains normative.
**Estimate:** 3–5 engineer-days
**UI hint:** no
**Plans:** Detailed executable plans created at phase planning; no completion credit from earlier task numbers.

**Success Criteria:**

1. Operators restore only the independent shop PostgreSQL cluster from encrypted off-host sbg pgBackRest full/differential/WAL backups with separate namespaces and independently recoverable artifacts/secrets; existing PostgreSQL instances are never targets. Shop-owned metrics/alerts cover WAL, backups, resource/storage growth, certificate, jobs/mail/payments/fulfilment/support with named owners; existing SMTP/monitoring interfaces are consumed unchanged or the precise integration stays deferred. (OPS-01, OPS-06)
2. Recovery mode blocks mutating bank/SMTP/workers before data exposure; restored sessions/challenges are invalidated, post-point grants/revocations reconciled and consumed MFA codes recovered/reset before access. Complete-pool-loss recovery succeeds on an independently authorized off-host target without production rpool data/snapshots/local backups or host-only secrets; fault/exhaustion/restart/restore drills never run on mx1 or its existing MicroVM. (OPS-02, OPS-07)
3. Restored financial/order/acceptance/host/document/key records reconcile complete external windows and retained versions under original identities; missing acceptance or ambiguous preparation holds affected operations. Independent shop backup jobs and custody qualify real 35-day retained backup/WAL/artifact/evidence growth and 70%/85% shop/pool warnings; required recovery/evidence is never pruned to fit the illustrative object-storage estimate. (OPS-03, OPS-08)
4. Support credits/reservations/completed work reconcile after restore without restoring spent hours, including a debit committed before completion-archive acknowledgement; missing completion is never invented. (OPS-04)
5. An isolated off-host full-pool-loss drill measures five-minute WAL archive timeout, 35-day recovery window, 15-minute DB RPO and four-hour operator-start technical restore separately from detection/response/safe reopening, including replacement provisioning and DNS/TLS timing. (OPS-05)

**Required outputs:** Independently owned shop pgBackRest base/differential/WAL backup to off-host storage; isolated recovery mode, evidence, custody and monitoring/ownership runbooks. Prepare shop health/alert interfaces without editing existing Prometheus/Grafana/Blackbox/Alertmanager/SMTP or backup jobs. Rehearse a simulated complete loss of `rpool` only on an isolated off-host replacement resource, recovering shop configuration/artifacts/credentials and business state. Document replacement-host or explicitly authorized future-cloud restoration and separately authorized traffic activation.

**Normative acceptance:** Prove recovery without reading surviving production `rpool` data, same-pool snapshots/local backups or credentials available only on that host. Do not make the actual pool unavailable, change protected resources, run restore/fault/exhaustion/restart drills on `mx1` or its MicroVM, or automatically buy infrastructure. Use isolated off-host credentials, quarantine and a separately identified shop test database; never restore into an existing PostgreSQL service. Before exposing restored data, stop only isolated shop effect workers and block their mutating bank/SMTP access. Restore database/artifacts/keys; permit read-only complete-window bank reconciliation; reconstruct missing order/acceptance/host records, document reservations, delivered keys and support debits. Prepared evidence does not prove completion. Preserve identities, hold missing contract evidence and avoid duplicate licences/support credits or reused invoice numbers. Qualify five-minute WAL archive timeout and 35-day recovery window; measure 15-minute DB RPO and four-hour technical restore after operator start, recording full safe-reopen delay separately. These targets never authorize loss of externally committed financial/licensing/support facts. Qualify SBG Object Lock, private ACLs and custody. Invalidate restored sessions/challenges, reconcile revocations and recover/reset used MFA recovery codes before privileged access; hold unresolved prepared support work. Monitoring/SMTP integrations use existing interfaces unchanged or remain deferred.

**Verification/evidence:** Dated isolated off-host drill representing unavailable production storage, without touching it; recovery inputs/custody, replacement runtime and conditional traffic plan, externally completed operations beyond the restore point, data-loss/technical/safe-reopen timings, retained versions/keys and no unintended bank/email effects. Prove denied revoked/restored access and recovery of a debit committed before completion-archive acknowledgement. Record shop-owned reporting for archive/retention/growth/resource faults and existing unchanged alert delivery where provisioned; otherwise list the specific deferred monitoring integration and named response owner.

### Phase 13: Integrated product, access, payment and deployment acceptance

**Goal:** Release reviewers can trace every source field/option/rule to exercised customer/staff journeys, exact new IDs/hostnames and source/profile/approval revisions.
**Depends on:** T04,T06–T12, with conditional external evidence
**Requirements:** UAT-01, UAT-02, UAT-03, UAT-04, UAT-05
**Source:** SLL-xSPI-MC-Shop-Codex-Handoff-2026-10-21.md T13; complete companion proposal remains normative.
**Estimate:** 3–5 engineer-days
**UI hint:** yes
**Plans:** Detailed executable plans created at phase planning; no completion credit from earlier task numbers.

**Success Criteria:**

1. Release reviewers can trace every source field/option/rule to exercised customer/staff journeys, exact new IDs/hostnames and source/profile/approval revisions. (UAT-01)
2. Integrated cases cover multi-vendor direct/quote orders, higher-volume quote, support-only/mixed checkout, private host access, rehosting/renewal and support usage statements. (UAT-02)
3. Risk-based regression checks cover payment uncertainty/duplicates, cross-resource/MFA denial, static/no-JS/offline accessibility, public/log leaks, restored support/document/grants and two-release rollback. (UAT-03)
4. Evidence separates operator-supplied facts, local/synthetic results, selected-bank sandbox, current mx1 read-only/bounded qualification, actual Object Storage, independent off-host recovery and production; unexecuted gates remain pending. (UAT-04)
5. Ten-customer/two-staff/bounded-burst capacity, OOM/quota exhaustion, runtime failure/restart/rollback are qualified off-host; mx1 uses bounded shop smoke checks and read-only comparison of every protected resource, with no proxy-reload exception. (UAT-05)

**Required outputs:** One integrated release-candidate check against the supplied definition and selected shared-host architecture: complete customer/admin journeys, exact source coverage, pricing/licensing/support behavior, accessibility, privacy, static HTTP/release behavior, resource containment, protected-service coexistence and complete-pool-loss recovery evidence.

**Normative acceptance:** Use risk-based end-to-end cases instead of repeating every unit test. Fail on unapproved public placeholders, unintended product IDs/fields/routes, stale hostnames or mixed catalog/terms. Verify no raw host IDs/keys/secrets in public output or ordinary logs. Exercise unauthenticated-customer denial, multi-vendor quote/direct order, higher-volume quote, support-only top-up/statement, rehosting/renewal, bank uncertainty and restored support/document/grant history. Run ten-customer/two-staff/bounded-burst qualification and runtime failure/exhaustion/restart/rollback tests in an isolated off-host environment. On `mx1`, use only bounded shop functional checks, read-only resource enforcement inspection and before/after protected-service latency/health/identity/restart-counter/listener comparison. The protected baseline must remain unchanged; there is **no reviewed-proxy-reload exception**. Test actual ingress only when its complete authorized unchanged path exists. Record unexecuted real-bank/host/storage gates and service/action blockers without blocking unrelated completion.

**Verification/evidence:** Traceability checklist, reproducible release/host/configuration identifiers, scoped commands/outcomes, sanitized screenshots where useful, effective cgroup/path/quota observations, before/after protected-service records, measured coexistence/restore results, unresolved risks and fixed-regression results. Stop optional repeated testing once the concrete risks and required gates are covered.

### Phase 14: Release handover and separately scoped live activation

**Goal:** Operators receive release/config/catalog/document identities, bank obligations, protected-resource register, shop mutation allowlist/isolation/database map, complete NixOS activation-impact review, shop-only rollback and independent recovery/custody runbooks.
**Depends on:** All applicable tasks plus affected commercial/operating decisions
**Requirements:** REL-01, REL-02, REL-03, REL-04, REL-05
**Source:** SLL-xSPI-MC-Shop-Codex-Handoff-2026-10-21.md T14; complete companion proposal remains normative.
**Estimate:** 2–3 engineer-days
**UI hint:** no
**Plans:** Detailed executable plans created at phase planning; no completion credit from earlier task numbers.

**Success Criteria:**

1. Operators receive release/config/catalog/document identities, bank obligations, protected-resource register, shop mutation allowlist/isolation/database map, complete NixOS activation-impact review, shop-only rollback and independent recovery/custody runbooks. (REL-01)
2. Live activation rejects missing prices/rights/host/seller/tax/legal/retention/bank/recovery/owner approvals, synthetic adapters and unqualified external proofs without blocking unaffected preparation. (REL-02)
3. Any allowed external action records its exact resource/action authority, verified shop ownership, before/after protected-state comparison, DNS/TLS/mail/bank/activation result and storage cost/cleanup; unexecuted activation remains pending. (REL-03)
4. The handover report separates completed work, conditional work, P-01–P-12 decisions, actual external changes and the precise next missing input. (REL-04)
5. A necessary protected-resource change is deferred until later explicit authorization names that exact service and action; generic deployment approval cannot override protection, DNS-01 cannot create ingress, and rollback never restores a host generation or protected resource. (REL-05)

**Required outputs:** Final protected register, shop mutation allowlist/isolation map, complete NixOS impact plan and shop-only rollback; release/catalog/documents, bank configuration/obligations, Object Storage scopes/costs, operators/custody, support/licensing/off-host recovery runbooks and evidence report. Separately list proposed protected-service actions and conditional DNS/certificate changes; none is executable under generic deployment approval. Execute only additions/activation whose required authority and protection checks are satisfied.

**Normative acceptance:** No unknown prices, rights, host mechanism, seller/tax terms or operator is inferred. Confirm `shop.xspi.pro`/bank callback origins, staff boundaries, source/profile revisions, resource budgets, shared-outage assumptions and off-host recovery evidence. Real transactions/messages/DNS/activation require their scoped authority. Earlier generic deployment or proxy approval cannot override the latest protection mandate. Any protected change must have later explicit authorization naming the exact service/action; otherwise defer only that step and public activation. Verify the untouched complete traffic/certificate path before A/AAAA changes. Rollback affects only proved shop-owned additions while preserving committed business records; never restore a host generation or restart/revert protected services. No unselected rental, disk alteration or automatic migration. Report completed/conditional work and actual actions without claiming an unexecuted system is live.

**Verification/evidence:** Final manifest, release and new shop configuration identities, sanitized baseline/after inventories and ownership proof, actual mutation receipts, any later service/action-specific authorization, complete traffic-path evidence before DNS activation, shop-only rollback and actual storage billing/cleanup. Explicitly report unchanged protected resources and precise deferred actions. Report no external mutation/purchase unless it occurred; do not label a reviewable proposal as an executed change.

## Progress

| Phase | Plans complete | Status |
|---|---|---|
| 1 | 2 / 2 | Documentation reconciled |
| 2 | 2 / 18 | Ready for 02-00; implementation not resumed |
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
