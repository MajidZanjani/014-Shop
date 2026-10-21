---
phase: 02-reproducible-application-and-deployment-skeleton
plan: "14"
status: implementation_pending
requires: [02-10, 02-11, 02-13]
provides: [candidate-image-derivations, disabled-shop-module, candidate-quadlets, readonly-storage-guard]
requirements-completed: []
---
# Phase 2 Plan 14: Candidate foundation; implementation and qualification pending

Prepared four immutable-build image derivations using the existing qualified interpreter/PG and six exact hash-locked runtime wheels; nonroot numeric identities, private Quadlet network, loopback-only gateway, narrow read-only secret mounts and no auto-init PostgreSQL entrypoint. The disabled Nix module has no proposed default UID/GID/ranges, checks declared overlaps, requires explicit digests/qualification, declares only the shop account ancestor's proposed 200% CPU/6G high/8G max/1024 tasks and uses a shop-only linger action without changing global policy. No global Podman/firewall/journal/mount/helper activation. Definitions are candidates, not deployed/qualified units.

## Actual evidence

Pinned dispatcher deployment-eval passed 9 checks and 4 guard tests, 1.396 seconds including dispatcher overhead. Four OCI derivations evaluate; disabled module creates no shop account/linger or global Podman activation; a synthetic NixOS fixture has the expected account ancestor and unchanged global linger policy. Positive/negative unit controls cover closed attestation/paths, quota constants and exact DB identity comparison/decoy rejection. Full build/boot commands were separately confirmed nonzero with their pending markers. No image build, Quadlet generation/container run, host inspection, cgroup/storage change or real credentials.

The read-only guard compares machine/account/mount/ZFS quota/PG system identifier/checksums and current process ancestor. It never initializes or repairs storage. A passing guard would not prove all-descendant containment or protect every future mutation: the full operator/bootstrap/mutation wrapper is still unimplemented. Do not misread a comparison unit test as a real decoy-cluster write-denial demonstration.

## Explicit remaining work

- Review exact new runtime components/closure/bundled licences; old approval does not extend. docs/evidence/t02/runtime-review.json records inert pinned versions/source identities only (Podman5.8.8/systemd260.5/Caddy2.11.7 and helpers), not approval or compatibility.
- Qualify build resources before image builds; current project filesystem has about 2.4 GiB free. No shared files/store/caches were removed or allocation changed. Actual images/manifests/digests are unbuilt; candidate tags cannot activate module units.
- Complete independent-cluster bootstrap and per-mutation destination wrapper, selected rootless runtime/generator/user config, storage declarations and exact new-account prerequisites. The module intentionally will not repair unsupported existing host policy.
- ops/runtime/offhost-cases.json is an explicit pending case/fixture matrix, **not an executable lifecycle suite**. ops/nixos/tests/shop.nix is pure synthetic evaluation only. Finish the reproducible replica driver for restart/OOM/quota/helper escape/destination/secret/recovery before any lifecycle pass.
- Independent runner is unassigned. No disruptive execution on mx1/its guests. Full boot refuses authorization absence and still refuses missing fixtures even if a runner record is later supplied. T11 actual host and T12 full-pool recovery remain separate.

## Findings

NixOS assertions have lazily evaluated failure messages; evaluating messages for passed assertions hit an upstream absent cycle attribute, fixed by rendering passed messages as passed. NixOS defaults general linger management on; the fixture now verifies its policy is unchanged and shopsvc.linger stays null, rather than incorrectly requiring the global policy off. Neither discovery permits changing the existing host.

Expanded owned paths (runtime guard/case/wheel metadata, network Quadlet, unit tests and inert review record) were declared in the GSD manifest before edits. No phase/BUILD requirement is complete from this partial slice. Continue independent profile/inventory work while completing this remaining implementation; do not count summary presence as completion.
