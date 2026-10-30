# Local multi-line draft cart — 2026-10-22

Delivered owner-only `/api/v1/cart/` and verified customer UI. Add separate one-vendor IP lines at quantity one; optional support splits into its own line. Add support independently, change positive package quantities, load/replace IP configuration, remove individual lines and resume on refresh. New explicit additions keep distinct line IDs; no automatic merge or dropping. Twenty-line bound. No host IDs or browser persistence.

PostgreSQL cart pointer serializes saves; immutable-by-API snapshots retain exact catalogue/evaluation/line revisions. Optimistic version mismatch rejects stale edits. Unique cart/request replay returns the original committed version plus current version, even after later edits or catalogue change. Changed reuse conflicts. An uncertain browser save retains the exact request/line IDs and blocks mutations until retry confirms it. GET does not create a cart. Production, unverified, staff and cross-owner access remain closed.

Prices/totals remain null; checkout always disabled; higher-volume lines preserve cart quotation status. Quoted support seconds are quantity ×36,000, never granted credits. No acceptance, order, bank, tax approval, real mail, private hosts, staff MFA or deployment operation.

## Executed evidence

- All six bounded `scripts/check.py dev` lanes passed on the initial implementation: frontend103 Node tests plus proxy test, core-local51, worker-smoke24, adapters6, contracts-local8, catalogue70 + cart26 shared cases. Later targeted checks supersede changed lanes below.
- Final isolated frontend lane: **110 tests**, zero failures (104 Node tests including actual React event dispatch/cart uncertain retry plus six privacy boundary methods); static build/typecheck/import policy/output scan passed. This bounded DOM host is not real-browser hydration/accessibility evidence.
- Final core-local: **52 tests**, zero failures, fresh owned real PostgreSQL, migrations/checks pass. Includes same-key races (201/200), competing edits (201/409), owner/auth/CSRF/production/parser boundaries, stale catalogue, old replay after later edits/catalogue change and support-only behavior.
- Final catalogue lane: **96 shared conformance cases** (70 configurations +26 carts), full Python/JavaScript output equality; 100 reported tests including compiler/selector tests.
- Real demo proxy/Gunicorn/PostgreSQL loopback: **13 observations passed** for captured verification, mixed vendors, save/retry/current read, stale version, support-only edit, old snapshot replay, logout and denied read. Codes remained private and unprinted. Owned demo stopped normally after checks.
- `git diff --check` passed. Source authority, dependency locks/notices/SBOMs preserved. Existing unchanged worker/adapter/contract evidence reused after UI/replay fixes; no repeated full qualification runs.

## Safety and limits

Tests use bounded synthetic rows/two requests and newly owned children. A lost response is simulated only in a React transport stub; no process/network interruption, exhaustion, off-host operation or protected resource mutation. User approval for earlier demos is retained; this new cart UI awaits review. Full phase acceptance remains pending; 7% still means one of fourteen phases fully complete. CI status for this slice is unverified; no credential access was retried.

## Inspect and continue

From `014-Shop`: `nix --extra-experimental-features 'nix-command flakes' develop --max-jobs 1 --cores 4 ./ops/nixos --command python3 scripts/demo.py --backend`; open http://127.0.0.1:4321, verify a synthetic .invalid email with its private captured code, then use Your draft cart. Demo data lasts only while its backend runs.

Next ready slice: protected quotation-request capture tied to an exact cart snapshot; retain pending commercial offers/totals and prevent acceptance/payment. Shared contact roles, private host editing, business declarations, approved quote/financial durability and all release gates remain pending. Traceability: Phase07 COM-01/COM-02 local cart portions only, not full requirement satisfaction.
