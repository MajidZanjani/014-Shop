---
phase: quick
plan: 261030-dsk
release: shb-1.1
status: complete
---

# SHB revision 1.1 scope amendment

Read the complete 1,017-line revision, including Appendix A. The source SHA256 is `ba801dff4adbfdcfa0f1e43cfe1f2d6963780476867da1b5e6f737230a472b5e`. Direct user instruction supersedes previous conflicting product scope and continuation; external/protected-operation authority is unchanged.

Rewrote all former planning instructions into SHB current scope or explicit archived-evidence dispositions, preserving stable phases/task IDs. Exact 342 prior planning/instruction files are retained with byte length and SHA256 under `docs/archive/2026-10-30-before-shb/manifest.json`. Consumed former pause artifacts. The untracked GSD process lock is runtime state and is intentionally untouched. All 30 SHB criteria and 89 previous requirement dispositions are mapped; IP-only/time-accounting requirements are deferred, shared security/payment/recovery/runtime gates retained. Updated AGENTS.md, README.md, docs/decisions.md and prior demonstration guidance.

Executed:

```sh
python3 scripts/check_purchase_plan.py --refresh-inventory
python3 scripts/check_planning.py
python3 -m unittest discover -s tests -p 'test_planning_activity.py'
python3 -m unittest discover -s tests -p 'test_purchase_plan_inventory.py'
```

Observed before this summary was added: `PURCHASE_PLAN_PASS release=shb-1.1 requirements=30 prior_dispositions=89 phases=14 planning_files=354 archived_originals=342 immutable_sources=5`; `PLANNING_PASS phases=14 development_focus=3 last_completed_phase=1 completed_phases=1 plans=11/42`; six focused tests pass. Inventory is refreshed again after close-out. New regression controls reject archive corruption, unchanged old active planning, path escape and duplicate original records. The first readback detected a README archive/index filename collision; exact original Git bytes matching the manifest were restored and the index renamed before all final checks passed. The one-time writer refuses any replay over later work.

This completes the scope amendment, not the SHB implementation or live qualification. Continue immediately with 03-01 catalog/forms and 04-01 invitations/private delivery. Rates/policies/ASIC adoption, bank/mail, actual runtime/recovery/host/legal/CI/independent gates remain pending in the single support-offer/external-input record. No real credentials or provider/host action. Unrelated http_cache.sqlite remains untouched.
