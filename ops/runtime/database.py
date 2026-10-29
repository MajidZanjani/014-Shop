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
    return identity_from_row(cursor.fetchone(), runtime)


def identity_from_row(row, runtime):
    """Decode the fixed observed row; callers still verify exact expected identity."""
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
    return _execute_schema_transaction(connection,expected,runtime_probe,statements)


def execute_schema_migration(connection, expected, runtime_probe, statements, migration):
    """Commit schema and its ledger row together; never auto-retry uncertain work.

    A new explicit call may observe already_applied for the exact same three IDs.
    Authorization validity and restore reconciliation remain caller requirements.
    The ledger must already exist under its reviewed migration owner.
    """
    validate_migration_identity(migration)
    return _execute_schema_transaction(connection,expected,runtime_probe,statements,dict(migration))


def validate_migration_identity(migration):
    require(type(migration) is dict and set(migration) == {
        'migration_id','artifact_sha256','authorization_id'})
    for key,pattern in (('migration_id',r'[a-z][a-z0-9_-]{0,95}'),
                        ('artifact_sha256',r'[a-f0-9]{64}'),
                        ('authorization_id',r'[a-f0-9]{32}')):
        require(type(migration[key]) is str and re.fullmatch(pattern,migration[key]))


def validate_ledger(cursor):
    """Reject absent/adopted views, changed columns, hooks, owners or write grants."""
    cursor.execute("""SELECT c.oid, c.relkind, c.relpersistence, c.relrowsecurity,
        c.relforcerowsecurity, c.relhasrules, c.relispartition, c.relhassubclass,
        c.relowner = (SELECT oid FROM pg_catalog.pg_roles WHERE rolname=current_user),
        n.nspowner = c.relowner,
        NOT EXISTS (SELECT FROM pg_catalog.pg_trigger WHERE tgrelid=c.oid),
        NOT EXISTS (SELECT FROM pg_catalog.pg_inherits WHERE inhrelid=c.oid),
        NOT EXISTS (SELECT FROM pg_catalog.aclexplode(COALESCE(c.relacl,
            pg_catalog.acldefault('r',c.relowner))) a WHERE a.grantee<>c.relowner
            AND a.privilege_type IN ('INSERT','UPDATE','DELETE','TRUNCATE','TRIGGER','REFERENCES')),
        NOT EXISTS (SELECT FROM pg_catalog.aclexplode(COALESCE(n.nspacl,
            pg_catalog.acldefault('n',n.nspowner))) a WHERE a.grantee<>n.nspowner
            AND a.privilege_type='CREATE')
        FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
        WHERE n.nspname='shop_control' AND c.relname='schema_migrations'""",prepare=True)
    relation=cursor.fetchone()
    require(relation is not None and relation[1:] == ('r','p',False,False,False,False,False,
                                  True,True,True,True,True,True))
    cursor.execute("""SELECT attnum,attname,pg_catalog.format_type(atttypid,atttypmod),
        attnotnull,atthasdef,attidentity,attgenerated FROM pg_catalog.pg_attribute
        WHERE attrelid='shop_control.schema_migrations'::pg_catalog.regclass
        AND attnum>0 ORDER BY attnum""",prepare=True)
    require(cursor.fetchall() == [
        (1,'migration_id','text',True,False,'',''),
        (2,'artifact_sha256','text',True,False,'',''),
        (3,'authorization_id','text',True,False,'',''),
        (4,'applied_at','timestamp with time zone',True,False,'','')])
    cursor.execute("""SELECT contype,conkey,convalidated,condeferrable,conenforced
        FROM pg_catalog.pg_constraint
        WHERE conrelid='shop_control.schema_migrations'::pg_catalog.regclass
        ORDER BY contype,conkey""",prepare=True)
    require(cursor.fetchall() == [('n',[1],True,False,True),('n',[2],True,False,True),
                                   ('n',[3],True,False,True),('n',[4],True,False,True),
                                   ('p',[1],True,False,True),('u',[3],True,False,True)])
    cursor.execute("""SELECT count(*),bool_and(indisunique AND indisvalid AND indisready
        AND indexprs IS NULL AND indpred IS NULL AND indexrelid IN
            (SELECT conindid FROM pg_catalog.pg_constraint WHERE
             conrelid='shop_control.schema_migrations'::pg_catalog.regclass))
        FROM pg_catalog.pg_index WHERE indrelid='shop_control.schema_migrations'::pg_catalog.regclass""",prepare=True)
    require(cursor.fetchone() == (2,True))
    return relation[0]


