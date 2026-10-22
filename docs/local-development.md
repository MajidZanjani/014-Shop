# Local product development

Use the frozen Linux development graph. No .env or production credentials are needed.

```sh
nix develop --max-jobs 1 --cores 4 ./ops/nixos --command python3 scripts/check.py dev
```

This bounded command runs frontend typecheck/build/tests, core-local (including catalog API and real PostgreSQL owner/retry tests), worker-smoke, isolated fake adapters, contracts-local and catalog cross-language conformance. `LOCAL_DEVELOPMENT_PASS` is local/synthetic evidence only. It never invokes full qualification, inventory, reproducibility or deployment pending paths, and does not change their results.

Safety review: core-local starts/cleans only a fresh token-owned PostgreSQL cluster and owned Gunicorn, without outage/restart injection. Worker-smoke excludes offhost-tagged interruption tests; bounded lease/concurrency and source-copy mutation tests use disposable rows. Fake adapters use an isolated child network namespace and reserved synthetic destinations. Contracts-local uses a mocked handler exception, never stops PostgreSQL. Frontend/schema/conformance tests modify disposable source copies only. No resource-exhaustion lane is selected. Root execution uses the existing unprivileged development identity for its new cluster. Set SHOP_TEST_SCRATCH to a short, owned, traversable directory if socket path limits require it. Process timeouts and cleanup affect only newly owned children.

To inspect the working catalog/configurator:

```sh
nix develop --max-jobs 1 --cores 4 ./ops/nixos --command python3 scripts/demo.py --backend
```

Open http://127.0.0.1:4321. Static files are served only from frontend/dist on loopback. With --backend, /api/ and /purchase/ are forwarded to an owned loopback Gunicorn with a fresh synthetic PostgreSQL database; Ctrl-C cleans only its owned processes/data. Without --backend the static preview still works. The canonical customer hostname remains https://shop.xspi.pro. Select families, term, RDP band/optional estimate, Altera fixed/floating counts and support packages. Validation and pending eligibility update immediately. No host IDs, business information, payment or submission; no browser persistence. Support quantities describe an optional addition, with zero meaning none. The parser bound of 1,000,000 is not an entitlement grant.

The canonical public draft is frontend/src/content/products/xspi.md (JSON-compatible YAML). `python3 scripts/compile_catalog.py` validates source identity/taxonomy and emits one content-addressed immutable public revision, the browser module and identical backend public manifest. `--check` rejects stale outputs. It cannot approve rates or rights. Private approvals and immutable private revisions require the later protected approval workflow; this slice contains no private manifest or invented approval.

Django exposes GET /api/v1/catalog/ and POST /api/v1/configurations/validate/ (JSON only, 8 KiB bound, closed fields, no input echo, stateless/no persistence). This public evaluator is separate from protected configuration persistence. Backend validation independently enforces the same conformance cases; the static preview does not submit anything.

The next ready local slice adds POST /api/v1/configuration-drafts/ and GET /api/v1/configuration-drafts/{uuid}/. It uses Django authenticated sessions, CSRF on save, owner-scoped reads, revision checks and a PostgreSQL unique owner/request ID for retry arbitration. Only valid public configurations are stored. Same-key changes conflict; stale revisions fail. These endpoints are explicitly restricted to local/synthetic environments, reject staff accounts, and remain closed in production. No customer registration/login, verified-email journey or staff MFA is claimed; tests establish synthetic sessions through Django. UI save/resume and production activation require those protected access prerequisites. These are draft selections, never order acceptance or approved rights.

Automatic development CI runs the lightweight frontend/schema/conformance subset on push/PR; the full ordinary local command also exercises Django/PostgreSQL. Public Actions inspection at task start returned zero runs, so hosted availability/permission has not been demonstrated. Automatic development CI is separate from `.github/workflows/ci.yml` manual specialized qualification. GitHub-hosted availability/billing permission is account-controlled; preparation does not prove a run or authorize billing changes. No production secrets or host runners. Full outage/restart/exhaustion/recovery checks retain original independent-runner authorization. Pending gates and next order: [.planning amendment](../.planning/EXECUTION-AMENDMENT-2026-10-22.md).

The Django /purchase/simple/ fallback is usable without JavaScript in the --backend demo: select the vendor and its families, term, RDP band and Altera access counts, then Review configuration. It uses the same evaluator and CSRF protection, rejects incompatible fields and never saves/submits an order. Only cleaned selections are redisplayed. The static no-JavaScript page also lists all families.
