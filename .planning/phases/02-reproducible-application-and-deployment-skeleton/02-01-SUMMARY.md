---
phase: 02-reproducible-application-and-deployment-skeleton
plan: "01"
status: complete
subsystem: build
tags: [dependencies, provenance, inert-review, checkpoint]
requires:
  - phase: "01"
    provides: Accepted source/documentation baseline
provides:
  - Exact direct-artifact packet with attributable human approval
affects: [02-02, 02-03, 02-05, 02-16]
actuals:
  tokens: 426774
  tasks: 2
  commits: 5
plan_head_before: abe44f866bafc46ef1691f817a3f83b7e282930a
plan_head_after: 851e389cab4228442ff1c4fe4d7db96b978b62d2
tech-stack:
  added: []
  patterns: [Standard-library inert downloads and archive inspection without extraction]
key-files:
  created: [scripts/qualify_dependencies.py, tests/test_qualify_dependencies.py, docs/build/dependency-candidates.json, docs/evidence/t02/dependency-review.json, docs/evidence/t02/dependency-review.md]
  modified: []
key-decisions:
  - Research versions remain candidates; current Node 24.22.0 and Python 3.13.16 selected from upstream listings.
  - Retain TypeScript 6.0.3 and reject 7.0.2 against actual checker peer metadata.
requirements-in-scope: [BUILD-01, BUILD-02]
requirements-completed: []
coverage:
  - id: D1
    description: Inert direct-artifact packet integrity and rejection controls
    verification:
      - kind: unit
        ref: python3 -B scripts/qualify_dependencies.py --self-test
        status: pass
      - kind: other
        ref: python3 -B scripts/qualify_dependencies.py --check-review
        status: pass
    human_judgment: true
    rationale: Task 2 explicitly requires attributable approval of the exact digest before installation.
duration: 14 min
completed: 2026-10-20
---

# Phase 02 Plan 01: Exact dependency artifact review Summary

**Twenty inert direct artifacts have a verified candidate-set digest and an attributable explicit human approval; no packages were installed.**

## Completion and evidence

- Tasks: 2/2. Five task files plus checkpoint/summary metadata; RED evidence preserved.
- User response: `approve`, attributed to the user in this conversation, recorded `2026-10-20T12:30:19Z`.
- Approved SHA-256: `136610b07612762d390b3b3c234ff1ef3f6dc6b0e44a69a2abc646d9106b51bd`; validated before recording and unchanged afterward.
- PASS: self-test, 7 tests; check-review, REVIEW_READY with 20 artifacts; approval-record assertions; git diff --check; retained root/branch and all supplied ancestors.
- Requirements-completed remains []: BUILD-01/BUILD-02 are only partially supported by this limited review packet; bootstrap, full inventory and application acceptance belong to later plans.
- Started: first RED commit 2026-10-20T12:17:34Z; completed: 2026-10-20T12:31:19Z.

## Bounded commit accounting

`plan_head_before` is the original base. `plan_head_after` is the exact pre-summary HEAD. `actuals.commits: 5` is measured by git rev-list over those bounds: two Task 1 commits, one halted checkpoint metadata commit, Task 2 approval commit and one correction. Final summary metadata commit is excluded from this bounded count; including that commit yields six commits after the original base. Actuals tokens are ceil(chars/4) of the five owned task-file diff, including retained upstream licence text.

| Stage | Commit |
|---|---|
| Task 1 RED | eb80af6b2df7cfd16f9ddaeb7799efebc03c9bfa |
| Task 1 GREEN | 6210f14100d339698b829ba4a039aedf59179920 |
| Halted checkpoint metadata | 15cd11c04c4157d42923f607a9c5086e4c9452ec |
| Task 2 approval | e97fa6ab139ef4667b3d51609592d04f635ab130 |
| Generated Markdown correction | 851e389cab4228442ff1c4fe4d7db96b978b62d2 |

All commits pushed immediately with normal hooks. Shared STATE/ROADMAP/REQUIREMENTS/config and source were untouched by this continuation. No installs, recollection or Task 1 repetition.

## Continuation deviations and limitations

[Rule 1 - Bug] Appending approval to generated Markdown caused check-review to report Markdown/JSON mismatch. Restored the original deterministic Markdown in 851e389; check-review passes. Its awaiting-response prose is historical generated review evidence; JSON human_response and resolved checkpoint record current approval. No qualifier source changes were authorized.

[Rule 3 - Blocker] Default bwrap still could not access the retained worktree. Scoped require_escalated repository operations succeeded. Automatic review rejected a combined read containing the host skill path; that path was not retried or bypassed. Supplied execution instructions were used.

Unresolved React DOM registry/archive scripts, signer authenticity, native/transitive qualification, legal judgment and runtime/build findings remain unchanged. Approval covers the exact reviewed artifact set only; no business/legal/provider/certification or operational approval follows. Next producing plans own bootstrap and actual compatibility proof. No external setup performed here.

