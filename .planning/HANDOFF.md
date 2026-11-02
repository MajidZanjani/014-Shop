# SHB continuation checkpoint

Current authority: [SHB revision1.1](../014-Shop-SHB-Proposal-Revision-2026-10-30.md). STATE.md / ROADMAP.md remain operative.

**Current development focus:** 7 — FPGA checkout, ASIC reviewed offers and scoped discounts.

**Last fully completed phase:** 1 — documentary authority only.

**Current plan:** 07-03 — matching dated ASIC offers, exact acceptance/payment and request-held coupon consumption verified; withdrawal/expiry/reissue and customer notices remain open.

**Execution status:** in progress — dated ASIC offers and exact acceptance/payment verified;458 tests/59 browser checks pass; remaining closure/notices and actual qualifications are pending.

**Next implementation task:** Implement explicit pre-acceptance ASIC request/offer withdrawal, final expiry/release and replacement/reissue, then remaining ordinary request/customer notices.

**Recorded implementation:** a227344f8c4c3c3cc2e599eab730525561f2140a

The current ASIC offer slice is verified at458 tests/59 actual browser checks, with identical332-backend/eight-script hashes; its implementation commit is being recorded. [Report and full commands](../docs/build/shb-asic-offers-2026-11-02.md). No parent SUMMARY/count change.

Next: explicit pre-acceptance request/offer withdrawal, final expiry/release, replacement/reissue and remaining ordinary request/customer notices. Expired unaccepted offers retain their concession until archived safe closing is implemented. Current accepted-checkout cancellation is complete; uncertain bank state stays lookup-only.

Retained tools remain separate synthetic evidence; normal Nix/source/runtime and all actual qualification gates are pending. Company inputs arrive later through docs/decisions.md. No real external action, .env or cache access. No owned job/process remains.
