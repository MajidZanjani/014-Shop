# Schema migration boundary

Status: repository implementation in progress. Production and bank-sandbox Django
connections remain blocked by `shop.db.unqualified`. No installed operator executable, approved
host record, role provisioning or production migration is supplied here.

`ops/runtime/schema_authorization.py` accepts an already connected idle autocommit
connection and immutable artifact bytes. It loads `schema-authorization.json`
through the bounded root-owned `/srv/shop/control` record reader. Record issuance,
replacement and access custody require their separately authorized operational
procedure; this library never creates or refreshes a record.

The record has exactly these fields:

| Field | Required value |
| --- | --- |
| schema_version | Integer 1 |
| action | `apply-reviewed-schema` |
| authorization_id | 32 lowercase hexadecimal characters |
| expires_at | Future UTC timestamp `YYYY-MM-DDTHH:MM:SSZ` |
| artifact_sha256 | SHA-256 of the exact artifact bytes, 64 lowercase hexadecimal characters |
| migration_id | Lowercase identifier, starts with a letter, at most 96 characters; letters, digits, underscore, hyphen |
| database | Complete expected database identity from the approved process record |

The artifact is UTF-8 JSON with exactly `schema_version` (integer 1),
`migration_id` (matching the authorization) and `statements` (array of reviewed SQL
strings). Duplicate JSON keys are rejected. The artifact limit is 2 MiB including
JSON escaping/formatting; decoded statements also have independent limits of
64 statements, 64 KiB each and 1 MiB total UTF-8 SQL. Hashing precedes parsing;
whitespace-only changes require a new explicit authorization. Nothing normalizes
or reopens the reviewed artifact after validation.

The database identity must equal the pinned root-owned process record. Before
locking, before each statement and before commit, the underlying schema primitive
checks fresh runtime evidence and live SQL identity/durability on the same
transaction connection. The authorization and process records are reloaded for
each runtime callback; removal, expiry or any changed content denies completion.
There is no automatic target discovery, record refresh or retry. Expiry is based
on the host UTC clock, whose trustworthy operation remains an operational
prerequisite. Revocation after the final check cannot undo an already committed
transaction; record replacement is not a cross-system atomic revocation protocol.

Only table/sequence/index SQL prefixes are accepted; prepared execution rejects
stacked commands. All statements remain trusted code, including expressions.
Rollback covers transactional PostgreSQL effects, not arbitrary external effects
of trusted SQL functions. The cooperative transaction advisory lock coordinates
only callers using the same path; role restrictions must separately prevent
bypasses. The caller must not interpret a digest or synthetically generated test
record as evidence of human approval.

The authorized path now uses `execute_schema_migration` to write a durable ledger
row in the same transaction as the schema statements. The ledger must already
exist as `shop_control.schema_migrations` under the exact migration owner. The
separate review/bootstrap artifact is `ops/postgresql/schema-ledger.sql`; it is
never automatically executed or used to adopt an existing object. A missing
ledger fails closed. The explicit destination-guarded bootstrap library is described below;
owner/role and record publication, command integration and actual deployment
authorization/qualification remain unfinished.

