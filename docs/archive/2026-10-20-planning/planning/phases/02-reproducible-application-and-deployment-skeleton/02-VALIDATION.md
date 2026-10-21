---
phase: "02"
slug: "reproducible-application-and-deployment-skeleton"
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-10-20"
---

# Phase 2 — Validation Strategy

This is a prospective contract aligned with 17 bounded plans/23 tasks. No application checks have run. Status stays draft, nyquist_compliant false and wave_0_complete false until actual execution/audit. Planning does not authorize implementation or external operations.

## Test Infrastructure

Use Django TransactionTestCase with independent real PostgreSQL connections, Python unittest and Node's test runner. No SQLite fallback. A missing PostgreSQL service fails the required lane rather than skipping it. Use the pinned development shell and exact runtime/tool locks created during execution.

Quick command: `nix develop ./ops/nixos --command python3 scripts/check.py quick`.
Full command: `nix develop ./ops/nixos --command python3 scripts/check.py all`.
Both are proposed interfaces produced by 02-02-01. Full verification reports positive test/check counts and cannot succeed if PostgreSQL, native build/boot, a required producer or tests are unavailable. No tools are invoked before their producing task. Installer/tool provenance and clean positive controls precede corrupted-hash tests.

## Sampling Rate

After each task run its focused command. After a wave run affected produced lanes; do not invoke quick/all before every required producer exists. Target focused warm feedback under 60 seconds; record actual timing, not invented results. Final quick covers environment/frontend/core/worker/adapters/contracts/boundaries with positive counts; full includes inventory, real installer negative controls, two clean builds and separate deployment evaluate/build/boot/profile results. Report warm checks, initial artifact acquisition/installation, two-build reproducibility and Nix evaluate/build/VM durations separately. Builds/VM/full may exceed 60/180 seconds and are required explicit lanes; a timeout cannot become a pass.

## Per-Task Verification Map

Every command runs from repository root. All are proposed interfaces, Exists=No/status=pending until execution. The pinned shell/dispatcher is produced by 02-02-01; pre-review qualifier uses existing Python stdlib. Every automated command has its adjacent observable fails_when in its task. Native boot is mandatory, with no eval-only/skip pass.

