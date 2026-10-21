---
phase: 02-reproducible-application-and-deployment-skeleton
plan: "05"
status: complete
subsystem: build
requires: [02-00, 02-02]
provides: [hash-locked-python-runtime, hash-locked-python-tools, clean-environment-qualification]
affects: [02-06, 02-12, 02-14, 02-16]
tech-stack:
  added: [Django 5.2.18, Gunicorn 26.2.0, Psycopg 3.3.6, pip-tools 7.6.2, jsonschema 4.26.0, cyclonedx-bom 7.5.0]
  patterns: [pip-owned-resolution, hash-enforced-wheel-installation, isolated-runtime-and-tools]
key-files:
  created: [backend/requirements/runtime.in, backend/requirements/runtime-linux-py313.txt, backend/requirements/tools.in, backend/requirements/tools-linux-py313.txt, scripts/check_python.py, tests/test_python_environment.py]
  modified: []
key-decisions:
  - Resolve dependencies with pip/pip-tools only; bootstrap complete wheel closure without executing downloaded distributions first.
  - Use owned checkout scratch storage rather than the undersized shared temporary filesystem.
  - Discover libpq through the exact pinned PostgreSQL package references; do not alter accepted development tools to add pg_config.
requirements-completed: [BUILD-01, BUILD-02]
completed: 2026-10-21
coverage:
  - deliverable: Complete isolated hash-locked runtime and tool import/install paths
    verification:
      - kind: command
        ref: nix develop ./ops/nixos --command python3 scripts/check_python.py --qualify
        status: pass
      - kind: test
        ref: tests/test_python_environment.py
        status: pass
    human_judgment: false
---
# Phase 2 Plan 05: Hash-locked Python runtime and tools

Actual Linux x86_64/Python 3.13.16 runtime and resolver/schema/SBOM tools install only frozen wheels, pass pip check and import under isolated environments with pinned libpq.

## Accomplishments

- Pip downloaded a complete inert 39-wheel tool closure. Root distribution metadata and SHA-256 were recorded; direct approved tool wheel bytes match the existing exact review. Bootstrap manifest SHA-256: 675ad55e147beddec93b8c4558383e9371790e8e898c407364d339d0158beec1. Vendored setuptools metadata is distinct from its single root distribution.
- The full closure installed with no-index/require-hashes into an isolated bootstrap, then actual pip-tools compiled both complete locks with generated hashes, pinned unsafe installer/build distributions and no emitted index credentials. Standard pip remains the resolver/installer.
- Qualification creates new owned scratch environments, downloads only hash-verified wheels, installs offline into empty venvs, runs pip check and actual imports and compares every installed version to the complete lock. No global/user packages are admitted. Pinned PostgreSQL package version and its declared store references select libpq; Psycopg reports version 180006 and pure-Python implementation.

## Actual verification

`nix develop ./ops/nixos --command python3 scripts/check_python.py --qualify` passed with 63 checks and 7 executed tests (zero skips), duration 9.754 seconds in the final run. Runtime: six distributions including Django 5.2.18, Gunicorn 26.2.0, Psycopg 3.3.6 and pip 26.2.1. Tools: 39 distributions including actual pip-tools/jsonschema/CycloneDX imports and native lxml/rpds imports. Both environments passed pip check. Tests reject missing hashes/dependencies, empty inventories, wrong interpreter/tool versions, global sites, duplicate/unpinned/URL-style lock inputs.

## Deviations from Plan

[Rule 3 — execution blocker] The existing /tmp mount is only 128 MB and filled while installing this task's bootstrap. Read-only df showed 2.4 GB available in the project filesystem. Moved only task-owned bootstrap files to .scratch, removed only the incomplete task-owned venv and rebuilt it there, using an owned TMPDIR. No shared files, Nix store, guest/service configuration or allocations were cleaned or changed. The final qualifier creates and cleans bounded owned checkout scratch automatically.

[Rule 3 — tool packaging] The accepted pinned Nix environment contains PostgreSQL runtime but no pg_config. The implementation reads only that exact package's bounded declared store references, requires one libpq candidate and verifies the actual loaded library version. No accepted flake change or system library fallback.

## Commit

b4def63 — complete target locks, qualifier and rejection tests. No Django application, host/production/container acceptance, bank/mail call or protected-resource operation occurred. Shared BUILD requirements remain incomplete until their other plans finish. Ready for 02-06; 02-04 frontend boundary is independent and can proceed.

Official installation reference: https://pip.pypa.io/en/stable/topics/secure-installs/ . Exact pip-tools flags were executed through the frozen installed tool; no hand-written dependency resolver was added.
