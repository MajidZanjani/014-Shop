> Current execution precedence: [final26October purchase-flow revision2](../../PURCHASE-FLOW-AMENDMENT.md) and STATE.md/ROADMAP.md. This file retains applicable baseline infrastructure work and qualification gates; any old next-step routing or conflicting purchase/delivery requirement is superseded. No protected/external authority changes.

---
phase: "02"
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-10-21"
---
# Phase 2 validation strategy — current protected-host contract

18 plans / 24 tasks / 14 waves. Current recorded evidence and routing are in [02-PROGRESS.md](02-PROGRESS.md), [02-COMPLETION-TRACKER.md](02-COMPLETION-TRACKER.md) and STATE/HANDOFF; historical command results below retain their dates. Plans 02-01/02-02 retain recorded development-only evidence; repository implementation through 13 now has local evidence in individual summaries. Runtime/host/full phase acceptance remains pending. This document retains the prospective full verification contract.

Use real isolated PostgreSQL, Django TransactionTestCase/independent backend connections, Python unittest and Node tests. No SQLite or missing-test/zero-count success. Existing pinned shell/dispatcher is retained. Focused commands run only after producers; quick/all remain nonzero until all required producers exist. Record actual counts/timings and positive controls before installer negatives. No real .env/host secrets.

Quick: `nix develop ./ops/nixos --command python3 scripts/check.py quick`. Full: `nix develop ./ops/nixos --command python3 scripts/check.py all`.

Evaluation/build and runtime lanes are distinct. deployment-boot remains a compatible CLI name for actual rootless lifecycle/failure cases, executed only on an independently authorized isolated off-host target. Require positive off-host identity/authorization; do not run it on mx1 or its existing development MicroVM. Missing capability is blocked/nonzero, never a skipped pass. mx1 enforcement is unproved until T11 read-only/bounded evidence.

## Task/producer verification map

