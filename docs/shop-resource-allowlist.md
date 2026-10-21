# Proposed shop allowlist and database map

**NOT OBSERVED.** No row below is an existing owned resource or permission to create/modify it. The selected profile keeps real IDs/digests/dataset names null and allocation/qualification false.

| Proposed new scope | Required actual proof before a write |
|---|---|
| shopsvc, its UID/GID/subordinate ranges and home /srv/shop | no pre-existing owner/resource/collision in any state; complete activation review; outside claude-dev |
| shop-app, shop-worker, shop-postgres, shop-gateway and shop-private network | exact rootless owner/store/container/image/network identities; one lifecycle manager and one worker; no inherited/default socket |
| New account ancestor | effective all-descendant CPU/memory/tasks/concurrency, payload/conmon/network/backup placement; no protected parent/delegation/cpuset change |
| New parent/DB datasets | actual owned pool/dataset/mount identities; proposed 80/50 GiB quota including snapshots/descendants and all data/index/WAL/writable categories; protect reserves |
| New runtime files and jobs | GraphRoot/images/volumes/temp/log/cert/spool accounting; independently owned shop backup jobs; new secret/certificate custody, no existing keys reuse |
| Candidate loopback gateway | actual unused listener/interface proof; example ports are not allocated; no change to existing public ingress |
| gra public/private, sbg recovery/evidence | exact project/namespaces/credentials/ACL/retention/bandwidth/billing proof; protect 001-xspi-pro |

The final allowlist must name exact new resource IDs, canonical paths, intended bounded actions, owner, expected before-state, identity recheck, approved change scope, expected after-state and shop-only rollback. Do not use wildcards, blanket ownership labels or generic deploy approval. Every unknown/pre-existing resource remains protected; no global prune/GC, network/journal policy, host reload/reboot or host-generation rollback.

Before **each** database mutation, positively match account UID, rootless engine/store/container ID, immutable image, mount/PGDATA/cluster system identifier, database/role, canonical socket or private server address/port and backup identity against actual reviewed evidence. Clear ambient DSN/service/engine variables. Missing mounts or empty PGDATA deny startup; no fallback initialization. Recheck after connection immediately before a guarded mutation; comparison of caller-supplied JSON alone is not observation or authorization. The per-mutation wrapper is still pending in plan 14. Test against an independently owned decoy cluster off-host and prove zero unintended writes.

Rollback may stop/remove only exact newly owned shop resources while retaining committed business/evidence records and protecting backups. Ownership ambiguity, changed identity or unexpected dependency halts rollback; never repair/revert a protected host/service to finish shop deployment.
