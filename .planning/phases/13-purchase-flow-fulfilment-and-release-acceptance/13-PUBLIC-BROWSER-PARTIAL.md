# Public React/browser qualification and required-platform fixes —2026-10-27

**Current result:** Exact frozen frontend and the real fresh public browser producer now pass locally:134 customer/staff/business/checkout/payment/support plus25 JavaScript/14 no-JavaScript assertions, including staff/customer keyboard MFA/access, error recovery and reflow below. Earlier diagnostic/failure/pending-build statements below are dated attempt history, superseded only for this exact local frontend/public qualification. Formal/manual accessibility and all actual/full gates remain pending.

## Implemented behavior

Current React entry now treats a missing platform answer as incomplete, including when an older draft without that field is resumed. The same normalized configuration reaches save/cart controls. Existing shared snapshot evaluation remains compatible with older platform-less revisions. Django configuration preview and its inherited no-JavaScript IP cart-entry form require an explicit platform answer; unknown/unfinished boards remain valid without a board name, pinout or project dossier. Standalone support commands do not acquire a platform questionnaire.

Actual browser diagnostic reproduction failed at `public-required-platform-0` before the fix. Twenty focused real-PostgreSQL catalog/form/cart tests pass after the fix, including missing/empty platform rejection, accepted unnamed/unfinished targets and retained legacy snapshot evaluation. Current cart fixtures now explicitly answer the platform question; shared legacy conformance data is unchanged.

Anonymous screenshot inspection also identified inactive server-rendered React controls and a permanent connecting message in the JavaScript-disabled page. A noscript-only inline style now hides that island; static product/vendor information and the working Django fallback remain visible. JavaScript-enabled hydration is unaffected. Agent inspection of diagnostic desktop/mobile captures is provisional layout evidence, not human/formal accessibility acceptance. Captures contain only initial anonymous public content and remain in private task scratch.

## Public browser path and closed gates

`scripts/check_browser_access.py --public` requires a fresh allowlisted Astro build with the exact Nix-selected frontend Node24.22.0/npm11.19.1. It never consumes retained repo dist or node_modules. Tool identities are checked before installation. Source policy runs before compilation; the existing public-output scanner checks produced files/canaries and an exact file-hash inventory is checked again before serving. The build subprocess receives a minimal environment and task-owned temporary space. All install/check/build/test commands retain finite bounds; the enclosing fresh-build limit is720 seconds. No diagnostic fallback is wired into this path.

Actual public scenarios exercise hydration, vendor-family/term resets and Altera-only RDP, required platform, conditional board names and pending ready-kit refusal, support quantity summary, visible labels/layout, captured-code authentication, saved draft/resume, separate cart IP/support lines, quotation capture and logout. With page JavaScript disabled the island is hidden, the actual fallback link is followed and a Django form is submitted with an explicit unfinished-board answer. The public report requires20 JavaScript and7 no-JavaScript assertions in addition to the existing54 customer/staff checks; it requires exact frontend/browser-controller versions and retains false production/formal-accessibility flags. Ordinary CI includes the evidence/build-boundary unit controls, not an invented hosted browser result.

Thirteen Python browser report/controller/public-build tests and the pinned Node exact-origin test pass. Public controls reject wrong executables/versions, missing modes/counts, diagnostic/promoted/private-extra reports, nonempty/symlink/external output roots, changed artifact inventories and failed builds without retry/downgrade. Mocked receipt tests do not establish a real frontend build.

## Exact evidence classes and remaining checks

Final current-source diagnostic: `BROWSER_PUBLIC_DIAGNOSTIC_PASS`, base58 plus public20/7, Chromium155.0.8059.84/test-client Node24.21.0, `qualified_frontend_graph:false`. Temporary scratch wrappers alone selected retained diagnostic build output; the committed validator rejects this envelope. Diagnostic TypeScript checking reports0 errors/warnings/hints and112 frontend tests pass. These are useful implementation diagnostics, not successful frozen frontend qualification. The later noscript-only markup change also passes actual diagnostic JS-on/off browser checks.

