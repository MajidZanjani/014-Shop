---
phase: 01-product-authority-repository-review-and-decision-register
reviewed: 2026-10-20T10:59:13Z
depth: standard
files_reviewed: 4
files_reviewed_list:
  - docs/product-source/verify_t01.py
  - docs/product-source/t01-scope.md
  - docs/decisions.md
  - docs/implementation-evidence.md
findings:
  critical: 2
  warning: 0
  info: 0
  total: 2
status: issues_found
---

# Phase 1: Code Review Report

**Reviewed:** 2026-10-20T10:59:13Z
**Depth:** standard
**Files Reviewed:** 4
**Status:** issues_found

## Summary

Reviewed the four explicit source files against the source ledger/matrix, the two phase plans/summaries, context and relevant immutable-source passages. Two reproducible checker defects prevent retaining and rechecking T01 evidence as shared project records evolve. Both were confirmed using in-memory copies; canonical files were untouched. No current commercial approval or later implementation acceptance is inferred from this review.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: Historical evidence hashes incorrectly constrain current shared records

**Classification:** BLOCKER
**File:** `/home/claude/project/014-Shop/docs/product-source/verify_t01.py:276-278`
**Issue:** `evidence()` compares the hashes recorded for the original T01 execution directly with the bytes of the current checkout. `ARTIFACTS` includes the working decision register and shared source ledger, which legitimately change after T01. The register explicitly supports later scoped approvals, and the ledger holds subsequent evidence. Thus a valid later update makes both `all` and `self-check` fail even when the historical evidence and canonical source identities remain correct. Maintaining a passing check would require refreshing the old execution's artifact hashes to revisions it did not observe, or preserving an obsolete live register/ledger. The relocation fix addresses the historical root but leaves this equivalent dependency on current artifact state.

**Practical trigger / reproduction:** Load the existing inputs and append only a future-phase documentation note to the ledger bytes in memory. `source(candidate)` still returns 18 and `inventory(candidate)` returns 279, but `all_contracts(candidate)` raises `evidence artifact revision: .planning/SOURCES.md`. No source, original evidence or decision was changed by the probe.

**Fix:** Bind historical artifact hashes to the actual observed artifact revisions, including captured working-tree content where the recorded HEAD predates it. Preserve those original observations. Validate current source/register contracts separately; record later checker revisions and reruns as distinct observations rather than rewriting the original artifact identity. Add a regression control that advances a shared ledger or a structurally valid decision revision while retaining independently verifiable T01 history.

### CR-02: T01 metadata extraction rejects subsequent phase evidence

**Classification:** BLOCKER
**File:** `/home/claude/project/014-Shop/docs/product-source/verify_t01.py:254-256`
**Issue:** The JSON-block search spans all of `docs/implementation-evidence.md` and requires exactly one match. This is the shared implementation-evidence path, so appending an independent later-phase record with its own JSON metadata prevents the checker from identifying the unchanged T01 record. Both `all` and `self-check` then fail on document growth unrelated to T01. This failure is independent of the historical artifact-hash comparison.

**Practical trigger / reproduction:** Append a separate `## T02 local documentation evidence` section containing a fenced JSON metadata object to an in-memory copy of the evidence document. Leave its T01 block, hashes and all other inputs unchanged. `all_contracts(candidate)` raises `one evidence metadata block`.

**Fix:** Extract an explicitly bounded T01 record before searching for metadata, or place per-phase records at distinct paths and point the checker at the T01 record. Enforce exactly one metadata block inside that record, preserving rejection of duplicate T01 metadata. Add a positive control with an unrelated later-phase JSON evidence block and a negative control with duplicate metadata inside T01.

## Review verification and limits

- Existing `python3 docs/product-source/verify_t01.py all` passed: source 18, scope 25, inventory 279, decisions 88, evidence 38.
- Existing `python3 docs/product-source/verify_t01.py self-check` passed: 57 asserted rejections and valid controls.
- The two additional lifecycle probes above ran against in-memory copies only. Tracked status remained clean before this report was created.
- Current P-01–P-12 statuses remain Pending/None supplied. The scope/evidence documents explicitly retain manual source-intent, approval-scope, isolation and prohibition judgments. Passing automated contracts does not resolve them.
- This review establishes no application, selected-bank, cloud, DNS/TLS, real-mail or production acceptance. No dependencies were installed, environment files opened, source files modified, commits created or external actions performed.
- Default sandbox commands failed before execution with `bwrap` workspace access errors; authorized escalated reads/checks succeeded. The supplied runtime exposes no Read/Write tool, so reads used shell commands and only this report was created with the available file-patching tool.

---

_Reviewed: 2026-10-20T10:59:13Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