| Task | Requirements | Automated command(s) | Producer dependency | Threat references |
|---|---|---|---|---|
| 02-01-01 | BUILD-01, BUILD-02 | `python3 scripts/qualify_dependencies.py --self-test`; `python3 scripts/qualify_dependencies.py --check-review` | Existing Python/source baseline; producer in same task when new | T-02-24, T-02-25, T-02-26, T-02-SC |
| 02-01-02 | BUILD-01, BUILD-02 | `python3 scripts/qualify_dependencies.py --check-review` | Existing Python/source baseline; producer in same task when new | T-02-24, T-02-25, T-02-26, T-02-SC |
| 02-02-01 | BUILD-01 | `nix develop ./ops/nixos --command python3 scripts/check.py environment` | 02-01; producer in same task when new | T-02-27, T-02-28, T-02-29, T-02-SC |
| 02-03-01 | BUILD-01, BUILD-03 | `nix develop ./ops/nixos --command npm --prefix frontend run build`; `nix develop ./ops/nixos --command npm --prefix frontend run test` | 02-02; producer in same task when new | T-02-30, T-02-31, T-02-32, T-02-SC |
| 02-03-02 | BUILD-01, BUILD-03 | `nix develop ./ops/nixos --command npm --prefix frontend run check`; `nix develop ./ops/nixos --command npm --prefix frontend run test` | 02-02; producer in same task when new | T-02-30, T-02-31, T-02-32, T-02-SC |
| 02-04-01 | BUILD-01, BUILD-03 | `nix develop ./ops/nixos --command python3 scripts/check.py frontend` | 02-03; producer in same task when new | T-02-33, T-02-34, T-02-35, T-02-SC |
| 02-05-01 | BUILD-01, BUILD-02 | `nix develop ./ops/nixos --command python3 scripts/check_python.py --qualify` | 02-02; producer in same task when new | T-02-36, T-02-37, T-02-38, T-02-SC |
| 02-06-01 | BUILD-01, BUILD-03 | `nix develop ./ops/nixos --command python3 scripts/check.py core` | 02-05; producer in same task when new | T-02-39, T-02-40, T-02-41, T-02-SC |
| 02-07-01 | BUILD-01, BUILD-03, BUILD-04 | `nix develop ./ops/nixos --command python3 scripts/check.py core` | 02-06; producer in same task when new | T-02-42, T-02-43, T-02-44, T-02-SC |
| 02-08-01 | BUILD-01, BUILD-03, BUILD-04 | `nix develop ./ops/nixos --command python3 scripts/check.py core` | 02-07; producer in same task when new | T-02-45, T-02-46, T-02-47, T-02-SC |
| 02-09-01 | BUILD-01, BUILD-03 | `nix develop ./ops/nixos --command python3 scripts/check_worker.py --enqueue-only` | 02-08; producer in same task when new | T-02-48, T-02-49, T-02-50, T-02-SC |
| 02-10-01 | BUILD-01, BUILD-03 | `nix develop ./ops/nixos --command python3 scripts/check.py worker-smoke` | 02-09; producer in same task when new | T-02-51, T-02-52, T-02-53, T-02-SC |
| 02-10-02 | BUILD-01, BUILD-03 | `nix develop ./ops/nixos --command python3 scripts/check.py worker` | 02-09; producer in same task when new | T-02-51, T-02-52, T-02-53, T-02-SC |
| 02-11-01 | BUILD-03 | `nix develop ./ops/nixos --command python3 scripts/check.py adapters`; `nix develop ./ops/nixos --command python3 scripts/check.py worker` | 02-10; producer in same task when new | T-02-54, T-02-55, T-02-56, T-02-SC |
| 02-12-01 | BUILD-03 | `nix develop ./ops/nixos --command python3 scripts/check.py contracts` | 02-06; producer in same task when new | T-02-57, T-02-58, T-02-59, T-02-SC |
| 02-13-01 | BUILD-01, BUILD-03, BUILD-04 | `nix develop ./ops/nixos --command python3 scripts/check.py contracts` | 02-04, 02-08, 02-12; producer in same task when new | T-02-60, T-02-61, T-02-62, T-02-SC |
| 02-13-02 | BUILD-01, BUILD-03, BUILD-04 | `nix develop ./ops/nixos --command python3 scripts/check.py boundaries` | 02-04, 02-08, 02-12; producer in same task when new | T-02-60, T-02-61, T-02-62, T-02-SC |
| 02-14-01 | BUILD-01, BUILD-03, BUILD-04 | `nix develop ./ops/nixos --command python3 scripts/check.py deployment-boot` | 02-10, 02-11, 02-13; producer in same task when new | T-02-63, T-02-64, T-02-65, T-02-66, T-02-SC |
| 02-14-02 | BUILD-01, BUILD-03, BUILD-04 | `nix develop ./ops/nixos --command python3 scripts/check.py deployment-boot` | 02-10, 02-11, 02-13; producer in same task when new | T-02-63, T-02-64, T-02-65, T-02-66, T-02-SC |
| 02-15-01 | BUILD-04 | `nix develop ./ops/nixos --command python3 scripts/check.py deployment-profiles` | 02-14; producer in same task when new | T-02-67, T-02-68, T-02-69, T-02-70, T-02-SC |
| 02-16-01 | BUILD-01, BUILD-02 | `nix develop ./ops/nixos --command python3 scripts/check.py inventory` | 02-15; producer in same task when new | T-02-71, T-02-72, T-02-73, T-02-74, T-02-SC |
| 02-17-01 | BUILD-01, BUILD-02, BUILD-03, BUILD-04 | `nix develop ./ops/nixos --command python3 scripts/check.py reproducibility`; `nix develop ./ops/nixos --command python3 scripts/check.py locks` | 02-16; producer in same task when new | T-02-75, T-02-76, T-02-77, T-02-78, T-02-SC |
| 02-17-02 | BUILD-01, BUILD-02, BUILD-03, BUILD-04 | `nix develop ./ops/nixos --command python3 scripts/check.py all`; `python3 docs/product-source/verify_t01.py all`; `python3 docs/product-source/verify_t01.py self-check` | 02-16; producer in same task when new | T-02-75, T-02-76, T-02-77, T-02-78, T-02-SC |

Explicit dispatcher mapping remains in 02-02 only. Direct qualification flags are scripts/check_python.py --qualify (02-05), scripts/check_worker.py --enqueue-only (02-09), plus the pre-review qualifier flags. Later scripts implement named lanes without rewriting the dispatcher. Early core uses counted real HTTP/DB assertions; 02-07 adds mandatory core module tests before later core/quick/all. Each declared task produces all tools/files it invokes or depends on the producing plan. Missing producer/tool, zero assertions/tests, required DB/VM unavailable, unsafe/live output or absent PASS marker is nonzero.

Worker producer order is explicit: 02-10-02 requires only migrated CLI smoke, existing fake-bank assertions and worker lease/contention/interruption tests. It never imports shop.adapters.tests or future mail/storage modules. 02-11-01 produces the full adapter test module, runs the separate adapters lane through the existing check_backend.py producer, then reruns worker as a regression against the expanded service path. Final quick/all require both lanes separately; missing adapters remain nonzero rather than skipped. No script ownership, plan dependency or wave changed.

