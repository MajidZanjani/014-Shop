# AGENTS.md — SLL Supporting Hours Bundle Shop

Current user-authorized product plan: [SHB revision 1.1](014-Shop-SHB-Proposal-Revision-2026-10-30.md), read fully including Appendix A. It supersedes conflicting earlier storefront/IP/time-ledger requirements. Existing .planning/PROJECT.md, REQUIREMENTS.md, ROADMAP.md and STATE.md are the operative plan; stable old phase/folder IDs are retained for history. Historical originals are in docs/archive/2026-10-30-before-shb; their next actions are not active instructions.

## Amendment precedence (2026-11-04)

The user-authorized planning and execution amendment
[`014-Shop-SHB-Claude-Correction-Prompt-2026-11-04.txt`](014-Shop-SHB-Claude-Correction-Prompt-2026-11-04.txt)
governs how work on this release continues. SHB revision 1.1 above
remains the **product specification**; the amendment supersedes
conflicting earlier **planning and execution** instructions, including
the previous "no local work remains" stopping condition recorded in
HANDOFF and the Phase 6 continuation. All security and operational
restrictions in this file — protected services, no blanket NixOS
activation, no real bank/mail/host/DNS/TLS action, no paid provisioning,
closed production/bank-sandbox gate, unassigned off-host runner, credential
handling — remain binding without exception.

The amendment identifies concrete defects in current source/test/CI/doc
artifacts (SHB-13 silent-skip, check_shb.py suite asymmetry, check_backend.py
legacy module list, development.yml demo_purchase_flow invocation,
REQUIREMENTS.md citations of nonexistent test methods). These are
tracked in `.planning/HANDOFF.md` as remaining SHB implementation.
Source/evidence registration and planning reconciliation for the
amendment were completed on 2026-11-04 by quick task `261104-81g`; future
sessions continue the resulting plan rather than repeat adoption. The
project-root `CLAUDE.md` imports this file and the amendment TXT; do not
add a second entry point.

## Product

Invitation-only shop at https://shop.xspi.pro. One visible product **Supporting Hours Bundle**; exactly **FPGA Supporting Hours Bundle** (10 hours, automatic eligible Checkout) and **ASIC Supporting Hours Bundle** (25 hours, Submit Request then reviewed matching offer/acceptance/payment). Positive whole-bundle quantity, authoritative price/hours, minimum company/billing/contact form and optional scoped percentage code. New IP sales/routes are disabled; preserve prior code/history/accepted obligations. No new licence/board/host/production questionnaire or technical uploads.

SHB records only bundle size, quantity and hours bought in each order. SLL manually tracks used/remaining FPGA/ASIC hours and manually emails each task outside the shop. Preserve historical code/data/accepted obligations. Automated time credits/debits/reservations, cumulative balances, customer support/bundle panels/APIs, staff time entry and task-usage-email generation are deferred and are not SHB launch dependencies.

## Architecture, privacy and money

Retain static Astro Content Collections + selected React islands; Django LTS/Gunicorn, PostgreSQL and one leased durable worker. No request-time Astro/Node, mandatory Redis/Celery/CMS/IdP or replacement platform. Markdown/YAML approved versioned catalog; unknown live price/currency/tax/terms/policy remains null and disables only the affected live action. One versioned support-offer approval record in docs/decisions.md; no invented adoption, approver, compatibility, legal/provider guarantee or automatic paid fallback.

Six-calendar-month invitations in Asia/Tbilisi (month-end clamp; UTC instant; now < expiry), 32 random-byte digest-only reusable bearers, no commercial effects from GET. Retain shorter 30-minute sessions capped by invitation and current-state expiry/revocation checks. No raw bearer in logs/referrers/normal DB records/bank URLs/browser persistence. Invitations authorize new offers/purchases only; no private history/prefill or proof of named identity. Preserve verified resource access and staff MFA/recent verification on every privileged route. Form-entered contact never becomes company authorization.

Protect static HTML/catalog/prices/assets behind server access control; private release storage with manifest-approved service delivery. No public bucket/alternate hostname/old route/preview/source-map bypass. No-store protected responses, host-only secure HTTP-only cookies and CSRF/origin controls. Authenticated bank reconciliation continues after invite expiry; preserve accepted prices/offer/order identity and archive-before-effects. Uncertain operations never authorize a blind retry. No synthetic record becomes real money/approval.

## Infrastructure and release gates

Existing October21 protection/security/financial/recovery requirements remain binding where relevant. Preserve Stalwart, WebAdminProxy, Plesk/WordPress, existing PostgreSQL, Prometheus, Grafana/Grafana-TLS, Blackbox, Alertmanager, MicroVMs, NetBird, Matrix and every pre-existing/uncertain resource in every state. No blanket NixOS activation, protected reload/restart/edit/prune/GC/upgrade/reboot, firewall/DNS/TLS change, real bank/mail action or paid fallback. Inventory all owners/resources read-only, maintain docs/host-protection-inventory.md and docs/shop-resource-allowlist.md, separate database identity and complete activation-impact review before any authorized shop write. Rootless shopsvc directly on mx1, outside claude-dev; one leased worker, independent PostgreSQL, internal Caddy. Proposed host-controlled aggregate 200% CPU, 6G high/8G max, bounded tasks; preserve cpusets/parents/guests. Proposed 80 GiB aggregate ZFS including snapshots/descendants, 50 GiB DB including WAL; account GraphRoot/images/volumes/temp/logs/certificates/spool/backups. Private gra release storage and independent sbg recovery custody; no new production compute/block/IP rental. No host process/control/management mounts in apps. Independent runtime/fault/exhaustion/complete-loss drills require an assigned authorized off-host runner; none is assigned. Production/bank-sandbox database connection gate stays closed until actual identity/all-write/transport/migration/runtime qualification. Prepared evidence is not completion; archive recoverable accepted/order/payment/document effects before use; uncertain bank dispatch cannot authorize a blind retry.

## GSD workflow and continuation

Before file edits start through gsd-fast (trivial), gsd-quick (ad hoc), gsd-debug or gsd-execute-phase (planned), unless the user explicitly bypasses. Keep PROJECT/STATE/ROADMAP/HANDOFF and state.json synchronized before implementation/status commits; refresh planning inventory and run scripts/check_planning.py and scripts/check_purchase_plan.py. Completion counts are records, not engineering effort. User authorizes continued local implementation and ordinary isolated tests; deployment and every external operation retain scoped gates.

Continue across commits/syncs without stopping after each small task; ordinary non-force push to origin/main after each project commit is already authorized. Company inputs will arrive later; do not repeatedly request them. Continue unaffected local work with explicit synthetic fixtures. No new subagent request exists; execute inline.

When context usage supplied by the session exceeds90%, run gsd-pause-work at a safe checkpoint, saving exact completed/remaining tasks, evidence, blockers and next action without secrets. Tell the user: “Context usage exceeded 90%. Work is saved. Clear the session, then run `$gsd-resume-work`.” Wait for resumed/cleared session. If no exact percentage is supplied, do not invent one or claim automatic monitoring; save proactively only when actual context pressure is apparent and state the limitation. The user's standing conditional pause authorization remains.

Credentials: consult only needed authorized entries in .env without printing/copying secrets; no automatic .env loading. Missing needed entries may be added empty with purpose and the user asked to fill them in the file, never chat. Credentials do not grant resource/action authority. Current local work needs no real credentials. Leave unrelated http_cache.sqlite untouched.
