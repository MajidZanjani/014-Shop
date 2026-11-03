# SHB-22 reconcile continues after invitation expiry

Authority: [SHB revision 1.1](../../014-Shop-SHB-Proposal-Revision-2026-10-30.md), including Appendix A. Phase 8's 08-01 slice is advanced inline with one explicit test; parent completion counts remain 11/42 and 1/14 until actual gates qualify. Real company inputs/adoption remain pending in the single [decision register](../decisions.md).

## Invariant

SHB-22: "Payment notification or ASIC review after invitation expiry — Existing work reconciles/continues; no new checkout through expired access."

Operational translation: when a customer has in-flight purchase work (uncertain payment attempt pending reconciliation) and their invitation elapses past its calendar expiry, the shop must:

1. Deny customer-side access to the payment and purchase surfaces (the middleware returns 403 as soon as `invitations.current(request)` returns None).
2. Still complete the existing work via the worker/archive-driven path: `checkout_payment.reconcile(customer, saved_id, archive)` captures the attempt from the real bank state and `finalize_shb` creates the `PaidOrder`.
3. Expose the finalized order to assigned staff through their existing grant and recent-MFA session, which is independent of the customer invitation lifecycle.

The ASIC-review-after-expiry angle of SHB-22 was already covered by `backend/shop/shb/review_tests.test_clarification_preserves_discount_after_claim_and_invitation_expiry`. This commit closes the payment-notification-after-expiry angle at the SHB payment surface.

## Verification

`test_payment_can_be_reconciled_after_invitation_expiry_without_new_checkout` in `backend/shop/shb/paid_order_tests.py`:

1. The fixture customer completes `/purchase/simple/` review+checkout (302 → `/purchase/shb/<pk>/`).
2. The first POST `action=pay` runs with a patched `checkout_payment.pay` that injects `fault='after_commit'`, yielding a 409 response. `SyntheticPaymentAttempt.state == 'uncertain'`. No `PaidOrder` exists.
3. `self.saved().pk` is captured.
4. With `patch('shop.shb.invitations.now', return_value=self.invitation.expires_at + timedelta(days=1))`:
   - `GET /purchase/shb/<pk>/` → 403.
   - `POST /purchase/shb/<pk>/ action=pay` → 403.
   - `POST /purchase/simple/ action=submit quantity=1` (fresh checkout attempt) → 403.
   - `PaidOrder.objects.exists()` is False at every point.
   - Direct worker call: `with PreparedArchive(Path(self.directory.name)) as archive: result = checkout_payment.reconcile(self.customer, saved_id, archive)`.
   - `result.attempt.provider_status == 'captured'`.
   - `PaidOrder.objects.count() == 1`.
5. Outside the patch:
   - `order.payload['purchase']['hours_purchased'] == 30`.
   - `order.payload['purchase']['variant_id'] == 'shb-fpga-10h'`.
   - Staff with `StaffCredential` + recent MFA + `PaidOrderGrant` can read `/staff/shb-orders/<pk>/`: status 200, `json()['purchase']['hours_purchased'] == 30`.

The middleware guard that produces the customer-side 403 is at `backend/shop/shb/middleware.py:37-38`: `request.shb_invitation = current(request); if request.shb_invitation is None: return denied()`. The worker-reconcile path is at `backend/shop/catalog/checkout_payment.py:195-202`: `reconcile(...)` writes the bank-looked-up state onto the attempt and then calls `finalize_shb(row, archive)`, which chains to `shop.shb.paid_orders.finalize(current.checkout.owner, current.checkout_id, archive)`. That finalize path uses the archived checkout owner, not the request session, so invitation expiry is irrelevant to it.

Shared regression passes **613 tests** (previously 612; +1 for SHB-22 at the SHB surface): 270 SHB, 95 access/recovery, 104 payment, 30 staff, 24 worker/statement-mail, 75 shared transaction/archive, nine source/catalog and six actual network-isolated adapter cases. Django check, migrations 0029/0030 and drift pass with no new drift. [Current regression/source record](../evidence/shb/retained-tests/81aeddaac29c61435e8cee0f03466f9d5a2817c67ea790fc21f3322a7ea3f18b.json); focused 1-test audit record [77a41c1c…json](../evidence/shb/retained-tests/77a41c1c2d9904aa956a0a68005ec48527dfbee6ad7426333e3ea641ddd34273.json). Browser lane unchanged at 161 checks; the assertion is backend-only.

## Reproduce

```sh
python3 scripts/check_shb_retained.py --test-label shop.shb.paid_order_tests.PaidOrderTests.test_payment_can_be_reconciled_after_invitation_expiry_without_new_checkout
python3 scripts/check_shb_retained.py --shared
python3 -m unittest discover -s tests -p 'test_planning_activity.py'
python3 scripts/check_purchase_plan.py --refresh-inventory
python3 scripts/check_planning.py
python3 scripts/check_purchase_plan.py
```

Normal pinned Nix/source/runtime/native/licence/OCI/CI and actual commercial/provider/refund/tax/mail/host/ingress/database/human/independent custody/post-backup/transport/restore/complete-loss qualification remain open. The authorized independent off-host runner is unassigned. Actual company inputs arrive later through docs/decisions.md; no repeated request. No real credentials/.env, production/bank-sandbox connection, host/DNS/TLS/bank/mail/storage operation or paid provision. The private Astro release and unrelated http_cache.sqlite remain unchanged. Parent counts stay 11/42 retained summaries and 1/14 documentary phases; no new SUMMARY/FULL_PASS. Current development focus remains Phase 6; this advance is a focused SHB-22 test addition within Phase 8's 08-01 scope.
