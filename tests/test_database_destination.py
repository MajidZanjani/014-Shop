"""Actual PostgreSQL tests; container identity is explicitly synthetic here."""
from pathlib import Path
import sys
import unittest
import psycopg
from psycopg.pq import TransactionStatus
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'ops/runtime'))
import database


class DatabaseDestinationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import dev_postgres
        cls.stack = __import__('contextlib').ExitStack()
        try:
            cls.target = cls.stack.enter_context(dev_postgres.isolated_postgres())
            cls.decoy = cls.stack.enter_context(dev_postgres.isolated_postgres())
            cls.runtime = {'container_id': 'a'*64, 'account_uid': 9909}
            cls.expected = dict(cls.runtime,
                system_identifier=cls.target.sql('SELECT system_identifier FROM pg_control_system()'),
                pgdata='/var/lib/shop/postgres', database='postgres', role='shop_test',
                server_address='unix-socket', server_port=5432)
            # Production attestation requires the fixed in-container path. Local
            # scratch PGDATA intentionally differs, so adapt the comparison only
            # in this test fixture while retaining actual server reads and equality.
            cls.real_validate = staticmethod(database.validate_database_identity)
            cls.actual = dict(cls.expected, pgdata=str(cls.target.root/'data'))
            for pg in (cls.target, cls.decoy):
                pg.sql('CREATE TABLE public.destination_probe (value integer PRIMARY KEY)')
        except BaseException:
            cls.stack.close()
            raise

    @classmethod
    def tearDownClass(cls):
        cls.stack.close()

    def setUp(self):
        from unittest.mock import patch
        def local_validate(expected, observed):
            # Normalize only this fixture's explicit scratch path to the production
            # path AFTER confirming observed data_directory exactly matches it.
            self.assertEqual(expected['pgdata'], str(self.target.root/'data'))
            database.require(observed['pgdata'] == expected['pgdata'])
            return self.real_validate(dict(expected, pgdata='/var/lib/shop/postgres'),
                                      dict(observed, pgdata='/var/lib/shop/postgres'))
        self.validation = patch.object(database, 'validate_database_identity', side_effect=local_validate)
        self.validation.start()
        self.addCleanup(self.validation.stop)
        self.target.sql('DELETE FROM public.destination_probe')
        self.decoy.sql('DELETE FROM public.destination_probe')

    def connection(self, pg=None):
        pg = pg or self.target
        conn = psycopg.connect(host=str(pg.socket), port=5432, dbname='postgres', user='shop_test',
            password='', connect_timeout=2, autocommit=True, client_encoding='utf8',
            passfile=str(pg.root/'absent.pgpass'), options='-c search_path=pg_catalog')
        self.addCleanup(conn.close)
        return conn

    def execute(self, conn=None, expected=None, probe=None, sql=None):
        return database.execute_mutation(conn or self.connection(), expected or self.actual,
            probe or (lambda: dict(self.runtime)),
            sql or 'INSERT INTO public.destination_probe(value) VALUES (%s)', (7,))

    def test_matching_destination_commits_and_parameterizes(self):
        self.assertEqual(self.execute(), 1)
        self.assertEqual(self.target.sql('SELECT value FROM public.destination_probe'), '7')

    def test_real_decoy_cluster_receives_no_write(self):
        with self.assertRaises(ValueError):
            self.execute(conn=self.connection(self.decoy))
        self.assertEqual(self.decoy.sql('SELECT count(*) FROM public.destination_probe'), '0')
        self.assertEqual(self.target.sql('SELECT count(*) FROM public.destination_probe'), '0')

    def test_each_server_identity_field_denied(self):
        for key, value in [('system_identifier','9999999999999999999'), ('database','decoy'),
                           ('role','decoy'), ('server_address','127.0.0.1'), ('server_port',5433)]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.execute(expected=dict(self.actual, **{key:value}))
        self.assertEqual(self.target.sql('SELECT count(*) FROM public.destination_probe'), '0')

    def test_runtime_rechecked_and_change_rolls_back(self):
        calls = []
        def probe():
            calls.append(True)
            return dict(self.runtime, container_id=('a' if len(calls)==1 else 'b')*64)
        with self.assertRaises(ValueError): self.execute(probe=probe)
        self.assertEqual(len(calls), 2)
        self.assertEqual(self.target.sql('SELECT count(*) FROM public.destination_probe'), '0')

    def test_wrong_runtime_denied_before_write(self):
        for key,value in [('account_uid',9910), ('container_id','b'*64)]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.execute(probe=lambda:dict(self.runtime, **{key:value}))
        self.assertEqual(self.target.sql('SELECT count(*) FROM public.destination_probe'), '0')

    def test_probe_failure_rolls_back_without_retry(self):
        calls=[]
        def probe():
            calls.append(True)
            if len(calls)==2: raise OSError('synthetic missing storage')
            return dict(self.runtime)
        with self.assertRaises(OSError): self.execute(probe=probe)
        self.assertEqual(len(calls),2)
        self.assertEqual(self.target.sql('SELECT count(*) FROM public.destination_probe'), '0')

    def test_multiple_commands_and_transaction_control_rejected(self):
        for sql in ['COMMIT', 'BEGIN', 'SELECT 1', 'CREATE DATABASE decoy',
                    'INSERT INTO public.destination_probe VALUES (%s); COMMIT']:
            with self.subTest(sql=sql), self.assertRaises((ValueError, psycopg.Error)):
                self.execute(sql=sql)
        self.assertEqual(self.target.sql('SELECT count(*) FROM public.destination_probe'), '0')

    def test_active_transaction_rejected_without_committing_caller(self):
        conn=self.connection()
        with conn.transaction():
            conn.execute('INSERT INTO public.destination_probe VALUES (9)')
            with self.assertRaises(ValueError): self.execute(conn=conn)
            self.assertEqual(self.target.sql('SELECT count(*) FROM public.destination_probe'), '0')
        self.assertEqual(self.target.sql('SELECT value FROM public.destination_probe'), '9')

    def test_real_server_read_requires_metadata_privilege(self):
        self.target.sql('CREATE ROLE destination_unprivileged LOGIN')
        self.addCleanup(self.target.sql, 'DROP ROLE destination_unprivileged')
        conn=self.connection()
        conn.execute('SET SESSION AUTHORIZATION destination_unprivileged')
        expected=dict(self.actual, role='destination_unprivileged')
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            self.execute(conn=conn, expected=expected)
        self.assertEqual(conn.info.transaction_status, TransactionStatus.IDLE)
        self.assertEqual(self.target.sql('SELECT count(*) FROM public.destination_probe'), '0')

    def test_weakened_durability_denied(self):
        conn=self.connection()
        conn.execute("SET synchronous_commit = off")
        with self.assertRaises(ValueError): self.execute(conn=conn)
        self.assertEqual(self.target.sql('SELECT count(*) FROM public.destination_probe'), '0')

    def test_autocommit_disabled_denied(self):
        conn=self.connection()
        conn.autocommit=False
        with self.assertRaises(ValueError): self.execute(conn=conn)
        self.assertEqual(conn.info.transaction_status, TransactionStatus.IDLE)

    def test_constraint_error_does_not_retry_or_poison_connection(self):
        conn=self.connection()
        self.assertEqual(self.execute(conn=conn),1)
        calls=[]
        def probe():
            calls.append(True)
            return dict(self.runtime)
        with self.assertRaises(psycopg.errors.UniqueViolation):
            self.execute(conn=conn,probe=probe)
        self.assertEqual(calls,[True])
        self.assertEqual(conn.info.transaction_status,TransactionStatus.IDLE)
        self.assertEqual(self.target.sql('SELECT count(*) FROM public.destination_probe'),'1')

    def test_every_call_rechecks_identity(self):
        conn=self.connection()
        calls=[]
        def probe():
            calls.append(True)
            return dict(self.runtime)
        self.assertEqual(self.execute(conn=conn,probe=probe),1)
        with self.assertRaises(ValueError):
            self.execute(conn=conn,expected=dict(self.actual,role='decoy'),probe=probe,
                         sql='DELETE FROM public.destination_probe WHERE value=%s')
        self.assertEqual(len(calls),3)
        self.assertEqual(self.target.sql('SELECT value FROM public.destination_probe'),'7')


    def schema(self, statements, conn=None, probe=None):
        return database.execute_schema_batch(conn or self.connection(), self.actual,
                    probe or (lambda: dict(self.runtime)), statements)

    def schema_exists(self, pg=None):
        return (pg or self.target).sql(
            "SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
            "WHERE n.nspname='public' AND c.relname='schema_guard_probe'")

    def test_schema_batch_commits_exact_reviewed_steps(self):
        self.addCleanup(self.target.sql, 'DROP TABLE IF EXISTS public.schema_guard_probe')
        self.schema(('CREATE TABLE public.schema_guard_probe (id integer PRIMARY KEY)',
                     'ALTER TABLE public.schema_guard_probe ADD COLUMN value text',
                     'CREATE INDEX schema_guard_value ON public.schema_guard_probe(value)'))
        self.assertEqual(self.schema_exists(), '1')
        self.assertEqual(self.target.sql(
            "SELECT count(*) FROM information_schema.columns "
            "WHERE table_name='schema_guard_probe' AND column_name='value'"), '1')

    def test_schema_decoy_receives_no_ddl(self):
        with self.assertRaises(ValueError):
            self.schema(('CREATE TABLE public.schema_guard_probe(id integer)',),
                        conn=self.connection(self.decoy))
        self.assertEqual(self.schema_exists(self.decoy), '0')

    def test_schema_later_error_rolls_back_prior_ddl(self):
        conn=self.connection()
        with self.assertRaises(psycopg.errors.UndefinedColumn):
            self.schema(('CREATE TABLE public.schema_guard_probe(id integer)',
                         'CREATE INDEX schema_guard_bad ON public.schema_guard_probe(absent)'), conn=conn)
        self.assertEqual(self.schema_exists(), '0')
        self.assertEqual(conn.info.transaction_status, TransactionStatus.IDLE)

    def test_schema_identity_checked_before_each_statement_and_commit(self):
        for fail_at in (2,3,4):
            calls=[]
            def probe():
                calls.append(True)
                return dict(self.runtime, container_id=('b' if len(calls)==fail_at else 'a')*64)
            with self.subTest(fail_at=fail_at), self.assertRaises(ValueError):
                self.schema(('CREATE TABLE public.schema_guard_probe(id integer)',
                             'ALTER TABLE public.schema_guard_probe ADD COLUMN value text'),probe=probe)
            self.assertEqual(len(calls), fail_at)
            self.assertEqual(self.schema_exists(), '0')

    def test_schema_lock_contention_denies_without_retry(self):
        owner=self.connection()
        with owner.transaction():
            owner.execute('SELECT pg_advisory_xact_lock(%s)', (database.SCHEMA_LOCK,))
            with self.assertRaises(ValueError):
                self.schema(('CREATE TABLE public.schema_guard_probe(id integer)',))
            self.assertEqual(self.schema_exists(), '0')
        # Transaction lock is released; a subsequent separately requested call works.
        self.schema(('CREATE TABLE public.schema_guard_probe(id integer)',
                     'DROP TABLE public.schema_guard_probe'))
        self.assertEqual(self.schema_exists(), '0')

    def test_schema_rejects_unbounded_or_non_schema_commands(self):
        invalid=((), [], ('CREATE DATABASE decoy',), ('COMMIT',),
                 ('CREATE INDEX CONCURRENTLY decoy ON public.destination_probe(value)',),
                 ('GRANT ALL ON public.destination_probe TO public',),
                 ('INSERT INTO public.destination_probe VALUES (7)',),
                 ('CREATE TABLE public.schema_guard_probe(id integer); COMMIT',),
                 ('CREATE TABLE ' + 'x'*65536,),
                 ('CREATE TABLE ' + 'é'*32768,),
                 ('CREATE TABLE ' + 'x'*17000,)*64,
                 ('CREATE TABLE public.schema_guard_probe(id integer)',)*65)
        for statements in invalid:
            with self.subTest(case=str(statements)[:40]), self.assertRaises((ValueError,psycopg.Error)):
                self.schema(statements)
        self.assertEqual(self.schema_exists(), '0')

    def test_schema_probe_exception_rolls_back_and_is_not_retried(self):
        calls=[]
        def probe():
            calls.append(True)
            if len(calls)==3:raise OSError('synthetic missing storage')
            return dict(self.runtime)
        with self.assertRaises(OSError):
            self.schema(('CREATE TABLE public.schema_guard_probe(id integer)',), probe=probe)
        self.assertEqual(len(calls), 3)
        self.assertEqual(self.schema_exists(), '0')

    def test_schema_refuses_caller_owned_transaction(self):
        conn=self.connection()
        with conn.transaction():
            with self.assertRaises(ValueError):
                self.schema(('CREATE TABLE public.schema_guard_probe(id integer)',),conn=conn)
        self.assertEqual(self.schema_exists(), '0')
