# Full NixOS activation-impact review

**NOT OBSERVED.** Neither an evaluated candidate nor a small textual diff authorizes host writes. The full actual current/proposed configuration and complete impact must be reviewed before the first write.

Record current/proposed source revisions, lock identities, complete evaluated closures and activation scripts, users/groups/subordinate ranges, units/generators, mounts/datasets, dependencies/order, restart/reload triggers, sockets/listeners, firewall/journal/delegation/cpuset/resource policy and boot/session/linger behavior. Review scripts privately with sanitized hashes/results; do not paste credential-bearing configuration into evidence. Compare all owners/states, native units and guests. Explain every removed/changed/new effect and every dependency-triggered action. A protected or unknown effect blocks its operation.

The candidate module is disabled, installs no global Podman policy, and does not change existing global linger policy. Its proposed new account/ancestor/Quadlet/linger definitions still require actual full impact review. Existing general user-management/activation machinery can have effects beyond a small new-user diff; do not infer safety from module intent or a passing synthetic evaluation.

Forbidden generic actions: nixos-rebuild switch/test/boot, host reload/reboot, global prune/GC, protected proxy/firewall/journal/cgroup changes, guest infrastructure changes, host-generation rollback. A narrowly authorized new-shop action must carry exact before/after evidence, bounded stop thresholds and record-preserving shop-only rollback.

## Deferred protected action form — unapproved

If no unchanged alternative works, prepare one concrete record with: exact protected service/resource; exact action; necessity and rejected unchanged alternatives; full affected dependencies/listeners/allocations/restart/reload effects; expected interruption; rollback and recovery ownership; preserved business/evidence data; bounded verification/stop criteria; and later user authorization explicitly naming that service/action. Authorization is currently absent. Generic deployment approval does not fill this record.

Do not run the action while preparing its proposal. DNS-01 cannot establish a missing route. If existing SMTP/monitoring/backup interfaces cannot be consumed unchanged, defer that integration using the same exact-action process.
