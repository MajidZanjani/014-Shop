---
phase: 02-reproducible-application-and-deployment-skeleton
plan: "16"
status: implementation_pending
requires: [02-15]
provides: [raw-installed-npm-sbom, raw-runtime-and-tools-python-sboms, exact-distribution-and-licence-findings]
requirements-completed: []
---
# Phase 2 Plan 16: Actual installed SBOM evidence; complete inventory pending

Standard npm sbom and locked cyclonedx-py environment produced raw CycloneDX outputs from actual new frozen installations. Installed metadata/graphs reconcile 271 unique npm identities, 6 runtime Python and 39 tool Python distributions. Seventy platform-optional locked paths are explicitly not installed, not invented components. Distribution URL/integrity or SHA-256, actual dependency fields, declared licence metadata and found incorporated text paths/content hashes are retained. Python wheel hashes match official registry file metadata; target tools/import/version checks run. The extra raw python-tools-sbom.json was in the GSD manifest before editing so build tooling is not omitted.

## Actual execution and unresolved findings

`inventory_artifacts.py --local` recorded 316 reconciled component checks and 4 rejection tests in 22.310 seconds, then returned **exit 2**. There is no INVENTORY_PASS or successful complete inventory claim.

Python SBOMs validate through the maintained tool's explicit validation. Strict maintained CycloneDX validation rejects npm's unchanged raw output: dependency metadata provides malformed repository URI git+https://github.com:ascorbic/am-i-vibing.git. Diagnostic and raw output are retained; no silent normalization or fictional success. Distribution artifact URL/hash remains independently reconciled.

The current incorporated-text scan records ten npm and two Python-tool missing-text findings. In particular sharp/libvips and other native bindings need bundled/redistribution review. Declared licence strings are not licence-text or legal acceptance proof. Native Node/Python/PostgreSQL/libpq/OpenSSL/systemd/Caddy/Podman/helpers/backup notices and actual Nix/OCI image manifests/layers/closures remain incomplete. runtime-image-inventory.json has an empty actual-images list with explicit unbuilt status and separates inert candidate metadata. No image/native component presence or approval is invented.

A later focused offline reconciliation after strengthening digest validation again matched all 316 identities; four tests pass and reject removed transitive/component coverage, absent/malformed distribution or text hashes, missing required text and invented version. No additional install or actual-host operation was needed. Full inventory default deliberately returns nonzero until required native/image/text/schema evidence exists.

## Remaining implementation

Complete native/OCI provenance/notice coverage after approved builds, resolve incorporated-text and npm-schema findings through attributable reviewed evidence, then implement full inventory acceptance. All legal conclusions remain unresolved. Existing exact direct approval does not approve new runtime bytes. No .env credential was read and no live provider, host or protected-resource action occurred. Plan is implementation_pending, not merely awaiting an off-host runner.
