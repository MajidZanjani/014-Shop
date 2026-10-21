# Schema migration boundary

Status: repository implementation in progress. Production and bank-sandbox Django
connections remain blocked by `shop.db.unqualified`. No deployment CLI, approved
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
migrations must use the authorized ledger path. No deployment CLI is supplied.
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
`shop-database-tools-source`. It contains exactly seven explicitly selected Python
modules plus the pinned SQL artifact and a closed SHA-256 manifest. Individual
source bytes are copied into separate store files; the bundle does not retain a
reference to the entire repository source. It contains no interpreter, dependency
environment, executable launcher, host account/configuration or authorization
record. No NixOS module installs it and no service uses it automatically.

The `database-tools` verification lane builds this source bundle, compares all
packaged bytes and its manifest with the selected sources, checks exported
metadata and exact direct store references, and imports the modules from the actual store path using isolated
Python and the existing hash-locked runtime dependencies. Import controls deny
database connections and control-record reads. This is actual source-bundle build
and local import evidence only; it does not build an OCI image or qualify a live
operator tool. A concrete launcher, minimum operator runtime/dependency review,
credential transport, host installation and operational qualification are still
pending. The source manifest is not a complete runtime SBOM or licence review.
