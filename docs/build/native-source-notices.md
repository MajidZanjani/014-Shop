# Cached Python and PostgreSQL source notice candidates

The exact upstream Python3.13.16 and PostgreSQL18.6 source archives already
exist in the local Nix store. The new required `native-source-notices` lane
binds them to source pointers/version/output membership in the current verified
operator closure and retained native observation, then verifies their original
exact archive SHA256 pins before parsing. It does not download/build/install
anything or extract archive files into a filesystem.

Actual collection and independent recheck retain nine named source candidates:
three in PostgreSQL and six in Python. The report records exact member names,
content hashes/sizes and source/output/derivation/native-evidence bindings.
Content-addressed files preserve original bytes. Required top-level PostgreSQL
COPYRIGHT and Python LICENSE are present. PostgreSQL scanned7944 members with
141525674 declared expanded bytes; Python scanned5272 members with110355801.

These are **upstream source candidates**, not proof that all nine texts are
licence terms or incorporated in the current Linux runtime. For example,
copyright.pl is an upstream copyright-maintenance script, and Python's source
includes Windows/Mac notices that need applicability review. No classifier
silently treats a filename as legal approval. The report keeps output notice
incorporation, source-offer-obligations satisfaction, inventory completeness and
legal approval false. Other native packages/source recipes/notices, modified
source/patch distributions, redistribution requirements and OCI layers remain
pending. Existing output notices, raw SBOMs and historical evidence stay unchanged.

The scanner verifies the bounded compressed archive before opening a streaming
tar reader, rejects unsafe/duplicate member paths and nonregular notice candidates,
never follows links, bounds100000 members/1GiB declared expanded bytes/64MiB
archive/10MiB per candidate and requires the exact top-level notice. Other archive
links are counted without traversal. These limits constrain this selected cached
archive scan; they are not a general hostile-archive processing service.

Run in the existing pinned shell using owned project scratch:

```sh
SHOP_TEST_SCRATCH=/home/claude/project/014-Shop/.scratch \
TMPDIR=/home/claude/project/014-Shop/.scratch \
nix develop --max-jobs 1 --cores 4 ./ops/nixos --command \
python3 scripts/check.py native-source-notices
```

Default re-observes current native/source bindings and requires exact retained
report/text bytes and file set. Explicit --write exclusively creates new report
and text directory; it rejects existing/partial evidence rather than repairing.
Writing is not crash-durable publication. Six negative/positive tests cover
identity/digest-before-parse, bytes, paths/duplicates/links, required notice and
size/count bounds. Scope-specific success never supplies full INVENTORY_PASS.
