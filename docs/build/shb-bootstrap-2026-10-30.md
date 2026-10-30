# SHB revision 1.1 — first implementation batch, paused 30 October 2026

Current authority is the complete [SHB revision 1.1](../../014-Shop-SHB-Proposal-Revision-2026-10-30.md), SHA256 `ba801dff4adbfdcfa0f1e43cfe1f2d6963780476867da1b5e6f737230a472b5e`. The user explicitly requested a pause before this batch was fully verified. This is local/synthetic partial implementation, not completed SHB acceptance or a live release.

The full planning rewrite is committed and pushed as `0773373`. Exact 342 prior planning/instruction originals remain hash-bound in [the archive manifest](../archive/2026-10-30-before-shb/manifest.json). Current requirement/phase routing is in `.planning/STATE.md` and `.planning/ROADMAP.md`, not historical next-action text.

Implemented current files:

- `frontend/src/content/products/supporting-hours-bundle.md`, `scripts/compile_shb_catalog.py`, generated `catalog/shb-revisions/9584fc023a225429966ae5e8771fb95bb3ae23b3d571a24b73dffde8e1c77667.json`, `backend/shop/shb/revision.json` and `frontend/src/lib/shb.ts`: one product, exact FPGA/ASIC labels,10/25 hours, null live commercial inputs and strict content schema. An ordinary content edit cannot approve rates.
- `backend/shop/shb/catalog.py`, `forms.py`, `views.py`, templates and CSS: exact whole-bundle math, synthetic integer-money review, minimum company/billing/contact fields, Same as company phone, conditional ASIC questions and privacy/acceptance stages. FPGA review and persisted ASIC submission work; actual checkout/approved ASIC offers are unfinished.
- `backend/shop/shb/models.py`, `invitations.py`, two migrations and `middleware.py`: digest-only32-random-byte reusable invitation, Asia/Tbilisi six-calendar-month expiry with month-end clamp, current expiry/revocation, existing30-minute session cap/recovery epoch, immutable scope and no invite-based login as the company. No private saved details/history are prefilled.
- `services.py` extends the existing `QuotationRequest`, cart/snapshot records for a synthetic ASIC request. PostgreSQL locks and retry identity produce one quotation/request. No bank attempt, accepted purchase, licence or time credit is created.
- `frontend/src/pages/index.astro` and `support.astro` now contain generic access-required content. The new static private page and React selector are served only through `private_release.py`, a separately pinned manifest and the invitation gate. `_astro` assets are protected too. Changed bytes, unknown paths, source maps and symlinks deny. No public object origin, upload, DNS, certificate or ingress was changed.
- `backend/shop/config/base.py`, `urls.py`, core referrer middleware and explicit `shb_synthetic.py` integrate the new release boundary. Paused IP creation/purchase and time-panel routes deny. Existing verified-contact/resource code and historical records remain. Native no-referrer SHB forms still require Django's valid CSRF cookie/token; the narrow null-Origin exception additionally requires same-origin browser Fetch Metadata on the exact form route. Other origins/metadata and missing tokens deny.
- The Nix backend-source, reproducible-package and worker mutation-copy allowlists include only the new exact SHB JSON/CSS/template assets. Historical payment/restore fixtures now construct old snapshots through the existing domain service; owner/logout/cross-customer assertions remain, with new IP capture explicitly denied. No shared security assertion was removed.

The team tracks support usage and manually sends task emails outside the shop. New SHB code does not mutate a time ledger, calculate cumulative/used/remaining hours, build a support/bundle panel or generate task-usage emails. Old code/data remains preserved. No new dependency version or actual commercial approval was supplied.

## Executed verification and precise limits

