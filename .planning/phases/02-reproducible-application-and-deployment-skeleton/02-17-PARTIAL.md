---
phase: 02-reproducible-application-and-deployment-skeleton
plan: "17"
status: implementation_pending
requires: [02-16]
provides: [two-local-payload-builds, real-installer-tamper-controls, manually-gated-ci, focused-versioned-evidence]
requirements-completed: []
---
# Phase 2 Plan 17: Local reproducibility/installer proof; full qualification pending

## Actual local results

- Final two-build command passed 4 checks/5 tests in 16.466 seconds. Exactly two independent actual npm installations/builds, backend source/migration/requirements packages and installed npm graph manifests match byte/path/size/hash. A deliberately changed byte, empty/symlink payload and existing canonical-target ownership controls are tested. No OCI comparison is claimed.
- Pinned locks dispatcher passed 3 tool checks/8 tests in 7.554 seconds. Successful real frozen installs precede six actual offline negative cases: npm lock-sync/SRI/changed valid React archive, pip wrong hash/missing hash/changed valid wheel. Diagnostics must identify lock/integrity failure; network/missing-artifact errors cannot satisfy tests. Two diagnostic-control unit tests pass.
- Environment dispatcher passed 2 checks/14 tests in 0.891 seconds using new owned PostgreSQL 18.6. The explicit short project scratch parent is now scoped/restored before existing cleanup tests; no shared /tmp cleanup.
- Current source all passed six groups (20/27/279/88/39/18) and self-check rejected 71 mutations. Historical evidence is unchanged.
- Full all was actually invoked: environment 2/14 and frontend 13/9 passed, then required core stopped with PENDING_OFF_HOST. Exit 1, 10.367 seconds, **no FULL_PASS**. Other required lanes did not execute after that stop and are not counted as passed.

Counts are separate/reused lanes, not unique totals. docs/evidence/t02/manifest.json is a validated focused **local reproducibility command** record anchored to implementation commit 373b2c5, dirty evidence state and actual script/output hashes, four tool/source locks and measured elapsed time. It is not an all/CI/production manifest. Raw SBOM timestamps/serials are outside deterministic payload comparison.

## Reproducibility finding and correction

The first independent roots differed only in Astro island UID. Failed raw manifests/hashes are retained in reproducibility-failure.json; qualified Astro7.4.1 source hashes the component URL into that UID. Pinning a canonical process-visible path in separate new private mount/network namespaces resolved the difference. Underlying source/cache/build directories remain independent. The parent exclusively creates an empty marker-protected /tmp target, rejects existing targets, verifies no parent mount exists and cleans only its own target. No output normalization or framework patch. Backend tar metadata is an explicit deterministic packaging contract. An early invalid-gzip tamper failed before integrity checking; the final control changes valid archive header bytes and requires EINTEGRITY.

## CI prepared, not executed

JSON-form YAML workflow parses and embedded Python compiles. It is manual-only/trusted-main, read-only, no persisted checkout credentials/global safe-directory change, no production credentials, no automatic provisioning or untrusted PR execution. SHA-pinned checkout v4 commit11d5960a326750d5838078e36cf38b85af677262 was observed from the official ref; official action.yml confirms Node20. Assigned independent runner/machine/commit/action proof is required before checkout. Local feedback uses existing dispatcher lanes and current source checks; full qualification uses identical check.py all. Required aggregate rejects unsuccessful/skipped/cancelled/missing/zero-count jobs. No runner or authorization record was created; no CI run occurred.

Standard core/worker/contracts/deployment commands can now consume separately named operator-provided authorization-file paths, so future assigned CI need not bypass the dispatcher. They create no permission and remain fail-closed. Runner specification is still the single docs/qualification-runner.md; no repeated assignment request or automatic capacity purchase.

## Remaining implementation/acceptance

Complete 14 bootstrap/per-mutation guard, actual generator/runtime and executable replica driver; resolve 16 raw npm schema/missing text/native/OCI provenance findings; build/compare actual OCI payload/config; complete required full CI/off-host evidence and human browser/source/licence/probe/prohibition reviews. Current boot matrix is not an executable suite. No live provider, mx1, existing service/guest or resource allocation was changed. Full phase/BUILD/production acceptance remains incomplete.

Additional paths (focused/failure evidence, existing producer authorization wiring, scoped environment scratch and runner-spec update) were declared in the GSD manifest before edits to satisfy actual integration requirements. .gitignore excludes owned outputs/secrets without hiding locks/evidence. Explicit user continuation authorizes repository implementation/ordinary tests, not external/protected operations.

## Actual local PostgreSQL archive — quick261022-bw3

One existing pinned candidate archive built locally,125653410 bytes,SHA25600ad3ec8402040624e9218f25fed63c5aa62a1a002a07dc3a3a1fab425021067;51 ordered archived layer hashes match declared config DiffIDs. Content-addressed archive/config/layer evidence plus actual successful local Nix builder log/provenance retained, no OCI distribution manifest invented.8 scanner tests0.019s and deployment16/31 2.133s pass, independent rescans match. Two initial scratch setup failures corrected with exclusive non-world-writable-ancestor /var/lib scratch; no existing permissions/global config/shared cleanup. Original empty candidate inventory retained historical. No container imported/run/cluster initialized/registry/host/provider/credential action. Other images, inner payload/native notices/OCI/two-independent-build comparison/full CI/off-host/runtime/independent retention remain pending; parent acceptance incomplete.

## Actual PostgreSQL inner-layer inventory — quick261022-cor

Streaming observer preserves independent outer hashes and original report. Actual51 layers/14480 entries/8298 regular files/298557309 regular bytes hashed;5151 unresolved symlinks,0 hardlinks/whiteouts.10517 absolute names preserved/flagged;2972 entries with PAX metadata. Preferred PAX-aware report874d877d6651a07c89871beaae9e66c30beefb469cfdfebc4018da318b639ba7;earlier narrower revision retained,not another build.2 notice filename candidates(ICU/Python) hashed,not complete native/legal review.17 tests0.035s and actual rescans pass;initial conservative relative-path policy denied actual absolute names before output,corrected via nonextracting observation. No container/import/extraction/rebuild/host/provider action. Importer/links/PAX/merged-rootfs/native/legal/OCI/two-build qualification remain pending.

## Four candidate images built and inspected — 2026-10-29

[Actual evidence](../../../docs/build/four-candidate-images-2026-10-29.md): four exact local Docker archives built in24.209s and independently scanned; app/worker40 layers each, PostgreSQL51, gateway11. PostgreSQL archive/outer/payload hashes reproduce historical bytes. Closed candidate selection passes23 tests after original23/15 controls; deployment16/31 and inventory/planning8 pass. Both app/worker archives contain276 exact source files. New task-owned local output roots are registered, with independent custody still pending. No old evidence was overwritten, import/run/OCI digest invented or review/runtime gate relaxed. Full plans14/16/17 and Phase2 acceptance remain incomplete.
