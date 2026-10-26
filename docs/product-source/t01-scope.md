> Current purchase/support/staged-delivery delta: [final26October revision2](../../.planning/PURCHASE-FLOW-AMENDMENT.md). Baseline source/evidence below retains its exact scope; it does not require a universal engineering questionnaire, portal or custom-board review.

> Historical October 20 observations retained unchanged below. Current authority is .planning/SOURCES.md; hosting changed on October 21. These results do not establish current rootless/mx1/protection compliance. The old executable verifier is explicitly migrated by 02-00; no current pass is claimed here.

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

## Observed local verification

Observed UTC: 2026-10-20T10:42:49Z; Python 3.13.13. Commands: python3 docs/product-source/verify_t01.py {source,scope,self-check} (each mode separately). Combined measured wall time: 0.073 seconds.

- PASS source: 18 executed checks (local documentation only)
- PASS scope: 25 executed checks (local documentation only)
- PASS self-check: 23 asserted rejections; valid source/scope and pending controls passed

Canonical source identities remained exact after the probes. All mutations were in memory; no canonical input was changed. inventory, decisions and all deliberately fail as unimplemented until 01-02. Isolation is fulfilled as recorded above; manual scope/evidence review and full inventory/register/evidence acceptance remain pending. These are local documentation checks, with no bank, OVH or production qualification.

## October 21 current checkout scope

Current source: SLL-xSPI-MC-Shop-Proposal-2026-10-21.md and SLL-xSPI-MC-Shop-Codex-Handoff-2026-10-21.md. Product/profile IDs: sll-xspi-mc, sll-xspi-mc-support-10h, sll-xspi-mc-v1. Customer https://shop.xspi.pro; proposed staff https://shop-admin.xspi.pro.

Old task numbers provide no new completion credit. Recoverable Git history is retained. Unrelated work is preserved. External state is uninspected. Application/runtime acceptance remains pending. Protected-resource ownership is unverified; no host mutation is authorized by this record.

Metadata records the actual input checkout/revision and Git path/status observations, not a future final commit. No host/service state or .env values were read. The separate worktree was created through GSD from current main; retained older worktrees are not reused or redispatched. Historical scope and observations above remain unchanged and apply to their original revision only.

