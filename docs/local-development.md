# Local product development

Use the frozen Linux development graph. No .env or production credentials are needed.

```sh
nix --extra-experimental-features 'nix-command flakes' develop --max-jobs 1 --cores 4 ./ops/nixos --command python3 scripts/check.py dev
```

This bounded command runs frontend typecheck/build/tests, core-local (including catalog API and real PostgreSQL owner/retry tests), worker-smoke, isolated fake adapters, contracts-local and catalog cross-language conformance. `LOCAL_DEVELOPMENT_PASS` is local/synthetic evidence only. It never invokes full qualification, inventory, reproducibility or deployment pending paths, and does not change their results.

Safety review: core-local starts/cleans only a fresh token-owned PostgreSQL cluster and owned Gunicorn, without outage/restart injection. Worker-smoke excludes offhost-tagged interruption tests; bounded lease/concurrency and source-copy mutation tests use disposable rows. Fake adapters use an isolated child network namespace and reserved synthetic destinations. Contracts-local uses a mocked handler exception, never stops PostgreSQL. Frontend/schema/conformance tests modify disposable source copies only. A dedicated five-request loopback proxy test rejects unapproved Host headers and permits the two documented local aliases. No resource-exhaustion lane is selected. Root execution uses the existing unprivileged development identity for its new cluster. Set SHOP_TEST_SCRATCH to a short, owned, traversable directory if socket path limits require it. Process timeouts and cleanup affect only newly owned children.

To inspect the working catalog/configurator:

```sh
nix --extra-experimental-features 'nix-command flakes' develop --max-jobs 1 --cores 4 ./ops/nixos --command python3 scripts/demo.py --backend
```

Open http://127.0.0.1:4321. Static files are served only from frontend/dist on loopback. With --backend, /api/ and /purchase/ are forwarded to an owned loopback Gunicorn with a fresh synthetic PostgreSQL database; Ctrl-C cleans only its owned processes/data. Without --backend the static preview still works. The canonical customer hostname remains https://shop.xspi.pro. Select families, term, RDP band/optional estimate, Altera fixed/floating counts and support packages. Validation and pending eligibility update immediately. No host IDs, business information, payment or submission; no browser persistence. Support quantities describe an optional addition, with zero meaning none. The parser bound of 1,000,000 is not an entitlement grant.

The canonical public draft is frontend/src/content/products/xspi.md (JSON-compatible YAML). `python3 scripts/compile_catalog.py` validates source identity/taxonomy and emits one content-addressed immutable public revision, the browser module and identical backend public manifest. `--check` rejects stale outputs. It cannot approve rates or rights. Private approvals and immutable private revisions require the later protected approval workflow; this slice contains no private manifest or invented approval.

Django exposes GET /api/v1/catalog/ and POST /api/v1/configurations/validate/ (JSON only, 8 KiB bound, closed fields, no input echo, stateless/no persistence). This public evaluator is separate from protected configuration persistence. Backend validation independently enforces the same conformance cases; the static preview does not submit anything.

The implemented local draft slice provides POST /api/v1/configuration-drafts/ and GET /api/v1/configuration-drafts/{uuid}/. It uses Django authenticated sessions, CSRF on save, owner-scoped reads, revision checks and a PostgreSQL unique owner/request ID for retry arbitration. Only valid public configurations are stored. Same-key changes conflict; stale revisions fail. These endpoints are explicitly restricted to local/synthetic environments, reject staff accounts, and remain closed in production. A captured-email verification journey and UI save/resume are now available only in local/synthetic mode. Real customer verification, production activation, shared contact roles and staff MFA remain pending. These are draft selections, never order acceptance or approved rights.

