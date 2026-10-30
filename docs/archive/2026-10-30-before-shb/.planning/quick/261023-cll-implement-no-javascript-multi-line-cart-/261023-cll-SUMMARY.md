---
quick_id: 261023-cll
status: complete
implementation_commit: 691ce9f
---
# No-JavaScript saved multi-line cart

Django /purchase/cart/ supports verified-owner separate IP/support additions, edits and removals. Shared transactional store preserves existing JSON contracts, validation, owner locks, exact retry reconciliation and version/catalog conflicts. Forms reconstruct exact retained owner base revisions using stable line/request IDs; retries remain exact after subsequent changes. Strict bounded fields/CSRF, fixed303 redirects, no private input echo, no-store/referrer/CSP; no order/acceptance/quotation/payment/credit effects. Access/preview/history link to cart. Local development/build docs refreshed.

CORE_LOCAL_PASS checks5 tests170 duration39.274s:157 Django plus13 actual Gunicorn transport observations on owned PostgreSQL18.6/UTF8. Six new targeted tests cover actual captured access, complete mixed editing, support-only/removal, form/API interoperability, replay after edits/catalog changes, request conflict/stale saves, invalid domain/support/max-line rules, strict queries/duplicates/body limits/CSRF, owner/environment denial and real concurrent form/JSON first-save arbitration. Existing API concurrency tests remain passing. Three new Gunicorn route observations cover access200 and unauthenticated cart/history401.

Actual Nix source /nix/store/pb2xv8am5xp6gi36r3w99xxwzz5nxwqh-shop-python-source:126 files18 templates, exact bytes/allowlist/no symlinks verified. Frontend/proxy unchanged; prior scoped results retained. Full browser/accessibility, real customer delivery, commercial/production/off-host acceptance pending. No Country/tax decisions. Phase1 last complete; focus7; Phase02 remains8/18.

Next: deliberate quotation-request capture from displayed saved cart revision without JavaScript, reusing existing owner/retry/transaction behavior. Continue after immediate commit/sync as authorized.
