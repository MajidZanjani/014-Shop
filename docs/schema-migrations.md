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

Before this can become a migration runner, implement and qualify an atomic durable
migration ledger binding migration ID, artifact digest and authorization ID to the
schema commit. Handle already-applied/conflicting artifacts and uncertain commit
outcomes without blind retry, including restore reconciliation. This library does
not consume authorization and does not prevent replay by itself. Also pending:
Django migration generation/recorder integration, reviewed migration-role grants,
credentials/private connection transport, root-owned record publication, immutable
host-side packaging and actual off-host rootless/runtime qualification. Do not
remove the production Django connection gate until those boundaries are covered.

Local tests use disposable PostgreSQL target/decoy clusters and synthetic records.
They adapt only the fixed PGDATA comparison to owned scratch paths. They do not
establish rootless process/storage/resource containment or production readiness.