| Task | Wave | Dependencies | Requirements | Commands | Status |
|---|---:|---|---|---|---|
| 02-00-01 | 3 | [02-02] | [BUILD-01, BUILD-03] | `python3 docs/product-source/verify_t01.py all; python3 docs/product-source/verify_t01.py self-check` | Local slice pass; see summary |
| 02-01-01 | 1 | [] | [BUILD-01, BUILD-02] | `python3 scripts/qualify_dependencies.py --self-test`; `python3 scripts/qualify_dependencies.py --check-review` | Retained development evidence |
| 02-01-02 | 1 | [] | [BUILD-01, BUILD-02] | `python3 scripts/qualify_dependencies.py --check-review` | Retained development evidence |
| 02-02-01 | 2 | [02-01] | [BUILD-01] | `nix develop ./ops/nixos --command python3 scripts/check.py environment` | Retained development evidence |
| 02-03-01 | 4 | [02-02, 02-00] | [BUILD-01, BUILD-03] | `nix develop ./ops/nixos --command npm --prefix frontend run build`; `nix develop ./ops/nixos --command npm --prefix frontend run test` | Local slice pass; see summary |
| 02-03-02 | 4 | [02-02, 02-00] | [BUILD-01, BUILD-03] | `nix develop ./ops/nixos --command npm --prefix frontend run check`; `nix develop ./ops/nixos --command npm --prefix frontend run test` | Local slice pass; see summary |
| 02-04-01 | 5 | [02-03] | [BUILD-01, BUILD-03] | `nix develop ./ops/nixos --command python3 scripts/check.py frontend` | Local slice pass; see summary |
| 02-05-01 | 4 | [02-02, 02-00] | [BUILD-01, BUILD-02] | `nix develop ./ops/nixos --command python3 scripts/check_python.py --qualify` | Local slice pass; see summary |
| 02-06-01 | 5 | [02-05] | [BUILD-01, BUILD-03] | `nix develop ./ops/nixos --command python3 scripts/check.py core` | Local implementation/test evidence; full qualification/review pending |
| 02-07-01 | 6 | [02-06] | [BUILD-01, BUILD-03, BUILD-04] | `nix develop ./ops/nixos --command python3 scripts/check.py core` | Local implementation/test evidence; full qualification/review pending |
| 02-08-01 | 7 | [02-07] | [BUILD-01, BUILD-03, BUILD-04] | `nix develop ./ops/nixos --command python3 scripts/check.py core` | Local implementation/test evidence; full qualification/review pending |
| 02-09-01 | 8 | [02-08] | [BUILD-01, BUILD-03] | `nix develop ./ops/nixos --command python3 scripts/check_worker.py --enqueue-only` | Local slice pass; see summary |
| 02-10-01 | 9 | [02-09] | [BUILD-01, BUILD-03] | `nix develop ./ops/nixos --command python3 scripts/check.py worker-smoke` | Local implementation/test evidence; full qualification/review pending |
| 02-10-02 | 9 | [02-09] | [BUILD-01, BUILD-03] | `nix develop ./ops/nixos --command python3 scripts/check.py worker` | Local implementation/test evidence; full qualification/review pending |
| 02-11-01 | 10 | [02-10] | [BUILD-03] | `nix develop ./ops/nixos --command python3 scripts/check.py adapters`; `nix develop ./ops/nixos --command python3 scripts/check.py worker` | Local implementation/test evidence; full qualification/review pending |
| 02-12-01 | 6 | [02-06] | [BUILD-03] | `nix develop ./ops/nixos --command python3 scripts/check.py contracts` | Local implementation/test evidence; full qualification/review pending |
| 02-13-01 | 8 | [02-04, 02-08, 02-12] | [BUILD-01, BUILD-03, BUILD-04] | `nix develop ./ops/nixos --command python3 scripts/check.py contracts` | Local implementation/test evidence; full qualification/review pending |
| 02-13-02 | 8 | [02-04, 02-08, 02-12] | [BUILD-01, BUILD-03, BUILD-04] | `nix develop ./ops/nixos --command python3 scripts/check.py boundaries` | Local implementation/test evidence; full qualification/review pending |
| 02-14-01 | 11 | [02-10, 02-11, 02-13] | [BUILD-01, BUILD-03, BUILD-04, BUILD-05, BUILD-06, BUILD-07] | `nix develop ./ops/nixos --command python3 scripts/check.py database-destination`; `database-tools`; `deployment-eval`; `deployment-build` | Local SQL236/source7/5/eval16/31 verified; full build/runtime/transport/all-write qualification pending |
| 02-14-02 | 11 | [02-10, 02-11, 02-13] | [BUILD-01, BUILD-03, BUILD-04, BUILD-05, BUILD-06, BUILD-07] | `nix develop ./ops/nixos --command python3 scripts/check.py deployment-boot` | Pending |
| 02-15-01 | 12 | [02-14] | [BUILD-04, BUILD-05, BUILD-06, BUILD-07, BUILD-08] | `nix develop ./ops/nixos --command python3 scripts/check.py deployment-profiles` | Retained local SUMMARY; actual host/ingress acceptance pending |
| 02-16-01 | 13 | [02-15] | [BUILD-01, BUILD-02] | `nix develop ./ops/nixos --command python3 scripts/check.py inventory` | Partial image/native/standard SBOM evidence; complete inventory/legal/human acceptance pending |
| 02-17-01 | 14 | [02-16] | [BUILD-01, BUILD-02, BUILD-03, BUILD-04] | `nix develop ./ops/nixos --command python3 scripts/check.py reproducibility`; `nix develop ./ops/nixos --command python3 scripts/check.py locks` | Current local payload/lock/NAR subsets verified; full OCI/qualified CI/independent comparison pending |
| 02-17-02 | 14 | [02-16] | [BUILD-01, BUILD-02, BUILD-03, BUILD-04] | `nix develop ./ops/nixos --command python3 scripts/check.py all`; `python3 docs/product-source/verify_t01.py all`; `python3 docs/product-source/verify_t01.py self-check` | Pending |

## Required boundaries and review

