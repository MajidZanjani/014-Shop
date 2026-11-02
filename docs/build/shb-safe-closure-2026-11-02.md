# SHB safe pre-dispatch cancellation and expiry

Authority: [SHB revision 1.1](../../014-Shop-SHB-Proposal-Revision-2026-10-30.md). This immediately follows [the paid-order continuation](shb-paid-orders-2026-11-02.md), implementation07cb88d. Both continue existing07-03 inline; matching dated ASIC offers and full parent acceptance remain unfinished. All records and bank behavior remain explicitly local/synthetic.

## Behavior

The originating invitation session can deliberately cancel an accepted FPGA checkout whose payment has never been dispatched. A GET never cancels or releases anything. The existing worker can also expire an unpaid checkout after its recorded synthetic bank/order deadline. Neither action extends the coupon's claim deadline, changes accepted prices or creates another purchase.

Closing uses one immutable saved intent, then recoverable archive publication, then an atomic safe terminal outcome and coupon release. The prepared intent immediately fences new payment attachment/dispatch/finalization. Archive failure retains the coupon and blocks payment; exact retry or the existing admitted worker can complete the same saved intent after invitation revocation/expiry. The worker does not reopen customer access.

An attached attempt must still be prepared, cancelled or expired. A prepared attempt is stopped before the coupon is released, with its stop timestamp retained. Uncertain or observed attempts cannot enter this path, even if a browser says the payment failed. Captured/refunded purchases retain their original paid order and consumed concession. Existing authenticated lookup/reconciliation continues independently. There is no blind bank retry or inferred provider cancellation guarantee.

Two independent PostgreSQL races exercise the boundary. Cancellation during attempt archive publication wins before the one-way bank claim and prevents any bank operation. A bank claim committed first makes cancellation fail while the coupon remains held; the original bank call then produces one paid order and one consumed concession. Database guards also prohibit attaching a new attempt, moving an old attempt into dispatch, or finalizing a purchase after a closing intent exists.

Additive access0009 and SHB0011/0012 migrations preserve the intent/receipt, bind release to the exact accepted checkout, and require the archived applied closure and concession release to commit together. Existing attributed pre-offer ASIC decline/release is retained. No time accounting, task email, balance or new IP fulfilment is connected.

## Executed evidence

Final unchanged-source run: **439 tests passed**, none failed or skipped (96 SHB,95 access/recovery,104 payment,30 staff review/navigation,24 local worker/statement-mail,75 preserved transactions/archive,9 source/catalog and6 actually network-isolated adapter cases). Django check, all additive migrations and schema drift checks passed. [Exact test/source record](../evidence/shb/retained-tests/55006209e60d31a27892bba57822c521100ea5da5ae6c787175c1ec78920e4ee.json).

Actual Chromium151.0.7922.173/Node24.15.0 passed **47 checks** in JavaScript/no-JavaScript modes at320px. It persisted2 ASIC50-hour requests,4 FPGA checkout/acceptances (2 paid,2 safely cancelled),2 bank operations,2 paid orders and2 durable purchase-notice captures. [Exact browser/source record](../evidence/shb/retained-tests/70f7fe71e607a3960e2df3daad8a77a47866058dcf1d2a7e451ba96fbd4fd825.json). Both final records bind identical hashes for326 backend files/8 scripts, checked unchanged across each run. Private empty-form screenshots: `.scratch/shb-checkout-browser-i4cll_t4`. Planning activity3 tests passed.

The first focused run passed103 tests (94 SHB plus9 source/catalog), with additive migrations and schema drift checks clean; its exact earlier snapshot remains e8b34cd7. It is not promoted to the final two-race/browser source.

The actual isolated [RED report](../evidence/shb/safe-closure-red-2026-11-02.json) ran one test and failed only because native cancellation returned400 rather than200. GSD returned `RED_EVIDENCE_OK`. Its cloned scratch helper initially labeled the command with its parent helper's filename; command metadata was corrected to the actual `.scratch/shb_closure_target.py` invocation without changing the captured report.

The expiry test waits for an actual short server deadline in the disposable fixture. It does not change host/server clocks. No off-host interruption/fault/exhaustion drill is claimed; the separately tagged off-host test remains gated and unchanged as described in the paid-order report.

## Reproduce

From the repository root, using the already retained exact tool archives:

```sh
python3 scripts/check_shb_retained.py --shared
python3 scripts/check_shb_retained.py --browser --release .scratch/shb-private-resume-t2p3r5cc/release --browser-binary /nix/store/53p8msmqxpi829zdrw6qkvaamidxy9cj-chromium-151.0.7922.173/bin/chromium --browser-node /nix/store/5a8ysg1jnj8jmzzyfcfw7rvpvnp5rfpa-nodejs-24.15.0/bin/node
python3 -m unittest discover -s tests -p 'test_planning_activity.py'
python3 scripts/check_planning.py
python3 scripts/check_purchase_plan.py
```

The retained tools are separate synthetic workspace evidence, not normal Nix packaging, actual OCI/runtime/provider, independent or human acceptance. The normal pinned environment remains unavailable under the prior documented tool boundary. No pins, host permissions, shared services or live resources were changed. No .env or http_cache.sqlite access was needed.

## Next

Continue matching dated ASIC offers and exact request revision/customer/scope/quantity/price/terms acceptance, withdrawal/expiry/reissue and the remaining ordinary request/customer notices. Staff technical readiness remains unpaid offer preparation, not a payable approval. Actual commercial/provider/mail/host/independent qualification stays pending through the existing single decision register; company inputs were not requested again. No parent SUMMARY or completion-count change is warranted.
