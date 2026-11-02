# SHB matching ASIC offers and exact purchase acceptance

Authority: [SHB revision 1.1](../../014-Shop-SHB-Proposal-Revision-2026-10-30.md), including Appendix A. This continues existing07-03/07-04 inline after the [paid-order](shb-paid-orders-2026-11-02.md) and [safe-closure](shb-safe-closure-2026-11-02.md) slices. It is local synthetic implementation evidence. Full parent acceptance and live qualification remain open.

## Implemented behavior

An assigned reviewer with current recent MFA can issue one matching dated ASIC offer after the latest exact request review establishes technical readiness. Readiness alone still creates no payable purchase. Issuance freezes the request/customer/revision/hash, project and requested assistance/context/timing, explicit prerequisites/exclusions, quantity and25-hour bundle size, rate/discount/tax/currency, policy and document bodies/versions, issuer and technical-review attribution, and issue/expiry instants. The14-calendar-day lifetime is an explicit synthetic policy; it does not establish real commercial adoption.

The immutable offer is prepared, archived and recovered before publication. Publication rechecks current staff MFA/credential/epoch, exact assignment and current request review after archive I/O. Failed archive publication retains the same prepared identity; exact retry recovers it. Revocation during I/O prevents publication. PostgreSQL uniqueness/locks admit one active offer per request and one checkout per offer; material in-place request/offer edits cannot reuse approval.

The original ASIC request's reserved concession stays attached to that request. Issuance and checkout carry its exact percentage/policy even when the original new-claim deadline has actually elapsed. Today’s rates/policy cannot reprice an issued offer. The reviewed offer’s document bodies are also retained, rather than regenerated from changed copy at acceptance. A new offer remains an explicit future lifecycle action.

The customer path `/purchase/shb/offer/<offer-id>/` requires current ASIC invitation access to the same customer/company and applicable project scope. It provides the current offer and blank billing/contact inputs. It provides no saved private contact/address prefill or history authorization. Quantity, engineering scope, rate, hours and discount come from the offer, not hidden customer fields. GET has no commercial or message effect.

Native Review then explicit terms acceptance and separate Privacy Policy acknowledgement bind the exact signed offer, documents, current form and originating invitation session. Acceptance reuses the existing archived checkout/acceptance/payment records. New checkout/dispatch after offer expiry is denied, including a PostgreSQL dispatch guard; authenticated existing-payment lookup/finalization continues after invitation revocation. A browser success never proves capture.

Verified payment finalizes one ASIC paid order with its approved scope and25×quantity purchased hours, consumes the original request reservation once, and queues the same ordinary support-team purchase notice. Repeated payment submits retain one bank operation and order. The existing recent-MFA assigned paid-order page shows the accepted ASIC scope/prerequisites/exclusions. The existing worker captures the durable fake notice. No actual mail or named-customer identity is asserted.

The existing safe never-dispatched cancellation path now also matches the ASIC request hold. It stops the accepted checkout, archives its safe closure, releases that exact unused reservation once and closes the offer. Uncertain payment cannot use this path. Pre-acceptance request/offer withdrawal, automatic final expiry/release, explicit replacement/reissue and the remaining ordinary request/customer notifications are still unfinished; an expired unaccepted offer keeps its concession held until that safe lifecycle is implemented.

Every order records only its own bundle size, quantity and purchased hours. No new IP fulfilment, online support-time accounting, cumulative balance, staff time entry, task email or customer support/bundle panel is connected.

## Current files

- [offers.py](../../backend/shop/shb/offers.py), [models.py](../../backend/shop/shb/models.py) and additive SHB0013/0014 plus access0010 migrations implement immutable offer publication, scoped checkout, PostgreSQL provenance and effect admission.
- SHB checkout/forms/views/templates and customer/staff URL additions provide native protected offer issue/review/acceptance. The existing staff request and paid-order screens retain current MFA and exact resource assignments.
- Shared checkout-payment hooks, SHB paid-order and closure services match the original ASIC request hold, preserve exact offer identity and retain late reconciliation. Existing FPGA and historical payment paths remain regression-tested.
- The common staff JSON/form readers retain their1KiB default. Only offer issuance explicitly admits a bounded32KiB request so its two1000-character prerequisite/exclusion fields work with encoded Unicode.
- [offer_tests.py](../../backend/shop/shb/offer_tests.py) adds19 cases. Both ordinary and retained SHB check scripts include them. The existing loopback demo/browser scripts exercise ASIC offers with CSRF-protected request submission and actual synthetic staff password/possession-code verification during fixture preparation.

## Executed evidence

