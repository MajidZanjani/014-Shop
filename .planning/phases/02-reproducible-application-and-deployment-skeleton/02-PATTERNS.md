# Phase 2: Reproducible application and deployment skeleton - Pattern Map

**Mapped:** 2026-10-20 UTC  
**Files analyzed:** 16 proposed file families, including implementation-test additions inferred from research  
**Analogs found:** 3 / 16 families (partial or role matches); no existing application-framework analogs

## Scope and provenance

Read AGENTS.md, Phase 2 RESEARCH.md and BUILD-01–04 in `.planning/REQUIREMENTS.md:22–25`. No Phase 2 CONTEXT.md exists. This is planning within the parent GSD workflow; no application implementation is authorized by this map. Proposed paths below are targets, not existing files. The tracked inventory contains documentation and one Python standard-library checker; it contains no Astro, React, Django, PostgreSQL worker, NixOS, schema or CI implementation. No project skill indexes were found in `.codex/skills/` or `.agents/skills/`.

The only source-code analog is `docs/product-source/verify_t01.py`. Its tracked status, and that of documentation analog `docs/implementation-evidence.md`, were verified using `git ls-files`. The existing `.gitignore` is tracked and contains only `.env`; that is insufficient as a future build-artifact exclusion policy. Do not inspect real credentials to extend it.

## File Classification

Brace notation expands to every named proposed file; directory entries describe a family whose exact members the planner must enumerate.

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `frontend/{package.json,package-lock.json,astro.config.mjs,tsconfig.json}` | config | batch | None | greenfield |
| `frontend/src/content.config.ts`, `frontend/src/content/probes/skeleton.md`, `frontend/src/pages/index.astro` | config/model/component | file-I/O → transform | None | greenfield |
| `frontend/src/components/BuildProbe.tsx` | component | event-driven | None | greenfield |
| `backend/manage.py`, `backend/shop/config/{base,local,synthetic,production}.py`, `backend/shop/{urls,wsgi}.py` | config/route | request-response | None | greenfield |
| `backend/shop/core/{health,checks,logging}.py` | controller/utility | request-response | None | greenfield |
| `backend/shop/adapters/{ports,fake_bank,capture_mail,local_storage}.py` | service | request-response/file-I/O | None | greenfield |
| `backend/shop/worker/{models,services}.py`, `backend/shop/worker/management/commands/run_worker.py`, initial worker migration | model/service/migration | CRUD/batch | None | greenfield |
| `backend/requirements/{runtime,tools}.in`, target-specific hashed `.txt` files | config | batch | None | greenfield |
| `schemas/v1/{probe,environment,artifact-manifest}.schema.json`, `api/v1/openapi.json`, `tests/fixtures/contracts/` | model/config/test | transform | None | greenfield |
| `ops/nixos/{flake.nix,flake.lock,modules/shop.nix,profiles/development.nix,profiles/ovh-template.nix}` | config | batch | None | greenfield |
| `ops/config/{local,synthetic,production}.example`, `ops/secrets/README.md`, `ops/qualification/ovh-image.md` | config/documentation | file-I/O | None | greenfield |
| `scripts/{check,dev_postgres,check_contracts,check_boundaries,check_reproducibility,inventory_artifacts}.py` | utility | batch/file-I/O/transform | `docs/product-source/verify_t01.py` | partial: bounded checks and hashing only |
| `.github/workflows/ci.yml` | config | event-driven/batch | None | greenfield |
| `backend/shop/{core,adapters,worker}/tests.py` or corresponding test packages; frontend/Node checks and NixOS test files to enumerate | test | request-response/CRUD/batch | None | greenfield: existing inline negative controls are not framework or concurrency tests |
| `docs/build.md`, `docs/service-boundaries.md` | documentation | batch | `docs/implementation-evidence.md` | partial: scope and evidence language only |
| `docs/evidence/t02/` manifest and result records | documentation/model | batch/transform | `docs/implementation-evidence.md` and checker evidence validation | role-match |

Framework package `__init__.py` files, test package initializers and generated lock/migration details are implied scaffolding; the planner must enumerate them with their owning family. Do not interpret grouped rows as permission to omit required files.

## Pattern Assignments

### Verification scripts (utility, batch/file-I/O)

**Analog:** `docs/product-source/verify_t01.py`.

**Imports and repository-root convention (lines 1–9):**

```python
#!/usr/bin/env python3
"""Read-only T01 documentation contracts; Python standard library only."""
import hashlib
import re
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
```

Copy explicit imports and root-relative path handling, adjusting the parent depth for `scripts/`. Do not impose the T01 standard-library-only constraint on schema validation, dependency inventory or framework tests: Phase 2 research explicitly selects maintained validators and SBOM tools.

**Named failure and decoding pattern (lines 23–36):**

```python
class ContractError(ValueError):
    pass

def require(ok, name):
    if not ok:
        raise ContractError(name)
    return 1

def text(data, name):
    require(data is not None and len(data) > 0, name + ": missing/empty")
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        raise ContractError(name + ": invalid UTF-8") from None
```

Use named checks and explicit errors for missing evidence; extend the future command entry point to return nonzero for missing dependencies/DB. This helper is suitable for build checks, not an HTTP error/authentication convention.

