# Requirements: SLL xSPI-MC Shop

**Defined:** 2026-10-21
**Status:** October 21 protected-services replan. SRC documentation reconciled; Phase 2 partial; all new host/runtime criteria pending execution.
**Core Value:** Turn an exact reviewed xSPI-MC configuration or support purchase into attributable acceptance, verified payment and recoverable licence delivery or support credit without duplicate effects.

## v1 Requirements

### Product authority and decisions

Source: new handoff T01; full proposal supplies normative detail.

- [x] **SRC-01**: Operators can verify the exact embedded product snapshot by filename, 23,969-byte length and SHA-256, using only the October 21 package as new product authority.
- [x] **SRC-02**: Reviewers can trace all three ordered vendors, thirteen families, thirteen logical controls, nineteen checkout groups, two helpers, four IP declarations and separate marketing control to source locations.
- [x] **SRC-03**: Operators can inspect one P-01–P-12 register with status, owner, evidence and the exact affected live operation; pending decisions do not block unrelated planning.
- [x] **SRC-04**: Reviewers can identify repository scope, new product/profile IDs, superseded assumptions and customer hostname without treating old task completion as new acceptance.

### Reproducible foundation

Source: new handoff T02; full proposal supplies normative detail.

- [ ] **BUILD-01**: Developers can reproduce static frontend, Django/worker and real-PostgreSQL development builds from compatible pinned dependencies, hashes and CI commands.
- [ ] **BUILD-02**: Reviewers can inspect component/transitive licences and SBOM for the actual locked artifacts; exact patches are verified when lockfiles are created.
- [ ] **BUILD-03**: Developers can run isolated synthetic bank/mail/storage fixtures and versioned OpenAPI/schema contracts without production credentials or external provisioning.
- [ ] **BUILD-04**: Operators can review pinned NixOS-declared rootless Podman Quadlet/user-systemd artifacts for separate Django, one worker, new shop PostgreSQL and internal Caddy containers directly on mx1 under the dedicated proposed shopsvc account, with one lifecycle per container.

- [ ] **BUILD-05**: Operators can review a shop identity/mutation map for UID/GID/subordinate mappings, rootless stores, units, networks, unused loopback ports, credentials and separate database cluster/PGDATA/roles/socket/backup identities; database mutations require positive destination checks.
- [ ] **BUILD-06**: Prepared host-controlled aggregate shop limits cover payload scopes, conmon, network helpers and backups: proposed CPUQuota=200%, MemoryHigh=6G, MemoryMax=8G, bounded TasksMax/concurrency; protected parent policies, cpusets and guest allocations remain unchanged.
- [ ] **BUILD-07**: Prepared local ZFS shop storage enforces an 80 GiB aggregate cap including descendants/snapshots and a 50 GiB PostgreSQL allowance including indexes/WAL; GraphRoot/images/volumes/temp/certificates/logs/spool are accounted and shared journal/reserves/disks remain unchanged.
- [ ] **BUILD-08**: Operators can review the complete evaluated NixOS closure, activation scripts, unit/user/mount/dependency and restart/reload impact before any host write; artifacts separate verified shop-only additions from deferred protected changes, without blanket activation.

### Catalog rules and price authority

Source: new handoff T03; full proposal supplies normative detail.

- [ ] **CAT-01**: Editors can compile one reviewed Markdown/YAML catalog into immutable public/private manifests with the same revision; incomplete approvals cannot be activated through editable content.
- [ ] **CAT-02**: Both browser and backend validate exact vendor/family/term/band relationships through strict schemas, cross-file checks and bounded predicates/named validators with shared conformance cases.
- [ ] **CAT-03**: Customers receive draft, invalid, requires_quote, awaiting_review or purchasable results with structured reasons; unknown necessary coverage/rights/access/prices remain unpurchasable.
- [ ] **CAT-04**: Price calculations use bounded exact minor-unit integers, approved per-licence allowances and distinct family coverage, with annual/one-time/tax components and recurrence; provisional five-plus-five/€50 values never become live rates.
- [ ] **CAT-05**: Public output excludes private approvals, host instances, implementation comments and unresolved production placeholders; labelled synthetic examples remain distinguishable.

