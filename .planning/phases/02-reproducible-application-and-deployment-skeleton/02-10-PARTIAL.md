---
phase: 02-reproducible-application-and-deployment-skeleton
plan: "10"
status: qualification_pending
requires: [02-09]
provides: [leased-synthetic-worker, fenced-completion, independent-session-tests, prepared-interruption-test]
requirements-completed: []
---
# Phase 2 Plan 10: Leased worker; interruption qualification pending

The foreground worker claims one row with skip-locked short transactions, database-time finite leases and random fencing tokens. Adapter work follows commit; completion conditionally checks current token, effect identity and unexpired lease. Attempts/poll/lease are finite. SIGTERM requests bounded loop shutdown. A deterministic fake receipt has a stable unique effect identity separate from claims; it is synthetic and implies no exactly-once financial guarantee. No commerce outbox or real payment was added.

## Actual local evidence

Final pinned dispatcher worker-smoke: 6 checks, 24 tests, zero failures, 8.235 seconds. Counts include 11 enqueue cases, actual run_worker --once/rerun and argument controls, seven real PostgreSQL transaction tests and two expected-failing mutation tests in bounded disposable source copies. Distinct real backend PIDs, simultaneous claim ownership, lease expiry/takeover, stale completion, outer transaction/autocommit rejection and a blocked deterministic fake with independently acquired NOWAIT row lock are exercised. Stable receipt reruns remain one row. Broken fencing and a claim-row lock held around adapter work are both rejected by their focused tests. No source mutation persists.

A separate three-assertion control confirmed full worker without authorization returns nonzero PENDING_OFF_HOST and no WORKER_PASS. The inherited core full lane remains pending too.

## Prepared but unexecuted

The offhost-tagged test creates a probe, starts a child using the exact synthetic test database, exits that child after a durable fake receipt/before completion, then reclaims and completes with one receipt. It has **not executed here**. Local producer explicitly selects ordinary transaction tests; full worker requires operator authorization matching actual independent machine/commit and permitted_actions=["owned-synthetic-worker-interruption"], then requires the interruption test. No runner authorization record was created. This is deliberate pending qualification, not a skipped full success.

## Integration scope and fixes

The existing runner validator gained a parameter for the exact permitted action; PostgreSQL outage remains its unchanged default. scripts/check_backend.py was added to the worktree allowlist before this bounded reuse. No protected-host write. The first smoke query needed parentheses around JSON extraction; actual PostgreSQL exposed and verified the fix. Parent scratch remains owned/short; no shared resources were cleaned or resized.
