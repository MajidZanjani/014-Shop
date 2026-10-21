---
phase: 02-reproducible-application-and-deployment-skeleton
plan: "02"
status: complete
subsystem: infra
tags: [nix, postgresql, python, node, native, tdd]
requires:
  - phase: 02-01
    provides: Exact direct-artifact review and attributable approval
provides:
  - Locked native development shell with observed reviewed runtime identities
  - Explicit fail-closed dispatcher and required aggregate lanes
  - Owned real PostgreSQL lifecycle with tested failure cleanup
affects: [02-03, 02-05, 02-06, 02-10, 02-14, 02-17]
actuals:
  tokens: 6225
  tasks: 1
  commits: 2
plan_head_before: 081d222dafe92c414375a1c3ddafe696f14ae2ac
plan_head_after: a4fa7493ef1a1ab3eaee9923e1ec9b1d8d9f50be
tech-stack:
  added: [Nixpkgs 26.05, Node 24.22.0, npm 11.19.1, Python 3.13.16, pip 26.2.1, PostgreSQL/libpq 18.6]
  patterns: [Explicit producer command table, marker and positive-count enforcement, owned temporary PostgreSQL, isolated tool configuration]
key-files:
  created:
    - ops/nixos/flake.nix
    - ops/nixos/flake.lock
    - scripts/check.py
    - scripts/dev_postgres.py
    - tests/test_check.py
    - .planning/phases/02-reproducible-application-and-deployment-skeleton/02-02-RED.json
    - .planning/phases/02-reproducible-application-and-deployment-skeleton/02-02-VERIFICATION.json
    - .planning/phases/02-reproducible-application-and-deployment-skeleton/02-02-POSTGRESQL.json
    - .planning/phases/02-reproducible-application-and-deployment-skeleton/02-02-BOOTSTRAP.json
  modified: []
key-decisions:
  - Retain one stable locked Nixpkgs revision and override native sources with the exact reviewed archives and hashes.
  - Keep native Python build and host splices on the same reviewed version/hash pair.
  - Root uses the existing unprivileged claude identity and a directly owned /tmp child; shell-parent permissions remain untouched.
  - Missing future producers are required errors; worker and adapters remain separate lanes.
patterns-established:
  - Tool versions run with disposable HOME, explicit configuration isolation and pinned executable provenance.
  - PostgreSQL uses a unique private Unix socket, ownership marker, bounded process groups and finally cleanup.
requirements-completed: [BUILD-01]
coverage:
  - id: D1
    description: Pinned native shell executes a real PostgreSQL backend query and counted environment tests.
    requirement: BUILD-01
    verification:
      - kind: integration
        ref: nix develop ./ops/nixos --command python3 scripts/check.py environment
        status: pass
    human_judgment: false
  - id: D2
    description: Dispatcher rejects missing producers, missing database tools, wrong identity and empty or incomplete results.
    requirement: BUILD-01
    verification:
      - kind: unit
        ref: tests/test_check.py#DispatcherTests
        status: pass
      - kind: other
        ref: 02-02-VERIFICATION.json#commands
        status: pass
    human_judgment: false
  - id: D3
    description: Owned real PostgreSQL cleans up after normal work, body failure and failed readiness.
    requirement: BUILD-01
    verification:
      - kind: integration
        ref: 02-02-POSTGRESQL.json#startup_failure
        status: pass
    human_judgment: false
duration: 80 min
completed: 2026-10-20
---

> Retained historical development evidence, reconciled 2026-10-21. Original execution details below remain unchanged; current 02-CONTEXT.md overrides old hosting/source assumptions. Approval covers the exact recorded artifact bytes only. This is not rootless-container, mx1, protected-resource or production acceptance. Do not rerun this completed plan to regenerate unchanged evidence. Supporting original JSON/log/checkpoint files are archived under docs/archive/2026-10-20-planning/planning/phases/02-reproducible-application-and-deployment-skeleton/.


# Phase 02 Plan 02: Pinned native development environment Summary

**A locked native shell runs 14 passing tests and a real PostgreSQL 18.6 query, with explicit producer requirements and verified scratch cleanup.**

## Performance

- Recorded interval: 2026-10-20T12:37:06Z through 2026-10-20T13:57:27Z, approximately 80 minutes. The start is the first RED commit; preceding preparation was not separately timed.
- Tasks: 1/1. Files: five task artifacts and nine RED/evidence/summary metadata files, 14 total.
- Final warm mandatory command: 1.183 seconds end to end. The environment lane reported 14 tests, two checks, zero failures and both required markers.
- Four-core acquisition attempt: 2,155.607 seconds through its last log write. Native packages completed, then the first runtime attempt exposed the repaired TMPDIR issue. The earlier two-core attempt timed out at 1,800 seconds. Acquisition and warm feedback are distinct measurements.

