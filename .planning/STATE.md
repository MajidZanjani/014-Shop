---
gsd_state_version: "1.0"
release: shb-1.1
current_phase: 6
current_phase_name: Invitation scope, verified resources and staff MFA
current_plan: 1
current_task: 1
status: active
last_updated: "2026-11-03T05:35:00.000Z"
last_activity: 2026-11-03
state_head: dc902cbddd0ec4f46b4d6989156a39691e854e14
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

**Current plan:** 06-01 — protected invitation issuance/reissue, scoped discount revocation and separate protected discount issuance verified locally; actual qualification remains open.

**Execution status:** active — SHB-07 FPGA top-up assertion committed (dc902cb); shared retained lane now passes 608 total (265 SHB) in 279.374s; browser lane remains at 161 (unchanged).

**Next implementation task:** Local 06-01 slice is fully verified. Continue with the next planned 06 work (or begin 07 continuation) under the existing synthetic-fixture boundaries. Normal pinned Nix/source/runtime/native/licence/OCI/CI and actual commercial/provider/refund/tax/mail/host/ingress/database/human/independent custody/post-backup/transport/restore/complete-loss qualification remain open; the authorized independent off-host runner is unassigned.

## Verified local scope

Existing staff application now supports explicit immutable eligibility scopes/exact issuance grants, digest-only durable invitation intent, archive-before-atomic-publication, one-time bearer response and inactive-source reissue without renewing original clocks. Current epoch/recent MFA/CSRF/exact scope, SQL immutable/atomic guards, reset/selected restore and retained recovery evidence are covered. Exact earlier records remain attributed in docs/build/shb-invitation-issuance-2026-11-02.md.

Scoped discount revocation adds exact code assignments/native/JSON forms and one archived immutable attributed audit before atomic revocation. It stops new claims while preserving existing request/offer/order price, reserved capacity and original claim deadline. A reserved ASIC offer still accepts/pays once for50 hours at its original synthetic concession. Uncertain archive publication after rollback returns503 rather than overwriting/retrying fresh bytes. Current MFA/grants are rechecked after I/O; reset/selected restore clear mutable grants but retain audits. No raw code/verifier, contact prefill, replacement, mail, commercial approval or time mutation. Full detail in docs/build/shb-discount-revocation-2026-11-02.md.

Protected discount issuance now registers synthetic commercial authority (customer/variant/percentage/use-limit/claim-period) as an immutable scope and binds a separate per-staff issuance grant distinct from invitation eligibility and revoke grants. The service archives an attributed digest-only intent before publication, atomically publishes exactly one DiscountCode with the matching scope and clocks, returns the raw code once in the issuing response and preserves the same prepared intent on retries. Archive failures retain the intent and refuse to reveal a code; published archive bytes after rollback remain503-held. SQL requires current exact issuance grant, append-only publication binding and matching DiscountCode fields in one commit. Operator/reset/selected restore clear mutable issuance grants; recovery validates original clocks and holds release on missing bytes. docs/build/shb-discount-issuance-2026-11-02.md.

Final608 tests pass with none failed/skipped:265 SHB,95 access/recovery,104 payment,30 staff,24 worker/statement-mail,75 shared transaction/archive, nine source/catalog and six actual network-isolated adapters. Django check,0029/0030 and migration drift pass. Actual Chromium151.0.7922.173/Node24.15.0 passes161 checks:71 customer/90 staff, JS/no-JS/320px with no regression. Original customer-session denial, FPGA30-hour/ASIC50-hour purchases, unpaid75-hour revisions/refunds/manual handoffs and coupon/order/notice/revocation facts are intact.

Final regression6272c2fa05205d30bbe9d9bcedb520005791ce43c136300b532424ae16c76c21.json (shared 607) and browser9a729dd1bbee341bd48a366d64a901beefedac6ccf2c8063da1561a6bca3276e.json bind the current retained source identity; prior shared record48448c3c and focused40-test record fe29b38a93d85070dc0c795a2b0260c7fb4d07656ea44ca237f7463bb5fbb26b.json are retained as the audit trail of the lifecycle/mirror addition. Full commands, initial fault-case errors, final behavior and limits: docs/build/shb-discount-issuance-2026-11-02.md. All owned contexts completed; no async job. Private9-file Astro release remains unchanged.

## Remaining work and gates

Normal pinned Nix/source/runtime/native/licence/OCI/CI and actual commercial/provider/refund/tax/mail/host/ingress/database/human/independent custody/post-backup/transport/restore/complete-loss qualification remain open. The authorized independent off-host runner is unassigned. The saved missing-dependency Nix failure was inspected, not rerun or weakened. No parent SUMMARY/FULL_PASS/count change: 11/42 summary records and1/14 documentary phases.

