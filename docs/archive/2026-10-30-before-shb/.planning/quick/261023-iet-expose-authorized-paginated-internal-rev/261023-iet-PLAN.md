---
quick_id: 261023-iet
type: quick
phase: "07"
status: complete
---

# Browse all assigned internal review decisions

Continue implementation after4063465 sync; no routine pause. The request screen currently exposes only the latest20 internal decisions. Add a read-only paginated history route and link so earlier corrections/attribution remain reachable.

Reuse the existing reviewer assignment and parent/snapshot consistency, bounded committed review counter and review-history queryset. Review metadata follows the existing request summary permission: parent assignment permits outcome/scope/reviewer/time, never private business values/digests/MFA evidence. New route emits a closed projection and fixed labels; current business permission is not invented or widened. Shared canonical positive-version cursor with preparation history; strict GET/query handling and private headers.

Test actual review creation/corrections, older pages/new decisions, original reviewer attribution, private-scope revocation, cursor/parent/MFA/mode boundaries, no writes/forbidden outputs and committed-prefix concurrent supported review. Run focused/full local PostgreSQL/Gunicorn and exact source proof; no migration/approval/commercial effect. Reconcile planning, commit and immediately sync0/0, then continue without a context-clear request.
