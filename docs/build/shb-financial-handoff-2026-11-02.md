# SHB refund review and manual support handoff

Authority: [SHB revision 1.1](../../014-Shop-SHB-Proposal-Revision-2026-10-30.md), including Appendix A. This executes the unblocked local slice of existing10-05 while actual12-01 independent runner/custody qualification remains gated.

## Behavior

The assigned SHB staff purchase page records an archived manual support check before preparing a new synthetic refund. The reviewer needs recent MFA, the exact paid-order assignment and the exact refund assignment. The record binds the original order/reference, acceptance, captured payment, amount/currency, staff attribution, manual-record reference and reason. It accepts no consumed/remaining-hours fields or browser-supplied financial amount.

The existing shared finance route prepares and dispatches the full synthetic refund with the retained review identity/hash. A PostgreSQL insert guard prevents bypass through direct financial intent creation. Existing immutable historical intents remain readable and reconcilable; an unreviewed intent cannot gain a new dispatch. Uncertain dispatch remains lookup-only. The shared result verifier is reused, with bank I/O outside transactions and fresh epoch/MFA/resource authorization before mutations.

After the exact refund result is recorded, the same staff purchase page accepts a communication reference attesting that the staff member informed the support team. That append-only handoff is archived and linked to the original review and verified financial result. It does not send mail or calculate a manual-record correction. The paid purchase snapshot, original purchased hours, consumed coupon and old transaction confirmation remain intact. Both native forms and JSON use the same services and controls.

Only the existing fake adapter's full-amount refund is implemented here. Actual refund eligibility, seller approval, tax credit document and provider qualification remain null. This record does not adopt a refund policy or authorize actual money. No time-ledger update, online usage/balance calculation, task email, customer panel or new support-management platform is added. Unsupported actual chargeback/partial-refund behavior remains subject to the selected provider contract.

The existing local recovery assessment now verifies refund review, financial intent/result and manual handoff archives. Missing review bytes refuse fixture release; replay retains the original purchase/coupon/result identity. Its actual-recovery, post-backup-completeness, retry and reopening authority flags remain false.

## Executed evidence

The actual [RED report](../evidence/shb/financial-review-red-2026-11-02.json) executes after successful ASIC offer/acceptance/payment and exact current staff grants. It fails only on200 versus409: the shared finance route prepared an SHB refund without a recorded manual check. GSD returns `RED_EVIDENCE_OK`; test/state commitd2a0a8f is pushed.

The initial focused12-case run had one fixture error: its helper requested a fresh CSRF token after quarantine. It now submits the existing token/session to verify denial. An intermediate525-test run passes ([record](../evidence/shb/retained-tests/b8fb8050b82988714a2f121379937c84cc35854087aa9efe7afb13692ddc185a.json)). Review then added a controlled missing-order-scope denial and its regression so the application rejects unauthorized new intents before the SQL guard; retained finance lookup keeps its separate scope.

The final run passes **526 tests**, none failed/skipped:183 SHB (including15 financial),95 access/recovery,104 payment,30 staff review/navigation,24 worker/statement-mail,75 preserved transaction/archive,9 source/catalog and6 actual `unshare --net` adapter cases. Django check, additive migrations0021/0022 and schema-drift checks pass. [Final regression/source record](../evidence/shb/retained-tests/fc078b95887c6023643d2e383867cee64b182aeecdb7d8d7f9d5245091f04658.json).

Actual Chromium151.0.7922.173/Node24.15.0 passes **71 customer browser checks** in JS/no-JS modes at320px, including30-hour FPGA and reviewed50-hour ASIC purchases plus linked unpaid75-hour revisions. [Browser/source record](../evidence/shb/retained-tests/17d1d92dceb18ae563b0064b380a3d54d23a6724710c5ba3bafec2e29a312c9a.json) binds the same350 backend/eight-script hashes as the final526-test record. Native staff refund forms have Django/CSRF coverage; these71 customer checks do not establish staff browser/human qualification. Private browser evidence: `.scratch/shb-checkout-browser-4dznj256`. All owned contexts completed; the private9-file Astro release/manifest is unchanged.

Current files: [refund service](../../backend/shop/shb/refunds.py), [immutable models](../../backend/shop/shb/models.py), additive SHB0021/0022 migrations, [shared finance service](../../backend/shop/payments/operations.py), existing staff order/finance views/templates/routes, [financial tests](../../backend/shop/shb/financial_tests.py), recovery assessment and both existing SHB runners. The existing [thirty-case register](../../.planning/phases/13-purchase-flow-fulfilment-and-release-acceptance/13-QUALIFICATION-REGISTER.md) now traces all criteria to local evidence and actual remaining limits.

## Reproduce

```sh
python3 scripts/check_shb_retained.py --shared
python3 scripts/check_shb_retained.py --browser --release .scratch/shb-private-resume-t2p3r5cc/release --browser-binary /nix/store/53p8msmqxpi829zdrw6qkvaamidxy9cj-chromium-151.0.7922.173/bin/chromium --browser-node /nix/store/5a8ysg1jnj8jmzzyfcfw7rvpvnp5rfpa-nodejs-24.15.0/bin/node
python3 -m unittest discover -s tests -p 'test_planning_activity.py'
python3 scripts/check_purchase_plan.py --refresh-inventory
python3 scripts/check_planning.py
python3 scripts/check_purchase_plan.py
```

The normal pinned lane remains `python3 scripts/check_shb.py --shared`. Retained exact tools are separate local synthetic evidence; normal Nix/source/runtime/native/licence/OCI/CI and actual company/provider/mail/host/database/independent/recovery/human qualification remain pending. One actual-input register remains [docs/decisions.md](../decisions.md); company inputs arrive later. The independent off-host runner remains unassigned. No real bank/mail/storage/protected-host/DNS/TLS operation, production/bank-sandbox connection, `.env`/cache access or paid provision is part of this work. No parent SUMMARY or completion-count change is claimed.
