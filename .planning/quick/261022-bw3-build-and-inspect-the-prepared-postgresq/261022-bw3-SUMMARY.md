---
status: complete
evidence_class: local-built-docker-archive-inspection
---
# One local PostgreSQL candidate archive

Built existing pinned shop-postgres derivation wv31yrg53saxdpfsy600yzywlllwgisv into /nix/store/55fbc919a5fwhyc1gcsn1h6m63s4ipai-shop-postgres.tar.gz.125653410 bytes, archive SHA25600ad3ec8402040624e9218f25fed63c5aa62a1a002a07dc3a3a1fab425021067;51 archived layer.tar hashes match ordered config DiffIDs. Config ImageIDsha256:2de6ade6a883cb6a376fe6239cbabc78a671007e6490c961f828eb93954f0e44. No OCI distribution manifest digest invented. Content-addressed archive inspection and actual local builder log/provenance retained. Selected flake/lock/entrypoint bytes match implementation commit a02e5a5; not full input/native inventory.

Bounded streaming no extraction/import/run. Checks exact single candidate, config/image-ID and referenced layer byte consistency, safe outer paths/types/names, archive/expanded/member/metadata bounds and file stability. Inner tar semantics, runtime/native licences and general OCI conformance unvalidated. Eight scanner tests pass0.019s (initial0.018s), deployment16/31 2.133s, actual collection plus independent rescans51 layers pass. Original candidate-only image inventory unchanged.

Two actual initial build setup failures: build user denied traversing project-private ancestors; Nix refused world-writable /var/tmp ancestry. No existing permissions/global config changed. New exclusive /var/lib/shop-image-scratch-VjIrVLVQ succeeded with max-jobs1/cores4, local /var6.3GiB free. Earlier owned .scratch/oci-builds and /var/tmp attempt paths retained/unmodified; no shared cleanup. Dry run13derivations/12 paths1.1MiB fetch3.8MiB unpacked; bounded existing graph, no dependency choice change. Successful actual Nix log retained, one image realization only; no failed test.

No image import/container/cluster/host/provider action, runtime secrets or activation. Archive local Nix store only, independent retention unqualified. Other images, inner payload/native notice/OCI manifest/two-build/full CI/off-host qualification and14/16/17 remain pending. Production closed and safe application/host evidence boundary unresolved.
