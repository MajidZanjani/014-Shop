# T01 repository scope and execution provenance

Documentation only: sll-xspi-mc; sll-xspi-mc-support-10h; sll-xspi-mc-v1. Customer origin: https://shop.xspi.pro. Proposed staff origin: https://shop-admin.xspi.pro.

## Fresh checkout observations

Commands: git rev-parse HEAD; git branch --show-current; git status --porcelain=v1; git worktree list --porcelain; git ls-files; git check-ignore .env. Empty status means clean at observation. Metadata below describes the input revision, not an invented final output commit. Main checkout appears only in Git worktree metadata; its contents were not inspected.

```json
{
  "observed_utc": "2026-10-20T10:42:02Z",
  "head": "73e40d1b08e241d03cd3e115b74448879ce725df",
  "branch": "worktree-agent-p01-01-1792492750",
  "root": "/home/claude/project/014-Shop/.claude/worktrees/agent-p01-01-1792492750",
  "worktrees": "worktree /home/claude/project/014-Shop\nHEAD 95721fb78aeccc7da3170be011e774235d08c670\nbranch refs/heads/main\n\nworktree /home/claude/project/014-Shop/.claude/worktrees/agent-p01-01-1792492750\nHEAD 73e40d1b08e241d03cd3e115b74448879ce725df\nbranch refs/heads/worktree-agent-p01-01-1792492750",
  "status": "",
  "ignore": ".env",
  "inventory": [
    ".gitignore",
    ".planning/PROJECT.md",
    ".planning/REPLAN-VERIFICATION.md",
    ".planning/REQUIREMENTS.md",
    ".planning/ROADMAP.md",
    ".planning/SOURCE-MATRIX.md",
    ".planning/SOURCES.md",
    ".planning/STATE.md",
    ".planning/config.json",
    ".planning/phases/01-product-authority-repository-review-and-decision-register/01-01-PLAN.md",
    ".planning/phases/01-product-authority-repository-review-and-decision-register/01-02-PLAN.md",
    ".planning/phases/01-product-authority-repository-review-and-decision-register/01-CONTEXT.md",
    ".planning/phases/01-product-authority-repository-review-and-decision-register/01-PATTERNS.md",
    ".planning/phases/01-product-authority-repository-review-and-decision-register/01-PLAN-CHECK.md",
    ".planning/phases/01-product-authority-repository-review-and-decision-register/01-RESEARCH.md",
    ".planning/phases/01-product-authority-repository-review-and-decision-register/01-VALIDATION.md",
    ".planning/research/ARCHITECTURE.md",
    ".planning/research/FEATURES.md",
    ".planning/research/PITFALLS.md",
    ".planning/research/STACK.md",
    ".planning/research/SUMMARY.md",
    ".planning/state.json",
    "AGENTS.md",
    "README.md",
    "SLL-xSPI-MC-Shop-Codex-Handoff-2026-10-20.md",
    "SLL-xSPI-MC-Shop-Proposal-2026-10-20.md",
    "docs/decisions.md",
    "docs/product-source/SLL_xSPI_MC_Product_Page.md",
    "docs/product-source/verify_t01.py"
  ],
  "isolation": "fulfilled"
}
```

## Reset delta and preservation boundary

The current .planning/SOURCES.md Reset scope and .planning/REPLAN-VERIFICATION.md record replacement of old active planning and the prior decision register with the October 20 pair and exact embedded product authority. This is attribution to those reset records, not a new claim that this executor performed that reset. No historic source names or assumptions are imported. Old task numbers provide no new completion credit. Recoverable Git history is retained.

AGENTS.md supplies repository instructions; .gitignore excludes .env. Only exclusion metadata was read; no environment values were opened, sourced, copied or published. Tracked path inventory contains documentation/planning and no reusable application implementation. No application/data migration identified within the inspected checkout. External state is uninspected. Unrelated work is preserved. Initial status was clean; task 1 changed only its three declared files. No branches were switched or rewritten.

## Isolation and acceptance

Isolation fulfilled for this execution: the supplied separate worktree and agent branch match the observed revision in Git metadata. This establishes checkout separation, not external authorization. FLAGGED SRC-04/unclassified remains for end-of-phase human review. Source intent, preservation and evidence-honesty review remain manual gates. Full T01 acceptance awaits plan 01-02; T02+, business approvals, application and external operations remain pending.
