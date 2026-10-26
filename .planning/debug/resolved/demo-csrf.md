---
status: resolved
trigger: Browser request-code form returns 403 CSRF verification failed
created: 2026-10-26
updated: 2026-10-26
---

## Symptoms

Expected: request a locally captured verification code through the browser demo.
Actual: Django CSRF 403 on the first request-code form submission.
Reproduction: start scripts/demo.py --backend and submit /purchase/access/.

## Current Focus

Hypothesis: private form pages send no-referrer, which makes navigation-mode POST Origin null; Django correctly rejects it. The proxy also omits Location on successful redirects.
Next action: user restarts the updated demo and reloads the access page; project execution resumes at the existing complete-cart acceptance/payment binding task.

## Evidence

- Proxy preserves Host, Origin, Cookie and CSRF headers.
- Customer/staff form responses use no-referrer. Fetch Standard append-a-request-origin-header specifies null for non-CORS POST with that policy.
- Existing form tests send no Origin and manually follow redirects, so they missed both browser integration failures.

## Constraints

Local/synthetic owned test data only. Never allow null origins, disable CSRF, trust arbitrary origins or change production services.

## Reproduction and fix

- Before the fix, scripts/check_demo_access.py failed request-code submission through the actual loopback demo proxy/Gunicorn/owned PostgreSQL with browser navigation Origin:null.
- Shared FormReferrerPolicyMiddleware sets same-origin only on HTML responses whose CSP explicitly permits self form submission. Cross-origin referrers remain suppressed; JSON/read-only policies remain unchanged. CSRF middleware and token/origin validation stay enabled.
- Demo proxy now preserves Location and Vary, fixing a second failure where successful303 responses could not lead to the verification page.
- Live header-level regression passes request/verification/sign-out for both loopback aliases and rejects null/foreign origins and missing tokens. This is not actual browser-engine qualification.
- Existing proxy unit test now asserts303 Location and Cookie Vary forwarding. Full form-suite regression exposed one JSON503 expectation; its no-referrer assertion is preserved separately from HTML form assertions.
- Primary source: https://fetch.spec.whatwg.org/#append-a-request-origin-header

## Resolution

Code commit: 8c319a0c723bd19a99c727011997bd9a549197e7

- Full final backend: CORE_LOCAL_PASS checks=5 tests=354 duration_seconds=94.845; real owned PostgreSQL18.6, migration/no-drift and Gunicorn checks. No off-host recovery claim.
- Final live HTTP check: DEMO_ACCESS_PASS checks=32 aliases=2 evidence=local-synthetic-header-level. Both loopback aliases request/verify/logout with browser-style navigation headers and redirect/cookie handling; null/foreign origins and missing tokens remain403. Real browser-engine/user rerun remains separate.
- Updated proxy unit test:1 test,1.515s, passes; redirect Location and Cookie Vary asserted. Scoped form-policy unit and affected HTML expectations pass in the full backend suite. Read-only/JSON no-referrer behavior retained, including the database-error JSON path.
- Planning/immutable-source checks and git diff --check pass. No dependency pin, real credentials, production service or external operation changed.

User recovery: Ctrl+C the old demo; git pull --ff-only origin main; restart the same demo command; reopen http://127.0.0.1:4321/purchase/access/ before requesting a new synthetic code. Old temporary database/captures are discarded by the demo lifecycle.
