# Django multi-statement transaction precursor

`ops/runtime/django_transaction.py` supplies library-only `guarded_atomic(wrapper,
expected, runtime_probe)` for an already-connected Django/Psycopg wrapper. It is
explicitly included in the inert database source artifact. It does not open a
connection, load credentials, discover a destination or enable production settings.
Production and bank-sandbox still select `shop.db.unqualified` and deny all
connection opens. No application/worker call site has been switched to a candidate
live backend. The existing single-statement mutation primitive cannot own the
multi-statement ORM transactions needed by worker claims; this context supplies
that missing transaction foundation.

The caller must separately bind expected identity and a fresh runtime probe to
approved immutable controls, qualify the existing connection's transport/roles,
and supply a trusted application operation. The guard is not a SQL sandbox or
automatic all-write enforcement. Raw SQL, other aliases, direct connection APIs,
external effects and code outside the context remain caller responsibilities.
No current role/auth/transport qualification is implied by this primitive.

The wrapper must be the registered Django connection for its alias, connected,
in autocommit and idle, with no outer atomic/manual transaction, rollback-only
state or queued commit callbacks. Admission is acquired before the owned durable
atomic block and retained through actual commit/rollback and autocommit
restoration. The guard sets transaction-local search_path to pg_catalog, public,
a two-second statement timeout and one-second lock timeout. These are bounded
candidate settings, not measured production tuning or schema-rights proof.

Before yielding, it checks fresh runtime and actual same-connection PostgreSQL
identity, role/session role, cluster/database/data directory/port, checksums,
fsync, synchronous_commit and primary status. Before commit it requires the exact
same raw connection, live transaction, unchanged runtime, valid admission and
matching SQL destination again. Rollback-only state and deferred commit callbacks
deny and roll back, preventing callbacks from performing unguarded work during
atomic exit. Nested Django savepoints may be used inside the owned transaction;
an existing outer transaction is denied. Trusted code must not bypass the wrapper
or alter transaction control directly.

Exceptions propagate without serialized SQL, values or credentials. There is no
reconnect, logging, repair, success artifact or automatic retry. A commit failure
is uncertain. A root/noncooperating authority change detected only after commit
cannot undo committed work; the cooperative admission lease excludes ordinary
publishers, not arbitrary root writers. Actual crash/runtime and recovery
qualification remain mandatory before any production use.

Local tests use actual Django QuerySet and cursor operations against an owned
PostgreSQL cluster, adapting only the scratch PGDATA comparison. Runtime account/
container evidence and the root physical admission path are synthetic/adapted,
with actual scratch flock behavior. Tests cover multi-statement commit/rollback,
late SQL durability/runtime/admission denial, missing-connection refusal without
reconnect, outer/manual transaction denial, deferred callbacks/rollback-only denial
and independent publisher exclusion during actual commit and rollback. They do
not qualify actual rootless transport, ORM interception, production credentials,
role privileges, all-write coverage or off-host recovery.


## Candidate restricted application observer

`guarded_application_atomic(wrapper, expected, runtime_probe, observer_owner=...)` now selects the fixed SQL observer in application_observer.py. The explicit owner is a separately approved immutable-policy input; this API does not create that authority or qualify the connection. Production and bank-sandbox remain on the denying backend, and no application/worker call site is changed.

The inert application-observer.sql returns only cluster ID and PGDATA via one zero-argument SECURITY DEFINER function. Exact catalog body/signature/owner/language/configuration/ACL and restricted caller policy are verified before invocation. No PUBLIC execution, implicit role grant, broad metadata-role membership, object adoption or fallback is accepted. Current/session role and durability are observed outside the definer as the actual caller. pg_catalog types are fully qualified and pg_temp is explicitly last; a demonstrated temporary-domain owner-privilege escalation is rejected by the final real PostgreSQL control.

The existing transaction/admission/connection/uncertain-commit rules above still apply. Privileged owners must cooperate with admission; client checks cannot prevent arbitrary noncooperating administrator changes. This remains local preparation for connection/transport/all-write/migration integration. [Exact204-test evidence and remaining scope](build/application-observer-2026-10-29.md).

## Policy-bound connection prerequisite

`application_connection.open_application_connection(policy, credential_fd, wrapper=...)` snapshots database/owner/namespace-peer/credential-version policy, opens one explicitly configured SCRAM Unix connection and uses only the registered Django wrapper's driver adapters. Its binding's `atomic(wrapper, runtime_probe)` selects the restricted observer from that snapshot and rechecks effective connection/peer policy at the existing transaction checkpoints. The private credential descriptor must match its version before connect; ambient libpq names and wrapper endpoint/auth overrides cannot redirect it. The context closes its single connection and never retries authentication or uncertain commits.

This library does not make a caller-supplied policy approved. Approved issuance/custody, isolated runtime-attestation lease transport, automatic application/worker write interception and migration/bootstrap/replica qualification remain required. Host-only process/control evidence must stay outside app containers. Production settings and runtime image payloads are unchanged. [Final236-test/source/deployment evidence and exact remaining scope](build/application-connection-2026-10-29.md).
