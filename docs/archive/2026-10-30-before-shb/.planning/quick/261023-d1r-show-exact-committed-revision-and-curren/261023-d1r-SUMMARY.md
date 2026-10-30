---
quick_id: 261023-d1r
status: complete
implementation_commit: 6171d3c
---
# Exact cart retry confirmations

No-JavaScript cart confirmations now identify the committed revision separately from the freshly loaded current revision and label reconciled earlier submissions. When revisions differ, the message explicitly confirms that later changes remain saved. The server session contains only a closed integer/boolean notice, consumed once; malformed/legacy notices are ignored without echo. Cart persistence/API behavior unchanged. Local guide updated.

CORE_LOCAL_PASS checks5 tests178 duration40.189s:164 Django plus14 actual Gunicorn transport observations on owned PostgreSQL18.6/UTF8. Existing exact-retry scenario now checks older confirmation after later edit/catalog drift, unchanged current data, one-time notice, same-current removal retry and invalid notice suppression. All owner-change/access/form/API concurrency/staff journey tests pass.

Actual Nix source /nix/store/4mgaw74ahgx1kclk6v3j7r8cp7bm5ad8-shop-python-source:129 files19 templates; exact bytes/allowlist/no symlinks verified. Frontend/proxy unchanged; previous scoped results retained. No full browser/accessibility, real delivery, commercial/production/off-host acceptance. Country/tax remains pending; Phase1 last complete; focus7; Phase02 8/18 unchanged.

Next: plan remaining Phase7 local acceptance and durable-evidence boundaries against delivered customer/staff slices, preserving every unknown approval and the user-deferred Country/tax choices.
