# Stack: supplied October 20 baseline

Source: proposal “Architecture and first-release boundaries” and handoff fixed architecture/T02. No independent version verification performed.

| Component | Planning choice | Verification |
|---|---|---|
| Public build | Static Astro Content Collections + React islands | Exact compatible releases/artifact hashes at T02; no server adapter |
| App | Django LTS, Gunicorn, Psycopg, Python | Supplied Django 5.2.18/Python 3.13 are research inputs, verify support/patches/licences at T02 |
| Database/queue | PostgreSQL and one leased outbox worker | Supplied PostgreSQL 18.6 is a baseline assertion; real locking/concurrency proof |
| Build runtime | Supplied Astro 7/React 19/Node 24 LTS | Verify actual compatibility and support before locks |
| Services | Supported pinned NixOS/native systemd; approved Podman fallback | Qualify image/bootstrap at T11; no simultaneous managers |
| Edge | Caddy 2, explicit Let's Encrypt | Pinned build; DNS-01 module only if needed, test renewal |
| Recovery | pgBackRest, separate gra/sbg namespaces and custody | Actual provider retention/ACL/restore proof at T11/T12 |

No mandatory Redis/Celery/CMS/external IdP/commercial edition. Verify full distributed transitive notices/SBOM rather than assuming licence-family summaries cover artifacts. Current prices and software versions are intentionally not newly asserted by this planning pass.
