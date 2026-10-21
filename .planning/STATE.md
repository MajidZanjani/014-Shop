---
gsd_state_version: "1.0"
current_phase: 02
current_phase_name: Reproducible application and deployment skeleton
status: executing
stopped_at: 02-06/07/08 implemented locally; off-host core qualification pending.
last_updated: "2026-10-21T06:15:23.993Z"
last_activity: 2026-10-21
last_activity_desc: 02-04 public build boundary passed; runner unassigned, disruptive qualification pending.
state_head: 2f07e57f8546cca4bfba4f77e466855af8092e55
progress:
  total_phases: 14
  completed_phases: 1
  total_plans: 20
  completed_plans: 8
  percent: 7
---

# Project State

## Project Reference

See .planning/PROJECT.md and SOURCES.md (October 21 current authority).

**Core value:** Turn an exact reviewed xSPI-MC configuration or support purchase into attributable acceptance, verified payment and recoverable licence delivery or support credit without duplicate effects.
**Current focus:** 02-00 and 02-03 complete; next 02-09 persisted synthetic enqueue. Phase 2 has 6/18 completed development plans; 3 implemented with qualification pending; 9 unimplemented, 24 tasks/14 waves. Current-source checks now pass; no host/runtime qualification claimed.

## Current Position

Phase: 02 of 14 — Reproducible application and deployment skeleton
Plan: 02-09 next; 02-06/07/08 implementation merged, qualification pending; existing 02-01 and 02-02 evidence retained only after applicability review.
Status: Executing Phase 2 under user continuation; phase auto-advance remains false.
Last activity: 2026-10-21 — Protected-host requirements, roadmap, detailed affected plans and stale handoff replaced.
Progress: [█░░░░░░░░░] 7% phases; no new application/host acceptance.

## Accumulated Context

### Decisions

- Only October 21 proposal/handoff governs architecture; exact product bytes unchanged.
- P-10 hosting direction resolved: rootless Podman/NixOS/Quadlet directly on mx1 under new proposed shopsvc, outside claude-dev. Separate app/worker/new PG/internal gateway; independently owned backup jobs.
- Proposed aggregate 200% CPU, 6/8 GiB memory and 80/50 GiB ZFS caps need qualification. No cloud compute/block/IP/fallback purchase; £0.79 is incremental object-only model.
- Every pre-existing/unknown resource in all states/owners/runtimes/native/VM is protected. Inventory/allowlist/DB identity/full activation impact precede host writes; only later explicit named service/action can permit a protected change.
- Ingress/TLS unchanged or deferred; no DNS before path proof. Existing SMTP/monitoring/backups unchanged. Fault/exhaustion/restart/capacity/restore tests off-host; bounded mx1 checks only. Rollback shop-only.
- Exact 02-01 approval digest remains 136610b07612762d390b3b3c234ff1ef3f6dc6b0e44a69a2abc646d9106b51bd. 02-02 cached development build/PG evidence retained; new OCI/runtime/host evidence pending. Bound any necessary native build cores/jobs/timeouts; never duplicate builds.
- User continuation authorizes repository implementation and ordinary local/synthetic tests. Existing applicable local execution authorization/push preference remains recorded; no protected-service or external operational authorization is inferred.

### Pending Todos

02-00 source migration is complete and merged. 02-03 static synthetic build passed 3 integration tests, clean install and diagnostics. 02-04 passed 13 checks/9 tests; 02-05 passed 63 checks/7 tests. Continue 02-06 under current context. Two old clean retained worktrees have no task edits/commits; they remain at historical base 2c64d9b and must never execute stale prompts. A future GSD orchestrator must reconcile the recorded manifest and supply fresh current context/base before dispatch. Do not manually merge, broadly clean or restart old workers. No worker was started by this replan.

### Blockers/Concerns

02-00 all passed six groups (20/27/279/88/39/18 checks) and self-check rejected 71 mutations. Historical/current evidence are separate; shared BUILD requirements remain incomplete.

P-10 host qualification remains unperformed. P-11 public route/zone/certificate contract and P-12 existing SMTP/monitoring/owners remain pending; other commercial/custody decisions stay pending. These defer exact affected operations only. No fresh mx1 inspection or independent off-host runner is claimed. Off-host runtime lanes require an authorized resource and return blocked/nonzero if absent; no automatic infrastructure purchase.

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|---|---|---|---|
| 261021-8cb | Replan October 21 protected mx1 rootless Podman architecture and retire cloud-instance requirements | 2026-10-21 | 2f07e57 | [261021-8cb-replan-from-october-21-proposal-and-hand](./quick/261021-8cb-replan-from-october-21-proposal-and-hand/) |

## Session Continuity

Last session: 2026-10-21T06:10:29Z
Stopped at: 02-00 merged; proceeding to frontend/Python dependency slices.
Resume file: .planning/phases/02-reproducible-application-and-deployment-skeleton/.continue-here.md

Python 02-05 is merged: 63 actual import/identity checks and 7 rejection tests; 6 runtime/39 tool distributions. Shared /tmp is only 128 MB; use task-owned project .scratch/TMPDIR for wheel/venv work, never clean shared files. User confirmed no independent runner is assigned. Continue implementation and ordinary local tests; prepare disruptive suites without executing them here. Runner specification: docs/qualification-runner.md. Do not ask repeatedly or provision automatically.

02-06/07/08 local backend implementation is merged. Latest ordinary core-local: 4 checks/20 tests; full core remains nonzero pending authorized off-host outage case. Do not count summary presence as completed qualification. Runner remains unassigned. Next 02-09.

Credential workflow: resource access secrets are available via repository .env. For a needed missing/empty credential, append a named blank entry/purpose without exposing existing values and ask the user to fill .env. Preserve runtime/build/privacy and operation authorization boundaries.
