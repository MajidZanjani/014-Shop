---
phase: quick
plan: 261028-htg
type: execute
wave: 1
depends_on: []
autonomous: true
requirements: [AUTH-01, AUTH-02, OPS-02, UAT-03]
files_modified:
  - backend/shop/catalog/views.py
  - backend/shop/catalog/tests.py
  - docs/local-recovery.md
---

<objective>
Reproduce and fence the finite configuration-draft list/get/save recovery boundary, preserving immutable unaccepted drafts and current catalog/retry semantics.
</objective>

<design_critique>
Live source inspection at5a1f5ea confirms entry-only local_customer checks before list/get queries and JSON parsing; the save transaction receives only cached request authority. First reproduce normal CSRF-checked saves/exact retries and private list/get reads after quarantine or quarantine/release. If confirmed, check and lock the originating epoch inside each existing bounded database operation, before draft queries. Materialize private responses under that lock. Preserve the original catalog admission order, immutable identity and owner isolation. No durable transaction nesting or provider I/O. Execute inline under the skill's spawn restriction.
</design_critique>

<tasks>
<task type="auto">
  <name>Reproduce and repair the three demonstrated draft API boundaries</name>
  <files>backend/shop/catalog/views.py, backend/shop/catalog/tests.py</files>
  <action>Add real-PostgreSQL customer HTTP controls using normal JSON parsing and CSRF. Trigger recovery after evaluation before save, and after entry authorization before private reads. Retain original response/committed-row failures before product edits. Recheck the originating epoch under its existing transaction-only lock before list/get/save/replay queries, serialize private payloads inside the bounded transaction and return the established fixed verification_required403 response after recovery. Cover fresh exact retries, owner isolation, unchanged catalog retry admission and independent PostgreSQL lock observations.</action>
  <verify>Owned project-local TMPDIR, retained hash-checked wheels and disposable prepared_database;120-second test bound. Expanded original-source control restores fixed bytes exactly.</verify>
  <done>Confirmed stale commands/reads deny without new drafts or private data, and fresh verified sessions preserve exact immutable identities.</done>
</task>
<task type="auto">
  <name>Qualify and record the finite local scope</name>
  <files>docs/local-recovery.md, .planning/STATE.md, .planning/ROADMAP.md, .planning/PROJECT.md, .planning/HANDOFF.md</files>
  <action>Run focused draft/cart/quotation/access recovery regressions, bounded full backend, supported complete-cart proxy/demo and exact inert source. Synchronize required manager-facing views/checkpoint, publish state.json, refresh the planning inventory and retain all actual/company gates before atomic implementation/completion commits. Push each commit normally under standing authority; respect actual review gates and avoid push-status-only commit chains. Audit any next source observation before a new task; do not manufacture speculative browser assertions.</action>
  <verify>At-most20 labels/120-second test batches; core900-second outer; source exactness; planning/source-authority and four planning/inventory tests; git diff --check.</verify>
  <done>Verified code and schema-backed quick completion are committed and actual remote synchronization is checked; no full Phase13 acceptance is inferred.</done>
</task>
</tasks>
