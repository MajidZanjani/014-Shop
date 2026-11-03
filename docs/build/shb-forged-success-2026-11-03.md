# SHB-19 forged payment-success rejection (SHB payment surface)

Authority: [SHB revision 1.1](../../014-Shop-SHB-Proposal-Revision-2026-10-30.md), including Appendix A. Phase 8's 08-01 slice is advanced inline with one explicit test; parent completion counts remain 11/42 and 1/14 until actual gates qualify. Real company inputs/adoption remain pending in the single [decision register](../decisions.md).

## Invariant

SHB-19: "Forged browser success or unauthenticated bank callback — No paid status, accepted purchase or paid-order confirmation."

Operational translation: the SHB payment surface (`/purchase/shb/<pk>/`) accepts exactly three action values -- `pay`, `reconcile`, `cancel` -- and exactly two body keys (`csrfmiddlewaretoken` + `action`). Any attempt to inject a smuggled "paid" indicator from the browser, or to invent a new action value, must result in a 400 rejection with zero mutation. The bank-side variant (an unauthenticated bank callback) is already structurally impossible: `synthetic_bank.CAPABILITIES.callbacks` is False and the worker drives payment lookups outbound, not via inbound callbacks.

## Verification

`test_forged_payment_success_fields_at_payment_page_cannot_mark_paid` in `backend/shop/shb/paid_order_tests.py` exercises the full invariant:

1. The fixture customer completes a review+checkout to reach the SHB payment page at `/purchase/shb/<pk>/`. No `PaidOrder` or `SyntheticBankOperation` exists yet; `SyntheticPaymentAttempt` and `SupportCheckout` counts are snapshotted.
2. For each of six forged bodies -- `{'action':'pay','status':'paid'}`, `{'action':'pay','payment_token':'fake-success-token'}`, `{'action':'pay','confirmed':'true'}`, `{'action':'pay','result':'captured'}`, `{'action':'pay','amount_minor':'0'}`, `{'action':'pay','provider_operation_id':<uuid>}` -- POST returns status 400 and all four tables are unchanged.
3. For each of seven forged action values -- `confirm`, `succeed`, `complete`, `authorized`, `ok`, `paid`, `capture` -- POST returns status 400 and the state is still unchanged.
4. Finally, POST `{'action':'pay'}` returns status 200 and `PaidOrder.objects.count()` is 1.

The rejection path is enforced at `backend/shop/shb/views.py:144-147` by `set(request.POST)-{'csrfmiddlewaretoken','action'}` (extra keys forbidden) and `request.POST.get('action') not in ('pay','reconcile','cancel')` (action allowlist). This commit documents and asserts both guards explicitly so a future refactor cannot broaden them silently.

The bank-side forged-callback clause of SHB-19 is already covered by `backend/shop/payments/notification_tests.test_hint_does_not_mark_paid_and_existing_worker_looks_up_without_start`, which exercises the hint/lookup path and asserts `synthetic_bank.CAPABILITIES.callbacks` is False -- the shop cannot be told "paid" from outside; the worker must look up the real bank state itself.

Shared regression passes **612 tests** (previously 611; +1 for SHB-19 at the SHB surface): 269 SHB, 95 access/recovery, 104 payment, 30 staff, 24 worker/statement-mail, 75 shared transaction/archive, nine source/catalog and six actual network-isolated adapter cases. Django check, migrations 0029/0030 and drift pass with no new drift. [Current regression/source record](../evidence/shb/retained-tests/2a24959efcd3a5e228a324c54224a8f169ad40440bee8823719085795e3b1642.json); focused 1-test audit record [6599b85f…json](../evidence/shb/retained-tests/6599b85ff13d527b8af809941009362446e50187086f819a2fda1f9bc4627d54.json). Browser lane unchanged at 161 checks; the assertion is backend-only.

## Reproduce

```sh
python3 scripts/check_shb_retained.py --test-label shop.shb.paid_order_tests.PaidOrderTests.test_forged_payment_success_fields_at_payment_page_cannot_mark_paid
python3 scripts/check_shb_retained.py --shared
python3 -m unittest discover -s tests -p 'test_planning_activity.py'
python3 scripts/check_purchase_plan.py --refresh-inventory
python3 scripts/check_planning.py
python3 scripts/check_purchase_plan.py
```

Normal pinned Nix/source/runtime/native/licence/OCI/CI and actual commercial/provider/refund/tax/mail/host/ingress/database/human/independent custody/post-backup/transport/restore/complete-loss qualification remain open. The authorized independent off-host runner is unassigned. Actual company inputs arrive later through docs/decisions.md; no repeated request. No real credentials/.env, production/bank-sandbox connection, host/DNS/TLS/bank/mail/storage operation or paid provision. The private Astro release and unrelated http_cache.sqlite remain unchanged. Parent counts stay 11/42 retained summaries and 1/14 documentary phases; no new SUMMARY/FULL_PASS. Current development focus remains Phase 6; this advance is a focused SHB-19 test addition within Phase 8's 08-01 scope.