No .env, real credentials, actual bank/mail/storage/protected-host/DNS/TLS operation, production/bank-sandbox connection or paid provision. Ordinary sandbox bwrap traversal remains unavailable; narrowly justified escalation was used for authorized local work only. Unrelated http_cache.sqlite stays untouched. Ordinary non-force origin/main sync remains authorized. No subagent request; execute inline.

## Session Continuity

Last session: 2026-11-02T12:16:14.551Z (paused) → 2026-11-02T12:35:00+00:00 (resumed) → 2026-11-02T13:05:00+00:00 (verified continuation)
Stopped at: Explicit user $gsd-pause-work after verified/pushed invitation issuance4db2586 and discount revocation34c0019. All implementation is committed and verified; no current local test failure or owned process/job.
Resumed at: 2026-11-02T12:35:00+00:00 — explicit user $gsd-resume-work. HANDOFF.json and phases/06-invitation-scope-and-staff-mfa/.continue-here.md consumed after confirming referenced commits (4db2586,34c0019,bb3d603) are pushed and the working tree carries no owned implementation changes.
Verified continuation 2026-11-02T13:05:00+00:00: protected scoped discount issuance implemented and pushed with RED705c2de and GREEN e5ec3dd.605 tests/147 browser checks initially; docs follow-up2efae9c and browser follow-up a7072ff/b04b955 raised browser coverage to161 checks (71 customer/90 staff) with no backend change.

Explicit pause 2026-11-02T13:42:27.791Z: user $gsd-pause-work during focused lifecycle-test addition. Two uncommitted follow-up tests pass focused (40 tests across discount_issuance+discount_admin, evidence fe29b38a…) but the shared regression rerun was interrupted mid-run. See HANDOFF.json and phases/06-invitation-scope-and-staff-mfa/.continue-here.md for the exact resume plan. No owned process/job, async manifest or new completion count; exact context percentage unavailable.

Resume 2026-11-03T00:00:00+00:00: explicit user $gsd-resume-work lifts the saved pause. Working tree matches HANDOFF.json snapshot exactly (two modified test files + fe29b38a evidence + unrelated http_cache.sqlite). HANDOFF.json and phases/06-invitation-scope-and-staff-mfa/.continue-here.md are the authority; proceeding inline to commit the two tests, rerun the shared regression lane and bump counts. No subagent, no external action, no completion-count change until counts verified.

Verified continuation 2026-11-03T05:11:00+00:00: the two uncommitted lifecycle/mirror tests are committed as b7cd2e9 (`test(06-01): close discount issuance->revocation lifecycle and mirror nav`,25 insertions across backend/shop/shb/discount_issuance_tests.py and discount_admin_tests.py). Shared retained regression passes 607 total in 262.864s: 264 SHB,95 access/recovery,104 payment,30 staff,24 worker/statement-mail,75 shared transaction/archive, nine source/catalog and six actual network-isolated adapters. Django check,0029/0030 and migration drift pass; new evidence docs/evidence/shb/retained-tests/6272c2fa05205d30bbe9d9bcedb520005791ce43c136300b532424ae16c76c21.json. Browser lane is unchanged at 161 checks (9a729dd1 remains current). Focused 40-test record fe29b38a is retained as the audit trail of the two new tests passing in isolation. HANDOFF.json and the 06 .continue-here.md are consumed. No parent SUMMARY/count change (11/42 and 1/14); actual gates/off-host runner unchanged.

Verified Phase 10 continuation 2026-11-03T05:35:00+00:00: explicit SHB-07 FPGA top-up assertion committed as dc902cb (`test(10-01): assert SHB-07 FPGA top-up records independent per-order hours`,35 insertions in backend/shop/shb/paid_order_tests.py). The same customer receives a new invitation and places a second eligible FPGA purchase; both PaidOrders are independent (30h/20h, distinct order_reference, independent purchase-notice delivery, support_tracking='manual-outside-shop'). No SyntheticFulfilment or SyntheticSupportEvent is produced -- no automated time credit, no online balance update. Shared retained regression passes 608 total in 279.374s (265 SHB, +1 vs 607); new evidence docs/evidence/shb/retained-tests/f5ae15048343dd4f4d6aa355379c8c83fcdf30caf1f34237f74323735117311d.json. Focused 1-test audit record ad265762332aeda016aa3dc77e5b5fec5f930456fbabf68acd6c719f5ccbfbc5.json retained. Browser lane unchanged at 161. The SHB-07 invariant was already implicit in the checkout/paid-order path; this commit makes it explicit coverage. No parent SUMMARY/count change (11/42 and 1/14); actual gates/off-host runner unchanged. Current development focus remains Phase 6; Phase 10's 10-01 slice is advanced inline as a focused test addition.
