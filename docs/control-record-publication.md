# Operator control-record preparation and publication contract

Status: offline validation and private candidate staging are implemented.
Publication/host installation and actual
socket, account, authentication and runtime qualification remain pending. No
publisher, root-record issuer or automatic refresh is supplied. A validated
candidate never establishes authority or actual host evidence.

`shop-operator-inspect validate-records` reads a private regular candidate file
through FD0; FD3 is unused. The existing owner/mode/stable-read rules apply. The
command uses the pinned standalone runtime but never loads live control files,
probes a process, connects to PostgreSQL, creates files or changes a service.
Ordinary Linux preparation is separate from the actual NixOS/Podman/ZFS checks.

The UTF8 JSON bundle has exactly schema_version (integer1), evidence_class
(`unverified-candidate`), records and artifact_base64. Maximum raw size is3MiB;
base64 must be strict and decode to the original reviewed artifact (at most2MiB,
or the smaller pinned bootstrap artifact limit). Original artifact bytes are
hashed exactly, never normalized. Records contains exactly these four files:

| File | Candidate consistency check |
| --- | --- |
| expected.json | Existing closed startup/storage/resource identity schema |
| database-process.json | Existing process schema and exactly matching startup record |
| operator-connection.json | Same complete database identity, fixed proposed Unix socket path and approved tool paths |
| schema-reconciliation.json | Same database identity, current inspection-only authority and exact original artifact |

The connection pg_control path must be the pg_controldata sibling of the approved
process executable. This binding is enforced by both candidate validation and the
inspection command. Each record is encoded as sorted-key compact ASCII JSON with
a final newline, at most32768 bytes. The library returns those exact proposed
record bytes privately; the CLI emits only their hashes and the raw bundle hash.
It does not emit payloads, process IDs, accounts, database identities or SQL.

Report status is candidate_validated, evidence_class remains unverified-candidate,
and publication_authorized, retry_authorized and reopening_authorized are all
false. Inner startup schemas use their existing actual-evidence labels; this tool
checks their shape, not whether the claimed observations happened. Never copy
fixture identities or promote a candidate report into qualification/approval.
Duplicate/unknown fields, mixed records, expiry, oversized input, altered artifacts
and extra files such as .env are denied. Keep input bundles, original artifacts
and any resulting review evidence private and outside Git, public output, Nix
store and ordinary logs. No credential belongs in this bundle. Provisioning later
uses the repository .env policy; if a genuinely needed credential is absent,
add its empty variable name/purpose and ask the owner to fill .env directly.

Before any actual publication, the operator must have actual read-only inventory,
proved new-shop ownership/UID/GID/database identity, exact shop mutation allowlist,
complete NixOS activation-impact review and the applicable exact write authority.
Review each value against retained observations and approved artifact bytes;
a digest match alone is not approval. The observation/inspection record never
renews an expired original write authorization. Existing services and resources
remain protected; this contract grants no host action.

The future publisher must satisfy these requirements:

1. Use only a proved new-shop staging scope in the exact allowlist and shop storage
   accounting. Reject existing/unknown objects rather than adopting them. Retain
   the prior generation and approval/observation custody privately.
2. Keep /srv/shop/control and every ancestor physically root-owned and not writable
   by group/others. Proposed control directory mode0750 and file mode0440 use only
   the separately verified shop read group; root owns the files. These are proposed
   new-object permissions, not instructions to chmod/chown an existing path.
3. Stage the exact approved canonical bytes, create exclusively, verify hashes and
   metadata, fsync each file and directory, and record the complete generation.
   Preserve original artifact bytes and recoverable prior-generation evidence.
4. Keep new-shop admission blocked during publication. Publish the complete physical
   generation atomically, or retain that barrier until the whole set is durable
   and revalidated. Symlink generation pointers are incompatible with the readers.
   No operation may observe an admitted partial/mixed generation.