The retained independently qualified default browser run passed54/2 roles/2 modes on the modified backend. Final browser expansion adds server rejection of missing-platform IP and zero-quantity support form submissions with native browser validation bypassed; each asserts unchanged saved cart revision/line count. Final committed default `BROWSER_LOCAL_PASS58`/2 roles/2 modes passes, including all four additional rejection assertions. These are inspector-driven client-validation bypasses of ordinary forms, not privileged test routes. Supported synthetic purchase fixture/proxy148 checks/2 aliases passes. Inert backend source `/nix/store/69wapz8z01dmy6jhm5rc8adar274mgkg-shop-python-source` matches264 exact files/33 templates/no symlinks.

The first full backend attempt returned a failing first batch containing current-entry form/cart tests before explicit platform fixture updates; detailed failure output was not retained by the runner. Focused verification after those updates passes. A subsequent full run passed its first batch, then reached the existing120-second second-batch bound while the native frontend build and other checks were running. That run is not a pass; no application/database/request/test timeout was increased. Final isolated full regression passes: `CORE_LOCAL_PASS checks=5 tests=570 duration_seconds=169.832`, enclosing171.128 seconds. No test/database/application timeout changed; off-host outage/recovery/full core qualification remains pending.

Native exact frontend build: first one-core client was interrupted after a Nix command reported no space. Inspection narrowed exhaustion to the shared128MiB `/tmp` tmpfs, not the persistent workspace or Nix store; native-build causation was not established. No shared files, caches, protected services or store objects were pruned. Subsequent Nix commands use `.scratch/browser-nix-tmp`; the exact Node24.22 source build used one core/job and reached its900-second outer bound (exit124) without completing. The exact owned client stopped; no compiler/background build remains. Actual fresh frontend/public acceptance remains pending until this build and the real `--public` producer succeed. Do not promote the diagnostic output or change frontend pins to satisfy the gate.

Reproduce qualified default browser: `nix develop --max-jobs 1 --cores 1 ./ops/nixos#browser --command python3 scripts/check_browser_access.py`. Qualified public path, once the exact compiler is available: same shell command with `--public`. If shared `/tmp` is full, explicitly set `TMPDIR` to a newly owned workspace scratch directory. Session dependency setup reused the retained exact hash-locked wheel cache; committed setup remains hash-locked. Formal/manual accessibility approval, actual technical intake/transport/commercial/provider/retention/runtime/recovery/host/public activation and full phase acceptance remain pending. New UI form requirements do not constitute an audit or change of historical API snapshot acceptance semantics.

Final CI workflow JSON and its embedded ordinary-check Python compile locally. Hosted execution is unobserved. Anonymous mobile screenshot review after the noscript fix confirms the static fallback is visible and the inactive island is absent; no formal/assistive-technology approval is inferred.

Final task processes are stopped: no native compiler, owned server/browser/test, agent or external async job is left running. Existing shared `/tmp` contents were preserved. Public diagnostic images/wrappers remain only in private ignored scratch; no credentials or private pages were retained as evidence.

## Resumed exact-toolchain qualification —2026-10-27

The user selected continuation of task5. One isolated native attempt used the unchanged frozen derivation `/nix/store/zkv9pcjdv9h73qcr6zbpnhln4xqsdw2w-nodejs-slim-24.22.0.drv`, `--max-jobs 1 --cores 2`, a newly owned persistent workspace `TMPDIR` and the existing900-second outer limit. Observed `make -j2` and active compiler progress. The timeout returned124; retained Nix output ends at `[545/1971] CXX ...v8_base_without_compiler.swiss-name-dictionary.o`. Nix's `interrupted by the user` message here follows the automatic timeout signal, not a new user cancellation. No native compiler/make remains. Workspace free space stayed about1.8GiB; shared128MiB `/tmp` stayed full and untouched. No memory/storage failure was observed in this attempt.

Exact invocation: `env TMPDIR=/home/claude/project/014-Shop/.scratch/frontend-qualification-20261027 timeout --signal=TERM --kill-after=10 900 nix develop --max-jobs 1 --cores 2 ./ops/nixos#default --command python3 -c 'import os,subprocess,json; print(json.dumps({k:os.environ.get(k) for k in ("SHOP_NODE","SHOP_NPM")})); subprocess.run([os.environ["SHOP_NODE"],"--version"],check=True); subprocess.run([os.environ["SHOP_NPM"],"--version"],check=True)'`.

