"""Host-side exact-byte schema admission; no CLI, record issuance or retries.

Schema and ledger commit atomically; restore reconciliation, role qualification
and deployment command integration remain pending. No automatic retry.
"""
from datetime import datetime, timezone
import hashlib
import json
import re
from control import load_control, unique_fields
from guard import require, validate_database_identity
from database import execute_schema_migration, validate_schema_statements
import process_probe


def validate_authorization(value, *, action='apply-reviewed-schema'):
    require(type(value) is dict and set(value) == {
        'schema_version', 'action', 'authorization_id', 'expires_at',
        'artifact_sha256', 'migration_id', 'database'})
    require(type(value['schema_version']) is int and value['schema_version'] == 1
            and value['action'] == action)
    for field, pattern in (('authorization_id', r'[a-f0-9]{32}'),
                           ('artifact_sha256', r'[a-f0-9]{64}'),
                           ('migration_id', r'[a-z][a-z0-9_-]{0,95}'),
                           ('expires_at', r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z')):
        require(type(value[field]) is str and re.fullmatch(pattern,value[field]))
    expiry = datetime.strptime(value['expires_at'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
    require(expiry > datetime.now(timezone.utc))
    validate_database_identity(value['database'],value['database'])
    return value


def load_authorization():
    return load_control('schema-authorization.json',validate_authorization)


def read_artifact(data, authorization, *, action='apply-reviewed-schema'):
    """Caller supplies bounded bytes; no pathname reopen or normalization."""
    validate_authorization(authorization,action=action)
    require(type(data) is bytes and 0 < len(data) <= 2097152)
    require(hashlib.sha256(data).hexdigest() == authorization['artifact_sha256'])
    artifact = json.loads(data.decode('utf8'), object_pairs_hook=unique_fields)
    require(type(artifact) is dict and set(artifact) == {'schema_version','migration_id','statements'})
    require(type(artifact['schema_version']) is int and artifact['schema_version'] == 1
            and artifact['migration_id'] == authorization['migration_id']
            and type(artifact['statements']) is list)
    statements = tuple(artifact['statements'])
    validate_schema_statements(statements)
    return statements


def execute_authorized_schema(connection, zfs, pg_control, data):
    """Library integration only; production readiness/restore reconciliation pending."""
    authorization = load_authorization()
    statements = read_artifact(data,authorization)
    approved = process_probe.load_record()
    require(approved['database'] == authorization['database'])
    def fresh():
        current_authorization = load_authorization()
        require(current_authorization == authorization)
        current = process_probe.load_record()
        require(current == approved)
        return process_probe.probe(current,zfs,pg_control)
    return execute_schema_migration(connection,authorization['database'],fresh,statements,
        {key:authorization[key] for key in ('migration_id','artifact_sha256','authorization_id')})
