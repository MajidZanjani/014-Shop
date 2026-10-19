# Synaptic Laboratories IP shop — Codex implementation handoff

Prepared 19 October 2026. Companion to **SLL-IP-Shop-Proposal-2026-10-19.md**. This document specifies future implementation; it is not evidence that any application, infrastructure, payment, or acceptance test has been implemented or run.

## 1. Authorization and intended outcome

The present request is **proposal preparation only**. This handoff does not authorize provisioning, production deployment, DNS/WordPress changes, sending customer/staff email, submitting the existing Monday form, payments, refunds, or changes to existing services. When SLL gives Codex an implementation task using this document, Codex may perform the isolated local/development work actually authorized by that task. Obtain separately scoped authorization only for the real external operations that remain outside it. Do not manufacture repeated approval gates for routine reversible work already authorized.

Build one configurable semiconductor-IP shop with an entirely static Astro storefront, selected React islands, a small Django backend, a durable PostgreSQL business record, bank-hosted payment entry, browser administration, and protected manual IP fulfilment. Routine catalog edits must use ordinary Markdown/YAML, followed by validation, preview and publication. No unknown price, compatibility claim, licence right, certification claim, bank behavior or legal rule may be fabricated.

### Initial instruction to give Codex with an authorized implementation task

> Read this handoff and SLL-IP-Shop-Proposal-2026-10-19.md, inspect the authorized repository/workspace and its applicable instructions, and begin T01–T03 in an isolated development checkout. Preserve existing work and reuse the proposal's completed source audit; perform targeted checks only for a relevant change or missing evidence, rather than repeating the whole audit. Implement the dependency-ordered tasks that do not require missing business inputs, using clearly labelled synthetic fixtures and disabled live-payment settings. The initial valid but unapproved configuration outcome is `awaiting_review`. Record assumptions and unknowns once in the decision register; continue unaffected tasks without repeated clarification. Do not submit the Monday form, contact recipients, initiate payments/refunds, provision cloud resources, change DNS, modify WordPress, or touch existing production services unless the implementation task explicitly authorizes those actions. Before a separately authorized external action, prepare its concrete configuration, expected impact, rollback and relevant verification so the authorization covers a reviewable result. Complete each task with scoped evidence, then continue until all authorized work is done. Do not call fake-bank tests real-bank qualification or call an unexecuted deployment tested.

## 2. Baseline architecture and scope

| Area | Implementation baseline |
|---|---|
| Static frontend | Astro **7.4.0** and React/React DOM **19.3.1** as researched baselines; build-time Content Collections; ordinary `.md`; static output only. Reverify secure compatible patches when locking dependencies. No SSR, Astro API runtime, server islands, live collections or React Server Components. |
| Build/runtime | Node **24 LTS** for the frontend build; Python **3.13** + Django **5.2 LTS** + Gunicorn at backend runtime; PostgreSQL **18** and pgBackRest for backup/WAL archiving. Record exact patches, reproducible build hashes, licences and transitive notices. Never deploy an unbounded `latest`. |
| Admin/auth | Django admin augmented with workflow views and domain actions; mandatory TOTP plus offline recovery codes using maintained OSS packages (`django-two-factor-auth` / `django-otp` baseline). Customer guest access uses verified-email, resource-scoped server sessions. |
| Background work | One worker from the same backend build artifact; PostgreSQL outbox/job leases and deduplication. No Redis, Celery, external queue, CMS, identity service or analytics SaaS. |
| Compute | Assumed separate OVH Public Cloud B3-8 in **GRA11**, 2 vCPU/8 GB, fixed 50 GB local disk plus 50 GB High Speed data volume. Confirm stock, quota, new-VM installation path, account quote and authorization before provisioning. Existing NixOS host configuration is not permission to change that host. |
| Deployment model | Recommend **NixOS on the new VM**, with native hardened systemd services for Caddy, PostgreSQL, pgBackRest and unprivileged application/worker identities. The research OS baseline is **NixOS 26.05**, whose support ends **31 December 2026**; select a supported stable release at actual deployment and pin the exact nixpkgs revision/flake lock. Rootless Podman with Quadlet on an approved Linux distribution is an evaluated fallback, not a mandatory runtime. |
| Public origin | OVH S3-compatible Standard storage at region identifier **`gra`**; Caddy on the shop VM terminates public HTTPS and fetches static objects over the HTTPS object API. The website endpoint is a separate HTTP-only service and is not the chosen origin path. |
| Storage ACLs | Static bucket ACL remains private; only approved public static objects receive public-read ACL. Anonymous listing/write stays denied. Private commercial IP, invoices and recovery data use separate private buckets and credentials. Use OVH-supported user policies/ACLs; do not assume AWS bucket-policy parity. |
| Customer origin | Proposed `https://shop.synaptic-labs.com`, not yet created: customer `/api/` routes and Django's **`/inquiry/simple/`** fallback route to the backend; public static paths route to S3. Staff/admin routes return **404 on this host**. No permissive cross-origin API is required. Strip cookies, authorization and irrelevant customer query data before object-origin requests. |
| Staff origin | Proposed `https://shop-admin.synaptic-labs.com`, also not created: staff/admin routes only, served by the same VM/application with distinct host-only cookies and mandatory MFA. No additional VM or identity provider. Staff routes must not leak through customer-host aliases or static fallback. |
| Recovery | Encrypted off-instance/off-location backups in **`sbg`** through pgBackRest base backup + continuous WAL/PITR. Proposed DB RPO is 15 minutes; the technical restore target is four hours **after an operator starts recovery**, subject to a measured drill. Full end-to-end RTO also includes detection, response and financial clearance and needs the agreed operating coverage. Safe reopening may take longer if bank/required external services remain unavailable. Archive payment/capture/refund intents before bank calls and financial-document/delivery evidence before issue or activation. |
| Integrations | One eventually selected acquiring bank/gateway; existing Stalwart SMTP using supplied endpoint, approved sender, real sales recipient and scoped credential; existing DNS. Existing monitoring integration is separately scoped. |

