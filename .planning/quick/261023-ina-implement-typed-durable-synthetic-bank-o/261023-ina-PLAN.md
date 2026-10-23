---
quick_id: 261023-ina
type: quick
phase: "08"
status: complete
---

# Typed durable synthetic-bank boundary

Independent T08 slice authorized by the execution amendment and source permission for synthetic flows while live tax/legal inputs remain pending. Implement a separate payments app and fake-provider records, not Probe/FakeReceipt repurposing. No approved offer/order, real merchant/account capability, confirmed money, entitlement, public route or external bank is implied.

1. Add immutable typed start request/observation and explicit synthetic capabilities. Validate canonical UUID/reference, bounded synthetic merchant namespace/currency tokens and positive integer minor amounts; observations remain local-synthetic with financial-confirmation/effects false. Exact correlation is not authentication or commerce confirmation.
2. Persist immutable fake operation plus retained idempotency-key aliases under semantic merchant/reference uniqueness. Own short durable transactions; reject outer/manual transactions and live modes before calls. Support explicit authorized/captured/declined/pending synthetic statuses, timeout before commit and lost response after commit. Lookup performs no retry/write. Unsupported capture/refund/callback operations stay unsupported.
3. Use real PostgreSQL tests for replay/changed-key aliases, conflicting bodies/key reuse rollback, concurrent starts/key collisions, post-commit timeout lookup across connections, status/correlation/type boundaries, database constraints and no-write lookup. Generate migration on an owned synthetic cluster; integrate focused/full core-local and exact source proof. No real credentials/network/bank approval.
4. Mark only the independent Phase08 slice In Progress, preserve all acceptance gates/counts, reconcile planning, commit and immediately sync origin/main0/0. Continue without routine context-clear checkpoints.
