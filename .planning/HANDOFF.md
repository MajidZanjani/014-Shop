# Active SHB continuation

Current authority: [SHB revision 1.1](../014-Shop-SHB-Proposal-Revision-2026-10-30.md), SHA256 `ba801dff4adbfdcfa0f1e43cfe1f2d6963780476867da1b5e6f737230a472b5e`. The user explicitly replaces the earlier active product plan on 2026-10-30. Current routing: [STATE.md](STATE.md) / [ROADMAP.md](ROADMAP.md).

**Current development focus:** 3 — Supporting Hours Bundle catalog and approved pricing.

**Last fully completed phase:** 1 — documentary authority/reconciliation only; historical implementation evidence is not SHB acceptance.

**Current plan:** 03-01 — Supporting Hours Bundle catalog, 10/25-hour variants and common/ASIC form rules.

**Execution status:** in progress — SHB revision 1.1 replanned; implementing the single-product catalog and minimum forms; no live acceptance.

**Next implementation task:** Implement and verify SHB catalog/forms, then invitation-gated private storefront and old-IP route denial; continue FPGA/ASIC/coupon/payment integration under the revised plans.

**Recorded implementation:** cbf5941086172dd7cf53bca637e5a8529d22f23b

Replan is not product completion. Continue 03-01 immediately; then 04-01 access/private delivery and 07/08/10 workflows. No old Phase2 pause or historic time-ledger task routes execution.

SHB records only bundle size, quantity and hours bought in each order. SLL manually tracks used/remaining FPGA/ASIC hours and manually emails each task outside the shop. Preserve historical code/data/accepted obligations. Automated time credits/debits/reservations, cumulative balances, customer support/bundle panels/APIs, staff time entry and task-usage-email generation are deferred and are not SHB launch dependencies.

External dependencies and actual operation scope: docs/decisions.md. No independent runner or new external authority. Full commands/results will be recorded only after execution. Original snapshot and inventory: docs/archive/2026-10-30-before-shb/manifest.json.
