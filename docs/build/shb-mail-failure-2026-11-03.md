# SHB-23 cross-model invariant under temporary mail failure

Authority: [SHB revision 1.1](../../014-Shop-SHB-Proposal-Revision-2026-10-30.md), including Appendix A. Phase 10's 10-01 slice is advanced inline with one explicit test; parent completion counts remain 11/42 and 1/14 until actual gates qualify. Real company inputs/adoption remain pending in the single [decision register](../decisions.md).

## Invariant

SHB-23: "Temporary transaction-mail failure — Order/payment/coupon state retained; paid order remains visible to staff and notification retries do not create a second purchase."

Operational translation: a transient failure in the mail-publish adapter must leave the paid-order, coupon-reservation, and payment-attempt rows untouched. Staff with their existing grants must still see the paid order. When the fault clears, worker recovery produces exactly one notice capture without duplicating anything upstream.

## Verification

`test_temporary_mail_failure_retains_order_coupon_payment_and_staff_view` in `backend/shop/shb/paid_order_tests.py` exercises the full cross-model invariant:

1. The fixture customer completes an FPGA purchase with a two-use 10% discount; one `PaidOrder`, one `DiscountReservation` (consumed), and one `SyntheticPaymentAttempt` exist.
2. The test records byte-identical snapshots of: `PaidOrder.payload`, `DiscountReservation.state` + `consumed_order_id`, and `SyntheticPaymentAttempt.state` + `amount_minor`.
3. The staff view at `/staff/shb-orders/<pk>/` is wired up with a `StaffCredential`, recent MFA, and a `PaidOrderGrant` before the failure window opens.
4. Within a `patch.object(PreparedArchive, 'publish', side_effect=ArchiveError('temporary mail failure'))` context, `purchase_mail.claim(lease_seconds=1)` + `capture()` is attempted — the capture raises `ArchiveError`, no `PurchaseNoticeCapture` is created.
5. All three business-state snapshots are re-asserted byte-identical during the failure window. `PaidOrder.objects.count()` is still 1. The staff view returns 200 with the correct `hours_purchased` and company name.
6. After the lease expires (`lease_until = timezone.now() - timedelta(seconds=1)`) and the mail-failure patch is lifted, `purchase_mail.execute_once()` returns True — recovery succeeded.
7. Final: `PaidOrder.objects.count() == 1`, `PurchaseNoticeCapture.objects.count() == 1`, and the `PaidOrder.payload` + `DiscountReservation` state are still byte-identical to the pre-failure snapshot.

The existing `test_mail_failure_and_expired_claim_keep_paid_state_and_reuse_same_effect` already covered purchase-notice-worker idempotency around a mail failure. This commit adds the cross-model clause: the DiscountReservation, the SyntheticPaymentAttempt and the staff view were not previously asserted to be byte-identical through a mail-failure window. This makes SHB-23 explicit so a future refactor cannot silently roll back a reservation or mutate attempt state during a notice-adapter failure.

Shared regression passes **610 tests** (previously 609; +1 for SHB-23): 267 SHB, 95 access/recovery, 104 payment, 30 staff, 24 worker/statement-mail, 75 shared transaction/archive, nine source/catalog and six actual network-isolated adapter cases. Django check, migrations 0029/0030 and drift pass with no new drift. [Current regression/source record](../evidence/shb/retained-tests/be47eee8c6b72c8c31211f545a151d9ac5f583f7aa118c0eae3365328899c0a0.json); focused 1-test audit record [c2800773…json](../evidence/shb/retained-tests/c280077332d182a2a5883c937554d58d75559069fbe7c920416e528f2696e3ef.json). Browser lane unchanged at 161 checks; this assertion is backend-only.

## Reproduce

```sh
python3 scripts/check_shb_retained.py --test-label shop.shb.paid_order_tests.PaidOrderTests.test_temporary_mail_failure_retains_order_coupon_payment_and_staff_view
python3 scripts/check_shb_retained.py --shared
python3 -m unittest discover -s tests -p 'test_planning_activity.py'
python3 scripts/check_purchase_plan.py --refresh-inventory
python3 scripts/check_planning.py
python3 scripts/check_purchase_plan.py
```

Normal pinned Nix/source/runtime/native/licence/OCI/CI and actual commercial/provider/refund/tax/mail/host/ingress/database/human/independent custody/post-backup/transport/restore/complete-loss qualification remain open. The authorized independent off-host runner is unassigned. Actual company inputs arrive later through docs/decisions.md; no repeated request. No real credentials/.env, production/bank-sandbox connection, host/DNS/TLS/bank/mail/storage operation or paid provision. The private Astro release and unrelated http_cache.sqlite remain unchanged. Parent counts stay 11/42 retained summaries and 1/14 documentary phases; no new SUMMARY/FULL_PASS. Current development focus remains Phase 6; this advance is a focused SHB-23 test addition within Phase 10's 10-01 scope.
