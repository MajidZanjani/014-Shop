---
phase: "01"
slug: "product-authority-repository-review-and-decision-register"
status: validated
nyquist_compliant: true
wave_0_complete: true
created: "2026-10-20"
---

# Phase 1 — Validation Strategy

Both documentation plans have executed. Source, scope, inventory, decision and evidence modes run green on merged main after the recorded portability repair. Automated coverage is audited below; manual source/approval/scope judgments still require verification and are not auto-approved.

## Test Infrastructure

| Property | Value |
|---|---|
| Framework | Python standard library and Git; no package/framework installation |
| Existing inputs | Hash-verified source pair, extracted product and existing inventory matrix |
| Planned checker | docs/product-source/verify_t01.py; created by Plan 01-01 and extended by Plan 01-02 |
| Quick command | python3 docs/product-source/verify_t01.py source |
| Full command | python3 docs/product-source/verify_t01.py all |
| Negative checks | python3 docs/product-source/verify_t01.py self-check |
| Runtime budget | Target under 30 seconds; actual time recorded at execution |

## Sampling Rate

Run the relevant available checker mode after each task, then all/self-check at the final plan gate. Every runnable automated command in PLAN.md must have an immediately following fails_when element. Commands that depend on future artifacts must be tied to the producing task or wave; no missing referenced framework/config is accepted as a pass.

## Per-Task Verification Map

Final task IDs below match the two dependent three-task plans. Wave 2 follows Wave 1 because the checker and matrix are shared; no phase implementation has run during planning.

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | Availability | Status |
|---|---|---|---|---|---|---|---|
| 01-01-01 | 01 | 1 | SRC-01, SRC-02 tracer | provenance + one-row tracer | python3 docs/product-source/verify_t01.py source | checker and source mode produced by this task | green (observed execution) |
| 01-01-02 | 01 | 1 | SRC-04 | scope metadata and identity | python3 docs/product-source/verify_t01.py scope | scope note/mode produced by this task after 01-01-01 | green (observed execution) |
| 01-01-03 | 01 | 1 | SRC-01, SRC-04 | isolated negative checks | python3 docs/product-source/verify_t01.py self-check | source/scope self-check produced by this task | green (observed execution) |
| 01-02-01 | 02 | 2 | SRC-02 | exact ordered inventory and locators | python3 docs/product-source/verify_t01.py inventory | inventory mode and its self-check cases produced by this task | green (observed execution) |
| 01-02-02 | 02 | 2 | SRC-03 | register structure/status/gates | python3 docs/product-source/verify_t01.py decisions | decisions mode and read-only/rejection cases produced by this task | green (observed execution) |
| 01-02-03 | 02 | 2 | SRC-01–SRC-04 | complete evidence consistency | python3 docs/product-source/verify_t01.py all | all/evidence checks produced by this task; also runs completed self-check and scoped diff check | green (observed execution) |

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

## Validation Audit

2026-10-20: all six tasks have producing-task-ordered automated commands and explicit failure signals. The final merged checker runs source 18, scope 25, inventory 279, decisions 88 and evidence 38 checks; self-check runs 57 asserted rejections plus positive controls, including historical worktree relocation and requirement-status lifecycle coverage. No framework installation or missing checker reference remains. The initial post-merge evidence-root failure was fixed in 25b8417 and rechecked. No additional automated coverage gap was found.

Nyquist compliance here means the planned automated sampling/rejection contract is present and green; it does not resolve the four manual-only judgments or imply commercial/security/production acceptance. Test-runtime target is operational guidance, not a benchmark guarantee.
