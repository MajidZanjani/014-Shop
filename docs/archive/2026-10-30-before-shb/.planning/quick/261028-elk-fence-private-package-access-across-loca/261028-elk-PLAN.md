---
phase: quick
plan: 261028-elk
type: execute
wave: 1
depends_on: []
autonomous: true
requirements: [OPS-02, AUTH-04, FUL-05, UAT-03]
files_modified:
  - backend/shop/access/recovery.py
  - backend/shop/catalog/private_packages.py
  - backend/shop/catalog/private_package_tests.py
  - docs/local-recovery.md
---

<objective>
Fence private package grant issuance and download consumption against stale cached customer sessions and concurrent local quarantine.
</objective>

<design_critique>
Package services receive a customer request already checked by their view, but currently use its cached session key without rechecking the recovery epoch. A request admitted before a reset can still reach these services afterward. Add an opt-in locking mode to the existing epoch predicate and require it at the start of both existing package transactions. Acquire the epoch lock before owner/resource locks; acquiring it afterward could invert quarantine's epoch-before-credential order through a staff/owner wait chain. Existing fake local archive reads already run within these bounded resource transactions. No network archive, bank or mail mutation is added under a lock. Preserve default read-only epoch checks, private errors, one-use/session/artifact/expiry and current-owner/archive controls. No new middleware, model, migration, dependency or actual recovery mechanism. Execute inline.
</design_critique>

<threat_model>
- Cached authenticated requests from a held, released or newly selected restore epoch must not issue or consume private package access.
- A successful package transaction must serialize with quarantine on the same epoch row through commit; proof uses a separate real PostgreSQL connection.
- Denied access must leave grants, token consumption, package/stage history and entitlement/support facts unchanged.
- Acquire the recovery epoch before customer/resource locks to avoid a new lock-order cycle with staff work and quarantine.
- Synthetic local transactions do not qualify actual traffic/egress isolation, confidential intake, revocation completeness, custody or off-host restore.
</threat_model>

<tasks>
<task type="auto">
  <name>Reproduce stale package authority and fence both transaction boundaries</name>
  <files>backend/shop/catalog/private_package_tests.py, backend/shop/access/recovery.py, backend/shop/catalog/private_packages.py</files>
  <action>Add PostgreSQL failures for cached request issuance/consumption after quarantine/release, fresh selected-startup denial and an independently observable epoch lock during local package archive reads. Require the existing epoch predicate in transaction-only PostgreSQL locking mode before owner/resource locks. Preserve default callers and existing package failure/expiry/replay contracts.</action>
  <verify>TMPDIR="$PWD/.scratch/auth-unicode-tmp" nix develop --offline ./ops/nixos#backend --command python3 .scratch/package-recovery-focused.py baseline; then focused after the fix. Existing frozen wheels, prepared_database and120-second test bounds remain.</verify>
  <done>Original code demonstrably accepts stale requests or lacks serialization; fixed code denies stale operations without effects and holds the epoch lock through each supported transaction.</done>
</task>
<task type="auto">
  <name>Qualify and record the narrow private-material recovery boundary</name>
  <files>docs/local-recovery.md, .planning/STATE.md, .planning/ROADMAP.md, .planning/PROJECT.md, .planning/HANDOFF.md, .planning/state.json, .planning/phases/13-purchase-flow-fulfilment-and-release-acceptance/.continue-here.md, .planning/phases/13-purchase-flow-fulfilment-and-release-acceptance/13-01-PLAN.md, .planning/phases/13-purchase-flow-fulfilment-and-release-acceptance/13-QUALIFICATION-REGISTER.md, .planning/phases/13-purchase-flow-fulfilment-and-release-acceptance/13-PACKAGE-RECOVERY-PARTIAL.md, .planning/quick/261028-elk-fence-private-package-access-across-loca/261028-elk-SUMMARY.md</files>
  <action>Run focused package/delivery/recovery/authentication cases, current bounded backend and exact inert source verification. Record exact local evidence and all actual gates. Synchronize current planning views, publish machine state and refresh inventory/checks before each commit. Push each commit immediately without force under standing authorization. Record actual implementation identity through the GSD quick helper after its commit. Continue authorized concrete work without inventing actual inputs or full acceptance.</action>
  <verify>Core-local≤20 labels per120-second batch/900-second outer; exact source paths/bytes/no symlinks; planning/source-authority checks; existing four planning/inventory tests; git diff --check.</verify>
  <done>Scoped implementation and completion metadata are committed/pushed, with actual revocation/MFA/custody/runner and commercial inputs still pending.</done>
</task>
</tasks>
