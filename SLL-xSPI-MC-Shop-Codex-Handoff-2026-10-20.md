# SLL xSPI-MC Shop — Codex Implementation Handoff

**Revision:** 20 October 2026 · **Customer hostname:** `shop.xspi.pro` · **Companion specification:** [SLL-xSPI-MC-Shop-Proposal-2026-10-20.md](SLL-xSPI-MC-Shop-Proposal-2026-10-20.md).

## Start here

Implement the authorized local/repository scope of the accompanying proposal, using **`SLL_xSPI_MC_Product_Page.md` as the sole product-definition source**. Read the full proposal, its exact source appendix and the applicable repository instructions before changing code. Continue through the tasks and prepare reviewable deployment artifacts. Keep unresolved commercial values explicitly pending and complete unaffected work while waiting for a fact needed by a later phase.

This handoff and its companion proposal supersede prior versions for the new implementation. The public domain is **`shop.xspi.pro`**. Do not infer completion from an earlier task with the same number. Do not restore obsolete product inputs, names, rules or deployment assumptions through old scaffolding. Preserve unrelated repository work and any existing business history.

An instruction to implement this plan authorizes the local/repository work it describes. Cloud spending, billing conversion, live DNS or certificate operations, messages to real recipients, bank charges/refunds and production cutover are performed only within the scope SLL actually authorizes. Prepare the concrete change, impact, validation and rollback first; do not repeatedly seek permission for already authorized reversible work.

### Package identity and authority

| Item | Exact identity or rule |
|---|---|
| Proposal filename | `SLL-xSPI-MC-Shop-Proposal-2026-10-20.md` |
| Proposal SHA-256 | `d8db6b54e3e887ca940f0faff0949ca1a1fa2ce24c26075aabd78925f0f60356` |
| Supplied product filename | `SLL_xSPI_MC_Product_Page.md` |
| Original product bytes | 23,969 UTF-8 bytes, including its final newline |
| Original product SHA-256 | `562dc4015c62f165df5df3e9ae1aab26b8102385d9dc76a556d5965ddc1a0263` |
| IP product ID | `sll-xspi-mc` |
| Support product ID | `sll-xspi-mc-support-10h` |
| Product profile ID | `sll-xspi-mc-v1` |
| Customer origin | `https://shop.xspi.pro` |
| Staff origin | Proposed `https://shop-admin.xspi.pro` |
| DNS zone | Route 53 `xspi.pro`; verify actual control, delegation and zone ID |
| Source availability | Exact source embedded under “Product source snapshot” in the proposal; a separate third file is unnecessary. |

Copy the source appendix to `docs/product-source/SLL_xSPI_MC_Product_Page.md` or the equivalent approved repository path and verify its hash. If a separately supplied source differs, retain both evidence versions and identify the changed requirements before replacing the agreed source. The latest explicit SLL instruction governs authorized scope; the source supplies product meaning, approved decisions complete provisional policies, and the proposal supplies architecture. Report a material conflict instead of silently choosing an old interpretation.

All paths below are proposed responsibilities within the chosen repository, not evidence that those files or a deployed application already exist. Match the repository organization table in the proposal and record any conventional path mapping.

## Fixed architecture and proposed operating values

| Concern | Implementation contract |
|---|---|
| Frontend | Static Astro with build-time Markdown Content Collections and React islands. Public HTML/assets live in OVH Object Storage. No request-time Astro/Node service. |
| Backend | Django LTS + PostgreSQL + one durable PostgreSQL-backed worker/outbox. No mandatory Redis/Celery, commercial commerce edition, CMS or external identity platform. |
| Software | Researched baselines Django 5.2.18 LTS and PostgreSQL 18.6; compatible supported Astro 7/React 19, Node 24 LTS and Python 3.13. Verify exact patch releases, artifact hashes, compatibility and licences when creating lockfiles. |
| VM | New OVH B2-7 in GRA11, with two vCPUs, 7 GB RAM and included 50 GB root SSD; legacy monthly billing after actual quote/image/workload qualification. B3-8 hourly is the documented fallback. |
| Service management | Prefer native hardened systemd on a supported pinned NixOS release. Qualify the custom-image/bootstrap route. Rootless Podman on an approved supported Linux is a fallback if needed, not a second simultaneous service manager. |
| Primary storage | Separate 50 GB High Speed PostgreSQL volume in the same compute region; public and private S3 objects in `gra`; private delivery access controlled by the application. |
| Recovery storage | Separate `sbg` mutable database backups, retained financial/licensing/support evidence and protected artifact copies; distinct scoped credentials. |
| Ingress | Caddy on the new VM; customer API, protected customer routes and no-JS purchase route matched before static routes. Staff paths only on the staff hostname, with MFA. |
| Object origin | Fixed HTTPS object-API origin with correct Host/SNI and certificate verification. Approved public objects, private bucket listing; no credentials/query/client metadata sent to the static origin. |
| TLS | Dedicated new certificate/key for each application hostname. Standard HTTP-01/TLS-ALPN-01 first; conditional DNS-01 only when needed and with the proposal's scoped IAM/module design. |
| Existing services | Consume supplied existing SMTP through a shop-scoped credential. No reuse of existing-host administrator access, private keys or live service state. |
| Mode defaults | Synthetic bank/mail/storage for local work; live acquiring disabled until affected approvals and actual integration evidence exist. |

