---
phase: 07-multi-line-cart-quotations-business-checkout-and-acceptance
plan: "04"
status: partial
release: shb-1.1
---

# Assigned SHB ASIC triage and safe decline

Current authority: [SHB revision1.1](../../../014-Shop-SHB-Proposal-Revision-2026-10-30.md). STATE.md / ROADMAP.md remain operative.

Implemented: existing assigned quotation screen now shows the exact private SHB capture only with its explicit request-revision business-scope grant and current recent MFA/epoch/credential. Existing local_staff grant-business supports that scope. Clarification retains the coupon after claim/invitation expiry; technical readiness is not commercial approval. Pre-offer decline records an immutable attributed reason/prior state and releases only the matching unused reservation atomically. Concurrent decisions, retries, SQL provenance/rewrites, cross-request releases and offer/payment-state denial are covered. Closed-request resubmission shows the actual released state.

Evidence: [review report](../../../docs/build/shb-review-2026-10-30.md). Final complete shared test result is recorded there; customer Chromium33 checks/two modes and306-file/twelve-import exact source pass. An actual native-document/layout timing failure was isolated and the harness now waits for completion without changing the320px assertion. Local/synthetic only; no bank/mail/host effects or staff-browser/human qualification is claimed.

Remaining: explicit withdrawal, matching approved dated offer/offer revision/expiry/reissue and customer acceptance;07-03 FPGA checkout and shared08/10 payment/coupon consumption/once-only order/transaction notifications. SQL reservation consumption and payment/offer closure remain unavailable. No full parent SUMMARY, completed requirement or completion-count increase.
