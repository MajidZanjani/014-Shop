---
phase: 02-reproducible-application-and-deployment-skeleton
plan: "04"
status: complete
subsystem: build
requires: [02-03]
provides: [isolated-public-build-boundary]
requirements-completed: [BUILD-01, BUILD-03]
completed: 2026-10-21
---
# Phase 2 Plan 04: Public frontend boundary

An explicit nine-file allowlist supplies a disposable frontend build. Frozen installation precedes diagnostics and an actual network-denied build. The checker rejects runtime features and private imports, inventories every emitted artifact, and scans bounded maps and nested compressed assets for synthetic private canaries. No real credentials or private business data are read.

## Actual verification

`nix develop ./ops/nixos --command python3 scripts/check.py frontend` passed: 13 checks, 9 tests, zero failures, 9.715 seconds including dispatcher overhead. Four nonempty static artifacts were inventoried with SHA-256. Tests exercise actual private-asset publication, AST mutations for private imports/request-time features, symlinks, malformed manifests, missing output, source maps and disguised compressed canaries. The three frontend tests retain real static serving and React state/event coverage. A new process network namespace denies build networking without changing any existing service or network.

Commit: 9c5bd37. Browser hydration remains the separately recorded human check from 02-03. This evidence is local/synthetic; it establishes no host, production or off-host failure qualification. Shared BUILD requirements await sibling plans.
