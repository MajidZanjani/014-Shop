---
phase: "01"
slug: "product-authority-repository-review-and-decision-register"
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-10-20"
---

# Phase 1 — Validation Strategy

Planning contract only. No future checker command below has run or passed. Implementation sign-off remains pending until the documentation plans are actually executed.

## Test Infrastructure

| Property | Value |
|---|---|
| Framework | Python standard library and Git; no package/framework installation |
| Existing inputs | Hash-verified source pair, extracted product and existing inventory matrix |
| Planned checker | docs/product-source/verify_t01.py; absent until Plan 01-01 creates it |
| Quick command | python3 docs/product-source/verify_t01.py source |
| Full command | python3 docs/product-source/verify_t01.py all |
| Negative checks | python3 docs/product-source/verify_t01.py self-check |
| Runtime budget | Target under 30 seconds; actual time recorded at execution |

## Sampling Rate

Run the relevant available checker mode after each task, then all/self-check at the final plan gate. Every runnable automated command in PLAN.md must have an immediately following fails_when element. Commands that depend on future artifacts must be tied to the producing task or wave; no missing referenced framework/config is accepted as a pass.

## Per-Task Verification Map

The planner must reconcile final task IDs with this initial map before checker approval.

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | Availability | Status |
|---|---|---|---|---|---|---|---|
| 01-01-01 | 01 | 1 | SRC-01, SRC-02 tracer | provenance + one-row tracer | python3 docs/product-source/verify_t01.py source | produced by task | pending |
| 01-01-02 | 01 | 1 | SRC-04 | scope metadata and identity | python3 docs/product-source/verify_t01.py scope | source mode exists; extend in task | pending |
| 01-01-03 | 01 | 1 | SRC-01, SRC-04 | isolated negative checks | python3 docs/product-source/verify_t01.py self-check | implement available-mode probes in task | pending |
| 01-02-01 | 02 | 2 | SRC-02 | exact ordered inventory and locators | python3 docs/product-source/verify_t01.py inventory | extend checker in task | pending |
| 01-02-02 | 02 | 2 | SRC-03 | register structure/status/gates | python3 docs/product-source/verify_t01.py decisions | extend checker in task | pending |
| 01-02-03 | 02 | 2 | SRC-01–SRC-04 | complete evidence consistency | python3 docs/product-source/verify_t01.py all | earlier tasks produce all modes | pending |

## Wave 0 Requirements

- Plan 01-01 creates the small checker and scope-note inputs before their dependent commands.
- Existing source snapshots stay byte-identical; no fixture mutation touches canonical source or .env.
- Plan 01-02 extends the checker, exact source locators and register validation. No dependency installation required.

## Negative Directions

Source checks reject altered bytes/final newline/appendix equality. Inventory checks reject same-count label substitutions/order changes and missing logical groups. Decision checks reject malformed column widths, duplicate/missing P entries, missing owners/phase/operation or approval claims without scoped evidence. Scope checks reject wrong source IDs/origin and unsupported branch isolation claims. self-check exits zero only if every expected rejection is observed in memory or isolated temporary input; the canonical source is never edited for testing.

## Manual-Only Verifications

| Behavior | Requirement | Why manual | Instructions |
|---|---|---|---|
| Source intent vs proposed enforcement | SRC-02 | Counts/grep cannot establish semantic fidelity | Inspect requiredness, logical/repeated rows and provisional choices against cited source |
| Approval/phase mapping | SRC-03 | Operation gating requires judgment | Review all P entries; keep role-only ownership and pending status; no invented names/approvals |
| Scope and isolation | SRC-04 | Metadata alone cannot authorize changes | Record actual HEAD/branch/worktrees, protect unrelated work; planning never switches branch; execution isolation is fulfilled or explicitly reported as pending |
| Evidence honesty | SRC-01–SRC-04 | File presence is not executed proof | Record only actual task command/environment/revision outcomes; later phases remain pending |

## Security Sampling

Every plan includes a proportional threat_model covering source substitution, fabricated approval/completion and credential/unrelated-work disclosure. All reads are explicit allowlisted document/metadata paths; .env remains ignored and unopened. Source checks exercise tampering; register checks exercise approval/structure defects. No application ASVS implementation/certification is claimed.

## Validation Sign-Off

- [ ] All planned tasks have executable verification and explicit failure signals.
- [ ] Producer tasks precede every future checker command.
- [ ] Negative directions reject mutated candidates without changing canonical inputs.
- [ ] Manual source/approval/scope/evidence review completed during execution.
- [ ] All actual task results recorded with environment/revision identity.
- [ ] nyquist_compliant and wave_0_complete updated only from execution evidence.

Approval: pending execution.
