# Roadmap — Supporting Hours Bundle

Current authority: [SHB revision 1.1](../014-Shop-SHB-Proposal-Revision-2026-10-30.md), SHA256 `ba801dff4adbfdcfa0f1e43cfe1f2d6963780476867da1b5e6f737230a472b5e`. The user explicitly replaces the earlier active product plan on 2026-10-30. Current routing: [STATE.md](STATE.md) / [ROADMAP.md](ROADMAP.md).

**Current development focus:** 6 — Invitation scope, verified resources and staff MFA.

**Last fully completed phase:** 1 — documentary authority/reconciliation only; historical implementation evidence is not SHB acceptance.

**Current plan:** 06-01 — protected staff invitation revocation and recoverable audit verified locally; remaining administration/actual qualification open.

**Execution status:** in progress — local invitation revocation verified with 543 tests/123 browser checks; remaining staff issuance/discount administration and actual qualifications stay open.

**Next implementation task:** Continue existing 06-01/07-02 protected invitation issuance/reissue and scoped discount administration using explicit eligible associations and safe secret handling; preserve all actual input, runtime and external-operation gates.

Stable T01–T14/folder IDs preserve history. Titles and active task scopes now follow SHB 1.1. Completed summary counts below are historical records, not engineering effort or new commercial acceptance.

## Phases

- [x] **Phase 1: Source authority and SHB scope reconciliation**
- [ ] **Phase 2: Reproducible application and isolated deployment foundation**
- [ ] **Phase 3: Supporting Hours Bundle catalog and approved pricing**
- [ ] **Phase 4: Shared SHB form, invitations and private storefront**
- [ ] **Phase 5: SHB durable records, archives and outbox**
- [ ] **Phase 6: Invitation scope, verified resources and staff MFA** — CURRENT DEVELOPMENT FOCUS; in progress — local invitation revocation verified with 543 tests/123 browser checks; remaining staff issuance/discount administration and actual qualifications stay open.
- [ ] **Phase 7: FPGA checkout, ASIC reviewed offers and scoped discounts**
- [ ] **Phase 8: Payment lifecycle and fault-injectable synthetic bank**
- [ ] **Phase 9: Selected-bank sandbox and complete reconciliation**
- [ ] **Phase 10: Paid SHB orders, transaction notices and manual handoff**
- [ ] **Phase 11: Private release delivery and protected-host qualification**
- [ ] **Phase 12: Independent backup, restore and SHB reopening**
- [ ] **Phase 13: Thirty SHB acceptance cases and release verification**
- [ ] **Phase 14: SHB handover and separately authorized activation**

## Phase details

### Phase 1: Source authority and SHB scope reconciliation

Goal: Retain immutable sources; apply SHB revision 1.1, document deferrals and reconcile every planning file.

Depends on: source authority. Local unaffected slices proceed while actual external gates remain pending.

Acceptance: Source hash, archive readback, planning inventory and all thirty acceptance mappings.

Requirements: retained shared controls in REQUIREMENTS.md.

Plans: [01-01-PLAN](phases/01-product-authority-repository-review-and-decision-register/01-01-PLAN.md), [01-02-PLAN](phases/01-product-authority-repository-review-and-decision-register/01-02-PLAN.md)

### Phase 2: Reproducible application and isolated deployment foundation

Goal: Reuse exact pinned Astro/Django/PostgreSQL/worker stack; retain database destination, all-write/attestation, native/licence/SBOM, immutable-image, CI and independent runtime gates.

Depends on: 1. Local unaffected slices proceed while actual external gates remain pending.

Acceptance: Original BUILD-01–08 criteria, actual PostgreSQL, full OCI/CI and authorized independent lifecycle/resource/storage observations. No full acceptance is claimed.

Requirements: retained shared controls in REQUIREMENTS.md.