**Byte identity checks (lines 49–54):**

```python
for name, (size, digest) in IDENTITIES.items():
    data = inputs.get(name)
    text(data, name)
    count += require(len(data) == size, name + ": byte length")
    count += require(hashlib.sha256(data).hexdigest() == digest, name + ": SHA-256")
    count += require(data.endswith(b"\n"), name + ": final newline")
```

Reuse byte hashing in artifact/reproducibility manifests. T01 source hashes are immutable authority checks; T02 release hashes must be generated from actual built outputs, with two clean builds compared. Do not hardcode research candidate versions as already qualified identities.

**Bounded subprocess and allowlisted artifact reads (lines 264–276):**

```python
def historical_artifacts(revision):
    """Read only the five allowlisted artifacts from an attributable Git commit."""
    require(isinstance(revision, str) and bool(re.fullmatch(r"[0-9a-f]{40}", revision)),
            "historical artifact commit identity")
    ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", revision, "HEAD"],
                              cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
    require(ancestor.returncode == 0, "historical artifact commit reachable")
    result = {}
    for name in ARTIFACTS:
        saved = subprocess.run(["git", "show", f"{revision}:{name}"], cwd=ROOT,
                               capture_output=True, timeout=5)
        require(saved.returncode == 0, "historical artifact available: " + name)
        result[name] = saved.stdout
```

Copy argument-list invocation, explicit cwd, timeout and return-code enforcement. The new PostgreSQL lifecycle needs its own safe scratch-state ownership and cleanup design; this read-only Git helper is not a process-supervision analog. Limit captured/logged data to synthetic safe outputs.

### Build/service documentation and T02 evidence (documentation, batch)

**Analogs:** `docs/implementation-evidence.md`; validation in `docs/product-source/verify_t01.py`.

The existing evidence document separates historical observations from later repair notes; use a distinct dated T02 record/directory rather than rewriting T01 outcomes. The concrete machine-readable field contract is in checker lines 290–294:

```python
for field in ("observed_utc", "head", "branch", "root", "status", "environment",
              "tasks", "commands", "artifacts", "artifact_revision", "isolation", "acceptance"):
    count += require(field in meta and meta[field] is not None, "evidence field: " + field)
count += require(bool(re.fullmatch(r"[0-9a-f]{40}", meta["head"])), "evidence head")
count += require(bool(re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", meta["observed_utc"])), "evidence timestamp")
```

Apply attributable source revision, command, environment and artifact identity to T02 manifests. Establish a versioned T02 schema instead of importing a T01 task-specific metadata parser. Label local/synthetic versus template evaluation, VM boot, actual OVH and production observations separately. Prepared templates cannot count as deployment proof. Keep unknown licence/approval conclusions explicit.

## Shared Patterns

- **Fail closed:** named contract errors in `docs/product-source/verify_t01.py:23–36` are a useful utility precedent. Missing PostgreSQL, incomplete lock/licence inventory and unresolved schema references must fail required checks rather than produce a skip or success claim.
- **Bounded and attributable operations:** copy explicit subprocess timeouts and safe argument lists from `docs/product-source/verify_t01.py:264–276`; record revision/artifact identity using lines 290–294. Do not infer those helpers provide sandboxing or redaction.
- **Public/private boundary:** no existing implementation enforces it. Implement the research's frontend allowlist and synthetic canary tests; never scan real secret contents or copy `.env` into build inputs.
- **Auth/guards:** no existing authentication, resource authorization or staff MFA analog. Keep privileged/private routes unmounted; do not add a permissive fake guard to establish a convention.
- **Transactions/logging/response formatting:** no existing application conventions. Use the selected Django/PostgreSQL/platform interfaces from research and verify signatures against actual locks. T01's printed documentation gates are not a structured logging or API response pattern.

## No Analog Found

The thirteen unmatched classification families are greenfield: frontend config/content/island; Django configuration/routes/core; adapters; worker/model/migration; requirements locks; versioned schemas/contracts; NixOS configuration; deployment/secrets templates; CI; framework/concurrency tests. Use `02-RESEARCH.md` Architecture Patterns, Code Examples and Validation Architecture as proposed designs, then verify against selected locked upstream artifacts. They are not existing project conventions.

In particular, use real PostgreSQL independent-session transaction tests for leases; no generic checker, regex parser or JSON block parser substitutes for them. Use maintained JSON Schema/OpenAPI validation, installer hash enforcement and standard SBOM tooling rather than expanding the T01 handwritten documentation parser into those roles. Keep complete commerce/outbox semantics, MFA, real bank integration, deployment and recovery proof in their owning later phases.

## Metadata

**Analog search scope:** tracked repository inventory; `docs/product-source/verify_t01.py`, `docs/implementation-evidence.md`, `.gitignore`, README, project instructions and Phase 2 research/requirements. No credential contents, runtime mirrors or external worktrees inspected.  
**Source analog count:** one Python source file; one evidence-document analog. Search stopped because the tracked inventory has no other implementation source.  
**Pattern extraction date:** 2026-10-20 UTC.  
**Coverage:** exact 0; partial 2 families; role-match 1 family; greenfield 13 families. Counts describe file families, not individual expanded scaffold files.
