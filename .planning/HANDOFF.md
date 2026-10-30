# SHB active implementation handoff

Current authority: [SHB revision1.1](../014-Shop-SHB-Proposal-Revision-2026-10-30.md). STATE.md / ROADMAP.md remain operative.

**Current development focus:** 7 — FPGA checkout, ASIC reviewed offers and scoped discounts.

**Last fully completed phase:** 1 — documentary authority only.

**Current plan:** 07-02 — Scoped SHB discounts and reservations; previews and ASIC holds verified, matched outcomes pending.

**Execution status:** in progress — scoped coupon preview and atomic ASIC reservations verified; integrating matched lifecycle outcomes.

**Next implementation task:** Reuse the immutable checkout/acceptance/archive/payment interfaces for SHB and couple coupon consumption/release only to matched verified or safely closed outcomes; keep uncertain claims held.

**Recorded implementation:** f6bf69a096bc521cbe1929a3566059b49b27b8d1

The user resumed the explicit pause. Earlier04-01 verification repairs are committed/pushed. The new07-02 coupon slice is verified locally:250 tests including16 coupon and direct PostgreSQL race tests,33 Chromium checks in JavaScript/no-JavaScript,17 usable loopback checks and300-file/ten-import exact source. See [coupon evidence](../docs/build/shb-coupons-2026-10-30.md). Original code/rate/claim expiry changes cannot reprice a retried request. No reservation consumption/release or real payment is enabled.

Continue inline across commits;07-02 matched outcomes and07-03/04 accepted FPGA/assigned ASIC workflows remain open. No parent SUMMARY/full acceptance or completion count has been added. One-shot HANDOFF.json was consumed. The07 checkpoint contains the next action. All completed test/demo/browser processes returned; no external job exists.

Commercial/company inputs will arrive later in docs/decisions.md; no repeated request. No actual bank/mail/storage/host/DNS/TLS/provisioning action, .env read or support-time automation. Ordinary sandbox startup still denies the workspace; narrow local exec works. Unrelated http_cache.sqlite remains untouched. Ordinary non-force origin/main push after each project commit is authorized. No exact context percentage is supplied.