### Static configuration and fallback

Source: new handoff T04; full proposal supplies normative detail.

- [ ] **SHOP-01**: Customers can read static product/support/legal pages and select only the exact ordered vendor/family/term/band options, including Altera-only RDP and higher-volume quotation.
- [ ] **SHOP-02**: Customers can change vendor, term, access modes and counts with the specified notice/reset behavior while unrelated details/support persist; fixed-row reductions allow choice/cancel and cleared host data never revives.
- [ ] **SHOP-03**: Customers see accessible labelled controls, keyboard/mobile behavior, error focus and state-appropriate actions with separate annual/one-time prices and optional unticked marketing.
- [ ] **SHOP-04**: Customers can use Django /purchase/simple/ without JavaScript under the same domain rules; backend failure gives truthful status and does not claim persistence or payment.
- [ ] **SHOP-05**: Customers see masked host summaries and no raw host IDs, private links, business/tax records or keys in public bundles, URLs or default browser storage.

### Transactions and evidence primitives

Source: new handoff T05; full proposal supplies normative detail.

- [ ] **DATA-01**: Business records for contacts, configuration/host revisions, quotes/orders, acceptance, money, licensing, support and evidence are persisted with reconstructable immutable snapshots.
- [ ] **DATA-02**: Committed domain work and notification outbox entries survive crashes through short leases and bounded retries; uniqueness and idempotency protect all intended effect identities.
- [ ] **DATA-03**: Workers release database transactions before network calls and recover abandoned work without duplicate domain effects, demonstrated with real PostgreSQL.
- [ ] **DATA-04**: Archive primitives verify recoverable object version/hash/retention and distinguish prepared from completed evidence; error/log paths redact sensitive values.

### Verified access and host privacy

Source: new handoff T06; full proposal supplies normative detail.

- [ ] **AUTH-01**: Customers exchange deliberate single-use email verification for rotated resource-scoped host-only secure sessions; GET scanners/replay do not consume credentials or accept contracts.
- [ ] **AUTH-02**: Purchasing, invoice and technical contacts receive explicit verified memberships; cross-customer/domain equality grants no unrelated resource access.
- [ ] **AUTH-03**: Every staff/admin/custom privileged route requires MFA and role/resource permission, with recent verification for sensitive actions and safe recovery; customer hostname returns 404 for staff aliases.
- [ ] **AUTH-04**: Authorized customers edit encrypted key-versioned host bindings under revision control, using actual manager-specific normalization and duplicate rules; fixed rows match nodes and floating seats use the approved server model.
- [ ] **AUTH-05**: Private raw-host access, CSRF/origin controls, key recovery and revocation are audited; unknown manager profiles hold qualification without inventing a universal MAC format.
- [ ] **AUTH-06**: Customers can independently withdraw marketing preference without affecting service messages or paid rights.

### Cart, quote and acceptance

Source: new handoff T07; full proposal supplies normative detail.

- [ ] **COM-01**: Customers retain separate configured IP lines at quantity one across vendors and explicit duplicate scopes; support has positive real package quantity and zero selector value omits its line.
- [ ] **COM-02**: Customers review exactly the selected line IDs/revisions; any review/quote-only line blocks combined payment until explicit cart editing or a combined quote, with no silent dropping/splitting/merging.
- [ ] **COM-03**: Quotes freeze immutable scope, host, component price, tax, document and validity versions; one accepted revision produces one acceptance/order across browser sessions and idempotency keys.
- [ ] **COM-04**: Business checkout preserves nineteen source groups with country-aware applicability and approved tax/status options; same-as helpers resolve final values and purchaser/licensee differences enter review.
- [ ] **COM-05**: IP orders capture all four exact versioned declarations, support-only orders capture applicable general/support/refund terms and owner/quantity without IP fields, and mixed orders accept both document sets.
- [ ] **COM-06**: One guarded review/acceptance service rejects tampered totals and stale catalog/host/terms/entity revisions, records signatory/authority/hashes/time and separates quote validity, order payment-start deadline and bank-session expiry.

### Synthetic payments and finance safety

Source: new handoff T08; full proposal supplies normative detail.