## Accomplishments

- Generated the actual Nix lock for stable `nixos-26.05`, revision `f3a73bcf5d1c5b75a66cf35a48957e30d41d647a`, NAR hash `sha256-qVt97ILUu2DorFGGEi+mqVuzOF8R18fQLgFkHiLrNfE=`. [Upstream download page](https://nixos.org/download/) identified 26.05 as the current stable release when checked.
- Observed actual Node 24.22.0, npm 11.19.1, Python 3.13.16, pip 26.2.1 and PostgreSQL 18.6 executables. Native paths for systemd, archive and build tools are retained in the verification record. Source overrides use the approved Node/Python/pip/PostgreSQL artifact hashes; candidate observations were not substituted for builds.
- Implemented every documented lane as an explicit required producer/command. `quick` requires environment/frontend/core/worker/adapters/contracts/boundaries; `all` additionally requires inventory, locks, reproducibility and four separately timed deployment lanes. Future missing producers fail immediately.
- Ran actual PostgreSQL SELECT, fresh-database creation, intentional body failure and invalid-startup readiness failure against the reviewed-source build. Cleanup assertions passed. The helper uses no TCP listener, private sockets, clean libpq configuration, ownership checks, bounded waits and an existing unprivileged identity when invoked as root.

## Task Commits

| Stage | Commit | Scope |
|---|---|---|
| RED | `824c39996e17e171ee9a3dbac2f198cc8434ae9a` | Required quick-lane assertion, nonfunctional seam and real RED report |
| GREEN | `a4fa7493ef1a1ab3eaee9923e1ec9b1d8d9f50be` | Five complete task artifacts and 14 passing tests |

Both task commits ran normal hooks and were pushed immediately to `origin HEAD`. This summary and retained evidence are a separate final documentation commit. No tracked files were deleted.

Accounting is measured over `plan_head_before..plan_head_after`: two task commits and ceil(chars/4) = 6,225 for the five owned task-file diff. The final documentation commit and retained logs are outside that bounded task-cost measurement.

## TDD Gate Compliance

- RED: `test_quick_requires_every_producer` actually executed and failed on the planned tuple-equality assertion: the seam returned `()` instead of seven required lanes. The complete unchanged unittest report is in `02-02-RED.json`. The GSD classifier returned `RED_EVIDENCE_OK`; semantic inspection confirmed the intended missing behavior, with no load/fixture error.
- GREEN: the same target and the full 14-test suite pass inside the pinned shell. Real PostgreSQL and the CLI failure controls also pass.
- REFACTOR: no separate refactor commit was necessary. RED precedes GREEN on this branch.

## Verification and Acceptance

`02-02-VERIFICATION.json` preserves exact argv, stdout, stderr, actual/expected exits, timings, source hashes and worktree identity for seven final commands:

| Check | Observed exit | Result |
|---|---:|---|
| Exact mandatory `nix develop ./ops/nixos --command python3 scripts/check.py environment` | 0 | ENVIRONMENT_PASS, POSTGRESQL_BACKEND, 14 tests, two checks |
| Clear SHOP_POSTGRES_BIN inside the pinned shell | 1 | Missing database rejected for the intended reason |
| Supply an invalid SHOP_NODE identity | 1 | Wrong tool identity rejected before database work |
| quick with future producers absent | 1 | Missing producer rejected |
| all with future producers absent | 1 | Missing producer rejected |
| Exact approved review-packet validation | 0 | REVIEW_READY; digest unchanged |
| git diff --check | 0 | Clean |

Every documented mode also has a missing-producer unit control. Tests cover zero counts, missing markers, skipped/failed checks, separate worker/adapter ownership, unsafe cleanup markers/symlinks, binary-path traversal, clean libpq configuration and an actual bounded sleeping subprocess.

`02-02-POSTGRESQL.json` retains the final helper hash, actual pinned driver argv, real backend output, six procedural checks, startup exit 1, unchanged error output and owned server log. The invalid `max_connections=0` option was injected only into a newly owned scratch server. Both exception and failed-readiness roots were removed. The successful environment command was repeated after the native bootstrap, satisfying tracer re-verification.

All task acceptance criteria and focused plan verification passed. Positive final `quick`/`all`, application builds, native VM boot and full phase acceptance belong to their producing plans. The requirements frontmatter copies this plan's declared `[BUILD-01]`; this completion covers its native-bootstrap contribution. The shared requirement remains governed by all declaring plans, and REQUIREMENTS.md was not changed.

## Files Created/Modified

- `ops/nixos/flake.nix` and `flake.lock`: locked native-only Linux development tools, exact reviewed source overrides, pip wheel, PostgreSQL/libpq and installer/build tools.
- `scripts/check.py`: explicit producer table, strict counts/markers, tool provenance, isolated version probes and aggregate dispatch.
- `scripts/dev_postgres.py`: owned PostgreSQL context manager; `sql()` and `create_database()` expose actual scratch operations. The latter returns Django-shaped HOST/PORT/NAME/USER/PASSWORD fields; its empty password is intentional private-socket synthetic trust.
- `tests/test_check.py`: 14 behavioral/safety tests.
- `02-02-RED.json`, `02-02-VERIFICATION.json`, `02-02-POSTGRESQL.json`, `02-02-BOOTSTRAP.json`: attributable execution evidence.
- `02-02-native-build.log`, `02-02-native-repair.log`, `02-02-final-bootstrap.log`, `02-02-final-runtime.log`: retained historical failed/interrupted/acquisition reports. Their failures are superseded by the explicit final verification record, not rewritten as successful commands.

## Decisions Made

The stable package set lagged the reviewed Node/Python patches and used a different PostgreSQL archive transport. Keep its supported native recipes and pin the exact reviewed source archives. Preliminary stock-Nixpkgs PostgreSQL smoke observations do not qualify the final reviewed archive; the latter was rebuilt and independently tested.

Native Python splices explicitly share the reviewed source version/hash. This shell makes no cross-compilation claim. Root uses existing `claude` and pinned `runuser`; ordinary non-root callers run directly. Scratch state is a unique direct `/tmp` child, avoiding traversal through root-private shell TMPDIR without changing parent permissions.

Version probes use disposable HOME/cwd, explicit npm configuration/cache paths and `PIP_CONFIG_FILE=os.devnull`, which disables pip configuration loading per [pip's official configuration documentation](https://pip.pypa.io/en/stable/topics/configuration/#pip-config-file). No credentials are required.

## Deviations from Plan

1. **[Rule 3 - Blocker] Default sandbox mount failure.** The initial bwrap operation could not access this worktree. Scoped authorized elevated operations succeeded. No automatic-review denial was retried or bypassed. No task-file scope expansion.
2. **[Rule 1 - Bug] Native Python splice mismatch.** Qualification exposed the new hash paired with the old build-time interpreter source version. Fixed native splices in `flake.nix`; retained the failed hash report. Exact reviewed hashes remained enforced. Verified by actual Python/pip builds and final environment command; committed in GREEN.
3. **[Rule 1 - Bug] Root-private Nix TMPDIR.** The first built-shell runtime failed initdb because the existing unprivileged test UID could not traverse the shell parent. Changed only helper-owned scratch placement and tests. Final real PostgreSQL and all cleanup paths pass; committed in GREEN.

Total deviations: three auto-fixed, with no architectural or external-operation scope change.

## Issues Encountered

Native compilation dominated acquisition time. The first overly concurrent attempt was stopped; a bounded two-core attempt timed out; the four-core attempt completed native packages. All failure/acquisition logs remain available. The final mandatory command succeeds from the actual locked shell. No failed native attempt is credited as a passing environment run.

## Known Stubs

None in the shipped deliverables. Absent future lane producers are explicit required errors with ownership assigned by the plan graph.

## User Setup Required

None for this local/synthetic slice. No accounts, services, real credentials or external resources were provisioned.

## Next Phase Readiness

Ready for 02-03 and 02-05. Frontend compatibility, frozen Python closures, full inventories/licences, deployment evaluate/build/boot and complete CI remain with their producing plans. BUILD-01's flagged edge assumption remains unclassified/unresolved; no predicate or approval was invented. Earlier dependency-review findings and P-01–P-12 remain unchanged. This is local native/synthetic evidence and grants no bank, OVH, DNS/TLS or production acceptance.

STATE.md, ROADMAP.md, REQUIREMENTS.md, config, other plans and immutable source artifacts were untouched.

## Self-Check: PASSED

All five task artifacts exist and match retained tested SHA-256 identities; both task commits are ancestors of HEAD and pushed. The approved candidate digest remains `136610b07612762d390b3b3c234ff1ef3f6dc6b0e44a69a2abc646d9106b51bd`. Fourteen tests, seven final command controls and real PostgreSQL failure cleanup passed. No skipped mandatory verification, uncommitted source change or owned running server remains.