Plans: [02-00-PLAN](phases/02-reproducible-application-and-deployment-skeleton/02-00-PLAN.md), [02-01-PLAN](phases/02-reproducible-application-and-deployment-skeleton/02-01-PLAN.md), [02-02-PLAN](phases/02-reproducible-application-and-deployment-skeleton/02-02-PLAN.md), [02-03-PLAN](phases/02-reproducible-application-and-deployment-skeleton/02-03-PLAN.md), [02-04-PLAN](phases/02-reproducible-application-and-deployment-skeleton/02-04-PLAN.md), [02-05-PLAN](phases/02-reproducible-application-and-deployment-skeleton/02-05-PLAN.md), [02-06-PLAN](phases/02-reproducible-application-and-deployment-skeleton/02-06-PLAN.md), [02-07-PLAN](phases/02-reproducible-application-and-deployment-skeleton/02-07-PLAN.md), [02-08-PLAN](phases/02-reproducible-application-and-deployment-skeleton/02-08-PLAN.md), [02-09-PLAN](phases/02-reproducible-application-and-deployment-skeleton/02-09-PLAN.md), [02-10-PLAN](phases/02-reproducible-application-and-deployment-skeleton/02-10-PLAN.md), [02-11-PLAN](phases/02-reproducible-application-and-deployment-skeleton/02-11-PLAN.md), [02-12-PLAN](phases/02-reproducible-application-and-deployment-skeleton/02-12-PLAN.md), [02-13-PLAN](phases/02-reproducible-application-and-deployment-skeleton/02-13-PLAN.md), [02-14-PLAN](phases/02-reproducible-application-and-deployment-skeleton/02-14-PLAN.md), [02-15-PLAN](phases/02-reproducible-application-and-deployment-skeleton/02-15-PLAN.md), [02-16-PLAN](phases/02-reproducible-application-and-deployment-skeleton/02-16-PLAN.md), [02-17-PLAN](phases/02-reproducible-application-and-deployment-skeleton/02-17-PLAN.md)

### Phase 3: Supporting Hours Bundle catalog and approved pricing

Goal: One Supporting Hours Bundle product; FPGA Supporting Hours Bundle/10 hours and ASIC Supporting Hours Bundle/25 hours. Strict positive quantity and authoritative integer money; approved ASIC base hourly rate exceeds FPGA. Per-order purchased hours only.

Depends on: 1. Local unaffected slices proceed while actual external gates remain pending.

Acceptance: SHB-01/03/04/05/29; null live rates/terms fail closed, explicit synthetic fixtures pass. Markdown is the reviewed catalog source.

Requirements: SHB-01, SHB-03, SHB-04, SHB-05.

Plans: [03-01-PLAN](phases/03-catalog-platform-and-offer-policies/03-01-PLAN.md)

### Phase 4: Shared SHB form, invitations and private storefront

Goal: Minimal common billing/contact form, same-phone helper and conditional tax; ASIC short assistance/context. Six calendar months in Asia/Tbilisi, UTC expiry, digest-only reusable invitations, current-state session checks and private static delivery.

Depends on: 3. Local unaffected slices proceed while actual external gates remain pending.

Acceptance: SHB-02/06/10/11/12/13/14/27. Deny base/deep/static/origin/alternate-host bypass and new IP purchases; GET has no purchase/request/coupon/mail effects.

Requirements: SHB-02, SHB-06, SHB-10, SHB-12, SHB-27.

Plans: [04-01-PLAN](phases/04-minimal-configurator-and-shared-purchase-flow/04-01-PLAN.md)

### Phase 5: SHB durable records, archives and outbox

Goal: Reuse immutable order/acceptance/payment and archived evidence/outbox primitives. Add invitation/request/offer/coupon records with explicit customer scope. Preserve old data and ledger without connecting SHB.

Depends on: 3. Local unaffected slices proceed while actual external gates remain pending.

Acceptance: Transactions/uniqueness/retry identity, archive-before-effects, bounded leased worker and failure recovery; no manual-time record import or cumulative balances.

Requirements: retained shared controls in REQUIREMENTS.md.

Plans: [05-01-PLAN](phases/05-durable-records-and-outbox/05-01-PLAN.md)

### Phase 6: Invitation scope, verified resources and staff MFA

Status: CURRENT DEVELOPMENT FOCUS; in progress — local invitation revocation verified with 543 tests/123 browser checks; remaining staff issuance/discount administration and actual qualifications stay open.

Goal: Invitation authorizes current offers/new purchases only; no customer history or prefilled private data. Retain verified-contact access for old private resources and MFA/recent verification/resource permissions for every staff route.

Depends on: 4, 5. Local unaffected slices proceed while actual external gates remain pending.

Acceptance: SHB-11/13/14/22. Forwardable bearer is not named identity; contact edits never replace the authorized company support contact.

Requirements: SHB-11, SHB-13, SHB-14.

Plans: [06-01-PLAN](phases/06-invitation-scope-and-staff-mfa/06-01-PLAN.md)

