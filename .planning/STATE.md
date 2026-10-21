---
gsd_state_version: "1.0"
current_phase: 02
current_phase_name: Reproducible application and deployment skeleton
status: executing
stopped_at: Candidate runtime and local evidence committed; finish 14/16/17 gaps.
last_updated: "2026-10-21T09:42:35.620223+00:00"
last_activity: 2026-10-21
last_activity_desc: Closed PostgreSQL runtime draft added; native parser/HBA7 tests and deployment/environment regressions pass.
state_head: 87047c5
progress:
  total_phases: 14
  completed_phases: 1
  total_plans: 20
  completed_plans: 10
  percent: 7
---

# Project State

## Current position

Phase 02 remains executing; auto-advance false. Eight local slices complete (00–05,09,15), seven qualification/human-review pending (06–08,10–13), three implementation-incomplete (14,16,17). Only completion evidence uses SUMMARY.md; incomplete records use PARTIAL.md so GSD discovery cannot turn file presence into 18/18 completion. BUILD requirements and full phase/production acceptance remain incomplete. See 02-VERIFICATION.md (gaps_found) and individual records; the prior one-shot HANDOFF.json was consumed.

## Next authorized work

Finish14 actual qualification and record lifecycle for the new host-side process probe, operator CLI and integration of the single-DML SQL primitive with all applicable application/operator writes, schema/migration commands and app-role/auth/runtime configuration plus qualification of the new offline bootstrap; installation and qualification of the newly prepared account-scoped runtime/user-generator artifacts, and an executable independent replica driver. Current offhost-cases.json is only a matrix. Resolve16 raw npm CycloneDX URI validation failure,12 incorporated-text findings and actual native/Nix/OCI manifest/layer/notice coverage. Then finish17 actual OCI payload/config reproducibility and required full CI evidence. Human browser hydration/source/licence/probe/prohibition reviews remain pending.

No independent off-host runner assigned. User permits all authorized repository implementation, ordinary local/synthetic checks and deployment preparation. Do not run disruptive outage/restart/exhaustion/recovery tests on mx1, existing containers or MicroVMs. Preserve every existing service/allocation/resource. Do not provision/purchase automatically or repeatedly ask for runner; raise assignment at remaining qualification stage. Single specification: docs/qualification-runner.md. This dependency does not excuse unfinished repository implementation.

## Current evidence

Local environment2 checks/14 tests; frontend13/9; core-local4/20; worker-smoke6/24 including broken-fence/lock controls; adapters3/6 in isolated network; contracts-local12/8; combined boundaries17/32; deployment-eval14/25; postgresql-config3/7; bootstrap-local3/13; database-destination3/13; profiles6/5; locks3/8; reproducibility4/5 with exactly2 independent public/backend builds. Counts overlap across lanes; no unique total implied. Reproducibility uses a fixed canonical path in separate private process namespaces; raw failed HTML-island-ID comparison remains recorded, no output normalization. Focused versioned manifest is local reproducibility only.

Installed standard SBOM evidence reconciles271 npm/6 runtime Python/39 tool Python components and records70 uninstalled optional paths. Collector exits2, not INVENTORY_PASS: raw npm malformed URI, missing licence texts and native/image coverage remain unresolved. Images are unbuilt; no real digest or compatibility claimed. Candidate profile/guard evaluation is not operational protection proof. Manual-only read-only SHA-pinned CI is prepared, never executed; no runner/authorization record created.

Full all actually exited1 after environment/frontend, stopped at required off-host core gate, no FULL_PASS. Later lanes did not run in that aggregate and are not reported as passed. Current source all six groups20/27/279/88/39/18 and self-check71 rejections passed. Historical evidence/source bytes unchanged.

## Locked decisions and scope

October21 proposal/handoff govern; embedded product bytes unchanged. New proposed shopsvc rootless Podman/NixOS/Quadlet directly on existing mx1, outside claude-dev. Separate app/one worker/new independent PostgreSQL/internal gateway and independently owned backup jobs. Proposed aggregate200% CPU,6/8GiB memory,80/50GiB ZFS need actual all-descendant/writable-path qualification. No new cloud compute/block/IP/fallback or permanent staging. £0.79 object-only model is dated/unverified.

All pre-existing/unknown owners/states/engines/native/VM resources protected. Sanitized read-only inventory, exact new-shop allowlist/database identity and full evaluated activation-impact review precede any host write. No blanket activation, protected reload/restart/repair/prune/GC/reboot, global policy/delegation/cpuset change or host-generation rollback. Ingress/TLS stays unchanged or deferred to a later exact named-service/action approval; no premature DNS or inference that DNS01 supplies routing. Existing SMTP/monitoring/backups unchanged or integration pending. Shop-only rollback retains committed records. Actual host qualification T11; recovery T12.

User continuation authorizes repository/application skeleton implementation and ordinary local tests, not real provider/bank/mail/DNS/TLS/production operations. Exact original dependency approval digest136610b07612762d390b3b3c234ff1ef3f6dc6b0e44a69a2abc646d9106b51bd does not extend to newly selected runtime bytes. Keep unresolved commercial/custody/P11/P12 decisions and flagged BUILD/prohibition findings explicit.

