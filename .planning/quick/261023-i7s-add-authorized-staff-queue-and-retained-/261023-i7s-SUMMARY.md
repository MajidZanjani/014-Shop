---
quick_id: 261023-i7s
status: complete
implementation_commit: 4063465
---
# Authorized staff queue and retained preparation history

Staff assigned requests now have stable20-row older-page navigation in HTML/JSON; cursors require current assignment. A new authorized retained-preparation history reuses the existing scope filter, can browse an old granted scope independently of a newer current attachment, and exposes safe metadata only. CORE_LOCAL_PASS5 checks/283 tests (269 Django plus14 Gunicorn),75.493s; source166 files22 templates/no symlinks exact at /nix/store/71rlacdm91c40a1iv98d879z2adzmfzm-shop-python-source. No migration or commercial effect.

Queue pagination uses existing canonical UUID/current-resource anchor checks and (created_at,quotation UUID) keysets. New requests/timestamp ties do not shift older pages. HTML has older/newest navigation; JSON adds older while preserving existing item fields/limit.

GET /staff/quotation-requests/<UUID>/preparation-snapshots/history/ uses a canonical positive bounded version cursor anchored in the currently authorized rows. Shared authorized_history serves both existing capture-page metadata and history, retaining unbound scope0 and exact granted positive scope/owner/reference constraints. No current-scope grant substitution or automatic widening. New links connect assigned request/current/retained screens. Fixed metadata includes version/business/review/time only; private no-store/no-referrer/Vary Cookie/form-action none responses and no forms on history.

## Verification

Eight new real-PG tests cover ties/later inserts, unassigned/revoked/other-staff cursors, safe projections/no SQL writes, strict query/method/mode/MFA/customer boundaries, actual23-capture pagination, old/current scope changes and concurrent supported capture after parent lookup. First focused run exposed a new helper named capture shadowed by the existing fixture override_settings attribute; renamed capture_assessment, no runtime fix needed. Failed run is not evidence. Corrected focused27 Django plus14 Gunicorn=41 tests/18.506s passes. Final full283/75.493s passes, no skips; actual PostgreSQL18.6/UTF8,0012 application/no-drift checks pass. New module retained in full producer. Exact source166 files22 templates/no symlinks verified by relative paths and bytes. No frontend/proxy changes/rerun, migration or production transport/browser/off-host/recovery qualification.

## Continuation policy

User rejected frequent context-clear pauses and requested continuing implementation. The active execution amendment now records that task/commit completion is not context pressure. No exact percentage is available; no new clear/resume checkpoint is created. Previous one-shot handoff consumed. Continue across commits and syncs under existing authorization; preserve all external/protected/commercial gates.

Next: Continue staff workflow implementation: add authorized paginated internal review-decision history so decisions older than the20-row request summary remain reachable, preserving original attribution, committed parent review counters and private digest/MFA suppression in the history projection. Reuse existing reviewer/resource permissions and canonical bounded cursors. Do not rerun the completed unchanged-scope audit or pause at commit/task boundaries.
