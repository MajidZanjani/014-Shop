# Plan07-02 separate-process command smoke — partial

Runtime remains ccab85a; this slice changes command regression tests only. No phase/plan completion credit.

Two new real-PostgreSQL TransactionTestCase regressions launch backend/manage.py run_prepared_archive through the frozen sys.executable. Explicit child environment copies only pinned PATH/LD_LIBRARY_PATH, supplies synthetic settings/fake adapters and NAME/USER/HOST/PORT from the actual test connection, and excludes ambient provider/credential/libpq-service configuration. subprocess.run captures output, bounds each child to15 seconds and kills/waits on timeout. No shell, queue loop or automatic retry.

Success returns the exact fixed safe JSON with empty stderr and commits one claim/verification visible to the parent. Repeating the command yields the exact generic error and preserves original IDs and every archive byte. Invalid authorization, unknown destination, missing root and revoked authority return exactly the safe error with empty stdout, create no claims/verification and preserve the original root bytes. Exact output assertions exclude private paths/UUIDs/tokens/hashes implicitly.

Initial full and targeted runs failed because the scrubbed environment omitted pinned PATH required for libpq discovery; no pass claimed. After adding only that runtime tool path, targeted five-command tests pass (19 combined observations9.937s). Complete ordinary lane: CORE_LOCAL_PASS checks5 tests248 duration59.426s,234 Django plus14 Gunicorn observations. Owned PostgreSQL18.6/UTF8; migration application/no-drift passes. Source /nix/store/mhq0irgiqjjqwh2ry1mzqzwjkda5p6py-shop-python-source has157 exact allowlisted files19 templates and no symlinks. Frontend/proxy unchanged, not rerun.

This is local owned synthetic OS-process smoke, not independent runtime/transport/outage/off-host/provider/recovery qualification. No live mail/bank/DNS/TLS/host/deployment activity. Country/tax deferred and commercial effects disabled. Next local regressions: busy bound root and tampered marker refusal through the actual process boundary. Default probe daemon/images remain unchanged. Preserve populated evidence and archive bytes on rollback.

## Cross-process root refusal follow-up

After3f5cdb5 synced0/0, two additional tests hold the actual BoundPreparedArchive operation lock in the parent while the management-command child exits, and replace only the owned fixture marker bytes before child execution. Busy root fails before claim allocation; release after child exit creates no deferred work. Tampered marker produces the fixed generic error and remains byte-for-byte unchanged; only the test restores its fixture in finally. No root adoption, repair or automatic retry.

Targeted seven command tests pass (21 combined observations10.952s). Full local lane CORE_LOCAL_PASS checks5 tests250 duration60.268s:236 Django plus14 Gunicorn observations; no migrations/drift. Updated source /nix/store/0d8ksbdbhcjbflq01ghg8fla7qs3i64d-shop-python-source:157 exact allowlisted files19 templates, no symlinks. No failed runs for this follow-up. Initial248-test evidence above remains historical. Next local tests: process PostgreSQL row-lock contention and wrong physical root rejection. These are ordinary owned synthetic tests, never protected-host fault injection or independent qualification.

## PostgreSQL contention and physical-root identity

Continued after9a979ea on explicit user instruction. Two additional subprocess tests hold the actual owner row lock in the parent until the child reaches its configured one-second PostgreSQL statement timeout, and initialize a second owned physical root with the same destination UUID. The child returns the exact safe generic error in both cases. Timeout rolls back before claim allocation; releasing the parent lock after child exit creates no deferred work. Wrong-root refusal leaves both roots byte-for-byte unchanged and creates no claim/verification. No database outage, process termination, or protected-host experiment.

Nine command tests pass (23 combined observations12.934s). Full CORE_LOCAL_PASS checks5 tests252 duration62.376s:238 Django plus14 Gunicorn observations. Owned PostgreSQL18.6/UTF8, migration application/no-drift pass; no migrations changed. Source /nix/store/a987nja21h6baddyr5g7yyb4j1bmnzjj-shop-python-source:157 exact allowlisted files19 templates/no symlinks. No failed run for this slice. Frontend/proxy unchanged/not rerun. Next local operator command/uncertain-result runbook; no extra work authority or independent qualification is inferred.

Operator guide: docs/local-prepared-archive.md describes existing internal preparation prerequisites, one selected invocation, exact safe outputs and uncertainty reconciliation without retry authority. Documentation/source-link review only;252-test evidence remains unchanged. A supported staff read-only exact-attempt observation route is the next proposed contract.