### Phase 7: FPGA checkout, ASIC reviewed offers and scoped discounts

Goal: Automatic eligible FPGA checkout; ASIC request/clarify/decline/withdraw/approve/dated offer/acceptance. One scoped percentage code; PostgreSQL reservations survive ASIC review beyond claim expiry. Immutable accepted price/scope revisions.

Depends on: 3, 4, 5, 6. Local unaffected slices proceed while actual external gates remain pending.

Acceptance: SHB-05/07/08/09/15/16/17/18. Concurrent one-use arbitration, price-change reacceptance, one active offer/reservation; no routine engineer approval for eligible FPGA.

Requirements: SHB-08, SHB-09, SHB-15, SHB-16, SHB-17, SHB-18.

Plans: [07-01-PLAN](phases/07-multi-line-cart-quotations-business-checkout-and-acceptance/07-01-PLAN.md), [07-02-PLAN](phases/07-multi-line-cart-quotations-business-checkout-and-acceptance/07-02-PLAN.md), [07-03-PLAN](phases/07-multi-line-cart-quotations-business-checkout-and-acceptance/07-03-PLAN.md), [07-04-PLAN](phases/07-multi-line-cart-quotations-business-checkout-and-acceptance/07-04-PLAN.md)

### Phase 8: Payment lifecycle and fault-injectable synthetic bank

Goal: Reuse one archived attempt claim and lookup-only uncertainty; authenticate/correlate merchant/order/amount/currency and preserve duplicate money events without duplicate purchase. Couple coupon consumption/finalization/outbox durably.

Depends on: 7. Local unaffected slices proceed while actual external gates remain pending.

Acceptance: SHB-19/20/21/22/23. Real PostgreSQL races/process interruption, forged return/callback denial, safe cancellation/expiry and no blind retry.

Requirements: SHB-19, SHB-20, SHB-21, SHB-22.

Plans: [08-01-PLAN](phases/08-payment-domain-and-fault-injectable-fake-bank/08-01-PLAN.md), [08-02-PLAN](phases/08-payment-domain-and-fault-injectable-fake-bank/08-02-PLAN.md), [08-03-PLAN](phases/08-payment-domain-and-fault-injectable-fake-bank/08-03-PLAN.md)

### Phase 9: Selected-bank sandbox and complete reconciliation

Goal: Implement only actual selected-bank documented hosted payment/callback/status/refund capabilities and transaction bounds. Keep unknown provider behavior disabled.

Depends on: 8. Local unaffected slices proceed while actual external gates remain pending.

Acceptance: Authenticated sandbox positive/negative evidence and complete financial windows under separately supplied merchant/provider authority.

Requirements: retained shared controls in REQUIREMENTS.md.

Plans: [09-01-PLAN](phases/09-selected-bank-reconciliation/09-01-PLAN.md)

### Phase 10: Paid SHB orders, transaction notices and manual handoff

Goal: Finalize accepted verified paid orders once with variant, quantity, per-order hours, scope and reference; staff order view plus retryable transaction/request notifications. Financial refunds link the original order; staff consult/inform manual support records.

Depends on: 7, 8. Local unaffected slices proceed while actual external gates remain pending.

Acceptance: SHB-07/20/23/24/25/26. No new IP licence/package/reference-design obligation, time credit/debit, usage calculation, time-entry screen, task-email automation or customer bundle panel.

Requirements: SHB-07, SHB-23, SHB-24, SHB-25, SHB-26.

Plans: [10-01-PLAN](phases/10-staged-delivery-and-support-ledger/10-01-PLAN.md), [10-02-PLAN](phases/10-staged-delivery-and-support-ledger/10-02-PLAN.md), [10-03-PLAN](phases/10-staged-delivery-and-support-ledger/10-03-PLAN.md), [10-04-PLAN](phases/10-staged-delivery-and-support-ledger/10-04-PLAN.md), [10-05-PLAN](phases/10-staged-delivery-and-support-ledger/10-05-PLAN.md), [10-06-PLAN](phases/10-staged-delivery-and-support-ledger/10-06-PLAN.md)

### Phase 11: Private release delivery and protected-host qualification

Goal: Private Object Storage releases; manifest-approved Astro snapshot behind Django authorization in isolated shop runtime. Retain unchanged shared ingress/TLS, full inventory/allowlist/activation-impact review, separate DB and aggregate CPU/memory/storage controls.

