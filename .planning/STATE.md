---
gsd_state_version: "1.0"
status: executing
last_updated: "2026-10-21T12:42:03.202Z"
state_head: 908195a7a4a4db9db69d1c93ed36b12d145f2619
progress:
  total_phases: 14
  completed_phases: 1
  total_plans: 20
  completed_plans: 10
  percent: 7
last_activity: 2026-10-21
current_phase: 02
current_phase_name: Reproducible application and deployment skeleton
stopped_at: Resumed; control-record read hardening complete, plan14 implementation gaps remain.
last_activity_desc: Actual local SCRAM operator inspection and wrong-password/read-only denial verified.
---

# Project State

## Current position

Phase 02 remains executing; auto-advance false. Eight local slices complete (00–05,09,15), seven qualification/human-review pending (06–08,10–13), three implementation-incomplete (14,16,17). Only completion evidence uses SUMMARY.md; incomplete records use PARTIAL.md so GSD discovery cannot turn file presence into 18/18 completion. BUILD requirements and full phase/production acceptance remain incomplete. See 02-VERIFICATION.md (gaps_found) and individual records; the prior one-shot HANDOFF.json was consumed.

## Next authorized work

Finish14 actual qualification and record lifecycle for the new host-side process probe, operator integration/positive-transport qualification (source bundle and standalone inspection runtime are built) and integration of the single-DML SQL primitive with all applicable application/operator writes, schema/migration commands and app-role/auth/runtime configuration plus qualification of the new offline bootstrap; installation and qualification of the newly prepared account-scoped runtime/user-generator artifacts, and an executable independent replica driver. Current offhost-cases.json is only a matrix. Resolve16 raw npm CycloneDX URI validation failure,12 incorporated-text findings and actual native/Nix/OCI manifest/layer/notice coverage. Then finish17 actual OCI payload/config reproducibility and required full CI evidence. Human browser hydration/source/licence/probe/prohibition reviews remain pending.

No independent off-host runner assigned. User permits all authorized repository implementation, ordinary local/synthetic checks and deployment preparation. Do not run disruptive outage/restart/exhaustion/recovery tests on mx1, existing containers or MicroVMs. Preserve every existing service/allocation/resource. Do not provision/purchase automatically or repeatedly ask for runner; raise assignment at remaining qualification stage. Single specification: docs/qualification-runner.md. This dependency does not excuse unfinished repository implementation.

## Current evidence

Local environment2 checks/14 tests; frontend13/9; core-local4/22; worker-smoke6/24 including broken-fence/lock controls; adapters3/6 in isolated network; contracts-local12/8; combined boundaries17/32; deployment-eval15/27; postgres-diagnostics3/8; postgresql-config3/7; bootstrap-local3/13; database-destination3/82; database-tools6/5; operator-runtime4/10; profiles6/5; locks3/8; reproducibility4/5 with exactly2 independent public/backend builds. Counts overlap across lanes; no unique total implied. Reproducibility uses a fixed canonical path in separate private process namespaces; raw failed HTML-island-ID comparison remains recorded, no output normalization. Focused versioned manifest is local reproducibility only.

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

## Latest continuation — PostgreSQL console privacy

Code62c6f44 implements content-free console filtering and candidate image linkage using the exact existing Python interpreter. Local lane3 checks/8 tests includes real single-user PostgreSQL raw-versus-filtered runtime-generated canary evidence; synthetic native PID/exit/environment/stream controls pass. Deployment-eval15/25, PG config3/7 and environment2/14 passed. No image/container or fault execution. Next qualify actual image/canary/worker containment, postmaster reaping/PID1/lifecycle/backpressure and other log/private result paths; a protected forensic channel remains unimplemented. Continue roles/auth/network, archive/recovery, records/migrations/app/operator and generator/replica implementation;16/17/runtime/full CI/off-host gates remain pending. No credentials/host changes. Phase02 incomplete.

## Latest continuation — closed production Django database gate

Code52942a4 selects shop.db.unqualified in both production and bank-sandbox settings. It inherits PostgreSQL metadata/operations but refuses get_new_connection before the driver call; application/worker/management/migration and maintenance connections remain unavailable until qualified destination integration replaces this gate. This deliberately prevents readiness and migrations in these modes; it is not live transaction attestation or role/auth completion. Local/synthetic settings retain their ordinary disposable PostgreSQL backend.