The VM is the common HTTPS ingress: a VM/Caddy failure also makes the custom-domain storefront unavailable. Object Storage origin durability does not make the whole shop highly available. A Django failure can leave static browsing operational if the VM/proxy/storage remain healthy.

### Commercial behavior

- Launch one explicitly selected configurable product. Preserve the source form's information without making every listed SLL service launch merchandise.
- Provide discovery, configuration, trial inquiry, technical review, quote request, issued-quote payment, and direct purchase of specifically approved offers.
- Recommend one licence per explicitly scoped configured line, quantity fixed at 1. Manufacturing volumes are separate qualification data.
- Keep inquiries, quotes, orders, payment attempts/refunds/disputes, fulfilment tasks, and entitlements separate.
- Initial prices/compatibility rules/legal terms are unapproved. Use `awaiting_review` for syntactically valid requests whose eligibility is unknown; `quote_only` for an approved quote route; `unsupported` only under an explicit SLL-approved exclusion; `purchasable` only when all offer/price/currency/tax/terms/prerequisites pass.
- Manual licence/package provisioning is part of v1. Automated licence generation, recurring billing, subscriptions, exchange rates, complex discounts, team accounts, marketing analytics and full WordPress migration are excluded unless later scoped.

## 3. Source evidence to preserve

Reuse the dated audit in SLL-IP-Shop-Proposal-2026-10-19.md. When a targeted delta or unresolved observation needs checking, inspect these public sources without submission, real personal data or agreement acceptance:

- https://synaptic-labs.com/trial-ip-request/
- https://forms.monday.com/forms/embed/9ddd6f8c852b1c67107849bb1af1e1d3?r=use1

The completed proposal audit identifies **53 distinct fields across explored branches**, not proof that all possible combinations have been exhausted. Reuse its evidence-backed matrix, 16 option lists and country/phone table, preserving exact labels/order, type/cardinality, help, observed requiredness/defaults, validation uncertainty, conditional visibility and accessible source IDs. Recheck only changed or decision-relevant missing evidence. If the companion audit is unavailable, the URLs remain sufficient to recover the necessary read-only evidence. Preserve observed/inferred/unverified distinctions; missing evidence is not permission to invent it.

| Group | Baseline labels |
|---|---|
| Contact/company — 15 | First name; Last name; Job title; Email; Work mobile; Company - Name; Company - Website; Company - Address line 1; Company - Address line 2; Company - Address line 3; Company - Suburb; Company - Post code; Company - State / Region; Company - Country; Personal contact details. |
| Use/product — 4 | Use case environment; Multi select; Use case; SLL IP cores and services. |
| Memory — 12 | Memory device protocols; Memory device vendors; Memory device type; Other memory device support; Memory channel top clock speed; Other memory channel top clock speed; Memory device voltage; Memory device package; Memory product order code(s); Memory access use cases; Other memory access use case; Memory channel bandwidth. |
| Target — 8 | Project type; FPGA device family; Other FPGA device family; FPGA product order code; FPGA development board; ASIC process/foundry; FPGA device used for ASIC prototyping; FPGA board used for ASIC prototyping. |
| Schedule/production — 7 | R&D start date; Prototype date; Start production date; Start mass production date; First year production volume; Annual production volume; Number of years manufacturing. |
| Licensing/completion — 7 | Ownership; Other arrangement; IP licensing models; Other licensing model; Your questions:; SLL Trial IP usage; GDPR agreement. |

Known branch triggers: `01 - Memory controller IP's`; FPGA versus ASIC project; Other memory type; other clock speed; Other memory access use case; Other, please specify. FPGA family; Some other arrangement. ownership; 04 - Other? Please indicate. licensing. Match exact option text/IDs to the audited evidence.

Separate contact, configuration, qualification and consent. Preserve immutable source profile **`sll-trial-form-2026-10-19`**; use separate shop profile **`sll-shop-form-v1`** and change set **`sll-source-to-shop-v1`**, covering the proposal's **F-01–F-14**. Journey-specific requirements apply to configuration, inquiry qualification, evaluation and commercial checkout. The change set initially remains pending; previews/local implementation can proceed, while production compilation/import requires its recorded approval. Editing an `approved` frontmatter word alone must not create approval. Resolve profile choices once and continue routine implementation without repeated permission prompts.

Implement these proposed response/validation changes only as the reviewed shop profile specifies: F-06 allows the identified required schedule/production answers to be known or **Unknown — with reason**; F-07 allows ASIC-prototype device/board answers to be known, **Not applicable**, or **Unknown — with reason**; F-08 allows the FPGA-board answer to be known or unknown with reason. Encode response status separately from value/reason, never as fabricated dates, zero counts or dummy devices. F-09–F-11 define commercial legal-entity/billing and journey-specific agreement/privacy behavior; original trial requiredness must not silently become checkout policy.

F-12 deliberately changes observed hidden-state retention: clear newly inapplicable values with notice. F-13 proposes 500 Unicode characters for ordinary text, 2000 for the three multiline fields, and field-specific email/phone handling; exact limits and unusually long part-list treatment require profile approval. Preserve website and bandwidth as text. F-14 proposes nonnegative integer known production counts, finite positive decimal known manufacturing years, and valid ISO calendar dates. No chronology, future-only dates, business maximum, compatibility or price is inferred. State parser precision/length bounds in the schema. Safety selections remain customer requests; Ownership concerns the end product; trial and commercial acceptance stay distinct.

## 4. Work plan and effort