The modeled OVH production budget is **£27.20/month ex VAT**, or **£29.24** with 100 hours of temporary D2-4 staging and stated fixture storage. Permanent D2-4 staging brings the combined modeled total to **£38.76**. These are derived estimates using published UK tariffs and 730 metered hours; use the proposal's full arithmetic, service units and exclusions. Route 53 adds its actual incremental DNS charges. Confirm IPv4 billing for all ranges, included older-generation disks, Gen3 separately billed disks and billing-mode constraints before provisioning. No tariff, quota or performance has been verified inside SLL's project.

Proposed initial operational values are a five-minute WAL archive timeout, 35-day database recovery window, 15-minute database RPO target and four-hour technical restoration after an operator starts. Full safe reopening also includes operator response and reconciliation. Start with bounded worker/database concurrency, qualify ten interactive customers plus two staff and a bounded burst, and retain measured memory/resource headroom. Evidence-retention duration, support rounding and business response commitments remain policy inputs, not arbitrary technical defaults.

For `shop.xspi.pro`, update every canonical URL, Astro `site`, customer origin/CSRF setting, email-link base, API example, bank return/callback registration, DNS record, TLS name, observability check and deployment acceptance case. Keep customer/staff cookies host-only. A certificate limited to `synaptic-labs.com` or `*.synaptic-labs.com` cannot secure either `xspi.pro` application name. Actual extra SANs on the existing certificate are unknown and unnecessary for the new-certificates design.

## Product and commerce invariants

Implement these together with the full inventories and typed examples in the proposal. The examples describe the contract; T03 must turn them into complete strict schemas and cross-file validation.

