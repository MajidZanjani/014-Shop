# Planning Sources

## Current authority

The user's 2026-10-20 instruction replaces the complete active planning baseline with the following two files. The embedded product is the sole product-definition source; the proposal supplies architecture and the handoff supplies task acceptance. Subsequent explicit user scope governs authorization. Report material source conflicts; do not revive superseded inputs.

| Source | Lines | UTF-8 bytes | SHA-256 |
|---|---:|---:|---|
| `SLL-xSPI-MC-Shop-Proposal-2026-10-20.md` | 1783 | 201117 | `d8db6b54e3e887ca940f0faff0949ca1a1fa2ce24c26075aabd78925f0f60356` |
| `SLL-xSPI-MC-Shop-Codex-Handoff-2026-10-20.md` | 264 | 42140 | `60e6af0fce6db7412408e04eceb0283881585a295f45cbba0607c4bde9f4227e` |
| `docs/product-source/SLL_xSPI_MC_Product_Page.md` | 449 | 23969 | `562dc4015c62f165df5df3e9ae1aab26b8102385d9dc76a556d5965ddc1a0263` |

Both October 20 documents were read completely, including the source appendix. Proposal and embedded source hashes match the package identities recorded in the handoff. The source's final newline is preserved. The separate third source file was extracted from the proposal, not obtained from another authority.

## Evidence policy

This is source-based planning. Supplied research is recorded as dated input, with no new live vendor/site/bank/account audit. Exact dependency versions/licences/support must be verified in T02; selected merchant capabilities in T09; current quote/stock/IPv4/disk/billing/DNS/TLS/ACL behavior in T11; retained storage/recovery in T12; release approvals in T14. No legal conclusion or provider performance guarantee is inferred.

The source is a written working draft, not a live-form audit. Counts are logical definitions and source rows: 3 vendors, 13 ordered families, 13 controls with repeated host rows, 19 business checkout groups, two helpers, four IP declarations and one independent marketing control. It supplies no fixed country list or tax-status enum. Price/schema/API examples are incomplete illustrative contracts. Missing price, recurrence, coverage, access or rights stays pending.

## Traceability

SOURCE-MATRIX.md preserves exact option/control/declaration and reset inventories with requirement links. REQUIREMENTS.md gives atomic IDs and one primary phase each. ROADMAP.md retains exact new handoff outputs, acceptance and evidence. docs/decisions.md is the single working P-01–P-12 register. Implementation evidence is planned under docs/implementation-evidence.md with per-task status, code/catalog/config revisions, commands/observations, environment, unresolved decisions and exact affected operations. Observed T01 documentation results are now recorded in docs/implementation-evidence.md; no later implementation results are claimed.

## Reset scope

All old .planning contents were removed before regeneration; docs/decisions.md was replaced and generated AGENTS.md context refreshed. No legacy source names, trial inventories/profiles or D-register carry active authority. The two supplied files are unchanged. Prior planning is recoverable from Git history and a temporary /tmp snapshot, outside active planning. No application or external state was changed.

## Reproducible local provenance check

Run `python3 docs/product-source/verify_t01.py source` from this checkout. It verifies raw package identities, bounded appendix equality and family-1-1 source/requirement locators. Passing proves documentation identity, not approval or live acceptance.

## T01 execution evidence

See [observed T01 record](../docs/implementation-evidence.md). Reproduce local checks with python3 docs/product-source/verify_t01.py all and python3 docs/product-source/verify_t01.py self-check. The former checks source/scope/inventory/decisions/evidence consistency; the latter asserts in-memory defect rejection with valid controls and unchanged canonical bytes. These checks do not independently attest to the honesty of recorded observations. All P decisions and manual flagged judgments remain pending; T02–T14 remain unexecuted.