Planning assumptions: one engineer competent in the selected stack, one English product, one currency, manual provisioning, one documented hosted-checkout bank, prompt commercial review, no existing code to rescue and no major undocumented bank defects. Estimates include the scoped tests inside each task; do not add a second blanket QA allowance to these totals. They exclude merchant/legal waiting time, specialist legal work and optional new scope.

| Task | Work package | Depends on | Engineer-days |
|---|---|---|---:|
| T01 | Evidence, scope and decision register | Implementation instruction | 2–3 |
| T02 | Reproducible skeleton, contracts and isolation | T01 | 3–5 |
| T03 | Markdown compiler, schema and rule conformance | T01–T02 | 3–4 |
| T04 | Static storefront and configurable product journey | T03 | 4–6 |
| T05 | Database/API and durable inquiries | T02–T03 | 2–4 |
| T06 | Guest access, admin MFA and role enforcement | T05 | 3–5 |
| T07 | Quote/order/terms model and checkout authority | T03,T05–T06 | 3–5 |
| T08 | Outbox, payment domain and fault-injectable fake bank | T07 | 4–6 |
| T09 | Selected-bank sandbox adapter and reconciliation | T08 + bank inputs | 4–6 |
| T10 | Manual fulfilment, entitlement and finance workflows | T06–T08 | 3–5 |
| T11 | Caddy/object-origin publication and rollback | T02–T04 + cloud-test authorization for deployed proof | 2–4 |
| T12 | Backups, recovery mode, monitoring and restore drill | T08,T10–T11; T09 for bank proof | 3–5 |
| T13 | Integrated risk, accessibility and isolation acceptance | T04,T06–T12, with conditional bank/cloud evidence | 2–4 |
| T14 | Release readiness and separately authorized activation | Prior applicable tasks + activation decisions | 2–3 |
| **Total** | **Full one-product launch** | External waiting excluded | **40–65** |

T09 can run alongside T10/T11 once bank inputs arrive. T11/T12 can be prepared locally before any cloud action. A blocked bank or legal input must not stop unrelated implementation.

### T01 — Evidence, scope and decision register

**Outputs:** imported/reused proposal source-form matrix and branch observations; exact source options/IDs where accessible; a targeted delta/missing-evidence record; source and shop profiles with F-01–F-14 mapping; one decision register with owner and blocking phase; scope and preservation note.

**Acceptance:** reuse the completed 53-field audit and every retained inspected option/branch, preserving all 242 country/phone labels and ordering rather than generating a generic ISO list. Do not repeat a wholesale audit without a concrete change or evidence gap. Account for discrepancies without claiming invisible validation/requiredness was tested. Separate immutable source semantics from proposed/approved shop changes, including the deliberately changed hidden-state policy. No form submission or agreement acceptance occurs. Unknown live commercial values remain disabled and named.

**Evidence:** companion audit identity/hash and reused source evidence, any targeted dated observations/screenshots or permissible DOM evidence, source URLs, profile/change-set revisions and approval status, unresolved branch list. Do not save real personal data in fixtures.

### T02 — Reproducible skeleton, contracts and isolation

**Outputs:** frontend/backend/worker skeleton; pinned Python/Node dependencies and reproducible Nix/application build outputs; supported-release/nixpkgs/flake-lock plan for the new VM; licence/SBOM inventory; local PostgreSQL and synthetic mail/bank/storage fixtures; OpenAPI and shared catalog schema; CI commands; environment/secrets templates. OCI images/digests are needed only if the evaluated Podman fallback is selected.

Use `catalog/public/{products,fields,option-sets,legal}`, `catalog/private/{offers,approvals}`, `contracts/{catalog.schema.json,openapi.yaml,rule-conformance/}`, `storefront/`, `backend/`, `infra/`, `tests/{contract,payment-fixtures,e2e}` and `docs/runbooks/`. Keep the source/shop profile and change-set records within the versioned catalog authority, referenced by their stable IDs.

**Acceptance:** clean isolated build reproduces outputs from lockfiles; real credentials/customer data/IP are absent; production frontend needs no server-side Astro/Node runtime. The new-VM configuration defaults to hardened native systemd services and separate unprivileged identities; it does not require containers. No repository, service or optional container requires dedicated-host production state, credentials or service sockets. Runtime/migration/publisher/private-delivery/evidence/backup credentials are distinct in design. The deployment plan cannot silently retain an unsupported NixOS release when its date changes.

**Evidence:** dependency manifest and notices; build command/results; environment-boundary diagram; initial API/schema checks. Do not provision a VM to prove a local skeleton.

### T03 — Markdown compiler, schema and rule conformance

**Outputs:** one version-controlled Markdown catalog authority; immutable source profile, separate proposed/approved shop/journey profiles and protected approval/change-set records; public/private compiled immutable manifests; stable product/field/value IDs separate from labels; shared-list mechanism; complete JSON Schema and generated types; small Python/TypeScript interpreters for the same declarative rule data; conformance fixtures. The proposal's abbreviated schema fragment must be completed before production validation, including strict objects and cross-file integrity.

Use exactly the initial AST operators `all`, `any`, `not`, `selected`, `equals`, `in`, `is_present`; do not introduce `contains` as an alias or substring rule. `selected` checks a normalized selected-ID collection, with cardinality enforced separately; `equals` is strict scalar equality and `in` is scalar membership in an explicit literal list. No executable expressions/imports in content. Check identifier integrity, types, recursion depth/cycles, conflicting outcomes, approved parser/input bounds and missing/null semantics. Isolate visibility/requiredness from engineering compatibility and eligibility.

Represent responses as a strict tagged union: `known` carries a non-null field-validated value, `unknown` carries a nonblank bounded reason and no value, and `not_applicable` carries no value. Permit each alternative only on its approved fields and reject mixed payloads, undeclared properties and invalid alternatives. Preserve source required markers, absent HTML limits and unverified server behavior in the evidence profile; apply F-01–F-14 through the shop profile rather than rewriting history. Test F-13 Unicode counting/limits consistently in both runtimes, F-14 integer/decimal/date types, unknown reasons and unrelated-value preservation. Do not invent date chronology or production/business maximums.