## Wave 0 Requirements

- [ ] First producing plan creates the check dispatcher and focused test entry points before dependent commands are used.
- [ ] Pin build/runtime/tools and supply a real isolated PostgreSQL lifecycle helper with bounded readiness and safe ownership checks.
- [ ] Create synthetic test fixtures and framework configuration; no real `.env` reads.
- [ ] Add each final plan task ID, unique threat reference and producer dependency to this map; no three consecutive tasks lack automated feedback.
- [ ] Fail on missing tests, zero counts, unavailable required tools/services, silently skipped database checks, unresolved schema references or command errors.
- [ ] Actual npm integrity, Python transitive hash locks, installer/bootstrap identities and Nixpkgs lock are generated and qualified at execution, not copied as approved research candidates.
- [ ] Standard raw npm/CycloneDX Python SBOMs, native closure and complete actual licence evidence are produced; unknown legal conclusions remain findings.
- [ ] Two independent clean builds compare real public/backend payload bytes; raw SBOM serial/time fields remain preserved separately.
- [ ] Nix evaluation, complete derivation build and executed VM service cases each have distinct positive evidence; evaluation alone cannot satisfy boot.

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

## Dependency and Wave Graph

| Plan | Needs | Executable slice | Tasks | Files | Wave |
|---|---|---|---|---|---|
| 02-01 | T01 source baseline | Concrete dependency review | 2 | 5 | 1 |
| 02-02 | 02-01 | Pinned native development environment | 1 | 5 | 2 |
| 02-03 | 02-02 | Static Astro collection and React island | 2 | 9 | 3 |
| 02-04 | 02-03 | Public frontend build boundary | 1 | 3 | 4 |
| 02-05 | 02-02 | Frozen Python runtime and tools | 1 | 6 | 3 |
| 02-06 | 02-05 | Django real-PostgreSQL health path | 1 | 9 | 4 |
| 02-07 | 02-06 | Fail-closed Django environment configuration | 1 | 9 | 5 |
| 02-08 | 02-07 | Safe logs and developer environment examples | 1 | 7 | 6 |
| 02-09 | 02-08 | Migrated synthetic enqueue path | 1 | 9 | 7 |
| 02-10 | 02-09 | Leased worker and PostgreSQL ownership proof | 2 | 8 | 8 |
| 02-11 | 02-10 | Mail and storage fake-boundary expansion | 1 | 6 | 9 |
| 02-12 | 02-06 | Versioned actual-response API and probe contracts | 1 | 6 | 5 |
| 02-13 | 02-04, 02-08, 02-12 | Environment/artifact schemas and cross-boundary proof | 2 | 9 | 7 |
| 02-14 | 02-10, 02-11, 02-13 | Native boot, mount and credential isolation | 2 | 7 | 10 |
| 02-15 | 02-14 | Deployment profiles and image qualification plan | 1 | 5 | 11 |
| 02-16 | 02-15 | Actual component licences and SBOM | 1 | 6 | 12 |
| 02-17 | 02-16 | Two clean builds and complete CI evidence | 2 | 8 | 13 |

All owned files, including conventional initializers, count toward scope; each plan declares fewer than ten files. Single-task tracer slices preserve the original work without artificial task multiplication. Same-wave sets are disjoint. Existing shared dispatcher is written only by 02-02; shared settings/flake/docs/producer modifications are sequenced by explicit dependencies. Estimate factor remains 1, sample_count 0, confidence low.

## Multi-Source Coverage Audit

