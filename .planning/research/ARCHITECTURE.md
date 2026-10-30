# SHB architecture

Current authority: [SHB revision 1.1](../../014-Shop-SHB-Proposal-Revision-2026-10-30.md), SHA256 `ba801dff4adbfdcfa0f1e43cfe1f2d6963780476867da1b5e6f737230a472b5e`. The user explicitly replaces the earlier active product plan on 2026-10-30. Current routing: [STATE.md](../STATE.md) / [ROADMAP.md](../ROADMAP.md).

Static Astro generates a private release snapshot; Django authorizes storefront and APIs, isolated gateway serves manifest-approved files only. React enhances the same form/backend. PostgreSQL and one leased worker retain durable commerce; invitations, ASIC offers and coupons reuse established access/order/quote/payment primitives. No request-time Node and no public static-origin bypass.

SHB records only bundle size, quantity and hours bought in each order. SLL manually tracks used/remaining FPGA/ASIC hours and manually emails each task outside the shop. Preserve historical code/data/accepted obligations. Automated time credits/debits/reservations, cumulative balances, customer support/bundle panels/APIs, staff time entry and task-usage-email generation are deferred and are not SHB launch dependencies.
