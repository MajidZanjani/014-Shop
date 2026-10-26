> Current requirements delta: [final26October purchase flow](../PURCHASE-FLOW-AMENDMENT.md). Baseline research below is dated; no compulsory technical checkout dossier/portal, blanket custom-board review or automated pooling prerequisite. Preserve unchanged architecture/protection and exact pending qualifications.

# Stack — selected October 21 architecture

Source-derived planning; no new upstream/current-host compatibility audit in this replan. Software/tariff research is dated October 20; actual recorded 02-01/02-02 artifacts are retained only for development.

| Component | Planning choice | Verification |
|---|---|---|
| Public build | Static Astro Content Collections + selected React islands | Exact compatible frozen graph; no runtime Node/adapter |
| App | Django LTS/Gunicorn/Psycopg/Python | Retained approved artifacts; actual runtime/import/lock/SBOM proof in T02 |
| Database/queue | New independent PostgreSQL container/cluster and one worker | Real PostgreSQL concurrency; distinct PGDATA/roles/credentials/socket/backup; destination checks |
| Development tools | Pinned Nix shell, Node/npm, Python/pip and PostgreSQL/libpq | Existing 02-02 development evidence; cached outputs retained |
| Production services | Rootless Podman, NixOS-declared Quadlet/user-systemd, proposed shopsvc directly on mx1 | Pin exact OCI/runtime/Quadlet/systemd/network/storage compatibility; one lifecycle; off-host runtime evidence then bounded T11 attestation |
| Resource boundary | Proposed host-controlled aggregate 200% CPU, MemoryHigh 6G / MemoryMax 8G, bounded tasks/concurrency | Covers payload scopes/conmon/network helpers/backup; protected parent/CPU/guest allocations unchanged |
| Persistence | New local ZFS shop datasets: 80 GiB aggregate, 50 GiB DB subtree | Snapshots/descendants and all rootless writable paths/logs/spool accounted; existing reserves/disks unchanged |
| Edge | New internal Caddy 2 behind unchanged existing public ingress | Fixed HTTPS object origin and metadata boundary; conditional A/B profile, complete path before DNS; new-shop Let’s Encrypt only |
| Recovery | Independent sbg pgBackRest, retained evidence, artifacts and custody | Full-pool-loss off-host rehearsal; existing PostgreSQL/services never restore targets |

No mandatory Redis/Celery/CMS/IdP/commercial edition. All distributed OCI/runtime/build transitive notices and SBOM identities require verification. Actual host OS/runtime support is observed read-only; no upgrade, shared reload, blanket NixOS activation or paid fallback follows from a missing capability.
