# SHB per-order completion and ordinary purchase notice

Authority: [SHB revision 1.1](../../014-Shop-SHB-Proposal-Revision-2026-10-30.md). This continues existing 07-03 inline. It does not complete the parent plan or change historical completion counts. The implementation and all fixtures remain explicitly local/synthetic, with no real payment, approved commercial terms, email delivery or support entitlement.

## Result

A matching archived acceptance and recoverable captured bank observation now finalize one immutable paid-order record on the existing shared checkout/payment records. The same PostgreSQL transaction consumes its reserved coupon and queues the ordinary purchase notice. Consumed slots remain occupied, including after a financial refund; a new FPGA/ASIC claim cannot reuse them. Current code status, expiry or prices never silently reprice an accepted purchase.

The paid order preserves the existing acceptance/order reference, customer, billing/transaction contact, exact FPGA variant, bundle size, quantity, purchased hours for that order, eligibility scope, accepted documents, attempt and captured-observation identities. The protected confirmation shows the completed synthetic purchase only to its originating invitation session. A contact field creates no company/private-resource authorization.

Shared pay/lookup processing invokes completion after recorded capture. If capture commits but finalization/archive publication fails, the payment remains captured and the coupon remains reserved. The existing single leased worker finds the unfinished captured acceptance and completes the same order after its archive is available, even after invitation revocation/expiry. Uncertain bank dispatch remains lookup-only and retains the concession. Missing acceptance/capture/archive evidence cannot finalize a purchase. A refund preserves the original order and consumed coupon without creating a second purchase or adjusting support time.

The existing worker also leases an ordinary purchase notice, with a fixed synthetic recipient and stable effect/order reference. Archive failure leaves the paid order intact. An expired worker loses ownership; another finite claim can recover the same durable fake capture. Lost completion responses produce one capture. This is a local durable sink, not proof of SMTP or customer-mail delivery. Actual mail routing and request/customer notifications remain pending where not yet implemented/qualified.

Staff can inspect only explicitly assigned paid orders through `/staff/shb-orders/` and its exact-order detail. The existing staff host, recent MFA/current epoch and per-resource assignment checks apply. The list is bounded and paginated. The detail shows customer/contact, per-order quantity/hours, accepted documents, notice state and current financial status, so a repeated observation/refund is identifiable as the same purchase. Local `grant-shb-order`/`revoke-shb-order --order UUID` actions extend the existing operator command. Staff reset/revocation and selected-restore grant clearing include the new assignment.

Additive access0008 and SHB0009/0010 migrations enforce paid-order/capture provenance, immutable records, atomic coupon consumption/notice intent, permanent consumed-slot occupancy and bounded fenced notice leases. No historical record is retagged. No IP/time fulfilment, support balance, used/remaining-hour calculation, staff time-entry or task-usage email is connected.

## Verification

Final unchanged-source PostgreSQL run: **429 tests passed**, none failed or skipped, including86 SHB,95 shared access/recovery,104 payment,30 staff review/navigation,24 local worker/statement-mail,75 preserved transaction/archive,9 pure source/catalog and6 actual network-isolated adapter cases. Django check, all additive migrations and `makemigrations --check --dry-run` passed. [Exact test/source record](../evidence/shb/retained-tests/4f86876cde93b9ba08f1e7cb464b29b090eee589bc0e1a70220a395a44e38fea.json).

Actual Chromium151.0.7922.173/Node24.15.0 passed **41 checks** in JavaScript/no-JavaScript modes at320px. The demonstration persisted2 ASIC50-hour requests and2 FPGA30-hour checkout/acceptance/payment/paid-order records despite duplicate payment clicks, then the existing worker produced2 durable synthetic purchase-notice captures. No historical IP/time fulfilment was created. [Exact browser/source record](../evidence/shb/retained-tests/cac82c7b6553211040e187a023907f87329766b0c34b35c9309035942190fa04.json). Both final records bind identical hashes for321 backend files and8 scripts, checked unchanged across the runs. Private empty-form screenshots: `.scratch/shb-checkout-browser-zuxei3yt`. Planning activity3 tests also passed. Earlier browser snapshot8b7b50a1 remains historical evidence for its exact earlier script hashes.

