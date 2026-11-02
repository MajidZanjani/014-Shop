# SHB staff financial browser verification

Authority: [SHB revision 1.1](../../014-Shop-SHB-Proposal-Revision-2026-10-30.md), including Appendix A. This continues the saved existing13-01 acceptance task after explicit user resume. The local10-05 refund services and12-01 recovery assessment remain unchanged.

## Executed behavior

The existing [demonstration](../../scripts/demo_shb.py) now starts a separate owned loopback staff Gunicorn process against the same disposable PostgreSQL as the customer demonstration. Its temporary settings import the existing synthetic staff configuration; staff routes and cookies retain their separate application boundary. The existing [Chromium runner](../../scripts/browser_shb.mjs) exercises native keyboard forms with JavaScript enabled and disabled, at320px. No application service, schema, production setting or frontend release is changed.

Each staff mode signs in with the synthetic password and the actual private possession-code capture. An unauthenticated session and a password-only session cannot read the purchase; sign-out removes privileged access. Unassigned orders return404. An order assignment without a refund assignment exposes no financial controls, and a retargeted native refund-review submission is denied. Removing the review form's CSRF token produces403.

The assigned reviewer records the manual-support check, archives the existing full synthetic refund intent, dispatches it once, and performs retained lookup twice. The same purchase page then records the attributed support-team communication reference after the observed refund. Both50-hour ASIC purchases retain their original order references and per-order hours. The database verification compares all original paid-order payloads/hashes, coupon outcomes, purchase-notice captures and ordinary transaction notices before/after; every original fact matches. Exactly two archived reviews, financial results, bank transitions and support handoffs exist. Archive validators verify the original review/result linkage. Real financial authority remains false, policy fields remain null, and no mail, fulfilment or support-time event is created by the refund/handoff.

## Evidence

Actual Chromium151.0.7922.173/Node24.15.0 passes **113 browser checks**:71 customer and42 staff checks, each lane in JavaScript/no-JavaScript modes. The customer lane retains30-hour FPGA purchases, reviewed50-hour ASIC purchases, safe unpaid cancellation/withdrawal and linked unpaid75-hour ASIC revisions. Its four purchase notifications and twenty ordinary transaction notices are captured locally before staff refunds.

[Browser/source record](../evidence/shb/retained-tests/443cb77cf447b39ddf28d6a8b74173aaa67e9919b4d8b1e1e61ad5c115fe64e0.json) binds350 backend/eight-script hashes. Private screenshot evidence: `.scratch/shb-checkout-browser-wtwr376y`. A first attempt reached the staff lane but the browser resolver blocked the staff fixture hostname; the bounded diagnostic is in `.scratch/shb-checkout-browser-1k6iqeo_/browser-failure.json`. The corrected browser resolver explicitly maps only `staff.localhost` to127.0.0.1, while request interception continues to admit only the current loopback origin. No host DNS/network configuration changed.

The current shared regression passes **526 tests**, none failed/skipped:183 SHB (including15 financial),95 access/recovery,104 payment,30 staff review/navigation,24 worker/statement-mail,75 preserved transaction/archive,9 source/catalog and6 actual `unshare --net` adapter cases. Django check, additive migration application and migration-drift checks pass. [Regression/source record](../evidence/shb/retained-tests/5c2a832ddcce997e3e3839b3d8021510c0a6bbc608373758aee46c8e0f5ef451.json) binds exactly the same350 backend/eight-script hashes as the113-check browser record. Planning activity3 tests and both planning checks pass. All owned browser/server/database contexts completed.

This closes the recorded local staff-finance browser gap for SHB-25/27. It does not establish attributable human UAT, selected-bank/refund/chargeback policy, actual commercial or legal adoption, mail delivery, host/ingress/database qualification, normal pinned Nix/source/runtime/native/licence/OCI/CI, independent custody, complete post-backup reconstruction or actual restore/complete-loss qualification. The authorized independent runner remains unassigned. Company inputs arrive later through the single [decision register](../decisions.md); no repeat request is needed. No real bank/mail/storage/protected-host/DNS/TLS operation, production/bank-sandbox connection, `.env`/unrelated cache access or paid provision occurred. Parent13-01 and actual release gates remain open; no SUMMARY or completion-count change (11/42 records,1/14 documentary phases).

## Reproduce

```sh
python3 scripts/check_shb_retained.py --browser --release .scratch/shb-private-resume-t2p3r5cc/release --browser-binary /nix/store/53p8msmqxpi829zdrw6qkvaamidxy9cj-chromium-151.0.7922.173/bin/chromium --browser-node /nix/store/5a8ysg1jnj8jmzzyfcfw7rvpvnp5rfpa-nodejs-24.15.0/bin/node
python3 scripts/check_shb_retained.py --shared
python3 -m unittest discover -s tests -p 'test_planning_activity.py'
python3 scripts/check_purchase_plan.py --refresh-inventory
python3 scripts/check_planning.py
python3 scripts/check_purchase_plan.py
```

These are the separate verified retained-tool commands for local synthetic evidence. Verification commit `f06869f12e4e458e282509f388b37884461e21f6` is committed and ordinarily pushed to origin/main. The normal pinned lane remains `python3 scripts/check_shb.py --shared`; its existing qualification gates are not replaced by this result.
