---
gsd_state_version: "1.0"
status: paused
last_updated: "2026-10-22T09:18:17.520Z"
state_head: dd322e1
progress:
  total_phases: 14
  completed_phases: 1
  total_plans: 20
  completed_plans: 10
  percent: 7
paused_at: "2026-10-22T09:18:17.520Z"
last_activity: 2026-10-22
current_phase: 02
current_phase_name: Reproducible application and deployment skeleton
stopped_at: Proactive context checkpoint after payload inventory; read HANDOFF and resume safe local implementation.
last_activity_desc: "PostgreSQL inner-layer inventory verified: 14480 entries, 8298 regular files; absolute names and PAX recorded; production remains closed."
---

# Project State

**Updated 2026-10-22 (UTC). Evidence reviewed through implementation commit dd322e1.**
Current detail: [Phase 02 progress](phases/02-reproducible-application-and-deployment-skeleton/02-PROGRESS.md).
Chronological prior notes: [ACTIVITY-LOG.md](ACTIVITY-LOG.md); their old statuses are historical.

## Current position

Session proactively paused with a complete [handoff](HANDOFF.json). Exact context percentage is unavailable; this is not a threshold measurement. Clear/resume before further implementation.

Phase 02 is executing. Phase 01 has 2/2 documentation plans complete; Phase 02 has 8/18 local slices complete (00–05, 09, 15), 7 qualification/review pending (06–08, 10–13), 3 implementation/qualification incomplete (14, 16, 17). Across the milestone 10/20 planned records and 1/14 phases are complete. Frontmatter 7% is the rounded completed-phase ratio, not an estimate of implementation effort or today's work.

**Today 25 implementation quick tasks completed**, indexed below, plus one completed planning reconciliation. Quick tasks advance incomplete plans without falsely completing phase/BUILD acceptance. Eight Phase 02 SUMMARY files and ten PARTIAL files remain intentional; no FULL_PASS or production readiness is claimed.

## Current implementation and today's work

- Plan 14: pinned operator/schema launchers, actual local restricted SCRAM/peer tests, source-only exact control admission/block/custody/publication/reopening lifecycle and independent uncertainty observations. Twelve-module inert source package. New multi-statement Django transaction precursor holds admission through actual commit/rollback. Production/bank-sandbox still use the closed backend; safe host/application evidence boundary, all-write/role/transport integration and actual installation/qualification remain pending.
- Plan 16: exact artifact/named-file/embedded-header/npm-marker evidence and offline reconciliation.12 original gap packages:1 named text, 2 headers, 10 marker observations (overlap), all 12 package-wide/legal reviews pending. Raw npm SBOM remains invalid; separate attributable schema-valid derivative exists. Native closure/notice evidence is partial, not complete legal/native acceptance.
- Plans 16/17: one PostgreSQL Docker save candidate archive now actually built locally, 125653410 bytes, 51 ordered layer byte hashes checked against declared DiffIDs. Exact builder log/provenance/archive report retained. This supersedes yesterday's blanket unbuilt statement for PostgreSQL only; other images remain unbuilt. Inner layers now inventoried: 14,480 entries, 8,298 regular files, 298,557,309 bytes hashed; 5,151 symlinks and 10,517 absolute names recorded without resolution or extraction. PAX-aware manifest and two notice filename candidates retained. No image imported/run or merged-rootfs/native-licence/OCI distribution manifest/two-independent-build/runtime qualification.

## Current recorded evidence

Latest recorded results below are separate overlapping lanes, not a unique total or new full-suite execution.

| Scope | Latest passing evidence | Record |
|---|---|---|
| PostgreSQL destination/admission/Django primitive | 3 checks/184 tests, 13.762s | quick261022-aql |
| Inert database source package | 7/5, 9.497s; 12 explicit modules | quick261022-aql |
| Operator launchers | 7/17, 5.951s | quick261022-aql |
| Deployment evaluation | 16/31, 2.133s | quick261022-bw3 |
| Django core-local | 4/22, 7.710s | quick261022-aql |
| Worker-smoke | 6/24, 9.022s | quick261022-aql |
| Native operator closure / source notices | 56/9, 1.035s / 9/7, 3.820s | quick261022-aql |
| Licence/reconciliation/marker/inventory units | 28+8+4 tests, 40 total in these suites | quick261022-bqg |
| Docker archive / payload inspectors | 17 tests, 0.035s; actual 51-layer, 14,480-entry rescans match | quick261022-cor |

