# SHB invitation-scoped FPGA checkout

Authority: [SHB revision 1.1](../../014-Shop-SHB-Proposal-Revision-2026-10-30.md). This continues the uncommitted07-03 work saved in the30 October handoff. It is a verified local checkout/acceptance/fake-payment slice. Paid-order finalization, coupon consumption, matching ASIC offers and transaction notices remain unfinished; no parent SUMMARY, requirement completion or release acceptance is asserted.

Eligible FPGA review now signs the exact minimum form, quantity, authoritative purchase/policy/document revisions, originating session and explicit synthetic review/payment deadlines. Checkout requires separate terms acceptance and privacy acknowledgement; a new FPGA review clears both checkboxes. Material edits, changed prices/policies, another invitation/session, expired review or unsupported bank amount require a new review or fail closed. ASIC still starts with Submit Request and cannot check out without its future matching offer. Its privacy acknowledgement survives Apply/Remove previews.

The existing SyntheticCheckout, SyntheticCheckoutAcceptance, payment attempt and archive are reused. SupportCheckout adds invitation/session scope; the minimum SHB form does not fabricate an old licence questionnaire or verified identity. Legacy private-resource paths retain their verified-contact checks. A shared archive helper now rechecks the same explicit scope, and the payment attempt rechecks invitation/session authorization after archive I/O before claiming a new bank dispatch. An internal call cannot start a new SHB payment without customer access; trusted reconciliation of an already dispatched attempt continues after invitation revocation/expiry.

The protected `/purchase/shb/<uuid>/` page exposes only the originating session's current purchase, acceptance and fake payment state, with CSRF/origin controls, no-store responses and no bearer in the URL. Duplicate payment clicks retain one attempt and one fake bank operation. An uncertain attempt is lookup-only. Archive failure preserves the immutable submission for exact retry without acceptance or payment; revocation/expiry during archive work prevents acceptance or dispatch. Existing nonblocking archive contention may return503; the concurrency test verifies exact retry returns the same checkout, acceptance and held coupon rather than assuming both racing HTTP requests must immediately succeed.

Additive catalog0025 and SHB0007/0008 migrations add the scoped checkout and exactly-one request/checkout coupon target. PostgreSQL guards freeze the scope, shared cart/checkout/retry/acceptance captures, reject historical-row retagging and require matching customer/variant/policy/capacity and payment-attempt provenance. FPGA and ASIC compete for the same limited coupon slots. Existing ASIC pre-offer decline/release remains available. Successful fake payment currently leaves a coupon held: consumption and safe payment-linked closure are the next work, never inferred from a clock or a browser return.

Each frozen purchase records bundle size, quantity and hours in that order only. New SHB purchases cannot enter the historical IP/time fulfilment function. No time ledger, support balance, staff time-entry screen, task email, licence/package grant or customer history panel is introduced.

## Executed evidence

- Django checks, all additive PostgreSQL18.6 migrations and `makemigrations --check --dry-run` passed.
- Final unchanged-source run: `RETAINED_SHB_TEST_PASS tests=390 duration_seconds=130.913`. This includes9 pure source/catalog checks,71 SHB cases including20 checkout cases,95 shared access/recovery,104 payment,30 staff review/navigation/preparation,75 preserved checkout/acceptance/fulfilment/archive regressions and6 adapter tests actually inside `unshare --net`. None failed or skipped. [Exact test/source record](../evidence/shb/retained-tests/71f876d388f81812a08bb3311dc76209b17b6690a8327defb46bb7257f262b8b.json).
- The75 historical transaction tests use a disposable fake-only settings module excluding only the new-IP sale gate, so they can exercise preserved services and HTTP recovery checks. The71 SHB tests use the actual gate and prove those new-sale routes stay closed. This exclusion is a test fixture, never production configuration.
- Final actual Chromium151.0.7922.173 / Node24.15.0:41 checks in JavaScript and no-JavaScript modes at320px. Native keyboard submissions record a discounted50-hour ASIC request and exact30-hour FPGA acceptance/payment in each mode. Persisted results:2 ASIC requests,2 FPGA checkouts/acceptances,2 attempts/bank operations despite duplicate clicks,2 ASIC coupon holds and0 historical fulfilments. [Exact browser/source record](../evidence/shb/retained-tests/a45fa4da54213036c4b89a33aa8a648249109d8efcbf845c5077abd1e7cf2183.json). Private empty-form screenshots: `.scratch/shb-checkout-browser-ibn6teoj`.
- A prior native Apply assertion observed status200 while the new document was still interactive and had0 loaded stylesheets. Every native submission now waits for its own changed loader and completed document before the same content/layout assertions. The failing value-free diagnostic is retained at `.scratch/shb-checkout-browser-0vydy44n/browser-failure.json`.
- The test and browser records contain identical hashes for312 current backend files and8 test/demo scripts, checked unchanged across each run. They are workspace-source evidence, not a new packaged-source/runtime qualification. The earlier14-test RED baseline belongs to the30 October checkpoint; intermediate failures were fixed before these final passes. Existing coupon tests now expect a422 missing-review/unapproved-offer denial instead of the obsolete blanket503 integration-pending response.