```json
{
  "observed_utc": "2026-10-21T06:19:34Z",
  "head": "1397c66518a5cbb7e1c21dd594280ef4bd7a672d",
  "branch": "worktree-agent-p02-00-oct21",
  "root": "/home/claude/project/014-Shop/.claude/worktrees/agent-p02-00-oct21",
  "worktrees": "worktree /home/claude/project/014-Shop\nHEAD 1397c66518a5cbb7e1c21dd594280ef4bd7a672d\nbranch refs/heads/main\n\nworktree /home/claude/project/014-Shop/.claude/worktrees/agent-p02-00-oct21\nHEAD 1397c66518a5cbb7e1c21dd594280ef4bd7a672d\nbranch refs/heads/worktree-agent-p02-00-oct21\n\nworktree /home/claude/project/014-Shop/.claude/worktrees/agent-p02-03-1792504881\nHEAD 2c64d9ba3e5a227df6424b8b8c30355a26e2c99c\nbranch refs/heads/worktree-agent-p02-03-1792504881\n\nworktree /home/claude/project/014-Shop/.claude/worktrees/agent-p02-05-1792504881\nHEAD 2c64d9ba3e5a227df6424b8b8c30355a26e2c99c\nbranch refs/heads/worktree-agent-p02-05-1792504881",
  "status": "M docs/product-source/verify_t01.py",
  "ignore": ".env",
  "inventory": [
    ".gitignore",
    ".planning/HANDOFF.json",
    ".planning/PROJECT.md",
    ".planning/REPLAN-VERIFICATION.md",
    ".planning/REQUIREMENTS.md",
    ".planning/ROADMAP.md",
    ".planning/SOURCE-MATRIX.md",
    ".planning/SOURCES.md",
    ".planning/STATE.md",
    ".planning/config.json",
    ".planning/phases/01-product-authority-repository-review-and-decision-register/01-01-PLAN.md",
    ".planning/phases/01-product-authority-repository-review-and-decision-register/01-01-SUMMARY.md",
    ".planning/phases/01-product-authority-repository-review-and-decision-register/01-02-PLAN.md",
    ".planning/phases/01-product-authority-repository-review-and-decision-register/01-02-SUMMARY.md",
    ".planning/phases/01-product-authority-repository-review-and-decision-register/01-VERIFICATION.md",
    ".planning/phases/02-reproducible-application-and-deployment-skeleton/.continue-here.md",
    ".planning/phases/02-reproducible-application-and-deployment-skeleton/02-00-PLAN.md",
    ".planning/phases/02-reproducible-application-and-deployment-skeleton/02-01-PLAN.md",
    ".planning/phases/02-reproducible-application-and-deployment-skeleton/02-01-SUMMARY.md",
    ".planning/phases/02-reproducible-application-and-deployment-skeleton/02-02-PLAN.md",
    ".planning/phases/02-reproducible-application-and-deployment-skeleton/02-02-SUMMARY.md",
    ".planning/phases/02-reproducible-application-and-deployment-skeleton/02-03-PLAN.md",
    ".planning/phases/02-reproducible-application-and-deployment-skeleton/02-04-PLAN.md",
    ".planning/phases/02-reproducible-application-and-deployment-skeleton/02-05-PLAN.md",
    ".planning/phases/02-reproducible-application-and-deployment-skeleton/02-06-PLAN.md",
    ".planning/phases/02-reproducible-application-and-deployment-skeleton/02-07-PLAN.md",
    ".planning/phases/02-reproducible-application-and-deployment-skeleton/02-08-PLAN.md",
    ".planning/phases/02-reproducible-application-and-deployment-skeleton/02-09-PLAN.md",
    ".planning/phases/02-reproducible-application-and-deployment-skeleton/02-10-PLAN.md",
    ".planning/phases/02-reproducible-application-and-deployment-skeleton/02-11-PLAN.md",
    ".planning/phases/02-reproducible-application-and-deployment-skeleton/02-12-PLAN.md",
    ".planning/phases/02-reproducible-application-and-deployment-skeleton/02-13-PLAN.md",
    ".planning/phases/02-reproducible-application-and-deployment-skeleton/02-14-PLAN.md",
    ".planning/phases/02-reproducible-application-and-deployment-skeleton/02-15-PLAN.md",
    ".planning/phases/02-reproducible-application-and-deployment-skeleton/02-16-PLAN.md",
    ".planning/phases/02-reproducible-application-and-deployment-skeleton/02-17-PLAN.md",
    ".planning/phases/02-reproducible-application-and-deployment-skeleton/02-CHECK.md",
    ".planning/phases/02-reproducible-application-and-deployment-skeleton/02-CONTEXT.md",
    ".planning/phases/02-reproducible-application-and-deployment-skeleton/02-PATTERNS.md",
    ".planning/phases/02-reproducible-application-and-deployment-skeleton/02-RESEARCH.md",
    ".planning/phases/02-reproducible-application-and-deployment-skeleton/02-VALIDATION.md",
    ".planning/phases/02-reproducible-application-and-deployment-skeleton/COVERAGE.md",
    ".planning/quick/261021-8cb-replan-from-october-21-proposal-and-hand/261021-8cb-PLAN.md",
    ".planning/quick/261021-8cb-replan-from-october-21-proposal-and-hand/261021-8cb-SUMMARY.md",
    ".planning/quick/261021-8cb-replan-from-october-21-proposal-and-hand/261021-8cb-VERIFICATION.json",
    ".planning/research/ARCHITECTURE.md",
    ".planning/research/FEATURES.md",
    ".planning/research/PITFALLS.md",
    ".planning/research/STACK.md",
    ".planning/research/SUMMARY.md",
    ".planning/state.json",
    "AGENTS.md",
    "README.md",
    "SLL-xSPI-MC-Shop-Codex-Handoff-2026-10-21.md",
    "SLL-xSPI-MC-Shop-Proposal-2026-10-21.md",
    "docs/archive/2026-10-20-planning/README.md",
    "docs/archive/2026-10-20-planning/docs/decisions.md",
    "docs/archive/2026-10-20-planning/docs/implementation-evidence.md",
    "docs/archive/2026-10-20-planning/docs/product-source/t01-scope.md",
    "docs/archive/2026-10-20-planning/planning/HANDOFF.json",
    "docs/archive/2026-10-20-planning/planning/PROJECT.md",
    "docs/archive/2026-10-20-planning/planning/REPLAN-VERIFICATION.md",
    "docs/archive/2026-10-20-planning/planning/REQUIREMENTS.md",
    "docs/archive/2026-10-20-planning/planning/ROADMAP.md",
    "docs/archive/2026-10-20-planning/planning/SOURCE-MATRIX.md",
    "docs/archive/2026-10-20-planning/planning/SOURCES.md",
    "docs/archive/2026-10-20-planning/planning/STATE.md",
    "docs/archive/2026-10-20-planning/planning/phases/01-product-authority-repository-review-and-decision-register/01-01-PLAN.md",
    "docs/archive/2026-10-20-planning/planning/phases/01-product-authority-repository-review-and-decision-register/01-01-SUMMARY.md",
    "docs/archive/2026-10-20-planning/planning/phases/01-product-authority-repository-review-and-decision-register/01-02-PLAN.md",
    "docs/archive/2026-10-20-planning/planning/phases/01-product-authority-repository-review-and-decision-register/01-02-SUMMARY.md",
    "docs/archive/2026-10-20-planning/planning/phases/01-product-authority-repository-review-and-decision-register/01-CONTEXT.md",
    "docs/archive/2026-10-20-planning/planning/phases/01-product-authority-repository-review-and-decision-register/01-PATTERNS.md",
    "docs/archive/2026-10-20-planning/planning/phases/01-product-authority-repository-review-and-decision-register/01-PLAN-CHECK.md",
    "docs/archive/2026-10-20-planning/planning/phases/01-product-authority-repository-review-and-decision-register/01-RESEARCH.md",
    "docs/archive/2026-10-20-planning/planning/phases/01-product-authority-repository-review-and-decision-register/01-REVIEW-DISPOSITION.md",
    "docs/archive/2026-10-20-planning/planning/phases/01-product-authority-repository-review-and-decision-register/01-REVIEW.md",
    "docs/archive/2026-10-20-planning/planning/phases/01-product-authority-repository-review-and-decision-register/01-SECURITY.md",
    "docs/archive/2026-10-20-planning/planning/phases/01-product-authority-repository-review-and-decision-register/01-UAT.md",
    "docs/archive/2026-10-20-planning/planning/phases/01-product-authority-repository-review-and-decision-register/01-VALIDATION.md",
    "docs/archive/2026-10-20-planning/planning/phases/01-product-authority-repository-review-and-decision-register/01-VERIFICATION.md",
    "docs/archive/2026-10-20-planning/planning/phases/02-reproducible-application-and-deployment-skeleton/.continue-here.md",
    "docs/archive/2026-10-20-planning/planning/phases/02-reproducible-application-and-deployment-skeleton/02-01-CHECKPOINT.md",
    "docs/archive/2026-10-20-planning/planning/phases/02-reproducible-application-and-deployment-skeleton/02-01-PLAN.md",
    "docs/archive/2026-10-20-planning/planning/phases/02-reproducible-application-and-deployment-skeleton/02-01-RED.json",
    "docs/archive/2026-10-20-planning/planning/phases/02-reproducible-application-and-deployment-skeleton/02-01-SUMMARY.md",
    "docs/archive/2026-10-20-planning/planning/phases/02-reproducible-application-and-deployment-skeleton/02-02-BOOTSTRAP.json",
    "docs/archive/2026-10-20-planning/planning/phases/02-reproducible-application-and-deployment-skeleton/02-02-PLAN.md",
    "docs/archive/2026-10-20-planning/planning/phases/02-reproducible-application-and-deployment-skeleton/02-02-POSTGRESQL.json",
    "docs/archive/2026-10-20-planning/planning/phases/02-reproducible-application-and-deployment-skeleton/02-02-RED.json",
    "docs/archive/2026-10-20-planning/planning/phases/02-reproducible-application-and-deployment-skeleton/02-02-SUMMARY.md",
    "docs/archive/2026-10-20-planning/planning/phases/02-reproducible-application-and-deployment-skeleton/02-02-VERIFICATION.json",
    "docs/archive/2026-10-20-planning/planning/phases/02-reproducible-application-and-deployment-skeleton/02-02-final-bootstrap.log",
    "docs/archive/2026-10-20-planning/planning/phases/02-reproducible-application-and-deployment-skeleton/02-02-final-runtime.log",
    "docs/archive/2026-10-20-planning/planning/phases/02-reproducible-application-and-deployment-skeleton/02-02-native-build.log",
    "docs/archive/2026-10-20-planning/planning/phases/02-reproducible-application-and-deployment-skeleton/02-02-native-repair.log",
    "docs/archive/2026-10-20-planning/planning/phases/02-reproducible-application-and-deployment-skeleton/02-03-PLAN.md",
    "docs/archive/2026-10-20-planning/planning/phases/02-reproducible-application-and-deployment-skeleton/02-04-PLAN.md",
    "docs/archive/2026-10-20-planning/planning/phases/02-reproducible-application-and-deployment-skeleton/02-05-PLAN.md",
    "docs/archive/2026-10-20-planning/planning/phases/02-reproducible-application-and-deployment-skeleton/02-06-PLAN.md",
    "docs/archive/2026-10-20-planning/planning/phases/02-reproducible-application-and-deployment-skeleton/02-07-PLAN.md",
    "docs/archive/2026-10-20-planning/planning/phases/02-reproducible-application-and-deployment-skeleton/02-08-PLAN.md",
    "docs/archive/2026-10-20-planning/planning/phases/02-reproducible-application-and-deployment-skeleton/02-09-PLAN.md",
    "docs/archive/2026-10-20-planning/planning/phases/02-reproducible-application-and-deployment-skeleton/02-10-PLAN.md",
    "docs/archive/2026-10-20-planning/planning/phases/02-reproducible-application-and-deployment-skeleton/02-11-PLAN.md",
    "docs/archive/2026-10-20-planning/planning/phases/02-reproducible-application-and-deployment-skeleton/02-12-PLAN.md",
    "docs/archive/2026-10-20-planning/planning/phases/02-reproducible-application-and-deployment-skeleton/02-13-PLAN.md",
    "docs/archive/2026-10-20-planning/planning/phases/02-reproducible-application-and-deployment-skeleton/02-14-PLAN.md",
    "docs/archive/2026-10-20-planning/planning/phases/02-reproducible-application-and-deployment-skeleton/02-15-PLAN.md",
    "docs/archive/2026-10-20-planning/planning/phases/02-reproducible-application-and-deployment-skeleton/02-16-PLAN.md",
    "docs/archive/2026-10-20-planning/planning/phases/02-reproducible-application-and-deployment-skeleton/02-17-PLAN.md",
    "docs/archive/2026-10-20-planning/planning/phases/02-reproducible-application-and-deployment-skeleton/02-CHECK.md",
    "docs/archive/2026-10-20-planning/planning/phases/02-reproducible-application-and-deployment-skeleton/02-EDGE-PROBE.json",
    "docs/archive/2026-10-20-planning/planning/phases/02-reproducible-application-and-deployment-skeleton/02-PATTERNS.md",
    "docs/archive/2026-10-20-planning/planning/phases/02-reproducible-application-and-deployment-skeleton/02-RESEARCH.md",
    "docs/archive/2026-10-20-planning/planning/phases/02-reproducible-application-and-deployment-skeleton/02-VALIDATION.md",
    "docs/archive/2026-10-20-planning/planning/phases/02-reproducible-application-and-deployment-skeleton/COVERAGE.md",
    "docs/archive/2026-10-20-planning/planning/research/ARCHITECTURE.md",
    "docs/archive/2026-10-20-planning/planning/research/FEATURES.md",
    "docs/archive/2026-10-20-planning/planning/research/PITFALLS.md",
    "docs/archive/2026-10-20-planning/planning/research/STACK.md",
    "docs/archive/2026-10-20-planning/planning/research/SUMMARY.md",
    "docs/archive/2026-10-20-planning/planning/state.json",
    "docs/build/dependency-candidates.json",
    "docs/decisions.md",
    "docs/evidence/t02/dependency-review.json",
    "docs/evidence/t02/dependency-review.md",
    "docs/implementation-evidence.md",
    "docs/product-source/SLL_xSPI_MC_Product_Page.md",
    "docs/product-source/t01-scope.md",
    "docs/product-source/verify_t01.py",
    "ops/nixos/flake.lock",
    "ops/nixos/flake.nix",
    "scripts/check.py",
    "scripts/dev_postgres.py",
    "scripts/qualify_dependencies.py",
    "tests/test_check.py",
    "tests/test_qualify_dependencies.py"
  ],
  "isolation": "fulfilled",
  "ownership": "repository checkout only",
  "host_inspected": false,
  "production_qualified": false
}
```