This is a failed local native-toolchain qualification, not a successful frontend or public-browser run. The real `--public` path was not run because its exact prerequisite remains unavailable. The two-core900-second envelope is demonstrably insufficient and must not be repeated unchanged. No pins, acceptance gate, test/application/database limit, shared resource, protected service or external operation changed. No broad backend rerun was warranted. Retained backend570/browser58/proxy148 and diagnostic-only public20/7 classifications remain unchanged; formal/manual and all actual qualification gates remain pending. Planning views now record the attempted resumption and exact prerequisite rather than a user pause or build still running.

## Native-build capacity investigation —2026-10-27

Following user continuation, an unchanged exact derivation was tried with four compiler jobs and a separate3600-second native-preparation bound. It progressed to1274/1971, then available memory dropped below0.5GiB with no swap and compilation stalled. Temporarily pausing positively identified task-owned compiler children did not recover headroom; all held children were resumed for cleanup and only the owned build client was stopped. The client returned1 after the explicit signal; it did not exhaust the3600-second bound. No make/ninja/compiler remained and available memory recovered to about6.7GiB. No memory/swap/cgroup/host-service setting was changed. The cgroup's cumulative OOM-kill count was observed without a baseline, so no new OOM event or victim is attributed to this attempt.

The next materially different attempt uses two compiler jobs and a5400-second native-preparation bound with fresh owned persistent TMPDIR. This combines the previously observed two-job memory behavior with a sufficient preparation window rather than repeating900 seconds. The720-second fresh frontend gate, per-command150-second frontend checks,90-second browser and existing application/database/backend-test limits remain unchanged. Exact native qualification remains pending until successful tool identity checks and the real public producer complete.

## Exact native/frontend/public local qualification passed —2026-10-27

The unchanged exact derivation completed successfully with one Nix build/two compiler jobs and a5400-second separate native-preparation bound, using owned persistent TMPDIR. Nix reports `buildPhase completed in 59 minutes 3 seconds`, `checkPhase completed in 3 minutes 56 seconds` and `All tests passed.` Its TAP output ends at5505 entries, including the pinned recipe's existing platform/environment skips and exclusions; this is not a claim that every upstream test ran. Approximately63 minutes elapsed for the complete preparation. No compiler/make/ninja remains. No pin, test/application/database/browser/frontend timeout, host memory/swap/cgroup setting, protected service or external-operation authority changed. Earlier900-second failure and four-job memory-pressure stop remain valid attempt history.

Exact selected executables: `/nix/store/x6a7dbhj1fmhwk0d9124zkszdfhd7k91-nodejs-24.22.0/bin/node` and `/nix/store/x6a7dbhj1fmhwk0d9124zkszdfhd7k91-nodejs-24.22.0/bin/npm`; actual versions `v24.22.0` and `11.19.1`. Source/native derivation remains `/nix/store/zkv9pcjdv9h73qcr6zbpnhln4xqsdw2w-nodejs-slim-24.22.0.drv`.

The committed `scripts/check_browser_access.py --public` CLI ran through the unchanged pinned browser shell. A task-local Python launcher only replaced the locked wheel download source with the retained `/tmp/shop-ledger-wheels` cache; the exact lock/hash/inventory/install/runtime checks remained active. It used `runpy` to execute that committed CLI with `--public`; no browser/public producer or validator was patched or bypassed. The frontend nested producer ran unchanged with newly created allowlisted inputs/output, exact executable/version checks, fresh `npm ci`, source policy, Astro check/build, frontend tests, public-output privacy scanning and final artifact inventory recheck. The720-second fresh-build,150-second frontend-command and90-second browser bounds stayed unchanged.

The actual closed, validated report was:

```json
{
  "browser_sandbox": "disabled-for-owned-local-root-smoke",
  "browser_version": "155.0.8059.84",
  "checks": 58,
  "evidence_class": "local-synthetic-browser-engine",
  "formal_accessibility": false,
  "frontend_toolchain": {
    "node": "24.22.0",
    "npm": "11.19.1"
  },
  "modes": 2,
  "node_version": "24.21.0",
  "production_qualified": false,
  "public_checks": {
    "javascript": 20,
    "no_javascript": 7
  },
  "roles": 2,
  "status": "BROWSER_LOCAL_PASS"
}
```