## Self-Check: PASSED

All five owned task artifacts exist; supplied task/checkpoint commits are ancestors; exact digest and attributable response match; seven tests and packet checks pass. Checkpoint is resolved without deleting its historical evidence.

## Historical halted summary (preserved verbatim; superseded by completion above)


# Phase 02 Plan 01: checkpoint summary — NOT COMPLETE

**Twenty exact direct artifacts are hashed and inspected without execution; Task 2 is awaiting an explicit human response.**

## Accomplishments

- Task 1 completed: 20 artifacts, including all ten research SUS rows (11 package identities because React/DOM are paired), 459 licence-text entries and actual peer/interpreter declarations.
- Seven offline tests pass; missing hash, wrong upstream, missing licences/hooks, empty/duplicate/tampered packets, incompatible peers/interpreters and untrusted URLs are rejected.
- `--collect` fetched inert archives and public metadata only. Nothing downloaded was extracted to disk, imported, installed, built or executed.

## Task Commits

| Task / stage | Commit | Files |
|---|---|---|
| 1 RED | eb80af6b2df7cfd16f9ddaeb7799efebc03c9bfa | tests/test_qualify_dependencies.py; scripts/qualify_dependencies.py initial nonfunctional seam |
| 1 GREEN | 6210f14100d339698b829ba4a039aedf59179920 | All five owned task files |

Both commits pushed to origin HEAD on worktree-agent-p02-01-1792498547, with normal hooks. No deletions. The measured actuals above cover the two task commits, before this metadata close-out. Diff size includes copied upstream licence texts; it is not a harness token count.

## TDD evidence

`02-01-RED.json` preserves the actual single-target unittest report and semantic assessment. GSD returned `RED_EVIDENCE_OK`: `test_exact_artifact_contract` executed and failed on `None != 1`, the planned successful-validation assertion. An initial file-existence probe was superseded; it did not authorize implementation. GREEN: seven tests, zero failures, `QUALIFIER_TESTS_PASS tests=7`. No separate refactor was needed.

## Verification and acceptance

- PASS: `python3 -B scripts/qualify_dependencies.py --self-test` — seven executed tests.
- PASS: `python3 -B scripts/qualify_dependencies.py --check-review` — `REVIEW_READY`, 20 artifacts.
- PASS: complete direct set and 11 SUS package identities counted; TS/checker and tool bootstrap decisions recorded; no tested-compatibility claim.
- PASS: `git diff --check`; cwd/branch and expected-base ancestry verified before commits.
- Task 2 human acceptance: NOT SATISFIED; human_response is null. No package installation authorization recorded.

## Exact review identity

`136610b07612762d390b3b3c234ff1ef3f6dc6b0e44a69a2abc646d9106b51bd`

Review paths: `docs/evidence/t02/dependency-review.md`, `docs/evidence/t02/dependency-review.json`, `docs/build/dependency-candidates.json`.

## Decisions and findings

- React DOM registry scripts include `start: node server.js`; its downloaded package manifest has no scripts. Both observations are retained as an unresolved human review finding. Registry existence or recency is not compromise evidence.
- npm has a `prepack` script; direct source archives contain build/configure files. JSON retains direct npm commands, source build-file hashes and licence texts. These were not executed. Transitive hook/security/licence closure remains later work.
- Gunicorn registry declares Python >=3.10 versus installation documentation 3.12+; selected 3.13 satisfies both declarations, with actual runtime tests pending.
- Registry/checksum agreement does not authenticate signers. Native closures, transitive locks/SBOM, runtime/build tests and legal judgment remain explicit future obligations.
- Current official release notes for Node/Python/Django/PostgreSQL were inspected; selected Python source SHA-256 matches its official release-page checksum. No vulnerability-free conclusion was inferred.

## Deviations from Plan

**[Rule 3 — blocker] Sandbox mount failure:** default execution failed before running commands because bwrap could not access the supplied worktree. Scoped commands used authorized require_escalated access; no auto-review denial occurred.

**[Rule 2 — evidence completeness] Registry/archive script difference:** preserved both script observations and an unresolved finding instead of hiding it or treating the registry as the artifact manifest. No change to the human gate or selected package identity.

## Checkpoint / resume

Resume at **Task 2 / 02-01-02**, blocking-human. Present the exact digest and review packet, obtain actual attributable approval or requested changes, then record only that real response and digest. Re-run packet validation. Do not redo Task 1 or install packages before the gate is satisfied. No completed-plan or milestone status is claimed. Shared STATE/ROADMAP/REQUIREMENTS/config remain parent-owned and unchanged.

## Self-Check: PASSED for checkpoint scope only

Five task files exist; both task commits are reachable and pushed. Task 1 checks pass. Task 2 and complete-plan acceptance remain pending.