5. Read back exact hashes/ownership/permissions and run the separately authorized
   bounded qualification. Do not infer permission to reopen from validation or a
   ledger observation. A changed PID/start time or other stale evidence requires
   separately reviewed fresh observation, never automatic discovery/repair.

If publication outcome is uncertain, keep admission blocked and reconcile the
read-back generation and retained receipts before any separately authorized
repair. Never blindly repeat a write, erase the ledger/evidence, roll back a host
generation or alter/restart protected resources. Actual publication durability,
partial-generation rejection, custody, positive socket/SCRAM/peer identity and
failure/recovery evidence remain unexecuted. See qualification-runner.md for the
single independent-runner specification; no resource is provisioned automatically.

## Local authentication evidence

The database-destination lane exercises a real disposable PostgreSQL18.6 Unix
socket with a synthetic SCRAM password and the operator's actual libpq connection
options and read-only ledger inspector. It checks not_recorded, recorded and
conflict reports, unchanged ledger rows, closed connections, wrong-password
rejection and rejection of a DELETE under the default read-only session.
Input files use the real private-file reader through fixture descriptor mapping.

This ordinary Linux test adapts the socket/PGDATA paths and uses mocked root
records, process probes, effective operator UID and socket ancestry/identity.
It uses the disposable cluster's administrative role, so it is not least-privilege
role qualification. No installed fixed socket, actual FD0/FD3 launcher transport,
peer-process/container binding, root-record publication, NixOS/Podman/ZFS or mx1
proof follows. Those positive transport and operational checks remain pending.
The production command's paths, privileges and closed connection contract are
unchanged; no host HBA, credential or service is modified.

## Library-only private candidate staging

`record_bundle.stage_candidate(data, parent_fd)` prepares a new private review
artifact under an already caller-owned directory FD with exactly mode0700.
It validates the candidate before creating anything, duplicates the supplied FD,
and exclusively creates `candidate-<raw-bundle-sha256>` mode0700. It accepts no
live control path, performs no discovery and is not exposed by the operator CLI.
The caller must supply a trusted private scratch directory; this does not prove
root-owned ancestor custody or an approved publication location.

The new directory contains the four canonical record files, exact original
`bundle.json`, exact decoded `artifact.bin` and `prepared.json` containing only
closed unverified flags and hashes. Each file is created exclusively mode0400,
written with bounded short-write handling, fsynced and read back through its FD.
The stage directory is fsynced before the final marker and again afterward;
the parent directory is fsynced. Final readback reopens every file without
following symlinks, verifies ownership/modes/single links/stable metadata and
compares exact bytes. The named candidate directory must still match its opened
inode. No chmod/chown/adoption of existing objects or automatic cleanup occurs.

`candidate_staged` still means unverified-candidate; publication_authorized,
retry_authorized and reopening_authorized remain false. A failure may leave any
partial set, including a final marker when a later sync/readback fails. Marker
presence alone is never completion or durable evidence. An existing full,
partial, file or symlink target is denied; no automatic repeat/overwrite/repair
is supported. Retain uncertain artifacts privately for explicit reconciliation.

Ordinary Linux tests execute only on new token-owned scratch files, including
short writes, zero writes, corrupt/replaced readback, nonprivate parents,
preexisting targets and sync failures before/after the marker. Successful fsync
calls do not qualify power-loss durability, filesystem/storage containment or a
complete atomic live generation. The private staging owner (or root) can still
alter these artifacts; this is not an immutable archive or a trusted issuer.
The separately authorized publisher, approval/observation custody, live admission
barrier, actual host installation and independent off-host recovery tests remain
unfinished. No production path, existing service or resource is changed.

## Read-only inspection of retained candidates

`record_bundle.inspect_candidate(original_data, parent_fd)` compares an existing
private candidate with the exact original input. It is library-only; the operator
CLI gains no command or path option. The input must still pass validation,
including the existing inspection expiry check. It never renews that expiry.
Canonical material and bounded file readback are shared with staging.