| Source | Item | Covering plan/task | Status and limits |
|---|---|---|---|
| GOAL | Reproducible static/Django/worker/real PostgreSQL builds and CI | 02-02/03/05/06/09/10/17 | COVERED |
| REQ | BUILD-01 | 02-02/03/04/05/06/07/08/09/10/14/17 | COVERED |
| REQ | BUILD-02 actual transitive/native licences/SBOM | 02-01/05/16/17 | COVERED; actual evidence required |
| REQ | BUILD-03 fakes and versioned contracts | 02-07/08/09/10/11/12/13 | COVERED |
| REQ | BUILD-04 native/image/secrets/environment/variants | 02-07/08/14/15 | COVERED; actual cloud remains T11 |
| RESEARCH | Exact supported artifacts, TS6/checker compatibility and one SUS review | 02-01/02/03/05 | COVERED; no candidate proof invented |
| RESEARCH | Missing pip/PostgreSQL bootstrap, frozen full tool/runtime closure | 02-02/05 | COVERED |
| RESEARCH | Static build-time collection/island/public allowlist/canaries | 02-03/04 | COVERED |
| RESEARCH | Conventional Django, safe startup/logs, four environments | 02-06/07/08 | COVERED |
| RESEARCH | Persisted short leases, independent real PG sessions, fenced stable fake identity | 02-09/10 | COVERED; commercial outbox/payment T05/T08 |
| RESEARCH | Fake bank/mail/storage, deterministic faults, active outbound denial, path safety | 02-10/11 | COVERED |
| RESEARCH | OpenAPI3.1.1/Schema2020-12/offline ref/format validation and full-schema ownership | 02-12/13 | COVERED; actual full product schemas T03 |
| RESEARCH | Runtime credentials/hardened native units/separate mount/VM failure cases | 02-14 | COVERED; real boot cannot skip |
| RESEARCH | B2-7/B3-8 profiles and unexecuted exact image/provider qualification | 02-15 | COVERED; account proof T11 |
| RESEARCH | Actual SBOM/native/transitive licence text coverage | 02-16 | COVERED; legal findings remain explicit |
| RESEARCH | Two real clean payload builds, installer negatives, CI and evidence timing/classes | 02-17 | COVERED |
| RESEARCH | Four Open Questions | RESEARCH planning dispositions with exact tasks/gates | RESOLVED planning ownership only; execution facts unobserved |
| CONTEXT | No Phase2 CONTEXT/D-NN decisions | Source/PROJECT govern every plan | NOT APPLICABLE; none invented |
| SOURCE | Complete T02 outputs/acceptance/evidence and proposal environment/repository structure | All 17 bounded plans | COVERED; source bytes/history unchanged |
| PATTERN | Bounded checks/hash identity analog | 02-05/12/13/16/17 actions name docs/product-source/verify_t01.py | COVERED; maintained validators/SBOM/installers retained |
| PATTERN | Service/evidence document analog | 02-08/13/16/17 actions name docs/implementation-evidence.md | COVERED; no historical evidence rewrite |
| EDGE | BUILD-01 unclassified/unresolved | 02-02 flagged assumptions | FLAGGED; no invented predicate/backstop |
| EDGE | BUILD-02 unclassified/unresolved | 02-16 flagged assumptions | FLAGGED; no invented predicate/backstop |
| EDGE | BUILD-03 unclassified/unresolved | 02-13 flagged assumptions | FLAGGED; no invented predicate/backstop |
| EDGE | BUILD-04 unclassified/unresolved | 02-15 flagged assumptions | FLAGGED; no invented predicate/backstop |
| PROHIBITION | No provisional activation/competing catalog | 02-13 must_haves.prohibitions | Original canonical projection, unresolved/descriptor-less |
| PROHIBITION | No silent spend/billing/reused identities | 02-15 must_haves.prohibitions | Original canonical projection, unresolved/descriptor-less |
| PROHIBITION | No synthetic evidence passed off as provider/production proof | 02-17 must_haves.prohibitions | Original canonical projection, unresolved/descriptor-less |

No in-scope source/requirement/research/decision/probe item is omitted. Full catalog/product UI/commercial model/authorization/payment/actual bank/cloud/recovery retain T03/T04/T05/T06/T08/T09/T11/T12 ownership respectively. Every plan retains ASVS5 L1 threat modeling, unique non-SC threat IDs and blocking high severity. The existing single consolidated pre-install review gate is unchanged.

## Probe and Capability Accounting

Edge engine output is retained unchanged: applicable 4, unclassified 4, unresolved 4, resolved 0. No edge is auto-dismissed or converted into backstop. Adversarial prohibition recall considered product activation, fabricated evidence, operational spending, privacy/logging, secrets, installation, unsafe claims, error handling, path safety and retries; precision retained the three bespoke intent constraints above. Routine correctness was dropped, and canon injection/path/privacy controls were referred to threat models and $gsd-secure-phase. projectProhibitions was actually invoked on all three kept records: surfaced 3 = authored 3, all unresolved with no check_* descriptor; downstream disposition remains flagged-unverified. Four edge records = four explicit flagged assumptions.

Planner contributions were consumed verbatim from the plan:pre payload. Actual assumption-delta detector returned true (fallback/configurable/chosen); 02-15 records promote deployment profile. Actual API detector returned true on generic framework/API and negated provider-SDK prose; scope review confirms no external API integration. A reasoned COVERAGE.md declaration is supplied by the orchestrator, rather than fabricated provider capabilities. Schema detector's listed ORM patterns do not apply; Django migrate --noinput and pending-migration checks are explicitly required before worker verification. UI gate had no frontend implementation evidence and did not block; no product UI-SPEC or AI integration is applicable.
