---
quick_id: 261023-hn4
status: complete
implementation_commit: b96b665
---
# Capture-status reads across supported operator revocation

Supported operator revocation races verified: credential reset/revoke and exact business-grant withdrawal each block status on the exact operator PostgreSQL backend; rollback preserves recorded status, commit safely refuses. Retained envelope/intent attribution and work gates remain unchanged. CORE_LOCAL_PASS5 checks/275 tests (261 Django plus14 Gunicorn),71.878s; owned PostgreSQL18.6/UTF8 and0012 application/no-drift pass. Exact source /nix/store/vvwm917wanx5ad6zi60n2a8fw1m5m4k8-shop-python-source:163 files21 templates/no symlinks. Runtime unchanged; tests only. Full07-02 and external/commercial gates remain pending; country/tax deferred.

## Verification

Three new tests cover six deterministic interleavings using actual synthetic staff password/private-code login, CSRF preview/capture, local_staff reset/revoke/revoke-business commands and separate PostgreSQL connections. Operator changes are deliberately held inside a test transaction. pg_blocking_pids confirms the exact operator backend blocks the status backend before commit/rollback release. Rollback returns capture_recorded; commit returns private404/not_found from the in-flight producer recheck. All retained envelope/intent values (including original actor/MFA) remain identical. Archive publish/recover/attestation are trapped, work tables stay empty, and the observation does not change disposable operator credential files. Reset credential-file writes are deliberately separate from archive/business evidence and may survive a synthetic database rollback; no production bootstrap/recovery behavior is claimed.

Focused temporary wrapper:18 Django tests plus14 Gunicorn observations pass,32 total/14.105s; final retained full producer275/71.878s passes. Exact built source compared by relative path and bytes against the Nix allowlist, no symlinks. Frontend/proxy unchanged and not rerun. No migration/application behavior changes; no direct domain tampering added by these regressions.

These are in-process controlled interleavings, not independent process/transport/outage, real staff MFA, provider/off-host/restore or production qualification. Initial bounded audit remains clean; no runtime defect reproduced or speculative fix applied.

## Next existing plan action

Review the existing07-EVIDENCE-CONTRACT against current offer-preparation/catalog/document interfaces and original COM-02–06 requirements. Resolve the closed protected-offer/domain revision and approval contract on paper, keeping all missing prices/rights/terms/hosts/country/tax/deadlines null or pending; identify the exact implementation blockers. Do not implement or approve offers from request-only prepared evidence.

All original prerequisite, approval, host protection and release gates remain pending. No agents, real credentials or protected/external services used. All test processes finished.