Actual local evidence: core-local4 checks/22 tests,7.286 seconds; worker-smoke6/24,8.495 seconds. Added tests assert both production modes select the gate (mocked runtime secret reader only), named/default-maintenance connection attempts and cursor access fail with no driver call and no password in the error. Full off-host checks remain pending. First attempted dispatcher core-local was rejected as an unsupported lane before tests; corrected to scripts/check_backend.py core-local. No .env read, credentials required, host/provider action or resource change. Phase02 and plans14/16/17 remain incomplete.

## Latest continuation — guarded schema batch precursor

Codea008e1f adds bounded reviewed transactional schema SQL (1–64 statements,64KiB each and1MiB total UTF8), a cooperative nonblocking transaction advisory lock, fresh runtime/live SQL checks before each statement and before commit, and a host-side wrapper pinning the root-owned process record for the whole batch. Stacked commands are rejected by prepared execution; failures roll back without automatic retry. Exact artifact authorization, schema-role rights, Django migration/ledger integration and an operator command remain pending; production Django gate remains closed. Trusted SQL expressions are not sandboxed and external/nontransactional effects are outside rollback guarantees.

Actual local evidence: database-destination3 checks/21 tests,4.930s; deployment-eval15/27,2.128s. Real disposable PostgreSQL target/decoy tests cover schema commit/rollback, changed identity before each step/commit, failed later DDL, lock contention/release, bounds/forbidden commands and caller transaction refusal. Runtime/container/storage evidence remains synthetic and PGDATA comparison is fixture-adapted. No actual rootless lifecycle/fault qualification, .env read, missing credential, host/provider action or resource change. Plans14/16/17 and full production acceptance remain incomplete.

## Latest continuation — exact-byte schema authorization

Code22728e1 adds host-side schema_authorization library and docs/schema-migrations.md. A closed bounded root-owned schema-authorization.json record binds action, authorization/migration IDs, UTC expiry, exact artifact SHA256 and the complete approved database identity. Immutable UTF8 artifact bytes are hashed before strict duplicate-free JSON parsing and shared schema bounds validation. Fresh authorization/process-record checks run at each existing SQL/runtime guard callback; revocation, expiry or change before commit denies/rolls back. No command, record issuance, credential loading or deployment is supplied. Production Django gate remains closed.

Actual local evidence: database-destination3 checks/29 tests,5.016s; deployment-eval15/27,2.274s. Added tests cover exact authorization, equivalent-JSON byte changes, expiry/closed fields/IDs, duplicate/malformed/forbidden artifacts, byte bounds, target mismatch, authorization removal/change/expiry and process-record changes with DDL rollback. These are real disposable PostgreSQL plus synthetic authority/runtime records and fixture PGDATA adaptation only. No approval invented, .env read/value needed, host/provider operation or protected resource change.

Next migration work: atomic durable ledger/replay/uncertain-commit/restore reconciliation, Django migration generation/recorder integration, reviewed roles/credentials/private transport and root-owned publication/immutable packaging. Library does not consume authorization or prevent replay and must not become a deployment command before ledger integration. Revocation after final check cannot undo commit; trustworthy UTC clock/record custody remain operational prerequisites. Other14/16/17 and off-host/T11/T12 gates remain pending; no full acceptance.

## Latest continuation — atomic migration ledger

Code1f7b165 routes exact-byte authorized schema work through execute_schema_migration. A preexisting reviewed shop_control.schema_migrations relation is required; schema plus migration/digest/authorization IDs and transaction timestamp commit atomically. The same three values in a new explicit valid-authority call return already_applied without DDL; conflicting migration/digest/authorization reuse is denied. No automatic retry. A cooperative advisory lock and bounded table lock serialize this path. Ledger relation/owner/columns/constraints/indexes/hooks/grants are checked, including PostgreSQL18 catalog NOT NULL constraints; the original relation OID must survive DDL. Missing/changed/replaced ledgers fail closed. Separate schema-ledger.sql is a review/bootstrap artifact, not automatically applied or permission to adopt/create on a real host.

