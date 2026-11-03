# SHB-24 manual-tracking boundary (per-order display)

Authority: [SHB revision 1.1](../../014-Shop-SHB-Proposal-Revision-2026-10-30.md), including Appendix A. Phase 10's 10-01 slice is advanced inline with one explicit test; parent completion counts remain 11/42 and 1/14 until actual gates qualify. Real company inputs/adoption remain pending in the single [decision register](../decisions.md).

## Invariant

SHB-24: "Manual support-tracking boundary — No online time-ledger mutation, available/used/remaining-hour calculation, support/bundle panel or API, staff time-entry workflow or automated task-usage email. Purchased-hours display remains per order."

Operational translation: the shop does not maintain any aggregate hour counter. Even when a single customer has multiple paid orders, the staff order list and individual order views expose per-order rows only -- never a sum, "available", "used", or "remaining" value. SLL's support team tracks consumption outside the shop by hand, using each `order_reference` as a durable identifier.

## Verification

`test_staff_order_views_show_per_order_hours_only_without_cumulative_balance` in `backend/shop/shb/paid_order_tests.py` exercises the full invariant:

1. The fixture customer completes a first FPGA purchase (3 × 10h = 30h) through the setUp invitation.
2. The staff issuer issues a second invitation to the same customer with the same `Synthetic Company Limited` company name and a `SLL top-up` project reference.
3. The customer activates the new invitation on the existing browser session and places a second eligible FPGA purchase (quantity 2 → 20h). Two `PaidOrder` rows now exist.
4. The staff user is set up with a `StaffCredential`, recent MFA, and a `PaidOrderGrant` on each of the two orders.
5. `GET /staff/shb-orders/` (JSON mode):
   - Status 200.
   - Top-level JSON keyset is exactly `{orders, limit, older}` (no additional aggregate keys).
   - Each row has exactly `{id, order_reference, variant, hours_purchased}`.
   - `sorted(row['hours_purchased'] for row in orders)` equals `[20, 30]` -- not a sum.
   - The raw JSON string (lowercased) does NOT contain any of: `total hours`, `total_hours`, `hours_total`, `cumulative`, `available hours`, `remaining hours`, `used hours`, `hour balance`, `hours balance`, `balance of hours`, `bundle panel`, `time ledger`, `time-ledger`, `time entry`, `time-entry`, `task usage`, `task-usage`.
6. `GET /staff/shb-orders/` (HTML mode via `Accept: text/html`):
   - Contains `30 hours in this order` and `20 hours in this order` (two per-order rows).
   - Does NOT contain any forbidden phrase (same list, lowercased).
7. For each order, `GET /staff/shb-orders/<pk>/` returns status 200 with `purchase.hours_purchased` matching the order's own hours (30 or 20), and neither the JSON body nor the HTML contains any forbidden key or phrase.

The staff list handler at `backend/shop/shb/staff_orders.py:52` constructs rows explicitly as `[{id, order_reference, variant, hours_purchased}, ...]` with no aggregation. The HTML template at `backend/shop/shb/templates/shb/staff_orders.html` renders `{{ order.hours_purchased }} hours in this order` per row and nothing else. This commit asserts that invariant end-to-end so a future refactor cannot silently add a cumulative-balance key, a "remaining hours" calculation, or a task-usage email trigger.

Shared regression passes **611 tests** (previously 610; +1 for SHB-24): 268 SHB, 95 access/recovery, 104 payment, 30 staff, 24 worker/statement-mail, 75 shared transaction/archive, nine source/catalog and six actual network-isolated adapter cases. Django check, migrations 0029/0030 and drift pass with no new drift. [Current regression/source record](../evidence/shb/retained-tests/64898b984a7313d8e4baa73864c5be5fd8be27624fc1ae29edd21cbf9ad06385.json); focused 1-test audit record [5aa11980…json](../evidence/shb/retained-tests/5aa11980998196c85026e358575098330e890603f5601e9f1d976713700806c5.json). Browser lane unchanged at 161 checks; the assertion is backend-only.

## Reproduce

```sh
python3 scripts/check_shb_retained.py --test-label shop.shb.paid_order_tests.PaidOrderTests.test_staff_order_views_show_per_order_hours_only_without_cumulative_balance
python3 scripts/check_shb_retained.py --shared
python3 -m unittest discover -s tests -p 'test_planning_activity.py'
python3 scripts/check_purchase_plan.py --refresh-inventory
python3 scripts/check_planning.py
python3 scripts/check_purchase_plan.py
```

Normal pinned Nix/source/runtime/native/licence/OCI/CI and actual commercial/provider/refund/tax/mail/host/ingress/database/human/independent custody/post-backup/transport/restore/complete-loss qualification remain open. The authorized independent off-host runner is unassigned. Actual company inputs arrive later through docs/decisions.md; no repeated request. No real credentials/.env, production/bank-sandbox connection, host/DNS/TLS/bank/mail/storage operation or paid provision. The private Astro release and unrelated http_cache.sqlite remain unchanged. Parent counts stay 11/42 retained summaries and 1/14 documentary phases; no new SUMMARY/FULL_PASS. Current development focus remains Phase 6; this advance is a focused SHB-24 test addition within Phase 10's 10-01 scope.