1. **Exact taxonomy.** Preserve the source's three vendors and thirteen families in the supplied order. Stable vendor IDs are `altera`, `amd-xilinx` and `microchip`; the proposal supplies the exact family IDs. Preserve all three Cyclone 10 labels and hold affected offers until coverage overlap is resolved; do not silently merge labels or charge duplicate coverage.
2. **One vendor per configured licence.** Select one or more distinct families from that vendor. Another vendor means another configured IP line. Generic IP quantity is one. Explicit node/seat counts, production bands and family scope determine its rights; equal-looking lines are not automatically merged.
3. **Term availability.** `rd-annual` and `perpetual` are offered by the draft for all three vendors. `rdp-yearly` is Altera-only. R&D is a paid annual licence category with its approved use restriction; perpetual does not imply unrestricted production, updates or support.
4. **Production bands.** The RDP bands are `units-1-100`, `units-101-1000`, `units-1001-5000`, and `higher-volume` for more than 5,000, which requires quotation. Unit, measurement period, counting event, aggregation and expansion/expiry rules require approved terms. Development nodes and production units are separate quantities.
5. **Access and dependent fields.** Altera requires fixed, floating or both. Use the canonical flat values `fixed_enabled`, `fixed_node_count`, `floating_enabled` and `floating_seat_count`; enabled counts are positive integers and disabled counts zero. Fixed-host rows match the selected node count and contain optional `workstation_reference` plus required `host_id`. Floating seats use the approved server identity mechanism, not one customer-workstation row per seat. Vendor/mode changes clear incompatible hidden values and charges. Non-Altera configurations omit Altera-specific controls and await their real access profile.
6. **Host data.** Use the actual licence-manager format and approved normalization. Do not impose a universal MAC format. Raw identifiers enter only through the protected resource-scoped editor; encrypt at rest, version bindings, mask ordinary summaries and prevent disclosure through logs, URLs, public assets and browser storage.
7. **Prices and eligibility.** Unknown rates remain null and unpurchasable. The draft five-fixed plus five-floating allowance is separate per mode and per configured licence. The draft €50 extra-node rate and recurrence are unapproved. Do not multiply allowances by family count or grant unselected nodes. Distinguish `draft`, `invalid`, `requires_quote`, `awaiting_review` and `purchasable`. Use exact integer-minor money with checked bounds and separate annual/one-time/tax components.
8. **Versioned authority.** One Markdown catalog compiles public/private manifests. The backend recalculates all totals from an approved immutable offer and validates the same rules as the browser. Quote, checkout and payment snapshots retain exact configuration, host, price, rights and legal versions. Material changes require explicit review; accepted contracts are not repriced on catalog rollback.
9. **Line-type-aware checkout.** IP purchases retain the source's nineteen business-checkout groups and four required declarations, with country/policy-aware requirements. Support-only purchases need applicable support/general/refund acceptance, quantity and resource owner, with no invented IP configuration or new IP entitlement. Mixed orders accept all applicable document sets. Marketing is separate, optional and unticked, with withdrawal handling.
10. **Support as an entitlement.** `sll-xspi-mc-support-10h` has real positive cart quantity; the optional selector may be zero to omit it. Each paid/accepted package grants exactly 36,000 integer seconds once, with no expiry. Later standalone purchases work. Support does not renew annual IP rights. Usage statements show task hours, cumulative usage and remaining balance from a committed statement revision.
11. **Protected delivery.** The source deliverables are encrypted RTL, user manual, reference design and a licence key matching the approved scope. Manual issuance verifies payment/acceptance, legal entity, release, tool/coverage, term, production and host bindings. Archive artifacts and delivery evidence before enabling access. Grants are resource- and artifact-specific; short presigned URLs are bearer credentials, not guaranteed single-use links.
12. **Manual future actions.** Renewal, rehosting, family/node additions and production upgrades create reviewed cases and new applicable revisions/orders. Do not silently alter historical rights or automatically debit a payment method. Actual expiry, fees, overlap/revocation and maintenance policies are decision inputs.

The non-sensitive stateless validation API may omit private host instances and return the required private step. A browser support-package selector is a convenience that creates/updates the separate support cart line; it does not put support hours into the IP licence's node rights. Distinguish an omitted irrelevant field from an unknown required policy; neither authorizes an invented default.

## Financial, support and recovery invariants

Use the typed provider-neutral bank contract and capability matrix in the proposal. Build the synthetic adapter first, then exactly one selected eligible bank adapter after its documented merchant details arrive.

- Commit the order/acceptance reference, attempt identity, merchant reference and idempotency record; archive recoverable evidence and verify version/hash/required retention; recheck cancellation, deadline, holds and live activation; claim one dispatch; then call the bank. Never hold a long database transaction while waiting for the network.
- A not-yet-dispatched operation is `preparing`. A timeout after possible dispatch is `uncertain`, not rejected or safe to repeat. Browser navigation cannot confirm money. Exact merchant, currency, amount and reference matching uses authenticated bank observations and actual capture semantics.
- Same/different idempotency keys and concurrent browser sessions cannot create duplicate intended orders, grants or blind payment operations. A second confirmed capture is an overpayment case, preserving both financial events and one intended fulfilment.
- Callback authentication follows the actual bank protocol. A notification-only callback triggers a bounded authenticated lookup for a known attempt; it cannot set paid state. Reconciliation must discover payments/refunds absent from the local database through a complete transaction window or auditable statement import.
- Archive capture/refund intents before their supported external effects. Preserve requested/uncertain/confirmed states, reference identities and original money facts. Enable only qualified bank operations. Real financial policies and PCI/ASV scope come from the actual merchant/acquirer setup.
- Support credits are archived before becoming spendable. Approved task identity and estimate/reservation/authority are archived before chargeable work. Actual completion and ledger revision are archived before final balance/statement publication. Pending reservations cannot be spent twice; ambiguous prepared work is reconciled with operator evidence and holds the affected balance during recovery.
- Each ledger purchase/task uses a unique durable identity. Corrections reverse and replace entries. Refunding already consumed support requires review; it cannot erase performed work or silently expose a negative usable balance. An email retry never debits again.
- Recover invoice/credit-number reservations and issued-number high-water marks before allocating more. A prepared key or invoice record does not prove issue/delivery; recover its identity or hold it, rather than create a duplicate.
- Recovery mode stops side-effect workers and blocks mutating bank calls/SMTP before restoration or service exposure. After database restoration, invalidate restored customer/staff sessions and verification challenges, reconcile post-restore-point access revocations and recover/reset consumed MFA recovery codes before any application/privileged access. Then reconcile bank facts, acceptance, artifacts, numbers and support work before safe reopening.
- Database RPO does not permit forgetting an externally completed payment, issued key or performed support task. Deliberately rehearse those divergences. Prepared evidence proves intent, not completion; missing acceptance data cannot be invented from a bank charge.

