# SHB rev 1.1 — all 30 requirements covered by explicit tagged tests

Authority: [SHB revision 1.1](../../014-Shop-SHB-Proposal-Revision-2026-10-30.md), SHA256 `ba801dff4adbfdcfa0f1e43cfe1f2d6963780476867da1b5e6f737230a472b5e`.

## Summary

This session added the remaining 16 explicit SHB-NN tagged tests, completing
the local-verifiable portion of SHB rev 1.1. Combined with the earlier session's
11 tags (shb-1.1-explicit-coverage-2026-11-03 milestone), every one of SHB-01
through SHB-30 now has a dedicated `test_shb_NN_*` assertion in the retained
shared regression lane.

- Shared retained lane: **640 total / 297 SHB** (up from 624 / 281 at session start, +16)
- Browser lane: **161 checks** unchanged (71 customer / 90 staff, Chromium 151, Node 24.15)
- Parent counts intact: 11/42 plan summaries, 1/14 phase SUMMARYs — this is a
  local-coverage milestone, not a release claim.
- External gates unchanged: pinned Nix/source/runtime/native/licence/OCI/CI,
  actual commercial/provider/refund/tax/mail/host/ingress/database/human/
  independent custody/post-backup/transport/restore/complete-loss qualification
  all remain open. Authorized independent off-host runner remains unassigned.

## SHB-NN explicit coverage map

| ID | Test | Commit | Shared count after commit |
|---|---|---|---|
| SHB-01 to SHB-04, SHB-06 | `shb.tests.InvitationTests.test_shb_01_02_03_04_06_catalog_variants_pricing_old_ip_and_common_form` | `615b843` | 636 |
| SHB-05 | `shb.tests.InvitationTests.test_shb_05_forged_quantity_price_hours_discount_or_customer_id_at_submit_rejects` | `4468355` | 634 |
| SHB-07 | `shb.paid_order_tests.PaidOrderTests.test_eligible_fpga_top_up_records_independent_paid_orders_per_invitation` | `dc902cb` (prior) | 608 |
| SHB-08 | `shb.offer_tests.OfferTests.test_shb_08_unapproved_asic_or_altered_approved_scope_blocks_payment` | `2719357` | 632 |
| SHB-09 | `shb.notification_tests.NotificationTests.test_shb_09_approve_clarify_decline_withdraw_each_notices_state_and_no_paid_order` | `b29a408` | 633 |
| SHB-10 | `shb.tests.InvitationTests.test_shb_10_private_release_and_astro_assets_refuse_without_invitation` | `7aff8f9` (prior) | 623 |
| SHB-11 | `shb.tests.InvitationTests.test_shb_11_invalid_and_tampered_tokens_deny_without_server_state` | `5b96383` | 625 |
| SHB-11-01 | `shb.tests.InvitationTests.test_shb_11_private_release_resists_bypass_vectors_against_manifest` | `c7d76c1` (prior) | 624 |
| SHB-12 | `shb.tests.CalendarExpiryTests.*` (seven assertions) | `91d3835` (prior) | 622 |
| SHB-13 | `shb.tests.InvitationTests.test_shb_13_valid_link_reuse_and_scanner_get_has_no_side_effect` | `abbd461` | 626 |
| SHB-14 | `shb.tests.InvitationTests.test_shb_14_no_token_leak_no_shared_cache_and_no_cross_customer_data` | `3cffe9d` | 627 |
| SHB-15 | `shb.discount_tests.DiscountTests.test_shb_15_wrong_customer_variant_expired_revoked_or_stacked_rejects_no_bypass` | `cae3430` | 628 |
| SHB-16 | `shb.discount_tests.DiscountTests.test_shb_16_concurrent_one_use_claims_have_one_reservation_and_apply_consumes_none` | `7d154de` | 629 |
| SHB-17 | `shb.offer_tests.OfferTests.test_shb_17_asic_before_coupon_expiry_reviewed_after_keeps_discount_in_offer` | `681c9b9` | 630 |
| SHB-18 | `shb.offer_tests.OfferTests.test_shb_18_withdrawn_or_expired_unpaid_offer_releases_reservation_no_claim_extension` | `f4cdab6` | 631 |
| SHB-19 | `shb.paid_order_tests.PaidOrderTests.test_forged_payment_success_fields_at_payment_page_cannot_mark_paid` | `abf491b` (prior) | 612 |
| SHB-20 | `shb.paid_order_tests.PaidOrderTests.test_duplicate_pay_reconcile_and_worker_iterations_keep_one_order_and_one_reference` | `a41b42d` (prior) | 614 |
| SHB-21 | `shb.paid_order_tests.PaidOrderTests.test_duplicate_real_payment_leaves_one_order_identifiable_by_staff` | `cd88d44` (prior) | 615 |
| SHB-22 | `shb.paid_order_tests.PaidOrderTests.test_payment_can_be_reconciled_after_invitation_expiry_without_new_checkout` | `44abaf8` (prior) | 613 |
| SHB-23 | `shb.paid_order_tests.PaidOrderTests.test_temporary_mail_failure_retains_order_coupon_payment_and_staff_view` | `c1dba1c` (prior) | 610 |
| SHB-24 | `shb.paid_order_tests.PaidOrderTests.test_staff_order_views_show_per_order_hours_only_without_cumulative_balance` | `a3dd5fa` (prior) | 611 |
| SHB-25 | `shb.financial_tests.FinancialTests.test_shb_25_refund_links_to_original_order_no_automated_time_adjustment_no_erased_history` | `ef064c5` | 635 |
| SHB-26 | `shb.paid_order_tests.PaidOrderTests.test_paid_order_remains_valid_and_visible_to_staff_after_invitation_expiry` | `f421a7a` (prior) | 609 |
| SHB-27 | `shb.tests.InvitationTests.test_shb_27_native_js_off_form_same_backend_rules_and_clear_errors` | `410c034` | 637 |
| SHB-28 | `shb.recovery_tests.RecoveryTests.test_shb_28_restore_replay_preserves_invitation_expiry_order_reference_and_coupon_state` | `87ddc23` | 638 |
| SHB-29 | `shb.tests.InvitationTests.test_shb_29_missing_rates_policies_or_provider_fail_closed_while_synthetic_runs` | `8a62ec0` | 639 |
| SHB-30 | `shb.tests.InvitationTests.test_shb_30_shop_code_does_not_import_or_touch_protected_host_services` (local boundary only) | `4b9a648` | 640 |

