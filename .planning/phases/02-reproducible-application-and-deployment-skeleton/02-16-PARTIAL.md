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

## Continuation — explicit schema-valid derivative, raw unchanged

Codecacc247 adds scripts/derive_npm_sbom.py, seven tests, an explicit npm-sbom-derived.json and hash/change/validator receipt plus docs/build/npm-sbom-derivation.md. Raw npm-sbom.json and licences.json remain byte-for-byte unchanged. The derivative omits only exact known malformed VCS external-reference objects for am-i-vibing0.5.0 and common-ancestor-path2.0.0; no replacement URL inferred. JSON pointers/removed values allow exact parsed-JSON reconstruction. All component identities/hashes/licences/dependency edges and other fields remain unchanged. Both original metadata defects remain unresolved upstream.

Actual local: seven transformation tests pass (0.097s), four existing inventory tests pass; locked cyclonedx-python-lib11.12.0 strict CycloneDX1.5 validator confirms raw invalid/derived valid. Exclusive --write pass4 checks/271 reconciled retained unique npm identities15.500s; subsequent default retained-output check pass4/271 in15.682s. No new application install/recollection or image/host qualification implied; tool environment uses existing frozen tools lock. Three initial single-omission qualification/diagnostic attempts failed actual derivative validation, exposing second malformed raw reference git@github.com:isaacs/common-ancestor-path after first raw failure. Expanded only the explicit two-reference policy; no invalid artifacts were written. Reversible-change/coverage tests and actual maintained validator both pass. git diff --check and unchanged raw/provenance checks pass.

Raw SHA25660f9f60edc3164ca4ce7fb3489245a5ae60bcb5178f0efa8ecb09d2f735f892c; derivative8c9d56af9ac8b008a983fff6acf4d178eca7ee8d91d5f806c02dbb4809c2908d. Receipt names actual validator and records raw/derived results; software/legal approval/inventory_complete/raw_upstream_metadata_resolved all false. Default CLI checks exact retained derivative/receipt; --write creates only new outputs and refuses existing ones, no repair/overwrite. Full raw collector unchanged/nonzero on schema findings, not rerun. Twelve missing incorporated-text findings, native/Nix/OCI/layers/notices/compatibility and full inventory approval remain pending. Plan16 remains implementation-incomplete, not completed by a derived SBOM. Plans14/17 and full phase remain incomplete; no FULL_PASS.

No .env read/needed credential, source/product change, host/provider operation, existing service/resource change or purchase. Independent off-host runner remains unassigned and disruptive tests pending. Continue authorized repository preparation, including live record publisher/admission/transport/app migration integration, qualified runtime/generator/replica/images, inventory/licences and OCI/CI evidence. Do not repeatedly ask about runner before remaining qualification stage.

## Continuation — exact-distribution archive audit

Code8052689 and docs/build/licence-gap-audit.md retain separate exact-distribution evidence. All twelve official artifacts downloaded and verified against retained SRI/SHA256 before nonextracting archive inspection. Zero separately named licence/notice candidates across ten npm archives and two Python-tool wheels; original twelve findings remain open. Report binds source inventory hash, archive hash and complete member name/size/type inventory. No embedded-text/source classification or legal/native completeness inferred. Original raw/derived SBOM and licences.json bytes unchanged.

Eight new audit controls and four inventory controls pass; fresh retained-report verification passes12 distributions. No full inventory or phase acceptance. No package installation/host/provider operation or credentials. Native/Nix/OCI closure/notices/layers/compatibility, embedded/source review and other14/17 implementation remain pending. Local commits retained; automatic approval review denied remote push pending destination/publication authority.

## Continuation — two embedded Python headers

Supplementary embedded-licences.json plus two content-addressed exact leading comment ranges retain MIT grant/condition/disclaimer and holder evidence from the exact verified pip-requirements-parser32.0.1 and packageurl-python0.17.6 wheels. Binds inventory/archive/source/header hashes and byte offsets. Named-file report and original raw inventory/SBOM unchanged. Two observations address text discovery, not complete package/native/redistribution/legal review. Ten npm findings remain without this supplemental evidence; all parent acceptance gates stay pending.

Actual initial collection and independent recheck pass2 distributions. Five new tests, eight archive tests and four inventory tests pass. One initial negative control exposed missing copyright-holder enforcement; required actual holder line added, focused controls and actual retained recheck pass. No legal approval, package-wide notice completeness or INVENTORY_PASS. No credentials/install/host/resource/provider action. Previous origin block resolved by user continuation and successful exact two-commit push.