Value predicates return `true`, `false` or `unknown`. For a tagged response, project `known.value` only after field validation; `unknown` and `not_applicable` supply no known scalar/selection value. Reject declared operand-type mismatches. Missing/unresolved values are not known mismatches, and `not unknown` remains unknown. `all` is false if any child is false and true only if all are true; `any` is true if any child is true and false only if all are false; other combinations remain unknown. `is_present` tests a fully validated response under the field profile, not arbitrary JSON existence; satisfying requiredness alone never establishes purchase eligibility. An offer matches only a definite true result. Visibility likewise opens a dependent branch only on true; unresolved prerequisites still appear as validation/review needs. Prove these rules, including negated unknown values and malformed tagged responses, in the shared conformance corpus.

**Acceptance:** representative nested rules evaluate identically on backend/browser; Markdown edits can alter product/help/options/approved public prices without component changes; a malformed catalog fails before publication. Pending/excerpt/test-only records cannot enter prohibited production modes. Shop-profile approval matches the protected approval record, not merely editable frontmatter. Unknown rules/prices never permit purchase. Public manifest selection is an explicit allowlist and excludes private approval/pricing data.

**Evidence:** sample product and shared-list Markdown, schema, valid/invalid compiler results, rule-conformance corpus/results and output hashes. Use labelled test-only prices/terms, with production activation disabled.

### T04 — Static storefront and configurable product journey

**Outputs:** discovery/docs pages; accessible React configurator; trial/quote/direct-purchase routes; cart/review view; static privacy/legal placeholders clearly unapproved; meaningful backend-offline/no-JavaScript messages; a link to Django's **`/inquiry/simple/`** fallback using the same approved profiles; human editing/preview instructions. The fallback is backend-rendered and does not add a request-time Astro runtime.

**Acceptance:** exact audited field choices/order/cardinality are preserved except for explicitly approved F-01–F-14 mappings; all approved conditional branches and response states work. The clear/reset policy is tested as **F-12's deliberate source-to-shop change**, not falsely reported as unchanged source parity. Preserve unrelated valid values after recoverable errors; show a notice when dependent values are discarded. Contact data is not repeated unnecessarily. Use the approved “Safety and certification requirements” label while retaining the source label/ID. No compatibility/certification claim is inferred from a selection.

Test every approved field/value and branch from the data-driven audit plus representative nested combinations; do not claim exhaustive testing of the cart's combinatorial cross-product. With JavaScript disabled, product information remains readable and `/inquiry/simple/` permits an accessible inquiry using server-rendered validation/branch steps. During a backend outage, describe that limitation accurately and preserve valid non-sensitive draft data; do not substitute an unconfirmed email address or leave a misleading Pay action.

**Evidence:** static output inspection, screenshots at representative mobile/desktop widths, keyboard path/error summary, branch/value coverage linked to audit rows and source revision.

### T05 — Database/API and durable inquiries

**Outputs:** migrations/models and API services for `Organization`, `Contact`, `CatalogRevision`, `Product`, `ProductRelease`, `ConfigurationSnapshot`, `Cart`/`CartLine` and `Inquiry`; source/shop-profile references; typed validation/eligibility responses; persisted notifications/outbox records; rate limits/spam controls; read-only snapshot admin; Django's `/inquiry/simple/` with the same profile-driven server validation.

**Acceptance:** the server recomputes validity/visibility from the referenced approved shop profile/catalog; rejects unknown IDs/stale hidden data or returns an explicit normalized draft for reconfirmation; does not quietly change licence scope. The React and simple backend form accept the same approved known/unknown/not-applicable states and apply the same limits. Persist inquiry and notification jobs before reporting acceptance. Mail failure retains the inquiry and reference. Customer input cannot inject HTML/SQL/mail headers or choose outbound recipient/From addresses.

**Evidence:** real-PostgreSQL API integration tests for transaction rollback, duplicates and validation; OpenAPI examples; record/outbox evidence with synthetic data. Use the supplied real sales destination only in a later authorized integration test.

### T06 — Guest access, admin MFA and role enforcement

**Outputs:** vetted token/session guest flow using `AccessGrant`; verified contact/order/quote permissions; Django workflow admin on **`shop-admin.synaptic-labs.com`**; enforced TOTP/recovery code enrolment; sales/technical/fulfilment/finance/admin permission groups; documented factor and contact-recovery procedures. Actual staff names and recovery custodians are supplied by SLL, not inferred.

**Acceptance:** secure HttpOnly host-only sessions, distinct customer/staff host boundaries, session rotation, explicit CSRF protection and no public cross-origin credential policy. Customer-host requests to staff/admin routes return **404**, including alternate paths; a staff hostname alone still grants no authorization. A GET email-link fetch cannot accept terms or consume the only verification opportunity. Challenges are single-use/expiring/rate-limited. Order IDs, email knowledge and company email domains do not grant unrelated resource access.

Use `AdminSiteOTPRequired` or its documented equivalent; the default login patch alone is insufficient. Enforce verified sessions on every custom admin view, remove alternate plain-login bypasses, and test direct endpoint calls. Spare factors/offline codes and a documented operator procedure support recovery during an email/shop outage. Recovery revokes sessions and is audited.

**Evidence:** cross-customer/role/MFA-bypass integration tests, factor-loss recovery rehearsal, cookie/CSRF checks, sanitized screenshots. Routine admin actions require no DB/source edits.

### T07 — Quote/order/terms model and checkout authority