- 02-00 current source/locator/P-10/evidence controls precede 02-03/05; original artifact approval is not repeated.
- Frontend build/check/static HTTP/collection/island and public-only canary controls remain required. Actual browser interaction remains human skeleton review.
- Deliberate core DB-outage and worker process interruption/restart cases also require the independent off-host runner; ordinary bounded owned scratch startup/transaction checks may use the unchanged development allocation. A full lane cannot skip its required off-host fault evidence.
- Worker producer ordering remains 02-09 enqueue, 02-10 bank/leases/interruption, then 02-11 full adapter tests and worker regression. quick/all require worker and adapters separately; no future-module dependency in early worker tests.
- 02-14 real rootless images/runtime/new PG identity, absent mount/secret/wrong-database denial and aggregate process/storage containment are exercised off-host with positive controls. No native-production/host-kernel isolation claim.
- 02-15 selected profile/inventory/allowlist/full activation-impact and conditional ingress are validated offline; actual host facts are pending. Reject old cloud fields, generic protected permission, false observed templates, early DNS, protected rollback or accounting escape.
- 02-16 actual image/runtime/helper/transitive component licences/SBOM; no extension of old approval to new bytes. 02-17 two real clean payload builds, frozen installer negative controls and complete required off-host CI lanes.
- Four historical unclassified BUILD edge records remain unresolved review flags, preserved in archived EDGE-PROBE.json; no automatic engine rerun/disposition is claimed. Prior plan-check verdict is superseded for deployment. Old descriptor-less no-provisional-activation, no-false-evidence and no-spend/reused-identity constraints still hold; new source protection is additionally mandatory, not an unapproved assumption.
- Manual review checks exact source/digest scope, accessible island interaction, new image/runtime provenance and all required host/ingress/custody/operational gates. Commercial, host and protected-service action approvals are never inferred from a passing script.

## Sign-off (pending execution)

- [ ] All current focused producers run with positive counts and failure controls.
- [ ] Full source/lock/schema/public/private/real-PostgreSQL/worker/adapter evidence passes.
- [ ] Actual independent off-host rootless/runtime/cgroup/storage/lifecycle evidence passes.
- [ ] Full SBOM/licences, two clean builds and required CI lanes pass.
- [ ] Human judgments and exact deferred host/external actions are recorded.

Do not set nyquist_compliant true based on documentation review. T11/T12/T13/T14 separately close current host/storage, off-host business restore, integrated and public activation criteria.

## Current recorded checkpoint — 2026-10-21

Only8 completed local SUMMARY records remain;10 incomplete records are PARTIAL. Deployment-eval9/4 and profiles6/5 passed; locks3/8 and two independent public/backend builds4/5 passed. Native/OCI inventory and boot implementation/evidence remain incomplete. Installed SBOM collector recorded316 components/4 controls then exit2 with raw npm schema/notice/native gaps. Full all exited1 after environment/frontend at required off-host core gate, no FULL_PASS. Source six groups and71 rejections pass. See02-VERIFICATION.md and PARTIAL records; no sign-off checkbox is complete from this checkpoint.


## Policy-bound SCRAM application connection —2026-10-29

[Final source, six retained raw logs and exact scope](../../../docs/build/application-connection-2026-10-29.md): SQL3/236/17.607s, source7/5/4.302s and deployment16/31/2.222s. Twelve new connection tests plus twenty inherited restricted-observer tests are included in236. Real newly generated synthetic SCRAM credentials, peer/authentication denial, immutable policy snapshot, credential version, Django adapter-only integration, exact-wrapper/connection binding and transaction controls pass on owned disposable PostgreSQL. PGDATA/socket/runtime/admission are scratch-adapted or synthetic.

Actual inert source has14 Python modules/two SQL files and remains non-executable/unqualified; production/bank-sandbox and runtime image definitions are unchanged. Initial missing-producer and adapter/fixture failures remain retained. Approved policy issuance/custody, isolation-preserving attestation lease transport, automatic app/worker all-write, migration/bootstrap and executable independent replica integration remain open. Full14/16/17/native/source/helper/backup/notices/legal/CI/independent/runtime/recovery/human/related acceptance is still incomplete8/18. User requests complete planning synchronization, commit/sync and pause after this verified step; no parent SUMMARY/FULL_PASS.


Current pause routing —2026-10-29T11:14:41.573450+00:00: implementation a4d7e07 committed/pushed; user-requested pause at02-14 task1/2. STATE/HANDOFF.json/HANDOFF.md and .continue-here.md preserve exact next work and all incomplete qualification gates. `$gsd-resume-work` resumes; full Phase2/related acceptance remains8/18.
