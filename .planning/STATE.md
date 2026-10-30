---
gsd_state_version: "1.0"
release: shb-1.1
current_phase: 3
current_phase_name: Supporting Hours Bundle catalog and approved pricing
current_plan: 1
current_task: 1
status: in_progress
last_updated: "2026-10-30T10:06:03.188759+00:00"
last_activity: 2026-10-30
state_head: cbf5941086172dd7cf53bca637e5a8529d22f23b
progress:
  total_phases: 14
  completed_phases: 1
  total_plans: 42
  completed_plans: 11
  percent: 7
---

# Project state — Supporting Hours Bundle revision 1.1

Current authority: [SHB revision 1.1](../014-Shop-SHB-Proposal-Revision-2026-10-30.md), SHA256 `ba801dff4adbfdcfa0f1e43cfe1f2d6963780476867da1b5e6f737230a472b5e`. The user explicitly replaces the earlier active product plan on 2026-10-30. Current routing: [STATE.md](STATE.md) / [ROADMAP.md](ROADMAP.md).

**Current development focus:** 3 — Supporting Hours Bundle catalog and approved pricing.

**Last fully completed phase:** 1 — documentary authority/reconciliation only; historical implementation evidence is not SHB acceptance.

**Current plan:** 03-01 — Supporting Hours Bundle catalog, 10/25-hour variants and common/ASIC form rules.

**Execution status:** in progress — SHB revision 1.1 replanned; implementing the single-product catalog and minimum forms; no live acceptance.

**Next implementation task:** Implement and verify SHB catalog/forms, then invitation-gated private storefront and old-IP route denial; continue FPGA/ASIC/coupon/payment integration under the revised plans.

SHB records only bundle size, quantity and hours bought in each order. SLL manually tracks used/remaining FPGA/ASIC hours and manually emails each task outside the shop. Preserve historical code/data/accepted obligations. Automated time credits/debits/reservations, cumulative balances, customer support/bundle panels/APIs, staff time entry and task-usage-email generation are deferred and are not SHB launch dependencies.

Historical completed-plan counts describe retained records, not SHB acceptance or engineering effort. Earlier Phase2 policy-issuance continuation is retained as a release prerequisite and is not the next product task.

## Evidence and constraints

Previous synthetic backend/payment, archived transaction, staff MFA/recovery, exact source/image/SBOM/lock evidence remains attributable at docs/archive/2026-10-30-before-shb and docs/build. No old test result verifies the revised SHB product. SHB tests are pending until executed.

## External inputs

One support-offer record and exact operation boundaries are in docs/decisions.md. No commercial rate/legal/tax/ASIC adoption, bank/mail/provider, independent runner, host or public activation approval is invented. User will provide company inputs later; continue independent local work without repeated requests.

## Session Continuity

Last session: 2026-10-30T10:06:03.188759+00:00
Stopped at: active SHB replan complete; proceeding with 03-01. Old pause artifacts archived/consumed.
Resume file: HANDOFF.md

Sandbox startup fails on this workspace; narrowly scoped escalated local commands are the recorded workaround. Use existing owned .scratch/auth-unicode-tmp and .scratch/phase2-repro-nix-cache per command. Do not read/delete/stage unrelated http_cache.sqlite. No .env or real credentials are needed. Exact context percentage is unavailable; honor the user checkpoint rule without claiming automatic threshold monitoring.
