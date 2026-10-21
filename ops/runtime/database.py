"""Guarded DML and bounded transactional schema primitives.

Callers supply reviewed runtime evidence. This is not a SQL sandbox or a
complete migration/bootstrap command. It does not connect,
read credentials, discover containers, initialize storage or retry uncertain work.
"""
import re
from psycopg.pq import TransactionStatus
from guard import require, validate_database_identity

IDENTITY_SQL = """SELECT system_identifier::text, current_setting('data_directory'),
    current_database(), current_user, session_user,
    inet_server_addr()::text, inet_server_port(), current_setting('port')::integer,
    current_setting('fsync'), current_setting('synchronous_commit'),
    current_setting('data_checksums'), pg_is_in_recovery()
    FROM pg_catalog.pg_control_system()"""


def observe_database(cursor, runtime):
    cursor.execute(IDENTITY_SQL, prepare=True)
    row = cursor.fetchone()
    require(row is not None and len(row) == 12)
    system, data, database, role, session_role, address, port, configured_port, fsync, sync, checksums, recovery = row
    require(role == session_role and fsync == 'on' and sync == 'on'
            and checksums == 'on' and recovery is False)
    require(type(runtime) is dict and set(runtime) == {'container_id', 'account_uid'})
    return dict(runtime, system_identifier=system, pgdata=data, database=database,
                role=role, server_address=address if address is not None else 'unix-socket',
                server_port=port if port is not None else configured_port)


def execute_mutation(connection, expected, runtime_probe, statement, parameters=()):
    """Execute one reviewed INSERT/UPDATE/DELETE, returning affected row count.

    runtime_probe must freshly verify the exact container/account/storage/resource
    binding and return its container ID/account UID. No cached caller claim is a
    runtime attestation. Host-side probe integration remains a separate requirement.
    The caller retains the connection; this function owns the entire transaction.
    Denials/errors propagate without printing SQL, parameters or connection details.
    """
    validate_database_identity(expected, expected)
    expected = dict(expected)
    require(type(statement) is str and len(statement) <= 65536
            and re.match(r'\A(?:INSERT|UPDATE|DELETE)\s', statement, re.IGNORECASE))
    require(callable(runtime_probe) and connection.autocommit is True
            and connection.info.transaction_status == TransactionStatus.IDLE)
    # A prepared statement cannot contain a second command. Only DML is accepted,
    # so transaction control and nontransactional bootstrap/DDL are not exposed.
    with connection.transaction():
        with connection.cursor() as cursor:
            cursor.execute("SET LOCAL search_path = pg_catalog", prepare=True)
            cursor.execute("SET LOCAL statement_timeout = '2s'", prepare=True)
            cursor.execute("SET LOCAL lock_timeout = '1s'", prepare=True)
            before = runtime_probe()
            validate_database_identity(expected, observe_database(cursor, before))
            cursor.execute(statement, parameters, prepare=True)
            count = cursor.rowcount
            # Catch changed role/durability/runtime evidence before commit too.
            after = runtime_probe()
            require(after == before)
            validate_database_identity(expected, observe_database(cursor, after))
    return count


# A shop-specific cooperative lock: held for this transaction only, never waited
# on or retried. Every future schema command must use the same guarded path.
SCHEMA_LOCK = 0x53484F505343484D


def validate_schema_statements(statements):
    """Validate bounds/prefixes only; statements remain trusted reviewed SQL."""
    require(type(statements) is tuple and 1 <= len(statements) <= 64)
    for statement in statements:
        require(type(statement) is str and len(statement.encode('utf8')) <= 65536
                and re.match(r'\A(?:(?:CREATE|ALTER|DROP) (?:TABLE|SEQUENCE)|'
                             r'CREATE (?:UNIQUE )?INDEX|DROP INDEX)\s',
                             statement, re.IGNORECASE))
    require(sum(len(s.encode('utf8')) for s in statements) <= 1048576)


def execute_schema_batch(connection, expected, runtime_probe, statements):
    """Atomically apply bounded, trusted reviewed schema SQL to one destination.

    This is a precursor to a migration runner, not Django migration integration
    or a SQL sandbox. Callers must authorize exact artifact bytes and role rights
    separately. Only table/sequence/index schema prefixes are accepted. Embedded
    SQL expressions remain trusted code; they are not parsed or sandboxed.
    Transaction commands, role grants and migration ledger DML are rejected.
    Concurrent indexes cannot run inside the owned transaction.
    Never connect, initialize a cluster, print diagnostics or retry on failure.
    """
    validate_database_identity(expected, expected)
    expected = dict(expected)
    validate_schema_statements(statements)
    require(callable(runtime_probe) and connection.autocommit is True
            and connection.info.transaction_status == TransactionStatus.IDLE)
    with connection.transaction():
        with connection.cursor() as cursor:
            cursor.execute("SET LOCAL search_path = pg_catalog", prepare=True)
            cursor.execute("SET LOCAL statement_timeout = '2s'", prepare=True)
            cursor.execute("SET LOCAL lock_timeout = '1s'", prepare=True)
            baseline = runtime_probe()
            validate_database_identity(expected, observe_database(cursor, baseline))
            cursor.execute('SELECT pg_catalog.pg_try_advisory_xact_lock(%s)',
                           (SCHEMA_LOCK,), prepare=True)
            require(cursor.fetchone() == (True,))
            for statement in statements:
                current = runtime_probe()
                require(current == baseline)
                validate_database_identity(expected, observe_database(cursor, current))
                # Extended protocol rejects stacked commands, including COMMIT.
                cursor.execute(statement, prepare=True)
            current = runtime_probe()
            require(current == baseline)
            validate_database_identity(expected, observe_database(cursor, current))
