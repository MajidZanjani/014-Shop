# SHB ordinary request and customer purchase notices

Authority: [SHB revision 1.1](../../014-Shop-SHB-Proposal-Revision-2026-10-30.md), including Appendix A. This continues existing07-03/07-04 and the [archived closing](shb-asic-closing-2026-11-02.md) slice inline. Results are local synthetic evidence; no actual mail was sent.

## Implemented behavior

The existing leased worker now handles ordinary customer request acknowledgements, review questions/declines, issued-offer notices, request/offer closing notices, safe accepted-checkout cancellation/expiry notices and purchase confirmations. Each source operation queues its immutable notice and pending delivery in the same database transaction. PostgreSQL rejects a new event that omits its required notice, a notice that omits its delivery, or a recipient/body/source substitution.

Each event has a deterministic notice identity and a unique source/event association. Integer retained review IDs and UUID request/offer/order IDs remain unchanged; the notice stores a typed event plus textual source identity. Retry never creates a second notice. Technical readiness alone sends no payable offer promise. Offer notices contain a clean protected offer path and exact deadline, without an invitation token or confidential scope. Closing notices describe their committed outcome. Customer purchase confirmations retain the original order reference, variant, quantity, bundle size, per-order hours, amount and currency; no aggregate balance or usage calculation is added.

Recipients come from the originating request or accepted transaction contact. This is explicitly `this-transaction-only`, with `named_identity_verified=false`. No contact becomes company authorization or a replacement authorized support contact. No private history/prefill, raw invitation/coupon, technical attachment or task-usage email is included. Existing support-team purchase notices continue separately on the same worker.

The worker claims bounded finite leases with skip-locked arbitration, archives and recovers the exact notice envelope and capture proof, then commits a durable fake receipt only while it still owns the current lease. An interrupted archive retains pending work; an expired owner cannot complete; process loss after capture is repaired under the same identity. Exhaustion enters `held`. A failed customer notice does not erase a paid order, reverse its coupon consumption or create another bank operation. Already stored notices continue after invitation revocation.

All captured envelopes/proofs explicitly retain `actual_email_sent=false`, `evidence_class=local-synthetic`, `financial_confirmation=false` and `effects_authorized=false`. There is no SMTP dispatch, provider retry claim, real recipient verification, actual mail-route qualification or legal/commercial adoption. Those live gates remain pending.

## Executed evidence

The initial [one-target RED report](../evidence/shb/ordinary-notices-red-2026-11-02.json) executes after successful request capture and fails only because the existing worker has no acknowledgement work. GSD returned RED_EVIDENCE_OK. Test/state commit6bab1fe is pushed.

Twelve focused notice cases and17 ASIC closing cases pass together. They cover source/retry identity, exact review messages, offer/purchase references, no-balance scope, withdrawal, archive loss, stale leases, capture-before-process-loss recovery, revoked invitations, parallel ownership, finite exhaustion, immutable recipients, paid-state preservation through mail failure and SQL rejection of an omitted source notice.

Full unchanged-source run: **487 tests passed**, none failed or skipped:144 SHB,95 access/recovery,104 payment,30 staff review/navigation,24 local worker/statement-mail,75 preserved transaction/archive,9 source/catalog and6 actual network-isolated adapter cases. Django check, migrations and schema drift checks passed. [Final regression/source record](../evidence/shb/retained-tests/93af6fd4197a2dbfdfe11f41409febc648e44ec5e828539acd9be417521e6ba4.json). Both final records bind identical340 backend/eight-script hashes. Planning activity3 tests and both required planning checks pass. An earlier browser snapshot is retained separately and is not substituted for these final source hashes.

Actual Chromium151.0.7922.173/Node24.15.0 passes65 checks in JavaScript/no-JavaScript modes at320px. The same persisted browser fixture additionally verifies that the existing worker captures all18 ordinary notices:6 request acknowledgements,4 issued offers,2 request withdrawals,2 accepted-checkout closings and4 customer purchase confirmations. It also retains4 support-team fake captures,4 paid orders/bank operations and0 historical fulfilments. Every ordinary delivery is captured once; none reports a real email. [Final browser/source record](../evidence/shb/retained-tests/94c330c1b4791fee917fdfe8006212ff6e49d1b2918a361bbb60220bf22610ac.json). Private empty screenshots: `.scratch/shb-checkout-browser-iecrpdkt`.

Development corrections: generic source triggers must branch before referencing table-specific columns; retained review keys are integers rather than UUIDs. Full regression also exposed the archive's existing nonblocking directory-lock contention during the acceptance/withdrawal race. The test now accepts only the specific recovery-evidence503, then requires saved-intent recovery or exact safe acceptance retry and exactly one final outcome with the correct concession.503 itself is never counted as completion. No archive lock or security guard was weakened.

## Reproduce

```sh
python3 scripts/check_shb_retained.py --shared
python3 scripts/check_shb_retained.py --browser --release .scratch/shb-private-resume-t2p3r5cc/release --browser-binary /nix/store/53p8msmqxpi829zdrw6qkvaamidxy9cj-chromium-151.0.7922.173/bin/chromium --browser-node /nix/store/5a8ysg1jnj8jmzzyfcfw7rvpvnp5rfpa-nodejs-24.15.0/bin/node
python3 -m unittest discover -s tests -p 'test_planning_activity.py'
python3 scripts/check_purchase_plan.py --refresh-inventory
python3 scripts/check_planning.py
python3 scripts/check_purchase_plan.py
```

Current files: [transaction_mail.py](../../backend/shop/shb/transaction_mail.py), [models.py](../../backend/shop/shb/models.py), additive SHB0017/0018 migrations, source hooks in existing services/review/offers/closing/paid-order modules and the existing worker. [notification_tests.py](../../backend/shop/shb/notification_tests.py) is included in ordinary and retained checks. Existing paid-order/closing tests now account for the additional ordinary workload. The existing demo asserts all18 captures; no second worker/platform was introduced.

The retained lane verifies the same2 exact OCI tool archives/91 layers and locked Python3.13.16/Django5.2.18/PostgreSQL18.6/libpq180006 inventory, using a read-only store overlay and owned disposable database. It remains separate synthetic evidence. Normal pinned Nix/source/runtime/native/licence/OCI/CI and actual company/provider/mail/host/ingress/database/independent/recovery/human qualification remain pending. Company inputs arrive later through the single [decision register](../decisions.md); the off-host runner is unassigned. No `.env`, unrelated cache, actual bank/mail/storage/protected-host/DNS/TLS action or paid provision was used.

Complete linked material changed-work/request revision handling remains open; unchanged-scope offer reissue is already verified. No parent SUMMARY or completion-count change:11/42 retained summaries and1/14 documentary phases. No support-time accounting, customer panel or task-email automation.