## Current tool boundary

Ordinary sandbox startup still cannot traverse the workspace; narrowly justified local execution was used without changing directory/host permissions. The normal offline Nix development shell cannot materialize its missing pinned dependencies. A separate attempt to build `shop-app-source` also failed resolving build dependencies; its bounded output is retained at `.scratch/shb-checkout-source-build.log`. No new `SHB_SOURCE_PASS`, Nix environment, OCI or deployed-runtime qualification is claimed.

The reproducible fallback `scripts/check_shb_retained.py` verifies the SHA256 of two already retained immutable OCI archives, their config hashes and all91 uncompressed layer hashes, then recovers only store entries into owned scratch. A temporary read-only namespace overlay exposes those bytes without registering them in the host store. Actual Python3.13.16, Django5.2.18, PostgreSQL/libpq18.6 and the installed locked distribution versions are checked before current workspace source runs on a new disposable Unix-socket database. This is a separate synthetic test lane; it does not weaken or replace `check_shb.py`, pinned Nix/build/browser gates or independent runtime qualification. The available browser versions above are explicitly different from the previously recorded155/24.21 toolchain.

The private9-file Astro snapshot remains `.scratch/shb-private-resume-t2p3r5cc/release`, manifest `ef2d68408ac264a2da888af45ec167242c1a21680990d66a772bd761b86941f3`. No frontend source or dependency pins changed. No .env, real bank/mail/storage action, protected service/host/DNS/TLS change or paid provision was used. User company inputs will arrive later through `docs/decisions.md`; they were not requested again. Unrelated `http_cache.sqlite` remains untouched.

## Reproduce

From the repository root, with the two retained archive paths named in the fallback script present:

```sh
python3 scripts/check_shb_retained.py --shared
python3 scripts/check_shb_retained.py --browser --release .scratch/shb-private-resume-t2p3r5cc/release --browser-binary /nix/store/53p8msmqxpi829zdrw6qkvaamidxy9cj-chromium-151.0.7922.173/bin/chromium --browser-node /nix/store/5a8ysg1jnj8jmzzyfcfw7rvpvnp5rfpa-nodejs-24.15.0/bin/node
python3 -m unittest discover -s tests -p 'test_planning_activity.py'
python3 scripts/check_planning.py
python3 scripts/check_purchase_plan.py
```

The normal qualification commands remain, subject to the actual missing-tool boundary:

```sh
env TMPDIR="$PWD/.scratch/auth-unicode-tmp" XDG_CACHE_HOME="$PWD/.scratch/phase2-repro-nix-cache" nix develop --offline ./ops/nixos#backend --command python3 scripts/check_shb.py --shared
env TMPDIR="$PWD/.scratch/auth-unicode-tmp" XDG_CACHE_HOME="$PWD/.scratch/phase2-repro-nix-cache" nix develop --offline ./ops/nixos#backend --command python3 scripts/check_shb_source.py
env TMPDIR="$PWD/.scratch/auth-unicode-tmp" XDG_CACHE_HOME="$PWD/.scratch/phase2-repro-nix-cache" nix develop --offline ./ops/nixos#browser --command python3 scripts/demo_shb.py --serve --release .scratch/shb-private-resume-t2p3r5cc/release
```

The last command is the usable private loopback demonstration once its pinned shell is available. Invitation/code values are printed only as paths to private files. Use Synthetic Company Limited and synthetic.invalid contacts. It supports FPGA review/acceptance/fake payment and ASIC intake; it does not complete the remaining paid-order workflow.

Next: finish per-order paid FPGA finalization, coupon consumption and safe closure, staff purchase details and ordinary durable transaction notification. Then continue assigned dated ASIC offers/withdrawal/expiry/reissue and matching acceptance. Actual commercial, bank/mail, host/ingress, Nix/image/native/licence/CI and independent recovery/runtime/human gates remain pending. No SLL support-time automation is part of that work.
