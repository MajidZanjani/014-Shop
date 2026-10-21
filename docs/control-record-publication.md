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
