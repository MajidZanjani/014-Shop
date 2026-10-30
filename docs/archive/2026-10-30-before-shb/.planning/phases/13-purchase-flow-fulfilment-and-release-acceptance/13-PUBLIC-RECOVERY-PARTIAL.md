# Public recovery response — local partial evidence

2026-10-28; quick261028-b7f under13-01 task5, OPS-02/AUTH-01/UAT-03. Continues verified0f4a063 authentication recovery; commercial inputs remain pending under the user's continuation.

## Reproduced failures and behavior

Original transport/real-React baseline has3 failures: the explicit recovery response is unclassified, a late private body is accepted, and a verified customer view remains displayed. Initial frontend correction passes136 tests/32 checks and browser227, but a controlled follow-up exposes2 further failures: an older session response can rebase a cleared marker, and a fresh same-context reconnect can revive an older private body. These intermediate results are retained separately from final-source qualification.

The existing exact JSON recovery503 now emits fixed X-Shop-Access-Recovery:pending. Only that status/header pair starts client recovery; arbitrary error bodies stay unread. An ApiError carries the closed local classification, the existing parent cleanup removes private drafts/cart/quotation/configuration/input/pending state, and fixed human guidance offers manual reconnect. Ordinary503/network uncertainty retains existing exact pending-write retries. No automatic POST replay, browser persistence, new route/channel or authority.

An opaque module-only recovery generation changes on the explicit signal. Every response checks its originating generation before/after JSON, so earlier private/session/verification responses cannot restore context or return stale bodies, including after a fresh same-context reconnect. Existing comparison-only context/MFA/resource authority and CSRF/no-store controls remain. The marker/generation grants no access.

## Final-source verification

- FRONTEND_PASS checks=32 tests=137 duration_seconds=10.769; exact Node24.22.0/npm11.19.1, allowlisted fresh source, type/Astro check/build, network-isolated build, real React/transport and privacy/hash controls.
- Focused real PostgreSQL access/recovery tests63 in17.811s, including actual JSON response-header/503/no-store and existing authentication/form/CSRF/epoch/effect behavior. Backend business logic is unchanged; prior full624 tests/5 checks194.530s and proxy148/2 belong to0f4a063 before this fixed header, not a new full run.
- CATALOG_PASS checks117 tests121;91 configuration/26 cart parity cases remain unchanged.
- Final fresh BROWSER_LOCAL_PASS: private134, public JavaScript79/no-JavaScript14 (227 total), roles2/modes2, Chromium155.0.8059.84/controller Node24.21.0; frontend Node24.22.0/npm11.19.1. Evidence local-synthetic-browser-engine; formal_accessibility:false and production_qualified:false. Closed report/controller/public tests13 pass and older76-count reports are rejected.
- Source /nix/store/kxjilvd16zhhg9ap7r5j87hd6qf4mj7k-shop-python-source matches272 allowed files/33 templates/1 CSS byte for byte, no symlinks. PostgreSQL18.6 and migration0007/no drift remain.

The three new browser assertions use the existing bounded CDP interception to fulfill one local logout request with the fixed recovery503, verify private cleanup/manual controls, and reconnect explicitly. A read-only session check proves the backend remained authenticated: no actual logout, quarantine, restore or safe reopening was performed by that scenario. Existing native-keyboard/no-JavaScript, normal authentication, scope/privacy and exact response-loss retry cases remain in the fresh producer. Browser success is not formal accessibility or real channel/provider qualification.

## Reproduction, diagnostics and limits

Use owned .scratch/auth-unicode-tmp with frozen ops/nixos#default/browser shells. Final commands: scripts/check_frontend.py; .scratch/auth-recovery-focused.py; scripts/check_catalog.py; .scratch/run-public-exact.py; unittest discover -s tests -p test_browser*.py. Cache wrappers substitute only retained locked-wheel download sourcing, preserving hashes/install checks. Shared full128MiB /tmp and Nix store are untouched.

Logs .scratch/public-recovery-{baseline,frontend,rebase-baseline,frontend-final,backend,catalog,browser,browser-final,source,source-qualified}.log retain controlled failures, intermediate and final successes. The first browser-contract unittest invocation named a nonexistent plural controller module and omitted the tests import path; corrected discovery runs the actual13 cases across three modules. It is a harness diagnostic, not a product pass. Backend/frontend/browser/controller finite limits and pins are unchanged. No actual mail/bank/host/DNS/TLS/deployment/recovery or commercial/legal approval.

Next source-required local design is restore-startup quarantine before any data/effect exposure when restored database state contains an unheld AccessEpoch. This design has not been produced. Preserve read-only complete-window lookup, tracked unfinished admission, no blind financial retry and no adapter I/O under DB locks. Actual startup/traffic/egress isolation, post-point reconciliation, external MFA reset, independent complete-loss/custody/retention and full acceptance remain pending.