## Task order and completion evidence

The estimate is **46–74 engineer-days**, excluding external waiting and ongoing operations. It is a planning range, not a Codex execution-time prediction. Independent work may proceed in parallel where dependencies permit, but code changes, live mutations and reviews must respect the actual repository and external scope.

For each task, record: status; code/catalog/configuration revisions; concrete outputs; commands or observations that demonstrate the acceptance criteria; the environment used; unresolved decisions and the exact operation affected. Do not claim cloud or bank qualification from a local mock. Complete authorized work and stop optional repeated testing once the specific risks are resolved.

### T01 — Product authority, repository review and decision register

**Dependencies:** An implementation instruction · **Planning effort:** 1–2 engineer-days.

**Outputs:** Record the supplied product definition and embedded source hash; inventory the three vendors, 13 families, terms, bands, access controls, 19 business-checkout groups, four required declarations and separate marketing choice. Establish sll-xspi-mc, sll-xspi-mc-support-10h and sll-xspi-mc-v1. Inspect any existing repository/worktree, instructions and implementation before changes; document the new scope and one decision register with approval status and affected phase.

**Acceptance:** Use this revision's product authority exclusively. Earlier task completion does not establish compliance with this task list. Retire superseded implementation assumptions in the authorized checkout, without deleting unrelated work or historical business records. All source placeholders/provisional assumptions remain explicitly pending; recording mapping/approval status does not block local implementation. The authoritative customer hostname is shop.xspi.pro.

**Evidence:** Source filename/hash and new requirement matrix; repository status and isolated working branch; recorded decisions P-01–P-12; exact product/profile IDs; scope/delta note.

### T02 — Reproducible application and deployment skeleton

**Dependencies:** T01 · **Planning effort:** 3–5 engineer-days.

**Outputs:** Static Astro/React project, Django/application/worker skeleton, PostgreSQL development service, supported dependency lockfiles and licence inventory, CI checks, synthetic mail/bank/storage boundaries, OpenAPI and full-schema scaffolding, native NixOS service modules and environment/secret templates. Prepare the OVH image/bootstrap qualification plan without provisioning.

**Acceptance:** Clean local build reproduces artifacts from pinned versions; no runtime Astro/Node server or mandatory Redis/Celery/CMS/IdP. Keep the new VM independent of existing production state. B2-7 monthly is a planning selection, not permission to spend; support the documented B3-8 fallback through configuration. A supported OS and exact Nixpkgs revision are chosen at actual deployment. No secrets in Git, Nix store derivations or static output.

**Evidence:** Build commands/results, lockfile/artifact identities, component and transitive licence/SBOM record, environment/service-boundary diagram and actual dependency compatibility checks.

### T03 — Markdown catalog, schemas and approved price calculations

**Dependencies:** T01–T02 · **Planning effort:** 4–6 engineer-days.

**Outputs:** One versioned Markdown/YAML catalog; full strict schemas and cross-file integrity checks; public/private immutable manifests; exact new option taxonomy; bounded declarative predicates/named validators; approved access/coverage/rate/terms profiles; consistent browser/backend conformance fixtures. Complete the proposal examples into production schemas rather than treating the examples as complete validators.

**Acceptance:** Validate vendor-family/term/band relationships, unique coverage, enabled-mode counts, disabled-mode reset, host-row cardinality and non-Altera profile gating. Distinguish source draft, approval and production eligibility. No arbitrary executable content. Reject missing rates instead of using zero; apply allowances per configured licence, never per family, and only if approved. Separate annual and one-time components, support quantity and tax category. Public output excludes private approvals/host IDs/internal comments and unresolved placeholders. Unapproved examples may run only in labelled local/synthetic mode.

**Evidence:** Parsed catalog and schema checks, exact vendor/family list comparison, valid/invalid/quote/review cases in both runtimes, provisional node-price boundary cases and annual-versus-one-time calculation evidence.

### T04 — Static product, configurator, support page and accessible fallback

**Dependencies:** T03 · **Planning effort:** 4–6 engineer-days.

