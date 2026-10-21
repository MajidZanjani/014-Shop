"""Guarded single-statement DML primitive; caller supplies reviewed runtime evidence.

This is not a SQL sandbox or a migration/bootstrap command. It does not connect,
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
