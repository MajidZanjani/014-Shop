---
phase: 07-multi-line-cart-quotations-business-checkout-and-acceptance
plan: "02"
status: partial
release: shb-1.1
---

# Scoped SHB coupons — partial local implementation

Current authority: [SHB revision1.1](../../../014-Shop-SHB-Proposal-Revision-2026-10-30.md). STATE.md / ROADMAP.md remain operative.

Implemented: protected Apply/Remove; authoritative integer-money percentage preview without changing hours; digest-only random codes; customer/variant/window/revocation checks; durable customer-wide guessing budget; atomic request/quotation/discount capture; per-code database slots and immutable snapshots; original request retry after claim expiry/revocation/rate change. Raw codes never enter request/database snapshots. No automatic held-reservation expiry.

Executed evidence: [coupon report](../../../docs/build/shb-coupons-2026-10-30.md),250 focused/shared tests including16 coupon tests and direct PostgreSQL races,33 real Chromium checks in both modes,17 loopback demonstration checks and300-file/ten-import exact inert source pass. Source/rates/code policy are explicitly synthetic; no live adoption/effects.

Remaining07-02: reservation consumption/release linked atomically to the matching accepted verified order or safely closed request/offer/attempt; preserve uncertain payments; test process-loss/reconciliation outcomes with07-03/04 and08/10. FPGA payable checkout, assigned ASIC dated matching offers/acceptance, one active revision and staff transaction notifications remain open. No full parent SUMMARY, completed requirement or completion-count increase.