Actual local evidence: database-destination3 checks/38 tests,6.415s; deployment-eval15/27,2.132s. New real disposable PostgreSQL controls cover same-call replay decision, digest/authorization conflicts, authorization reuse for another migration, failed DDL and post-insert final-guard rollback, missing/altered/replaced ledger and schema/index/grant/trigger mutation. Lost caller acknowledgment is simulated by discarding a successful result then explicitly calling again; no real transport/process failure was injected. Existing runtime/root authority remains synthetic with fixed PGDATA fixture adaptation. Initial new-ledger run failed on incomplete PostgreSQL18 NOT NULL catalog expectations; corrected against official18 pg_constraint documentation and real tests. Final pass includes the stricter conenforced/OID checks.

Next: separately guarded ledger bootstrap/custody and production role grants, Django migration generation/recorder and operator command/credentials/private transport, immutable host packaging; uncertain-commit and restored-ledger reconciliation against external evidence plus actual failure/recovery qualification. already_applied is a ledger decision, not schema-drift verification or restored-service reopening permission. Privileged/inherited-role history tampering remains outside this local proof. Production Django gate stays closed. No .env read/needed credential, host/provider operation, existing service/resource change or purchase. Other14/16/17 and off-host/T11/T12/full acceptance gaps remain pending.

## Latest continuation — explicit guarded ledger bootstrap

Code995fdb8 adds ledger_bootstrap.py library, accepting only the exact pinned schema-ledger.sql bytes under a separate root-owned ledger-bootstrap.json record/action and reserved shop_ledger_bootstrap_v1 ID. It checks the same approved process/database and fresh runtime/live SQL identity before every CREATE/REVOKE, receipt insertion and commit, under the shared schema transaction lock. Any existing shop_control namespace is denied, including empty/matching/previously successful bootstrap. Validated new ledger plus bootstrap receipt commit atomically; no adoption, cleanup, target discovery or automatic retry. A repeated/uncertain bootstrap needs separate read-only reconciliation, never ledger removal. Source pin changes require review; no record issued or deployment command exposed.

Actual local evidence: database-destination3 checks/48 tests,7.055s; deployment-eval15/27,2.155s. Ten new controls cover receipt and later migration, matching/empty namespace denial, repeat denial, exact pin/action/ID/expiry, midway/final revocation rollback, real decoy no mutation, shared lock/caller transaction, named-role inherited grant denial and explicit removal of PUBLIC grants. Initial47-test run had one incorrect test expectation: pinned REVOKE correctly removes default PUBLIC INSERT. Corrected to distinguish named-role denial from intended PUBLIC removal; final48 passed. Root authority/runtime identity remains synthetic, fixed PGDATA fixture-adapted; no off-host or production proof.

Next: operator CLI/immutable packaging and separately authorized root-record publication/custody, migration/app roles and credentials/private transport, Django migration generation/recorder integration, read-only uncertain-commit/recovery reconciliation and actual off-host qualification. Bootstrap implementation is locally prepared; actual bootstrap/role/runtime qualification remains pending. Production Django connections stay closed. No .env read/needed credential, host/provider action, existing service/resource change or purchase. Other14/16/17 and off-host/T11/T12/full acceptance gaps remain open.

## Latest continuation — read-only schema outcome observations

Code835bf80 adds schema_reconciliation.py with separate root-owned schema-reconciliation.json, action inspect-schema-outcome and artifact_kind schema/ledger-bootstrap. New unexpired inspection authority refers to the original operation IDs/bytes; original write records are not read or renewed. Exact artifact and pinned process/database checks precede a READ ONLY, REPEATABLE READ transaction with fresh authority/runtime/live SQL checks before/after ledger reads. A closed result reports recorded/not_recorded/conflict/ledger_absent with retry_authorized=false and reopening_authorized=false. No artifact SQL, writes, advisory locks, repairs, bootstrap, record refresh or retries. Malformed/partial ledger is a denial, not a clean absence.

