# Complete-cart checkout rehearsal — 2026-10-26

Status: partial implementation of 03-01/04-01/07-02–03 under [final purchase-flow revision2](../../PURCHASE-FLOW-AMENDMENT.md). This is dated local evidence, not full plan/phase acceptance or commercial approval.

## Implemented

`catalog.checkout` applies the fixed synthetic seller policy to every retained IP/support line or holds the entire basket. Required minima come from the fixture policy, not a universal board-category rule. New packages in this basket are allocated once and priced once; per-line totals sum to the basket total. No existing-credit pooling, silent line drop/split or ready-kit-to-development substitution. Exact cart/catalog/platform/offer/rights/start/staged-delivery, resolved business/entity/contact defaults and complete source document definition are frozen together. Real ready-kit catalog entries remain empty; the ready-kit cart test injects an explicitly synthetic catalog only inside its test context.

Verified local customer API `/api/v1/checkout-rehearsal/` and no-JavaScript `/purchase/checkout-rehearsal/` use that same service. The saved cart links to the page. Commands accept only a canonical request UUID and SHA256 of reviewed bytes. Stale cart/business/source changes fail; exact committed retries reconcile before current-cart admission. Owner locking and unique snapshot/retry keys prevent duplicate captures and prevent alias keys from being reused for another scope. CSRF, strict bounded parsers, no-store/no-referrer/CSP and customer resource permissions remain enforced. Business values stay in private snapshots and previews; receipts carry metadata only.

`SyntheticCheckout` and `SyntheticCheckoutKey`, catalog migrations0013/0014, retain prepared facts with database-constrained local-synthetic/false financial and effects flags. The archive helper publishes/recovers exact private snapshot bytes before recording its receipt, outside database locks. The reproducible demo now uses actual customer cart/business/API/no-JavaScript routes and temporary archive recovery alongside the separately labelled existing single-draft fake-payment/staged-delivery scenario.

## Verification

- Full pinned backend/owned PostgreSQL18.6 local regression: `CORE_LOCAL_PASS checks=5 tests=353 duration_seconds=93.302`; migrations/no drift and loopback Gunicorn checks pass. No off-host database outage/recovery or production claim.
- Final focused `shop.catalog.checkout_tests`:14 tests,1.652s, pass after adding explicit per-line amount totals. Covers mixed/support-only/ready-kit baskets, seller-policy minimum changes, insufficient support across two IP lines, unapproved-line whole-basket hold, stale review, retry aliases, concurrent capture, business/document source holds, CSRF/private resource access, production denial, API/form parity, archive failure/recovery and database refusal of actual effects. The full run precedes the final per-line-total assertion; the final focused lane covers that addition.
- Extended `scripts/demo_purchase_flow.py`: `PURCHASE_FLOW_DEMO_PASS`, including `complete_cart_checkout` with all lines retained, business/document revisions, API/form same capture, recovered archive, acceptance false. Uses fresh owned PostgreSQL and synthetic `.invalid` identity/details, then cleans up. No actual mail/bank/host actions.
- Planning/source reconciliation and whitespace checks pass. Frontend source/tool graph unchanged; prior frontend evidence retains its exact scope and pinned Node24.22 qualification remains pending.

## Remaining

Bind this complete-cart retained snapshot to explicit synthetic acceptance/document fixtures and one payment attempt/order reference, with archive-before-dispatch and lookup-only uncertainty. Keep the existing single-draft scenario separate until that integration is proved. Actual legal acceptance, approved document bodies/versions, country/tax applicability, applicable encrypted host bindings, approved prices/rights/kit/support policy, real order/licence/support ledger and fulfilment remain pending. Recording or archiving a prepared checkout does not accept terms, authorize money, grant credits or fulfil delivery. No protected/external authority is added. All14 phases/29 plan records and11 completed-plan records retain their prior completion counts.
