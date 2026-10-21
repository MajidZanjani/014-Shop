# Protected host inventory procedure

**NOT OBSERVED.** This is a review template. No SSH, host/provider query or resource change has occurred. Host location is unknown; gra/sbg describe object regions only. Existing and unknown resources are protected regardless of owner, state, engine, native/VM placement or apparent use.

Before any host write, an authorized operator records a timestamp, machine identity hash, actual NixOS configuration/generation revision and sanitized provenance for every inventory category. Use exact read-only commands and bounded field selectors; never dump .env, unrestricted inspect/config/environment, credentials, raw private keys, bearer URLs or unredacted application records. Repository .env supplies needed authorized access credentials; missing names are added blank and the user fills them directly.

| Required coverage | Sanitized evidence to collect later |
|---|---|
| Native units/sockets/timers and dependency/restart relationships | all running/stopped/failed/inactive units; owner, fragment hash, listeners and dependency edges; no Environment/credential values |
| Rootful engines and every rootless account/store | engine/version/UID; exact root/runroot; all containers/pods/networks/images/volumes, including stopped/failed resources; selected identity/state/mount/label fields only |
| VMs/MicroVMs and allocations | owners, configured/running state, CPU/RAM/disk/cgroup/delegation/mount identities; never alter guest allocations |
| Pools/datasets/mounts/reserves/snapshots | actual sources, all quota/refquota/snapshot accounting, unknown other-disk usage and protected reserves; no mount/create/set operations |
| Listeners/routes/firewall/proxies/certificates | TCP/UDP/all interfaces, process owner, route and termination chain, certificate references/renewal ownership; no certificate/key contents or reload |
| Existing services/integrations | Stalwart, existing PostgreSQL, Prometheus/Grafana/Blackbox/Alertmanager, NetBird/Matrix/Plesk, proxies and any unlisted service; preserve actual owners/interfaces unchanged |
| CPU/memory/tasks/storage ancestor graph | complete effective descendant accounting, delegation/cpuset constraints and shared journal/storage policy; unknown means not qualified |

Inventory runs against explicit owner/engine/store identities, not default sockets, aliases or ambient engine connection variables. Account enumeration and authorized owner-specific read-only access must cover all stores; inaccessible/unknown owners remain protected and block the affected operation. Example 18080/18443 are unallocated; preserve existing 80/443 and NetBird 18444.

Record each actual resource in a separate sanitized evidence artifact: observed_at, observer, exact bounded command, exit status, owner/type/state/name or hashed sensitive identity, config/artifact hash and protection disposition. This template cannot be filled by assumptions. Compare before/after during an independently authorized shop-only operation; stop on unexpected ownership, listener, allocation, restart, mount or protected health change. Do not repair protected services.