Actual local evidence: database-destination3 checks/60 tests,7.713s; deployment-eval15/27,2.175s. Twelve new tests cover ordinary/bootstrap receipts, missing/conflicting/invalid ledgers, independent action/kind/expiry, absent original write record, revocation, decoy denial, real read-only/repeatable transaction enforcement and refusal of writes/caller-owned transactions. Ordinary two-connection test commits a migration after the query but before return; old snapshot reports not_recorded without authorizing retry and a fresh inspection reports recorded. All tests passed; no process/network failure injected. Runtime/root custody remains synthetic, scratch PGDATA comparison adapted.

This is only a ledger observation library, not external-evidence or restore reconciliation, schema-drift verification or safe reopening. Next operator CLI/immutable packaging, record publication/custody, roles/credentials/private transport and Django migration/recorder integration; external recovery barrier and actual uncertain-commit/failure/recovery qualification remain pending. No .env read/value needed, host/provider action, existing service/resource change or purchase. Production Django gate stays closed; other14/16/17 and off-host/T11/T12/full acceptance remain incomplete.

## Latest continuation — immutable inert database source bundle

Code7dfa316 exposes shop-database-tools-source as a separate Nix package with seven explicit guarded modules, pinned ledger SQL and a closed hash manifest. Individual source bytes are copied into separate immutable store files; actual direct references equal exactly those8 files plus manifest. No interpreter/dependency environment, launcher, record, host configuration or installation. Exported metadata names the actual built source/manifest and keeps executable/runtimeQualified/productionActivation false. New required database-tools lane builds it and checks bytes, hashes, references, metadata and isolated imports through existing frozen runtime dependencies; no import-time connection/control read permitted. This is actual source-bundle build evidence, not OCI/operator-runtime qualification or a complete SBOM/licence review.

Actual local evidence: database-tools5 checks/5 tests,3.494s; deployment-eval15/27,2.164s; environment2/14 passes including updated all-lane producer checks. Prior database-destination3/60 remains recorded, not rerun because runtime module bytes unchanged. Full all not rerun; known off-host gate remains nonzero and the new lane is required by all. No failing test/build run this step. ROADMAP baseline/scope, misplaced Phase01 plan count, Phase02 count and progress row reconciled with actual2 Phase01 and8 Phase02 SUMMARY records. VERIFICATION gap audit refreshed without full verification or acceptance credit.

Next: concrete operator launcher/minimum dependency runtime, credentials/private transport/roles, record publication/custody and host-side installation, Django migration/recorder and application write integration, generator/replica/OCI/notices/reproducibility/full CI and actual off-host qualification. Source-only packaging does not complete these gates. No .env read/value needed, host/provider/service/resource change or purchase. Production Django connections remain blocked; Phase02 and14/16/17 remain incomplete.

## Latest continuation — prepared read-only operator command

Coded011e40 adds operator_inspect.py (inspect/--help only), strict root-owned operator-connection.json, private regular artifact FD0/credential FD3 reads, fixed proposed Unix socket path under shop tmp, approved binary paths, nonroot UID matching, socket ancestor/type/ownership/mode and stable record/socket checks. Standalone entrypoint scrubs environment before command handling; libpq parameters explicitly require SCRAM and default read-only sessions with bounded timeouts/null passfile. Records/artifact/process are checked before credentials/connect; inspection still uses guarded read-only snapshot. No DSN/password/path/mutation arguments, automatic setup or retries. Output is closed observation or fixed denial, no input/libpq/exception echo. Helpers use null stdin; descriptors are non-inheritable. Source bundle now contains8 modules, still no executable launcher/runtime/install/activation.

Actual local evidence: database-destination3 checks/72 tests,7.914s (61 database-suite cases plus11 FD/mock/process operator cases); database-tools6/5,4.029s including actual packaged help/mutation-command denial; deployment-eval15/27,2.144s. Real disposable PG trust-only server is rejected under require_auth=scram-sha-256. Positive command connection/probe/socket path is mocked, not real runtime/SCRAM qualification. Initial71/72-test attempts failed only child help import because the test omitted the pinned runtime discovery PATH; diagnostic run confirmed libpq not found, and corrected controlled PATH/LD_LIBRARY_PATH/PSYCOPG_IMPL preload fixture passed. Environment scrub occurs after required imports. This finding reinforces unfinished pinned executable-runtime packaging; no invented positive transport proof.

