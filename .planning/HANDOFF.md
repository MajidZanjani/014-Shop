# SHB continuation checkpoint

Current authority: [SHB revision1.1](../014-Shop-SHB-Proposal-Revision-2026-10-30.md). STATE.md / ROADMAP.md remain operative.

**Current development focus:** 7 — FPGA checkout, ASIC reviewed offers and scoped discounts.

**Last fully completed phase:** 1 — documentary authority only.

**Current plan:** 07-03 — SHB immutable FPGA checkout/acceptance and fake payment verified locally; paid-order finalization remains open.

**Execution status:** in progress — FPGA checkout slice verified with390 local tests and41 browser checks; full paid workflow and Nix qualification remain pending.

**Next implementation task:** Complete per-order FPGA paid finalization and coupon consumption with archived acceptance/captured payment, staff visibility and durable transaction notice; then continue matching dated ASIC offers.

**Recorded implementation:** 551fd1326f84871925680eab45f7202068c54cae

The saved six-file WIP now has guarded migrations, protected routes/templates, signed exact review and repeat-safe archived FPGA acceptance/fake payment. The final390-test run includes71 SHB/20 checkout cases; actual Chromium151/Node24.15 passes41 native checks in two modes. Exact current hashes cover312 backend files/eight scripts. Full details, fixed failures and reproduction commands: [checkout report](../docs/build/shb-checkout-2026-11-02.md).

Coupons remain held after fake payment; paid-order finalization, coupon consumption/safe closure, staff purchase visibility/ordinary transaction notices and matching dated ASIC offers are unfinished. No parent SUMMARY/FULL_PASS/requirement completion or count change:11/42 records,1/14 documentary phases. Support-time tracking and task emails stay manual.

The original HANDOFF.json was consumed on resume. A new context-pressure checkpoint follows after the implementation commit. Exact percentage is unavailable. Current Nix development/source builds cannot resolve pinned dependencies; the artifact-verified retained-tool runner is separate local evidence. It neither changes pins nor establishes OCI/runtime qualification. No .env, actual bank/mail/storage/protected host/DNS/TLS action or paid provision. User company inputs arrive later; no repeat request. http_cache.sqlite remains untouched.