| Observation | Result | Scope/limit |
|---|---|---|
| Focused source/money/private-release plus Django/PostgreSQL | `SHB_LOCAL_PASS checks=4 tests=29 duration_seconds=10.551 postgres=18.6` | Nine pure controls plus20 real-PostgreSQL tests; included form, calendar/expiry/revocation, no prefill, old-IP denial, native CSRF, immutable scope, concurrent same-request arbitration and recovery hold. No actual provider/host/runtime qualification. |
| Full existing frontend suite and source/output boundary | `FRONTEND_PASS checks=37 tests=138 duration_seconds=12.550` | Exact Node24.22.0/npm11.19.1, Astro static build/check, all existing default tests retained, plus new SHB source/privacy controls. Not a browser-engine run. |
| Actual loopback Django/Gunicorn/PostgreSQL demo | `SHB_DEMO_PASS checks=16` | Header/form-level: FPGA quantity3 reviews30 hours/EUR3,000 fixture total; ASIC quantity2 records50 requested hours once on retry; no payment or grant; current-cookie revocation denies. Not completed paid workflows or browser evidence. |
| Private release build |9 files, manifest SHA256 `bb507afd975241eb1a9a136556209c0d41788e4efa3ce93a68739e6a7c6b52a1` | Fresh exact frontend build retained at `.scratch/shb-private-release-t89j52jy/release`; source/runtime qualification remains false. The reused helper's `PUBLIC_BROWSER_BUILD_PASS` marker names its build tool, not public publication or successful browser execution. |
| Actual inert source comparison/import |295 exact files,8 isolated SHB imports,2 checks,3.496s | `/nix/store/dxckfmms1mkc6z7x4fzanhiki9iw8xq0-shop-python-source`; [source record](../evidence/shb/source-revisions/9685315cc2dc24efe479fe2ffa6c022a5e5c25d2e6774f95a7c17aa6a962c0b2.json). This precedes the last two test-fixture edits: refresh source verification before final qualification. No executable/deployed-runtime claim. |
| Reproducible-source packaging regression |11 tests pass | Exact SHB assets included; private inputs, symlinks and changed payloads remain rejected. Not full independent OCI/CI reproducibility. |
| Corrected shared access/security/recovery group |95 tests pass | After historical fixtures stopped opening paused IP HTTP routes; all shared assertions retained. |
| Next shared bank/adapter group |110 executed,6 failures | Six adapter guards correctly require the actual network-isolated adapter harness. The new combined runner invoked them directly. Aggregate `--shared` has **not passed**. Fix invocation using the existing adapter lane; do not merely set its guard variable. |
| Actual Chromium attempt |Failed at `browser-ready` twice | No browser flow, hydration, native-keyboard/mobile, screenshot, visual or formal accessibility pass is claimed. Private diagnostics from the second new blank-browser process are at `.scratch/shb-browser-evidence-3l1_szjf/browser-startup.log`; debugger URI redacted. Investigate on resume without changing pins/limits or unknown resources. |

The first candidate failed on missing modules, Django session iteration, a recovery fixture missing its recorded hold reference and the synthetic `testserver` host. Those were corrected using proper session keys, the existing quarantine service and an explicit localhost test client. The latest shared run confirms the95-test group; its remaining six failures concern adapter harness invocation. Full logs shown during execution are not represented as an independent retained raw-log archive.

Automatic approval review rejected a proposed reduction of the default frontend test command. That patch was not applied. The safer result keeps the original full default suite unchanged and adds SHB tests;138 frontend tests pass. No pending permission is needed for that rejected approach, and it must not be bypassed. Dedicated IP/time-accounting requirements remain deferred in the documented SHB plan; shared checks are retained.

## Reproducible commands

Use existing owned scratch/cache paths; no real credentials or `.env` are needed:

