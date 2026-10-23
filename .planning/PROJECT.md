# SLL xSPI-MC Shop

## What This Is

A configurable xSPI-MC semiconductor-IP shop at `shop.xspi.pro` for engineering and business purchasers. Customers configure separate vendor-specific licence lines, request reviewed quotes or buy approved offers, and purchase non-expiring ten-hour support packages independently or with IP. Staff use MFA-protected workflows to review acceptance/payment, issue matching private packages and keys, process renewal/rehosting cases, and account for support work.

## Current implementation status — 2026-10-23

**Current development focus: Phase7**, implemented in local/synthetic slices with full acceptance pending. **Last fully completed phase: Phase1**. Phases2–6 remain partial or awaiting qualification; independent Phase7 work follows the October22 amendment. Total1/14 (rounded7%),10/20 planned records, Phase02 remains8/18. See [STATE.md](STATE.md) and [ROADMAP.md](ROADMAP.md) for current evidence, next action and unchanged release gates. Country/tax answers are being prepared by the user; no choices/rates are approved. Local audit is complete; newest supported-route journey evidence is149 core-local tests. Next: implement a Django no-JavaScript customer access entry using the existing local captured-verification flow, without real mail or new membership scope.

Before **every commit**, check all planning files for affected live status references, update them together, regenerate canonical state.json and run `python3 scripts/check_planning.py`. Preserve immutable sources and dated evidence; do not relabel partial local implementation as phase acceptance. Sync every commit to configured origin/main without force. This later user instruction supersedes the amendment's narrower status-maintenance convention.

## Core Value

Turn an exact reviewed xSPI-MC configuration or support purchase into attributable acceptance, verified payment and recoverable licence delivery or support credit without duplicate effects.

## Business Context

- **Customer:** Business/professional engineering purchasers and their explicitly authorized purchasing, invoice and technical contacts.
- **Revenue model:** Reviewed annual/perpetual IP licence scopes plus separately purchased ten-hour support packages; hosted payments of approved direct or quoted orders.
- **Success metric:** Verified end-to-end purchase/delivery and support usage journeys with reconstructable evidence and no duplicate financial, licence or ledger effects; no sales target supplied.
- **Strategy notes:** October 21 proposal and handoff, identified in SOURCES.md; P-10 hosting direction is selected, with qualification and other commercial/operating inputs pending.

## Requirements

### Validated

- ✓ Exact source preservation and complete option/field/declaration traceability — Phase 1, automated checks and four explicit human review responses. This validates documentation only; no application or deployed system acceptance is claimed.

### Active

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

Replanned on 2026-10-21 from the complete protected-services proposal/handoff. The exact product bytes and commerce rules are unchanged. Earlier planning is archived outside active planning; retained development evidence is reviewed for applicability rather than credited by task number. The original reset was documentation-only. The 2026-10-22 execution amendment now authorizes local repository implementation and ordinary isolated tests; external operations retain scoped authority gates.

Retain the existing authorized workflow preferences (autonomous planning, fine granularity, independent parallel work, documentation commits/sync and current-model inheritance). This planning pass is performed inline. Use supplied research as dated input; exact dependencies, tariffs, account capabilities and legal/merchant facts are verified at their affected phases. No live external audit or application tests are claimed.

## Constraints

- **Architecture:** Static Astro Content Collections + selected React islands; Django LTS/Gunicorn + PostgreSQL and one leased database outbox worker; Django owns `/purchase/simple/`. No request-time Astro/Node service or mandatory Redis/Celery/CMS/IdP.
- **Authority:** `SLL_xSPI_MC_Product_Page.md` embedded in the October 21 proposal is the sole product-definition source. One Markdown/YAML catalog compiles immutable public/private revisions; protected approvals govern offers. Admin cannot create a competing catalog.
- **Product:** `sll-xspi-mc`, `sll-xspi-mc-support-10h`, profile `sll-xspi-mc-v1`; exactly three vendors and thirteen ordered families. One vendor and quantity one per configured IP line; support has real positive package quantity.
- **Rights and money:** RDP is Altera-only; higher volume requires quotation. EUR is draft display/collection intent. Unknown rates, recurrence, coverage, rights, access or terms remain null/pending and disable affected live offers. Five-plus-five allowances and €50 are provisional; no universal MAC rule.
- **Private data:** Encrypt/version host bindings, mask ordinary summaries, and authorize each resource. Keep raw host IDs/keys, business/tax details and bearer links out of public artifacts, URLs, ordinary logs and browser persistence. Staff MFA covers every privileged route.
- **Durability:** Archive recoverable snapshots before bank dispatch, document issue, delivery activation, support-credit spendability and chargeable work; archive actual support completion before final statement publication. Prepared evidence is not completion. An uncertain bank operation cannot authorize a blind retry.
- **Support:** Each paid/accepted package grants exactly 36,000 integer seconds once with no expiry. Reservations prevent competing spend; corrections reverse/replace; statements use committed ledger revisions. Support never renews IP rights.
- **Infrastructure:** Existing OVH dedicated host `mx1`; NixOS-declared rootless Podman Quadlet/user-systemd under new proposed `shopsvc`, directly on the host, outside `claude-dev`. Separate Django, one worker, new shop PostgreSQL cluster and internal Caddy containers; independently owned backup jobs. No new production compute/block/IP rental or automatic paid fallback.
- **Domains:** Customer `https://shop.xspi.pro`; proposed staff `https://shop-admin.xspi.pro`; Route 53 authority unverified. Existing public ingress/TLS stays unchanged: prove a complete existing route/certificate lifecycle or defer activation with exact service/action proposal. Only later explicit service/action authorization can permit a protected change. New shop issuer is Let’s Encrypt; conditional DNS-01 cannot supply a missing traffic path. No A/AAAA before end-to-end path proof.
- **Recovery:** Independent off-host complete-pool-loss rehearsal, without production rpool or host-only secrets. Five-minute WAL timeout, 35-day DB window, 15-minute DB RPO and four-hour operator-start technical restore are proposed targets; include target provisioning/traffic timing and measure safe reopening separately. Block effects before exposure; reconcile money/acceptance/documents/licences/support and invalidate restored access/MFA state.
- **Evidence:** Real PostgreSQL for concurrency; label local/synthetic, selected-bank sandbox, actual OVH and production evidence separately. No invented approvals, compatibility, legal or provider guarantees.
- **Authorization:** The 2026-10-22 execution amendment authorizes local repository implementation and ordinary isolated tests; deployment and external operations retain their separate scoped gates. Source deployment designs do not grant host access or a protected-service exception. Real mail, bank, DNS/certificates, allowed host mutations and public activation require their actual scoped authority; generic deployment approval never overrides protection.
- **Estimates:** Supplied 46–74 engineer-days excludes external waiting/ongoing operations. About £0.79/month ex VAT is the dated illustrative incremental OVH cost for 130 GiB objects only; existing dedicated-server bill/capacity, bandwidth, DNS, merchant costs, retention growth and independent drills remain excluded. No permanent staging VM. Qualify real storage usage and tariffs; never prune required evidence to fit the model.

