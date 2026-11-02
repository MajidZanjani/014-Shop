---
gsd_state_version: "1.0"
release: shb-1.1
current_phase: 7
current_phase_name: FPGA checkout, ASIC reviewed offers and scoped discounts
current_plan: 3
current_task: 1
status: in_progress
last_updated: "2026-11-02T06:12:20.448928+00:00"
last_activity: 2026-11-02
state_head: a3936d512c822d608a086740fc64e346c0ec31e4
progress:
  total_phases: 14
  completed_phases: 1
  total_plans: 42
  completed_plans: 11
  percent: 7
---

# Project state — Supporting Hours Bundle revision1.1

Current authority: [SHB revision1.1](../014-Shop-SHB-Proposal-Revision-2026-10-30.md), SHA256 `ba801dff4adbfdcfa0f1e43cfe1f2d6963780476867da1b5e6f737230a472b5e`. STATE.md / ROADMAP.md remain operative.

**Current development focus:** 7 — FPGA checkout, ASIC reviewed offers and scoped discounts.

**Last fully completed phase:** 1 — documentary authority/reconciliation only.

**Current plan:** 07-03 — per-order FPGA finalization, consumed coupons, assigned staff visibility and durable purchase notices verified locally; safe closure and matching ASIC offers remain open.

**Execution status:** in progress — verified 429 tests and41 browser checks; continuing safe payment-linked cancellation/expiry and matching ASIC offers; normal Nix/external qualification pending.

**Next implementation task:** Implement archived safe pre-dispatch FPGA cancellation/expiry and coupon release without reopening payment; then continue matching dated ASIC offers and request/customer notices.

## Verified local scope

Invitation-scoped FPGA review/acceptance/captured fake payment now produces one archived paid order, atomically consumes its scoped coupon and queues an ordinary purchase notice. The existing leased worker recovers interrupted finalization after invitation expiry and captures the stable fake notice. Staff require recent MFA/current epoch plus exact order assignment. Reset/recovery clears new order grants. Each order retains variant, bundle size, quantity and purchased hours only; no IP/time fulfilment or support-time automation is connected.

Current unchanged-source evidence:429 passing tests (86 SHB,95 access/recovery,104 payment,30 staff review/navigation,24 local worker/statement-mail,75 preserved transactions/archive,9 source/catalog,6 actual unshare--net adapters) and41 actual Chromium151/Node24.15 browser checks/two modes/320px. Test and browser records bind identical321 backend files/eight scripts. Report and full commands: docs/build/shb-paid-orders-2026-11-02.md. The source/runtime/tool distinction remains explicit; normal pinned Nix source/environment qualification is unavailable.

No parent SUMMARY, FULL_PASS or count change:11/42 retained summary records and1/14 documentary phases. Safe pre-dispatch cancellation/expiry and payment-linked coupon release, dated matching ASIC offers, withdrawal/reissue and remaining ordinary request/customer notices remain open.

## Current artifacts and external inputs

Private release `.scratch/shb-private-resume-t2p3r5cc/release`, manifest `ef2d68408ac264a2da888af45ec167242c1a21680990d66a772bd761b86941f3`. Empty browser screenshots `.scratch/shb-checkout-browser-zuxei3yt`. Exact evidence records and failed-control history are linked in the report. No running verification processes remain after the completed owned test contexts.

One actual-input register: docs/decisions.md. Company inputs arrive later; no repeat request. Actual rates/policies/seller/tax/eligibility/reviewer/bank/mail and normal Nix/runtime/native/licence/OCI/CI/recovery/human/host/ingress evidence remain pending. Independent off-host runner remains unassigned. No .env, actual external action, protected change or paid provision. http_cache.sqlite untouched. Ordinary origin/main push remains authorized.

## Session Continuity

Explicit resume restored and consumed HANDOFF.json. Continue07-03 inline through gsd-execute-phase. Verified paid-order implementation is being committed; next is archived safe cancellation/expiry and coupon release, then dated ASIC offers. No exact context percentage is supplied and no threshold is claimed.