This supersedes diagnostic-only public20/7 with fresh actual local execution of the committed exact producer. The older diagnostic envelope remains diagnostic; it was not promoted. Browser controller Node24.21.0 remains separate from frontend Node24.22.0. Current JS-on/off customer/staff/auth/revocation/privacy/form-rejection checks and actual public React/no-JavaScript scenarios pass. Retained backend570/5 checks and proxy148/2 aliases were not repeated for these documentation-only changes. Formal/manual accessibility/assistive-technology approval, actual confidential intake/custody/transport, commercial/source/provider/retention/runtime/recovery/host/activation and full Phase13 acceptance remain pending. No actual customer materials, bank/mail, deployment or protected-service action occurred.

Reproduce once exact native outputs are available: `TMPDIR=<new-owned-workspace-directory> nix develop --max-jobs 1 --cores 1 ./ops/nixos#browser --command python3 scripts/check_browser_access.py --public`. The committed command uses hash-locked index downloads; this run's retained-wheel substitution is explicitly scoped above. No hosted CI execution or independent off-host qualification is claimed.

## Keyboard, accessibility-tree and320px reflow follow-up —2026-10-27

User continued after the exact public baseline. Existing UAT-03 local accessibility coverage now uses actual CDP keyboard events, without DOM `.focus()` or synthetic click substitution for the tested keyboard path. Bounded Tab traversal reaches the React vendor selector, the public no-JavaScript fallback link and the Django vendor selector; each asserts a visible focus outline and vertical viewport visibility. Enter activates the fallback link; ArrowDown selects the React vendor. Chromium's actual accessibility tree must expose each tested vendor selector as a nonignored named combobox. Device emulation must report320 CSS pixels and no horizontal document overflow on hydrated React, static no-JavaScript public content and the Django fallback, then restore the original viewport.

The first real expanded run failed at `public-reflow-django-1`. The fallback response lacked the shared stylesheet, so its long native select options exceeded the narrow viewport. The fix adds only the existing `/purchase/assets/shop.css?v=20261026` link and existing `shop-container panel` classes to that response. Licence/platform/form inputs, privacy sanitization, CSRF/no-store and local/synthetic-only production denial remain unchanged. No new dependency, template, questionnaire or private intake. The real browser subsequently passes the same reflow assertion and keyboard/focus checks with that shared styling.

The closed public report now requires25 JavaScript/14 no-JavaScript assertions; the previous20/7 report is deliberately rejected for this expanded scope. The additional12 assertions cover five React checks and seven no-JavaScript checks; Enter activation strengthens the existing fallback navigation assertion. These are finite local checks, not formal accessibility, complete keyboard journeys, contrast,200%/400% text zoom or actual assistive-technology approval.

Actual report after the fix:

```json
{
  "browser_sandbox": "disabled-for-owned-local-root-smoke",
  "browser_version": "155.0.8059.84",
  "checks": 58,
  "evidence_class": "local-synthetic-browser-engine",
  "formal_accessibility": false,
  "frontend_toolchain": {
    "node": "24.22.0",
    "npm": "11.19.1"
  },
  "modes": 2,
  "node_version": "24.21.0",
  "production_qualified": false,
  "public_checks": {
    "javascript": 25,
    "no_javascript": 14
  },
  "roles": 2,
  "status": "BROWSER_LOCAL_PASS"
}
```

Verification: real exact fresh `--public` build/browser pass above; all13 browser report/control/public contract tests pass;20 existing real-PostgreSQL catalog/form/cart tests pass in1.706 seconds, including CSRF/private-input and production-denial behavior. No broad backend rerun is inferred for this narrow response markup/style change; retained backend570/proxy148 predate it. Current inert source `/nix/store/xwz80mphdkzly6h8d471j6sb9n4qphi1-shop-python-source` matches264 exact files/33 templates/1 stylesheet/no symlinks. Only the inert source was built; no image/deployment operation occurred. All existing timeout/toolchain/source/privacy/formal/actual gates remain. No owned browser/server/database/compiler process remains.

## Keyboard-only customer verification and error recovery —2026-10-27

