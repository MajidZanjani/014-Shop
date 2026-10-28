---
phase: quick
plan: 261028-cgz
type: execute
wave: 1
depends_on: []
autonomous: true
requirements: [OPS-02, UAT-03]
files_modified:
  - backend/shop/core/checks.py
  - backend/shop/config/base.py
  - backend/shop/core/tests.py
  - backend/shop/access/startup.py
  - backend/shop/access/recovery.py
  - backend/shop/access/effects.py
  - backend/shop/access/startup_tests.py
  - scripts/check_backend.py
  - docs/local-recovery.md
  - docs/local-development.md
  - ops/config/local.example
  - ops/config/synthetic.example
threat_model:
  - Restored unheld or missing access epoch must not admit old sessions, login, workers, bank mutations or captured mail before explicit cleanup.
  - A restore identity comes from process configuration outside the restored database, is fresh for each local restore, and is shared by all cooperating processes.
  - Earlier recovery history, wrong identities, partial cleanup or unfinished admitted calls cannot reopen the selected restore.
  - Read-only typed bank lookup remains usable; no adapter I/O runs under recovery locks, no uncertain operation becomes retryable.
  - This fake-only fixture boundary cannot authorize actual restore, post-point reconciliation, MFA recovery, external egress or production reopening.
---

<objective>
Implement an explicitly selected local restore startup fence independently of restored database hold state. Preserve normal isolated development behavior and all actual qualification gates.
</objective>

<design_critique>
The database hold alone can be restored as unheld. Settings import must validate a fresh external UUID4 without opening or mutating the database. A selected SHOP_LOCAL_RESTORE_ID blocks access and new effect admission until immutable local history contains its quarantine and matching synthetic release, and the current epoch is unheld. Missing epoch is closed. Release continues to require the current hold and no unfinished admissions. A completed startup sequence remains recognized across cooperating process restarts and later ordinary quarantine/release cycles; a new restore identity closes again. No automatic hold/release at Django import and no production command are added. This requires explicitly selecting restore configuration before connecting app/effect processes; omission, token reuse, traffic/egress isolation and actual reconciliation remain unqualified deployment obligations. No external API integration is added.
</design_critique>

<tasks>
<task type="auto">
  <name>Reproduce restored unheld access and implement configuration plus shared admission gate</name>
  <files>backend/shop/core/checks.py, backend/shop/config/base.py, backend/shop/core/tests.py, backend/shop/access/startup.py, backend/shop/access/recovery.py, backend/shop/access/effects.py, backend/shop/access/startup_tests.py</files>
  <action>First retain a real PostgreSQL failure using a fresh external restore marker with an unheld epoch and existing session. Validate only canonical UUID4 in local/synthetic modes; reject blank/malformed or production-shaped use without echoing values. Apply shared startup readiness to customer/staff authority, deliberate login stamping and serialized effect admission. Report startup-pending separately from persisted database quarantine/drain. Keep fixture quarantine/release and read-only reconciliation usable.</action>
  <verify>Run new PostgreSQL startup tests and configuration subprocess tests through the existing pinned frozen-environment/prepared_database harness; verify absent epoch has no automatic initialization, held old sessions and login/worker/bank/capture paths deny, and lookup causes no admission/mutation.</verify>
  <done>Pre-fix exposure is recorded; selected restore mode fails closed before explicit quarantine/release while existing local mode and read-only lookup retain their behavior.</done>
</task>
<task type="auto">
  <name>Prove restore identity, release ordering and restart behavior without changing bounds</name>
  <files>backend/shop/access/startup_tests.py, scripts/check_backend.py</files>
  <action>Exercise a fresh identity against older completed history, wrong reset release, unfinished calls, a completed matching sequence in separate customer/staff/worker-shaped processes, later quarantine and another new restore identity. Add the module to the existing complete backend runner. Preserve DB/test/outer bounds, no production database access and no blind retry.</action>
  <verify>Focused recovery/auth/effect tests, full core-local runner in batches of at most20 labels under120 seconds each and900 seconds outer; worker/proxy lanes only where changed concerns justify them. Build and compare inert app source after staging owned new files.</verify>
  <done>Current changed source has passing bounded tests and exact inert source evidence; actual restoration and safe reopening remain pending.</done>
</task>
<task type="auto">
  <name>Record scoped evidence and synchronize current GSD execution state</name>
  <files>.planning/STATE.md, .planning/ROADMAP.md, .planning/PROJECT.md, .planning/HANDOFF.md, .planning/state.json, .planning/phases/13-purchase-flow-fulfilment-and-release-acceptance/13-01-PLAN.md, .planning/phases/13-purchase-flow-fulfilment-and-release-acceptance/13-QUALIFICATION-REGISTER.md, .planning/phases/13-purchase-flow-fulfilment-and-release-acceptance/13-STARTUP-RECOVERY-PARTIAL.md, .planning/quick/261028-cgz-fence-local-restore-startup-with-an-exte/261028-cgz-SUMMARY.md</files>
  <action>Consume the restored one-shot handoff and retain an active checkpoint. Record exact local evidence, configuration contract and limits; preserve commercial/actual inputs as pending. Synchronize all canonical fields and active roadmap views, publish state.json, refresh inventory and pass planning checks. Commit owned changes and immediately push ordinary non-force origin/main under standing authorization; append quick completion only after the implementation hash exists. Continue substantive authorized work.</action>
  <verify>python3 scripts/check_purchase_plan.py --refresh-inventory; python3 scripts/check_planning.py; python3 -m unittest tests.test_planning_activity tests.test_purchase_plan_inventory; git diff --check</verify>
  <done>Reviewable pushed local implementation, truthful evidence and concrete continuing task; no Phase13 full completion or external approval inferred.</done>
</task>
</tasks>