**Outputs:** immutable imported `ApprovedOffer`/`PriceVersion` records; staff draft/approve/issue/supersede quote screens; `Quote`, immutable `QuoteRevision`/`QuoteLine`, customer review/accept/pay, `Order`/`OrderLine` snapshots, `TermsVersion`/`AgreementAcceptance`, exact money/tax interfaces, `BillingDocument`/`DocumentNumberReservation` with immutable number/version identity, and `IdempotencyRecord`. Integrated payment of an approved quote is the recommended v1 behavior; manual negotiation may precede it without creating another payment model.

**Acceptance:** quote `/accept` owns the single acceptance event and returns its `acceptance_id` with a session-bound capability. `/payment-attempts` consumes that existing acceptance/capability and verifies the exact reviewed quote revision; it does not create a second acceptance. A database uniqueness constraint maps one accepted quote revision to at most one order across sessions and idempotency keys. Customer edits cannot alter its price/scope. Freeze catalog/product release/configuration/organization/quantity meaning, price/currency/tax, expiry and exact terms bundle. Record accepting person/verified identity, licensed organization, authority attestation and server time. A terms file without an acceptance event is insufficient.

Server money calculation rejects browser price tampering and unsupported precision/currency. Unknown tax treatment/price or unapproved terms prevent paid checkout. Quantity stays 1 per licence line. Distinguish trial acceptance from commercial rights. Quote acceptance and conversion check recorded quote validity; conversion freezes a separate `payment_start_deadline` on the unique order under the approved policy. The bank checkout-session expiry is another recorded limit. Preserve late-money exceptions without silently repricing accepted scope. Quote `/payment-attempts`, cart `/checkout` and order `/payment-attempts` all call the same guarded domain service.

**Evidence:** concurrent quote conversion across sessions/keys, one-acceptance/one-order assertions, immutable snapshot tests, stale-catalog/expired-quote/price-tampering scenarios, acceptance record and specimen synthetic invoice/receipt. Final financial-document issuance is subject to T10's archive-before-issue protection. Real contract/tax content remains an activation input.

### T08 — Outbox, payment domain and fake bank

**Outputs:** leased PostgreSQL worker; retry/dead-letter/admin jobs view; `PaymentAttempt`, `ProviderTransaction`, `PaymentEvent`, separate `Refund` and `Dispute` records; bank-adapter capability and typed create/callback contracts; fake bank with controlled faults; `ArchiveEvidenceRef` and archive-before-operation services. Each archive reference records namespace/key/object version, content hash, encryption/key-recovery reference, retention evidence, explicit `prepared`/`completed` phase and verified acknowledgement, with the actual recoverable snapshot bundle stored privately. Prepared evidence proves intent and preserves identity; completion must be recorded and reconciled separately.

**Acceptance:** DB changes and outgoing work commit atomically; `transaction.on_commit()` alone is not the durable queue. Claim short leases, do network I/O outside long transactions, recover abandoned jobs and make economic effects idempotent. No separate queue service is added.

Persist attempt/reference/idempotency key, then archive and verify the recoverable order/acceptance/attempt bundle before the payment-creation call. Likewise archive capture/refund operation intents before their bank calls. Store a verified `ArchiveEvidenceRef`; a digest without the snapshot contents is insufficient. Use deterministic operation identity and conditional archival writes, with retention/bypass permissions checked in the selected environment. Archive failures leave preparation pending and make **no bank call**. Only an operation that may have reached the bank can become **uncertain**; its outcome is not failure and cannot justify a second attempt. Browser return cannot mark paid. Duplicate/out-of-order events and multiple successes cannot grant duplicate licences. SMTP ambiguity can repeat email; document that boundary.

After archival and immediately before dispatch, lock the order and recheck current cancellation, the frozen `payment_start_deadline`, live activation and required approval state, including when preparation was queued. Confirm that quote acceptance/conversion already passed their recorded validity checks. Claim one dispatch operation under that lock, then release the transaction before network I/O. Resolve concurrent cancellation against the recorded in-flight operation without erasing payment history; an old archived approval is not an indefinite right to charge. Report expired eligibility as a reviewable conflict and preserve any late-money exception.

**Evidence:** fake-bank scenarios for wrong merchant/amount/currency/reference, forged success return, duplicate/reordered/lost callbacks, authorization versus capture, archive failure before a call, cancellation/expiry/deactivation during archive wait, concurrent cancellation/dispatch, timeout after provider acceptance, worker crashes and double clicks. Check row counts, archived contents/references and state/evidence, not only HTTP statuses. A known-reference unauthenticated callback hint may trigger a documented status lookup; it cannot itself confirm money.

### T09 — Selected-bank sandbox adapter and reconciliation

**Inputs that block only this task's real adapter:** selected bank/acquirer, merchant/sandbox configuration and credentials, supported methods/currencies, current API documentation, callback authentication/key handling, idempotency/reference semantics, status and transaction/statement access, refund/dispute flow and rate limits.

**Outputs:** exact selected-bank adapter implementing the proposal's method/result contracts; documented source-to-internal state map; credential/key rotation configuration; replay-safe callback handler; polling/reconciliation; audited transaction/statement import fallback when the bank has no suitable list API. Keep manual bank-transfer credit matching separate from the hosted-card adapter and its refund/dispute events if transfers are enabled.

**Acceptance:** implement the bank's actual algorithm against its documented raw-body/canonicalization rules; do not assume HMAC or fabricate event identifiers/freshness rules. Distinguish authenticated events, notification-only hints and rejected callbacks. Authenticated status checks match stored attempt/order, merchant context, provider reference, amount and currency; unreported financial details remain unknown rather than zero. Bank checkout URLs use approved HTTPS hosts. Creation/capture/refund retries are safe only where documented, and each relevant outgoing intent must have its verified archived evidence before the call. Unverifiable outcomes appear in finance queues.

Prove success/failure/cancellation, callback loss/reordering, return before confirmation, wrong data, duplicate success and ambiguous requests in the real sandbox where supported. Report unsupported simulations honestly. Reconciliation must discover bank transactions absent from the local DB, using an available statement/export path if necessary.

