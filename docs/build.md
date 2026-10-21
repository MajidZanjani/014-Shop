# Reproducible development skeleton

All results here are local/synthetic. The October 21 proposal/handoff and current source verifier govern the project; archived October 20 evidence is historical. Production architecture is new rootless Podman app/worker/PostgreSQL/internal gateway containers under proposed shopsvc on mx1. The development shell is not permission to deploy or change any existing resource.

Use the pinned Linux x86_64 shell with bounded build concurrency. Create only a new checkout-owned scratch directory; do not clear shared temporary files, stores or caches.

```sh
mkdir -p .scratch
nix develop --max-jobs 1 --cores 4 ./ops/nixos
python3 docs/product-source/verify_t01.py all
python3 docs/product-source/verify_t01.py self-check
python3 scripts/check_python.py --qualify
python3 scripts/check.py frontend
SHOP_TEST_SCRATCH="$PWD/.scratch" python3 scripts/check_backend.py core-local
```

Use a short absolute owned scratch parent if executing from a long worktree path: PostgreSQL Unix sockets have a strict path limit. The shared /tmp in the current development environment is small; the runner uses project scratch instead. Nix itself may need a checkout-owned TMPDIR set after creating that directory. No credential files are copied into builds or documentation.

`check_python.py --qualify` uses the interpreter's pinned pip to hash-verify wheel downloads, installs offline into separate empty runtime/tools venvs, runs pip check and imports the actual modules. Runtime dependencies are in backend/requirements/runtime-linux-py313.txt; resolver/schema/SBOM tools are in tools-linux-py313.txt. Build tools do not belong in the runtime image. Do not use global pip, unpinned npx, missing-package fallbacks or peer bypasses.

`core-local` performs the exact frozen runtime install, identifies a newly created PostgreSQL cluster/database, then executes these commands in that environment with synthetic settings and that database's generated Unix socket identity:

```sh
python manage.py check
python manage.py migrate --noinput
python manage.py test shop.core.tests --noinput
python -m gunicorn shop.wsgi:application --bind 127.0.0.1:PORT --workers 1 --threads 1 --timeout 5 --graceful-timeout 2 --max-requests 100
```

These commands run from backend; PORT is a newly selected loopback test port, not an existing service. The automated harness supplies it and bounds/cleans the process. Run the harness rather than pointing the commands at an existing cluster. Synthetic startup values come from ops/config/synthetic.example; local.example selects local mode. Production and bank-sandbox templates require runtime secret files under /run/secrets/shop and still select fake adapters/live payments false. They are templates, not operational approval. Only local/synthetic run this probe. All modes require explicit SHOP_ENV and settings selection; no .env loader or production fallback exists.

Backend package map: manage.py is the management entry point; shop.wsgi serves the application; shop.config owns environment settings; shop.core owns health, configuration checks and closed structured logging. Only /health/live and internal /health/ready exist. Internal readiness is not yet protected by a qualified ingress. No staff/MFA, commerce, payment or document-delivery implementation is claimed. /purchase/simple/ remains Django-owned and currently returns 404.

Safe logs emit only an enumerated event, bounded numeric status and locally generated correlation identifier. They discard exception strings, arguments, request bodies, paths and arbitrary extras. Tests seed synthetic host/key/business-tax/bearer/DSN canaries; no actual private values are inspected. Health SELECT and request timeouts are bounded. A mocked exception control is ordinary unit evidence, not an actual database outage result.

Full `scripts/check.py core` remains nonzero while an independent off-host runner is unassigned. `scripts/check_backend.py core --runner-authorization /path/to/operator-record.json` is reserved for the assigned runner. Its closed JSON has schema=1, runner_id, machine_id_sha256 (SHA-256 of stripped /etc/machine-id bytes), checkout_commit, permitted_actions=["owned-synthetic-postgresql-outage"], synthetic_only=true and independent_of_mx1=true. The operator must actually authorize that exact independent machine/commit/action. Do not manufacture a record for mx1, its guests or the current unassigned development environment. See [qualification-runner.md](qualification-runner.md) for resources, access, estimates and pending suites.

Adapter checks fail when their later test producer/wiring is absent. Missing capabilities and required producers are errors, not skipped successes. Full phase and production acceptance remain pending: off-host disruptive/runtime containment/recovery tests, real browser hydration, exact runtime image review and later provider/protected-host qualification. No external bank sandbox, actual OVH or production evidence is inferred from local tests.
