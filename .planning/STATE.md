---
gsd_state_version: "1.0"
release: shb-1.1
current_phase: 6
current_phase_name: Invitation scope, verified resources and staff MFA
current_plan: 1
current_task: 1
status: paused
paused_at: "2026-11-02T11:24:23.042Z"
last_updated: "2026-11-02T11:24:23.042Z"
last_activity: 2026-11-02
state_head: 175c3ce5f958c2a04229568e1863486c3d88a247
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

**Current plan:** 06-01 — protected staff invitation revocation and recoverable audit verified locally; remaining administration/actual qualification open.

**Execution status:** paused — standing context-pressure checkpoint after verified/pushed invitation revocation; 543 tests/123 browser checks retained; remaining local issuance/discount administration and actual gates remain open.

**Next implementation task:** After explicit resume, inspect existing invitation/discount fixture issuance and staff/operator ownership patterns, then implement protected invitation issuance/reissue with explicit eligibility/issuance scope and safe one-time bearer handling; continue scoped discount administration afterward. Do not treat the revocation assignment or form-entered contact as issuing/commercial authority.

## Verified local scope

Existing 06-01 now provides assigned staff invitation reads and native/JSON revocation through the existing staff application. Recent MFA, exact invitation grants, current recovery epoch and CSRF are required. Staff receive no bearer/digest, private history or contact prefill. Bounded reasons reject malformed/NUL input before archive/database work. An immutable attributed audit is archived before revocation; current MFA/grant/epoch are rechecked after I/O. SQL guards bind audit and timestamp atomically. Exact retries retain one event; archive failure keeps the invitation active.

The 17 invitation-administration tests cover access/GET/privacy, scope/cursor/MFA/CSRF, native forms, malformed fields, archive failure, grant/MFA changes during I/O, SQL immutable/atomic guards, concurrency, operator/reset, legacy revocation and recovery holds. Staff resets/selected restores clear the new mutable assignment, retaining history. Recovery validates retained audit bytes and original clocks; completeness/retry/actual reopening flags remain false. No automatic replacement, mail, price authority, order/coupon/time mutation or customer panel.

Final evidence: 543 tests, none failed/skipped (200 SHB, 95 access/recovery, 104 payment, 30 staff, 24 worker/statement-mail, 75 shared transactions/archive, nine source/catalog, six actual network-isolated adapters). Django check/migrations0023/0024/drift and planning checks pass. Actual Chromium151/Node24.15 passes 123 checks: 71 customer/52 staff, both JS/no-JS/320px. Two new invitations are revoked through actual native forms; pre-existing customer sessions then deny the next protected request. Existing 30-hour FPGA/50-hour ASIC purchases, unpaid75-hour revisions, refunds and manual handoffs preserve all original order/coupon/notice facts.

Both final records bind identical 357 backend/eight-script hashes. Browser 88fba02799ceb5de1f3650598871aae724adf8a99a904da68da54203b6260c32.json and regression 36d8f0f157241d73cffee09cfee8e1611c56ae4d75a0b7d63e977b786f9bb9e6.json are in docs/evidence/shb/retained-tests. Full commands/RED/intermediate/final results and limits: docs/build/shb-invitation-revocation-2026-11-02.md. Current private browser evidence: .scratch/shb-checkout-browser-ss83c58x. The private9-file Astro release remains unchanged. All owned contexts completed; no async external job.

## Remaining work and gates

Protected staff invitation issuance/reissue and discount administration are still local follow-up work; only existing fixture helpers issue them today. Reuse existing staff/eligibility/secret-capture patterns. Do not turn a form-entered company/contact or the revocation assignment into new issuance/commercial authority. New invitations are deliberate separately attributed six-month issues, never renewal of original clocks. Actual company inputs arrive later through docs/decisions.md; no repeated request.

Normal pinned Nix/source/runtime/native/licence/OCI/CI and actual commercial/provider/refund/tax/mail/host/ingress/database/human/independent custody/post-backup/transport/restore/complete-loss qualification remain open. The authorized independent off-host runner is unassigned. The saved missing-dependency Nix failure was inspected, not rerun or weakened. No parent SUMMARY/FULL_PASS/count change: 11/42 summary records and1/14 documentary phases.

No .env, real credentials, actual bank/mail/storage/protected-host/DNS/TLS operation, production/bank-sandbox connection or paid provision. Ordinary sandbox bwrap traversal remains unavailable; narrowly justified escalation was used for authorized local work only. Unrelated http_cache.sqlite stays untouched. Ordinary non-force origin/main sync remains authorized. No subagent request; execute inline.

## Session Continuity

Last session: 2026-11-02T11:24:23.042Z
Stopped at: Standing conditional pause for apparent context pressure at verified/pushed implementation 175c3ce5f958c2a04229568e1863486c3d88a247. No unfinished code, current test failure or owned job. Exact usage percentage is unavailable; no measured90% or monitoring claim.
Resume file: HANDOFF.json and phases/06-invitation-scope-and-staff-mfa/.continue-here.md.

Next: After explicit resume, inspect existing invitation/discount fixture issuance and staff/operator ownership patterns, then implement protected invitation issuance/reissue with explicit eligibility/issuance scope and safe one-time bearer handling; continue scoped discount administration afterward. Do not treat the revocation assignment or form-entered contact as issuing/commercial authority.

The user authorized apparent-pressure checkpoints when no exact percentage is supplied. Resume lifts this pause; continue inline with no new subagent request and no repeated company-input request. Existing actual gates remain closed.