Depends on: 2, 4, 6. Local unaffected slices proceed while actual external gates remain pending.

Acceptance: SHB-10/30. No publicly readable protected copy/JSON/assets/sourcemap/preview bypass; exact scoped host/service/action authority before mutations, no A/AAAA before traffic path proof.

Requirements: SHB-30.

Plans: [11-01-PLAN](phases/11-private-delivery-and-protected-host/11-01-PLAN.md)

### Phase 12: Independent backup, restore and SHB reopening

Goal: Independent sbg backups, complete-pool-loss off-host rehearsal and custody. Block effects before exposure; invalidate restored sessions/MFA; reconcile original invitation expiry/revocations, customer scope, financial/order/acceptance/coupon/offer/document events.

Depends on: 5, 8, 10, 11. Local unaffected slices proceed while actual external gates remain pending.

Acceptance: SHB-28. Preserve original order references and prevent staff counting replay as a new sale. Five-minute WAL timeout, 35-day DB window, 15-minute RPO and four-hour operator-start restore are proposed targets; measure safe reopening separately.

Requirements: SHB-28.

Plans: [12-01-PLAN](phases/12-independent-recovery/12-01-PLAN.md)

### Phase 13: Thirty SHB acceptance cases and release verification


Goal: Exercise both variant paths, JS/no-JS keyboard/mobile, invite/static/customer isolation, PostgreSQL coupon/payment concurrency, transaction-mail failure and restore/replay. Trace each SHB-01–30 result to exact artifacts.

Depends on: 3, 4, 6, 7, 8, 10. Local unaffected slices proceed while actual external gates remain pending.

Acceptance: No skipped mandatory shared security/payment/recovery check; distinguish local/synthetic, selected-bank, actual OVH, production and attributable human evidence. Dedicated deferred IP/time-ledger tests are not SHB launch gates.

Requirements: SHB-01, SHB-02, SHB-03, SHB-04, SHB-05, SHB-06, SHB-07, SHB-08, SHB-09, SHB-10, SHB-11, SHB-12, SHB-13, SHB-14, SHB-15, SHB-16, SHB-17, SHB-18, SHB-19, SHB-20, SHB-21, SHB-22, SHB-23, SHB-24, SHB-25, SHB-26, SHB-27, SHB-28, SHB-29, SHB-30.

Plans: [13-01-PLAN](phases/13-purchase-flow-fulfilment-and-release-acceptance/13-01-PLAN.md)

### Phase 14: SHB handover and separately authorized activation

Goal: Version release/config/catalog/policy identities, actual support-offer approvals, operating owners, private release/rollback/custody and concrete pending external actions. Supply usable local demonstration and full commands.

Depends on: 9, 11, 12, 13. Local unaffected slices proceed while actual external gates remain pending.

Acceptance: SHB-29/30; required image/runtime/legal/CI/independent/recovery/host/mail/bank evidence and exact external action authority. No activation from proposal or generic deployment approval.

Requirements: SHB-29.

Plans: [14-01-PLAN](phases/14-shb-release-handover/14-01-PLAN.md)

## Progress

| Phase | Retained plan summaries | Status | SHB qualification |
|---|---|---|---|
| 1. Source authority and SHB scope reconciliation | 2/2 | Complete (documentary scope) | Source reconciliation only |
| 2. Reproducible application and isolated deployment foundation | 8/18 | In Progress | Pending actual revised evidence |
| 3. Supporting Hours Bundle catalog and approved pricing | 0/1 | In Progress | Pending actual revised evidence |
| 4. Shared SHB form, invitations and private storefront | 0/1 | In Progress | Pending actual revised evidence |
| 5. SHB durable records, archives and outbox | 0/1 | In Progress | Pending actual revised evidence |
| 6. Invitation scope, verified resources and staff MFA | 0/1 | In Progress; CURRENT DEVELOPMENT FOCUS; in progress — local invitation revocation verified with 543 tests/123 browser checks; remaining staff issuance/discount administration and actual qualifications stay open. | Pending actual revised evidence |
| 7. FPGA checkout, ASIC reviewed offers and scoped discounts | 1/4 | In Progress | Pending actual revised evidence |
| 8. Payment lifecycle and fault-injectable synthetic bank | 0/3 | In Progress | Pending actual revised evidence |
| 9. Selected-bank sandbox and complete reconciliation | 0/1 | Pending | Pending actual revised evidence |
| 10. Paid SHB orders, transaction notices and manual handoff | 0/6 | In Progress; | Pending actual revised evidence |
| 11. Private release delivery and protected-host qualification | 0/1 | Pending | Pending actual revised evidence |
| 12. Independent backup, restore and SHB reopening | 0/1 | In Progress | Pending actual revised evidence |
| 13. Thirty SHB acceptance cases and release verification | 0/1 | In Progress; | Pending actual revised evidence |
| 14. SHB handover and separately authorized activation | 0/1 | Pending | Pending actual revised evidence |

