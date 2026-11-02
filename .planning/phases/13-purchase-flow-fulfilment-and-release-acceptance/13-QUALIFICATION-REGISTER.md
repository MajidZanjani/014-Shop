# SHB qualification register

Current authority: [SHB revision 1.1](../../../014-Shop-SHB-Proposal-Revision-2026-10-30.md), SHA256 `ba801dff4adbfdcfa0f1e43cfe1f2d6963780476867da1b5e6f737230a472b5e`. The user explicitly replaces the earlier active product plan on 2026-10-30. Current routing: [STATE.md](../../STATE.md) / [ROADMAP.md](../../ROADMAP.md).

Use all SHB-01–30 in REQUIREMENTS.md; current revised product evidence is pending. Required local lanes: catalog/forms, invitation/private routes, minimum no-JS/React UI, assigned recent-MFA ASIC review, PostgreSQL coupons/orders/payment races, outbox transaction mail and restore/replay. Full release additionally retains exact shared BUILD/host/independent/runtime/recovery/legal/CI and human gates. Legacy IP/licence/package/time-ledger/task-usage-email cases are historical/deferred, not launch blockers.

One concise external-input register: docs/decisions.md. No new rehearsal feature or repeated unchanged audit merely to add coverage.

## Current local acceptance trace — 2026-11-02

This table maps each current requirement to executed local component tests and the browser scenario. Exact totals, source hashes, commands and limits are in docs/build/shb-financial-handoff-2026-11-02.md and docs/build/shb-recovery-2026-11-02.md. Earlier financial/staff-browser reports retain their exact source-bound baselines. Current565 tests/137 browser checks and matching365-backend/eight-script records are owned by docs/build/shb-invitation-issuance-2026-11-02.md. A local pass does not mark a requirement or phase complete; actual bank/mail/host/runtime/recovery and attributable human qualification remain pending.

Test paths below are relative to backend/shop unless prefixed tests/ or scripts/. The shared lane executes the cited SHB/payment/access modules against owned PostgreSQL; the source/catalog lane executes tests/test_shb_*.py. Browser evidence now covers71 customer and66 staff native-form checks in both JS/no-JS modes at320px. Staff password/possession-code authentication, exact scope/CSRF denials, refund and attributed handoff are exercised in actual local Chromium. Attributable human verification remains pending.

