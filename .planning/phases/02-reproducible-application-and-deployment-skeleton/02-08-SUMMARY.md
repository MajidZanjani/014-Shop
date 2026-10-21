---
phase: 02-reproducible-application-and-deployment-skeleton
plan: "08"
status: qualification_pending
requires: [02-07]
provides: [closed-safe-events, documented-frozen-development, four-environment-templates]
requirements-completed: []
---
# Phase 2 Plan 08: Safe events and developer setup

Closed structured logging emits enumerated events, bounded numeric status and generated correlation IDs. It never formats arbitrary messages, exceptions, request data or extras. Real health handlers emit live/ready events and startup rejection uses a fixed safe message. Actual Django security logs pass through the safe formatter. Local/synthetic nonsecret examples complete all four environment templates. docs/build.md maps package ownership and exact pinned install/check/migration/test/Gunicorn paths, synthetic scope, missing capabilities and runner authorization. Adapter lane still rejects absent/unwired producers.

## Actual evidence

Final ordinary core-local run: 4 checks, 20 tests, 6.672 seconds, zero skipped tests. Ten Django test methods plus ten real loopback HTTP cases run with new real PostgreSQL. Log tests cover arbitrary message/exception/extras, malformed event types, real Django invalid-Host errors, actual readiness handler with a synthetic exception, startup errors and positive event/status/correlation fields. Synthetic host/key/tax-business/bearer/DSN canaries are absent. Real Gunicorn logs must contain both health event types before the local marker can pass.

No real DB-outage, restart/exhaustion/recovery or external adapter test was executed. Full core remains pending/nonzero; no production acceptance. Dependent implementation may continue under explicit user instruction.

## Bounded integration adjustment

health.py/checks.py were added to the worktree scope before editing: task explicitly requires logging on actual request/startup paths. No domain behavior or shared dispatcher changed. A first test fixture patched the connection proxy cursor and interfered with SimpleTestCase teardown; replacing only the handler's module connection reference fixed the test isolation. The final run passed. Historical evidence was unchanged.