**Outputs:** Static product/support/document pages, React configuration and price summary, separate licence/support cart presentation, quote request entry, country-aware checkout presentation, accessible errors and no-JavaScript Django purchase/simple flow using shared rules. Protected host editing integrates with T06.

**Acceptance:** Match all approved source options and declared requiredness; vendor/term/access changes clear only affected configuration and host data with notice. Show RDP only for Altera, exact nonoverlapping volume bands, higher-volume quotation, and permitted fixed/floating controls. Preserve unrelated business details and recoverable selections. Mask host IDs in summaries. Show annual and one-time costs separately, the correct action for eligibility state and useful offline behavior. Marketing is optional and unticked; implementation notes never become customer copy.

**Evidence:** Representative mobile/keyboard/screen-reader checks, all conditional/reset branches, state-specific screenshots or sanitized captures, no-JavaScript path, public bundle inspection and customer-facing copy review.

### T05 — Transactional records, durable work and private evidence primitives

**Dependencies:** T02–T03 · **Planning effort:** 3–5 engineer-days.

**Outputs:** Migrations/domain services for organizations, contacts, configured lines/host-binding revisions, quotes/orders, acceptance, financial records, licensing, support and evidence references; durable outbox/inbox, idempotency records, bounded leases/retry rules and synthetic notifications.

**Acceptance:** Persist business records before scheduling notification. Concurrency/uniqueness constraints protect line, quote, order, payment, document, licence and support identities. Worker crashes do not lose committed work; lease recovery cannot duplicate a domain effect. No long transaction spans network calls. Source configuration and acceptance snapshots are immutable and reconstructable. Host identifiers and credentials are redacted in error/log paths.

**Evidence:** Migration/reversal plan, focused transactional and lease-crash checks, schema/constraint evidence, redaction verification and clear prepared-versus-completed evidence semantics.

### T06 — Verified customer access, staff MFA and private host editing

**Dependencies:** T04–T05 · **Planning effort:** 3–5 engineer-days.

**Outputs:** Resource-scoped verified-email sessions, staff MFA/recovery and role enforcement, separate customer/staff host boundaries, protected configuration/host editor, raw-host encryption/key-version handling, explicit purchaser/invoice/technical contact membership and marketing withdrawal.

**Acceptance:** Use shop.xspi.pro and proposed shop-admin.xspi.pro with separate host-only cookies and no wildcard CORS. Customer host rejects all staff aliases. Email-domain equality grants no organization access; scanners cannot consume access credentials by GET alone. All privileged custom routes require MFA. Validate host IDs using an approved actual-manager profile rather than a universal MAC regex. Fixed rows match selected nodes; floating seats use the approved server model. Unknown formats block key qualification, not generic UI development. Mask ordinary responses, avoid host values in browser storage/URLs/logs, and qualify reauthentication for sensitive changes.

**Evidence:** Cross-customer/contact/role denial cases, scanner/replay/session/CSRF checks, raw-host data-flow inspection, canonicalization/duplicate cases for the actual supplied profile, private encryption/recovery key-version checks using synthetic values.

### T07 — Multi-line cart, quotations, business checkout and acceptance

**Dependencies:** T03,T05–T06 · **Planning effort:** 4–6 engineer-days.

**Outputs:** Multi-vendor carts with one licence scope per line, real support package quantities/support-only carts, immutable quotes, backend totals and tax decision adapter, country-aware business fields, exact document/declaration acceptance, one order conversion and separate quote/payment deadlines.

**Acceptance:** Never merge/double configured licence entitlements through generic quantity. A basket with an unapproved line cannot silently drop it or charge a partial basket. Verify the same reviewed scope and host-binding revision at acceptance/payment. Reject price tampering and stale changes; no silent repricing. One quote revision produces one acceptance/order across sessions and keys. The acknowledgements required by the applicable checkout profile remain separate from optional marketing; IP-containing orders preserve the four source declarations. Invoice/technical contacts and differing licensed entities follow approved review rules. Approved live tax/legal values can remain pending while synthetic flows work. Support-only checkout uses applicable support terms and owner/quantity confirmation with no IP configuration or new IP entitlement; mixed orders accept both applicable document sets.

**Evidence:** Full direct and quoted multi-line journeys, two-browser acceptance race, stale catalog/host/price/terms cases, synthetic tax/rounding and annual/one-time component tests, support-only purchase review. Include a support-only top-up with no vendor/family/host data and mixed-cart term applicability.

### T08 — Payment domain and fault-injectable fake bank