- [ ] **PAY-01**: Payment preparation commits order/acceptance/attempt/reference identities, archives recoverable snapshots, then rechecks cancellation/deadline/holds/activation before one dispatch claim.
- [ ] **PAY-02**: A potentially dispatched timeout is uncertain and cannot trigger a blind second charge; preparing means no known dispatch and browser navigation cannot confirm money.
- [ ] **PAY-03**: Only authenticated matched merchant/currency/amount/reference observations can confirm financial facts; durable bounded callbacks distinguish notification hints from payment evidence.
- [ ] **PAY-04**: Retries, different keys, reordered callbacks and two successful captures preserve both money events, one intended fulfilment and a finance overpayment case.
- [ ] **PAY-05**: Capture/refund intents are archived before supported effects and preserve requested/uncertain/confirmed history; fake-bank fault injection covers crashes, archive failure, cancellation and ambiguous success.

### Selected-bank qualification

Source: new handoff T09; full proposal supplies normative detail.

- [ ] **BANK-01**: One selected eligible merchant adapter implements only documented hosted domains, callback verification, key rotation and normalized authorization/capture states with distinct sandbox/production controls.
- [ ] **BANK-02**: Operators can reconcile complete transaction/statement windows including payments/refunds missing locally, preserving pagination/cutoff/completeness evidence and audited export fallback.
- [ ] **BANK-03**: Each creation/refund/capture/void capability has dated primary evidence for recovery/idempotency/reference behavior; unqualified operations remain disabled.
- [ ] **BANK-04**: Activation evidence records actual product/territory/currency/method eligibility, fees and acquirer PCI/ASV obligations and sanitized sandbox cases separately from synthetic tests.

### Licence, support and finance workflows

Source: new handoff T10; full proposal supplies normative detail.

- [ ] **FUL-01**: Staff manually release one approved encrypted RTL/manual/reference design/key package per intended paid/accepted scope after checking entity, release/tool/coverage, host, term, production and holds.
- [ ] **FUL-02**: Private artifacts/delivery manifests and invoice/credit-number reservations are archived before activation/issue; every artifact/document download checks resource entitlement and uses short-lived version-bound bearer access.
- [ ] **FUL-03**: Renewal, rehosting and family/node/production upgrades create reviewed cases and applicable new revisions/orders without rewriting historical rights, promising physical recall or automatically charging.
- [ ] **FUL-04**: Each paid/accepted support package credits exactly 36,000 seconds once after archival and never expires or renews IP rights; standalone top-ups require no new IP configuration.
- [ ] **FUL-05**: Support reservations/authority are archived before work; concurrent task posting cannot overspend or duplicate debits, completion is archived before publication, and corrections reverse/replace history.
- [ ] **FUL-06**: Committed task statements show task/cumulative/remaining usage; mail retry never debits again and refunds of consumed credit require review without erasing work or negative usable balances.

### Protected mx1 host, conditional ingress and static publication

Source: new handoff T11; full proposal supplies normative detail.

- [ ] **HOST-01**: Before the first mx1 deployment write, operators record a sanitized read-only inventory of host/configuration identity and every pre-existing rootful/rootless/native/VM resource in all lifecycle states; unknown ownership remains protected.
- [ ] **HOST-02**: Public ingress/TLS uses a complete already working unchanged route/certificate contract or stays deferred with an exact protected-service/action proposal; DNS A/AAAA activation requires end-to-end authorized path proof, Route 53 authority and staff-host approval.
- [ ] **HOST-03**: Caddy routes API/private/simple purchases before static matching, isolates staff, and fetches only manifest-listed GET/HEAD objects over verified fixed HTTPS Host/SNI with sensitive headers/query metadata stripped.
- [ ] **HOST-04**: Immutable publication verifies hash/MIME/route/ACL completeness before one validated route switch; interrupted upload/failed load/rollback and cached two-release assets remain safe.
- [ ] **HOST-05**: Authorized Object Storage checks prove public approved objects/private listing/private-object denial and HTTP semantics; mx1 checks are bounded/read-only comparisons, with new-shop certificate evidence only on a qualified unchanged path.

