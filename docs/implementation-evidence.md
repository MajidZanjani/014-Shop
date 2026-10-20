# T01 local documentation execution evidence

Scope: October 20 source pair and embedded product only. No application or external operations.
Full T01 acceptance is conditional manual review; T02–T14 remain unexecuted.

## Observed revision and environment

The observed HEAD below is Task 2's committed revision, with Task 3 checker/ledger edits identified by scoped status and SHA-256. These are observed input/document revisions, not an invented final commit. This evidence file excludes its own hash to avoid self-reference. Final task and summary commits are reported in the plan summary and Git history.

```json
{
  "observed_utc": "2026-10-20T10:51:23Z",
  "head": "713e5f74495be59e6e40feba6c3998502fb9b920",
  "branch": "worktree-agent-p01-02-1792493124",
  "root": "/home/claude/project/014-Shop/.claude/worktrees/agent-p01-02-1792493124",
  "status": "M .planning/SOURCES.md\n M docs/product-source/verify_t01.py",
  "environment": {
    "python": "3.13.13",
    "git": "git version 2.54.0",
    "platform": "Linux"
  },
  "isolation": "separate worktree observed; manual judgment pending",
  "acceptance": "conditional manual review",
  "tasks": {
    "01-01-01": "complete per committed 01-01 summary; 73e40d1; not rerun as a task",
    "01-01-02": "complete per committed 01-01 summary; 761b536; not rerun as a task",
    "01-01-03": "complete per committed 01-01 summary; bd04b75; not rerun as a task",
    "01-02-01": "complete; 7233b7e; 78 bounded traces",
    "01-02-02": "complete; 713e5f7; 12 aligned pending decision rows",
    "01-02-03": "complete local documentation checks; full acceptance conditional on manual review"
  },
  "commands": {
    "source": {
      "command": "python3 docs/product-source/verify_t01.py source",
      "exit": 0,
      "checks": 18
    },
    "scope": {
      "command": "python3 docs/product-source/verify_t01.py scope",
      "exit": 0,
      "checks": 25
    },
    "inventory": {
      "command": "python3 docs/product-source/verify_t01.py inventory",
      "exit": 0,
      "checks": 279
    },
    "decisions": {
      "command": "python3 docs/product-source/verify_t01.py decisions",
      "exit": 0,
      "checks": 88
    }
  },
  "artifacts": {
    "docs/product-source/verify_t01.py": "73602f2c396d401273dab29357af1fbbc6372f69040d651221a45da96d1c442e",
    ".planning/SOURCE-MATRIX.md": "cec2a1dbf8786aff51d589ba4a6b71dbd18a4cc88efa249208ed66a6b9beeaa3",
    "docs/decisions.md": "c8eafc9a0f11412b4befa2845dc0b7ce371c816d88d4fcc8c0ee06bd93cc2ece",
    "docs/product-source/t01-scope.md": "1fb740979566fe73aa81dc237ad4dd5dd99ca306d3f7fdd0f006886f4ef9d3bc",
    ".planning/SOURCES.md": "f6acf8f275a7302876d7d4abc8eb6ae10544e68f2e750364791595ee69ae204e"
  }
}
```

## Outputs and source identity

- [Source matrix](../.planning/SOURCE-MATRIX.md): 78 ordered supplemental records: 3 vendors, 13 families, 3 terms, 4 bands, 2 access modes, 13 logical controls, 19 business groups, 4 declarations, 1 marketing, 14 resets and 2 helpers. Original tables preserve full requiredness and proposed IDs; the original family tracer remains.
- [Decision register](decisions.md): exactly twelve eight-column rows with role-only owners, targeted phase/operation scopes, Pending and None supplied.
- [Checker](product-source/verify_t01.py): docs-local Python standard library; source, scope, inventory, decisions, all and self-check modes.
- [Scope record](product-source/t01-scope.md): prior wave's dated checkout/reset evidence, reused without claiming its task execution again.
- [Source ledger](../.planning/SOURCES.md): proposal d8db6b54e3e887ca940f0faff0949ca1a1fa2ce24c26075aabd78925f0f60356 (201117 bytes), handoff 60e6af0fce6db7412408e04eceb0283881585a295f45cbba0607c4bde9f4227e (42140 bytes), embedded product 562dc4015c62f165df5df3e9ae1aab26b8102385d9dc76a556d5965ddc1a0263 (23969 bytes). Source mode observed exact hashes, final newlines and appendix equality.

