# SHB-20 duplicate messages converge to one reference

Authority: [SHB revision 1.1](../../014-Shop-SHB-Proposal-Revision-2026-10-30.md), including Appendix A. Phase 8's 08-01 slice is advanced inline with one explicit chain test; parent completion counts remain 11/42 and 1/14 until actual gates qualify. Real company inputs/adoption remain pending in the single [decision register](../decisions.md).

## Invariant

SHB-20: "Duplicate/out-of-order bank messages and process interruption — Correct final bank/order state, one order finalization, one coupon redemption and repeat-safe transaction notifications carrying the same order reference."

Operational translation: once a purchase is paid, every subsequent duplicate at any layer -- customer-visible POSTs, mail-worker iterations, or transaction-notice-worker iterations -- must leave the single committed state unchanged and produce no new side effects. Transaction notices that are emitted for the paid order must all carry that one order's reference.

## Verification

`test_duplicate_pay_reconcile_and_worker_iterations_keep_one_order_and_one_reference` in `backend/shop/shb/paid_order_tests.py` chains the duplicates across all three layers:

1. **Customer POST layer:** after `self.pay(discount=True)` produces one `PaidOrder` and one consumed `DiscountReservation`, three repeated cycles of `POST action=pay` + `POST action=reconcile` each return 200. `PaidOrder.objects.count() == 1`, `SyntheticBankOperation.objects.count() == 1`, `DiscountReservation.objects.count() == 1`, `reservation.state == 'consumed'`, `reservation.consumed_order_id` unchanged.
2. **Purchase-mail worker layer:** `purchase_mail.execute_once()` is called three times. The first returns True and creates exactly one `PurchaseNoticeCapture`; the next two return False. The `PurchaseNoticeDelivery` row's primary key is the same at every observation.
3. **Transaction-notice worker layer:** `shop.worker.services.execute_once()` is drained to False (while-loop). Every resulting `TransactionNoticeCapture` row has `notice.payload['body']['reference'] == PaidOrder.payload['order_reference']` and `notice.payload['actual_email_sent'] is False`. Five additional `execute_once()` calls after the drain all return False. `TransactionNoticeCapture.objects.count()` is stable through those calls.
4. **Final re-assertion:** `PaidOrder.objects.count() == 1`, `SyntheticBankOperation.objects.count() == 1`, `DiscountReservation.objects.get().state == 'consumed'`, `consumed_order_id` unchanged from the initial pay.

The per-layer tests already exist (`test_one_order_coupon_and_notice_...` repeats pay+reconcile; `test_concurrent_finalization_...` asserts one-order under race; `test_mail_failure_and_expired_claim_...` asserts purchase-mail idempotency; `test_duplicate_reordered_hints_...` on the payments side covers duplicate bank hints). This commit chains all three idempotency layers plus the reference-stability clause into a single explicit SHB-20 assertion so a future refactor cannot silently fan out a notice chain whose reference drifts.

Shared regression passes **614 tests** (previously 613; +1 for SHB-20 chain): 271 SHB, 95 access/recovery, 104 payment, 30 staff, 24 worker/statement-mail, 75 shared transaction/archive, nine source/catalog and six actual network-isolated adapter cases. Django check, migrations 0029/0030 and drift pass with no new drift. [Current regression/source record](../evidence/shb/retained-tests/54f459219986f2ad2c15c0098b0e0fb9f25d486d40ec48552165564f93030aa1.json); focused 1-test audit record [ebb1fd7d…json](../evidence/shb/retained-tests/ebb1fd7dc923d7d2408b1055f958d050dfbdcb11f9ab841f14be63e38a8b773b.json). Browser lane unchanged at 161 checks; the assertion is backend-only.

## Reproduce

```sh
python3 scripts/check_shb_retained.py --test-label shop.shb.paid_order_tests.PaidOrderTests.test_duplicate_pay_reconcile_and_worker_iterations_keep_one_order_and_one_reference
python3 scripts/check_shb_retained.py --shared
python3 -m unittest discover -s tests -p 'test_planning_activity.py'
python3 scripts/check_purchase_plan.py --refresh-inventory
python3 scripts/check_planning.py
python3 scripts/check_purchase_plan.py
```

Normal pinned Nix/source/runtime/native/licence/OCI/CI and actual commercial/provider/refund/tax/mail/host/ingress/database/human/independent custody/post-backup/transport/restore/complete-loss qualification remain open. The authorized independent off-host runner is unassigned. Actual company inputs arrive later through docs/decisions.md; no repeated request. No real credentials/.env, production/bank-sandbox connection, host/DNS/TLS/bank/mail/storage operation or paid provision. The private Astro release and unrelated http_cache.sqlite remain unchanged. Parent counts stay 11/42 retained summaries and 1/14 documentary phases; no new SUMMARY/FULL_PASS. Current development focus remains Phase 6; this advance is a focused SHB-20 chain-test addition within Phase 8's 08-01 scope.