- [ ] **HOST-06**: Operators prove every proposed mx1 mutation is within the current shop allowlist and actual authority; all pre-existing services, stopped/failed resources, shared proxies/TLS/firewall/monitoring/SMTP/backups and MicroVM infrastructure remain unchanged.
- [ ] **HOST-07**: Operators observe effective shop ancestor/controller/path/quota enforcement and separate database destination read-only on mx1; missing support or capacity defers the step or qualifies smaller shop limits off-host without protected reallocations.
- [ ] **HOST-08**: Before/after configuration fingerprints, identities, listeners, lifecycle/restart evidence and bounded health observations detect adverse impact; stop shop activity and safely revert only proved shop additions, preserving business records and never repairing protected services.
- [ ] **HOST-09**: Storage project/bucket/credential/tariff/bandwidth scopes are qualified without modifying partner project 001-xspi-pro; no production compute/block/IP purchase, billing conversion, automatic paid fallback, disk restructuring or permanent staging VM is selected.

### Recovery and operating readiness

Source: new handoff T12; full proposal supplies normative detail.

- [ ] **OPS-01**: Operators restore only the independent shop PostgreSQL cluster from encrypted off-host sbg pgBackRest full/differential/WAL backups with separate namespaces and independently recoverable artifacts/secrets; existing PostgreSQL instances are never targets.
- [ ] **OPS-02**: Recovery mode blocks mutating bank/SMTP/workers before data exposure; restored sessions/challenges are invalidated, post-point grants/revocations reconciled and consumed MFA codes recovered/reset before access.
- [ ] **OPS-03**: Restored financial/order/acceptance/host/document/key records reconcile complete external windows and retained versions under original identities; missing acceptance or ambiguous preparation holds affected operations.
- [ ] **OPS-04**: Support credits/reservations/completed work reconcile after restore without restoring spent hours, including a debit committed before completion-archive acknowledgement; missing completion is never invented.
- [ ] **OPS-05**: An isolated off-host full-pool-loss drill measures five-minute WAL archive timeout, 35-day recovery window, 15-minute DB RPO and four-hour operator-start technical restore separately from detection/response/safe reopening, including replacement provisioning and DNS/TLS timing.
- [ ] **OPS-06**: Shop-owned metrics/alerts cover WAL, backups, resource/storage growth, certificate, jobs/mail/payments/fulfilment/support with named owners; existing SMTP/monitoring interfaces are consumed unchanged or the precise integration stays deferred.

- [ ] **OPS-07**: Complete-pool-loss recovery succeeds on an independently authorized off-host target without production rpool data/snapshots/local backups or host-only secrets; fault/exhaustion/restart/restore drills never run on mx1 or its existing MicroVM.
- [ ] **OPS-08**: Independent shop backup jobs and custody qualify real 35-day retained backup/WAL/artifact/evidence growth and 70%/85% shop/pool warnings; required recovery/evidence is never pruned to fit the illustrative object-storage estimate.

### Integrated acceptance

Source: new handoff T13; full proposal supplies normative detail.

- [ ] **UAT-01**: Release reviewers can trace every source field/option/rule to exercised customer/staff journeys, exact new IDs/hostnames and source/profile/approval revisions.
- [ ] **UAT-02**: Integrated cases cover multi-vendor direct/quote orders, higher-volume quote, support-only/mixed checkout, private host access, rehosting/renewal and support usage statements.
- [ ] **UAT-03**: Risk-based regression checks cover payment uncertainty/duplicates, cross-resource/MFA denial, static/no-JS/offline accessibility, public/log leaks, restored support/document/grants and two-release rollback.
- [ ] **UAT-04**: Evidence separates operator-supplied facts, local/synthetic results, selected-bank sandbox, current mx1 read-only/bounded qualification, actual Object Storage, independent off-host recovery and production; unexecuted gates remain pending.

- [ ] **UAT-05**: Ten-customer/two-staff/bounded-burst capacity, OOM/quota exhaustion, runtime failure/restart/rollback are qualified off-host; mx1 uses bounded shop smoke checks and read-only comparison of every protected resource, with no proxy-reload exception.

### Release and controlled activation

Source: new handoff T14; full proposal supplies normative detail.