Most recent historical full-all attempt exited1 at the required off-host core gate after environment/frontend. It was not rerun today; there is no FULL_PASS. Earlier frontend/contracts/installer/two-public-backend-build/source-baseline evidence remains scoped to its historical record, not a newly executed all/OCI/CI pass.

## Next authorized work

1. Review the two image notice candidates and map native components; qualify observed absolute-name/link/PAX/importer semantics, build remaining prepared candidates and implement independent image comparison. OCI distribution manifests and complete native/legal inventory remain pending.
2. Resolve the safe host/application evidence boundary before application-role/connection/all-write backend and migration integration. Do not expose host /proc or host control mounts to application containers. Keep production closed until complete and qualified.
3. Finish account-scoped runtime/generator and executable independent replica driver, then assigned off-host lifecycle/recovery/full CI and outstanding browser/source/licence reviews.

No off-host runner is assigned. This does not block remaining repository implementation or authorize provisioning/purchase. Do not run disruptive tests on mx1/claude-dev/existing guests. No actual host/provider/DNS/TLS/bank/mail actions or credential reads occurred. Scoped local implementation and origin/main pushes remain authorized.

## Progress maintenance

After a completed local slice, refresh this current summary/evidence and linked Phase 02 progress, record its real commit in the quick-task table, update roadmap/requirement evidence when it changes, and publish the canonical state.json snapshot. Keep old dated narrative in ACTIVITY-LOG.md and preserve all incomplete acceptance gates. Do not rely on append-only notes to communicate current progress.

## Locked decisions and scope

October21 proposal/handoff govern; embedded product bytes unchanged. New proposed shopsvc rootless Podman/NixOS/Quadlet directly on existing mx1, outside claude-dev. Separate app/one worker/new independent PostgreSQL/internal gateway and independently owned backup jobs. Proposed aggregate200% CPU, 6/8GiB memory, 80/50GiB ZFS need actual all-descendant/writable-path qualification. No new cloud compute/block/IP/fallback or permanent staging. £0.79 object-only model is dated/unverified.

All pre-existing/unknown owners/states/engines/native/VM resources protected. Sanitized read-only inventory, exact new-shop allowlist/database identity and full evaluated activation-impact review precede any host write. No blanket activation, protected reload/restart/repair/prune/GC/reboot, global policy/delegation/cpuset change or host-generation rollback. Ingress/TLS stays unchanged or deferred to a later exact named-service/action approval; no premature DNS or inference that DNS01 supplies routing. Existing SMTP/monitoring/backups unchanged or integration pending. Shop-only rollback retains committed records. Actual host qualification T11; recovery T12.

User continuation authorizes repository/application skeleton implementation and ordinary local tests, not real provider/bank/mail/DNS/TLS/production operations. Exact original dependency approval digest136610b07612762d390b3b3c234ff1ef3f6dc6b0e44a69a2abc646d9106b51bd does not extend to newly selected runtime bytes. Keep unresolved commercial/custody/P11/P12 decisions and flagged BUILD/prohibition findings explicit.

## Credential and workspace workflow

Resource-access credentials are available through repository .env. Read only needed values for authorized work without printing/copying into chat, logs, commands, evidence or public builds. If a needed credential is absent/empty, append a clear blank VARIABLE_NAME= entry/purpose preserving all existing values, then ask the user to fill .env directly. No currently needed missing credential identified. Runtime _FILE/build exclusions and action authorization remain distinct.

Use fresh GSD worktree manifests/full current HEAD and push every commit. Two old clean historical worktrees at2c64d9b must never replay stale prompts; no workers active. Reuse cached Nix outputs and bound jobs/cores/time. Project filesystem had~2.4GiB free at preparation; shared /tmp128MiB is small. Use owned .scratch/TMPDIR and short SHOP_TEST_SCRATCH; never clean shared files/store/caches or change allocations. No mx1 SSH/provider access, disruptive runtime operation, existing-service change or purchase occurred.