Under the schema advisory lock, the transaction takes a bounded table lock and
validates the ledger relation, schema/table owner, durable ordinary table shape,
columns, nullability, constraints/indexes and lack of rules, triggers, inheritance,
RLS and nonowner write/create grants. PostgreSQL18 not-null constraints are checked
explicitly against the [official pg_constraint catalog](https://www.postgresql.org/docs/18/catalog-pg-constraint.html).
The same relation OID and contract must survive the reviewed DDL; replacing the
ledger with an identically shaped empty table is rejected. These checks do not
protect history against a privileged owner or prove all inherited-role rights.
Production role/grant qualification is still required.

For a new migration, the transaction inserts migration ID, artifact digest,
authorization ID and a database transaction timestamp, then performs its final
runtime/authorization/SQL check and commits. A failure rolls back transactional
DDL and the ledger insert together. Migration ID is the primary key and
authorization ID is independently unique. A new explicit call with the exact same
three values returns `already_applied` without executing the artifact statements;
a different digest/authorization for that migration, or reused authorization for
another migration, is a conflict. The authorization must still be valid even for
a repeated call. The library never automatically retries an uncertain commit.
`already_applied` reports the ledger decision, not a schema-drift audit or proof
that external effects remain intact.

An uncertain result requires a separately initiated, authorized reconciliation
against the same positively identified database and original artifact. The local
test repeats a call after synthetically discarding its result; it does not inject
a real transport/process failure. After restore, do not infer safety from the
restored ledger alone: reconcile external evidence and effects under the recovery
barrier before exposing access or authorizing new work. Actual failure/restore
qualification remains pending on the independent off-host runner.

Django migration generation/recorder integration, operator command/credential and
private transport, root-owned record publication, immutable host-side packaging,
bootstrap/role qualification and actual off-host runtime qualification are
still pending. Direct lower-level `execute_schema_batch` remains an internal
untracked schema primitive for separately authorized bootstrap/tests; deployment
migrations must use the authorized ledger path. No mutation/deployment CLI is supplied.
Do not remove the production Django connection gate before those boundaries are
covered.

`ops/runtime/ledger_bootstrap.py` supplies the separate explicit library path for
initial creation. It loads root-owned `ledger-bootstrap.json` through the same
bounded reader. The record uses the fields above but requires action
`initialize-new-schema-ledger`, reserved migration ID `shop_ledger_bootstrap_v1`,
and the exact source pin in `ledger_bootstrap.ARTIFACT_SHA256`. Supply the exact
bytes of `ops/postgresql/schema-ledger.sql`, at most 32 KiB. The pin, approval and
actual bytes must agree; comments/whitespace are part of those bytes. The four
statements are decoded only after the pin check. This is a fixed artifact decoder,
not a general SQL-script parser; changing the artifact requires review and a code
pin update.

Bootstrap uses the same positively identified connection, runtime and process
record, live durability checks, transaction/time bounds and cooperative schema
lock. It rejects any existing `shop_control` namespace, including an empty one,
a matching ledger or a previous successful bootstrap. It rechecks authorization,
runtime and SQL identity before each CREATE/REVOKE and before receipt insertion
and commit. It validates the new ledger contract, so unexpected inherited write
grants also deny and roll back. Initial creation and a reserved bootstrap receipt
(with pinned artifact digest, authorization ID and transaction timestamp) commit
together. Ordinary later migrations use distinct migration/authorization IDs
through the ledger path.

No automatic creation, adoption, cleanup, authorization issuance, target discovery
or retry is provided. A repeated bootstrap is a denial, even with the original
approval; uncertain completion needs read-only reconciliation of the positively
identified database and retained evidence. It must never trigger ledger removal
or a blind bootstrap retry. Actual loss of an acknowledgment, crashes and restore
remain unexecuted qualification checks. This library does not create the database,
roles, account or control records, connect/read a password, install itself or
expose a CLI; production Django access remains blocked.

`ops/runtime/schema_reconciliation.py` supplies a separate read-only observation
library for uncertain schema/bootstrap results. Root-owned
`schema-reconciliation.json` has the authorization fields above plus
`artifact_kind` (`schema` or `ledger-bootstrap`) and requires action
`inspect-schema-outcome`. Its `authorization_id` refers to the original operation;
the new record grants inspection only. It must have a current expiry even when
the original write record has expired or been removed. Neither write record is
loaded or renewed. Supply the exact original artifact bytes: schema JSON is
validated under the inspection action, and bootstrap bytes/ID must match the
fixed source pin and reserved bootstrap ID. The database/process identity must
still match the separately approved process record. Record issuance/custody and
CLI integration remain pending.

The inspection opens one bounded READ ONLY, REPEATABLE READ transaction, checks
runtime/live SQL identity before and after its ledger query, and rechecks current
inspection/process records. It creates no schema, ledger row or advisory lock and
executes no artifact statements. A partial or malformed ledger is a denial;
a genuinely absent namespace is an observation. Results contain only
`schema_version` (1), `status`, `retry_authorized` (false) and
`reopening_authorized` (false), without artifact, database, role or authorization
values. Status has these meanings:

| Status | Point-in-time observation |
| --- | --- |
| recorded | One ledger row matches migration ID, digest and original authorization ID |
| not_recorded | Neither the migration ID nor original authorization ID is recorded |
| conflict | A migration/authorization row exists but the complete identity differs |
| ledger_absent | The shop_control namespace is absent in this snapshot |

None of these observations authorizes a write retry, ledger initialization,
repair or reopening. A concurrent commit after the query can make not_recorded
stale immediately; the local two-connection test demonstrates this and requires
a fresh inspection to observe that commit. A restored ledger can likewise omit
external evidence or effects. Operators must reconcile retained external evidence,
original artifacts, identity and recovery-barrier state before separately
approving any next action. This library does not verify schema drift, completed
external effects, backups, restore currency or safe reopening. Actual lost-result,
process/transport failure and restore qualification remain pending off-host.

Local tests use disposable PostgreSQL target/decoy clusters and synthetic records.
They adapt only the fixed PGDATA comparison to owned scratch paths. They do not
establish rootless process/storage/resource containment or production readiness.

The inert source bundle is available as the flake package
`shop-database-tools-source`. It contains exactly eleven explicitly selected Python
modules plus the pinned SQL artifact and a closed SHA-256 manifest. Individual
source bytes are copied into separate store files; the bundle does not retain a
reference to the entire repository source. It contains no interpreter, dependency
environment, executable launcher, host account/configuration or authorization
record. No NixOS module installs it and no service uses it automatically.

The `database-tools` verification lane builds this source bundle, compares all
packaged bytes and its manifest with the selected sources, checks exported
metadata and exact direct store references, imports the modules from the actual store path using isolated
Python and the existing hash-locked runtime dependencies. Import controls deny
database connections and control-record reads. Actual packaged help and mutation-
command denial are also exercised in isolated child processes. This is actual source-bundle build
and local import evidence only; it does not build an OCI image or qualify a live
operator tool. The separate candidate launcher/runtime described below is now built locally;
its native closure/licence review, credential/transport qualification, host
installation and operational qualification are still pending. The source manifest is not a complete runtime SBOM or licence review.

The prepared `operator_inspect.py` module now supplies `inspect`, offline `validate-records` and `--help`.
It is source code in that inert bundle, not an installed executable or qualified
operator runtime. No mutation/bootstrap command exists. Its standalone entrypoint
scrubs the environment before handling the command; invocation must use the
reviewed isolated Python/dependency runtime. That runtime must load the pinned
libpq before the entrypoint scrub; frozen local tests supply the existing verified
library path and pure-Python Psycopg implementation. The separate pinned launcher/runtime below replaces environment-based library
discovery. Actual client/server authentication and host qualification remain pending.

The command takes no DSN, password, artifact pathname or tool-path arguments. FD0
must be an already open private regular artifact file, at most2MiB. FD3 must be an
already open private regular credential file,16–4096 bytes, decoded exactly as
UTF8 without trimming; NUL is rejected. Each file must belong to the current
account, mode0400/0600, with stable identity/ownership/mode/size/modification
metadata while read. Inputs are read from offset0 without advancing the caller's
offset, and marked non-inheritable. Helpers receive null stdin; no artifact or
credential is sent to helper arguments/environment. Future credential provisioning
follows the repository .env policy; no real credential or .env value is needed by
these local preparation tests.

A separate root-owned `operator-connection.json` contains exactly schema_version1,
the complete approved database identity, socket_directory, zfs and pg_control.
The latter two are explicit approved Nix-store binary paths ending in /bin/zfs and
/bin/pg_controldata. The socket directory is fixed to the proposed
`/srv/shop/tmp/postgres-socket`, within the existing shop tmp boundary. Every
ancestor is opened without symlink traversal and must be root/account-owned and
not group/other writable; the directory and socket must belong to the shop account
with mode0700. Socket identity and connection record are compared before/after
connection and observation. The caller must be the nonroot approved shop UID.
Current Quadlets/HBA do not expose or authorize this proposed host-side socket:
mount/path/auth/account/role provisioning and actual identity/race/peer/runtime
qualification remain pending. The command creates or changes none of them.

The process/database/inspection authorities and exact artifact are checked before
credential use or connection. Connection parameters are explicit: only the fixed
Unix socket, approved database/role/port, two-second connect timeout, null passfile,
UTF8 and default_transaction_read_only=on with bounded search_path/query/lock
settings. `require_auth=scram-sha-256` rejects a trust-only server, as specified by
[PostgreSQL18 libpq](https://www.postgresql.org/docs/18/libpq-connect.html).
Local tests prove that negative case, not a qualified positive SCRAM exchange or
actual end-to-end operator connection. SQL inspection still uses its separate
read-only transaction/identity checks. Results retain only the closed observation
fields; denials emit a fixed event without argv, exception, libpq detail or private
bytes. Connections close on both success and post-connect denial. Original
inspection records are rechecked by the library; no write retry/reopening is
authorized. Production Django connections remain blocked.

The separate flake package `shop-operator-inspect` now builds a standalone candidate
launcher. It contains the existing exact Python3.13.16, only the already locked
Psycopg3.3.6 wheel in its added site directory, the source bundle and an isolated
driver. Pip is used for the offline, hash-checked build and is not installed into
the operator site. No Django/Gunicorn dependency is added to that site. No NixOS
module installs the launcher, account, record, socket, role or credential.

The shell launcher clears ambient environment before executing the pinned bare
Python with `-I`. The driver again sets its closed import environment, uses exact
Nix-store libpq18.6 and libc paths for Psycopg's two ctypes discovery requests,
then restores the original discovery function. It requires the exact interpreter,
pure-Python Psycopg implementation, libpq version180006 and sole added Psycopg
version before importing the approved command source. No compiler, pg_config or
host library lookup is used for those imports. The command then applies its own
closed execution environment. Python startup/import/identity failures emit only
the fixed denial event; the test-only synthetic startup-failure package confirms
that exception detail and traceback are suppressed.

The `operator-runtime` lane actually builds the main launcher and an independent
synthetic import-failure fixture, verifies exported identities against the existing
runtime lock and source artifact, and executes8 metadata/process controls. Actual
help works with absent PATH and hostile PG/Python/library environment settings;
a shadow module is ignored, mutation/secret options are rejected without echo,
invalid private input denies without connecting, and synthetic import failure
returns the fixed denial. The fixture is a flake check output, not a deployable
alternative or runtime fault injection against a service.

Metadata keeps installed=false, runtimeQualified=false and productionActivation=false.
These tests qualify local build/native startup/denial only. Positive SCRAM/peer/
socket/account/resource operation, FD3 use through a real connection, separately
authorized record publication and host installation remain unexecuted. Native
closure/SBOM/licence and full CI/reproducibility evidence are still pending. No
credentials are bundled and the current closed HBA/Quadlet configuration is
unchanged. This candidate does not authorize deployment, mutation retry or safe
reopening, and production Django access stays blocked.

Offline preparation now also validates the four-record control bundle and returns
only an unverified hash report. It checks common startup/database identity and
binds pg_controldata to the approved process executable. The inspection command
uses that same binding check. This does not issue or publish root records, perform
host observations or grant activation. The exact bundle/publication requirements
are in [control-record-publication.md](control-record-publication.md); publication
and operational qualification remain pending.

## Source-only schema apply integration

`ops/runtime/operator_schema.py` prepares a separate `apply-reviewed-schema`
source command. It is included in the inert source manifest, but the existing
standalone `shop-operator-inspect` launcher still rejects all mutation commands.
No mutating launcher is installed or qualified; no root record, role, socket,
credential or runtime configuration is provisioned by this code.

The source command requires private artifact FD0 and credential FD3, the exact
nonroot shop UID and the same fixed Unix socket/tool/process/record controls as
inspection. It validates the exact active schema authorization and immutable
artifact before reading credentials or connecting. Its explicit SCRAM session
is writable only for this reviewed schema operation; production Django remains
blocked. It exposes no DSN/path/role/bootstrap/retry arguments.

`execute_authorized_schema(..., admission_check=...)` can now call an additional
caller transport-admission callback inside every runtime/SQL guard, including
before DDL, ledger insert and commit. A provided callback must return exactly
True; exceptions/false deny. The source command uses this to recheck its original
connection record, process record, schema authorization and socket identity at
each guard. Existing root-authority/runtime/live-SQL checks still execute. No
callback can grant schema authorization or replace the underlying guard.

Connections close on success or failure; no automatic reconnect/retry. Successful
output contains only schema_version1, status applied/already_applied and false
retry/reopening flags. Any failure emits a fixed schema_outcome_unconfirmed
event, including failure after commit or while reporting a result. It never
claims that no effects occurred. Use the independently authorized read-only
inspection and retained external records to reconcile uncertainty; no observation
alone grants retry or safe reopening. Exact authority can permit an explicit
same-artifact call to return already_applied without repeating DDL.

Local tests exercise actual SCRAM/private-FD source schema apply and explicit
already_applied observation on a newly owned disposable PostgreSQL cluster,
with matching schema/ledger rows and closed connections. Runtime records, socket
ancestry/identity, UID and canonical PGDATA are fixture adaptations. The fixture
uses its administrative role, so it does not qualify least-privilege schema
access. Separate real-PostgreSQL cases deny admission at every transaction guard
and leave neither schema nor ledger effects. Package tests import the eleven-module
source set without connections and exercise source help/bootstrap denial. Full
pinned executable startup/error/FD transport, exact schema role privileges,
root-record publisher/admission barrier, Django recorder/migration integration,
actual host/runtime and independent failure/recovery qualification remain pending.


## Separate pinned schema candidate launcher

The flake now exports `shop-operator-schema` separately from
`shop-operator-inspect`. Both use the same exact Python3.13.16, Psycopg3.3.6
site, libpq18.6, libc and eleven-module source artifact. The shared driver selects
only one declared module at evaluation time; runtime arguments cannot change
command modules. The inspection executable continues to reject schema writes.
The schema executable accepts only its existing `--help` and
`apply-reviewed-schema` interface. Its help retains the historical source-only
wording; the source is now packaged, with operational qualification pending.

Both shell and Python startup clear ambient environment and preserve isolated
imports. Schema startup failures emit the same constant
`operator.schema_outcome_unconfirmed` event as command failures. Metadata for
the schema executable declares readOnly=false, installed=false,
runtimeQualified=false and productionActivation=false. It is never installed
by the NixOS module or added to application/container startup.

The required operator-runtime lane builds both candidates plus three check-only
outputs. Seventeen controls include actual native help under hostile library,
Python and PostgreSQL settings, ignored shadow source, closed arguments,
missing-authority denial and import-failure privacy. A synthetic check-only
module verifies FD0/FD3 private-file contents, owner/mode and cleared driver
environment through the actual shell/Python exec chain. It has no database
imports or apply implementation. This verifies descriptor transport, not a
positive schema connection through real records or the intended nonroot role.
The real local SCRAM/source/schema admission suite remains separate fixture
adapted evidence (107 tests); least-privilege and actual runtime qualification
remain pending. Native reference evidence still covers inspection only; sharing
native dependencies does not establish complete schema/package/OCI inventory.

No root record, role, socket, credential, installation, live application access,
retry or reopening permission is created by building or testing this candidate.
The publisher/custody/admission barrier, exact role provisioning, Django writes
and migration recorder integration, executable independent replica and full
runtime/human review gates remain unfinished.

## Restricted schema-role local qualification

The real disposable SCRAM/source-command fixture now connects directly as a
separate `schema_candidate` login with NOSUPERUSER, NOCREATEDB, NOCREATEROLE,
NOREPLICATION and NOBYPASSRLS. It owns only the fixture's `shop_control` ledger
schema/table and a dedicated `shop_app` schema. The administrative fixture
connection creates those objects and transfers ownership; no production role
provisioning SQL or automatic ownership adoption is supplied.

The current identity query needs both EXECUTE on
`pg_catalog.pg_control_system()` and membership in `pg_read_all_settings`.
Explicit calls with neither privilege and then only the function privilege fail
before schema/ledger effects. With both, the guarded source command applies and
recognizes the exact migration through SCRAM. The latter membership exposes all
configuration settings, including settings normally restricted to superusers;
it is broader than access to data_directory alone and requires review for the
isolated shop cluster. See [PostgreSQL predefined roles](https://www.postgresql.org/docs/18/predefined-roles.html).

Actual ACL denials cover database creation, role creation, SET ROLE to the fixture
administrator, server-file reads, creating a public-schema table and modifying
an unrelated administrator-owned table. A reviewed two-statement artifact first
creates a table in shop_app and then attempts forbidden public-schema DDL; the
later denial rolls back both the first table and its prospective ledger entry.
These are local database privilege observations, with the existing synthetic
root records/process/socket/UID and PGDATA adaptations. They do not qualify
host-side fixed socket/peer admission, a production grant set or role provisioning.

Schema ownership allows the migration role to change its own ledger and objects
outside this command. This fixture does not establish tamper-proof history or a
complete least-privilege model, and the role-admission predicate below is only a bounded privilege check.
Publication/custody, admission barriers, complete object/grant attestation,
Django integration and independent runtime/recovery
qualification remain pending. Production Django remains closed.


## Enforced schema-login admission

The separate schema command now checks the actual SQL session after connecting,
inside every schema admission callback and after its outcome. It requires
current_user=session_user, LOGIN, no SUPERUSER/CREATEDB/CREATEROLE/REPLICATION/
BYPASSRLS attributes, and no ownership of the current database. A recursive walk
of pg_auth_members rejects every reachable membership except
pg_read_all_settings, including membership edges with INHERIT/SET disabled.
Membership ADMIN OPTION is also denied on the login and reachable roles. Cycles
are bounded by the recursive UNION; existing session statement timeouts bound the
query. No role names, credentials, grants or ownership are changed by this check.

False/missing predicate observations or SQL errors deny through the existing
constant outcome-unconfirmed error path and close the connection. With a live
connection, every existing authority/socket/runtime/schema transaction admission
also runs this role check. Real disposable tests cover each forbidden attribute,
NOLOGIN, permitted metadata membership, membership administration, transitive
membership and database ownership. The SCRAM fixture promotes CREATEDB after the
first DDL statement; the next check observes the change and rolls back the DDL
without adding a ledger row. This is an explicit test action on an owned scratch
cluster, not a production fault test.

The predicate is deliberately conservative about role membership. It does not
inventory arbitrary directly granted function/object/parameter privileges,
SECURITY DEFINER routines, historical ownership or every other database in the
cluster. Ledger/app ownership still permits changes outside this command.
Concurrent privileged changes after the final check cannot be undone, and a
postcommit denial still reports an unconfirmed outcome. Production provisioning,
complete grant review, root-record custody/barriers, isolated runtime and
independent restore reconciliation remain prerequisites.


## Connected Unix peer admission

Both command paths now inspect the actual connected libpq socket on Linux.
A private duplicate of connection.fileno() must report AF_UNIX/SOCK_STREAM via
SO_DOMAIN/SO_TYPE, and its SO_PEERCRED PID/UID/GID must equal the approved
postmaster PID and startup host UID/GID. Only the duplicate is closed. The check
performs no send/receive and preserves protocol bytes and the libpq descriptor.
It runs before/after read-only inspection and at every connected schema admission.
Any mismatch/error follows the existing fixed-denial or unconfirmed-outcome path
and closes the command connection without reconnecting.

Linux [unix(7)](https://www.man7.org/linux/man-pages/man7/unix.7.html) defines these
credentials at connect/listen/socketpair time. They identify the listener as
observed by the caller's namespaces, not a live credential snapshot of a forked
PostgreSQL backend. Existing fresh process PID/start-tick/executable/resource
checks and live SQL identity guards remain necessary. Credential forwarding,
namespace mappings, socket passing and process lifecycle still need actual
rootless runtime qualification; no qualification claim follows from the match.

Local controls use real socketpairs to deny PID/UID/GID mismatch, TCP sockets,
Unix datagram sockets and regular files while retaining original descriptors and
queued protocol bytes. Actual disposable PostgreSQL SCRAM inspection and schema
apply/replay now compare the kernel peer to the scratch postmaster PID and host
UID/GID. A deliberately wrong approved PID denies a real schema connection before
its work; synthetic controls confirm both paths close before their SQL action.
Root records, startup/resource attestation, fixed path/UID and PGDATA comparisons
remain fixture-adapted. This is local transport evidence only; no production
socket, role, root record or host account is created.

The inert source set also includes publication.py, a root-only library publisher
with no operator CLI or installation. It preserves previous physical controls
and keeps admission blocked; separate actual publication/custody authority and
all host/runtime qualification remain required. See control-record-publication.md.
