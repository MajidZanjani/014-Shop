# SHB-26 invitation expiry invariant

Authority: [SHB revision 1.1](../../014-Shop-SHB-Proposal-Revision-2026-10-30.md), including Appendix A. Phase 10's 10-01 slice is advanced inline with one explicit test; parent completion counts remain 11/42 and 1/14 until actual gates qualify. Real company inputs/adoption remain pending in the single [decision register](../decisions.md).

## Invariant

SHB-26: "Invite expires with unused purchased hours — Purchased support remains valid under its terms; support team continues manual tracking and task emails independently."

Operational translation: the invitation's six-month calendar expiry closes the customer's purchase surface but does not touch anything downstream. The existing `PaidOrder` row, its `PurchaseNoticeDelivery` row, and the staff order view at `/staff/shb-orders/<pk>/` continue unaffected. Manual support tracking proceeds outside the shop; the shop never implies otherwise.

## Verification

`test_paid_order_remains_valid_and_visible_to_staff_after_invitation_expiry` in `backend/shop/shb/paid_order_tests.py` exercises the full lifecycle:

1. The fixture customer completes an FPGA purchase (3 × 10h = 30h, `shb-fpga-10h`) through the invitation created by `setUp`; one `PaidOrder` and one `PurchaseNoticeDelivery` exist.
2. The invariant is simulated by patching `shop.shb.invitations.now` to a time one day past `self.invitation.expires_at`. The DB-level `shb_invitation_immutable_scope` trigger forbids mutating `expires_at` directly, so a time-of-check patch is the only honest way to simulate calendar expiry.
3. The customer POSTs a new submission to `/purchase/simple/`. The test asserts: the response is NOT a 302 (so no checkout started), the `PaidOrder` count stays at 1, and the `SupportCheckout` count is unchanged from before the attempt.
4. After the patch exits, the test grants `PaidOrderGrant` to a staff user with recent MFA, hits `/staff/shb-orders/<pk>/`, and asserts the response is 200 with the same `hours_purchased=30`, `variant_id='shb-fpga-10h'`, `company_name='Synthetic Company Limited'`.
5. The `PaidOrder` row is refreshed from the DB; its `payload` dict must match the pre-expiry snapshot byte-for-byte.
6. `purchase_mail.execute_once()` must return True (there is still a notice to process), and the sole `PurchaseNoticeDelivery` row's primary key must equal the pre-expiry pk (no row was recreated).
7. Zero `SyntheticFulfilment` and zero `SyntheticSupportEvent` are produced at any point.

The invariant was already implicit in the existing invitation-eligibility, staff-grant and worker-claim paths. This commit makes it explicit so a future refactor cannot silently couple invitation expiry to paid-order lifecycle, hidden notice-worker cutoffs, or automated time adjustments.

Shared regression passes **609 tests** (previously 608; +1 for SHB-26): 266 SHB, 95 access/recovery, 104 payment, 30 staff, 24 worker/statement-mail, 75 shared transaction/archive, nine source/catalog and six actual network-isolated adapter cases. Django check, migrations 0029/0030 and drift pass with no new drift. [Current regression/source record](../evidence/shb/retained-tests/55f826a4a734289ea97b53cb0e508cfcdb4a66fe576a791bad1c82976d86310b.json); focused 1-test audit record [3d61e87b…json](../evidence/shb/retained-tests/3d61e87bd17f9baed58a960f279b571326dd24c003da446c9e869325878305a4.json). Browser lane unchanged at 161 checks; this assertion is backend-only and does not change any customer- or staff-visible behavior.

## Reproduce

```sh
python3 scripts/check_shb_retained.py --test-label shop.shb.paid_order_tests.PaidOrderTests.test_paid_order_remains_valid_and_visible_to_staff_after_invitation_expiry
python3 scripts/check_shb_retained.py --shared
python3 -m unittest discover -s tests -p 'test_planning_activity.py'
python3 scripts/check_purchase_plan.py --refresh-inventory
python3 scripts/check_planning.py
python3 scripts/check_purchase_plan.py
```

Normal pinned Nix/source/runtime/native/licence/OCI/CI and actual commercial/provider/refund/tax/mail/host/ingress/database/human/independent custody/post-backup/transport/restore/complete-loss qualification remain open. The authorized independent off-host runner is unassigned. Actual company inputs arrive later through docs/decisions.md; no repeated request. No real credentials/.env, production/bank-sandbox connection, host/DNS/TLS/bank/mail/storage operation or paid provision. The private Astro release and unrelated http_cache.sqlite remain unchanged. Parent counts stay 11/42 retained summaries and 1/14 documentary phases; no new SUMMARY/FULL_PASS. Current development focus remains Phase 6; this advance is a focused SHB-26 test addition within Phase 10's 10-01 scope.