Automatic development CI runs the lightweight frontend/schema/conformance subset on push/PR; the full ordinary local command also exercises Django/PostgreSQL. The hosted workflow [passed at d9d088a](https://github.com/MajidZanjani/014-Shop/actions/runs/39761244219); this establishes only that development subset, not specialized release qualification. Automatic development CI is separate from `.github/workflows/ci.yml` manual specialized qualification. GitHub-hosted availability/billing permission is account-controlled; preparation does not prove a run or authorize billing changes. No production secrets or host runners. Full outage/restart/exhaustion/recovery checks retain original independent-runner authorization. Pending gates and next order: [.planning amendment](../.planning/EXECUTION-AMENDMENT-2026-10-22.md).

The Django /purchase/simple/ fallback is usable without JavaScript in the --backend demo: select the vendor and its families, term, RDP band and Altera access counts, then Review configuration. It uses the same evaluator and CSRF protection, rejects incompatible fields and never saves/submits an order. Only cleaned selections are redisplayed. The static no-JavaScript page also lists all families.


## Captured verification and save/resume

After updating your checkout, start the --backend demo above and open http://127.0.0.1:4321. Under “Save your configuration”:

1. Enter a synthetic address such as engineer@synthetic.invalid and request a code. Real email domains are rejected; no SMTP runs.
2. The demo terminal prints a private captured-mail directory. Open its newest file locally and copy only the value after `Verification code:`. These files are mode0600 under an owned mode0700 directory, outside public/static output. There is no public inbox or code-bearing URL. Do not share the file or code.
3. Paste the code into the requesting browser and select Verify and continue. Codes expire in ten minutes and can be consumed once. Five wrong attempts lock that challenge; three requests per email or browser in ten minutes are the local demonstration limits.
4. Complete a valid configuration and select Save configuration draft. Refresh the page: your verified session can list and resume its latest20 saved drafts. Edits followed by save create a new snapshot; retrying an unchanged uncertain save uses its original request identity.
5. Sign out to revoke that browser session and clear the visible configuration. Codes, identities and drafts are synthetic; stopping/restarting the disposable demo destroys its database and capture directory. This is persistence within the running demo, not production recovery evidence.

All customer requests use reviewed same-origin browser transport, CSRF for POST, no-store responses and host-only HttpOnly Strict session cookies. Local HTTP permits non-Secure cookies only in local/synthetic mode; every customer endpoint is closed outside those modes. Successful verification rotates both session and CSRF identity. Authenticated but unverified sessions, inactive/staff identities and unrelated customer resources are denied. Owner membership is explicit through the saved draft's owner relation; matching email domains grant nothing. Shared purchasing/invoice/technical memberships and real email/HTTPS delivery require later implementation/qualification.

The static build does not fetch the customer API; the reviewed transport rejects build-time calls, absolute URLs, unapproved endpoints and code-bearing queries. Codes, email and retry keys stay in transient UI memory; session/CSRF cookies are the only browser persistence added. No host identifiers, bank operations, legal acceptance or payable offers are introduced.


### Multi-line draft cart

After synthetic verification, “Your draft cart” supports adding the current configuration (one IP licence at quantity one), independent support-only purchases, changing support quantity, loading/replacing an IP line, and removing individual lines. Optional configurator support becomes a separate support line. Each explicit IP addition gets a new line identity; no scopes are silently merged. At most twenty lines are allowed. Refreshing the page resumes the verified owner's cart while this disposable backend runs.

Every save records a versioned snapshot. Concurrent stale edits are rejected and require Reload cart before another edit. An uncertain network outcome exposes Retry last cart save, retaining the exact request and line identities until confirmed. No cart data enters browser persistence. Prices/totals remain null, all checkout is disabled, and quoted support hours grant no credit. Higher-volume lines keep the entire cart in quotation status. These draft snapshots do not establish approved quote, acceptance, payment or recovery evidence.

Backend cart tests use disposable PostgreSQL rows and two bounded concurrent requests; they perform no outage, restart, exhaustion or fault injection. The React test simulates a lost HTTP response in a transport stub only; it proves exact retry and separate line behavior without interrupting a process or network. Shared browser/backend cart conformance covers 26 valid/invalid cases. Full browser accessibility review remains separate.


## Local staff authentication and assigned review

`nix develop --max-jobs 1 --cores 4 ./ops/nixos --command python3 scripts/demo.py --backend --staff` starts the existing customer preview plus a separate staff process at `http://staff.localhost:4322/staff/`. Both bind to loopback and use one newly owned disposable database. Browser resolution of `staff.localhost` must be available locally; no hosts/DNS/TLS configuration is changed. The terminal prints a private staff-capture directory, containing a generated `demo-reviewer` password. This is synthetic fixture material; do not copy it into chat, logs or public output. The demo assigns this account exactly one newly created support-only quotation fixture. It does not assign existing customer requests.

The staff sign-in page works without JavaScript: enter the generated username/password, then read the new private `Code:` file and submit the possession code in the same browser. Password alone grants no staff session. Codes expire in five minutes and accept at most five attempts; a code can be consumed once. Five password/challenge requests per username per ten minutes bound the local rehearsal. Successful two-factor verification rotates session and CSRF identity. Staff use separate host-only `shop_staff_sessionid` / `shop_staff_csrftoken` cookies; local HTTP is limited to local/synthetic mode. Customer hosts cannot serve the staff app, and customer URLs expose no staff routes.

Assigned quotation pages require verification within five minutes and an explicit per-resource reviewer grant; staff/superuser flags alone grant no access to a quotation. Sessions expire after fifteen minutes. Sign out and sign in again to refresh verification. Staff can read captured selections only. There is no approval, pricing, acceptance, payment, fulfilment or support-credit action. HTML responses are no-store, use no-referrer, block framing/scripts and restrict form submissions to the same origin.

For a separately owned local/synthetic database, the operator-only `manage.py local_staff` command supports `provision`, `reset`, `revoke`, `grant` and `revoke-grant`, with `--username`; provision/reset additionally require a mode0700 owned `--capture-root`, and grant/revoke-grant require `--quotation UUID`. Never put passwords/codes in command arguments. Provision refuses existing identities; no customer account can enroll itself. Reset/revoke changes credential generation, invalidates old MFA sessions/challenges and removes existing assignments. Recovery requires explicit reassignment; no web recovery bypass exists. These commands are unavailable outside local/synthetic mode.

This is a two-factor **rehearsal using private local captures**, not qualified production MFA or factor delivery. Real factor enrollment/delivery, independent device/custody, recovery audit and restored-state invalidation, staff HTTPS/hostname approval and production access remain pending. The optional demo and tests touch no existing host services. Stop with Ctrl-C to remove owned demo processes/database/capture files.

Evidence: quick261023-72i records 68 core-local tests, a loopback proxy test and successful startup of both preview processes. The additional manual HTTP sign-in check was blocked by automatic approval review before reading synthetic fixture credentials; it remains pending specific authorization. No real credentials were accessed, no workaround was attempted, and the owned demo was stopped cleanly.
