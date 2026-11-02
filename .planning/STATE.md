---
gsd_state_version: "1.0"
release: shb-1.1
current_phase: 6
current_phase_name: Invitation scope, verified resources and staff MFA
current_plan: 1
current_task: 1
status: in_progress
last_updated: "2026-11-02T11:55:26.231440+00:00"
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

**Current plan:** 06-01 — protected invitation issuance/reissue and revocation verified locally; scoped discount administration/actual qualification open.

**Execution status:** in progress — protected issuance/reissue verified with565 tests/137 browser checks and identical source hashes; continue scoped discount administration; actual qualification remains open.

**Next implementation task:** Continue scoped discount administration inline: add exact-scope recent-MFA issue/revoke controls with attributed archive, preserving existing accepted/reserved concessions and independent clocks. Inspect existing discount helpers and grant/reset patterns; keep real commercial authority closed.

## Verified local scope

Protected staff issuance/reissue extends the existing application with immutable customer/eligibility/mode scopes and separate exact issuance grants. Native/JSON POST records one digest-only intent before archive I/O, then publishes the exact invitation atomically after current epoch/MFA/grant/eligibility rechecks. Only the creating response can show the32-random-byte bearer; GET and retries expose no bearer/digest. Interrupted/archive-failed publication retains the same original clocks/digest, with no active invitation until commit. Replacement requires an inactive exactly matching source and retains its original clocks/revocation. Issuing staff receive an exact revocation assignment for the new invitation. Reset/selected restore clear issue grants while retaining historical audits.

Twenty-one issuance cases plus18 revocation cases pass, including concurrency, same-key commands, native CSRF, malformed input, archive/I/O authority faults, SQL immutable scope/publication, interrupted and omitted publication, selected restore and missing archive holds. No contact/company field establishes eligibility, no new commercial authority/mail, and no order/coupon/time mutation. Prior revocation behavior is retained.

Final565 tests pass with none failed/skipped:222 SHB,95 access/recovery,104 payment,30 staff,24 worker/statement-mail,75 shared transaction/archive, nine source/catalog and six actual network-isolated adapters. Django check/migrations0025/0026/drift pass. Actual Chromium151/Node24.15 passes137 checks:71 customer/66 staff, JS/no-JS/320px. Two native invitation replacements show a bearer once and hide it on retry; original customer sessions remain denied. Existing FPGA30-hour/ASIC50-hour purchases and unpaid75-hour revisions/refunds/manual handoffs retain original facts.

Final browser11620cba8b55f8c1870147621b01ac8ab30cd31957c5e2a0a57043b6b9541a88.json and regression2028fdfde6332f22a78c601cf8215db7b642376763fca84fef10bb5048c0b29d.json bind identical365 backend/eight-script hashes. Focused48 record44338ca135f22f58d11d2a904a28a188bb80a88414646f37bef0a987860f4d96.json shares those bytes. Reports, intermediate failures and full commands: docs/build/shb-invitation-issuance-2026-11-02.md. Browser evidence: .scratch/shb-checkout-browser-rqbnhvgi. All owned contexts completed; no async job. The private9-file Astro release is unchanged.

## Remaining work and gates

Protected scoped discount issue/revoke administration remains local follow-up work; current discount helper issuance is fixture-only. Reuse exact grants and archive-before-state controls, preserving every held/accepted concession. Do not turn invitation eligibility or revocation assignments into discount/commercial authority. Invitation issuance/reissue is now verified only under the synthetic gate. Actual company inputs arrive later through docs/decisions.md; no repeated request.

Normal pinned Nix/source/runtime/native/licence/OCI/CI and actual commercial/provider/refund/tax/mail/host/ingress/database/human/independent custody/post-backup/transport/restore/complete-loss qualification remain open. The authorized independent off-host runner is unassigned. The saved missing-dependency Nix failure was inspected, not rerun or weakened. No parent SUMMARY/FULL_PASS/count change: 11/42 summary records and1/14 documentary phases.

No .env, real credentials, actual bank/mail/storage/protected-host/DNS/TLS operation, production/bank-sandbox connection or paid provision. Ordinary sandbox bwrap traversal remains unavailable; narrowly justified escalation was used for authorized local work only. Unrelated http_cache.sqlite stays untouched. Ordinary non-force origin/main sync remains authorized. No subagent request; execute inline.

## Session Continuity

Last session: 2026-11-02T11:55:26.231440+00:00
Stopped at: Verified565 tests/137 browser checks; preparing issuance implementation commit, then continue scoped discount administration inline. No owned process/job.
Resume file: HANDOFF.md

Next: Continue scoped discount administration inline: add exact-scope recent-MFA issue/revoke controls with attributed archive, preserving existing accepted/reserved concessions and independent clocks. Inspect existing discount helpers and grant/reset patterns; keep real commercial authority closed.

User authorizes local work and ordinary non-force origin/main pushes. Actual gates remain closed. Exact context percentage is unavailable.