def _execute_schema_transaction(connection, expected, runtime_probe, statements, migration=None):
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
            applied = False
            if migration is not None:
                # Fixed qualified relation; never CREATE IF NOT EXISTS or discover.
                cursor.execute('LOCK TABLE shop_control.schema_migrations IN SHARE ROW EXCLUSIVE MODE',prepare=True)
                ledger_oid=validate_ledger(cursor)
                cursor.execute("""SELECT migration_id,artifact_sha256,authorization_id
                    FROM shop_control.schema_migrations
                    WHERE migration_id=%s OR authorization_id=%s""",
                    (migration['migration_id'],migration['authorization_id']),prepare=True)
                rows=cursor.fetchall()
                require(not rows or rows == [(migration['migration_id'],
                        migration['artifact_sha256'],migration['authorization_id'])])
                applied=bool(rows)
            if not applied:
                for statement in statements:
                    current = runtime_probe()
                    require(current == baseline)
                    validate_database_identity(expected, observe_database(cursor, current))
                    cursor.execute(statement, prepare=True)
                if migration is not None:
                    current=runtime_probe()
                    require(current == baseline)
                    validate_database_identity(expected,observe_database(cursor,current))
                    require(validate_ledger(cursor) == ledger_oid)
                    cursor.execute("""INSERT INTO shop_control.schema_migrations
                        (migration_id,artifact_sha256,authorization_id,applied_at)
                        VALUES (%s,%s,%s,pg_catalog.transaction_timestamp())""",
                        (migration['migration_id'],migration['artifact_sha256'],
                         migration['authorization_id']),prepare=True)
            current = runtime_probe()
            require(current == baseline)
            validate_database_identity(expected, observe_database(cursor, current))
    if migration is not None:
        return 'already_applied' if applied else 'applied'


def inspect_schema_migration(connection, expected, runtime_probe, migration):
    """Return a read-only snapshot observation, never permission to retry/reopen.

    A missing row can reflect a concurrent commit or a restored/stale database.
    Invalid/partial ledger shape, wrong identity or unavailable guard is a denial.
    No schema SQL, ledger writes, advisory locks, discovery or automatic retries.
    """
    validate_migration_identity(migration)
    migration=dict(migration)
    validate_database_identity(expected,expected)
    expected=dict(expected)
    require(callable(runtime_probe) and connection.autocommit is True
            and connection.info.transaction_status == TransactionStatus.IDLE)
    with connection.transaction():
        with connection.cursor() as cursor:
            cursor.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY',prepare=True)
            cursor.execute('SET LOCAL search_path = pg_catalog',prepare=True)
            cursor.execute("SET LOCAL statement_timeout = '2s'",prepare=True)
            cursor.execute("SET LOCAL lock_timeout = '1s'",prepare=True)
            baseline=runtime_probe()
            validate_database_identity(expected,observe_database(cursor,baseline))
            cursor.execute("SELECT count(*) FROM pg_catalog.pg_namespace WHERE nspname='shop_control'",prepare=True)
            if cursor.fetchone() == (0,):
                status='ledger_absent'
            else:
                validate_ledger(cursor)
                cursor.execute("""SELECT migration_id,artifact_sha256,authorization_id
                    FROM shop_control.schema_migrations
                    WHERE migration_id=%s OR authorization_id=%s""",
                    (migration['migration_id'],migration['authorization_id']),prepare=True)
                rows=cursor.fetchall()
                exact=(migration['migration_id'],migration['artifact_sha256'],migration['authorization_id'])
                status='not_recorded' if not rows else ('recorded' if rows == [exact] else 'conflict')
            current=runtime_probe()
            require(current == baseline)
            validate_database_identity(expected,observe_database(cursor,current))
    return {'schema_version':1,'status':status,'retry_authorized':False,'reopening_authorized':False}
