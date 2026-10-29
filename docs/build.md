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

Backend package map: manage.py is the management entry point; shop.wsgi serves the application; shop.config owns environment settings; shop.core owns health, configuration checks and closed structured logging. The health endpoints remain /health/live and internal /health/ready; internal readiness still awaits qualified ingress protection. Local/synthetic catalog, verified-customer draft/cart/quotation/business workflows, owner document prerequisites and a separate staff rehearsal/review/preparation process are implemented. Django owns /purchase/simple/ preview and customer access/cart/history forms. See [local development](local-development.md) and [current project state](../.planning/STATE.md) for their exact scope. Real staff MFA/delivery, approved offers, acceptance/payment, fulfilment and production activation remain pending.

Safe logs emit only an enumerated event, bounded numeric status and locally generated correlation identifier. They discard exception strings, arguments, request bodies, paths and arbitrary extras. Tests seed synthetic host/key/business-tax/bearer/DSN canaries; no actual private values are inspected. Health SELECT and request timeouts are bounded. A mocked exception control is ordinary unit evidence, not an actual database outage result.

Full `scripts/check.py core` remains nonzero while an independent off-host runner is unassigned. `scripts/check_backend.py core --runner-authorization /path/to/operator-record.json` is reserved for the assigned runner. Its closed JSON has schema=1, runner_id, machine_id_sha256 (SHA-256 of stripped /etc/machine-id bytes), checkout_commit, permitted_actions=["owned-synthetic-postgresql-outage"], synthetic_only=true and independent_of_mx1=true. The operator must actually authorize that exact independent machine/commit/action. Do not manufacture a record for mx1, its guests or the current unassigned development environment. See [qualification-runner.md](qualification-runner.md) for resources, access, estimates and pending suites.

Adapter checks fail when their later test producer/wiring is absent. Missing capabilities and required producers are errors, not skipped successes. Full phase and production acceptance remain pending: off-host disruptive/runtime containment/recovery tests, real browser hydration, exact runtime image review and later provider/protected-host qualification. No external bank sandbox, actual OVH or production evidence is inferred from local tests.

## Later local evidence and incomplete full qualification

Implemented local feedback now includes candidate deployment evaluation/profile review, standard installed SBOM collection, installer tamper controls and two public/backend source payload builds. Full acceptance remains incomplete for implementation and evidence reasons, in addition to the unassigned runner.

```sh
mkdir -p .scratch
export SHOP_TEST_SCRATCH="$PWD/.scratch"
python3 scripts/check.py deployment-eval
python3 scripts/check.py deployment-profiles
python3 scripts/check.py locks
python3 scripts/check_reproducibility.py --local --record-evidence
python3 scripts/inventory_artifacts.py --local
```

Run inside the qualified pinned shell. The inventory collection returns exit 2 with retained raw standard SBOM/notice findings; that is not a pass. Complete inventory requires resolving its npm CycloneDX URI failure, missing incorporated texts and actual native/OCI closure coverage. Images are unbuilt and exact runtime/transitive review is pending; build/boot remain nonzero. ops/runtime/offhost-cases.json is a pending matrix, not an executable replica driver. Bootstrap/per-mutation wrapper and that driver remain implementation work.

Local reproducibility uses exactly two independent source/cache/build directories. Astro hashes its component URL into island IDs, so differing absolute roots initially changed HTML; the failed manifests are retained. Each build now sees the fixed /tmp/shop-reproducible-build path through its own new private mount/network namespace. The parent exclusively owns an empty marker-protected temporary target, never reuses an existing one, verifies it is not mounted in the parent and removes only its own target. Output bytes are not normalized. Backend source/migration/requirements tar metadata is deterministically specified; runtime/OCI payload reproducibility remains unproved. Raw SBOM serial/time fields are outside payload comparison; installed npm graph identities are compared separately. The versioned manifest records this focused local command only, not all/CI or production acceptance. Its elapsed timing runs through validation preparation; final cleanup/printing overhead is reported separately in the command marker.

Installer controls first pass real frozen installs. Offline negatives cover npm manifest/lock sync, SRI mismatch and changed bytes in a valid React archive, plus pip wrong hash, missing hash and changed valid wheel bytes. Expected integrity/lock diagnostics are mandatory; missing network/cache/artifact errors cannot count as success. Only disposable copies change.

The manual-only CI workflow has read-only permissions, SHA-pinned checkout, no persisted credentials/global safe-directory write, no production/bank/cloud secrets, no cache upload and no automatic runner provisioning. It runs trusted main only after exact operator runner/machine/commit authorization. Checkout is pinned to actions/checkout commit 11d5960a326750d5838078e36cf38b85af677262 (official v4 ref observed 2026-10-21; Node 20 runtime). No pull_request_target/workflow_run or automatic untrusted self-hosted execution. Ordinary feedback uses named dispatcher lanes; full required qualification uses the identical scripts/check.py all. Aggregate requires both jobs successful with positive counts; absent/skipped/cancelled/pending jobs cannot yield acceptance. No CI run is claimed.

The checkout authorization record has machine_id_sha256, checkout_commit, independent_of_mx1=true and permitted_actions=["owned-synthetic-ci-checkout"]. It must reflect an actually assigned independent runner, never be manufactured by the agent. Standard runtime lanes consume separate operator-provided file paths from SHOP_CORE_RUNNER_AUTHORIZATION, SHOP_WORKER_RUNNER_AUTHORIZATION, SHOP_CONTRACTS_RUNNER_AUTHORIZATION and SHOP_DEPLOYMENT_RUNNER_AUTHORIZATION. The records use the existing closed schema and sole permitted action respectively owned-synthetic-postgresql-outage, owned-synthetic-worker-interruption, owned-synthetic-postgresql-outage and owned-synthetic-rootless-lifecycle. They convey no production/protected-host permission. No record is supplied currently; full modes remain nonzero. Resource-access secrets remain in .env under the user's missing-name workflow; runtime/CI authorization records are not credentials or inferred approvals.

Provenance/scope-language analog: docs/implementation-evidence.md. Named-error/hash-identity analog: docs/product-source/verify_t01.py. Historical observations are unchanged. Independent human source/licence/prohibition/flagged-probe and browser checks remain pending; no actual OVH, selected-bank sandbox or production result is implied.

## Four candidate archive evidence — 2026-10-29

[Current actual build/inspection scope](build/four-candidate-images-2026-10-29.md): all four pinned local candidates are built, source/config/layer/payload observations retained, and historical PostgreSQL bytes reproduce. Both inspectors accept closed `--image` selection (app/worker/postgres/gateway); omitted selection preserves PostgreSQL. This is local build-only evidence. Importer/merged links, OCI/two-build comparison, native/licence, application/bootstrap/runtime, independent CI/recovery and human review remain pending. Original empty/candidate-only inventory records remain historical rather than silently rewritten.
