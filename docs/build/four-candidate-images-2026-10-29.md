# Four candidate images — local build and inspection, 2026-10-29

Four exact app/worker/PostgreSQL/gateway Docker save archives now exist and are inspected. This advances Phase2 plans14/16/17 and their dependent packaging/recovery/release work. Phase2 remains8/18 completed local plan records; full BUILD-01–08 acceptance is pending.

[Content-addressed build/inspection record](../evidence/t02/image-build-revisions/9d42b9f045e228de2d03e99bfe97e222295885ab8810861caca57d2c9e994102.json) binds the actual command, source commit/dirty state, lock/recipe hashes, measured builder log, archive/config/layer identities, payload reports and four new local output roots. No registry manifest digest or actual runtime result is inferred.

| Candidate | Archive bytes | Ordered layers | Inner entries | Regular files |
|---|---:|---:|---:|---:|
| shop-app | 107154882 | 40 | 25733 | 13638 |
| shop-worker | 107154870 | 40 | 25733 | 13638 |
| shop-postgres | 125653410 | 51 | 14480 | 8298 |
| shop-gateway | 31802498 | 11 | 2612 | 2224 |

Counts overlap between images and layers; they are not unique native-component totals. Exact hashes/paths and unresolved-link/PAX/notice observations are in the linked immutable reports.

## Executed work

- Original controls:23 tests/15 failed assertions, no errors, prove the inspectors lack explicit candidate selection. Both original tool files were substituted in a guarded control and the fixed bytes restored exactly. Final pinned Python23 tests pass in0.046s, including all four selectors, wrong/unknown-image denial, default PostgreSQL report/payload byte equality and CLI retention.
- Both existing inspectors now accept `--image shop-app|shop-worker|shop-postgres|shop-gateway`, defaulting to the unchanged PostgreSQL contract. The Python interfaces add `expected_image`; no schema or historical observation byte changes. Inspectors remain nonextracting and never follow image links or execute images.
- Initial offline dry-run reported1018 unrealized derivations. The bounded online dry-run instead found34 derivations/11 fetches,17.6MiB download/52.9MiB unpacked. Actual four-image build used max-jobs1/cores2 in a new exclusive child of the specifically recorded owned /var build directory, with6.4GiB free before execution and a1800-second preparation bound. It completed in24.209s. No existing directory permissions, global settings or services changed; shared /tmp stayed untouched.
- Initial PostgreSQL reinspection failed because the historical store archive was absent. Rebuilding restored exactly the original125653410-byte archive, SHA25600ad3ec8402040624e9218f25fed63c5aa62a1a002a07dc3a3a1fab425021067. Default and explicit CLI checks reproduce the original outer report f40a60ce47686368cd6dbd4dcbf2da6ad5bde1893eb865b757281dbfabb23e31 and preferred payload report874d877d6651a07c89871beaae9e66c30beefb469cfdfebc4018da318b639ba7 byte-for-byte. No old evidence was rewritten and no cause for the earlier absence is inferred.
- All four actual archives and inner payloads pass independent CLI rereads. Three new outer reports, three payload reports and three compressed entry manifests are retained with hashes. New task-owned indirect local Nix roots retain only these four outputs; this is not independent artifact custody and performs no garbage collection.
- Both application images contain all276 regular source files under the exact g1yy3csf0imkh4hsf3didszrk66ps8sa-shop-python-source prefix with matching observed SHA256 bytes. The /app aliases remain recorded links; this does not qualify merged-rootfs resolution or imports.
- Deployment evaluation16 checks/31 tests passes in2.763s before the scope-message-only correction and passes again afterward. Eight inventory/planning regressions pass. The full deployment-build command still rejects with PENDING_EXACT_RUNTIME_REVIEW; the local artifacts cannot approve runtime review. The evaluator now states that build/runtime qualification needs separate evidence instead of unconditionally calling all images unbuilt.

## Reproduction and remaining acceptance

Use the recorded exact `nix build` command only with a newly owned adequate build directory. For each output use `nix develop ./ops/nixos#backend --command python3 scripts/inspect_image_archive.py --archive <output> --image <candidate>` and the matching `inventory_image_payload.py --archive <output> --outer-report <content-addressed-report> --image <candidate>`. `--write` creates only new evidence; omit it to verify retained bytes. PostgreSQL defaults remain supported. Pinned inspector tests are test_inspect_image_archive and test_inventory_image_payload.

The full objective remains [Phase2 and related-step completion](../../.planning/phases/02-reproducible-application-and-deployment-skeleton/02-COMPLETION-TRACKER.md). Remaining work includes merged rootfs/links/PAX/importer semantics, complete actual native/standard SBOM/licence review, exact OCI distribution manifests and two independent image builds, application-role/all-write/transport/migration/bootstrap integration, an executable independently authorized replica driver, full CI and human source/probe/prohibition review. Related phases11/12/13/14 still need their actual containment/capacity/recovery/reopening/ownership/activation evidence. No image imported/run, independent runner assigned, real provider operation, mx1/protected change, legal approval, FULL_PASS or full phase completion is claimed.
