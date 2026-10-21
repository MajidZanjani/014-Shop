# Phase 1: Product authority, repository review and decision register - Pattern Map

**Mapped:** 2026-10-20. Planning only; no application exists.
**Files classified:** 7. **Existing documentation analogues:** 6 / 7 (including self-patterns).

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `.planning/SOURCES.md` | model (source ledger) | file-I/O | same file | exact |
| `.planning/SOURCE-MATRIX.md` | model (traceability matrix) | transform | same file | exact |
| `docs/decisions.md` | model (decision register) | CRUD | same file, prose/schema only | partial; malformed rows |
| `docs/product-source/SLL_xSPI_MC_Product_Page.md` | model (immutable source) | file-I/O | `.planning/SOURCES.md` | partial; identity contract only |
| `docs/product-source/t01-scope.md` (proposed) | model (scope record) | transform | `.planning/SOURCES.md` | role-match |
| `docs/implementation-evidence.md` (proposed) | model (evidence record) | batch | `.planning/REPLAN-VERIFICATION.md` | role-match; stronger metadata needed |
| `docs/product-source/verify_t01.py` (proposed) | utility | file-I/O / transform | none | no code analogue |

The supplied proposal and handoff are immutable inputs, not rewrite targets. The extracted product is a preservation/check target; its inclusion does not authorize changing its bytes. Existing analogues above were confirmed git-tracked with `git ls-files -- <path>`.

## Pattern Assignments

### Source ledger and preserved product
Copy the ledger schema from `.planning/SOURCES.md:7-11`:
```markdown
| Source | Lines | UTF-8 bytes | SHA-256 |
|---|---:|---:|---|
| `docs/product-source/SLL_xSPI_MC_Product_Page.md` | 449 | 23969 | `562dc4015c62f165df5df3e9ae1aab26b8102385d9dc76a556d5965ddc1a0263` |
```
Keep the authority/evidence distinction from lines 5, 13 and 17-19. Preserve raw source bytes, final newline and intentional Markdown hard breaks; record provenance without asserting commercial approval.

### Source inventory and requirement mapping
Reuse `.planning/SOURCE-MATRIX.md:5-12` for contract-to-requirement mapping and lines 30-50 for explicit vendor/family order:
```markdown
| Source contract | Primary requirement coverage | Integrated evidence |
|---|---|---|
| Exact source identity and repository scope | SRC-01–SRC-04 | UAT-01 |
```
Extend correct existing inventories with bounded source locators and per-row traceability. Preserve the separation between exact labels and proposed IDs (line 26), unresolved coverage (line 52), and written-specification observations versus runtime evidence (line 94). A future UAT reference is not a passed test.

### Single decision register
Reuse the approval semantics in `docs/decisions.md:3`: “All entries are pending; proposed owners are responsible roles, not assigned named people.” Its lines 5-6 define seven columns, but rows 7-18 have six cells: owner roles are joined to blocked-operation text. **Do not copy those rows as a valid table pattern.** Repair delimiters, retain P-01–P-12/status/evidence meaning, and add exact affected-phase/operation mapping. No named owner or approval may be invented.

### Scope and reset note (proposed)
Use `.planning/SOURCES.md:25-27` as the closest scope/delta analogue: identify current authority, superseded planning, recoverable history and unchanged application/external state. Add source-defined product/profile/origin identities and fresh branch/worktree/revision observations. Preserve the distinction between current checkout facts and an unresolved execution-isolation requirement; planning must not switch branches.

### Implementation evidence (proposed)
Use `.planning/REPLAN-VERIFICATION.md:3,5-15` for scoped observations and limits. Concrete opening pattern: `Scope: documentation reset/replanning only; no application, external resources, messages or financial operations.` Strengthen it using `.planning/SOURCES.md:23`: task status, revisions, commands/observations, environment, unresolved decisions and exact affected operations. Populate only after execution; do not inherit old verification as new completion credit.

## Shared Patterns

- Authority and status stay explicit: source provenance, provisional specification, pending decision and executed evidence are separate claims.
- Preserve existing inventories and unrelated work; modify only specifically planned documentation. Never inspect, source, copy or publish `.env` contents.
- No imports, authentication guards, runtime error handlers or test framework patterns exist in these documentation analogues. Staff MFA and application authorization belong to later phases.

## No Analog Found

`docs/product-source/verify_t01.py` has no tracked code analogue. Use the proposed standard-library algorithm in `01-RESEARCH.md`, not an invented project convention: allowlisted paths, raw-byte SHA-256/appendix equality, bounded exact ordered inventories, strict decision-table structure and scope metadata. Proposed modes are `source`, `inventory`, `decisions`, `scope`, `all`, `self-check`; none exists or passes merely because it is planned. Fail nonzero with contract names, without dumping private/unrelated content. Negative checks use memory or temporary copies; canonical inputs remain untouched. Manual review must assess truthful operation/phase mappings and checkout isolation.

## Metadata

**Search scope:** named phase inputs plus four tracked documentation analogues; no broad discovery or external research. **Analogue files read:** 4. Existing register structure is explicitly rejected; checker, scope and evidence paths remain proposed future responsibilities. Only this pattern map is written by this task.
