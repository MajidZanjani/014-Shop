<!-- GSD:project-start source:PROJECT.md -->

## Project

**SLL xSPI-MC Shop**

A configurable xSPI-MC semiconductor-IP shop at `shop.xspi.pro` for engineering and business purchasers. Customers configure separate vendor-specific licence lines, request reviewed quotes or buy approved offers, and purchase non-expiring ten-hour support packages independently or with IP. Staff use MFA-protected workflows to review acceptance/payment, issue matching private packages and keys, process renewal/rehosting cases, and account for support work.

**Core Value:** Turn an exact reviewed xSPI-MC configuration or support purchase into attributable acceptance, verified payment and recoverable licence delivery or support credit without duplicate effects.

### Constraints

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

<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->

## Technology Stack

| Component | Planning choice | Verification |
|---|---|---|
| Public build | Static Astro Content Collections + React islands | Exact compatible releases/artifact hashes at T02; no server adapter |
| App | Django LTS, Gunicorn, Psycopg, Python | Supplied Django 5.2.18/Python 3.13 are research inputs, verify support/patches/licences at T02 |
| Database/queue | PostgreSQL and one leased outbox worker | Supplied PostgreSQL 18.6 is a baseline assertion; real locking/concurrency proof |
| Build runtime | Supplied Astro 7/React 19/Node 24 LTS | Verify actual compatibility and support before locks |
| Services | Supported pinned NixOS/native systemd; approved Podman fallback | Qualify image/bootstrap at T11; no simultaneous managers |
| Edge | Caddy 2, explicit Let's Encrypt | Pinned build; DNS-01 module only if needed, test renewal |
| Recovery | pgBackRest, separate gra/sbg namespaces and custody | Actual provider retention/ACL/restore proof at T11/T12 |
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->

## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->

## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->

## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->

## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `$gsd-fast` for a trivial task inline, with no subagents and no PLAN.md
- `$gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `$gsd-debug` for investigation and bug fixing
- `$gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->

## Developer Profile

> Profile not yet configured. Run `$gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