**Dependencies:** T05,T07 · **Planning effort:** 4–6 engineer-days.

**Outputs:** Typed bank-adapter boundary/capability record, hosted-payment preparation, protected archive-before-dispatch ordering, normalized financial observations, durable callback inbox, reconciliation and finance exception workflows, fake-bank scenarios for uncertain/missing/duplicate outcomes.

**Acceptance:** Commit order/attempt/reference then archive recoverable snapshots before bank calls. Recheck cancellation/deadline/approval/live state after archive waits before claiming dispatch. Treat network ambiguity as uncertain; browser return is never payment proof. Enforce exact order/merchant/currency/amount matches and supported authorization/capture distinctions. Different idempotency keys cannot cause concurrent blind charges. Duplicate captured attempts create one intended entitlement and an overpayment case. Preserve original financial history and archive refund/capture intents too.

**Evidence:** Injected pre/post-bank crashes, delayed/replayed/reordered notifications, wrong amount/currency/merchant, timeout-with-bank-success, two successful attempts, archive outage, cancellation race and refund ambiguity. Fake-bank evidence is labelled synthetic.

### T09 — Selected-bank sandbox integration and complete reconciliation

**Dependencies:** T08 plus supplied bank/merchant inputs · **Planning effort:** 4–7 engineer-days.

**Outputs:** One actual bank adapter, documented callback verification/status mapping, idempotency/reference recovery behavior, hosted-domain allowlist, distinct sandbox/production configuration, usable full-window transaction/statement reconciliation and supported finance operations.

**Acceptance:** Prove the actual bank protocol, including original-body verification when required, credential/key rotation, amount/currency/reference correlation and ambiguous-call recovery. Discover transactions absent from local attempt lists; a reference parameter is not proof of lookup/idempotency support. Confirm merchant product/territory/currency/method eligibility, fee quote and actual PCI/ASV expectations before activation. Disable unqualified operations. No real charge/refund without scoped authorization.

**Evidence:** Primary bank documentation and dated capability matrix, sanitized sandbox outcomes, complete-window evidence/cutoffs and explicit gaps. Missing bank details block only this integration and its dependent real proof.

### T10 — Licence delivery, renewal/rehosting and support-hours workflows

**Dependencies:** T05–T08; actual access/rights profiles for real fulfilment · **Planning effort:** 5–8 engineer-days.

**Outputs:** Manual key/package release, artifact/version/entitlement checks, private download authorization, approved term/production/node records, rehosting/renewal/upgrade cases, invoice/credit numbering, support-only top-ups and non-expiring support purchase/consumption ledger with usage email statements.

**Acceptance:** One approved release/key per intended scope; all four declared deliverables and exact host/term/coverage are checked. Archive private artifacts/delivery and document reservations before issue. 10-hour support packages grant 36,000 seconds once; concurrent task posting cannot overspend or debit twice; task emails show task/cumulative/remaining usage. Corrections preserve history. Support remains after annual IP expiry and does not renew IP rights. Refunds distinguish available from consumed credit. Resource authorization protects both packages and balances. Rehosting/renewal cannot silently mutate old rights or automatically charge a card. Archive credit grants before spendability, approved task/reservation identities before chargeable work, and actual completion before final balance/statement publication; pending reservations cannot be spent twice.

**Evidence:** Synthetic manual fulfilment and unauthorized-download checks; term-boundary and rehosting cases; support 0/1/multiple packages, standalone top-up, concurrent debits, reversal, refund-after-consumption, mail retry and annual-expiry independence; reserved-document uniqueness.

### T11 — OVH deployment, Route 53, dedicated TLS and static publication

**Dependencies:** T02–T04; cloud/DNS authorization for deployed proof · **Planning effort:** 3–5 engineer-days.

**Outputs:** Qualified new-VM image and service configuration; B2-7 GRA11 monthly quote/qualification plan with fallback; separate volumes/buckets/credentials; exact Route 53 xspi.pro records; dedicated shop/staff ACME certificates; HTTPS S3 object-origin Caddy routing; staged immutable releases and rollback.

**Acceptance:** Verify current quote/stock, legacy monthly versus hourly/Savings Plan billing, IPv4 and disk line items; convert to monthly only within authorized scope. Use shop.xspi.pro A to the new VM and proposed shop-admin.xspi.pro; AAAA only after working IPv6. Standard HTTP-01/TLS-ALPN-01 needs no Route 53 credentials; DNS-01 requires the explicitly scoped alternative. Existing synaptic-labs.com certificate or wildcard is not assumed to cover xspi.pro. Keep public bytes in OVH Object Storage, serve them through HTTPS object API with fixed Host/SNI/TLS verification, strip credentials/query data and enforce actual routes/status/cache/MIME. No live-root deletion or partial-release activation. Preserve the existing main website and DNS records outside scope.