- [ ] **REL-01**: Operators receive release/config/catalog/document identities, bank obligations, protected-resource register, shop mutation allowlist/isolation/database map, complete NixOS activation-impact review, shop-only rollback and independent recovery/custody runbooks.
- [ ] **REL-02**: Live activation rejects missing prices/rights/host/seller/tax/legal/retention/bank/recovery/owner approvals, synthetic adapters and unqualified external proofs without blocking unaffected preparation.
- [ ] **REL-03**: Any allowed external action records its exact resource/action authority, verified shop ownership, before/after protected-state comparison, DNS/TLS/mail/bank/activation result and storage cost/cleanup; unexecuted activation remains pending.
- [ ] **REL-04**: The handover report separates completed work, conditional work, P-01–P-12 decisions, actual external changes and the precise next missing input.

- [ ] **REL-05**: A necessary protected-resource change is deferred until later explicit authorization names that exact service and action; generic deployment approval cannot override protection, DNS-01 cannot create ingress, and rollback never restores a host generation or protected resource.

## v2 / Deferred Scope

No additional features committed. Automatic renewal, general organization portals, automatic proprietary key generation, FPGA builds and broad marketing campaigns require later scope.

## Out of Scope

| Feature | Reason |
|---|---|
| Legacy trial-form inventories, profiles and change sets | Superseded product authority; no earlier implementation credit |
| Automatic debits, saved cards and implied renewal | Separate customer authorization and approved policy required |
| Generic IP quantity multipliers, inferred company wallets | Would invent entitlement/ownership semantics |
| Existing service/guest/proxy/TLS/firewall/SMTP/monitoring changes | Protected; only later explicit service/action authorization can permit the named exception |
| New CMS/IdP/Redis/Celery or runtime Astro service | Outside selected architecture |

## Traceability

Updated 2026-10-22: BUILD-01–08 have partial local implementation/evidence and are In Progress, not accepted. Their checkboxes remain unchecked. See [current Phase 02 progress](phases/02-reproducible-application-and-deployment-skeleton/02-PROGRESS.md) for completed work and remaining qualification gates.

| Requirement | Phase | Status |
|---|---|---|
| SRC-01 | Phase 1 | Complete |
| SRC-02 | Phase 1 | Complete |
| SRC-03 | Phase 1 | Complete |
| SRC-04 | Phase 1 | Complete |
| BUILD-01 | Phase 2 | In Progress |
| BUILD-02 | Phase 2 | In Progress |
| BUILD-03 | Phase 2 | In Progress |
| BUILD-04 | Phase 2 | In Progress |
| BUILD-05 | Phase 2 | In Progress |
| BUILD-06 | Phase 2 | In Progress |
| BUILD-07 | Phase 2 | In Progress |
| BUILD-08 | Phase 2 | In Progress |
| CAT-01 | Phase 3 | In Progress |
| CAT-02 | Phase 3 | In Progress |
| CAT-03 | Phase 3 | In Progress |
| CAT-04 | Phase 3 | In Progress |
| CAT-05 | Phase 3 | In Progress |
| SHOP-01 | Phase 4 | In Progress |
| SHOP-02 | Phase 4 | In Progress |
| SHOP-03 | Phase 4 | In Progress |
| SHOP-04 | Phase 4 | In Progress |
| SHOP-05 | Phase 4 | In Progress |
| DATA-01 | Phase 5 | In Progress |
| DATA-02 | Phase 5 | In Progress |
| DATA-03 | Phase 5 | Pending |
| DATA-04 | Phase 5 | Pending |
| AUTH-01 | Phase 6 | In Progress |
| AUTH-02 | Phase 6 | In Progress |
| AUTH-03 | Phase 6 | In Progress |
| AUTH-04 | Phase 6 | Pending |
| AUTH-05 | Phase 6 | In Progress |
| AUTH-06 | Phase 6 | Pending |
| COM-01 | Phase 7 | In Progress |
| COM-02 | Phase 7 | In Progress |
| COM-03 | Phase 7 | In Progress |
| COM-04 | Phase 7 | In Progress |
| COM-05 | Phase 7 | In Progress |
| COM-06 | Phase 7 | Pending |
| PAY-01 | Phase 8 | Pending |
| PAY-02 | Phase 8 | Pending |
| PAY-03 | Phase 8 | Pending |
| PAY-04 | Phase 8 | Pending |
| PAY-05 | Phase 8 | Pending |
| BANK-01 | Phase 9 | Pending |
| BANK-02 | Phase 9 | Pending |
| BANK-03 | Phase 9 | Pending |
| BANK-04 | Phase 9 | Pending |
| FUL-01 | Phase 10 | Pending |
| FUL-02 | Phase 10 | Pending |
| FUL-03 | Phase 10 | Pending |
| FUL-04 | Phase 10 | Pending |
| FUL-05 | Phase 10 | Pending |
| FUL-06 | Phase 10 | Pending |
| HOST-01 | Phase 11 | Pending |
| HOST-02 | Phase 11 | Pending |
| HOST-03 | Phase 11 | Pending |
| HOST-04 | Phase 11 | Pending |
| HOST-05 | Phase 11 | Pending |
| HOST-06 | Phase 11 | Pending |
| HOST-07 | Phase 11 | Pending |
| HOST-08 | Phase 11 | Pending |
| HOST-09 | Phase 11 | Pending |
| OPS-01 | Phase 12 | Pending |
| OPS-02 | Phase 12 | Pending |
| OPS-03 | Phase 12 | Pending |
| OPS-04 | Phase 12 | Pending |
| OPS-05 | Phase 12 | Pending |
| OPS-06 | Phase 12 | Pending |
| OPS-07 | Phase 12 | Pending |
| OPS-08 | Phase 12 | Pending |
| UAT-01 | Phase 13 | Pending |
| UAT-02 | Phase 13 | Pending |
| UAT-03 | Phase 13 | Pending |
| UAT-04 | Phase 13 | Pending |
| UAT-05 | Phase 13 | Pending |
| REL-01 | Phase 14 | Pending |
| REL-02 | Phase 14 | Pending |
| REL-03 | Phase 14 | Pending |
| REL-04 | Phase 14 | Pending |
| REL-05 | Phase 14 | Pending |

