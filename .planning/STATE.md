---
gsd_state_version: "1.0"
release: shb-1.1
current_phase: 6
current_phase_name: Invitation scope, verified resources and staff MFA
current_plan: 1
current_task: 1
status: paused
paused_at: "2026-11-02T12:16:14.551Z"
last_updated: "2026-11-02T12:16:14.551Z"
last_activity: 2026-11-02
state_head: 34c00196f5a9c0b3e43155927c2ee7ad561f800d
progress:
  total_phases: 14
  completed_phases: 1
  total_plans: 42
  completed_plans: 11
  percent: 7
---

# Project state — Supporting Hours Bundle revision 1.1

Current authority: [SHB revision 1.1](../014-Shop-SHB-Proposal-Revision-2026-10-30.md), SHA256 `ba801dff4adbfdcfa0f1e43cfe1f2d6963780476867da1b5e6f737230a472b5e`. STATE.md / ROADMAP.md remain operative.

**Current development focus:** 6 — Invitation scope, verified resources and staff MFA.

**Last fully completed phase:** 1 — documentary authority/reconciliation only.

**Current plan:** 06-01 — protected invitation issuance/reissue and scoped discount revocation verified locally; protected discount issuance/actual qualification open.

**Execution status:** paused — explicit user gsd-pause-work after pushed protected invitation issuance/reissue and discount revocation;583 tests/147 browser checks retained; discount issuance and actual qualification remain open.

**Next implementation task:** After explicit resume, inspect existing discount fixture issuance and invitation intent/scope patterns, then implement protected discount issuance with separate explicit synthetic customer/variant/percentage/use-limit/claim-period authority and a durable digest-only intent/one-time code response. Preserve original clocks and held concessions; invitation/revocation grants and entered contact never establish commercial authority.

## Verified local scope

Existing staff application now supports explicit immutable eligibility scopes/exact issuance grants, digest-only durable invitation intent, archive-before-atomic-publication, one-time bearer response and inactive-source reissue without renewing original clocks. Issuance4db2586 is ordinarily pushed. Current epoch/recent MFA/CSRF/exact scope, SQL immutable/atomic guards, reset/selected restore and retained recovery evidence are covered. The invitation component previously passed565 tests/137 browser checks; exact earlier records remain attributed in docs/build/shb-invitation-issuance-2026-11-02.md.

Scoped discount revocation adds exact code assignments/native/JSON forms and one archived immutable attributed audit before atomic revocation. It stops new claims while preserving existing request/offer/order price, reserved capacity and original claim deadline. A reserved ASIC offer still accepts/pays once for50 hours at its original synthetic concession. Uncertain archive publication after rollback returns503 rather than overwriting/retrying fresh bytes. Current MFA/grants are rechecked after I/O; reset/selected restore clear mutable grants but retain audits. No raw code/verifier, contact prefill, replacement, mail, commercial approval or time mutation.

Seventeen discount-administration cases plus new staff navigation pass. Final583 tests pass with none failed/skipped:240 SHB,95 access/recovery,104 payment,30 staff,24 worker/statement-mail,75 shared transaction/archive, nine source/catalog and six actual network-isolated adapters. Django check/migrations0027/0028/drift and planning activity3 tests pass. Actual Chromium151/Node24.15 passes147 checks:71 customer/76 staff, JS/no-JS/320px. Both native discount revocations retain original claim clocks; two invitation replacements show bearers once and hide them on retry. Original customer-session denial, FPGA30-hour/ASIC50-hour purchases, unpaid75-hour revisions/refunds/manual handoffs and coupon/order/notice facts are intact.

Final regression12bf40be73b635be6c478375030776b711118323f4f3c9ec5db43a2695e35264.json, browserafbf88024a843a4444b21f055e5f73567bebb5d52941c3c5275628a838601ae6.json and focused27 recorde82a8d31e4cee66b558548a10df7ca26446f94e5447b8e599f3ed06cb1595324.json bind identical372 backend/eight-script hashes. Full commands, initial fault-case errors, final behavior and limits: docs/build/shb-discount-revocation-2026-11-02.md. Browser evidence .scratch/shb-checkout-browser-aryd5bay. All owned contexts completed; no async job. Private9-file Astro release remains unchanged.

## Remaining work and gates

Protected discount issuance remains local follow-up work; current code issuance helpers are fixture-only. New codes need separate explicit customer/variant/percentage/use-limit/claim-period scope, digest-only durable intent, one-time raw response and archived attributed authority. Reuse invitation intent patterns without promoting invitation eligibility or revoke grants into commercial authority. Revocation is now verified under the synthetic gate. Actual company inputs arrive later through docs/decisions.md; no repeated request.

Normal pinned Nix/source/runtime/native/licence/OCI/CI and actual commercial/provider/refund/tax/mail/host/ingress/database/human/independent custody/post-backup/transport/restore/complete-loss qualification remain open. The authorized independent off-host runner is unassigned. The saved missing-dependency Nix failure was inspected, not rerun or weakened. No parent SUMMARY/FULL_PASS/count change: 11/42 summary records and1/14 documentary phases.

No .env, real credentials, actual bank/mail/storage/protected-host/DNS/TLS operation, production/bank-sandbox connection or paid provision. Ordinary sandbox bwrap traversal remains unavailable; narrowly justified escalation was used for authorized local work only. Unrelated http_cache.sqlite stays untouched. Ordinary non-force origin/main sync remains authorized. No subagent request; execute inline.

## Session Continuity

Last session: 2026-11-02T12:16:14.551Z
Stopped at: Explicit user $gsd-pause-work after verified/pushed invitation issuance4db2586 and discount revocation34c0019. All implementation is committed and verified; no current local test failure or owned process/job.
Resume file: HANDOFF.json and phases/06-invitation-scope-and-staff-mfa/.continue-here.md.

Next: After explicit resume, inspect existing discount fixture issuance and invitation intent/scope patterns, then implement protected discount issuance with separate explicit synthetic customer/variant/percentage/use-limit/claim-period authority and a durable digest-only intent/one-time code response. Preserve original clocks and held concessions; invitation/revocation grants and entered contact never establish commercial authority.

An apparent-context-pressure checkpoint was being prepared when the user explicitly requested pause. Exact usage percentage is unavailable; no measured90% or automatic-monitoring claim. Resume lifts this explicit pause. Continue inline with no new subagent request, no repeated company-input request and actual gates unchanged.
