"""Disposable SCRAM/restricted-role SQL; no real credentials or host targets."""
import copy
import hashlib
import importlib
import os
from pathlib import Path
import secrets
import socket
import struct
import tempfile
from unittest.mock import patch
import psycopg
from psycopg import sql
import test_application_observer as observers


class ApplicationConnectionTests(observers.ApplicationObserverTests):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.synthetic_password = secrets.token_hex(32)
        with psycopg.connect(host=str(cls.pg.socket), dbname='postgres', user='shop_test',
                             autocommit=True) as admin:
            admin.execute(sql.SQL('ALTER ROLE sll_app PASSWORD {}').format(
                sql.Literal(cls.synthetic_password)))
        (cls.pg.root/'data/pg_hba.conf').write_text(
            'local all sll_app scram-sha-256\nlocal all all trust\n')
        cls.pg.sql('SELECT pg_reload_conf()')
        from django.db import connections
        connections['guarded'].close()
        connections.databases['guarded']['PASSWORD'] = cls.synthetic_password
        connections.databases['guarded']['OPTIONS'] = {'require_auth':'scram-sha-256'}

    def producer(self):
        # Keep inherited observer tests aimed at their original producer.
        return importlib.import_module('application_observer')

    def module(self):
        return importlib.import_module('application_connection')

    def setUp(self):
        from django.db import connections
        connections['guarded'].close()
        super().setUp()
        self.addCleanup(self.wrapper.close)
        self.app = self.module()
        self.stack.enter_context(patch.object(self.app, 'SOCKET_DIRECTORY', str(self.pg.socket)))
        real_validate = self.app.validate_database_identity
        def validate(expected, observed):
            self.assertEqual(expected['pgdata'], str(self.pg.root/'data'))
            self.assertEqual(observed['pgdata'], expected['pgdata'])
            return real_validate(dict(expected, pgdata='/var/lib/shop/postgres'),
                                 dict(observed, pgdata='/var/lib/shop/postgres'))
        self.stack.enter_context(patch.object(self.app, 'validate_database_identity', side_effect=validate))
        with socket.fromfd(self.wrapper.connection.fileno(), socket.AF_UNIX, socket.SOCK_STREAM) as peer:
            pid, uid, gid = struct.unpack('=iII', peer.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
        self.policy = {'schema_version':1, 'database':copy.deepcopy(self.expected),
            'observer_owner':'shop_test', 'socket_directory':str(self.pg.socket),
            'peer':{'pid':pid, 'uid':uid, 'gid':gid},
            'credential_sha256':hashlib.sha256(self.synthetic_password.encode()).hexdigest()}
        self.credential = self.stack.enter_context(tempfile.TemporaryFile(dir=self.pg.root.parent))
        os.fchmod(self.credential.fileno(), 0o600)
        self.credential.write(self.synthetic_password.encode()); self.credential.flush()

    def opened(self, policy=None):
        return self.app.open_application_connection(
            self.policy if policy is None else policy, self.credential.fileno(), wrapper=self.wrapper)

    def attach(self, binding):
        self.wrapper.close()
        self.wrapper.connection = binding.connection
        self.wrapper.autocommit = True

    def test_bound_real_scram_connection_commits_restricted_django_writes(self):
        with self.opened() as binding:
            self.attach(binding)
            with binding.atomic(self.wrapper, lambda:dict(self.runtime)):
                self.insert(1); self.insert(2)
                self.assertEqual(self.count(), '0')
            self.assertEqual(self.count(), '2')
        self.assertTrue(binding.connection.closed)

    def test_policy_is_snapshotted_and_cannot_follow_caller_mutation(self):
        with self.opened() as binding:
            self.attach(binding)
            self.policy['database']['role'] = 'sll_other'
            self.policy['observer_owner'] = 'sll_other'
            with binding.atomic(self.wrapper, lambda:dict(self.runtime)): self.insert(1)
        self.assertEqual(self.count(), '1')

    def test_policy_wrong_owner_or_database_rolls_back_without_retry(self):
        for field, value in (('observer_owner','sll_other'), ('database','synthetic_decoy')):
            policy = copy.deepcopy(self.policy)
            if field == 'database': policy['database']['system_identifier'] = '9999999999999999999'
            else: policy[field] = value
            with self.opened(policy) as binding:
                self.attach(binding)
                with self.assertRaises(ValueError):
                    with binding.atomic(self.wrapper, lambda:dict(self.runtime)): self.insert(1)
            self.assertEqual(self.count(), '0')

    def test_credential_version_and_private_fd_validation_precede_connection(self):
        for change in ('digest', 'mode', 'pipe'):
            with self.subTest(change=change):
                policy = copy.deepcopy(self.policy); fd = self.credential.fileno()
                if change == 'digest': policy['credential_sha256'] = '0'*64
                elif change == 'mode': os.fchmod(fd, 0o644)
                else:
                    readfd, writefd = os.pipe(); self.addCleanup(os.close, readfd)
                    self.addCleanup(os.close, writefd); fd = readfd
                try:
                    with patch.object(psycopg, 'connect', side_effect=AssertionError('must deny before connect')):
                        with self.assertRaises(ValueError):
                            with self.app.open_application_connection(policy, fd, wrapper=self.wrapper): pass
                finally: os.fchmod(self.credential.fileno(), 0o600)

    def test_closed_policy_rejects_redirects_and_unknown_fields_before_connect(self):
        changes = ({'schema_version':True}, {'socket_directory':'/tmp'},
                   {'observer_owner':'sll_app'}, {'observer_owner':'invalid;sql'},
                   {'extra':'value'}, {'credential_sha256':'pending'},
                   {'peer':{'pid':-1,'uid':10001,'gid':10001}})
        for change in changes:
            with self.subTest(change=change), patch.object(psycopg, 'connect', side_effect=AssertionError('connect')):
                with self.assertRaises(ValueError):
                    with self.opened(dict(self.policy, **change)): pass

    def test_wrong_namespace_peer_is_denied_and_new_connection_is_closed(self):
        policy = copy.deepcopy(self.policy); policy['peer']['pid'] += 1
        actual_connect = psycopg.connect; opened=[]
        def connect(**kwargs):
            connection=actual_connect(**kwargs); opened.append(connection); return connection
        with patch.object(psycopg, 'connect', side_effect=connect):
            with self.assertRaises(ValueError):
                with self.opened(policy): self.fail('wrong peer accepted')
        self.assertEqual(len(opened), 1); self.assertTrue(opened[0].closed)

    def test_other_raw_connection_and_late_replacement_are_denied(self):
        for late in (False, True):
            with self.subTest(late=late), self.opened() as binding, self.opened() as other:
                if late: self.attach(binding)
                try:
                    with self.assertRaises((ValueError, psycopg.Error)):
                        with binding.atomic(self.wrapper, lambda:dict(self.runtime)):
                            self.insert(1)
                            self.wrapper.connection = other.connection
                finally:
                    if self.wrapper.connection is not binding.connection:
                        self.wrapper.connection = binding.connection
            self.assertEqual(self.count(), '0')

    def test_exception_closes_connection_without_serializing_private_input(self):
        with self.assertRaisesRegex(RuntimeError, 'synthetic failure'):
            with self.opened() as binding: raise RuntimeError('synthetic failure')
        self.assertTrue(binding.connection.closed)

    def test_ambient_libpq_redirect_is_denied_without_reading_its_value(self):
        with patch.dict(os.environ, {'PGSERVICE':'synthetic-redirect'}):
            with patch.object(psycopg, 'connect', side_effect=AssertionError('connect')):
                with self.assertRaises(ValueError):
                    with self.opened(): pass
        self.assertEqual(self.count(), '0')

    def test_only_django_adapters_are_used_from_wrapper_connection_parameters(self):
        adapters=self.wrapper.get_connection_params()['context']
        with patch.object(self.wrapper, 'get_connection_params', return_value={
                'context':adapters, 'host':'synthetic-decoy', 'user':'sll_other',
                'require_auth':'none'}):
            with self.opened() as binding:
                self.attach(binding)
                with binding.atomic(self.wrapper, lambda:dict(self.runtime)): self.insert(1)
        self.assertEqual(self.count(), '1')

    def test_incorrect_versioned_password_fails_once_without_retry(self):
        policy=copy.deepcopy(self.policy)
        incorrect=secrets.token_hex(32).encode()
        self.credential.seek(0); self.credential.truncate()
        self.credential.write(incorrect); self.credential.flush()
        policy['credential_sha256']=hashlib.sha256(incorrect).hexdigest()
        actual_connect=psycopg.connect; calls=[]
        def connect(**kwargs):
            calls.append(1); return actual_connect(**kwargs)
        with patch.object(psycopg, 'connect', side_effect=connect):
            with self.assertRaises(psycopg.OperationalError):
                with self.opened(policy): pass
        self.assertEqual(calls, [1]); self.assertEqual(self.count(), '0')

    def test_server_trust_authentication_cannot_satisfy_required_scram(self):
        hba=self.pg.root/'data/pg_hba.conf'; original=hba.read_bytes()
        hba.write_text('local all all trust\n'); self.pg.sql('SELECT pg_reload_conf()')
        try:
            with self.assertRaises(psycopg.OperationalError):
                with self.opened(): self.fail('trust accepted as SCRAM')
        finally:
            hba.write_bytes(original); self.pg.sql('SELECT pg_reload_conf()')
        self.assertEqual(self.count(), '0')
