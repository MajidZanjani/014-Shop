> Historical October 20 observations retained unchanged below. Current authority is .planning/SOURCES.md; hosting changed on October 21. These results do not establish current rootless/mx1/protection compliance. The old executable verifier is explicitly migrated by 02-00; no current pass is claimed here.

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
    "docs/product-source/verify_t01.py": "4db4e89050d5d461f4d640b44143128f573dc04ad88b489c343a0def6656657b",
    ".planning/SOURCE-MATRIX.md": "cec2a1dbf8786aff51d589ba4a6b71dbd18a4cc88efa249208ed66a6b9beeaa3",
    "docs/decisions.md": "c8eafc9a0f11412b4befa2845dc0b7ce371c816d88d4fcc8c0ee06bd93cc2ece",
    "docs/product-source/t01-scope.md": "1fb740979566fe73aa81dc237ad4dd5dd99ca306d3f7fdd0f006886f4ef9d3bc",
    ".planning/SOURCES.md": "f6acf8f275a7302876d7d4abc8eb6ae10544e68f2e750364791595ee69ae204e"
  },
  "post_merge_repair": {
    "observed_utc": "2026-10-20T10:55:12Z",
    "head": "87377f9e91a89aeef34d5e2a2605fce0a3cfbea6",
    "branch": "main",
    "root": "/home/claude/project/014-Shop",
    "previous_checker_sha256": "73602f2c396d401273dab29357af1fbbc6372f69040d651221a45da96d1c442e",
    "change": "Validate recorded historical worktree identity instead of equality to current checkout; allow requirement lifecycle statuses; add relocation/rejection regression checks."
  },
  "artifact_revision": "25b8417b0f9f0c59685bebb1c88811aa9e98b626"
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

## Post-merge repair observations

The original worktree passed its checks, but the first merged-checkout all/self-check runs on main failed with `evidence worktree identity`. The validator incorrectly equated the historical execution root to its current checkout. The repair validates the recorded absolute root/isolated branch relationship without opening that historical path. Its positive relocated-root control and three invalid-root/branch rejection probes run in memory. Source-to-requirement checks now accept documented lifecycle statuses so future completion tracking does not invalidate source identity.

The metadata keeps the original execution identity and records the later repair separately under post_merge_repair, including the previous checker hash. Only the checker artifact hash is refreshed to the repaired code; original task observations above remain historical. No original source bytes, approvals or original scope facts changed. Post-merge checker results are recorded after the actual repair run.

Observed repaired-checkout results: all mode exited 0 with source 18, scope 25, inventory 279, decisions 88 and evidence 38 checks; self-check exited 0 with 57 asserted rejections and a valid relocated-history control. Scoped whitespace check exited 0.

## Historical artifact and record-boundary repair

Independent review CR-01 and CR-02 reproduced two future-phase lifecycle failures. The original execution/post-merge artifact hashes are now anchored to commit 25b8417b0f9f0c59685bebb1c88811aa9e98b626, where all five recorded artifact bytes are preserved. The checker reads only those allowlisted Git objects after verifying the full commit is reachable; a shallow clone lacking the recorded commit fails with an explicit missing-history contract instead of claiming verified provenance. Current source, inventory and decision rules still validate current inputs separately. A later ledger/register edit no longer requires rewriting T01 observations.

T01 metadata parsing is now bounded by task-numbered evidence headings. Later T02 JSON blocks are independent, while duplicate JSON inside T01 is rejected. In-memory regression controls cover a later ledger note, a structurally valid synthetic approval record, later-phase JSON, duplicate T01 metadata and unavailable historical commits. The synthetic approval control is never persisted to the live register and grants no authority. Actual production/business statuses remain pending.

Observed lifecycle-repair results on main: all exited 0 (source 18, scope 25, inventory 279, decisions 88, evidence 39); self-check exited 0 with 59 asserted rejections and positive historical-relocation, later-ledger, later-register and later-phase-JSON controls. Whitespace checks passed.

## T02 02-00 current-source migration evidence

Current source/scope/inventory/decisions modes were actually run with the counts below. This is local documentation evidence only. Existing T01 observations above remain historical, not new acceptance or host inspection. Artifact hashes identify the committed migration inputs; the evidence record excludes its own hash. The hosting choice is selected; host protection, rootlessness, runtime/ingress and production qualification remain pending.

```json
{
  "schema_version": 1,
  "observed_utc": "2026-10-21T06:20:22Z",
  "head": "1ea8fabd32780199051fda61fea4b4e30ae3bdc7",
  "branch": "worktree-agent-p02-00-oct21",
  "root": "/home/claude/project/014-Shop/.claude/worktrees/agent-p02-00-oct21",
  "status": "?? docs/product-source/__pycache__/",
  "artifact_revision": "1ea8fabd32780199051fda61fea4b4e30ae3bdc7",
  "artifacts": {
    "docs/product-source/verify_t01.py": "3dc3194d3f03cf35dc3dfb936c0210e221a143e3809f88a816e3b1e7fd3ffcb4",
    "docs/product-source/t01-scope.md": "e20afc470cc860c14cc975eb4346ba78e2c25756f60fa96ca6bda763f94ccc8a",
    ".planning/SOURCE-MATRIX.md": "319d29caf4706f64017348c37e1cbd6ad59231db909134b21c078cc08dbdbec3",
    "docs/decisions.md": "28708da84758fc0c62a3ee01a5baeb200b302810b06dcea74289be733da8cc71",
    ".planning/SOURCES.md": "8d273cb093dafcb53a384dafef4bf838bb0f8f14374a1972b7484d3a0aa5a15c"
  },
  "commands": {
    "source": {
      "command": "python3 docs/product-source/verify_t01.py source",
      "exit": 0,
      "checks": 20
    },
    "scope": {
      "command": "python3 docs/product-source/verify_t01.py scope",
      "exit": 0,
      "checks": 27
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
  "evidence_class": "local-documentation",
  "host_inspected": false,
  "production_qualified": false,
  "approval_scope": "P-10 hosting direction selected; host qualification pending",
  "sources": {
    "SLL-xSPI-MC-Shop-Proposal-2026-10-21.md": "26a7359624ea4a9625005b39a3fa43beff01c31c830e3b6f122c1ad7417787d0",
    "SLL-xSPI-MC-Shop-Codex-Handoff-2026-10-21.md": "3ff0ecffe4432514bab4a29d500fff05c5537a79c0a8fa494faeb8dfda1c6fac",
    "docs/product-source/SLL_xSPI_MC_Product_Page.md": "562dc4015c62f165df5df3e9ae1aab26b8102385d9dc76a556d5965ddc1a0263"
  }
}
```

Final observed migration checks: all exited 0 with source 20, scope 27, inventory 279, decisions 88, historical evidence 39 and current evidence 18 checks. Self-check exited 0 with 71 asserted in-memory rejections, including obsolete source filenames, false host ownership/qualification, P-10 blanket approval and invalid current evidence. Canonical source, decision and historical records were unchanged by checks. The historical source-ledger evidence link is checked against its recorded Git revision rather than imposed on the current ledger. No host or runtime qualification was performed.