```sh
python3 scripts/compile_shb_catalog.py --check
env TMPDIR="$PWD/.scratch/auth-unicode-tmp" XDG_CACHE_HOME="$PWD/.scratch/phase2-repro-nix-cache" nix develop --offline ./ops/nixos#backend --command python3 scripts/check_shb.py
env TMPDIR="$PWD/.scratch/auth-unicode-tmp" XDG_CACHE_HOME="$PWD/.scratch/phase2-repro-nix-cache" nix develop --offline ./ops/nixos --command python3 scripts/check_frontend.py
env TMPDIR="$PWD/.scratch/auth-unicode-tmp" XDG_CACHE_HOME="$PWD/.scratch/phase2-repro-nix-cache" nix develop --offline ./ops/nixos#backend --command python3 scripts/demo_shb.py --check
python3 -m unittest discover -s tests -p 'test_reproducibility.py'
```

This command currently remains failing for the six adapter-harness cases:

```sh
env TMPDIR="$PWD/.scratch/auth-unicode-tmp" XDG_CACHE_HOME="$PWD/.scratch/phase2-repro-nix-cache" nix develop --offline ./ops/nixos#backend --command python3 scripts/check_shb.py --shared
```

Local interactive Django demonstration, with its own disposable cluster:

```sh
env TMPDIR="$PWD/.scratch/auth-unicode-tmp" XDG_CACHE_HOME="$PWD/.scratch/phase2-repro-nix-cache" nix develop --offline ./ops/nixos#backend --command python3 scripts/demo_shb.py --serve
```

The command prints a private invitation-file path; open its URL locally. Use the explicitly fictional `Synthetic Company Limited`, a `.invalid` contact and the required form fields. Ctrl-C closes only this demo and its cluster. No demo server remains running at the pause.

To use the retained private Astro snapshot, add `--release .scratch/shb-private-release-t89j52jy/release`. A fresh snapshot can be built through the existing `check_browser_public.build_public()` helper into a new empty directory under an owned `.scratch` parent, followed by `python3 scripts/compile_shb_release.py --dist <that-directory>`. Never serve the release directory through a public static server or bucket. The failing actual-browser invocation is:

```sh
env TMPDIR="$PWD/.scratch/auth-unicode-tmp" XDG_CACHE_HOME="$PWD/.scratch/phase2-repro-nix-cache" nix develop --offline ./ops/nixos#browser --command python3 scripts/demo_shb.py --check --browser --release .scratch/shb-private-release-t89j52jy/release
```

After current code stabilizes, refresh `python3 scripts/check_shb_source.py` in the pinned backend shell. The source checker requires new source files to be visible to Nix's Git input; stage only the explicit project files, never the unrelated `http_cache.sqlite` or scratch captures.

## Remaining implementation and actual gates

Resume04-01 task1: inspect the owned blank-browser startup diagnostics; correct the combined adapter test invocation with the actual existing isolated adapter harness; verify only affected failures, then refresh exact source evidence. Do not claim browser or full regression success before these pass.

Then continue the revised07/08/10 plans: scoped coupon reservation/redemption, automatic eligible FPGA immutable checkout/acceptance/payment, assigned recent-MFA ASIC review and dated matching offers, once-only paid-order finalization, staff order view and ordinary transaction/request notifications. No online time-accounting integration or task emails. Commercial/source configuration used so far is exclusively null live metadata and visibly synthetic example EUR100/200 hourly rates, zero example tax and synthetic policy revisions; these are not proposed live rates or legal/tax decisions.

The single actual-input register remains `docs/decisions.md`. Rates/currency, final policies/manual charging/ASIC adoption, seller/tax/territory, eligibility/reviewer ownership, bank/merchant, actual mail, independent off-host runtime/recovery, native/licence/OCI/CI/human and protected-host/ingress qualification remain pending. No actual bank/mail/storage/host/DNS/TLS action, paid provision or public activation occurred. Local `/tmp` currently had23GiB and the workspace47GiB free; old full-temp observations are historical, not the cause of this browser failure. Ordinary sandbox startup still required the recorded narrowly justified local exec workaround.

Saved WIP implementation: `6891c6eea5aae064e1c77f8977da31c0145dc1d6`; ordinary origin/main push succeeded. Browser startup and aggregate adapter-harness verification remain unresolved at this explicit user pause.