**Latest local verification:**526 tests and71 actual browser checks/two modes, identical350 backend/eight-script hashes; docs/build/shb-financial-handoff-2026-11-02.md. Actual qualification remains pending.

Resume 2026-10-30T13:52:15.032330+00:00: explicit resume lifts the context-pressure pause.07-03 proceeds inline using synthetic PostgreSQL fixtures; all live and protected-resource gates remain closed. HANDOFF.json consumed.

Explicit pause 2026-10-30T13:57:58.828345+00:00: user requested $gsd-pause-work during07-03. Partial model/service/test files remain uncommitted and unverified; migrations, routes/templates, SQL invariants, regression/browser/source checks remain. Only pause metadata is committed. See HANDOFF.json and the07 checkpoint.

Resume 2026-11-02T05:03:27.708886+00:00: explicit user $gsd-resume-work lifts the earlier pause. HANDOFF.json consumed after matching all six code files; planning changes in its snapshot were already committed. Continue07-03 inline with no external operation or commercial approval.

Context checkpoint 2026-11-02T05:37:52.615Z: verified FPGA checkout slice committed/pushed as a3936d512c822d608a086740fc64e346c0ec31e4. Exact context percentage is unavailable; new HANDOFF.json preserves the remaining paid-order/ASIC work. Completion counts remain unchanged.

Resume 2026-11-02T05:45:57.311365+00:00: explicit resume lifts the context checkpoint. Continue 07-03 inline, with actual company inputs and external/runtime qualifications still pending. HANDOFF.json consumed.

Verified paid-order continuation 2026-11-02T06:12:20.448928+00:00:429 tests and41 actual browser checks; identical321-backend/eight-script hashes. Paid-order/coupon/notice transaction, interrupted-finalization worker recovery and recent-MFA assigned staff purchase view are implemented. Evidence: docs/build/shb-paid-orders-2026-11-02.md. Safe cancellation/expiry and dated ASIC offers remain open. No parent SUMMARY/count change or live/independent qualification.

Verified safe-closure continuation 2026-11-02T06:30:46.556174+00:00:439 tests/47 actual browser checks and identical326 backend/eight-script hashes. Safe pre-dispatch cancellation/expiry now completes through archived intent, stopped attempt and atomic coupon release; uncertainty never frees a concession. Report: docs/build/shb-safe-closure-2026-11-02.md. No parent SUMMARY or count change.

Context checkpoint 2026-11-02T06:36:54.289Z: paid-order implementation07cb88d and safe-closure implementationa227344f8c4c3c3cc2e599eab730525561f2140a are committed/pushed.439 tests/47 browser checks remain verified; no uncommitted code or owned background job. Exact context percentage is unavailable; checkpoint uses the standing apparent-pressure authorization. Resume matching ASIC offers through HANDOFF.json. No parent completion count change.

Resume 2026-11-02T06:49:42.113651+00:00: explicit user $gsd-resume-work lifts the context checkpoint. Continue matching ASIC offers inline through the existing plan; real inputs/qualifications remain pending. HANDOFF.json consumed.

Resume 2026-11-02T07:42:05.168551+00:00: explicit user $gsd-resume-work lifts the context checkpoint. Continue07-04 pre-acceptance closing/reissue inline; no external action or count change. HANDOFF.json consumed.

Verified continuation 2026-11-02T08:03:47.200665+00:00:475 tests/65 actual browser checks and identical336-backend/eight-script source. Archived pre-acceptance ASIC withdrawal/final expiry and fresh-reviewed unchanged-scope reissue complete locally; report docs/build/shb-asic-closing-2026-11-02.md. Ordinary notices/linked material revisions/actual gates remain open; no parent count change.

