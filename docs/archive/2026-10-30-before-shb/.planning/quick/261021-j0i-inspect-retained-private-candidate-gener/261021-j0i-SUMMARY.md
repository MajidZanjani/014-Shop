---
status: complete
---
# Inspect retained private candidates

Code9cbc570 adds library-only inspect_candidate(original_data,parent_fd), sharing canonical candidate material and bounded file readback with staging. It revalidates the exact original input (including expiry), opens only an existing deterministic private directory, requires the exact seven files/current owner0400/regular/single-link/exact bytes and stable FD/named inode metadata, and checks named directory identity/metadata after inspection. Parent must remain current-owner0700. No CLI command/path option, write, mkdir, fsync, repair, cleanup, expiry refresh or retry. Staging final readback now shares stricter named-inode and final file-set checks.

Actual local database-destination PASS3 checks/98 tests,9.415s; database-tools6/5,4.002s; operator-runtime4/10,2.382s; git diff --check passes. Eight added filesystem cases cover successful strictly read-only snapshot, partial/extra sets, altered originals/records/marker, symlink/hardlink/FIFO/directory/mode denial, exact input/private parent, failed parent-sync with marker, replaced file after FD read and replaced named generation. All passed first run; no failure or skipped tests. Packaged module bytes rebuilt/verified; CLI unchanged. Full all not rerun, no FULL_PASS.

Successful candidate_matches remains unverified-candidate with durability_confirmed=false and publication/retry/reopening_authorized=false. A candidate left by a failed parent sync can match identically; result cannot establish past staging success, durability or permission to repeat. Owner/root changes after observation remain possible. Keep original input/failure history for later separately authorized custody/publication decisions. Actual live issuer/publisher/admission barrier, fixed socket/peer/container binding/least-privilege roles, Django/application write/migration integration, generator/replica/images/licences/CI and off-host qualification remain unfinished. Phase02 and14/16/17 stay incomplete. No .env/credential needed/read, host/service/resource modification or purchase. Off-host runner remains unassigned and disruptive tests pending; do not repeatedly ask before remaining qualification stage.

Bounded quick task complete; whole plan14/Phase02 remains incomplete.
