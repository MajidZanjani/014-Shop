# SHB linked material ASIC request revisions

Authority: [SHB revision 1.1](../../014-Shop-SHB-Proposal-Revision-2026-10-30.md), including Appendix A. This continues existing07-04 after [archived closing/reissue](shb-asic-closing-2026-11-02.md) and [ordinary notices](shb-ordinary-notices-2026-11-02.md). Results are local synthetic evidence, with actual qualification still pending.

## Implemented behavior

After deliberate archived withdrawal of an unpaid ASIC offer, the customer can select **Start revised ASIC request**. The protected `/purchase/shb/revise/<closure-id>/` route requires a current matching ASIC invitation, legal company and project association. It returns the existing minimum form with blank billing/contact details, fixed ASIC workflow, new assistance/quantity and an explicit explanation of current pricing, fresh review and coupon revalidation. GET creates no request, approval, coupon or message effect. The link itself grants no access or private history.

Submission creates a fresh immutable request and existing quotation snapshot with revision `previous + 1`, plus one immutable RequestReplacement link to the original request and its applied withdrawal. The new payload binds the predecessor identity/hash and closure. PostgreSQL enforces same customer/company/project, archived withdrawn predecessor, current invitation, fresh unpaid ASIC capture, consecutive revision and no still-held/consumed predecessor coupon. Request, lineage, new coupon reservation and acknowledgement commit together. Row locks and uniqueness allow one child; exact retries resume it and changed retries conflict.

Original request/offer payloads, review evidence, prices and documents remain unchanged. No approval or staff assignment carries into changed work. A newly assigned reviewer needs the exact new revision grant and a fresh technical review before issuing its matching offer. The new offer then requires fresh explicit customer acceptance and the shared verified payment path. Existing staff views show the request revision and predecessor reference within their current authorized scope.

The original concession was released by the customer's deliberate withdrawal. It does not automatically carry into changed work. The form states this before submission. A still-valid eligible code can be claimed anew against the new request after current validation; an expired code is rejected without extending its original deadline. An explicit new request without a code shows its current undiscounted amount. Ordinary clarification/review of an unchanged existing request still preserves that request's original hold beyond its claim deadline. Unchanged-scope offer replacement continues to retain its original hold as implemented earlier.

The existing shared acknowledgement copy now reports queued durable synthetic capture. No entered contact becomes company authorization. The new route adds no questionnaire, technical upload, licence/board/host/production field, support-time accounting, cumulative balance, staff time entry, task-email automation or customer panel.

## Executed evidence

The initial [RED report](../evidence/shb/material-revision-red-2026-11-02.json) executes successful protected issuance and deliberate withdrawal, then fails only on the missing revised-form route404 versus200. GSD returned RED_EVIDENCE_OK; test/state commit8061f26 is pushed.

Ten focused revision cases pass: blank protected form, changed quantity/assistance and immutable predecessor, exact/conflicting retries, one-child concurrency and acknowledgement, valid-code fresh claim, expired-code rejection and disclosed undiscounted amount, fresh exact review/offer/acceptance/payment for75 purchased hours, customer/project isolation, forged workflow/quantity/privacy rejection, immutable linkage and both revision counters. Current-purchase hours remain per order; the revised unpaid intake itself creates no purchase or payment.

Full unchanged-source run: **497 tests passed**, none failed or skipped:154 SHB,95 access/recovery,104 payment,30 staff review/navigation,24 local worker/statement-mail,75 preserved transaction/archive,9 source/catalog and6 actual `unshare --net` adapter cases. Django check, additive migrations and schema drift checks passed. [Final regression/source record](../evidence/shb/retained-tests/737917c955d55e03566ea44c1c1c095e7c4639de740550bd58213e9071791da5.json). Both final records bind identical344 backend/eight-script hashes. Planning activity3 tests and both required planning checks pass.

Actual Chromium151.0.7922.173/Node24.15.0 passes71 checks in JavaScript/no-JavaScript modes at320px. Each mode withdraws an unaccepted offer, follows its clean revision link, sees blank contact inputs, submits changed work/quantity and records a linked unpaid75-hour revision. The persisted fixture contains8 ASIC requests including2 linked revision2 children,6 shared checkouts/acceptances,4 bank operations/paid orders,2 safe FPGA cancellations,2 unaccepted ASIC withdrawals,20 ordinary fake notice captures,4 support-team fake captures and0 historical fulfilments. No notice reports a real email. [Final browser/source record](../evidence/shb/retained-tests/d800e00ceb0203e0b6121e505b56b4db1c7a89d2c0473e5970b649de4d3b2291.json). Private empty screenshots: `.scratch/shb-checkout-browser-kmc8fte5`.

## Reproduce

```sh
python3 scripts/check_shb_retained.py --shared
python3 scripts/check_shb_retained.py --browser --release .scratch/shb-private-resume-t2p3r5cc/release --browser-binary /nix/store/53p8msmqxpi829zdrw6qkvaamidxy9cj-chromium-151.0.7922.173/bin/chromium --browser-node /nix/store/5a8ysg1jnj8jmzzyfcfw7rvpvnp5rfpa-nodejs-24.15.0/bin/node
python3 -m unittest discover -s tests -p 'test_planning_activity.py'
python3 scripts/check_purchase_plan.py --refresh-inventory
python3 scripts/check_planning.py
python3 scripts/check_purchase_plan.py
```

Current files: [revisions.py](../../backend/shop/shb/revisions.py), [models.py](../../backend/shop/shb/models.py), additive SHB0019/0020 migrations, shared request service/views/templates and existing customer routes. [revision_tests.py](../../backend/shop/shb/revision_tests.py) is included in both ordinary and retained SHB checks. Existing browser/demo scripts assert the two linked revisions and all20 ordinary captures.

The private9-file Astro release/manifest is unchanged. Retained exact tools remain separate synthetic evidence; normal pinned Nix/source/runtime/native/licence/OCI/CI and actual company/provider/mail/host/ingress/database/independent/recovery/human qualification remain pending. Commercial defaults/rates/terms are explicit synthetic fixtures, not real adoption. Company inputs arrive later in the single [decision register](../decisions.md); no repeat request. The authorized independent off-host runner is unassigned. No real bank/mail/storage/protected-host/DNS/TLS action, `.env`/cache access or paid provision occurred.

Next shared work: extend the existing SHB recovery/replay assessment and tests to the new archived closing intents, ordinary notice delivery/capture and immutable replacement lineage, retaining original invitation clocks, coupon outcomes and paid-order references before reopening. This is local preparation; independent restore/complete-loss qualification remains gated. No parent SUMMARY, FULL_PASS or count change is claimed:11/42 retained summaries and1/14 documentary phases.