**Evidence:** redacted requests/responses, documented verification fixtures, sandbox transaction references/results, bank source URLs/date, mapping and capability checklist. No real charge or customer notification is authorized by sandbox evidence.

### T10 — Manual fulfilment, entitlement and finance workflows

**Outputs:** `FulfilmentTask`, `Artifact`, `Entitlement`, `DownloadGrant`, private `BillingDocument` versions and their `ArchiveEvidenceRef` records; tracked technical/contract approvals; manual package upload/release screens; finance reconciliation/refund/hold actions and audit timeline.

**Acceptance:** payment alone releases no file if another required prerequisite is missing. Staff can assign/prepare/release a package through the browser with named actions; database uniqueness prevents duplicate grants. **Before issuing a financial document**, archive its number reservation and immutable number/version/content. **Before activating delivery**, archive the release/entitlement-grant manifest and copy its private artefacts off-region; verify corresponding archive references before release. Distinguish this durable licence/delivery grant from each later ephemeral download URL. Archival failure waits without issuing/activating the side effect. Private object access requires an authorized session and entitlement. S3 presigned URLs are short-lived bearer grants, not promised single-use or instantly revocable links; full URLs never enter normal logs. Private artifact/document responses use `Cache-Control: private, no-store`, correct MIME and safe attachment filenames; validate download expiry/resume behavior on OVH.

Separate licence validity, support entitlement, update releases and future download access. Apply only SLL-approved refund/dispute policy; do not pretend revocation recovers downloaded files. Refund actions have permission/recent-authentication/reason checks, supported bank semantics and a durable uncertainty state. Invoice legal/tax fields remain pending until approved.

**Evidence:** A-versus-B access tests for orders/quotes/invoices/artefacts; expired URL behavior in authorized object-store tests; duplicate-release and archive-before-issue/activation tests; archived document identities, delivery manifests and off-region artefact-integrity checks; synthetic fulfilment/refund timeline. “Delivered” records the approved release/notification step, not proof of human reading; download-grant issuance is separate. Use dummy files, never confidential IP for public tests.

### T11 — Caddy/object-origin publication and rollback

**Outputs:** a declarative **new-VM NixOS** configuration using supported stable NixOS and a pinned nixpkgs/flake lock; native hardened systemd units for Caddy, PostgreSQL, pgBackRest and separate unprivileged app/worker services; object/publisher/private-delivery/evidence/backup permissions; generated route manifest; staged static-release uploader; proxy-config switch and rollback runbook. Document the evaluated rootless Podman/Quadlet fallback on an approved Linux distribution without making it a required layer. Prepare locally before any necessary cloud-test authorization.

**Acceptance on the actual authorized test deployment:** Caddy's upstream TLS Host/SNI is the configured `bucket.s3.gra.io.cloud.ovh.net`, with verification enabled; no plaintext website-origin hop. Customer `/api/` and `/inquiry/simple/` routes reach Django and never fall back to S3. Customer-host staff/admin routes return **404**; staff routes are exposed only on `shop-admin.synaptic-labs.com`, with host/CSRF/MFA checks and no static fallback. Public object GET works while anonymous bucket listing/write and all private data reads fail. Scope non-owner credentials and test forbidden cross-bucket operations under OVH semantics. Verify the actual service-user, filesystem/network restrictions and supported OS release; no new service uses existing dedicated-host credentials or management sockets.

Prove `/`, nested pages, genuine 308 canonical redirects, genuine 404s, correct MIME, GET/HEAD, conditional caching and compression. Manifest-listed missing/denied origin objects produce an operational error, not misleading 404/200. Reject traversal/malformed paths. Upload immutable release prefixes, validate completeness, then switch one route manifest; an interrupted upload or invalid proxy config cannot partially replace the live release. Retain old assets for cached pages/rollback.

**Evidence:** effective config with secrets removed, ACL positive/negative tests, actual HTTP transcripts, interrupted-publication and rollback demonstration. Public staging objects contain only synthetic/public content; random paths/noindex do not protect secrets. Confirm new-resource boundaries and no existing service changes.

### T12 — Backups, recovery mode and operating procedures

**Outputs:** pgBackRest-managed PostgreSQL base backups and continuous WAL archiving to a private SBG repository; separate configuration/key/artefact recovery; protected evidence archive for agreement/payment/capture/refund intents, financial-document number reservations/versions and delivery-grant manifests; recovery mode; admin reconciliation reports; incident/restore/runbooks; alert definitions for failed/unknown payments, dead jobs/mail, overdue fulfilment, certificates, backup age and capacity. WAL alarms track the age of the oldest outstanding WAL requiring archival and activity/failure/backlog evidence; time since the last successful archive alone must not alarm on an idle database. Keep the mutable backup repository separate from the evidence bucket's approved Object Lock/retention rules.

**Acceptance:** demonstrate complete isolated recovery against the proposed 15-minute DB RPO and four-hour technical restore target **after an operator starts recovery**. Report end-to-end outage/RTO including detection, staff response and financial clearance. Report actual safe reopening separately if the bank or another required external service delays it. **Before exposing the restored database to application/worker traffic**, establish recovery mode, stop ordinary workers and block mutating bank calls and SMTP; permit controlled read-only bank reconciliation separately. Prove those controls hold even when the restored database contains runnable old jobs. A dump or storage versioning alone does not establish PITR/geographic backup. Restore private artefact versions and independently recover credentials/keys; invalidate restored login sessions/challenges. Use a separate recovery/WAL archive namespace, and suppress real email, charging, refunds and fulfilment during rehearsal.

