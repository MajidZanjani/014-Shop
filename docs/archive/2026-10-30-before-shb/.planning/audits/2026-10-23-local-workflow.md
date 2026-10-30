# Local workflow audit — 2026-10-23

GSD audit-fix, inline under its Codex fallback; user authorized local workflow audit and fixes. Scope: customer cart/quotation/business and staff review/preparation routes. Canonical audit-uat query found0 UAT items; read both retained phase verification records. This does not resolve existing human/external qualification gates. Country/tax answers remain pending. No providers/host operations or manual credentials.

| ID | Finding | Severity | Classification | Status |
|---|---|---|---|---|
| F-00 | ROADMAP Phase7 Not started and stale state.json disagree with current implementation focus; live entry points stale | medium | auto-fixable: known current/completed distinction and canonical publication | Fixed; planning check verifies phase/status/count agreement |
| F-01 | Older quotation detail/list/capture retry/binding/staff-review routes lack consistent parent-cart/snapshot identity checks; a malformed retained FK can cross resource boundaries | high | auto-fixable: apply existing exact resource identity rule, no new access model | Fixed; five regression methods and full145 core-local pass |
| F-02 | Historical review digest projection/replay trusts matching grant version without rechecking historical business-snapshot ownership | medium | auto-fixable: reuse owner-filtered scope resolution, preserve old-source retry semantics | Fixed; historical owner checks and full147 core-local pass |

F-00 reproduction: new scripts/check_planning.py failed on unmodified ROADMAP/STATE mismatch. Reconciled live ROADMAP, STATE, canonical state.json, PROJECT, requirement traceability, ACTIVITY-LOG and Phase02 status/reconciliation views. Current phase7 is in progress; phase1 last fully complete. Unchanged1/14 completed phases (rounded7%),10/20 planned records, Phase02 remains8/18. All planning files reviewed for live status references; historical quick summaries/source/verification scopes preserved rather than rewriting past evidence. October22 roadmap activity moved verbatim into activity history.

Before every commit: update all affected planning status references, regenerate state.json with canonical GSD publisher and run planning check. After every commit: non-force sync origin/main and verify ahead/behind.

Existing manual/external gates remain pending: user human/browser review; Country/tax and commercial/source approvals; actual customer delivery/staff MFA/recovery; off-host runtime/full-pool-loss recovery/full CI and protected-host qualification. No new acceptance inferred.

## F-01 — fixed and verified

Pre-fix probes on fresh owned PostgreSQL reproduced5 failing methods/9 assertions across customer detail/list/document/binding, staff detail/list, cross-cart retry aliases, existing review replay and a controlled owner change before the attachment lock. Applied exact parent/cart/snapshot checks before dereference/replay and rechecked ownership under the business-attachment lock. New review writes also reject inconsistent parent identity. Existing stale-source/idempotent behavior on valid resources remains intact. Full CORE_LOCAL_PASS checks5/tests145/35.382 seconds; no production or actual customer fault injection. F-02 remains pending.

## F-02 — fixed and verified

Pre-fix reproduction showed two failing assertions: a matching historical business grant exposed a private review digest despite a malformed business-owner reference, and the exact review retry returned200 for that inconsistent scope. Added owner-filtered exact-version scope resolution for history projection/replay. Unauthorized historical hashes stay masked and malformed retries reject; valid old scopes remain readable/replayable after later attachments and source revisions, without a current-source freshness shortcut. Full CORE_LOCAL_PASS checks5/tests147/36.079 seconds, fresh owned PostgreSQL18.6/UTF8. All7 new audit test methods pass.

## Final result

F-00 fixed/synced at a70b38d; F-01 fixed/synced at93e9f04; F-02 is the final atomic fix in this report. All three findings fixed, none skipped or left fix-failed. Pre-fix probes were deliberate finding reproductions; no post-fix test gate failed. Actual candidate source `/nix/store/3p04yiv2v3b817scz96g7n917qxylfi4-shop-python-source`:116 files/fifteen templates, exact bytes/allowlist/no symlinks. This is source packaging only, not runtime/deployment proof. Existing frontend110 aggregate/proxy1 and harness15 retain prior scopes; not rerun for these backend-only changes.

Planning reconciliation reviewed all160 current files for affected live status references. ROADMAP/STATE/canonical state.json, PROJECT, requirement traceability, activity log, Phase02 progress and recorded-evidence verification agree before each commit. Historical evidence and immutable sources remain dated/preserved. Planning guard initially reproduced the mismatch, then passes14 phases/current7/completed1/10-of20 plan records. Phase02 remains8/18. Current focus7 differs from last-completed1; no acceptance or progress percentage inflated.

Next local action: automated owned-synthetic customer-to-staff round trip through supported routes, including verification/cart/request/business/review/preparation/compare, with no real mail/bank/tax validation, manual credentials or commercial effects. Country/tax answers and original human/external gates remain pending.