Verified 2026-11-02T08:24:28.608322+00:00:487 tests/65 browser checks, identical340 backend/eight-script hashes;18 ordinary notice captures through the existing worker, no real email. Report docs/build/shb-ordinary-notices-2026-11-02.md. Linked material revisions/actual gates remain open.

Verified 2026-11-02T08:39:55.241769+00:00: linked material revisions complete locally;497 tests/71 browser checks,20 ordinary and4 support-team fake captures, identical344 backend/eight-script hashes. Report docs/build/shb-material-revisions-2026-11-02.md. Next shared recovery/replay coverage and actual qualifications remain open; no parent count change.

Context checkpoint 2026-11-02T08:40:33.289Z: verified material-revision implementation2fb096adabfffd81565790ce17b0328d444f3ae0 and prior closing/notices slices are pushed.497 tests/71 browser checks,20 ordinary captures. Exact percentage unavailable; standing apparent-pressure checkpoint. HANDOFF.json records recovery/replay as next; actual gates and parent completion remain open.

Resume 2026-11-02T08:55:38.002109+00:00: explicit user resume lifts the context checkpoint. Existing12-01 proceeds inline with synthetic fixtures and all actual qualification gates retained. HANDOFF.json consumed.

Verified12-01 continuation 2026-11-02T09:19:40.853429+00:00: read-only SHB assessment and14 recovery/replay cases pass within511 tests/71 current browser checks, identical346 backend/eight-script hashes. docs/build/shb-recovery-2026-11-02.md records exact scope/commands and false completeness/actual qualification flags. Actual independent runner/custody/post-backup/restore gates remain open; no parent SUMMARY/count change.

Continue 2026-11-02T09:25:58.429725+00:00: user authorized continued local work. Existing12-01 actual qualification awaits the unassigned off-host runner; continue unblocked existing10-05 inline. Require manual support-record review/financial linkage and staff communication while preserving all original records and false live-authority flags.

Verified10-05 continuation 2026-11-02T09:56:40.275115+00:00: archived manual SHB refund review, shared finance linkage and attributed support-team communication pass15 new cases within526 tests/71 customer browser checks, identical350 backend/eight-script hashes. Existing13 register maps all thirty acceptance criteria and explicit actual limits. docs/build/shb-financial-handoff-2026-11-02.md records commands/results. No parent SUMMARY/count change or actual money/policy/recovery qualification.

Explicit pause 2026-11-02T10:03:35.210Z: user invoked $gsd-pause-work. Implementationd9bb925f93dd5ee6f3c58d2aa469ec4ba12ee4d1 and status6081bc2 are pushed.526 tests/71 customer checks and all thirty local evidence mappings are retained. HANDOFF.json saves13-01 staff browser verification as the first unblocked local action; actual qualification gates and parent completion remain open.

Resume 2026-11-02T10:08:54.578045+00:00: explicit user $gsd-resume-work lifts the saved pause. Continue existing13-01 staff-browser verification inline; HANDOFF.json consumed. No external authority or completion-count change.

Verified13-01 continuation 2026-11-02T10:20:51.502698+00:00:113 actual local Chromium checks (71 customer/42 staff) and526 shared tests pass with identical350 backend/eight-script hashes. Existing native staff authentication, scope/CSRF denials, full synthetic refund and manual team handoff preserve original order/coupon/notice facts. Evidence: docs/build/shb-staff-browser-2026-11-02.md. The saved local browser action is complete; remaining actual prerequisites/runner are still pending. No parent SUMMARY/count change or external action.

Recorded sync 2026-11-02T10:22:45.995398+00:00: existing13-01 staff-browser verification f06869f12e4e458e282509f388b37884461e21f6 is pushed to origin/main;526 tests/113 local browser checks remain the exact verified scope. Current STATE.md / ROADMAP.md and actual gates remain operative.

Continuation 2026-11-02T10:49:10.181609+00:00: existing06-01 staff invitation revocation is unimplemented; continue inline with synthetic data. STATE.md / ROADMAP.md remain operative. No actual authority or parent completion change.

Verified06-01 continuation 2026-11-02T11:16:44.495073+00:00: protected invitation revocation and archived audit, 17 new cases within543 tests/123 browser checks; identical 357 backend/eight-script hashes. Exact commands/results/limits: docs/build/shb-invitation-revocation-2026-11-02.md. Existing purchase/coupon/review and original invitation clocks retained; remaining local issuance/discount administration and actual gates remain open. No parent SUMMARY/count change or actual external operation.