The existing customer-access browser journey now reaches email/code controls through bounded actual Tab events, asserts visible focus/in-viewport geometry, enters text through Chromium `Input.insertText` and submits using native Enter events. It no longer uses inspector value assignment or `requestSubmit` for the selected customer request/verification forms. One deliberately invalid fixed synthetic code must return400 with the error in a DOM alert and a nonignored accessibility-tree alert; access remains unverified, the code field is empty and the failed code is absent from rendered body and URL. The original privately captured valid code then succeeds through the same keyboard path. This runs with page JavaScript both enabled and disabled. Existing customer/staff/MFA/revocation/privacy/cart checks remain. The six additional assertions per mode raise the required base report from58 to70; old58-check evidence cannot satisfy the expanded contract.

The first run failed at `keyboard-email-0`. The access page inherited the shared stylesheet link, but its route-specific `default-src 'none'` policy had no style source and prevented the shared focus styling. Adding only `style-src 'self'` gets the run past its focus assertion. `default-src 'none'`, self-only form actions, no framing and no base URI remain; the focused test now verifies the exact closed directive set. This permits the existing same-origin static stylesheet, not inline/external styles, scripts, images or a new service. Cache/referrer/session/CSRF/attempt/production gates and authentication operations are unchanged.

A follow-up reached `keyboard-entry-email-0` but failed before completing the request. This was a driver issue: input Enter submission requires the carriage-return text/unmodifiedText on keyDown. The driver now emits that native sequence and uses fixed reach/focus/entry/submit stage names. No app authentication workaround, DOM-submit fallback or automatic retry was introduced. The corrected default and combined exact public runs pass. Failure output contains only fixed stage metadata, never entered email, bearer code, cookies, request bodies or private URLs.

Actual combined report:

```json
{
  "browser_sandbox": "disabled-for-owned-local-root-smoke",
  "browser_version": "155.0.8059.84",
  "checks": 70,
  "evidence_class": "local-synthetic-browser-engine",
  "formal_accessibility": false,
  "frontend_toolchain": {
    "node": "24.22.0",
    "npm": "11.19.1"
  },
  "modes": 2,
  "node_version": "24.21.0",
  "production_qualified": false,
  "public_checks": {
    "javascript": 25,
    "no_javascript": 14
  },
  "roles": 2,
  "status": "BROWSER_LOCAL_PASS"
}
```

Focused real-PostgreSQL verification/customer-portal/race/security tests:17 pass in0.603 seconds. Browser report/controller/public tests:13 pass. Current inert source `/nix/store/6npnxy6mq6qa3xh3h0l3m22wyapsi07j-shop-python-source` matches264 exact files/33 templates/1 CSS/no symlinks. No full backend/proxy rerun is inferred; their earlier results retain their scope. Fresh exact frontend/native pins and all finite setup/build/browser/application/database limits remain unchanged. No owned browser/server/database process remains.

This covers the selected local customer-access forms and renderer accessibility tree, not every private/business/staff keyboard journey, spoken screen-reader behavior, contrast/text zoom or formal accessibility approval. Synthetic capture is not real mail/HTTPS transport or production MFA/customer-access qualification. Every commercial/source/private-intake/provider/retention/runtime/recovery/host/activation/full-acceptance gate remains pending.

## Staff keyboard MFA, narrow layout and safe retry pages —2026-10-27

User continued local UAT-03. Actual keyboard events now enter staff username/password/possession code and submit the supported forms in both JavaScript modes, including reauthentication after logout.320-CSS-pixel reflow is checked on password and challenge states. The prior password-only403, exact resource assignments, recent-MFA grant/revoke/regrant, logout and retained-cookie credential revocation checks remain. Earlier70-check reports cannot satisfy the expanded90-check contract; the intermediate80-check staff happy-path run also passed but remains narrower than the final result.

First real staff run failed at `keyboard-focus-staff-username-0`: the sign-in page had no shared focus styling. The exact existing fixed shared CSS is now embedded in one staff-home style block with an exact SHA-256 CSP allowance. The template receives only that trusted source string, never submitted values. Tests compare the rendered block to the shared CSS, recompute its hash and require the closed CSP directive set: default resources denied, only that style hash, self-only form actions, no framing/base URI. No `unsafe-inline`, self/external style source or pre-MFA asset exception was added. The existing stylesheet route remains403 before MFA and after password alone, and200 after both factors; the middleware allowlist/route set is unchanged.

