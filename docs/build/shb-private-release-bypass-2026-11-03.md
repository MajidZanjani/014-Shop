# SHB-11-01 private release bypass-vector denial

Authority: [SHB revision 1.1](../../014-Shop-SHB-Proposal-Revision-2026-10-30.md). Phase 11 advanced inline with a single bypass-vector test; the actual Object Storage / protected-host / DNS/TLS / off-host-runner qualifications remain external gates. Parent counts stay 11/42 and 1/14.

## Invariant

SHB-11-01: "Private Object Storage releases; manifest-approved Astro snapshot behind Django authorization in isolated shop runtime … no publicly readable protected copy/JSON/assets/sourcemap/preview bypass."

Operational translation: the two routed private surfaces (`/shop/private/index.html` and `/_astro/<asset>`) must deny unauthenticated access, AND no alternative URL spelling may leak the content behind them.

## Verification

`test_shb_11_private_release_resists_bypass_vectors_against_manifest` in `backend/shop/shb/tests.InvitationTests` iterates 15 bypass vectors (path traversal, URL-encoded %2f traversal, `?preview=true`/`?sourcemap=1` query, `#preview` fragment, alternate base paths `/shop/private/{support,_astro,private-storefront,build-probe}/`, `.map` suffixes, `//`-double-slash, `.`-prefix, per-asset traversal, case variations `SHOP/PRIVATE`) and asserts each returns 301/302/400/403/404 with none of `FPGA Supporting Hours Bundle`, `Supporting Hours Bundle`, `Synthetic Company`, `shb-fpga-10h`, `shb-asic-25h`, `discount_code`, `order_reference`, or `purchase_token` in the body.

The behavior comes from the middleware's protected-path allowlist in `backend/shop/shb/middleware.py` (OLD_SALES set + protected startswith list); this commit asserts the resulting attack surface is closed so a future refactor cannot silently broaden exposed paths.

Shared regression passes **624 tests** (previously 623; +1 for SHB-11-01): 281 SHB, 95 access/recovery, 104 payment, 30 staff, 24 worker/statement-mail, 75 shared transaction/archive, nine source/catalog and six actual network-isolated adapter cases. Evidence `be46883b…json` (shared), `faf74f44…json` (focused). Browser lane unchanged at 161.

## Remaining Phase 11 external gates

Actual Object Storage integration, protected-host runtime inventory on mx1, real DNS A/AAAA + TLS ingress proof, independent runtime/fault/exhaustion/complete-loss drills (off-host runner unassigned). SHB-30 full qualification is explicitly external.

## Reproduce

```sh
python3 scripts/check_shb_retained.py --test-label shop.shb.tests.InvitationTests.test_shb_11_private_release_resists_bypass_vectors_against_manifest
python3 scripts/check_shb_retained.py --shared
python3 scripts/check_purchase_plan.py --refresh-inventory
python3 scripts/check_planning.py
```

Parent counts stay 11/42 and 1/14; current development focus remains Phase 6.
