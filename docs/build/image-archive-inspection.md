# Local PostgreSQL image archive evidence

The existing pinned `shop-postgres` candidate was built locally on October22.
The output is `/nix/store/55fbc919a5fwhyc1gcsn1h6m63s4ipai-shop-postgres.tar.gz`,
125,653,410 bytes, SHA256
00ad3ec8402040624e9218f25fed63c5aa62a1a002a07dc3a3a1fab425021067.
It is a gzip-compressed Docker save archive, not an OCI distribution manifest.
Fifty-one ordered archived layer members match the config's declared DiffIDs.
The config ImageID is
sha256:2de6ade6a883cb6a376fe6239cbabc78a671007e6490c961f828eb93954f0e44.

[OCI image configuration terminology](https://raw.githubusercontent.com/opencontainers/image-spec/v1.1.1/config.md)
distinguishes the config-derived ImageID from ordered uncompressed layer DiffIDs;
these are also distinct from a distribution manifest digest. The collector records
archive bytes, archive manifest.json bytes, config bytes and each referenced
layer.tar member separately. No OCI distribution manifest was generated, queried
or pushed, so its digest is null. Hash agreement with declared DiffIDs is not
validation of inner layer filesystem semantics or proof of runtime compatibility.

`scripts/inspect_image_archive.py` uses bounded streaming and no extraction.
It rejects unsafe/duplicate outer paths, links/special outer members, multiple
images, oversized archive/member/metadata totals, duplicate JSON fields, missing
or unreferenced layers, config filename/hash mismatches and changed layer bytes.
It checks the prepared Linux/amd64 timestamp, nonroot10001:10001 identity,
working directory and exact environment defaults. It preserves exact config and
ordered hashes, without running its command or interpreting inner layer paths,
whiteouts, links, native binaries or licence coverage. The source input is a
stable no-follow regular file; named-inode/metadata changes deny inspection.
This is deliberately not a general OCI conformance validator or image sandbox.

The content-addressed report in `docs/evidence/t02/image-archive-revisions/`
reproduces on independent rescans. `docs/evidence/t02/image-builds/` retains the
exact successful local Nix builder log and a provenance record tying derivation,
archive/config/report hashes and selected unchanged source hashes to implementation
commit a02e5a5. Selected input hashing is not a complete build dependency inventory.
The original empty candidate-evaluation image report remains historical and
unchanged. The archive stays in this local Nix store; independent retention and
complete-pool-loss recovery are unqualified. No permanent artifact retention or
second independent realization is claimed.

The build used max-jobs1/cores4 and required thirteen small derivations; its dry
run listed1.1MiB extra cached build-tool downloads. Two initial setup attempts
failed: the Nix build user could not traverse private project ancestors, then Nix
rejected a world-writable /var/tmp ancestor. Existing permissions were preserved.
The successful build used a new exclusively created scratch directory under
/var/lib, with6.3GiB local free space and non-world-writable ancestors. No global
Nix configuration or shared storage cleanup was performed; only newly created
scratch paths were used. Shared /tmp was too small. The exact successful command
and scoped scratch path are retained in the build record.

Eight malformed-input tests and deployment evaluation16 checks/31 tests pass.
Actual archive inspection and independent rechecks pass51 layers. No image was
imported or run, no PostgreSQL cluster initialized, no registry push or mx1/service
operation occurred. Rootless/user-systemd/cgroup/storage/entrypoint execution,
inner payload/native notices, all other images, actual OCI manifests, independent
two-build comparison, off-host recovery and full phase acceptance remain pending.
Production Django remains closed.

To recheck locally, run the pinned development shell's Python with
`python3 -B scripts/inspect_image_archive.py --archive <retained-nix-store-path>`.
`--write` exclusively creates a content-addressed inspection report and refuses
existing output. It does not rebuild, import, execute, overwrite, repair or publish
the image.
