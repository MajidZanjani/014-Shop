> Current execution precedence: [final26October purchase-flow revision2](../../PURCHASE-FLOW-AMENDMENT.md) and STATE.md/ROADMAP.md. This file retains applicable baseline infrastructure work and qualification gates; any old next-step routing or conflicting purchase/delivery requirement is superseded. No protected/external authority changes.

Active local sequence and authorization: [2026-10-22 amendment](../../EXECUTION-AMENDMENT-2026-10-22.md). Historical replan-only statements below describe that earlier pass. T02 release qualifications no longer block independent local features.

# Phase 2 — October 21 locked context

Current continuation2026-10-29: policy-bound connection preparation is verified locally (SQL236/source7/5/eval16/31); [current scope](02-PROGRESS.md) and [complete remaining goal](02-COMPLETION-TRACKER.md) govern the next task. Prior replan-only/task-order prose below is historical. User requests complete planning synchronization and pause after this step; original locked constraints remain in force.

<decisions>
- The user selected existing mx1 + NixOS-declared rootless Podman Quadlet/user-systemd; Podman is mandatory production architecture, not fallback. Run directly under new proposed shopsvc, outside claude-dev and existing application owners.
- Separate app, one worker, new PostgreSQL container/cluster and internal Caddy containers; independently owned backup jobs. New PGDATA/roles/passwords/socket/network/backup identity, checked before every database mutation; no existing postgres reuse.
- Proposed host-controlled aggregate CPUQuota=200%, MemoryHigh=6G, MemoryMax=8G, bounded tasks/concurrency. Include payload scopes/conmon/network helpers/backup processes. No protected slice/cpuset/delegation/allocation changes.
- Proposed local ZFS 80 GiB aggregate including descendants/snapshots and 50 GiB PostgreSQL data/index/WAL subtree. Account for GraphRoot/images/volumes/temp/logs/certificates/spool; preserve reserves, snapshots, shared journal and unknown other-disk use.
- Every pre-existing/unknown resource in every state/owner/runtime/native/VM is protected. Before first mx1 write: sanitized read-only inventory, verified shop allowlist/isolation/DB map and complete evaluated NixOS activation-impact plan. No blanket activation, protected reload/restart/upgrade/prune/GC/reboot or guest infrastructure change.
- Existing public proxy/TLS/firewall remains unchanged. Qualify an already complete route/certificate lifecycle or defer public activation with exact service/action proposal; only later explicit service/action authorization can permit a protected mutation. DNS-01 does not create routing. No premature A/AAAA. Consume existing SMTP/monitoring interfaces unchanged or defer that integration.
- Runtime fault/exhaustion/restart/recovery and burst tests run off-host on independently authorized isolated replicas. Existing development checkout work can continue within unchanged allocations. mx1 allows bounded shop checks and read-only comparison only. Rollback is shop-only; preserve committed records and never roll back a host generation or repair protected services.
- Public/private gra and independent off-host sbg objects remain. No new production VM/block/IP rental, paid fallback, disk change or permanent staging VM. Model £0.79 incremental objects as dated illustrative input only; qualify actual retention and bandwidth.
</decisions>

## Evidence applicability and next execution

02-01 approval digest 136610b07612762d390b3b3c234ff1ef3f6dc6b0e44a69a2abc646d9106b51bd and 02-02 local development build/PostgreSQL evidence remain valid only for their recorded bytes/environment. They do not establish new source-checker compatibility, rootlessness, image identity or any host protection. Reuse cached development outputs; prior unbounded native compilation stalled the environment, so any necessary new build must have explicit cores/max-jobs/timeout and no duplicate derivation builds. Do not repeat unchanged review.

02-00 first migrates the historical source verifier. Then 02-03/02-05 resume; retained old worktrees are clean historical launch state and must receive fresh current context through the approved GSD isolation adapter before any execution. No stale worker may be redispatched. Plans 02-14/15 replace obsolete native-production/cloud-flavor designs. 02-16/17 cover new OCI/runtime inventory and off-host CI. This replan performs documentation only, with no application/runtime execution.

## Resource credentials — user instruction, 2026-10-21

The agent has access to resource credentials through the repository .env file. When authorized project work needs a credential, consult that file without printing values or copying them into planning, logs, commands, evidence or public artifacts. If the required credential is absent or empty, add a clearly named empty VARIABLE_NAME= entry with a short purpose comment to .env, preserving every existing entry, then ask the user to fill its value directly in that file. Never ask the user to paste secrets into chat. Continue independent work while waiting; do not invent values or approvals. No currently needed missing credential has been identified by this instruction alone.

This operator credential source does not require application .env auto-loading or relax runtime _FILE secrets, fake-only synthetic tests, build exclusions or existing action authorization. Read only the needed credential for the authorized operation; use non-logging process/environment or secret-file interfaces. Resource access is not automatic permission to purchase/provision, modify protected services or perform disruptive tests on mx1/its guests. The independent runner remains unassigned until the user supplies/authorizes it.