All four commands in metadata were run separately and exited zero with the shown counts after the Task 3 checker edit. Earlier Task 1 self-check rejected 33 mutations; Task 2 rejected 40, including its then-unimplemented all mode. Those staged counts are historical, not the final suite count.

## Register freshness and read-only behavior

Before replacement SHA-256: 55a30ef656b7e065086593aa08921c2a4ba9ede3a062d2e67befc510eba5fc48.
After replacement SHA-256: c8eafc9a0f11412b4befa2845dc0b7ce371c816d88d4fcc8c0ee06bd93cc2ece.
The write checked the original bytes immediately before replacement; no concurrent change was observed. Before Task 2 staging, the current bytes matched the after fingerprint and decisions mode passed again. Repeated in-memory validation and disk-byte comparison exercise read-only behavior, not a claim of a concurrent-writer stress test.

## Manual observations and remaining gates

Source intent: proposal controls/reset rows express intended behavior, not working UI. Intended application has unspecified source requiredness; mandatory enforcement is proposed. Repeated fixed-host references/IDs remain separate; floating seats use one drafted server. Both helpers are independent, country/tax enums absent, four declarations remain separate from optional unticked marketing and privacy. Coverage, access, rates, recurrence, rights and legal texts remain pending.

P-01–P-12 all remain pending. Exact live operations and unaffected preparation are in docs/decisions.md; its phase mappings are planning inferences. P-01 coverage/combinations, P-02 payable rates, P-03 rights, P-04 host/key scope, P-05 paid support/work policy, P-06 actual release/customer promises, P-07 selected bank/acquiring, P-08 acceptance/tax/collection, P-09 retained evidence/recovery, P-10 provisioned tests/billing, P-11 DNS/certificate activation and P-12 real mail/staff/operating readiness remain gated.

Execution isolation: the first read-only branch/base assertion passed against 87a701eca62cf9acd64dba67f7dfc8215d44865b. Supplied root and agent branch were rechecked before each commit; no branch switch, main checkout content inspection or ref rewrite occurred. The default sandbox failed before command execution with bwrap Permission denied for the supplied worktree; approved elevated calls performed the scoped work. No .env values were read, sourced, copied or published. Initial worktree status was clean; only declared files changed.

End-of-phase manual judgments remain explicit: FLAGGED SRC-04/unclassified; source intent; approval scope; execution isolation; source preservation prohibition (01-01); pending decisions prohibition (01-02). Git metadata and structural checks support but cannot independently resolve those judgments. Independent verification must decide acceptance.

Local documentation proof is distinct from synthetic application proof, selected-bank sandbox, actual OVH and production proof. None of those later environments was exercised; no compatibility, saleable catalog, business approval or production readiness follows from these results. All pending/manual/external gates remain open.

## Final observed checks

Recorded 2026-10-20T10:51:49Z after actual execution:

- python3 docs/product-source/verify_t01.py all: exit 0; source 18, scope 25, inventory 279, decisions 88, evidence 38 executed checks.
- python3 docs/product-source/verify_t01.py self-check: exit 0; 54 asserted in-memory rejections; valid controls and repeated read-only register validation passed; canonical source/register bytes unchanged.
- Scoped git diff --check for SOURCES, SOURCE-MATRIX, decisions, scope, checker and this record: exit 0.

No unperformed final commit is identified by this record. Structural evidence checks cannot prove the observations above independently.