- **Resources:** Proposed aggregate shop CPUQuota=200%, MemoryHigh=6G/MemoryMax=8G, bounded tasks/concurrency at a verified host-controlled shop ancestor including payloads/conmon/network helpers/backups. CPU quota is time, not exclusive cores. Preserve existing cpusets, shared slices/delegation and every guest/service allocation.

- **Storage:** Proposed local ZFS 80 GiB aggregate shop cap including descendants/snapshots, with 50 GiB PostgreSQL data/index/WAL allowance. Account for rootless GraphRoot/images/volumes/temp/logs/certificates/spool; preserve shared journal, reserves, snapshots and disks. `gra` public/private objects; independent off-host `sbg` backups/evidence/artifacts with scoped credentials.

- **Protection:** Inventory every pre-existing rootful/rootless/native/VM resource in all states read-only before the first mx1 deployment write. Unknown ownership is protected. Require docs/host-protection-inventory.md, docs/shop-resource-allowlist.md, separate database identity and complete NixOS activation-impact review before mutations. No protected reload/restart/edit/prune/GC/upgrade/reboot or blanket NixOS activation; rollback is shop-only and preserves business records.

## Key Decisions

| Decision | Rationale | Outcome |
|---|---|---|
| Replace active architecture and deployment planning from the October 21 pair | Explicit user request; new product authority supersedes old inputs | Completed documentation reset |
| Preserve new T01–T14 as the phase/dependency structure | Direct acceptance/evidence traceability to the supplied implementation plan | Current source structure; only explicitly reconciled evidence retained |
| Keep support separate from IP rights and quantities | Non-expiring support purchases and fixed-term IP have different effects | Required source contract |
| Keep P-10 hosting resolved and its qualification pending; other approvals require evidence | Source proposals cannot approve themselves | Affected live operations gated |
| Complete unaffected preparation while external inputs wait | Bank/host/ingress/policy gaps have specific scopes | Required workflow policy |

## Evolution

At phase transitions update validated/active scope and decisions from actual evidence. At milestones review core value, business context and exclusions. Preserve historical acceptance, source revisions and approval records; revise future offers explicitly.

---
*Last updated: 2026-10-21 after protected-host documentation replanning.*

## Resource credentials — user instruction, 2026-10-21

The agent has access to resource credentials through the repository .env file. When authorized project work needs a credential, consult that file without printing values or copying them into planning, logs, commands, evidence or public artifacts. If the required credential is absent or empty, add a clearly named empty VARIABLE_NAME= entry with a short purpose comment to .env, preserving every existing entry, then ask the user to fill its value directly in that file. Never ask the user to paste secrets into chat. Continue independent work while waiting; do not invent values or approvals. No currently needed missing credential has been identified by this instruction alone.

This operator credential source does not require application .env auto-loading or relax runtime _FILE secrets, fake-only synthetic tests, build exclusions or existing action authorization. Read only the needed credential for the authorized operation; use non-logging process/environment or secret-file interfaces. Resource access is not automatic permission to purchase/provision, modify protected services or perform disruptive tests on mx1/its guests. The independent runner remains unassigned until the user supplies/authorizes it.

## Session context checkpoint — user instruction, 2026-10-21

During project implementation, when session context usage exceeds 90%, run `$gsd-pause-work` at a safe checkpoint before continuing implementation. Save the current position, completed and remaining tasks, evidence, blockers and exact next action in the GSD handoff. Inform the user: “Context usage exceeded 90%. Work is saved. Clear the session, then run `$gsd-resume-work`.” Wait for the cleared/resumed session before further implementation; this instruction authorizes the conditional pause without another confirmation.

Use the context usage indicator supplied by the session when available. If an exact percentage is unavailable, do not invent a measurement or claim automatic threshold monitoring; preserve a handoff proactively when context pressure is apparent and state that limitation. Keep secrets out of the handoff and retain all pending qualification checks as pending.

Active execution policy: [2026-10-22 amendment](EXECUTION-AMENDMENT-2026-10-22.md).