## Completed reset

Quick261021-8cb: October21 protected-host replan, committed2f07e57; docs/archive/2026-10-20-planning is historical only. Source files were read completely and remain immutable; active cloud-instance backend requirements were replaced. Current execution follows that reset plus later user implementation/.env instructions.

## Standing implementation task: context checkpoint

When session context exceeds 90%, run `$gsd-pause-work`, save a complete resumable handoff and tell the user to clear the session and run `$gsd-resume-work`. Stop implementation until resume. Follow the indicator/unknown-percentage policy in AGENTS.md and PROJECT.md; never invent a measured percentage. This standing instruction preserves all current incomplete work and pending evidence.

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 261021-h2i | Reject control records changed during descriptor reads | 2026-10-21 | beef66a | [261021-h2i-reject-control-records-changed-during-de](./quick/261021-h2i-reject-control-records-changed-during-de/) |
| 261021-hk6 | Exercise real operator SCRAM inspection on disposable PostgreSQL | 2026-10-21 | 908195a | [261021-hk6-exercise-real-operator-scram-inspection-](./quick/261021-hk6-exercise-real-operator-scram-inspection-/) |
| 261021-i2j | Stage private unverified control candidates with durable exclusive files | 2026-10-21 | 542e2d8 | [261021-i2j-stage-private-unverified-control-candida](./quick/261021-i2j-stage-private-unverified-control-candida/) |
| 261021-j0i | Inspect retained private candidate generations without repair | 2026-10-21 | 9cbc570 | [261021-j0i-inspect-retained-private-candidate-gener](./quick/261021-j0i-inspect-retained-private-candidate-gener/) |
| 261021-j6p | Derive traceable schema-valid npm inventory while preserving raw evidence | 2026-10-21 | cacc247 | [261021-j6p-derive-traceable-schema-valid-npm-invent](./quick/261021-j6p-derive-traceable-schema-valid-npm-invent/) |
| 261022-6n6 | Audit exact distributions for twelve missing incorporated licence texts | 2026-10-22 | 8052689 | [261022-6n6-trace-missing-incorporated-licence-texts](./quick/261022-6n6-trace-missing-incorporated-licence-texts/) |
| 261022-6s2 | Retain exact embedded Python tool licence headers | 2026-10-22 | 4a02f7c | [261022-6s2-retain-exact-embedded-licence-headers-fr](./quick/261022-6s2-retain-exact-embedded-licence-headers-fr/) |
| 261022-6vp | Verify actual operator native reference closure | 2026-10-22 | 6008f2c | [261022-6vp-inventory-actual-cached-operator-native-](./quick/261022-6vp-inventory-actual-cached-operator-native-/) |
| 261022-700 | Prepare generator discovery for only new shop manager | 2026-10-22 | 8e7cbf4 | [261022-700-prepare-root-owned-generator-discovery-f](./quick/261022-700-prepare-root-owned-generator-discovery-f/) |
| 261022-73q | Integrate exact-authority schema operator transport and admission | 2026-10-22 | 0adc350 | [261022-73q-integrate-private-fd-guarded-schema-comm](./quick/261022-73q-integrate-private-fd-guarded-schema-comm/) |
| 261022-799 | Retain exact cached native upstream source notice candidates | 2026-10-22 | c14ae3a | [261022-799-retain-notices-from-cached-exact-python-](./quick/261022-799-retain-notices-from-cached-exact-python-/) |
| 261022-7l3 | Package separate pinned candidate schema launcher | 2026-10-22 | ec4c4db | [261022-7l3-package-separate-pinned-candidate-schema](./quick/261022-7l3-package-separate-pinned-candidate-schema/) |
| 261022-89m | Restricted-role schema qualification | 2026-10-22 | 1bbc889 | [261022-89m-qualify-guarded-schema-operations-with-a](./quick/261022-89m-qualify-guarded-schema-operations-with-a/) |
| 261022-8ci | Schema role admission enforcement | 2026-10-22 | 68b1c26 | [261022-8ci-enforce-restricted-schema-login-attribut](./quick/261022-8ci-enforce-restricted-schema-login-attribut/) |
| 261022-8fv | Connected Unix peer admission | 2026-10-22 | 3f03fe6 | [261022-8fv-bind-operator-unix-socket-peers-to-appro](./quick/261022-8fv-bind-operator-unix-socket-peers-to-appro/) |
| 261022-8m7 | Operator admission reader | 2026-10-22 | 96b7bc7 | [261022-8m7-hold-durable-control-admission-during-op](./quick/261022-8m7-hold-durable-control-admission-during-op/) |
| 261022-8so | Library-only persistent admission block | 2026-10-22 | be802bc | [261022-8so-prepare-separately-authorized-persistent](./quick/261022-8so-prepare-separately-authorized-persistent/) |
| 261022-9ba | Read-only uncertain-block reconciliation | 2026-10-22 | 1162972 | [261022-9ba-reconcile-uncertain-admission-blocks-wit](./quick/261022-9ba-reconcile-uncertain-admission-blocks-wit/) |
| 261022-9fo | Private exact-generation custody | 2026-10-22 | 783615a | [261022-9fo-retain-exact-admitted-control-generation](./quick/261022-9fo-retain-exact-admitted-control-generation/) |
| 261022-9m7 | Retained-generation inspection | 2026-10-22 | 2869c0b | [261022-9m7-inspect-retained-generation-custody-with](./quick/261022-9m7-inspect-retained-generation-custody-with/) |
| 261022-9uf | Physical control publication while blocked | 2026-10-22 | dfbdc74 | [261022-9uf-publish-reviewed-control-generations-whi](./quick/261022-9uf-publish-reviewed-control-generations-whi/) |
| 261022-a80 | Read-only publication reconciliation | 2026-10-22 | c5b3c7a | [261022-a80-reconcile-blocked-physical-publication-o](./quick/261022-a80-reconcile-blocked-physical-publication-o/) |
| 261022-afa | Prepare exact proposed admission bytes without activation | 2026-10-22 | 11279da | [261022-afa](./quick/261022-afa-prepare-exact-reviewed-admission-reopeni/) |
| 261022-ajs | Candidate reopening and uncertain-outcome inspection | 2026-10-22 | 820f7ba | [261022-ajs](./quick/261022-ajs-implement-separately-authorized-admissio/) |
| 261022-aql | Django multi-statement transaction precursor | 2026-10-22 | e863f6c | [261022-aql](./quick/261022-aql-integrate-admission-lifetime-into-a-clos/) |
| 261022-b5y | Supplemental prefixed licence-name audit | 2026-10-22 | e873adf | [261022-b5y](./quick/261022-b5y-audit-prefixed-licence-filenames-in-exac/) |
| 261022-bb9 | Bounded embedded npm notice-marker discovery | 2026-10-22 | 9c0f67d | [261022-bb9](./quick/261022-bb9-inspect-bounded-embedded-notice-candidat/) |
| 261022-bqg | Reconcile supplemental licence observations | 2026-10-22 | a02e5a5 | [261022-bqg](./quick/261022-bqg-reconcile-supplemental-licence-observati/) |
| 261022-bw3 | Build and inspect PostgreSQL candidate archive | 2026-10-22 | 798eaa3 | [261022-bw3](./quick/261022-bw3-build-and-inspect-the-prepared-postgresq/) |
| 261022-cci | Reconcile visible and machine-readable planning progress | 2026-10-22 | 8a5c91e | [261022-cci-reconcile-stale-planning-summaries-and-m](./quick/261022-cci-reconcile-stale-planning-summaries-and-m/) |
| 261022-cor | Inventory actual PostgreSQL inner-layer payload | 2026-10-22 | dd322e1 | [261022-cor-inventory-actual-postgresql-image-inner-](./quick/261022-cor-inventory-actual-postgresql-image-inner-/) |