| ID | Executed local evidence | Remaining limit |
|---|---|---|
| SHB-01 | shb/tests.py, tests/test_shb_catalog.py, scripts/browser_shb.mjs: one product and exact variants | Actual private deployment remains pending |
| SHB-02 | shb/tests.py denies old new-sale routes; preserved shared checkout/archive regressions remain separate | Historical obligations preserved; actual release gate open |
| SHB-03 | shb/checkout_tests.py and browser30-hour FPGA purchase; source quantity/money tests | Live rate/currency authority pending |
| SHB-04 | shb/tests.py and offer_tests.py; browser request then reviewed50-hour ASIC purchase | Live ASIC intake/offer terms pending |
| SHB-05 | shb/checkout_tests.py, offer_tests.py, discount_tests.py: forged values and quantity denial | Actual provider bounds pending |
| SHB-06 | shb/tests.py common fields/same-phone; native/browser shared form | Actual tax/territory policy pending |
| SHB-07 | shb/paid_order_tests.py: one purchase/coupon/notice; browser eligible FPGA path | Actual commercial/provider qualification pending |
| SHB-08 | shb/offer_tests.py, revision_tests.py: unapproved/altered scope denied, fresh review for changed work | Actual technical/commercial attribution pending |
| SHB-09 | shb/review_tests.py, lifecycle_tests.py, notification_tests.py: triage/closing/notices | Actual reviewer/mail operation pending |
| SHB-10 | shb/tests.py and private release source tests: gated manifest files/deep routes/alternate host denial | Actual ingress/private origin/storage/host tests pending |
| SHB-11 | shb/tests.py, checkout_tests.py and invitation_admin_tests.py, invitation_issuance_tests.py; actual native staff revocation/reissue and two surviving-session denials | Actual ingress/session delivery qualification pending |
| SHB-12 | shb/tests.py and recovery_tests.py: calendar month-end/leap-year and original expiry | Actual trusted clock/runtime qualification pending |
| SHB-13 | shb/tests.py, discount_tests.py: reusable entry and no GET reservation/request/mail effects | Actual ingress token redaction remains pending |
| SHB-14 | shb/tests.py, offer_tests.py, checkout_tests.py, invitation_admin_tests.py, invitation_issuance_tests.py: no-store/privacy/exact grants/no bearer or prefill | Actual logs, proxy/referrer and private-origin qualification pending |
| SHB-15 | shb/discount_tests.py: customer/variant/expiry/revocation/stacking denial | Actual discount defaults/authority pending |
| SHB-16 | shb/discount_tests.py and checkout_tests.py PostgreSQL concurrent one-use arbitration | Actual runtime/database qualification pending |
| SHB-17 | shb/discount_tests.py and offer_tests.py: reserved concession survives claim expiry/review | Actual adopted clock/discount defaults pending |
| SHB-18 | shb/closure_tests.py and lifecycle_tests.py: archived safe release; uncertainty keeps hold | Actual provider closing/reconciliation rules pending |
| SHB-19 | payments notification/attempt tests and shb/paid_order_tests.py deny forged/unobserved success | Actual selected-bank authentication/sandbox evidence pending |
| SHB-20 | shb/paid_order_tests.py, notification_tests.py, financial_tests.py: durable identities/races/replay | Actual provider and recovery completeness pending |
| SHB-21 | payments/operation_tests.py and shb/financial_tests.py: lookup-only uncertain operations | Actual provider duplicate/late-payment rules pending |
| SHB-22 | shb/offer_tests.py, paid_order_tests.py, financial_tests.py: staff/lookup after invite revocation | Actual independently authenticated bank route pending |
| SHB-23 | shb/notification_tests.py, paid_order_tests.py and worker regression: finite leases/held failures | Actual mail route/delivery remains unqualified |
| SHB-24 | shb/financial_tests.py rejects usage fields; paid/refund flows preserve no ledger/fulfilment effects | Manual time tracking remains outside shop |
| SHB-25 | shb/financial_tests.py: manual review, full synthetic refund, original order/coupon, attributed team communication; actual local staff Chromium in both script modes | Partial local scope: actual refund/chargeback/tax/provider policy pending |
| SHB-26 | shb/paid_order_tests.py and financial_tests.py retain purchased order despite invite revocation | ASIC no-expiry/service terms need actual adoption |
| SHB-27 | scripts/browser_shb.mjs:71 customer/66 staff native keyboard checks, two modes/320px; shb/financial_tests.py scope/MFA/CSRF | Attributable human UAT and actual deployment remain pending |
| SHB-28 | shb/recovery_tests.py, financial_tests.py and invitation_admin_tests.py, invitation_issuance_tests.py: retained archives, revocation clocks, corruption holds and same-reference replay | Partial local scope: full post-backup completeness, off-host restore/loss/custody pending |
| SHB-29 | shb/catalog/checkout/discount/financial tests: synthetic-only/null live policy and fixed denials | Actual commercial/provider inputs remain pending in docs/decisions.md |
| SHB-30 | Existing protection inventory/allowlist/release review retained; local suite makes no host changes | Actual protected-host/runtime/exhaustion/complete-loss qualification pending |

No independent off-host runner is assigned. No live permission, bank integration, actual refund policy, legal adoption or complete post-backup recovery is inferred from the table. Normal pinned Nix/source/runtime, native/licence/OCI/CI and actual deployment gates remain binding. Deferred IP/time-accounting tests remain historical; shared security/payment/recovery checks are retained.

## Historical first SHB batch — explicit pause

See docs/build/shb-bootstrap-2026-10-30.md. Focused29 tests, full frontend138 tests, header/form16 and shared security/recovery95 pass for their stated scopes. Combined later110 cases have six adapter-harness guard failures; aggregate is not passing. Actual Chromium fails before browser-ready. Source295/eight-import proof precedes final fixture edits. No browser/native UI, full acceptance, paid flow or live approval. Keep actual failure and original gates pending.
