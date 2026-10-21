---
phase: 02-reproducible-application-and-deployment-skeleton
plan: "09"
status: complete
requires: [02-08]
provides: [migrated-synthetic-probes, enqueue-cli]
requirements-completed: []
completed: 2026-10-21
---
# Phase 2 Plan 09: Persisted synthetic enqueue

Probe/FakeReceipt models and an actual Django-generated initial migration create only synthetic work/receipt tables. Probe version/evidence/state/attempt/claim consistency constraints and unique stable effect IDs are database-enforced. The bounded closed JSON CLI rejects unsupported versions/evidence, booleans, extra/duplicate keys, malformed/oversize inputs. Only local/synthetic environments may enqueue.

Final `check_worker.py --enqueue-only` in the pinned shell passed 4 checks and 11 tests in 6.127 seconds. A newly owned PostgreSQL 18.6 cluster/database was migrated; makemigrations --check --dry-run found no missing migration. Actual enqueue persisted one row, read through an independent psql session. Eight invalid payloads persisted nothing; two real uniqueness controls require PostgreSQL's actual duplicate-key error rather than accepting arbitrary SQL failures. No SQLite, skipped discovery, existing cluster or external effect.

This local slice is complete. Worker execution remains the next plan; inherited off-host core/runtime qualification remains pending. Shared BUILD requirements are incomplete. Scratch uses the short caller-selected owned project parent because shared /tmp lacks capacity; no shared cleanup or allocation changes.