Next minimum operator runtime/launcher and error/startup qualification, separately authorized root-record publication/custody, actual dedicated socket mount/HBA/role/credential integration and positive peer/runtime/SCRAM tests, Django/app write/migration integration, generator/replica/OCI/licences/CI and independent off-host qualification. Current Quadlets/HBA provide no such operator socket/access and were unchanged. No real credential/.env read/needed missing value, host/provider action, service/resource change or purchase. Production Django gate stays closed; plans14/16/17 and full readiness remain incomplete.

## Latest continuation — pinned standalone inspection runtime

Codec60cd58 adds shop-operator-inspect flake package and required operator-runtime lane. A separate minimal site installs only the existing hash-locked Psycopg3.3.6 wheel offline, with pip as build tool only. Launcher uses exact bare Python3.13.16 with -I and cleared environment. Driver resolves only pq/c ctypes requests to exact Nix-store libpq18.6/libc paths, verifies pure-Python Psycopg/libpq180006 and sole Psycopg distribution before importing approved source, then invokes the command's own scrub. No compiler/pg_config/ambient library lookup needed. Python import/startup failures use fixed denial. Metadata keeps installed/runtimeQualified/productionActivation false; no NixOS module installs this package or any record/account/socket/role/credential.

Actual local evidence: operator-runtime4 checks/8 tests,2.000s, including actual main and synthetic import-failure package builds, hostile environment/shadow-module help, mutation/secret-option denial, invalid private input and fixed startup failure; deployment-eval15/27,2.100s; environment2/14,0.902s including required new all-lane coverage. Source bundle is verified as a runtime build dependency against exact source hashes; prior SQL/operator3/72 and source6/5 remain retained, not rerun because underlying modules unchanged. Full all not rerun; new operator-runtime lane required, no FULL_PASS. Initial lane failed native startup due to Psycopg's additional libc lookup; inspected exact installed wheel, pinned libc as well as libpq, then all8 passed. Temporary source-only diagnostic file was removed; no private inputs were used.

Next: authorized record publication/custody and actual dedicated socket/HBA/role/credential/peer/FD transport integration plus positive qualified connection, app/Django writes/migrations, generator/replica/OCI/notices/reproducibility/full CI and off-host qualification. Native closure/SBOM/licence review must include standalone launcher/runtime; package build/startup is not approval or host qualification. No .env read/needed missing value, real connection/host install/provider action, service/resource change or purchase. Production Django gate remains closed; plans14/16/17 and full readiness remain incomplete.

## Latest continuation — unverified control-record bundle contract

Code6c1360b adds record_bundle.py and validate-records command, plus docs/control-record-publication.md. Private FD0 bundle must remain unverified-candidate and contain exactly expected.json, database-process.json, operator-connection.json and schema-reconciliation.json plus strict base64 original artifact. Validates closed schemas, expiry, common startup/database identity, exact original bytes and pg_controldata as the approved PostgreSQL executable sibling. The same binary binding now applies to actual inspect. Library returns exact canonical private payload bytes and a closed hash report; CLI emits hashes only with publication/retry/reopening_authorized=false. No live record load, probe, connect, publisher or host write. Inner actual-evidence schema labels are shape-checked claims, never proof; outer evidence remains explicitly unverified.

Actual local evidence: database-destination3 checks/81 tests,7.960s including9 new candidate controls; operator-runtime4/10,2.440s with actual packaged private-FD valid candidate and mixed-record denial; database-tools6/5,4.000s with9-module source bundle; deployment-eval15/27,2.247s. No failing runs. Nix emitted an ignored eval-cache busy warning during concurrent evaluation; all required lanes completed0 with positive counts. Reports contain only hashes/closed flags, no record values/SQL. Synthetic fixtures and existing adapted scratch PGDATA remain local evidence, not actual host observations/approvals.

