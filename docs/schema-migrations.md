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
ledger fails closed. Its separately destination-guarded bootstrap procedure,
owner/role publication and deployment authorization remain unfinished.

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
ledger bootstrap/role qualification and actual off-host runtime qualification are
still pending. Direct lower-level `execute_schema_batch` remains an internal
untracked schema primitive for separately authorized bootstrap/tests; deployment
migrations must use the authorized ledger path. No deployment CLI is supplied.
Do not remove the production Django connection gate before those boundaries are
covered.

Local tests use disposable PostgreSQL target/decoy clusters and synthetic records.
They adapt only the fixed PGDATA comparison to owned scratch paths. They do not
establish rootless process/storage/resource containment or production readiness.
