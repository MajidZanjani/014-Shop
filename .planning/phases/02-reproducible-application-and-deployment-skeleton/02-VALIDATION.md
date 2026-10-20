---
phase: "02"
slug: "reproducible-application-and-deployment-skeleton"
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-10-20"
---

# Phase 2 — Validation Strategy

This is a prospective contract. No application checks have run. The planner must align the per-task map and concrete command paths with its final plans before execution.

## Test Infrastructure

Use Django TransactionTestCase with independent real PostgreSQL connections, Python unittest and Node's test runner. No SQLite fallback. A missing PostgreSQL service fails the required lane rather than skipping it. Use the pinned development shell and exact runtime/tool locks created during execution.

Quick command (proposed): `python3 scripts/check.py quick`.
Full command (proposed): `python3 scripts/check.py all`.
Both entry points must be produced by the first implementation plan, have bounded timeouts and nonzero failure exits. Full verification must report positive test/check counts and cannot succeed if a required lane is unavailable.

## Sampling Rate

After each task, run its focused automated command. After each wave run all available producing-plan checks; after the final wave run the complete suite. Record real timing at execution: target quick feedback under 60 seconds, complete local suite under 180 seconds excluding initial downloads and separately reported Nix builds/reproducibility checks. Never claim these targets as measured results.

## Per-Task Verification Map

| Check | Requirement | Secure behavior | Type | Proposed automated command | Exists | Status |
|---|---|---|---|---|---|---|
| Compatible frozen installs and static/Django smoke | BUILD-01 | No runtime Node, privileged routes disabled | integration | `python3 scripts/check.py quick` | No — producing plan | pending |
| Worker ownership and recovery | BUILD-01, BUILD-03 | Real concurrent connections, short lock, fenced owner, stable fake effect identity | PostgreSQL transaction | `python3 scripts/check.py worker` | No — producing plan | pending |
| Closed contracts and synthetic adapters | BUILD-03 | Reject malformed/unknown inputs and live network access | contract/negative | `python3 scripts/check.py contracts` | No — producing plan | pending |
| Secret/public/runtime isolation | BUILD-01, BUILD-03, BUILD-04 | Reject canary leaks and unsafe startup without real secrets | boundary/negative | `python3 scripts/check.py boundaries` | No — producing plan | pending |
| Actual artifact licences and SBOM | BUILD-02 | Complete transitive inventory; preserve unresolved legal findings | artifact | `python3 scripts/check.py inventory` | No — producing plan | pending |
| Two clean build payloads | BUILD-01, BUILD-02 | Exact payload identities; raw evidence preserved | reproducibility | `python3 scripts/check.py reproducibility` | No — producing plan | pending |
| Native service/template qualification | BUILD-04 | Runtime credential paths, separate DB mount, least privilege, configurable flavor | Nix evaluation/build | `python3 scripts/check.py deployment` | No — producing plan | pending |

## Wave 0 Requirements

- [ ] First producing plan creates the check dispatcher and focused test entry points before dependent commands are used.
- [ ] Pin build/runtime/tools and supply a real isolated PostgreSQL lifecycle helper with bounded readiness and safe ownership checks.
- [ ] Create synthetic test fixtures and framework configuration; no real `.env` reads.
- [ ] Add each final plan task ID, unique threat reference and producer dependency to this map; no three consecutive tasks lack automated feedback.
- [ ] Fail on missing tests, zero counts, unavailable required tools/services, silently skipped database checks, unresolved schema references or command errors.

## Manual-Only Verifications

| Behavior | Requirement | Why manual | Instructions |
|---|---|---|---|
| Scope fidelity and evidence classes | BUILD-01..04 | Automation cannot grant operational/commercial acceptance | Confirm local/fake results do not stand for T03/T05/T09/T11 or live proof. |
| Exact dependency review if researcher package protocol still requires it | BUILD-01, BUILD-02 | Registry heuristic alone is not compromise evidence | Review the concrete artifact identities and upstream provenance before any required install checkpoint; never infer approval from editable metadata. |
| Deployment qualification plan | BUILD-04 | No actual OVH host/account is exercised by T02 | Review B2-7/GRA11 and B3-8 fallback, native image/bootstrap/mount/recovery checklist with every unperformed step labelled. |
| Four unclassified edge-probe items | BUILD-01..04 | Deterministic engine could not classify requirement shape | Explicitly retain flags in plans; assess acceptance without silently dropping them. |

## Validation Sign-Off

- [ ] All tasks have automated checks or explicit producing-plan dependencies.
- [ ] Negative and positive controls exercise actual behavior, not textual implementation mirrors.
- [ ] Final plan commands, threat references and sampling map agree.
- [ ] Required PostgreSQL lane and no-live-effects checks pass.
- [ ] Full suite green; measured latency and actual evidence recorded.
- [ ] `nyquist_compliant: true` only after executed audit.

Approval: pending execution and human judgments. This planning document is not test evidence.