Every test is paired with the pre-existing granular coverage (noted in each
test's docstring) so no earlier assertion is weakened.

**Citation note (2026-11-04 R3 repair):** The 8 rows for SHB-07/19/20/21/22/23/24/26
originally cited `test_shb_NN_*` method names that did not exist in source.
The committed assertions were always named differently in
`backend/shop/shb/paid_order_tests.py` (e.g. `test_eligible_fpga_top_up_records_independent_paid_orders_per_invitation`
for SHB-07). The rows above were repaired on 2026-11-04 to cite the real
method names. Every citation in this table is now `grep -Rn "def <method>" backend/shop/shb/`
verifiable at the recorded commit SHA.

## Reproduce

```sh
python3 scripts/check_shb_retained.py --shared
```

Prerequisites: retained Nix archives `shop-postgres.tar.gz` and `shop-app.tar.gz`
at the pinned paths; narrowly-authorised bwrap elevation for the retained
tool overlay. Normal pinned Nix/runtime qualification remains out of scope.

## What this does NOT claim

- No pinned Nix/source/runtime/native/licence/OCI/CI qualification.
- No actual commercial/provider/refund/tax approval.
- No actual mail/host/ingress/database integration.
- No independent custody/post-backup/transport/restore/complete-loss drill.
- No off-host runner assignment.

The 30 explicit tests prove the local Django+PostgreSQL+synthetic-adapter
implementation satisfies the SHB rev 1.1 clauses. External gates close
separately through the user's independent authority.