**Evidence:** Actual authorized resource IDs/region/tariff/service privileges, public TLS/CAA and customer/staff boundaries, IPv4/IPv6 observations, anonymous-private-object denials, representative load, interrupted publication/two-release asset survival/rollback, certificate renewal staging qualification. Local mocks are not OVH proof.

### T12 — Backups, operating alerts and financial/licensing restore rehearsal

**Dependencies:** T08,T10–T11; T09 for actual-bank proof · **Planning effort:** 3–5 engineer-days.

**Outputs:** pgBackRest base/differential/WAL backup, isolated recovery mode, protected evidence storage, secret custody/recovery, monitoring and ownership runbooks, full restoration/reconciliation rehearsal with orders, host revisions, documents, key delivery and support ledger state.

**Acceptance:** Before exposing restored data, stop effect workers and block mutating bank/SMTP access. Restore database/artifacts/keys; permit read-only complete-window bank reconciliation; reconstruct missing order/acceptance/host records, document reservations, delivered keys and support debits. Prepared evidence does not prove completion. Preserve identities, hold missing contract evidence and avoid duplicate licences/support credits or reused invoice numbers. Measure proposed 15-minute DB RPO and four-hour technical target after operator start; record full safe-reopen delay separately. SBG Object Lock, private ACLs and custody must be actually qualified. Invalidate restored sessions and verification challenges, reconcile resource revocations and recover/reset used MFA recovery codes before privileged access; hold unresolved prepared support work until reconciled.

**Evidence:** Dated isolated drill with externally completed operations beyond the restore point, measured data-loss/technical/safe-reopen timestamps, retained versions/key recovery, no unintended bank/email effects, alert routing and named operator coverage. Prove denial of revoked/restored access and recovery of a debit committed before completion-archive acknowledgement.

### T13 — Integrated product, access, payment and deployment acceptance

**Dependencies:** T04,T06–T12, with conditional external evidence · **Planning effort:** 3–5 engineer-days.

**Outputs:** One integrated release-candidate check against the supplied definition and new domain: complete customer/admin journeys, exact source coverage, pricing/licensing/support behavior, accessibility, privacy, static HTTP/release behavior, performance and recovery evidence.

**Acceptance:** Use risk-based end-to-end cases instead of repeating every unit test. Fail on unapproved public placeholders, unintended product IDs/fields/routes, stale shop hostnames or mixed catalog/terms. Verify zero raw host IDs/keys/secrets in public outputs or ordinary logs. Exercise guest resource denial, multi-vendor quote/direct order, higher-volume quote, support-only top-up and usage statement, rehosting/renewal approval, bank uncertainty and restored support/document/grant history. Record any unexecuted real-bank/cloud gate without blocking unrelated local completion.

**Evidence:** Traceability checklist, reproducible release identifiers, scoped commands/outcomes, sanitized screenshots where useful, unresolved risks and fixed-regression results. Stop optional repeated testing once the concrete risks and required gates are covered.

### T14 — Release handover and separately scoped live activation

**Dependencies:** All applicable tasks plus affected commercial/operating decisions · **Planning effort:** 2–3 engineer-days.

**Outputs:** Reviewable deployment plan, release/rollback artifacts, final approved catalog/documents, bank configuration and fee/obligation record, DNS/certificate/resource changes, operator and custody assignments, support/licensing runbooks and implementation evidence report. Execute only the external activation actually authorized.

**Acceptance:** No unknown live prices, rights, host mechanism, seller/tax terms or required operating owner is inferred. Confirm exact shop.xspi.pro URLs, bank return/callback domains, staff boundaries, source/profile/approval revisions and measured restore evidence. A real test transaction, notification and DNS/production switch need their actual scoped authority; do the necessary local preparation first. Report work completed, conditional work, remaining decisions and actual external actions without claiming an unexecuted system is live or tested.

**Evidence:** Final status/evidence manifest, approved release and configuration identities, observed activation results if authorized, rollback instructions, resource billing/cleanup account and precise remaining phase-specific blockers.

## Decisions and when they matter

