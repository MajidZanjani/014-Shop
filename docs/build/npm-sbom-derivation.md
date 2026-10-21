# Explicit npm SBOM derivative

The retained `docs/evidence/t02/npm-sbom.json` remains the unchanged raw npm output.
It fails strict CycloneDX1.5 schema validation. A separate
`npm-sbom-derived.json` omits exactly two malformed VCS external references:

| Component | Omitted raw reference |
| --- | --- |
| am-i-vibing0.5.0 | git+https://github.com:ascorbic/am-i-vibing.git |
| common-ancestor-path2.0.0 | git@github.com:isaacs/common-ancestor-path |

No replacement repository URL is inferred. `npm-sbom-derivation.json` records
source/derived SHA256 hashes, each JSON pointer and removed object, actual
maintained-validator identity/version/results and271 reconciled unique npm
component identities. Reinstating the removed objects at their recorded pointers
reconstructs the complete original parsed JSON; every other field is preserved.
Serialization of the derived copy is explicit and does not alter raw bytes.

Run from the pinned development shell with an owned short scratch parent:

```sh
SHOP_TEST_SCRATCH=/home/claude/project/014-Shop/.scratch \
TMPDIR=/home/claude/project/014-Shop/.scratch \
nix develop --max-jobs 1 --cores 4 ./ops/nixos --command \
python3 scripts/derive_npm_sbom.py
python3 -B -m unittest discover -s tests -p test_derive_npm_sbom.py
```

Default mode regenerates the transformation in owned temporary storage, checks
actual raw rejection/derived acceptance with the existing locked
cyclonedx-python-lib strict validator, reconciles retained installed identities,
and compares the exact retained derivative and receipt. `--write` is only for
exclusive creation of new evidence files; it refuses existing outputs and never
rewrites raw evidence. If exclusive output creation is interrupted, retain the
partial result for review; there is no automatic overwrite or repair.
Unknown/missing/duplicate target identities/references or input JSON keys deny
the transformation. Other schema failures remain failures in maintained validation;
there is no generic reference deletion or schema-error suppression.

The raw collector is unchanged and retains its nonzero/schema finding behavior.
The derived artifact is clearly labelled by filename and companion receipt, not
represented as raw npm output. Raw upstream metadata is still unresolved. All
component hashes, licence fields and dependency edges remain unchanged. This
creates no software/redistribution/legal approval and no full inventory pass.
The twelve missing incorporated-licence-text findings, native/Nix/OCI closure,
image/layer/notice coverage and runtime compatibility remain pending. No new
application dependency, host operation, credential or resource is introduced.