Create a payment and capture/refund intent, reserve/issue a financial document and activate a delivery after the chosen DB recovery point; restore the older DB. Reconcile the **complete bank transaction/statement window**, including transactions absent from local/archived attempt indexes and older unresolved attempts. Compare archived operation intents with actual bank outcomes before any retries. Recover exact acceptance/order snapshots and archived document number reservations/version identities; reconstruct numbering high-water marks before any new issuance so PITR cannot reuse a reserved or issued identity. Never fabricate historical agreement acceptance. Recover delivery/entitlement manifests and off-region artefact copies before replaying licence work, and preserve policy-driven holds/revocations. Find orphan/duplicate successes and already completed refunds; hold missing-contract or ambiguous cases. Keep charging, financial-document issuance, delivery activation and downloads paused until the relevant reconciliation succeeds. Use fake bank locally, then actual selected-bank sandbox/statement evidence.

Exercise both `prepared` and `completed` archive records. A prepared-only invoice or delivery manifest does not prove issuance or delivery; inspect completion evidence and safely finish or hold the same deterministic document/grant identity. Reserved financial-document numbers stay reserved even when issuance is uncertain. Never create a replacement number or grant merely because an acknowledgement or post-effect database update is missing.

**Evidence:** backup chain/age and activity-aware WAL metrics, idle-versus-backlogged archive alarm checks, proof that recovery controls precede restored-DB exposure, restore start/ready/reopen timestamps and hashes, complete bank-window evidence, recovered operation/document/delivery archive references, reconstructed number reservations/high-water marks, exception report, no-duplicate-payment/refund/document/licence assertions, and runbook execution record. Any off-instance WORM/retention claim must have tested selected-region/product/mode/bypass-permission evidence; ordinary data hashes alone are not immutability. Recovery enumerates retained versions instead of treating a delete marker as loss of protected evidence.

### T13 — Integrated acceptance focused on remaining risks

**Outputs:** one coherent release-candidate acceptance report; targeted fixes; accessible customer/staff journey review; security/data-exposure and production-isolation evidence.

**Acceptance:** run representative end-to-end journeys across actual component boundaries: inquiry with mail outage; quote acceptance/payment/manual delivery; direct purchase with a test-only approved offer; preparing versus uncertain payment; financial/worker/archive failure recovery; cross-customer/private-file denial; approved refund/dispute policy; catalog/publication rollback. Exercise mobile/keyboard and no-JavaScript `/inquiry/simple/`, approved known/unknown/not-applicable validation, F-12 reset notices, real redirects/404s including staff routes on the customer host, backend-offline behavior and modest representative load.

Scan static output/source maps/bundles and public objects for secrets, customer fixtures and private material; inspect sensitive logs for session/token/payment leakage. Use distinct data-driven source-fidelity and approved-shop-change coverage, including F-01–F-14 and the 242 country/phone entries, not repetitive manual audit clicks or claims that a proposed change was observed source behavior. Tests already proven inside a task need rerun only for changed code/dependencies or a concrete integration risk. Clearly label untested real-bank/cloud cases as pending.

**Evidence:** commands/versions and selected results, screenshots, coverage-to-requirement map, sanitized security findings and closure, residual limitations, no changes to existing production-service boundary.

### T14 — Readiness and separately authorized activation

**Outputs before external authorization:** exact release commit/digests/manifests and supported NixOS/nixpkgs lock; data migrations; final scoped cloud/DNS/cutover plan for the separate customer/staff hostnames; rollback; complete restore/reconciliation/archive evidence; approved source-to-shop profile/change set and offer/licence/tax/terms configuration; SLL-supplied operators/recovery custodians; current OVH quote and merchant/PCI requirements; real email destinations supplied; consolidated unresolved items.

**Acceptance:** reused source audit, approved shop profile/change-set and critical workflow proofs are complete or explicitly blocked. Live payments cannot be enabled with fake adapter/test prices/unapproved commercial terms or unverified required archives. Issued-document and activated-delivery evidence is recoverable off-region. Acquirer confirms relevant merchant assessment/scanning requirements; required external costs are not assumed zero. OS support status at deployment, RPO/RTO start condition, bank-dependent reopening limits and VM availability coupling are acknowledged.

After the separate production instruction supplies authorization, execute only its approved resource/DNS/service scope, monitor the cutover, and provide concrete rollback readiness. Changing the old `/trial-ip-request/` page or WordPress redirects is a separately identified action. A controlled real payment/refund test needs explicit authorization for that transaction and amount; sandbox approval is insufficient. If production is not authorized, deliver a reviewable release candidate and continue any unaffected authorized work rather than marking production complete.

**Evidence:** release record, authorized action scope, deployment/HTTP checks actually executed, monitoring observations and remaining limitations. A website rollback changes static/application presentation as designed; never restore an old DB to undo a website edit.

## 5. Test boundaries

| Layer | Purpose | Boundary |
|---|---|---|
| Unit/contract | Catalog parsing, source/shop-profile distinction, tagged answers/three-valued rule parity, exact money, legal state transitions and risky input/schema edges | Fast synthetic data. Avoid tests that merely repeat trivial implementation lines. |
| Database integration | Transactions, row locks/races, uniqueness, outbox lease recovery, permissions and session/entitlement authorization | Use real PostgreSQL 18, not SQLite approximations of locking/constraints. |
| Adapter integration | Bank raw-body verification, status mapping, authentication, idempotency and ambiguous network behavior | Fake bank for fault injection; real selected-bank sandbox proves its protocol. |
| Deployed HTTP/storage | Native service privileges, OVH ACLs, Host/SNI, HTTPS, customer/staff boundaries, routes, cache/MIME, interrupted releases and private downloads | Requires the actual authorized OVH test deployment; local S3 mocks do not prove OVH semantics. |
| End-to-end | A small set of complete customer/admin recovery journeys and accessibility | One integrated release-candidate pass, then focused regression for fixes. |
| Recovery | Controls before DB exposure, data/key/artefact recovery, archived operation/document/grant reconstruction and complete bank reconciliation | Isolated restoration with deliberately divergent fake/sandbox records; measure operator-start-to-ready and safe-reopen separately. Never destructive testing of production. |