The next keyboard run reproduced a second gap at `staff-keyboard-invalid-submit-0`: native form failures returned JSON without an alert/retry form. Exact URL-encoded form failures now render fixed safe error text and empty retry controls with the existing400/429/503 status; JSON clients retain their original error bodies and statuses. Enabled/host/CSRF checks, throttles, challenge consumption, session rotation, current MFA state and resource authorization are unchanged. No submitted username/password/code is placed into template context or reflected in the error body. The new test covers wrong password, duplicate fields, wrong-code attempt count and successful correction; replay still fails without revoking an already verified session.

`TemplateResponse` and a deferred challenge-pending boolean evaluate the retry template only after the authentication transaction exits. A real-PG fault test starts with an existing database-backed session, forces local capture failure after challenge creation, and verifies safe503 HTML after rollback, no challenge/throttle residue, unchanged prior session state and no credential/exception reflection. No whole session object is passed as template context. This avoids querying a session while its transaction is marked for rollback.

Actual final combined report:

```json
{
  "browser_sandbox": "disabled-for-owned-local-root-smoke",
  "browser_version": "155.0.8059.84",
  "checks": 90,
  "evidence_class": "local-synthetic-browser-engine",
  "formal_accessibility": false,
  "frontend_toolchain": {
    "node": "24.22.0",
    "npm": "11.19.1"
  },
  "modes": 2,
  "node_version": "24.21.0",
  "production_qualified": false,
  "public_checks": {
    "javascript": 25,
    "no_javascript": 14
  },
  "roles": 2,
  "status": "BROWSER_LOCAL_PASS"
}
```

This staff continuation adds ten assertions per mode: three keyboard-entry checks and two reflow checks, followed by invalid-code entry, rejection, accessible-alert presence, credential privacy and denied privileged access. Correct-code success remains an existing assertion, strengthened by actual keyboard entry/submission. Native key entry uses no inspector assignment/focus/requestSubmit fallback for these selected staff/customer sign-in forms. The invalid staff code cannot grant access; the privately captured correct code subsequently succeeds in the same browser. The renderer's alert tree is checked, not actual spoken screen-reader output.

Final focused staff security/navigation suite:23 tests,11.494 seconds;13 browser-report/controller/public contracts pass. Exact inert source `/nix/store/a5y1jcv7xln5d4fa126gjcip87qscdkx-shop-python-source`:264 byte-identical files/33 templates/1 stylesheet/no symlinks. Earlier21-test staff happy-path and23-test pre-boolean checks remain intermediate evidence, not substitutes for the final run. No full backend/proxy rerun is inferred; their earlier scope remains dated. Only inert source was built; no runtime image, host mutation, real staff transport or external service operation occurred. Existing setup/build/browser/application/database limits and exact frontend/controller pins are unchanged. No owned browser/server/database/compiler remains.

Formal/manual accessibility, complete keyboard coverage beyond these selected journeys, contrast/text zoom/real assistive technology, actual MFA/customer transport, commercial/source/private-intake/provider/retention/runtime/recovery/host/activation and full Phase13 acceptance remain pending. No approval, actual payment, entitlement or support-credit effect is inferred.

## Business validation and reflow continuation —2026-10-27

The private business page previously denied its inherited shared stylesheet under default-src none and exposed only an unassociated error list. Allowing style-src self enables existing fixed styles without scripts, external origins or new dependencies. A role=alert summary links to each invalid field; aria-invalid and aria-describedby point to fixed safe text. Only sanitized details are redisplayed. Original expected revision/source survive validation; no rejected revision is saved and no required field/approval policy changes.

Actual default browser BROWSER_LOCAL_PASS98 (two roles/two modes), followed by the exact fresh --public producer98+25 JavaScript/14 no-JavaScript, passes. Eight added checks cover both modes: unchanged expected revision after422, stripped rejected synthetic email/field association, accessibility-tree alert, and320-CSS-pixel reflow with the existing stylesheet loaded. This slice uses the existing native form helper, not a new claim of keyboard-only business completion. Prior customer/staff/public keyboard checks remain. Browser90 reports are now rejected as incomplete;13 report/controller/public tests pass.

