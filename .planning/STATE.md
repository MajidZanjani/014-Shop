---
gsd_state_version: "1.0"
current_phase: 02
current_phase_name: Reproducible application and deployment skeleton
status: executing
stopped_at: 02-13 implementation merged; next 02-14 artifacts, independent runner unassigned.
last_updated: "2026-10-21T06:15:23.993Z"
last_activity: 2026-10-21
last_activity_desc: 02-04 public build boundary passed; runner unassigned, disruptive qualification pending.
state_head: 2f07e57f8546cca4bfba4f77e466855af8092e55
progress:
  total_phases: 14
  completed_phases: 1
  total_plans: 20
  completed_plans: 10
  percent: 7
---

# Project State

## Project Reference

See .planning/PROJECT.md and SOURCES.md (October 21 current authority).

**Core value:** Turn an exact reviewed xSPI-MC configuration or support purchase into attributable acceptance, verified payment and recoverable licence delivery or support credit without duplicate effects.
**Current focus:** All Phase 2 plans have some repository work, but only eight local slices are complete (00–05,09,15). Seven await required qualification/human review (06–08,10–13). Three remain implementation-incomplete (14,16,17). Their evidence is in PARTIAL.md files, not completion SUMMARY.md files. Next: finish 14 bootstrap/per-mutation/runtime driver and 16 native/notice/schema coverage; then complete 17 OCI/full CI qualification.

## Current Position

Phase: 02 of 14 — Reproducible application and deployment skeleton
Status: executing; full phase/BUILD/production acceptance incomplete, auto-advance false.
Last activity: 2026-10-21 — Candidate rootless/Nix/profile artifacts, real installed SBOM findings, two local payload builds and installer controls committed; full all exits 1 at off-host gate.
Progress: 1/14 phases complete. Existing protected services/resources unchanged.

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

02-00 source migration is complete and merged. 02-03 static synthetic build passed 3 integration tests, clean install and diagnostics. 02-04 passed 13 checks/9 tests; 02-05 passed 63 checks/7 tests. Continue 02-14 under current context. Two old clean retained worktrees have no task edits/commits; they remain at historical base 2c64d9b and must never execute stale prompts. A future GSD orchestrator must reconcile the recorded manifest and supply fresh current context/base before dispatch. Do not manually merge, broadly clean or restart old workers. No worker was started by this replan.

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

Latest execution: frontend 13 checks/9 tests; core-local 4/20; worker-smoke 6/24 including two broken-control rejection tests; adapters 3/6 in network namespace; contracts-local 12/8; combined boundaries 17/32. Counts are separate/reused lanes, not a sum of unique tests. Full core/worker/contracts remain nonzero pending actual authorized off-host cases. Human browser hydration and schema/diagram source-fidelity review pending. No runner assigned and no disruptive tests executed on mx1/its guests.

Prepared: real DB-outage/recovery and worker receipt-before-completion interruption cases, guarded by exact independent runner/machine/commit/action authorization. Remaining rootless resource-exhaustion/lifecycle/recovery artifacts are owned by 14–17/T12, not yet implemented. Runner specification: docs/qualification-runner.md. Do not repeatedly ask or automatically provision.

Current continuation (supersedes older next-plan prose): finish 14 implementation (bootstrap/per-mutation wrapper, exact user runtime/generator configuration and executable replica driver). Existing offhost-cases.json is only a matrix. 16 retains actual standard SBOMs (271 npm/6 runtime Python/39 tool Python), but raw npm schema URI failure, 12 missing-text findings and native/OCI closure coverage prevent INVENTORY_PASS. 17 local payload reproducibility passed two builds/5 tests, locks 3 checks/8 tests, environment 2/14. Full all ran environment/frontend then stopped pending off-host with exit1, no FULL_PASS. Manual CI prepared only, not run. Images unbuilt; ~2.4 GiB free at preparation, never clean shared files/store/caches or change allocations. Exact new component review/build resources still need qualification.

Incomplete evidence records now use PARTIAL.md because GSD completion discovery counts SUMMARY presence. Eight genuine local completion summaries remain; no accidental 18/18 completion. Read PARTIAL records before work; do not replay completed implementations or mistake missing off-host evidence for permission to run faults here. Runner remains unassigned; no repeat question or automatic provisioning. Credential .env policy remains in PROJECT/CONTEXT.
