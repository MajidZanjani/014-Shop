"""Policy-bound restricted application connection; inert, no live settings switch.

Policy must arrive from separately approved immutable custody/attestation. These
functions do not issue policy, discover endpoints, provision roles or grant use of
production. Only the dedicated database data socket belongs inside the app; host
process/control/management mounts remain forbidden. Namespace peer observations
must be independently qualified, never guessed from host PID/UID mappings.
"""
import contextlib
import hashlib
import hmac
import json
import os
import re
import socket
import struct
import psycopg
import django_transaction
from guard import require, validate_database_identity
from operator_inspect import read_private_fd

SOCKET_DIRECTORY = '/run/shop/postgres'
OPTIONS = '-c search_path=pg_catalog -c statement_timeout=2000 -c lock_timeout=1000'
CONNECTION_OPTIONS = {'connect_timeout':'2', 'client_encoding':'UTF8',
    'passfile':'/dev/null', 'require_auth':'scram-sha-256', 'sslmode':'disable',
    'gssencmode':'disable', 'options':OPTIONS}


def validate_policy(value):
    require(type(value) is dict and set(value) == {'schema_version','database',
        'observer_owner','socket_directory','peer','credential_sha256'})
    require(type(value['schema_version']) is int and value['schema_version'] == 1
            and value['socket_directory'] == SOCKET_DIRECTORY)
    validate_database_identity(value['database'], value['database'])
    require(value['database']['server_address'] == 'unix-socket')
    owner = value['observer_owner']
    require(type(owner) is str and re.fullmatch(r'[a-z_][a-z0-9_]{0,62}', owner)
            and owner != value['database']['role'])
    require(type(value['credential_sha256']) is str
            and re.fullmatch(r'[a-f0-9]{64}', value['credential_sha256']))
    peer = value['peer']
    require(type(peer) is dict and set(peer) == {'pid','uid','gid'}
            and all(type(n) is int for n in peer.values())
            and 0 <= peer['pid'] < 2**31
            and 0 < peer['uid'] < 2**32-1 and 0 < peer['gid'] < 2**32-1)
    return value


def policy_bytes(policy):
    validate_policy(policy)
    return json.dumps(policy, sort_keys=True, separators=(',',':')).encode('ascii')


def require_connection(raw, policy):
    """Validate effective libpq settings and the actual connected Unix peer.

    No password/DSN is read or reported. Peer PID zero is valid only when it is
    the explicitly approved observation for this client's PID namespace.
    """
    require(not raw.closed and raw.autocommit in (True, False))
    expected = policy['database']; info = raw.info
    require(info.host == policy['socket_directory'] and info.port == expected['server_port']
            and info.dbname == expected['database'] and info.user == expected['role'])
    parameters = info.get_parameters()
    require(all(parameters.get(key) == value for key,value in CONNECTION_OPTIONS.items()))
    with socket.fromfd(raw.fileno(), socket.AF_UNIX, socket.SOCK_STREAM) as peer:
        require(peer.getsockopt(socket.SOL_SOCKET, socket.SO_DOMAIN) == socket.AF_UNIX
                and peer.getsockopt(socket.SOL_SOCKET, socket.SO_TYPE) == socket.SOCK_STREAM)
        observed = struct.unpack('=iII', peer.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
        require(observed == tuple(policy['peer'][key] for key in ('pid','uid','gid')))


class _ApplicationConnection:
    def __init__(self, raw, encoded_policy, wrapper):
        self.connection = raw
        self._policy = encoded_policy
        self._wrapper = wrapper

    @contextlib.contextmanager
    def atomic(self, wrapper, runtime_probe):
        """Bind this exact authenticated connection, owner and transaction policy.

        Existing admission remains held through commit/rollback. Automatic
        all-write interception and isolated transport are separate integration.
        This context cannot make arbitrary caller-supplied policy authoritative.
        """
        policy = json.loads(self._policy)
        require(callable(runtime_probe) and wrapper is self._wrapper
                and wrapper.connection is self.connection)
        def fresh():
            require(wrapper.connection is self.connection)
            require_connection(self.connection, policy)
            return runtime_probe()
        with django_transaction.guarded_application_atomic(wrapper, policy['database'],
                fresh, observer_owner=policy['observer_owner']) as admitted:
            yield admitted


@contextlib.contextmanager
def open_application_connection(policy, credential_fd, *, wrapper):
    """Open one explicit SCRAM connection, close once; never reconnect or retry.

    All libpq environment names are refused without reading their values. The
    strong private credential FD must match its policy version before connecting.
    Credentials stay in memory only and never enter returned/public metadata.
    SQL/runtime identity is rechecked by atomic() before work and before commit.
    """
    encoded = policy_bytes(policy)
    policy = json.loads(encoded)
    require(not any(name.startswith('PG') for name in os.environ))
    from django.db import connections
    require(wrapper.vendor == 'postgresql' and connections[wrapper.alias] is wrapper
            and not wrapper.in_atomic_block)
    # Use only Django's driver adapters (including timezone loaders), never its
    # endpoint/auth settings. Every libpq connection option below is fixed here.
    adapters = wrapper.get_connection_params()['context']
    credential = read_private_fd(credential_fd, 4096, 32)
    require(b'\x00' not in credential
            and hmac.compare_digest(hashlib.sha256(credential).hexdigest(), policy['credential_sha256']))
    password = credential.decode('utf8'); del credential
    expected = policy['database']
    try:
        raw = psycopg.connect(host=policy['socket_directory'], port=expected['server_port'],
            dbname=expected['database'], user=expected['role'], password=password,
            autocommit=True, context=adapters, **CONNECTION_OPTIONS)
    finally:
        del password
    try:
        require_connection(raw, policy)
        yield _ApplicationConnection(raw, encoded, wrapper)
    finally:
        raw.close()