The parent must be caller-owned mode0700. Inspection opens the deterministic
candidate directory without following a symlink and requires its exact seven-file
set. Every file must be current-owner mode0400, regular, singly linked and exactly
the expected length/bytes, with stable metadata and matching named/opened inode.
It also checks directory identity/metadata after readback and rejects changes to
the named generation. Missing, extra, modified, linked or wrongly permissioned
files deny inspection; nothing is created, adopted, overwritten or repaired.

A successful report has status candidate_matches, remains unverified-candidate,
and explicitly sets durability_confirmed=false. Publication/retry/reopening
permissions remain false. This is a current byte comparison, not a historical
receipt proving that staging returned successfully. In particular, the same report
can result after a failed parent fsync left a full marker. Inspection performs no
fsync or implicit repair and does not authorize repeating staging, which still
rejects an existing target. Caller/root ownership and filesystem durability are
not qualified by this local helper; retain the original input and failure history
for separately authorized custody and publication decisions. Owner/root changes
after the observation are outside this snapshot guarantee.

## Prepared operator admission reader

The two live-source operator operations now require a separate physical
`/srv/shop/control-admission.json`, outside the replaceable control directory.
The reader walks root-owned non-writable ancestors without following symlinks,
opens an existing root-owned regular singly linked mode0440 file, and takes a
nonblocking shared flock for the whole operation. Missing, malformed or blocked
state and an exclusive writer lock deny entry before control/credential/SQL work.
No lock file, directory, admission state or authority is created by the reader.
Offline candidate validation and help do not acquire admission.

The closed record has integer schema_version1, state admitted, a64-character
lowercase hex generation identity, and record_sha256. The latter binds exact raw
control-file bytes; expected.json, database-process.json and
operator-connection.json are required. Additional keys are limited to
schema-reconciliation.json, schema-authorization.json, ledger-bootstrap.json and
bootstrap.json. All digests are lowercase SHA256. Generation/hash equality
identifies bytes; it is not evidence of approval or permission to reopen.

While this context is active, load_control rechecks the unchanged barrier and
requires every loaded record to belong to its manifest with its exact raw hash.
Schema admission also rechecks the barrier at every existing transaction guard.
Both operations verify it again before returning, so a late failed check cannot
escape as a successful command result; a schema outcome remains unconfirmed.
Descriptor metadata and the named lock inode must remain identical. Nested
admission contexts deny. Existing standalone library readers without an operator
admission context retain their prior behavior; this is not an application/worker
or universal bootstrap barrier.

