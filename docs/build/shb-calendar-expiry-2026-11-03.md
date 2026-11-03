# SHB-12 six-month calendar expiry suite

Authority: [SHB revision 1.1](../../014-Shop-SHB-Proposal-Revision-2026-10-30.md). Phase 6's 06-01 scope is advanced inline with a focused unit suite on the calendar-expiry utility. Parent completion counts remain 11/42 and 1/14 until actual gates qualify.

## Invariant

SHB-12: "Calendar expiry month-end/leap-year — current expiry correct."

Operational translation: `backend/shop/shb/invitations.six_month_expiry` computes an invitation's `expires_at` as six Asia/Tbilisi calendar months after creation. For edge cases where the created day doesn't exist in the target month (e.g., Aug 31 → Feb 28/29), the function clamps to the last day of the target month using `calendar.monthrange`. The function must also reject naive datetimes and non-datetime input, and the returned time must be strictly later than the input.

## Verification

`backend/shop/shb/tests.CalendarExpiryTests` adds seven focused SimpleTestCase assertions:

1. `test_six_month_expiry_rejects_naive_or_non_datetime` — ValueError on a naive datetime and on a stringified timestamp.
2. `test_normal_same_day_six_month_shift` — Jan 15 → Jul 15; Jun 1 → Dec 1.
3. `test_year_boundary_crossing` — Sep 15 → Mar 15 of the next year; Dec 1 → Jun 1 of the next year.
4. `test_month_end_clamps_to_last_day_of_target_month` — Aug 31 2025 → Feb 28 2026 (non-leap); Mar 31 → Sep 30; May 31 → Nov 30; Oct 31 → Apr 30.
5. `test_leap_target_month_keeps_day_29_available` — Aug 31 2027 → Feb 29 2028 (leap target); Aug 30 2027 → Feb 29 2028; Aug 28 2027 → Feb 28 2028 (no over-clamp).
6. `test_leap_source_day_29_shifts_cleanly` — Feb 29 2024 → Aug 29 2024.
7. `test_expiry_is_strictly_after_creation` — round-trip invariant across five mixed boundary cases (Feb 29 2024, Aug 31 2025, Mar 31 2026, Jun 15 2026, Dec 1 2027).

Pre-existing coverage in `backend/shop/shb/invitation_issuance_tests.test_expired_month_end_replacement_is_separate_six_calendar_month_issue` already tied the function into the Invitation-level flow (Aug 31 2025 → Feb 28 2026 end-to-end). This commit expands the raw utility surface so a future refactor cannot silently regress leap-target or year-boundary cases.

Shared regression passes **622 tests** (previously 615; +7 for the calendar suite): 279 SHB, 95 access/recovery, 104 payment, 30 staff, 24 worker/statement-mail, 75 shared transaction/archive, nine source/catalog and six actual network-isolated adapter cases. Django check, migrations 0029/0030 and drift pass with no new drift. [Current regression/source record](../evidence/shb/retained-tests/d2ef0a6e8edd8b0c68ac51dfda4b4774256e127d2a0e36677b0b305e5e290f67.json); focused 7-test audit record [692da03d…json](../evidence/shb/retained-tests/692da03dd65c465f254c0c8f4b5681841175717e07813e3e6e9574df2b44adb1.json). Browser lane unchanged at 161; the suite is backend-only.

## Reproduce

```sh
python3 scripts/check_shb_retained.py --test-label shop.shb.tests.CalendarExpiryTests
python3 scripts/check_shb_retained.py --shared
python3 -m unittest discover -s tests -p 'test_planning_activity.py'
python3 scripts/check_purchase_plan.py --refresh-inventory
python3 scripts/check_planning.py
python3 scripts/check_purchase_plan.py
```

Normal pinned Nix/source/runtime/native/licence/OCI/CI and actual commercial/provider/refund/tax/mail/host/ingress/database/human/independent custody/post-backup/transport/restore/complete-loss qualification remain open. The authorized independent off-host runner is unassigned. Parent counts stay 11/42 retained summaries and 1/14 documentary phases; no new SUMMARY/FULL_PASS. Current development focus remains Phase 6.