**Coverage:** 80 v1 requirements; 80 mapped exactly once; 0 unmapped.

Local implementation evidence for CAT/SHOP and initial owner/retry DATA/AUTH behavior: [quick261022-dj5](quick/261022-dj5-amend-local-execution-sequence-and-deliv/261022-dj5-SUMMARY.md). Checkboxes remain pending full acceptance; verified customer access, staff MFA, private approvals, approved money and release qualification are not claimed. Current sequence follows the execution amendment.

Local T06/T07 prerequisite evidence: [quick261022-hrl](quick/261022-hrl-verify-local-customer-access-through-cap/261022-hrl-SUMMARY.md). AUTH-01/02/05 cover synthetic session/owner behavior only; real delivery, full memberships, staff MFA and recovery remain pending.


## Current local implementation — 2026-10-23

Current development focus is Phase7, not a completed Phase7; last fully completed phase is1 and Phases2–6 remain partial/qualification-pending. See [STATE.md](STATE.md), [ROADMAP.md](ROADMAP.md) and the [local workflow audit](audits/2026-10-23-local-workflow.md). AUTH-03 and COM-01–05 have partial local implementation: staff rehearsal, cart/quotation/review/business scopes and declaration/preparation previews. Their requirement checkboxes remain unchecked. No approved offer, tax decision, declaration acceptance or order conversion is claimed; COM-06 remains pending. Full phase counts remain1/14 and10/20 plans; Country/tax answers and release gates remain pending.



Latest local evidence: [Django saved cart](quick/261023-cll-implement-no-javascript-multi-line-cart-/261023-cll-SUMMARY.md),170 core-local tests. SHOP-04/AUTH/COM behavior has local evidence only; all requirement checkboxes unchanged. Next: add deliberate no-JavaScript quotation-request capture from an exact saved cart revision using existing retry and owner protections. Country/tax and commercial effects pending.

Latest local evidence: no-JavaScript saved cart;170 core-local tests, source126 files18 templates. History implementation120f0a5 synced. Focus7/completed1; Phase02 8/18 unchanged. Reviewed 2026-10-23T09:10:53.964791+00:00.
