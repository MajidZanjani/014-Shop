---
status: complete
---
# Private unverified candidate staging

Code542e2d8 adds library-only record_bundle.stage_candidate(data,parent_fd). It validates before writes, requires a caller-owned mode0700 parent descriptor, creates only an exclusive candidate-<raw-bundle-hash> directory, stages the four canonical records plus exact bundle.json/artifact.bin, and creates prepared.json with hashes and unverified flags. Files are exclusive0400/current-owner/single-link, writes handle short writes and reject zero progress, fsync/readback checks exact bytes and stable metadata; stage/parent directories are fsynced, final file reopening rejects symlinks/substitution. Caller FD stays open. Existing targets are denied; no adoption, chmod/chown, overwrite, discovery, automatic cleanup/retry or operator CLI publication command.

Actual local evidence: database-destination3 checks/90 tests,8.922s (eight new filesystem tests); database-tools6/5,3.966s; operator-runtime4/10,2.379s. All exit0, no failing runs. New cases exercise actual private scratch files, modes/ownership/hashes/bytes, invalid inputs/nonprivate parents, existing full/file/symlink targets, short/zero writes, corrupt and replaced readback, first sync failure and parent-sync failure after marker. Partial files are retained and repeat denied. Final marker can exist after failed sync, so marker presence never means successful/durable completion. Package lanes rebuild exact updated module bytes; CLI unchanged. git diff --check passes.

Status remains unverified-candidate; publication/retry/reopening_authorized=false. Supplied parent is trusted caller scratch, not proof of root-owned ancestor/allowlist custody. Owner/root can alter staged files; no immutable archive or power-loss guarantee. Complete live generation publication, separately scoped authority/receipts, admission barrier, positive fixed socket/peer/container transport, least-privilege roles, application/Django writes/migrations, generator/replica/OCI/notices/full CI and independent runtime/recovery qualification remain unfinished. Phase02/14/16/17 remain incomplete. No .env read/needed credential, host write, existing-service/resource change or purchase. Off-host runner unassigned; disruptive tests pending, no repeated question or full readiness claim.

Bounded quick task completed; no phase/task14 completion inferred.
