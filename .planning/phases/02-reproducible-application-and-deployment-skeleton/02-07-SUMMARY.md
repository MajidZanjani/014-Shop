---
phase: 02-reproducible-application-and-deployment-skeleton
plan: "07"
status: qualification_pending
requires: [02-06]
provides: [explicit-environments, runtime-secret-files, registered-django-checks]
requirements-completed: []
---
# Phase 2 Plan 07: Fail-closed environments

Shared base and explicit local/synthetic/production-shaped settings enforce SHOP_ENV, false live payments, three fake-only adapters, absent live endpoints/inline credentials and DEBUG false. Production and bank-sandbox use the production module with private regular bounded runtime secret files under /run/secrets/shop; no production secret file was read. Supported Django check registration guards settings overrides. Nonsecret production/bank-sandbox templates describe the same contract. No privileged routes or provider integration were added.

## Actual evidence

The inherited ordinary `core-local` command passed 3 checks and 16 tests in 6.485 seconds: six Django configuration test methods plus ten actual Gunicorn HTTP cases on new isolated PostgreSQL 18.6. Subcases execute real Django startup for valid local/synthetic and missing/unknown/mismatched environment, live toggles/adapters/endpoints, inline secret and DEBUG rejection. Both production-shaped modes reject missing/relative/outside-runtime file paths. Synthetic temporary files test private permissions, symlinks, size limits and a known-good control. Configuration and secret canary contents are absent from startup errors. Templates parse and validate without credentials.

## Pending and scope adjustment

No deliberate outage test ran; full core remains nonzero without independent runner authorization. Plan 06's pending qualification also applies here. User explicitly permits implementation continuation. Requirements and phase acceptance remain incomplete.

Producer wiring was necessarily included in scripts/check_backend.py although omitted from this plan's original files_modified: it now explicitly supplies synthetic environment values, requires/discovers shop.core.tests, rejects zero/skipped tests and counts captured passing results once. This fulfills the task's explicit producer requirement; no shared dispatcher change. The worktree allowlist included this bounded integration change before editing.