Publication contract requires actual retained inventory/ownership and exact authority, new-object staging and readback hashes, root-owned nonsymlink ancestors, bounded read-group permissions, durable complete generations under shop-only admission barrier and uncertainty reconciliation. It performs none of these writes. Next actual publisher/custody and positive socket/HBA/role/credential/peer/FD integration/qualification; application/Django migration/write integration, generator/replica/OCI/notices/reproducibility/full CI and off-host/T11/T12 remain pending. No .env read/needed credential, root record issued/published, real service connection, host/provider operation, existing service/resource change or purchase. Production Django access stays blocked; plans14/16/17 and full readiness incomplete.

## User-requested pause

Paused with structured HANDOFF.json and phase .continue-here.md. No implementation or qualification advanced during checkpoint. Resume with `$gsd-resume-work`; preserve pending 14/16/17 work and off-host gates. SUMMARY audit flags historical 02-01 pending-approval wording for reconciliation against the later actual approval record.

## Resumed continuation — stable control-record reads

Consumed the user-requested pause handoff. Plan02-01 review JSON records approve at2026-10-20T12:30:19Z for digest136610b07612762d390b3b3c234ff1ef3f6dc6b0e44a69a2abc646d9106b51bd; SUMMARY explicitly labels the later pending passage historical and superseded. No missing approval or summary correction is needed; approval scope unchanged.

Quick261021-h2i code5330962 checks file device/inode/UID/GID/mode/size/mtime/ctime stability across a bounded control-file read and requires exact nonempty length before parsing/validation. Synthetic cases deny every changed metadata field, truncated/empty reads and accept the32768-byte boundary. Actual local: process suite18 tests; deployment-eval15 checks/29 tests (2.543s), database-tools6/5 (4.341s), operator-runtime4/10 (7.714s), all exit0. A concurrent Nix evaluation emitted ignored cache-busy warning; no test failures. This detects observed descriptor changes, not hostile-root immutability or atomic multi-record publication. No host write, credential access, service/resource change or qualification execution.

Phase02 and14/16/17 remain incomplete. Next scoped durable generation publication/custody and private operator transport/application integration, plus previously recorded implementation/review/OCI/CI gates. Off-host runner unassigned; disruptive tests pending, no repeated runner question. Full all not rerun; no FULL_PASS. Continue using .env only when an authorized action actually needs credentials, and commit/push each step.

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 261021-h2i | Reject control records changed during descriptor reads | 2026-10-21 | beef66a | [261021-h2i-reject-control-records-changed-during-de](./quick/261021-h2i-reject-control-records-changed-during-de/) |
| 261021-hk6 | Exercise real operator SCRAM inspection on disposable PostgreSQL | 2026-10-21 | 908195a | [261021-hk6-exercise-real-operator-scram-inspection-](./quick/261021-hk6-exercise-real-operator-scram-inspection-/) |

## Latest continuation — real local SCRAM inspection

Code908195a adds actual disposable PostgreSQL18.6 SCRAM authentication through operator_inspect.inspect_from_fds and the actual guarded read-only ledger inspector. Three connections observe not_recorded/recorded/conflict, return retry/reopening=false, leave ledger rows unchanged and close. All use default read-only sessions and an attempted DELETE is rejected. A wrong synthetic password is rejected without retry. The real private FD reader executes through test descriptor mapping. Only the new token-owned scratch cluster's HBA/password are changed; existing services and allocations unchanged.

Local database-destination passed3 checks/82 tests,8.657s after final read-only denial assertion. Earlier first run failed fixture prevalidation of expected==expected; corrected explicit scratch-path adaptation. Second failed fixture insert omitted required applied_at; supplied clock_timestamp(). Intermediate82-test run passed8.662s before final assertion. These are fixture corrections, not production runtime fixes. No other lanes rerun because runtime/package bytes are unchanged. No full all/FULL_PASS or operational qualification.

Socket/PGDATA paths, root records, effective operator UID, process probe and socket ancestry/identity are explicitly adapted/mocked. Uses fixture administrative role, not qualified least-privilege access. Actual fixed FD0/FD3 launcher, positive peer/container/process binding, root-record issuer/publisher/admission barrier, production socket/HBA/roles, Django writes/migrations, generator/replica/image/notices/CI and off-host qualification remain pending. No .env read, actual credential needed, host access, protected-service change or purchase. Phase02/14/16/17 remain incomplete; runner unassigned with no repeated request.
