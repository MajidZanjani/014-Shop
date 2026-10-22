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