## Credential and workspace workflow

Resource-access credentials are available through repository .env. Read only needed values for authorized work without printing/copying into chat, logs, commands, evidence or public builds. If a needed credential is absent/empty, append a clear blank VARIABLE_NAME= entry/purpose preserving all existing values, then ask the user to fill .env directly. No currently needed missing credential identified. Runtime _FILE/build exclusions and action authorization remain distinct.

Use fresh GSD worktree manifests/full current HEAD and push every commit. Two old clean historical worktrees at2c64d9b must never replay stale prompts; no workers active. Reuse cached Nix outputs and bound jobs/cores/time. Project filesystem had~2.4GiB free at preparation; shared /tmp128MiB is small. Use owned .scratch/TMPDIR and short SHOP_TEST_SCRATCH; never clean shared files/store/caches or change allocations. No mx1 SSH/provider access, disruptive runtime operation, existing-service change or purchase occurred.

## Completed reset

Quick261021-8cb: October21 protected-host replan, committed2f07e57; docs/archive/2026-10-20-planning is historical only. Source files were read completely and remain immutable; active cloud-instance backend requirements were replaced. Current execution follows that reset plus later user implementation/.env instructions.

## Standing implementation task: context checkpoint

When session context exceeds 90%, run `$gsd-pause-work`, save a complete resumable handoff and tell the user to clear the session and run `$gsd-resume-work`. Stop implementation until resume. Follow the indicator/unknown-percentage policy in AGENTS.md and PROJECT.md; never invent a measured percentage. This standing instruction preserves all current incomplete work and pending evidence.

## Session continuity — SQL guard continuation

Resumed from HANDOFF.json; consumed and removed the one-shot handoff after preserving its pending work here and in 02-14-PARTIAL.md. Code commit169f72c adds same-transaction live SQL identity checks and a required database-destination lane: local synthetic3 checks/13 tests. Container/account evidence and canonical-path adaptation remain test fixtures; no rootless/runtime/host proof. Deployment-eval9/4 and environment2/14 passed. Next implement the concrete runtime attestation and command integrations, bootstrap/migrations and generator configuration; 14/16/17 and all external/human gates remain incomplete. No credentials needed or read.

## Latest continuation — process probe

Code3e83014 adds the concrete read-only host-side process snapshot producer, root-owned attestation loader and execute_operator_mutation binding. Deployment evaluation10 checks/18 tests (14 new synthetic tests); actual local SQL regression3/13 passes. New tests use synthetic /proc and mocked descriptor evidence, not actual Podman. No record installed, process discovered or runtime test executed. Concrete operator commands/credentials, record lifecycle, app/worker enforcement, bootstrap/migrations, runtime/generator and replica driver remain unfinished. Keep14/16/17 incomplete and off-host execution pending. Commit and push after each completed step per user instruction.

## Latest continuation — account-scoped runtime bundle

Code acaa097 prepares pinned, cleared-environment Podman/Quadlet wrappers and immutable account-scoped runtime/storage configuration. Code3cc8b8c disables implicit read-only tmpfs mounts and bounds shared memory on all four candidates. Both steps committed/pushed. Final deployment-eval12 checks/25 tests includes actual Nix evaluation/TOML parsing/shell syntax and negative fixture checks only. Disabled module leaves runtime artifacts absent; global user generators/linger unchanged. No native build, actual generator/Podman/container execution or mx1/credential access. Next finish bootstrap/migration configuration, per-user discovery installation and record lifecycle, app/operator enforcement and replica driver; runtime review/licences/images and independent off-host tests remain pending. Phase02 remains executing and incomplete.

## Latest continuation — offline bootstrap

Code637b901 adds explicit one-use offline cluster initialization, durable attempt/receipt handling, shared root-owned authority loading and inert Nix bootstrap artifact. Local bootstrap3 checks/13 tests ran actual initdb and single-user UTF8 catalog verification only on a new owned disposable directory; no listener. Deployment-eval13/25, SQL3/13 and environment2/14 regressions pass. Forced Nix bootstrap evaluation now retains whole-repository Git context; earlier metadata was not a build proof. No production record provisioned, .env credential needed/read or host/service action. Next implement application database/roles/auth/runtime config, reviewed record publication, migrations and isolated app/operator enforcement, per-user generator installation and replica driver; off-host bootstrap/runtime/recovery and image/licence/CI qualification remain pending. Phase02 incomplete.

## Latest continuation — closed PostgreSQL runtime draft

Code87047c5 adds immutable PostgreSQL/HBA candidate files and readonly Quadlet mounts. TCP disabled; every connection rejected; explicit durability and deliberately failing archive command retain WAL without a successful-backup claim. Local native single-user config/HBA verification3 checks/7 tests; deployment-eval14/25 and environment2/14 passed. No listener, archiver, host/service mutation or credential access. Provisional memory/connection settings are not qualification; archive backlog can exceed max_wal_size. Next implement qualified application roles/auth/network access, **PostgreSQL diagnostic privacy and canary handling**, real archive integration and migrations/app/operator enforcement; generator/replica/OCI/licence/full CI and off-host/recovery remain pending. Phase02 remains incomplete.
