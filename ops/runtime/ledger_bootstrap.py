"""Explicit host-side ledger initialization; no CLI or automatic adoption/retry.

Only the exact separately reviewed SQL artifact pinned below is accepted. Record
publication, migration-role grants and actual runtime qualification are pending.
"""
import hashlib
from psycopg.pq import TransactionStatus
import database
from control import load_control
from guard import require
import process_probe
from schema_authorization import validate_authorization as validate_schema_authorization

ARTIFACT_SHA256 = '7b20aa11e7d220bebb9c0370905dfddef450798cf32933743ec18cd5ca3bff4c'
MIGRATION_ID = 'shop_ledger_bootstrap_v1'


def validate_authorization(value):
    validate_schema_authorization(value,action='initialize-new-schema-ledger')
    require(value['migration_id'] == MIGRATION_ID
            and value['artifact_sha256'] == ARTIFACT_SHA256)
    return value


def load_authorization():
    return load_control('ledger-bootstrap.json',validate_authorization)


def read_artifact(data, authorization):
    validate_authorization(authorization)
    require(type(data) is bytes and 0 < len(data) <= 32768)
    require(hashlib.sha256(data).hexdigest() == ARTIFACT_SHA256)
    # This is decoding a fixed pinned artifact, not a general SQL script parser.
    # Any artifact edit, even comments/whitespace, requires review and a new pin.
    sql='\n'.join(line for line in data.decode('ascii').splitlines()
                  if not line.startswith('--'))
    statements=tuple(part.strip() for part in sql.split(';') if part.strip())
    require(len(statements) == 4)
    return statements


def execute_authorized_bootstrap(connection, zfs, pg_control, data):
    """Create ledger plus bootstrap receipt atomically in a positively bound DB.

    Any existing shop_control namespace is a denial, including an empty one or a
    matching previously initialized ledger. Uncertain completion needs separate
    reconciliation; never repeat bootstrap blindly or remove an existing ledger.
    """
    authorization=load_authorization()
    statements=read_artifact(data,authorization)
    approved=process_probe.load_record()
    require(approved['database'] == authorization['database'])
    expected=dict(authorization['database'])
    require(connection.autocommit is True
            and connection.info.transaction_status == TransactionStatus.IDLE)
    def fresh(cursor, baseline=None):
        current_authorization=load_authorization()
        require(current_authorization == authorization)
        current=process_probe.load_record()
        require(current == approved)
        runtime=process_probe.probe(current,zfs,pg_control)
        require(baseline is None or runtime == baseline)
        database.validate_database_identity(expected,database.observe_database(cursor,runtime))
        return runtime
    with connection.transaction():
        with connection.cursor() as cursor:
            cursor.execute('SET LOCAL search_path = pg_catalog',prepare=True)
            cursor.execute("SET LOCAL statement_timeout = '2s'",prepare=True)
            cursor.execute("SET LOCAL lock_timeout = '1s'",prepare=True)
            baseline=fresh(cursor)
            cursor.execute('SELECT pg_catalog.pg_try_advisory_xact_lock(%s)',
                           (database.SCHEMA_LOCK,),prepare=True)
            require(cursor.fetchone() == (True,))
            cursor.execute("SELECT count(*) FROM pg_catalog.pg_namespace WHERE nspname='shop_control'",prepare=True)
            require(cursor.fetchone() == (0,))
            for statement in statements:
                fresh(cursor,baseline)
                cursor.execute(statement,prepare=True)
            database.validate_ledger(cursor)
            fresh(cursor,baseline)
            cursor.execute("""INSERT INTO shop_control.schema_migrations
                (migration_id,artifact_sha256,authorization_id,applied_at)
                VALUES (%s,%s,%s,pg_catalog.transaction_timestamp())""",
                (MIGRATION_ID,ARTIFACT_SHA256,authorization['authorization_id']),prepare=True)
            fresh(cursor,baseline)
    return 'initialized'
