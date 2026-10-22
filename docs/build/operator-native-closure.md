# Actual cached operator reference closure

The required `native-closure` lane observes only the already-realized
shop-operator-inspect package. It invokes Nix offline evaluation and read-only
path-info/derivation queries, then `nix store verify --no-trust --recursive` to
hash actual store bytes. It neither builds/downloads packages nor repairs the
store. Verification does not assert binary-cache signature trust.

October22 evidence records53 reachable objects with222931552 NAR bytes,
including Python, libpq, OpenSSL, glibc and their reference dependencies plus
the shop source/launcher/site artifacts. It binds every reference edge and NAR
hash/size to the root, and binds available local derivation recipes to matching
output paths. Fifteen distinct recipe objects are absent locally; they are
explicit missing-local-provenance findings, never invented source evidence.
Only two output objects contain named notice candidates under the scanner's
rules. Their paths, sizes and SHA256 hashes are recorded. Most native output
notice coverage remains unresolved; source archives/build inputs, embedded
notices, source offers and redistribution obligations require further review.

`operator-native-closure.json` is supplementary Nix closure evidence, **not a
standard SBOM**, complete software/component source inventory or OCI manifest.
Declared names/versions/source pointers come only from actual recipe fields;
missing fields remain null. A source store pointer alone establishes neither
upstream URL/hash nor source-offer availability. Multiple output objects may
belong to one component;53 is a store-object count, not53 unique packages.
Recipe/flake-lock file hashes bind the local producing inputs. Existing raw
CycloneDX inventories and licence evidence remain unchanged.

Run through the pinned shell:

```sh
SHOP_TEST_SCRATCH=/home/claude/project/014-Shop/.scratch \
TMPDIR=/home/claude/project/014-Shop/.scratch \
nix develop --max-jobs 1 --cores 4 ./ops/nixos --command \
python3 scripts/check.py native-closure
```

The default independently compares current observed evidence to the retained
report, so graph/source/notice changes fail. `check_native_closure.py --write`
exclusively creates a new report; it refuses overwrite. Report writing is not
a crash-durable publication protocol. Nix2.34.7's measured format4 derivation
JSON is required; other formats fail until explicitly reviewed. The scanner
walks directories without following symlinks and reads only bounded regular
named notice files. Absence of named files does not prove absence of embedded
notices. Cached derivation absence is reported without an automatic fetch.

The lane is required by `all`, with eight graph/hash/derivation/path/notice
rejection tests. Scope-specific success leaves inventory_complete, legal_approval,
runtime_qualified and oci_images_included false. Host runtime/transport/resource
compatibility, full native source/notice coverage, all four OCI images/layers
and production qualification remain pending.

## Preserving observed revisions

When current realized source/recipe/closure bytes change, a new explicit --write
creates `operator-native-closure-revisions/<report-SHA256>.json`. The original
operator-native-closure.json is never overwritten. Default verification derives
the current observation again and requires either the matching original report
or its exact content-addressed revision. No mutable current pointer is trusted.
The ten-module source bundle produces a later54-object operator reference closure;
that observed revision remains supplementary evidence with missing provenance,
notice/OCI/legal/runtime gates open. Nine controls now include historical-byte
preservation and deterministic revision naming.