The validated test-first baseline is [the actual isolated RED report](../evidence/shb/paid-order-red-2026-11-02.json): one target ran and failed specifically because captured payment left its coupon reserved. GSD returned `RED_EVIDENCE_OK`. The first aggregate report had two unittest summaries and was rejected; the first isolated rerun encountered a guarded test-database teardown timeout. The corrected isolated command used the existing disposable `--keepdb` convention. Original aggregate/teardown reports remain in `.scratch/shb-paid-red.json` and `.scratch/shb-paid-red-teardown.json`.

Intermediate controls are preserved: `.scratch/shb-paid-first.log` records the missing recovery-reference fixture failure, `.scratch/shb-paid-shared.log` the added grant-count expectation, and `.scratch/shb-paid-final-tests.log` the off-host authorization denial. The latter came from selecting the whole worker module. The local lane now names `shop.worker.tests.OwnershipTests` and the existing statement-mail regressions explicitly. The tagged off-host interruption test is unchanged, unexecuted beyond its authorization assertion and still requires an assigned authorized runner. No off-host flag was fabricated and no selected test is skipped.

## Reproduce

From the repository root, using the already retained tool archives identified in `scripts/check_shb_retained.py`:

```sh
python3 scripts/check_shb_retained.py --shared
python3 scripts/check_shb_retained.py --browser --release .scratch/shb-private-resume-t2p3r5cc/release --browser-binary /nix/store/53p8msmqxpi829zdrw6qkvaamidxy9cj-chromium-151.0.7922.173/bin/chromium --browser-node /nix/store/5a8ysg1jnj8jmzzyfcfw7rvpvnp5rfpa-nodejs-24.15.0/bin/node
python3 -m unittest discover -s tests -p 'test_planning_activity.py'
python3 scripts/check_planning.py
python3 scripts/check_purchase_plan.py
```

The browser command supplies the automated local demonstration of FPGA review/acceptance/payment/completion and ASIC request intake. `scripts/demo_shb.py --serve --release .scratch/shb-private-resume-t2p3r5cc/release` remains the interactive demonstration inside its pinned backend environment; that normal environment is currently unavailable. Invitation/code values are kept in private scratch files. Use only Synthetic Company Limited and synthetic.invalid contacts.

The retained-tool lane rechecks the two immutable OCI archive/config/91 layer hashes, locked installed versions and actual Python3.13.16/Django5.2.18/PostgreSQL18.6/libpq180006. It uses a read-only store overlay and its own disposable Unix-socket databases. Normal Nix source/runtime/image/native/licence/CI/provider/independent/human qualification remains pending under the previous documented tool boundary. No dependency pins or host permissions were changed.

## Remaining scope

Complete safe payment-linked cancellation/expiry before releasing a held FPGA concession; uncertainty must continue holding it. Then continue matching dated ASIC offers, exact request revision/scope/customer/quantity/price/policy acceptance, withdrawal/expiry/reissue, and ordinary request/customer transaction notices. Existing technical readiness is not an issued payable ASIC offer. Proposed commercial defaults remain synthetic or pending actual adoption.

Actual company inputs will arrive later through `docs/decisions.md`; they were not requested again. All production, bank/mail/storage, protected-host, DNS/TLS, database qualification, off-host recovery/runtime and activation gates stay closed. No .env or unrelated http_cache.sqlite access was needed.

Subsequent continuation: [safe closure](shb-safe-closure-2026-11-02.md) completes archived pre-dispatch cancellation/expiry and payment-race fencing, with439 tests/47 browser checks. Its report is the current source boundary.
