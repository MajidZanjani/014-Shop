<!-- GSD:project-start source:PROJECT.md -->

## Project

**SLL xSPI-MC Shop**

A configurable xSPI-MC semiconductor-IP shop at `shop.xspi.pro` for engineering and business purchasers. Customers configure vendor-specific licences, answer one basic board/platform question, buy applicable pre-approved standard offers or request a narrow exception quote, and purchase non-expiring ten-hour SLL support independently or with IP. Approved R&D materials may precede a promised later reference design. Staff use MFA-protected workflows to review acceptance/payment, issue matching private packages and keys, process renewal/rehosting cases, and account for support work.

**Core Value:** Turn an exact approved standard or reviewed xSPI-MC configuration or support purchase into attributable acceptance, verified payment and recoverable licence delivery or support credit without duplicate effects.

### Constraints

- **Architecture:** Static Astro Content Collections + selected React islands; Django LTS/Gunicorn + PostgreSQL and one leased database outbox worker; Django owns `/purchase/simple/`. No request-time Astro/Node service or mandatory Redis/Celery/CMS/IdP.
- **Authority:** `SLL_xSPI_MC_Product_Page.md` embedded in the October21 proposal is the immutable baseline; final26October purchase-flow revision2 supersedes conflicting purchase/support/staged-delivery requirements. One Markdown/YAML catalog compiles immutable public/private revisions; protected approvals govern offers. Admin cannot create a competing catalog.
- **Product:** `sll-xspi-mc`, `sll-xspi-mc-support-10h`, profile `sll-xspi-mc-v1`; exactly three vendors and thirteen ordered families. One vendor and quantity one per configured IP line; support has real positive package quantity.
- **Rights and money:** RDP is Altera-only; higher volume requires quotation. EUR is draft display/collection intent. Unknown rates, recurrence, coverage, rights, access or terms remain null/pending and disable affected live offers. Five-plus-five allowances and €50 are provisional; no universal MAC rule.
- **Private data:** Encrypt/version host bindings, mask ordinary summaries, and authorize each resource. Keep raw host IDs/keys, business/tax details and bearer links out of public artifacts, URLs, ordinary logs and browser persistence. Staff MFA covers every privileged route.
- **Durability:** Archive recoverable snapshots before bank dispatch, document issue, delivery activation, support-credit spendability and chargeable work; archive actual support completion before final statement publication. Prepared evidence is not completion. An uncertain bank operation cannot authorize a blind retry.
- **Purchase flow:** One platform question plus conditional kit/name; unknown/custom/unfinished boards may use an applicable pre-approved development offer. Support optional/required and approved minimum come from the offer; no universal mandatory package, per-sale engineering approval, technical dossier or portal. Later reference design remains an explicit obligation.
- **Support:** SLL IP/integration guidance only. Each paid/accepted package grants exactly 36,000 integer seconds once with no expiry. Reservations prevent competing spend; corrections reverse/replace; statements use committed ledger revisions. Support never renews IP rights.
- **Infrastructure:** Existing OVH dedicated host `mx1`; NixOS-declared rootless Podman Quadlet/user-systemd under new proposed `shopsvc`, directly on the host, outside `claude-dev`. Separate Django, one worker, new shop PostgreSQL cluster and internal Caddy containers; independently owned backup jobs. No new production compute/block/IP rental or automatic paid fallback.
- **Domains:** Customer `https://shop.xspi.pro`; proposed staff `https://shop-admin.xspi.pro`; Route 53 authority unverified. Existing public ingress/TLS stays unchanged: prove a complete existing route/certificate lifecycle or defer activation with exact service/action proposal. Only later explicit service/action authorization can permit a protected change. New shop issuer is Let’s Encrypt; conditional DNS-01 cannot supply a missing traffic path. No A/AAAA before end-to-end path proof.
- **Recovery:** Independent off-host complete-pool-loss rehearsal, without production rpool or host-only secrets. Five-minute WAL timeout, 35-day DB window, 15-minute DB RPO and four-hour operator-start technical restore are proposed targets; include target provisioning/traffic timing and measure safe reopening separately. Block effects before exposure; reconcile money/acceptance/documents/licences/support and invalidate restored access/MFA state.
- **Evidence:** Real PostgreSQL for concurrency; label local/synthetic, selected-bank sandbox, actual OVH and production evidence separately. No invented approvals, compatibility, legal or provider guarantees.
- **Authorization:** The 2026-10-22 execution amendment authorizes local repository implementation and ordinary isolated tests; deployment and external operations retain their separate scoped gates. Source deployment designs do not grant host access or a protected-service exception. Real mail, bank, DNS/certificates, allowed host mutations and public activation require their actual scoped authority; generic deployment approval never overrides protection.
- **Estimates:** Supplied 46–74 engineer-days excludes external waiting/ongoing operations. About £0.79/month ex VAT is the dated illustrative incremental OVH cost for 130 GiB objects only; existing dedicated-server bill/capacity, bandwidth, DNS, merchant costs, retention growth and independent drills remain excluded. No permanent staging VM. Qualify real storage usage and tariffs; never prune required evidence to fit the model.

