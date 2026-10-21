---
phase: 02-reproducible-application-and-deployment-skeleton
plan: "11"
status: qualification_pending
requires: [02-10]
provides: [fake-bank-scenarios, synthetic-mail-capture, bounded-local-storage, outbound-denied-adapter-tests]
requirements-completed: []
---
# Phase 2 Plan 11: Integrated synthetic adapters

The committed-claim worker invokes local byte storage, synthetic .invalid mail capture and deterministic fake-bank receipt outside claim locks. Storage uses owned private directory descriptors, generated identities, bounded bytes, exclusive/no-follow opens and closed traversal rules. Mail is bounded/in-memory/resettable with stable effect identity and rejects real recipients/header injection. Fake bank explicitly distinguishes ok/rejected/unknown/timeout/malformed cases; none represents verified money. All adapters reject production-shaped use. No real message, S3 emulator or live bank call.

## Actual local evidence

Final adapters dispatcher passed 3 checks/6 tests in 4.733 seconds, using fresh migrated PostgreSQL and actual fake calls in a separate network namespace. An actual IP connection fails; HTTP/SMTP/object/DNS entry-point guard attempts also fail. Positive integrated worker execution reaches completion/one receipt. Fixtures exercise repeat/conflict identities, all named scenarios, capture reset and invalid recipients/size, storage round-trip/reset/traversal/symlink/oversize rejection and fake-mode restrictions.

Then worker-smoke reran through the expanded service path: 6 checks/24 tests in 8.306 seconds. Distinct-session ownership, fencing, blocked-fake lock release and both mutation controls still pass. Full worker remains nonzero pending off-host interruption; no forced interruption/restart was executed. This keeps the plan's required regression qualification pending rather than claiming full completion. BUILD/production acceptance remains incomplete.

## Integration correction

The original plan claimed producer changes were unnecessary, but its inherited adapter producer explicitly refused execution until 02-11. scripts/check_backend.py was included in the worktree allowlist before wiring the real mandatory test module, real PG migration and network-isolated invocation with positive/no-skip counts. No shared dispatcher change or dependency addition. Current user credential policy is recorded on main in PROJECT/02-CONTEXT: resources use .env when needed; these tests require no real credentials and do not read .env.
