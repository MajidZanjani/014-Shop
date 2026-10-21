# Operator control-record preparation and publication contract

Status: offline validation is implemented. Publication/host installation and actual
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
