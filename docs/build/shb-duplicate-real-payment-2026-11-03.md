# SHB-21 duplicate real payment identifiable by staff

Authority: [SHB revision 1.1](../../014-Shop-SHB-Proposal-Revision-2026-10-30.md), including Appendix A. Phase 8's 08-01 slice advances inline with one explicit staff-identifiability assertion; parent completion counts remain 11/42 and 1/14 until actual gates qualify.

## Invariant

SHB-21: "Uncertain payment dispatch or duplicate real payment — Reconcile; no blind second charge or duplicate purchase; staff can identify the original order."

Operational translation: once a payment is captured and a PaidOrder exists, any further `action=pay` POST against the same payment path -- a "duplicate real payment" attempt -- must be idempotent at the bank layer (no second SyntheticBankOperation, no second SyntheticPaymentAttempt) and visible to staff as a single order with its original reference.

## Verification

`test_duplicate_real_payment_leaves_one_order_identifiable_by_staff` in `backend/shop/shb/paid_order_tests.py`:

1. `self.pay()` commits one PaidOrder, one SyntheticPaymentAttempt and one SyntheticBankOperation. The attempt and operation primary keys are snapshotted.
2. Four repeated client `POST action=pay` calls against the same payment path each return 200 (idempotent).
3. After the duplicates: `PaidOrder.objects.count() == 1`, `SyntheticPaymentAttempt.objects.count() == 1` with the same pk, `SyntheticBankOperation.objects.count() == 1` with the same pk, `PurchaseNoticeDelivery.objects.count() == 1`.
4. Staff identifiability: `GET /staff/shb-orders/` returns `{'orders': [one row], ...}` whose `id` and `order_reference` match the single committed order; `GET /staff/shb-orders/<pk>/` returns 200 with `purchase.hours_purchased == 30` and `details.company_name == 'Synthetic Company Limited'`.

The backbone SHB-21 invariants are already covered elsewhere:
- `checkout_tests.test_uncertain_dispatch_is_lookup_only_and_internal_reconciliation_survives_invite_expiry` -- uncertain-attempt lookup semantics,
- `paid_order_tests.test_concurrent_finalization_is_one_order_and_one_concession` -- concurrent finalize converges to one order,
- `paid_order_tests.test_uncertainty_never_finalizes_or_releases_and_lookup_after_expiry_recovers` -- recovery through reconcile,
- `payments/operation_tests.test_timeout_after_commit_lookup_recovers_and_duplicate_lookup_is_once` -- bank-side duplicate-lookup idempotency.

This commit closes the explicit staff-identifiability clause so a future refactor cannot silently fan out duplicates into two visible rows at the staff order list.

Shared regression passes **615 tests** (previously 614; +1 for SHB-21 staff-identifiability): 272 SHB, 95 access/recovery, 104 payment, 30 staff, 24 worker/statement-mail, 75 shared transaction/archive, nine source/catalog and six actual network-isolated adapter cases. Django check, migrations 0029/0030 and drift pass with no new drift. [Current regression/source record](../evidence/shb/retained-tests/ad241ffe8cfbe5d6c2c5a4e036a73d6176f3dc2512224c279c799913b2a0f39f.json); focused 1-test audit record [d301ad9a…json](../evidence/shb/retained-tests/d301ad9ad3521a337318599c8705d96e754df13c8449af36cb2202b340139ceb.json). Browser lane unchanged at 161 checks.

## Reproduce

```sh
python3 scripts/check_shb_retained.py --test-label shop.shb.paid_order_tests.PaidOrderTests.test_duplicate_real_payment_leaves_one_order_identifiable_by_staff
python3 scripts/check_shb_retained.py --shared
python3 -m unittest discover -s tests -p 'test_planning_activity.py'
python3 scripts/check_purchase_plan.py --refresh-inventory
python3 scripts/check_planning.py
python3 scripts/check_purchase_plan.py
```

Normal pinned Nix/source/runtime/native/licence/OCI/CI and actual commercial/provider/refund/tax/mail/host/ingress/database/human/independent custody/post-backup/transport/restore/complete-loss qualification remain open. The authorized independent off-host runner is unassigned. Actual company inputs arrive later through docs/decisions.md; no repeated request. No real credentials/.env, production/bank-sandbox connection, host/DNS/TLS/bank/mail/storage operation or paid provision. Parent counts stay 11/42 retained summaries and 1/14 documentary phases; no new SUMMARY/FULL_PASS. Current development focus remains Phase 6.
