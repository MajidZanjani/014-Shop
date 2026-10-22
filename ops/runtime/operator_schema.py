"""Prepared source-only exact-authority schema command; not installed/qualified.

Only apply-reviewed-schema and --help. No bootstrap, DSN/path, role provisioning,
retry or production application connection. Private artifact FD0/credential FD3.
"""
import json
import os
import sys
import operator_inspect as transport
import schema_authorization as schema
from guard import require

ERROR = b'{"event":"operator.schema_outcome_unconfirmed"}\n'
HELP = b'Prepared source-only command: apply-reviewed-schema (private artifact FD0, credential FD3). Runtime/role/publication qualification pending.\n'


def validate_report(value):
    require(type(value) is dict and set(value) == {
        'schema_version', 'status', 'retry_authorized', 'reopening_authorized'})
    require(type(value['schema_version']) is int and value['schema_version'] == 1
            and value['status'] in ('applied', 'already_applied')
            and value['retry_authorized'] is False and value['reopening_authorized'] is False)
    return value


def require_schema_role(connection):
    """Bounded role admission, not complete ACL or owner-history attestation."""
    row = connection.execute("""WITH RECURSIVE memberships(roleid) AS (
        SELECT roleid FROM pg_catalog.pg_auth_members
        WHERE member=(SELECT oid FROM pg_catalog.pg_roles WHERE rolname=current_user)
        UNION
        SELECT a.roleid FROM pg_catalog.pg_auth_members a
        JOIN memberships m ON a.member=m.roleid
    ) SELECT current_user=session_user AND me.rolcanlogin
        AND NOT (me.rolsuper OR me.rolcreatedb OR me.rolcreaterole
                 OR me.rolreplication OR me.rolbypassrls)
        AND NOT EXISTS (SELECT FROM pg_catalog.pg_database d
                        WHERE d.datname=current_database() AND d.datdba=me.oid)
        AND NOT EXISTS (SELECT FROM memberships m JOIN pg_catalog.pg_roles r ON r.oid=m.roleid
                        WHERE r.rolname<>'pg_read_all_settings')
        AND NOT EXISTS (SELECT FROM pg_catalog.pg_auth_members a WHERE a.admin_option
                        AND (a.member=me.oid OR a.member IN (SELECT roleid FROM memberships)))
        FROM pg_catalog.pg_roles me WHERE me.rolname=current_user""", prepare=True).fetchone()
    require(row == (True,))


def apply_from_fds():
    """Single-process source command only; never invoke inside an app server."""
    require(dict(os.environ) == transport.SAFE_ENV and os.geteuid() > 0)
    connection_record = transport.load_connection()
    expected = connection_record['database']
    require(os.geteuid() == expected['account_uid'])
    approved = transport.process_probe.load_record()
    authorization = schema.load_authorization()
    transport.validate_bindings(connection_record, approved, authorization)
    artifact = transport.read_private_fd(0, 2097152)
    schema.read_artifact(artifact, authorization)
    transport.process_probe.probe(approved, connection_record['zfs'], connection_record['pg_control'])
    socket_before = transport.socket_identity(expected['account_uid'], expected['server_port'])

    connection = None

    def admission():
        require(transport.load_connection() == connection_record
                and transport.process_probe.load_record() == approved
                and schema.load_authorization() == authorization
                and transport.socket_identity(expected['account_uid'], expected['server_port']) == socket_before)
        if connection is not None:
            transport.require_peer(connection, approved)
            require_schema_role(connection)
        return True

    admission()
    password = transport.read_private_fd(3, 4096, 16).decode('utf8')
    require('\x00' not in password)
    # This is the schema-role session only. Least-privilege role/HBA provisioning
    # and positive fixed socket/runtime qualification remain separate gates.
    connection = transport.psycopg.connect(host=transport.SOCKET_DIRECTORY, port=expected['server_port'],
        dbname=expected['database'], user=expected['role'], password=password,
        autocommit=True, connect_timeout=2, client_encoding='utf8', passfile='/dev/null',
        require_auth='scram-sha-256', sslmode='disable', gssencmode='disable',
        options='-c default_transaction_read_only=off -c search_path=pg_catalog -c statement_timeout=2000 -c lock_timeout=1000')
    del password
    try:
        admission()
        status = schema.execute_authorized_schema(connection, connection_record['zfs'],
            connection_record['pg_control'], artifact, admission_check=admission)
        # A failure after commit is deliberately unconfirmed, never a safe retry.
        admission()
        return validate_report({'schema_version': 1, 'status': status,
                                'retry_authorized': False, 'reopening_authorized': False})
    finally:
        connection.close()


def main(argv):
    if argv == ['--help']:
        os.write(1, HELP)
        return 0
    if argv != ['apply-reviewed-schema']:
        os.write(2, ERROR)
        return 2
    try:
        result = apply_from_fds()
        os.write(1, json.dumps(result, sort_keys=True, separators=(',', ':')).encode('ascii') + b'\n')
        return 0
    except BaseException:
        # Includes lost acknowledgement/post-commit admission failure. No detail,
        # SQL, artifact, credential, IDs or promise that no effects occurred.
        try:
            os.write(2, ERROR)
        except OSError:
            pass
        return 1


def entrypoint():
    os.environ.clear()
    os.environ.update(transport.SAFE_ENV)
    return main(sys.argv[1:])


if __name__ == '__main__':
    raise SystemExit(entrypoint())
