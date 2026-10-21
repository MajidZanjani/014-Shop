"""Separately authorized, read-only schema/bootstrap ledger observation.

No write retry, repair, restore approval, record refresh or deployment CLI.
"""
import hashlib
import database
from control import load_control
from guard import require
import ledger_bootstrap
import process_probe
import schema_authorization

ACTION = 'inspect-schema-outcome'


def validate_authorization(value):
    require(type(value) is dict and 'artifact_kind' in value
            and value['artifact_kind'] in ('schema','ledger-bootstrap'))
    original={key:item for key,item in value.items() if key != 'artifact_kind'}
    schema_authorization.validate_authorization(original,action=ACTION)
    if value['artifact_kind'] == 'ledger-bootstrap':
        require(value['migration_id'] == ledger_bootstrap.MIGRATION_ID
                and value['artifact_sha256'] == ledger_bootstrap.ARTIFACT_SHA256)
    else:
        require(value['migration_id'] != ledger_bootstrap.MIGRATION_ID)
    return value


def load_authorization():
    return load_control('schema-reconciliation.json',validate_authorization)


def inspect_authorized_schema(connection, zfs, pg_control, data):
    """Observe original exact bytes under new read-only authority and pinned DB.

    authorization_id identifies the original operation, not a new write approval.
    The inspection record must be unexpired even if the original write expired.
    """
    authorization=load_authorization()
    original={key:value for key,value in authorization.items() if key != 'artifact_kind'}
    if authorization['artifact_kind'] == 'schema':
        schema_authorization.read_artifact(data,original,action=ACTION)
    else:
        require(type(data) is bytes and 0 < len(data) <= 32768
                and hashlib.sha256(data).hexdigest() == ledger_bootstrap.ARTIFACT_SHA256)
    approved=process_probe.load_record()
    require(approved['database'] == authorization['database'])
    def fresh():
        current_authorization=load_authorization()
        require(current_authorization == authorization)
        current=process_probe.load_record()
        require(current == approved)
        return process_probe.probe(current,zfs,pg_control)
    return database.inspect_schema_migration(connection,authorization['database'],fresh,
        {key:authorization[key] for key in ('migration_id','artifact_sha256','authorization_id')})