Focused real PostgreSQL shop.catalog.business_tests:10 tests in1.424s, including concurrent exact retries/edits, stale version/source rejection and invalid-value/privacy recovery. Exact inert source `/nix/store/ilxk6c3731l3ifrd38778l024hh8i8mr-shop-python-source`:264 byte-matched files/33 templates/1 CSS/no symlinks. No broad backend/proxy rerun is claimed. The temporary runners only replace locked wheel download sourcing with the retained cache; lock/hash/inventory installation controls remain unchanged. Formal accessibility and production_qualified stay false. All actual/full gates remain pending.

## Checkout keyboard review regression and diagnosis correction —2026-10-27

The actual expanded browser run passed108 before any checkout/view/CSP change. FormReferrerPolicyMiddleware already adds style-src self to HTML with form-action self. The initial source-only checkout stylesheet diagnosis was incorrect; no UI/policy fix was necessary or made. This also corrects the preceding business continuation's stylesheet claim: its explicit view policy was redundant with middleware, while its alert/field associations were the substantive validation fix. Historical source-level CSP observations must not be read as browser-reproduced stylesheet failures on these routes.

Actual default BROWSER_LOCAL_PASS108 and exact fresh --public108+25 JavaScript/14 no-JavaScript pass. Ten new assertions across both modes cover exact synthetic preview/disclaimer,320px reflow/styles, actual Tab/visible focus on Record synthetic checkout, native Enter after changing only the submitted digest to a guaranteed stale value,409 with accessibility-tree alert/no reflected digest or record form, then unchanged reviewed digest on reload. No valid checkout is submitted by this slice. Earlier98-check reports are now rejected as incomplete. Formal_accessibility and production_qualified stay false.

Focused real PostgreSQL shop.catalog.checkout_tests:15 tests in2.180s, including exact captures/retries/concurrency, privacy/CSRF/access and new stale-review no-checkout/no-retry-key/no-bank-effect assertions. Tests inspect the effective closed HTML CSP as directives, retaining unchanged API/denied policy.13 browser report/controller/public tests pass. Exact source `/nix/store/7r3b2w45jgh1wrbgjnszbxh8qcm0q5fk-shop-python-source`:264 byte-matched files/33 templates/1 CSS/no symlinks. Temporary runners retain the previously disclosed hash-locked wheel-cache sourcing only. Browser controller Node24.21.0/Chromium155.0.8059.84 and exact frontend Node24.22.0/npm11.19.1 remain distinct. All finite bounds remain unchanged. No broad backend/proxy rerun, formal accessibility or actual/full qualification is inferred.

## Payment HTML recovery guidance —2026-10-27

The payment template displayed raw internal error codes directly. Fixed HTML-only guidance now describes rejected submissions, changed reviews, confirmation/acceptance holds, missing recovery evidence and unavailable rehearsals. Uncertain payment explicitly requires lookup and forbids starting again. Unknown codes use a fixed hold message rather than displaying internal text. API return occurs before HTML mapping, preserving exact machine codes/statuses and payloads; no service/payment/archive/authorization state machine changes.

An initial browser attempt failed at payment-error-0 because the path-only navigation helper compared pathname with a query-bearing path. This driver issue was corrected with an explicit Page.navigate and a bounded search/ready-state/alert wait. A controlled corrected baseline temporarily restored only the original raw-error template, failed at payment-error-0, and restored fixed bytes in finally. The final exact fresh --public path passes BROWSER_LOCAL_PASS118+25 JavaScript/14 no-JavaScript, with frontend Node24.22.0/npm11.19.1 and browser controller Node24.21.0/Chromium155.0.8059.84. Ten new assertions across both modes cover retained simulated-paid status/disclaimer,320px reflow,400 query error with AX alert/no raw code/no action form, Tab/visible-focus recovery link and native Enter back to paid retained status. The browser slice submits no payment/acceptance/grant action. Earlier108 reports now fail the closed count contract;13 browser report/controller/public tests pass.

Focused real PostgreSQL shop.catalog.checkout_payment_tests:17 tests in3.619s. New tests preserve API codes/statuses, remove raw/unknown private synthetic error text from HTML, retain safe error recovery without action forms and confirm no acceptance/attempt/bank effects for rejected requests. A real synthetic after-commit response loss yields one attempt/operation; the retained page offers lookup only, reconciliation runs with bank.start patched to reject blind resend, and captured recovery creates no second operation. No actual bank/provider evidence is inferred.