Final unchanged-source run: **458 tests passed**, none failed or skipped:115 SHB (including19 offer cases),95 access/recovery,104 payment,30 staff review/navigation,24 local worker/statement-mail,75 preserved transaction/archive,9 source/catalog and6 actually `unshare --net` adapter cases. Django check, all additive migrations and schema drift checks passed. [Final test/source record](../evidence/shb/retained-tests/2e56a1b8dd097255b5da8a539889aedf9b18d732587d132bf74f0864fa087daf.json).

Actual Chromium151.0.7922.173/Node24.15.0 passed **59 checks** in JavaScript/no-JavaScript modes at320px. Browser runs persisted4 ASIC requests (2 prepared offers and2 native initial submissions),6 shared checkout/acceptances (2 paid ASIC50-hour orders,2 paid FPGA30-hour orders,2 safely cancelled FPGA orders),4 bank operations,4 paid orders and4 durable fake purchase-notice captures, with0 historical fulfilments. The19 PostgreSQL offer cases additionally exercise native staff authority, competing issuance/acceptance, post-deadline discount preservation, immutable price/documents, interrupted archives, uncertain payment and cancellation. [Final browser/source record](../evidence/shb/retained-tests/02a6058c130ec85a9e93c9ba9e89ae0b1cfb60d0203955c5230a8d1484d504fe.json).

Both final records bind identical hashes for **332 backend files and8 scripts**, verified unchanged across each run. Private empty-form screenshots are in `.scratch/shb-checkout-browser-ncexecxa`. The private9-file Astro release/manifest `ef2d68408ac264a2da888af45ec167242c1a21680990d66a772bd761b86941f3` is unchanged. Planning activity3 tests and both required planning checks pass.

The initial [RED report](../evidence/shb/asic-offer-red-2026-11-02.json) runs exactly one target: technical readiness succeeds, then offer issuance fails with404 instead of201. GSD returned `RED_EVIDENCE_OK`; the test and resumed state were committed/pushed as `e0efab5`. A development model-string syntax error was corrected before migrations; it was not classified as RED. The first browser invocation had a mistyped Node path and failed before browser execution; the corrected exact command below passed. An earlier458-test/59-browser snapshot is retained separately; it is not substituted for the final issuer/review-provenance source above.

Locking and transaction use follow the repository’s Django5.2 documentation: [transactions](https://docs.djangoproject.com/en/5.2/topics/db/transactions/) and [select_for_update](https://docs.djangoproject.com/en/5.2/ref/models/querysets/#select-for-update). Concurrency evidence uses actual PostgreSQL transaction tests.

## Reproduce

From the repository root, using the existing retained exact tool archives and private release:

```sh
python3 scripts/check_shb_retained.py --shared
python3 scripts/check_shb_retained.py --browser --release .scratch/shb-private-resume-t2p3r5cc/release --browser-binary /nix/store/53p8msmqxpi829zdrw6qkvaamidxy9cj-chromium-151.0.7922.173/bin/chromium --browser-node /nix/store/5a8ysg1jnj8jmzzyfcfw7rvpvnp5rfpa-nodejs-24.15.0/bin/node
python3 -m unittest discover -s tests -p 'test_planning_activity.py'
python3 scripts/check_planning.py
python3 scripts/check_purchase_plan.py
```

The retained lane verifies the2 immutable OCI archives/configs/91 layers, exact locked installed inventory and actual Python3.13.16/Django5.2.18/PostgreSQL18.6/libpq180006, then uses a read-only store overlay and owned disposable database. It is separate synthetic evidence. The normal pinned Nix shell/source packaging remains unavailable under the prior recorded boundary; normal Nix, OCI/runtime, CI, provider, independent/off-host and human qualification remain pending. No version pin or host permission was changed.

## Remaining boundary

Continue explicit pre-acceptance ASIC request/offer withdrawal, final expiry/release and replacement/reissue with archived safe outcomes and no blind bank retry. Finish ordinary request/clarification/decline/offer/customer purchase notices through the existing worker, including process-loss/retry cases. Preserve the completed exact-offer/acceptance/payment path and existing safe accepted-checkout cancellation.

Actual company values and approvals remain pending in the single [decision register](../decisions.md); company inputs will arrive later and were not requested again. The local `catalog.synthetic_offer()` rates/tax/policy and synthetic14-day offer policy are test inputs only. No actual ASIC no-expiry adoption, approver, bank/mail/provider guarantee, production/bank-sandbox database, protected-host/ingress/DNS/TLS operation or paid provision was introduced. No `.env` or `http_cache.sqlite` access was needed. The independent authorized off-host runner remains unassigned.

No parent SUMMARY, FULL_PASS, SHB acceptance checkbox or completion-count change is warranted. Counts remain11/42 retained summary records and1/14 documentary phases.