A cooperating publisher must exclusively lock this same permanent inode, persist
and fsync blocked state before changing any generation, retain evidence and only
reopen under separate actual authority after complete durable qualification.
Never replace or unlink the lock inode: a new inode creates an independent lock.
Advisory locking cannot stop a privileged/noncooperating writer. Lock release on
exit does not make blocked bytes admitted. See Linux [flock(2)](https://www.man7.org/linux/man-pages/man2/flock.2.html).
The full publisher, actual state provisioning and installation remain unfinished;
the separately authorized library block precursor is described below.

Local scratch tests use actual independent-process locks, writer exclusion and
release, persisted blocked state after release, named-inode/metadata/bytes changes,
exact control hashes, closed schemas/modes and exception release. A synthetic
postcommit-return change suppresses the success report. Real scratch PostgreSQL
SCRAM inspection/schema commands now hold the actual lease while another process
is denied an exclusive lock. Physical production paths/root records remain
fixture-adapted; this neither qualifies power-loss durability nor grants actual
host publication, credentials, provisioning or reopening authority.

## Library-only persistent admission block

`control.block_admission()` prepares the first publisher transition only. It has
no CLI entry, installer, target/path argument, authority issuer, record-generation
writer or reopen function. The caller must be root, outside a reader context,
and possess a separately root-owned `record-publication.json` under the existing
control record custody rules. The closed authority contains integer
schema_version1, action block-control-admission, authorization_id (32 lowercase
hex), expires_at (future UTC YYYY-MM-DDTHH:MM:SSZ) and
current_admission_sha256 (64 lowercase hex). It authorizes only blocking these
exact current admitted bytes. It does not authorize generation publication or
reopening, and no such record is generated by the repository.

The helper opens only the existing physical admission inode for writing, takes
nonblocking LOCK_EX and validates the original admitted snapshot and exact
raw-authority hash. It rechecks authority before writes and after readback.
Before truncating, it revalidates the named inode and unchanged original bytes.
It writes the same generation/manifest with state blocked and a
block_authorization_id, handles short writes, fsyncs file and parent, and reads
back exact bytes and unchanged inode/owner/group/mode. It never replaces the
lock, changes permissions, creates paths, adopts objects, publishes controls,
refreshes authority, clears blocked state or automatically retries.

Successful output reports admission_blocked and local_fsync_readback_completed,
with durability_qualified/publication_authorized/retry_authorized/
reopening_authorized all false. Retain original bytes, scoped approvals and
recoverable custody externally before any actual operation. A failure after
truncation can leave empty, partial or complete blocked bytes; all deny readers.
Revocation after the write leaves blocked state and no success result. A later
explicit call still rejects blocked/malformed current state rather than repairing
it. Loss of acknowledgement requires read-only reconciliation, never repetition
inferred from a marker or receipt. Actual storage crash durability remains
unqualified even when local fsync/readback succeeds.

Local controls execute only on new owned scratch files: exact-current-byte
binding, closed/expired authority, root denial, real reader/writer exclusion,
unchanged inode, short/zero writes, sync failure, revocation before/after writes,
persisted deny after release and explicit-repeat denial. Production root
custody/authority remains fixture-adapted and no actual record is issued.
Before any host use, actual protected-resource inventory, new-shop ownership,
exact allowlist, activation-impact review and exact action authorization remain
mandatory. Full generation staging/publication, custody/receipt archive,
separately authorized reopening and independent recovery qualification remain
unfinished. No production, provider or protected-service action has occurred.

## Read-only reconciliation of uncertain admission blocking

`control.inspect_admission_block(original_bytes)` is a separate library-only
root operation. It requires an independent root-owned
publication-inspection.json record with integer schema_version1, action
inspect-control-admission-block, authorization_id (32 hex), a future UTC
expires_at, original_admission_sha256 (64 hex) and the original
block_authorization_id (32 hex). It never reads or renews the original write
authority. The supplied exact original bytes must form a valid admitted manifest
and match the inspection authority before opening the admission file.

A nonblocking shared lock permits observing denied state while excluding a
cooperating writer. The fixed root-owned physical file is read boundedly and
must retain its named inode/ownership/mode/single-link/stable metadata. Empty
bytes are accepted only by this observation path. Current bytes are compared
with the exact original and the canonical blocked form generated by the original
block ID. Status is original_matches, blocked_matches or different_bytes. The
last includes malformed/partial/empty bytes and a different generation/block ID;
it never treats such bytes as an admitted generation. Missing files, wrong
custody, excessive size, changed/replaced state or revoked/expired inspection
authority deny without a report. Authority and bytes are checked again before
returning.

The closed report contains status and observed_sha256 only alongside false
completion_confirmed/durability_qualified/publication_authorized/
retry_authorized/reopening_authorized flags. Matching bytes can reflect a failed
sync, stale/restored data or an interrupted operation; they do not establish
historical completion or safe next actions. The helper writes, fsyncs, repairs,
refreshes and reopens nothing. There is no new operator CLI or host installation.

Local tests cover original/exact-block/empty/partial/different-ID observations,
no writes/sync or old write-authority reads, raw-original hash binding, closed
inspection authority/expiry/root denial, writer contention, revocation and
concurrent byte/inode changes. A failed writer fsync can still yield
blocked_matches with all completion/permission flags false and reader admission
still denied. Root paths and authority provisioning remain fixture-adapted;
independent custody, full publisher and actual recovery qualification are pending.
