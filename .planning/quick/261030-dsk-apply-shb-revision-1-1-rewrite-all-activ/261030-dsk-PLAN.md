---
phase: quick
plan: 261030-dsk
type: execute
autonomous: true
files_modified: [.planning, AGENTS.md, README.md, docs/decisions.md, scripts/check_purchase_plan.py]
---

# Apply Supporting Hours Bundle revision 1.1

Authority: the user's explicit 30 October instruction to read the complete new proposal, rewrite all planning and proceed. Source: `014-Shop-SHB-Proposal-Revision-2026-10-30.md`, SHA256 `ba801dff4adbfdcfa0f1e43cfe1f2d6963780476867da1b5e6f737230a472b5e`; all 1,017 lines, including Appendix A, read. This supersedes the prior product scope and continuation. Existing protected-service and external-operation authority is unchanged.

<tasks>
<task type="auto" id="1">
<name>Preserve and reconcile every planning artifact</name>
<files>.planning/**, docs/archive/2026-10-30-before-shb/**</files>
<action>Archive exact current bytes with a hash manifest. Rewrite each existing planning artifact for SHB revision 1.1 or replace dated history with an explicit archived-evidence pointer. Preserve phase/task IDs, locks/configuration semantics and source/evidence identities. Resolve scope conflicts using the direct user instruction: IP sales and automated time accounting are deferred; shared security/payment/recovery gates remain.</action>
<verify>python3 scripts/check_purchase_plan.py; python3 scripts/check_planning.py</verify>
<done>Every former planning file has an explicit disposition, recoverable original and current SHB precedence; synchronized canonical status and revised executable plans.</done>
</task>
<task type="auto" id="2">
<name>Rewrite requirements, execution order and instructions</name>
<files>.planning/PROJECT.md, .planning/REQUIREMENTS.md, .planning/ROADMAP.md, .planning/STATE.md, .planning/HANDOFF.md, .planning/state.json, .planning/phases/**, AGENTS.md, README.md, docs/decisions.md, scripts/check_purchase_plan.py</files>
<action>Map all SHB-01–30 criteria to retained phases. Plan the single product/two variants, minimum form, invitations and private delivery, discounts, reviewed ASIC offers, immutable per-order hours, financial finalization and transaction notifications. Keep one short pending commercial/external register. Remove dedicated deferred-ledger/IP tests from SHB launch requirements without deleting history/code or weakening shared controls.</action>
<verify>Planning inventory/source hashes; requirement/phase/task traceability; no stale active routing; focused planning-check regression tests.</verify>
<done>Existing planning structure is the new operative plan. Phase 3 product/forms is the next executable batch. No fabricated commercial or external approval.</done>
</task>
</tasks>

Continue immediately with revised 03-01 and 04-01 after this scope amendment; ordinary commits push to origin/main under standing authorization. Do not stop after planning. No .env, unknown cache, protected host/provider or real bank/mail actions are needed.