## 6. Evidence and completion report

Maintain `docs/decisions.md`, `docs/implementation-status.md` and one concise `docs/evidence/Txx.md` per task. Do not put secrets, full access URLs, raw card payloads, real customer data or confidential IP into evidence/Git. Record:

```text
Task: Txx
Status: completed | in progress | blocked | conditional external phase
Commit / artifact digests:
Companion / source profile / shop profile / change-set revision and approval:
Outputs:
Acceptance criteria satisfied:
Commands/tests actually run and relevant results:
Evidence paths / sanitized screenshots or protocol fixtures:
Relevant archive references / OS and runtime lock / deployed host boundaries:
Assumptions and limitations:
Unresolved decision, owner and affected phase:
External actions taken and authorizing instruction (if any):
Next unblocked dependency:
```

The final implementation report must identify **SLL-IP-Shop-Proposal-2026-10-19.md**, the retained source profile and approved shop/change-set revisions, what changed and why, and what was tested in each real environment. Include the exact release/rollback and supported OS/runtime lock, customer/staff hostname boundaries, SLL-supplied operator/recovery owners, relevant archived intent/document/delivery references, measured RPO and operator-start/ready/safe-reopen timestamps, untested bank/cloud behavior, running resource boundary and unresolved activation decisions. Do not claim proposal, compilation, mock, sandbox and production evidence are equivalent. Do not ask the user to approve incomplete internal preparation; produce the concrete authorized work first.

## 7. Decisions that may remain open while local work proceeds

| Input | Owner | Blocks |
|---|---|---|
| Actual seller/merchant entity, target markets, bank and supported currencies/methods | SLL finance/commercial + acquiring bank | Real-bank adapter details, tax/invoice policy, live merchant activation |
| Approved shop profile and F-01–F-14 source-to-shop change set | SLL engineering/commercial and applicable policy owner | Production compilation/import of those changes; synthetic previews and local implementation continue |
| Launch IP offer, licence scope/deliverables/support, approved compatibility/pricing | SLL engineering/commercial | Purchasable offers and real provisioning; not generic catalog/configurator work |
| Trial/commercial/NDA text, acceptance authority, refund/dispute policy | SLL commercial/legal | Respective real trial/paid release and live financial actions |
| Actual sales address, SMTP settings and sender | Email administrator | Real notifications; synthetic local mail tests continue |
| Staff roles, recovery custodians, fulfilment target and retention | SLL operations/commercial | Production admin/data lifecycle readiness |
| OVH project/new-VM installation/quote/quota, supported OS and customer/staff DNS/resource scope | SLL infrastructure owner | Provisioned testing/production; NixOS configuration and evaluated fallback can be prepared locally |
| Recovery objective, named operator/custodian coverage and bank reconciliation access | SLL operations + finance | Final acceptance of resilience, four-hour target after operator start and external-service-dependent safe reopening |

Residence in Georgia does not determine any seller, acquiring, tax, privacy, export or settlement obligation. Determine applicable policy only from the actual entity/products/markets. Ask for missing business facts once at the phase that needs them; do not block unrelated engineering.

## 8. Primary references for implementation checks

Research baselines can change; verify current compatible security patches and exact installed artifact licences during T02. The following are source facts supporting the design, not a substitute for deployed tests:

- [Astro Content Collections](https://docs.astro.build/en/guides/content-collections/) and [islands](https://docs.astro.build/en/concepts/islands/) — selected build-time and client-island boundary.
- [Django 5.2 administration](https://docs.djangoproject.com/en/5.2/ref/contrib/admin/) and [transactions](https://docs.djangoproject.com/en/5.2/topics/db/transactions/) — admin extension and transaction behavior; `on_commit` does not replace durable work records.
- [django-two-factor-auth enforcement](https://django-two-factor-auth.readthedocs.io/en/1.18.1/implementing.html) — mandatory OTP enforcement on the admin site.
- [PostgreSQL locking](https://www.postgresql.org/docs/18/sql-select.html) and [PITR](https://www.postgresql.org/docs/18/continuous-archiving.html) — queue-like row claims and base/WAL recovery.
- [pgBackRest user guide](https://pgbackrest.org/user-guide.html) and [configuration](https://pgbackrest.org/configuration.html) — actual backup, archive and isolated recovery configuration; verify the pinned release.
- [OVH website endpoint](https://docs.ovhcloud.com/en/guides/storage-and-backup/object-storage/s3-website), [HTTPS example](https://docs.ovhcloud.com/en/guides/storage-and-backup/object-storage/s3-website-https), [IAM](https://docs.ovhcloud.com/en/guides/storage-and-backup/object-storage/s3-identity-and-access-management), and [object sharing](https://docs.ovhcloud.com/en/guides/storage-and-backup/object-storage/s3-share-object-externally) — endpoint distinction and actual permission mechanisms.
- [Caddy reverse proxy](https://caddyserver.com/docs/caddyfile/directives/reverse_proxy) and [configuration API](https://caddyserver.com/docs/api) — upstream HTTPS handling and whole-configuration loading; test the generated routing policy.
- [PCI FAQ 1439](https://www.pcisecuritystandards.org/faqs/1439/) and [FAQ 1604](https://www.pcisecuritystandards.org/faqs/1604/) — redirect integrity and remaining SAQ A/ASV obligations; actual merchant requirements need acquirer confirmation.
- [OWASP payment integration](https://cheatsheetseries.owasp.org/cheatsheets/Third_Party_Payment_Gateway_Integration_Cheat_Sheet.html), [authorization](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html), and [MFA](https://cheatsheetseries.owasp.org/cheatsheets/Multifactor_Authentication_Cheat_Sheet.html) — server verification, resource checks and recovery considerations.
