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

## Continuation — actual operator native reference closure

New required native-closure lane observes and read-only hashes the actual already-realized operator closure:53 reachable store objects,222931552 NAR bytes. Complete NAR hashes/sizes/reference edges, exact recipe hashes, available derivation/output bindings/source pointers and two named-notice candidates retained separately in operator-native-closure.json. Fifteen distinct local derivation recipes absent; explicit missing-source/provenance status, no auto-fetch/build/repair. Supplementary reference closure evidence is not standard SBOM or complete source/native notice inventory; all approval/OCI/runtime flags false.

Actual pinned lane53 checks/8 tests0.899s; operator-runtime4/10 in2.159s; environment2/14 in0.900s. First format diagnostic used unsupported --json-format on derivation show; observed actual JSON envelope4, now pinned. First collector assumed2 and failed; corrected to measured4. Second collector denied absent cached derivation; changed scoped observation to retain explicit absence instead of inventing provenance. Actual creation and retained recheck then passed. No raw evidence rewritten, image build, host/provider/service operation or credential read. Plan16/14/17 and full phase remain incomplete.

### Native report revision after ten-module source integration

Current operator reference closure has54 realized objects; original53-object report retained unchanged. New content-addressed exact report revision plus deterministic current-observation selection prevent historical overwrite. Actual native54/9 in0.918s after source/operator builds. Missing native/source/notice/OCI/legal/runtime gates remain open; not standard SBOM or complete inventory.

## Continuation — exact cached native source notices

Required native-source-notices lane binds already-cached exact Python3.13.16/PostgreSQL18.6 source archives to current verified operator recipe/output and original source SHA256 pins. Nine upstream named candidates retained with member/content hashes and native-evidence binding, including exact top-level LICENSE/COPYRIGHT. No downloads/builds/extraction. PostgreSQL7944 members/141525674 expanded bytes/3 candidates; Python5272/110355801/6 candidates. Filename candidates include copyright.pl and non-Linux notices, so no legal/output-incorporation or source-offer completion inferred. Original raw/native reports unchanged.

Actual initial9 checks/6 tests3.718s; pinned independent recheck9/6 in3.696s; environment2/14 in0.897s pass. No failed tests. Other native/npm notices/source/OCI/legal/runtime/CI gates,14/17 and full phase remain incomplete. No credentials or host/provider/service/resource operation.

## Continuation — separate pinned schema candidate

Code ec4c4db packages a distinct schema launcher with exact isolated Python/Psycopg/libpq/site/source inputs shared with inspection. Actual operator7/17 passes, including hostile startup, closed errors/arguments and synthetic private-FD0/FD3 transport through exec. Real source SCRAM/admission3/107, deployment16/31, environment2/14 pass. First Nix check declaration failed and was corrected. No role/authority/socket/publication/host qualification implied.

Current inspection reference native54/9 and cached notices9/7 pass with content-addressed reports preserving history/texts. Separate schema closure/standard/native/OCI/legal inventory pending. No live apply, records, credentials, installation, host/provider or production connection.14/16/17/full phase/BUILD incomplete. See quick261022-7l3. Remote push blocked by approval review pending explicit origin/main publication authority.

## Supplemental prefixed notice names — quick261022-b5y

Original report/default remains immutable/reproducible; expanded supplemental collector includes mit.LICENSE-like prefixed names under unchanged nonextracting archive/digest guards. All12 exact official distributions verified/refetched twice. Named candidate observed in pip-requirements-parser32.0.1: mit.LICENSE,1080 bytes,SHA25618081c2c82771ca09d99d08cdac405924309e09fd19b16f1eea59cbc6ab809ed, separately retained in licence-name-audit.json/licence-name-texts. The original full member list already recorded this file; its original anchored filename policy omitted it. Ten npm/packageurl-python still without named candidates under expanded policy; original raw/derived/inventory/embedded evidence unchanged.20 collector+4 inventory tests pass; original12/0 audit reproduces, supplementary12/1/1 report/text reproduces independently. One gap now has observed actual named text, not legal/package-wide/native completion. No install/execute/host/provider action; parent16/native/OCI/legal and17 remain incomplete.

## Bounded npm notice-marker discovery — quick261022-bb9

All10 exact unresolved npm artifacts refetched/verified twice. Supplemental report binds original inventory/audit/member inventories and explicit textual scan/skips/hashes/ranges;13 members have markers,6 distinct exact lines239 bytes retained separately. Ten package.json declared-licence fields and sharp-libvips/am-i-vibing/process-ancestry README references, not complete grant or legal/package-wide/native completeness. Binary/native/source-map/oversize/invalidUTF8/NUL remain unreviewed under explicit bounded policy.8 new scanner+20 licence collector+4 inventory tests pass, no failures.9 original evidence files unchanged. No install/execute/dependency/runtime/host/provider action. Ten npm/full inventory/legal/native/OCI16/17 remain incomplete.

## Offline supplemental reconciliation — quick261022-bqg

New review report binds five source reports and exact package/artifact/member/text/hash/range evidence, complete original gap coverage, no-follow stable bounded reads and final source rechecks.12 packages:1 named text/2 headers/10 marker observations (overlap),12 package-wide reviews pending. No inventory/legal/completeness grant or raw evidence rewrite.40 collector/marker/inventory tests pass; original full inventory gate deliberately remains exit1/PENDING_FULL_INVENTORY and raw required-text entries remain empty. Actual offline report creation/rechecks pass;10 prior reports unchanged. No failures/network/install/runtime/host/provider operation.16/legal/native/OCI and17 plus application integration remain incomplete.

## Actual local PostgreSQL archive — quick261022-bw3

One existing pinned candidate archive built locally,125653410 bytes,SHA25600ad3ec8402040624e9218f25fed63c5aa62a1a002a07dc3a3a1fab425021067;51 ordered archived layer hashes match declared config DiffIDs. Content-addressed archive/config/layer evidence plus actual successful local Nix builder log/provenance retained, no OCI distribution manifest invented.8 scanner tests0.019s and deployment16/31 2.133s pass, independent rescans match. Two initial scratch setup failures corrected with exclusive non-world-writable-ancestor /var/lib scratch; no existing permissions/global config/shared cleanup. Original empty candidate inventory retained historical. No container imported/run/cluster initialized/registry/host/provider/credential action. Other images, inner payload/native notices/OCI/two-independent-build comparison/full CI/off-host/runtime/independent retention remain pending; parent acceptance incomplete.

## Actual PostgreSQL inner-layer inventory — quick261022-cor

Streaming observer preserves independent outer hashes and original report. Actual51 layers/14480 entries/8298 regular files/298557309 regular bytes hashed;5151 unresolved symlinks,0 hardlinks/whiteouts.10517 absolute names preserved/flagged;2972 entries with PAX metadata. Preferred PAX-aware report874d877d6651a07c89871beaae9e66c30beefb469cfdfebc4018da318b639ba7;earlier narrower revision retained,not another build.2 notice filename candidates(ICU/Python) hashed,not complete native/legal review.17 tests0.035s and actual rescans pass;initial conservative relative-path policy denied actual absolute names before output,corrected via nonextracting observation. No container/import/extraction/rebuild/host/provider action. Importer/links/PAX/merged-rootfs/native/legal/OCI/two-build qualification remain pending.