- **Resources:** Proposed aggregate shop CPUQuota=200%, MemoryHigh=6G/MemoryMax=8G, bounded tasks/concurrency at a verified host-controlled shop ancestor including payloads/conmon/network helpers/backups. CPU quota is time, not exclusive cores. Preserve existing cpusets, shared slices/delegation and every guest/service allocation.

- **Storage:** Proposed local ZFS 80 GiB aggregate shop cap including descendants/snapshots, with 50 GiB PostgreSQL data/index/WAL allowance. Account for rootless GraphRoot/images/volumes/temp/logs/certificates/spool; preserve shared journal, reserves, snapshots and disks. `gra` public/private objects; independent off-host `sbg` backups/evidence/artifacts with scoped credentials.

- **Protection:** Inventory every pre-existing rootful/rootless/native/VM resource in all states read-only before the first mx1 deployment write. Unknown ownership is protected. Require docs/host-protection-inventory.md, docs/shop-resource-allowlist.md, separate database identity and complete NixOS activation-impact review before mutations. No protected reload/restart/edit/prune/GC/upgrade/reboot or blanket NixOS activation; rollback is shop-only and preserves business records.

<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->

## Technology Stack

| Component | Planning choice | Verification |
|---|---|---|
| Public build | Static Astro Content Collections + selected React islands | Exact compatible frozen graph; no runtime Node/adapter |
| App | Django LTS/Gunicorn/Psycopg/Python | Retained approved artifacts; actual runtime/import/lock/SBOM proof in T02 |
| Database/queue | New independent PostgreSQL container/cluster and one worker | Real PostgreSQL concurrency; distinct PGDATA/roles/credentials/socket/backup; destination checks |
| Development tools | Pinned Nix shell, Node/npm, Python/pip and PostgreSQL/libpq | Existing 02-02 development evidence; cached outputs retained |
| Production services | Rootless Podman, NixOS-declared Quadlet/user-systemd, proposed shopsvc directly on mx1 | Pin exact OCI/runtime/Quadlet/systemd/network/storage compatibility; one lifecycle; off-host runtime evidence then bounded T11 attestation |
| Resource boundary | Proposed host-controlled aggregate 200% CPU, MemoryHigh 6G / MemoryMax 8G, bounded tasks/concurrency | Covers payload scopes/conmon/network helpers/backup; protected parent/CPU/guest allocations unchanged |
| Persistence | New local ZFS shop datasets: 80 GiB aggregate, 50 GiB DB subtree | Snapshots/descendants and all rootless writable paths/logs/spool accounted; existing reserves/disks unchanged |
| Edge | New internal Caddy 2 behind unchanged existing public ingress | Fixed HTTPS object origin and metadata boundary; conditional A/B profile, complete path before DNS; new-shop Let’s Encrypt only |
| Recovery | Independent sbg pgBackRest, retained evidence, artifacts and custody | Full-pool-loss off-host rehearsal; existing PostgreSQL/services never restore targets |
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

## Session context checkpoint — user instruction, 2026-10-21

During project implementation, when session context usage exceeds 90%, run `$gsd-pause-work` at a safe checkpoint before continuing implementation. Save the current position, completed and remaining tasks, evidence, blockers and exact next action in the GSD handoff. Inform the user: “Context usage exceeded 90%. Work is saved. Clear the session, then run `$gsd-resume-work`.” Wait for the cleared/resumed session before further implementation; this instruction authorizes the conditional pause without another confirmation.

Use the context usage indicator supplied by the session when available. If an exact percentage is unavailable, do not invent a measurement or claim automatic threshold monitoring; preserve a handoff proactively when context pressure is apparent and state that limitation. Keep secrets out of the handoff and retain all pending qualification checks as pending.

Active sequencing and concise progress policy: [2026-10-22 execution amendment](.planning/EXECUTION-AMENDMENT-2026-10-22.md).

Current purchase-flow authority and sequencing: [.planning/PURCHASE-FLOW-AMENDMENT.md](.planning/PURCHASE-FLOW-AMENDMENT.md). Dated completed quick/phase evidence is historical; use STATE/HANDOFF and amended active plans for routing.
