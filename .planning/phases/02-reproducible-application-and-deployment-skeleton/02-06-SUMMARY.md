---
phase: 02-reproducible-application-and-deployment-skeleton
plan: "06"
status: qualification_pending
subsystem: backend
requires: [02-05]
provides: [django-gunicorn-health, real-postgresql-local-health, prepared-scoped-outage-suite]
requirements-completed: []
completed: null
---
# Phase 2 Plan 06: Django health implementation; qualification pending

Commit 62430ea implements conventional Django/WSGI packages, explicit synthetic settings, loopback foreground Gunicorn and minimal GET live/ready JSON. Readiness performs actual PostgreSQL SELECT with bounded connection/statement/request timeouts; errors disclose only unavailable. Health handlers validate Host. No admin/private/commerce routes are mounted; Django retains future /purchase/simple/ ownership.

## Actual local evidence

`SHOP_TEST_SCRATCH=/home/claude/project/014-Shop/.scratch nix develop ./ops/nixos --command python3 scripts/check_backend.py core-local` passed: 3 checks, 10 HTTP tests, 4.277 seconds. The frozen runtime was installed in an empty owned environment. A new token-validated PostgreSQL 18.6 cluster/database was identified, checked and migrated. Actual Gunicorn served live/ready 200, five absent-route 404s, POST 405s and unapproved Host 400. Cleanup stopped only this newly created scratch cluster/process. No deliberate outage was executed.

A separate rejection control confirmed the full core command without runner authorization returns nonzero with PENDING_OFF_HOST and no CORE_PASS (3 assertions). The dispatcher full core lane therefore remains nonzero; no full qualification is claimed.

## Pending and implementation continuation

The prepared fault suite stops only its newly created token-validated cluster, checks bounded 503 and unchanged liveness, restarts that cluster, and checks readiness recovery. It has **not run**. Before execution, an operator-supplied closed JSON authorization must match an independently assigned runner machine-ID hash, exact checkout commit and sole owned-synthetic-postgresql-outage action. Protected hostname checks add a rejection guard; file contents must reflect actual explicit runner authorization, never be invented by the agent. No authorization record was created.

User explicitly permits continuing dependent repository implementation/ordinary local tests while this evidence remains pending. See docs/qualification-runner.md; no runner assigned and no purchase/provisioning authorized. Phase/BUILD acceptance remains incomplete.

## Deviations and test discovery

The existing shared /tmp has only 31 MiB free. The caller selects a short owned project .scratch parent for the existing disposable-PG helper (module-local parent override); no shared files were deleted or helper rewritten. Long Unix socket roots fail before initdb. An initial real HTTP test exposed that ALLOWED_HOSTS is not automatically evaluated by these minimal views; explicit get_host validation fixed the failing control and the final suite passed.