The table is the same P-01–P-12 register as the proposal. Track one current status, owner, evidence and affected scope for each item. A pending decision disables the specific live offer/operation it governs; it does not automatically block unrelated schema, UI or synthetic implementation. Ask for concrete missing input at the point it becomes necessary, using the prepared alternatives and their implications.

| ID | Decision or supplied fact | Recommended handling | Phase actually blocked |
|---|---|---|---|
| P-01 | Distinct Cyclone 10 coverage and approved FPGA/tool/reference-design combinations | Preserve all 13 requested labels; approve nonoverlapping licensed coverage and any reviewed restrictions. | Sale/release of affected combinations; generic configurator work continues. |
| P-02 | Base/family/band/access/support rates, the five-plus-five allowance, €50 rate and each charge's annual/one-time basis | Keep placeholders/null live prices; independently approve component rate cards and tax categories. EUR is the draft display currency. | Payable offers and real quotes. |
| P-03 | R&D/RDP/perpetual permitted use, RDP expansion, annual start/expiry/renewal, perpetual production and production accounting | Specify unit, period, aggregation, reporting/upgrade rules and effects on existing deployments. | Sale of each affected licence term/production offer. |
| P-04 | Licence-manager host formats, fixed/floating server mechanism, non-Altera access, redundant servers and rehosting | Version a documented access profile per vendor/term; define host/family/node changes, fees and amended-key behavior; no universal MAC rule. | Host validation, payable licensed scope and key issuance. |
| P-05 | Support price/scope, sharing, time rounding/authorization, refund handling and response commitment | Preserve non-expiring 10-hour packages; use exact ledger units and explicitly assigned resource access. | Real support sales and chargeable time policy. |
| P-06 | Actual IP release, package/key production procedure, approved tool versions, delivery time and included update/maintenance/warranty rights | Manual tracked provisioning and protected downloads; archive artifacts before release. | Actual delivery and customer promises. |
| P-07 | Contracting seller/merchant, customer markets, bank, methods and collection/settlement capabilities | Qualify one hosted bank flow; EUR collection is intended, settlement remains a merchant fact. | Bank-specific integration proof and live acquiring. |
| P-08 | Approved IP/support/T&C/refund/privacy texts, seller and customer tax/invoice rules, purchaser/licensee differences, acceptance authority/timing and relevant end-use review | Version exact documents and line-type-aware checkout profiles, country-aware requirements and required declarations; define decline/refund/payment timing. Keep marketing optional. | Real collection/acceptance, tax documents and financial policies as applicable. |
| P-09 | Data/evidence retention, Object Lock mode/duration and key custody | Governance proposed; qualify storage behavior; protect host IDs and evidence under an approved lifecycle. | Production retained evidence and recovery readiness. |
| P-10 | OVH project/account quotation, B2 monthly availability/quota/image path, exact volume placement and budget | B2-7 monthly is the chosen planning fit subject to these checks and measured qualification; B3-8 hourly is a documented fallback. | Provisioned tests and monthly-billing conversion. |
| P-11 | Route 53 hosted-zone authority and exact approved customer/staff records; ACME reachability/CAA | Customer hostname is fixed at shop.xspi.pro; dedicated certificates proposed; staff name still to be confirmed. | DNS/certificate activation; local config generation continues. |
| P-12 | SMTP settings/credential, sender/sales mailbox, staff roles, support/fulfilment owners and recovery coverage | Use supplied addresses and narrowly scoped credentials; synthetic notifications first. | Real mail, staff production access and operating readiness. |

## Handover report and next action

Deliver reviewable code and configuration, the current catalog and source hash, the completed requirement matrix, task evidence, applicable dependency/licence inventory, operations and recovery runbooks, and the exact release/rollback instructions. Record all approved production values and all still-pending ones. List actual external changes only if they occurred within authorized scope.

If deployment is not yet authorized or an external prerequisite is unavailable, finish the authorized implementation and deployment preparation, identify the particular remaining operation and why it needs that input, and present the concrete result for review. Do not leave ordinary local work unfinished behind a general request for confirmation. If activation is authorized and all its prerequisites are satisfied, execute the scoped activation and report observed results without seeking duplicate permission.

A useful instruction to accompany these two files is:

> Implement the revised xSPI-MC shop proposal and its Codex handoff. Use shop.xspi.pro and the embedded product definition. Start with the repository review, then complete the authorized local implementation and deployment preparation. Keep the recorded commercial decisions pending where necessary and continue unaffected tasks. Present concrete cloud, DNS, certificate, email and live-payment changes for any authorization that is still missing before executing them.
