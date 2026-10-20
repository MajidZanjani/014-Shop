# SLL xSPI-MC Shop

## What This Is

A configurable xSPI-MC semiconductor-IP shop at `shop.xspi.pro` for engineering and business purchasers. Customers configure separate vendor-specific licence lines, request reviewed quotes or buy approved offers, and purchase non-expiring ten-hour support packages independently or with IP. Staff use MFA-protected workflows to review acceptance/payment, issue matching private packages and keys, process renewal/rehosting cases, and account for support work.

## Core Value

Turn an exact reviewed xSPI-MC configuration or support purchase into attributable acceptance, verified payment and recoverable licence delivery or support credit without duplicate effects.

## Business Context

- **Customer:** Business/professional engineering purchasers and their explicitly authorized purchasing, invoice and technical contacts.
- **Revenue model:** Reviewed annual/perpetual IP licence scopes plus separately purchased ten-hour support packages; hosted payments of approved direct or quoted orders.
- **Success metric:** Verified end-to-end purchase/delivery and support usage journeys with reconstructable evidence and no duplicate financial, licence or ledger effects; no sales target supplied.
- **Strategy notes:** October 20 proposal and handoff, identified in SOURCES.md; P-01–P-12 remain commercial/operating inputs.

## Requirements

### Validated

None. No application or deployed system exists in this checkout; source verification is documentation evidence only.

### Active

- [ ] Preserve the exact source and complete option/field/declaration traceability.
- [ ] Compile strict, immutable Markdown catalogs with matching browser/backend rules and approval gates.
- [ ] Provide accessible static configuration, private host editing, multi-line quotes and line-type-aware checkout.
- [ ] Preserve exact acceptance, totals and payment identities across retries, races and crashes.
- [ ] Deliver approved encrypted RTL/manual/reference design/key packages through private resource grants.
- [ ] Sell support-only top-ups and account for non-expiring credits, reservations, work and statements durably.
- [ ] Prepare isolated publication, DNS/TLS, backup, restore and operational handover with honest external gates.

Detailed testable scope and phase mapping: REQUIREMENTS.md and ROADMAP.md. Original handoff acceptance remains normative.

### Out of Scope

Automatic recurring debits, a general organization-account portal, automatic proprietary key generation, FPGA synthesis/build services, broad marketing campaigns, website migration, and changes to existing production services are excluded by the new source. No additional products, vendors, invented trial form or country/tax options are imported from earlier plans.

## Context

Replanned from the two October 20 files at the user's explicit request on 2026-10-20. All prior active planning and the old decision register were replaced; no earlier task number implies completion. The exact embedded product bytes were extracted and hash-verified. The source specifies 13 logical configuration controls, 19 business-checkout groups, two convenience helpers, four IP declarations and a separate optional marketing control. It is a working draft, not a live-form audit. Pricing/schema/API examples are illustrative and require complete validation before implementation.

Retain the existing authorized workflow preferences (autonomous planning, fine granularity, independent parallel work, documentation commits/sync and current-model inheritance). This planning pass is performed inline. Use supplied research as dated input; exact dependencies, tariffs, account capabilities and legal/merchant facts are verified at their affected phases. No live external audit or application tests are claimed.

## Constraints

- **Architecture:** Static Astro Content Collections + selected React islands; Django LTS/Gunicorn + PostgreSQL and one leased database outbox worker; Django owns `/purchase/simple/`. No request-time Astro/Node service or mandatory Redis/Celery/CMS/IdP.
- **Authority:** `SLL_xSPI_MC_Product_Page.md` embedded in the October 20 proposal is the sole product-definition source. One Markdown/YAML catalog compiles immutable public/private revisions; protected approvals govern offers. Admin cannot create a competing catalog.
- **Product:** `sll-xspi-mc`, `sll-xspi-mc-support-10h`, profile `sll-xspi-mc-v1`; exactly three vendors and thirteen ordered families. One vendor and quantity one per configured IP line; support has real positive package quantity.
- **Rights and money:** RDP is Altera-only; higher volume requires quotation. EUR is draft display/collection intent. Unknown rates, recurrence, coverage, rights, access or terms remain null/pending and disable affected live offers. Five-plus-five allowances and €50 are provisional; no universal MAC rule.
- **Private data:** Encrypt/version host bindings, mask ordinary summaries, and authorize each resource. Keep raw host IDs/keys, business/tax details and bearer links out of public artifacts, URLs, ordinary logs and browser persistence. Staff MFA covers every privileged route.
- **Durability:** Archive recoverable snapshots before bank dispatch, document issue, delivery activation, support-credit spendability and chargeable work; archive actual support completion before final statement publication. Prepared evidence is not completion. An uncertain bank operation cannot authorize a blind retry.
- **Support:** Each paid/accepted package grants exactly 36,000 integer seconds once with no expiry. Reservations prevent competing spend; corrections reverse/replace; statements use committed ledger revisions. Support never renews IP rights.
- **Infrastructure:** New isolated OVH B2-7 GRA11 monthly after quote/image/workload qualification; B3-8 hourly fallback. Native hardened NixOS/systemd preferred; one approved Podman alternative if necessary. Separate 50 GB DB volume, `gra` public/private objects and `sbg` recovery/evidence with distinct credentials.
- **Domains:** Customer `https://shop.xspi.pro`; proposed staff `https://shop-admin.xspi.pro`; Route 53 `xspi.pro` authority unverified. Dedicated new certificate/key per hostname, explicit Let's Encrypt, HTTP-01/TLS-ALPN-01 first; conditional tightly scoped DNS-01 only if needed. Existing services/keys/DNS outside scope.
- **Recovery:** Proposed five-minute WAL archive timeout, 35-day DB recovery window, 15-minute DB RPO and four-hour technical restore after operator start. Measure full safe reopening separately. Block effects before restored service exposure; invalidate sessions/challenges, reconcile revocations and consumed MFA codes before access.
- **Evidence:** Real PostgreSQL for concurrency; label local/synthetic, selected-bank sandbox, actual OVH and production evidence separately. No invented approvals, compatibility, legal or provider guarantees.
- **Authorization:** This reset authorizes reading and replacing planning/documentation only. Application implementation, cloud spending/billing, DNS/TLS issuance, real mail, bank operations and production cutover require their applicable scope.
- **Estimates:** Supplied 46–74 engineer-days excludes external waiting and ongoing operations. Supplied modeled production £27.20/month ex VAT, £29.24 with temporary staging or £38.76 with permanent staging excludes DNS and other stated costs; these are unverified account estimates, not current quotes.

## Key Decisions

| Decision | Rationale | Outcome |
|---|---|---|
| Replace the complete planning baseline from the October 20 pair | Explicit user request; new product authority supersedes old inputs | Completed documentation reset |
| Preserve new T01–T14 as the phase/dependency structure | Direct acceptance/evidence traceability to the supplied implementation plan | Planning baseline; no execution credited |
| Keep support separate from IP rights and quantities | Non-expiring support purchases and fixed-term IP have different effects | Required source contract |
| Keep P-01–P-12 pending until evidenced approval | Source proposals cannot approve themselves | Affected live operations gated |
| Complete unaffected preparation while external inputs wait | Bank/cloud/policy gaps have specific scopes | Required workflow policy |

## Evolution

At phase transitions update validated/active scope and decisions from actual evidence. At milestones review core value, business context and exclusions. Preserve historical acceptance, source revisions and approval records; revise future offers explicitly.

---
*Last updated: 2026-10-20 after complete source-based replanning.*