Exact inert source `/nix/store/cvh8mcxcfvgrp6f1d7ad34gyi5j3g4xl-shop-python-source`:264 byte-matched files/33 templates/1 CSS/no symlinks. Temporary runners use the previously disclosed retained locked wheel cache only; all hash/inventory/install controls and finite bounds remain unchanged. Prior broad backend570/proxy148 and earlier scoped tests retain historical scope; no full regression is claimed. Formal_accessibility/production_qualified remain false and all actual/full gates remain pending.

## Customer/staff support error recovery —2026-10-27

The original support template exposed raw internal codes and used href="" for recovery, retaining a rejected query. The expanded actual baseline failed at support-recovery-customer-0. Fixed HTML-only guidance now covers invalid commands/seconds, insufficient balance/reservation, stale context/request identities and missing recovery evidence; unknown codes show a fixed hold. An explicit request.path recovery link strips the query and retains the authorized customer/staff route. JSON serialization returns before HTML mapping; codes/statuses and ledger/context services are unchanged. Early denied staff/MFA/grant responses retain their existing protections.

Exact fresh --public BROWSER_LOCAL_PASS134+25 JavaScript/14 no-JavaScript passes. Sixteen new assertions cover customer and staff in both modes:400 query error with AX alert/readable text/no raw code or action form, exact query-free recovery href, actual Tab/visible focus/320px reflow and native Enter back to the same committed ledger revision and70200 available seconds. No added browser scenario reserves/spends/corrects/publishes support. Earlier118-check reports now fail closed.13 report/controller/public tests pass. Frontend Node24.22.0/npm11.19.1, browser controller Node24.21.0 and Chromium155.0.8059.84 remain selected; finite bounds unchanged.

Focused real PostgreSQL ledger/context24 tests pass in8.253s, including reservation competition, retries, corrections, archive/CAS, exact recent-MFA grants and new unchanged-state/customer-staff recovery/API-parity checks. Invalid zero/excess seconds create no event or balance effect; unknown private synthetic error text is absent from HTML. An initial focused test failed because customer requests were incorrectly inside the staff-only host/URL/session override. The fixture now checks each client in its actual configuration; no host/protection policy changed. That failed attempt is diagnostic, superseded by the final focused pass.

Exact inert source `/nix/store/6k4lq06jcsm8vssp1clq19l35dpdfxzv-shop-python-source`:264 byte-matched files/33 templates/1 CSS/no symlinks. Temporary runners retain disclosed hash-locked wheel-cache sourcing with all install controls. No broad backend/proxy rerun or actual provider/host action is claimed. Formal_accessibility and production_qualified stay false; all actual/full gates remain pending.

## Consolidated current-source local regression —2026-10-27

Accumulated staff/customer authentication and business/checkout/payment/support HTML changes justified one isolated full core-local run, followed sequentially by proxy/demo checks. Exact producer output:

```json
{"backend_duration_seconds": 171.478, "checks": 5, "elapsed_seconds": 172.77996964706108, "evidence_class": "local-synthetic", "failures": 0, "lane": "core-local", "tests": 578, "tool_identity": {}}
```

Proxy/demo output:

```text
DEMO_ACCESS_PASS checks=148 aliases=2 evidence=local-synthetic-header-level
```

Both existing120-second Django batch limits and900-second outer lane remain unchanged. The temporary wrapper only substitutes the retained hash-locked wheel cache for download sourcing, preserving frozen installs/hash checks. Core verifies real PostgreSQL18.6/UTF8 identity, migrations/no drift, all required application labels and Gunicorn health/routes. Proxy evidence is local synthetic/header-level; it is separate from retained actual browser134+public25/14. Backend code/source is unchanged from `/nix/store/6k4lq06jcsm8vssp1clq19l35dpdfxzv-shop-python-source` (264 files/33 templates/1 CSS/no symlinks); this continuation changes planning evidence only. No repeated browser/frontend build, hosted CI, formal accessibility, actual provider/host/recovery or full phase acceptance is inferred. All actual gates remain pending.
