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
        for pg in (self.target,self.decoy):
            pg.sql('DROP SCHEMA IF EXISTS shop_control CASCADE')
            pg.sql((ROOT/'ops/postgresql/schema-ledger.sql').read_text())
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


    def schema_authority(self, data=None):
        import hashlib,json
        from datetime import datetime,timedelta,timezone
        data = data if data is not None else json.dumps({'schema_version':1,
            'migration_id':'synthetic_001',
            'statements':['CREATE TABLE public.schema_guard_probe(id integer)']}).encode()
        return data, {'schema_version':1,'action':'apply-reviewed-schema',
            'authorization_id':'a'*32,'artifact_sha256':hashlib.sha256(data).hexdigest(),
            'migration_id':'synthetic_001','database':dict(self.actual),
            'expires_at':(datetime.now(timezone.utc)+timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%SZ')}

    def authorized_schema(self, data=None, authorization=None, loader=None, record=None, admission_check=None):
        from unittest.mock import patch
        import schema_authorization as auth
        default_data, default_authority=self.schema_authority()
        data=default_data if data is None else data
        authorization=default_authority if authorization is None else authorization
        with patch.object(auth,'validate_database_identity',database.validate_database_identity), \
             patch.object(auth,'load_authorization',side_effect=loader or (lambda:auth.validate_authorization(authorization))), \
             patch.object(auth.process_probe,'load_record',return_value=record or {'database':dict(self.actual)}), \
             patch.object(auth.process_probe,'probe',return_value=dict(self.runtime)):
            return auth.execute_authorized_schema(self.connection(),'synthetic-zfs','synthetic-pg-control',data,admission_check=admission_check)

    def test_authorized_exact_schema_artifact_executes(self):
        self.addCleanup(self.target.sql,'DROP TABLE IF EXISTS public.schema_guard_probe')
        self.authorized_schema()
        self.assertEqual(self.schema_exists(),'1')

    def test_artifact_byte_change_denied_even_equivalent_json(self):
        data,authority=self.schema_authority()
        with self.assertRaises(ValueError):
            self.authorized_schema(data+b' ',authority)
        self.assertEqual(self.schema_exists(),'0')

    def test_schema_authorization_closed_fields_and_expiry(self):
        data,authority=self.schema_authority()
        for patch in ({'expires_at':'2000-01-01T00:00:00Z'}, {'schema_version':True},
                      {'action':'unreviewed'}, {'extra':True}, {'authorization_id':'invalid'},
                      {'migration_id':'different'}, {'artifact_sha256':'f'*64}):
            with self.subTest(patch=patch),self.assertRaises(ValueError):
                self.authorized_schema(data,dict(authority,**patch))
        self.assertEqual(self.schema_exists(),'0')

    def test_artifact_duplicate_fields_and_unreviewed_content_denied(self):
        cases=(b'{"schema_version":1,"schema_version":1,"migration_id":"synthetic_001","statements":[]}',
               b'{"schema_version":1,"migration_id":"synthetic_001","statements":[],"extra":true}',
               b'{"schema_version":1,"migration_id":"synthetic_001","statements":["COMMIT"]}',
               b'{}', b'\xff')
        for data in cases:
            _,authority=self.schema_authority(data)
            with self.subTest(data=data[:30]),self.assertRaises(ValueError):
                self.authorized_schema(data,authority)
        self.assertEqual(self.schema_exists(),'0')

    def test_authorization_target_must_equal_pinned_process_record(self):
        with self.assertRaises(ValueError):
            self.authorized_schema(record={'database':dict(self.actual,role='decoy')})
        self.assertEqual(self.schema_exists(),'0')

    def test_authorization_revocation_or_change_rolls_back_ddl(self):
        import schema_authorization as auth
        from unittest.mock import patch
        data,authority=self.schema_authority()
        for change in ('removed','changed','expired'):
            calls=[]
            def loader():
                calls.append(True)
                if len(calls)==4: # initial, baseline, before DDL, before commit
                    if change=='removed':raise FileNotFoundError('synthetic revocation')
                    if change=='changed':return dict(authority,authorization_id='b'*32)
                    return auth.validate_authorization(dict(authority,expires_at='2000-01-01T00:00:00Z'))
                return authority
            with self.subTest(change=change),self.assertRaises((ValueError,FileNotFoundError)):
                self.authorized_schema(data,authority,loader=loader)
            self.assertEqual(len(calls),4)
            self.assertEqual(self.schema_exists(),'0')


    def test_authorized_artifact_has_explicit_byte_bound(self):
        for data in (b'', b' '*2097153):
            _,authority=self.schema_authority(data)
            with self.subTest(size=len(data)),self.assertRaises(ValueError):
                self.authorized_schema(data,authority)
        self.assertEqual(self.schema_exists(),'0')

    def test_authorized_schema_process_record_change_rolls_back(self):
        from unittest.mock import patch
        import schema_authorization as auth
        data,authority=self.schema_authority()
        original={'database':dict(self.actual),'synthetic_process':'original'}
        changed={**original,'synthetic_process':'changed'}
        with patch.object(auth,'validate_database_identity',database.validate_database_identity), \
             patch.object(auth,'load_authorization',return_value=authority), \
             patch.object(auth.process_probe,'load_record',side_effect=[original,original,original,changed]), \
             patch.object(auth.process_probe,'probe',return_value=dict(self.runtime)) as observed:
            with self.assertRaises(ValueError):
                auth.execute_authorized_schema(self.connection(),'synthetic-zfs','synthetic-pg-control',data)
            self.assertEqual(observed.call_count,2)
        self.assertEqual(self.schema_exists(),'0')


    def ledger_count(self):
        return self.target.sql('SELECT count(*) FROM shop_control.schema_migrations')

    def test_migration_ledger_commits_and_repeated_call_skips_ddl(self):
        self.addCleanup(self.target.sql,'DROP TABLE IF EXISTS public.schema_guard_probe')
        self.assertEqual(self.authorized_schema(),'applied')
        self.assertEqual(self.ledger_count(),'1')
        # New explicit connection/request after a synthetically lost caller result.
        # A repeated CREATE TABLE would fail if the ledger did not skip the DDL.
        self.assertEqual(self.authorized_schema(),'already_applied')
        self.assertEqual(self.ledger_count(),'1')
        self.assertEqual(self.target.sql(
            "SELECT migration_id||'|'||authorization_id FROM shop_control.schema_migrations"),
            'synthetic_001|'+'a'*32)

    def test_migration_ledger_conflicting_digest_or_authorization_denied(self):
        import hashlib
        self.addCleanup(self.target.sql,'DROP TABLE IF EXISTS public.schema_guard_probe')
        data,authority=self.schema_authority()
        self.assertEqual(self.authorized_schema(data,authority),'applied')
        changed=data+b' '
        cases=((changed,dict(authority,artifact_sha256=hashlib.sha256(changed).hexdigest())),
               (data,dict(authority,authorization_id='b'*32)))
        for artifact,approval in cases:
            with self.subTest(approval=approval['authorization_id']),self.assertRaises(ValueError):
                self.authorized_schema(artifact,approval)
        self.assertEqual(self.ledger_count(),'1')

    def test_migration_ledger_authorization_cannot_apply_another_migration(self):
        import json
        self.addCleanup(self.target.sql,'DROP TABLE IF EXISTS public.schema_guard_probe')
        self.assertEqual(self.authorized_schema(),'applied')
        data=json.dumps({'schema_version':1,'migration_id':'synthetic_002',
             'statements':['ALTER TABLE public.schema_guard_probe ADD COLUMN unexpected integer']}).encode()
        _,authority=self.schema_authority(data)
        authority['migration_id']='synthetic_002'
        with self.assertRaises(ValueError):self.authorized_schema(data,authority)
        self.assertEqual(self.ledger_count(),'1')
        self.assertEqual(self.target.sql("SELECT count(*) FROM information_schema.columns "
            "WHERE table_name='schema_guard_probe' AND column_name='unexpected'"),'0')

    def test_migration_ledger_and_schema_roll_back_after_later_ddl_failure(self):
        import json
        data=json.dumps({'schema_version':1,'migration_id':'synthetic_001','statements':[
             'CREATE TABLE public.schema_guard_probe(id integer)',
             'ALTER TABLE public.absent_ledger_test ADD COLUMN value integer']}).encode()
        _,authority=self.schema_authority(data)
        with self.assertRaises(psycopg.errors.UndefinedTable):self.authorized_schema(data,authority)
        self.assertEqual(self.schema_exists(),'0')
        self.assertEqual(self.ledger_count(),'0')

    def test_migration_precommit_denial_rolls_back_ledger_insert(self):
        data,authority=self.schema_authority();calls=[]
        def loader():
            calls.append(True)
            if len(calls)==5:raise FileNotFoundError('synthetic final revocation')
            return authority
        with self.assertRaises(FileNotFoundError):self.authorized_schema(data,authority,loader=loader)
        self.assertEqual(len(calls),5)
        self.assertEqual(self.schema_exists(),'0')
        self.assertEqual(self.ledger_count(),'0')

    def test_migration_requires_preexisting_ledger_without_adoption(self):
        self.target.sql('DROP SCHEMA shop_control CASCADE')
        with self.assertRaises(psycopg.errors.InvalidSchemaName):self.authorized_schema()
        self.assertEqual(self.schema_exists(),'0')
        self.assertEqual(self.target.sql("SELECT count(*) FROM pg_namespace WHERE nspname='shop_control'"),'0')

    def test_migration_rejects_changed_ledger_shape_hooks_grants_and_indexes(self):
        changes=(
            'ALTER TABLE shop_control.schema_migrations ADD COLUMN unexpected integer',
            "ALTER TABLE shop_control.schema_migrations ALTER COLUMN applied_at SET DEFAULT now()",
            'ALTER TABLE shop_control.schema_migrations ENABLE ROW LEVEL SECURITY',
            'ALTER TABLE shop_control.schema_migrations DROP CONSTRAINT schema_migrations_authorization_id_key',
            'GRANT INSERT ON shop_control.schema_migrations TO PUBLIC',
            'GRANT CREATE ON SCHEMA shop_control TO PUBLIC',
            'CREATE INDEX unexpected_ledger_idx ON shop_control.schema_migrations(applied_at)',
            'CREATE TRIGGER unexpected_ledger_trigger BEFORE UPDATE ON shop_control.schema_migrations '
            'FOR EACH ROW EXECUTE FUNCTION pg_catalog.suppress_redundant_updates_trigger()')
        for change in changes:
            self.target.sql('DROP SCHEMA shop_control CASCADE')
            self.target.sql((ROOT/'ops/postgresql/schema-ledger.sql').read_text())
            self.target.sql(change)
            with self.subTest(change=change),self.assertRaises(ValueError):self.authorized_schema()
            self.assertEqual(self.schema_exists(),'0')
            self.assertEqual(self.ledger_count(),'0')

    def test_migration_rejects_ledger_alteration_in_reviewed_batch(self):
        import json
        data=json.dumps({'schema_version':1,'migration_id':'synthetic_001','statements':[
             'CREATE TABLE public.schema_guard_probe(id integer)',
             'ALTER TABLE shop_control.schema_migrations ADD COLUMN unexpected integer']}).encode()
        _,authority=self.schema_authority(data)
        with self.assertRaises(ValueError):self.authorized_schema(data,authority)
        self.assertEqual(self.schema_exists(),'0')
        self.assertEqual(self.ledger_count(),'0')
        self.assertEqual(self.target.sql("SELECT count(*) FROM information_schema.columns "
            "WHERE table_schema='shop_control' AND column_name='unexpected'"),'0')


    def test_migration_rejects_replacement_ledger_even_with_same_shape(self):
        import json
        original_oid=self.target.sql("SELECT 'shop_control.schema_migrations'::regclass::oid")
        bootstrap=(ROOT/'ops/postgresql/schema-ledger.sql').read_text()
        create='CREATE TABLE'+bootstrap.split('CREATE TABLE',1)[1].split(';',1)[0]
        data=json.dumps({'schema_version':1,'migration_id':'synthetic_001','statements':[
            'CREATE TABLE public.schema_guard_probe(id integer)',
            'DROP TABLE shop_control.schema_migrations',create]}).encode()
        _,authority=self.schema_authority(data)
        with self.assertRaises(ValueError):self.authorized_schema(data,authority)
        self.assertEqual(self.schema_exists(),'0')
        self.assertEqual(self.ledger_count(),'0')
        self.assertEqual(self.target.sql("SELECT 'shop_control.schema_migrations'::regclass::oid"),original_oid)


    def bootstrap_authority(self):
        import ledger_bootstrap as bootstrap
        data=(ROOT/'ops/postgresql/schema-ledger.sql').read_bytes()
        _,authority=self.schema_authority(data)
        authority.update(action='initialize-new-schema-ledger',authorization_id='c'*32,
                         migration_id=bootstrap.MIGRATION_ID)
        return data,authority

    def authorized_bootstrap(self, data=None, authority=None, loader=None, conn=None):
        from unittest.mock import patch
        import ledger_bootstrap as bootstrap
        import schema_authorization as auth
        default_data,default_authority=self.bootstrap_authority()
        data=default_data if data is None else data
        authority=default_authority if authority is None else authority
        with patch.object(auth,'validate_database_identity',database.validate_database_identity), \
             patch.object(bootstrap,'load_authorization',side_effect=loader or (lambda:bootstrap.validate_authorization(authority))), \
             patch.object(bootstrap.process_probe,'load_record',return_value={'database':dict(self.actual)}), \
             patch.object(bootstrap.process_probe,'probe',return_value=dict(self.runtime)):
            return bootstrap.execute_authorized_bootstrap(conn or self.connection(),
                        'synthetic-zfs','synthetic-pg-control',data)

    def namespace_count(self):
        return self.target.sql("SELECT count(*) FROM pg_namespace WHERE nspname='shop_control'")

    def test_guarded_ledger_bootstrap_commits_receipt_and_allows_migration(self):
        import ledger_bootstrap as bootstrap
        self.target.sql('DROP SCHEMA shop_control CASCADE')
        self.assertEqual(self.authorized_bootstrap(),'initialized')
        self.assertEqual(self.ledger_count(),'1')
        self.assertEqual(self.target.sql("SELECT migration_id||'|'||artifact_sha256||'|'||authorization_id "
            "FROM shop_control.schema_migrations"),bootstrap.MIGRATION_ID+'|'+bootstrap.ARTIFACT_SHA256+'|'+'c'*32)
        self.addCleanup(self.target.sql,'DROP TABLE IF EXISTS public.schema_guard_probe')
        self.assertEqual(self.authorized_schema(),'applied')
        self.assertEqual(self.ledger_count(),'2')

    def test_bootstrap_rejects_preexisting_matching_ledger_or_empty_namespace(self):
        with self.assertRaises(ValueError):self.authorized_bootstrap()
        self.assertEqual(self.ledger_count(),'0')
        self.target.sql('DROP TABLE shop_control.schema_migrations')
        with self.assertRaises(ValueError):self.authorized_bootstrap()
        self.assertEqual(self.namespace_count(),'1')
        self.assertEqual(self.target.sql("SELECT count(*) FROM pg_class c JOIN pg_namespace n "
            "ON n.oid=c.relnamespace WHERE n.nspname='shop_control'"),'0')

    def test_bootstrap_never_repeats_after_committed_initialization(self):
        self.target.sql('DROP SCHEMA shop_control CASCADE')
        self.assertEqual(self.authorized_bootstrap(),'initialized')
        with self.assertRaises(ValueError):self.authorized_bootstrap()
        self.assertEqual(self.ledger_count(),'1')

    def test_bootstrap_rejects_modified_artifact_even_if_record_approves_hash(self):
        import hashlib
        data,authority=self.bootstrap_authority()
        self.target.sql('DROP SCHEMA shop_control CASCADE')
        for changed in (data+b' ',data.replace(b'PRIMARY KEY',b'')):
            for approval in (authority,dict(authority,artifact_sha256=hashlib.sha256(changed).hexdigest())):
                with self.assertRaises(ValueError):self.authorized_bootstrap(changed,approval)
        self.assertEqual(self.namespace_count(),'0')

    def test_bootstrap_requires_dedicated_action_id_and_unexpired_authority(self):
        data,authority=self.bootstrap_authority()
        self.target.sql('DROP SCHEMA shop_control CASCADE')
        for changed in ({'action':'apply-reviewed-schema'},{'migration_id':'synthetic_001'},
                        {'expires_at':'2000-01-01T00:00:00Z'},{'extra':True}):
            with self.subTest(changed=changed),self.assertRaises(ValueError):
                self.authorized_bootstrap(data,dict(authority,**changed))
        self.assertEqual(self.namespace_count(),'0')

    def test_bootstrap_revocation_midway_and_after_receipt_rolls_back_namespace(self):
        data,authority=self.bootstrap_authority()
        self.target.sql('DROP SCHEMA shop_control CASCADE')
        for fail_at in (4,8): # before revoke, or final check after receipt insert
            calls=[]
            def loader():
                calls.append(True)
                if len(calls)==fail_at:raise FileNotFoundError('synthetic revocation')
                return authority
            with self.subTest(fail_at=fail_at),self.assertRaises(FileNotFoundError):
                self.authorized_bootstrap(data,authority,loader=loader)
            self.assertEqual(len(calls),fail_at)
            self.assertEqual(self.namespace_count(),'0')

    def test_bootstrap_decoy_receives_no_mutation(self):
        self.target.sql('DROP SCHEMA shop_control CASCADE')
        with self.assertRaises(ValueError):self.authorized_bootstrap(conn=self.connection(self.decoy))
        self.assertEqual(self.namespace_count(),'0')
        self.assertEqual(self.decoy.sql('SELECT count(*) FROM shop_control.schema_migrations'),'0')

    def test_bootstrap_obeys_schema_lock_and_caller_transaction_boundary(self):
        self.target.sql('DROP SCHEMA shop_control CASCADE')
        owner=self.connection()
        with owner.transaction():
            owner.execute('SELECT pg_advisory_xact_lock(%s)',(database.SCHEMA_LOCK,))
            with self.assertRaises(ValueError):self.authorized_bootstrap()
            with self.assertRaises(ValueError):self.authorized_bootstrap(conn=owner)
        self.assertEqual(self.namespace_count(),'0')


    def test_bootstrap_inherited_named_role_write_grant_denied_and_rolled_back(self):
        self.target.sql('DROP SCHEMA shop_control CASCADE')
        self.target.sql('CREATE ROLE ledger_unexpected_writer NOLOGIN')
        self.addCleanup(self.target.sql,'DROP ROLE ledger_unexpected_writer')
        self.target.sql('ALTER DEFAULT PRIVILEGES GRANT INSERT ON TABLES TO ledger_unexpected_writer')
        self.addCleanup(self.target.sql,'ALTER DEFAULT PRIVILEGES REVOKE INSERT ON TABLES FROM ledger_unexpected_writer')
        with self.assertRaises(ValueError):self.authorized_bootstrap()
        self.assertEqual(self.namespace_count(),'0')


    def test_bootstrap_explicit_public_revoke_removes_default_write_grant(self):
        self.target.sql('DROP SCHEMA shop_control CASCADE')
        self.target.sql('ALTER DEFAULT PRIVILEGES GRANT INSERT ON TABLES TO PUBLIC')
        self.addCleanup(self.target.sql,'ALTER DEFAULT PRIVILEGES REVOKE INSERT ON TABLES FROM PUBLIC')
        self.assertEqual(self.authorized_bootstrap(),'initialized')
        self.assertEqual(self.target.sql("SELECT count(*) FROM pg_class c, "
            "LATERAL aclexplode(c.relacl) a WHERE c.oid='shop_control.schema_migrations'::regclass "
            "AND a.grantee=0"),'0')


    def inspection_authority(self, data=None, authority=None, kind='schema'):
        if authority is None:
            data,authority=self.schema_authority(data)
        return data,dict(authority,action='inspect-schema-outcome',artifact_kind=kind)

    def authorized_inspection(self, data=None, authority=None, loader=None, conn=None):
        from unittest.mock import patch
        import schema_authorization as auth
        import schema_reconciliation as inspection
        default_data,default_authority=self.inspection_authority()
        data=default_data if data is None else data
        authority=default_authority if authority is None else authority
        with patch.object(auth,'validate_database_identity',database.validate_database_identity), \
             patch.object(inspection,'load_authorization',side_effect=loader or (lambda:inspection.validate_authorization(authority))), \
             patch.object(inspection.process_probe,'load_record',return_value={'database':dict(self.actual)}), \
             patch.object(inspection.process_probe,'probe',return_value=dict(self.runtime)):
            result=inspection.inspect_authorized_schema(conn or self.connection(),
                    'synthetic-zfs','synthetic-pg-control',data)
        self.assertEqual(set(result),{'schema_version','status','retry_authorized','reopening_authorized'})
        self.assertEqual(result['schema_version'],1)
        self.assertIs(result['retry_authorized'],False)
        self.assertIs(result['reopening_authorized'],False)
        return result['status']

    def test_readonly_inspection_not_recorded_does_not_apply_schema(self):
        self.assertEqual(self.authorized_inspection(),'not_recorded')
        self.assertEqual(self.schema_exists(),'0')
        self.assertEqual(self.ledger_count(),'0')

    def test_readonly_inspection_observes_recorded_without_write_authorization(self):
        from unittest.mock import patch
        import schema_authorization as auth
        self.addCleanup(self.target.sql,'DROP TABLE IF EXISTS public.schema_guard_probe')
        self.assertEqual(self.authorized_schema(),'applied')
        # Original write authority can be removed/expired; this separate observation
        # uses a newly valid inspection record referring to the original three IDs.
        with patch.object(auth,'load_authorization',side_effect=FileNotFoundError('synthetic expired write record')):
            self.assertEqual(self.authorized_inspection(),'recorded')
        self.assertEqual(self.ledger_count(),'1')

    def test_readonly_inspection_reports_conflicts_without_changing_history(self):
        import hashlib,json
        self.addCleanup(self.target.sql,'DROP TABLE IF EXISTS public.schema_guard_probe')
        self.authorized_schema()
        data,authority=self.inspection_authority()
        cases=((data,dict(authority,authorization_id='b'*32)),
               (data+b' ',dict(authority,artifact_sha256=hashlib.sha256(data+b' ').hexdigest())))
        for artifact,approval in cases:
            self.assertEqual(self.authorized_inspection(artifact,approval),'conflict')
        original=json.loads(data);original['migration_id']='synthetic_002'
        artifact=json.dumps(original).encode()
        approval=dict(authority,migration_id='synthetic_002',artifact_sha256=hashlib.sha256(artifact).hexdigest())
        self.assertEqual(self.authorized_inspection(artifact,approval),'conflict')
        self.assertEqual(self.ledger_count(),'1')

    def test_readonly_inspection_absent_ledger_never_bootstraps(self):
        self.target.sql('DROP SCHEMA shop_control CASCADE')
        self.assertEqual(self.authorized_inspection(),'ledger_absent')
        self.assertEqual(self.namespace_count(),'0')

    def test_readonly_inspection_partial_or_invalid_ledger_is_denial(self):
        self.target.sql('ALTER TABLE shop_control.schema_migrations ADD COLUMN unexpected integer')
        with self.assertRaises(ValueError):self.authorized_inspection()
        self.target.sql('DROP TABLE shop_control.schema_migrations')
        with self.assertRaises(ValueError):self.authorized_inspection()
        self.assertEqual(self.namespace_count(),'1')

    def test_readonly_inspection_observes_bootstrap_receipt(self):
        data,authority=self.bootstrap_authority()
        data,approval=self.inspection_authority(data,authority,kind='ledger-bootstrap')
        self.assertEqual(self.authorized_inspection(data,approval),'not_recorded')
        self.target.sql('DROP SCHEMA shop_control CASCADE')
        self.assertEqual(self.authorized_bootstrap(),'initialized')
        self.assertEqual(self.authorized_inspection(data,approval),'recorded')
        self.assertEqual(self.ledger_count(),'1')
        with self.assertRaises(ValueError):self.authorized_inspection(data+b' ',approval)

    def test_readonly_inspection_needs_its_own_valid_action_kind_and_expiry(self):
        data,authority=self.inspection_authority()
        for patch in ({'action':'apply-reviewed-schema'},{'action':'initialize-new-schema-ledger'},
                      {'artifact_kind':'unknown'},{'artifact_kind':'ledger-bootstrap'},
                      {'expires_at':'2000-01-01T00:00:00Z'},{'extra':True}):
            with self.subTest(patch=patch),self.assertRaises(ValueError):
                self.authorized_inspection(data,dict(authority,**patch))
        self.assertEqual(self.ledger_count(),'0')

    def test_readonly_inspection_revocation_before_return_denies_report(self):
        data,authority=self.inspection_authority();calls=[]
        def loader():
            calls.append(True)
            if len(calls)==3:raise FileNotFoundError('synthetic inspection revocation')
            return authority
        with self.assertRaises(FileNotFoundError):self.authorized_inspection(data,authority,loader=loader)
        self.assertEqual(len(calls),3)
        self.assertEqual(self.ledger_count(),'0')

    def test_readonly_inspection_rejects_decoy(self):
        with self.assertRaises(ValueError):self.authorized_inspection(conn=self.connection(self.decoy))
        self.assertEqual(self.decoy.sql('SELECT count(*) FROM shop_control.schema_migrations'),'0')

    def test_inspection_uses_actual_readonly_repeatable_transaction(self):
        conn=self.connection();observed=[]
        _,authority=self.schema_authority()
        migration={key:authority[key] for key in ('migration_id','artifact_sha256','authorization_id')}
        def probe():
            observed.append(conn.execute("SELECT current_setting('transaction_read_only'), "
                                         "current_setting('transaction_isolation')").fetchone())
            return dict(self.runtime)
        result=database.inspect_schema_migration(conn,self.actual,probe,migration)
        self.assertEqual(result['status'],'not_recorded')
        self.assertEqual(observed,[('on','repeatable read')]*2)
        self.assertEqual(conn.info.transaction_status,TransactionStatus.IDLE)
        self.assertEqual(conn.execute('SHOW transaction_read_only').fetchone(),('off',))
        def attempted_write():
            conn.execute('INSERT INTO public.destination_probe(value) VALUES (7)')
            return dict(self.runtime)
        with self.assertRaises(psycopg.errors.ReadOnlySqlTransaction):
            database.inspect_schema_migration(conn,self.actual,attempted_write,migration)
        self.assertEqual(self.target.sql('SELECT count(*) FROM public.destination_probe'),'0')

    def test_readonly_inspection_refuses_caller_owned_transaction(self):
        conn=self.connection()
        with conn.transaction():
            conn.execute('INSERT INTO public.destination_probe(value) VALUES (9)')
            with self.assertRaises(ValueError):self.authorized_inspection(conn=conn)
            self.assertEqual(self.target.sql('SELECT count(*) FROM public.destination_probe'),'0')
        self.assertEqual(self.target.sql('SELECT value FROM public.destination_probe'),'9')


    def test_inspection_snapshot_cannot_authorize_retry_during_concurrent_commit(self):
        self.addCleanup(self.target.sql,'DROP TABLE IF EXISTS public.schema_guard_probe')
        _,authority=self.schema_authority()
        migration={key:authority[key] for key in ('migration_id','artifact_sha256','authorization_id')}
        calls=[]
        def probe():
            calls.append(True)
            if len(calls)==2:
                # Ordinary second-connection commit after the inspection query,
                # before its final guard/return; no process or transport fault.
                self.assertEqual(self.authorized_schema(),'applied')
            return dict(self.runtime)
        result=database.inspect_schema_migration(self.connection(),self.actual,probe,migration)
        self.assertEqual(result['status'],'not_recorded')
        self.assertIs(result['retry_authorized'],False)
        self.assertIs(result['reopening_authorized'],False)
        self.assertEqual(self.ledger_count(),'1')
        self.assertEqual(self.authorized_inspection(),'recorded')


    def test_operator_scram_requirement_rejects_real_trust_only_cluster(self):
        with self.assertRaises(psycopg.OperationalError) as error:
            psycopg.connect(host=str(self.target.socket),port=5432,dbname='postgres',
                user='shop_test',password='SYNTHETIC_PRIVATE_PASSWORD',autocommit=True,
                connect_timeout=2,passfile=str(self.target.root/'absent.pgpass'),
                require_auth='scram-sha-256',options='-c default_transaction_read_only=on')
        self.assertIn('authentication',str(error.exception))
        self.assertEqual(self.target.sql('SELECT count(*) FROM public.destination_probe'),'0')


    def test_real_operator_scram_connection_and_readonly_ledger_outcomes(self):
        """Actual libpq/SCRAM/SQL; root records, runtime and path are fixtures."""
        import contextlib,json,os,tempfile
        from unittest.mock import patch
        from psycopg import sql
        import dev_postgres,operator_inspect as cli,schema_reconciliation
        from test_process_probe import candidate_bundle
        with dev_postgres.isolated_postgres() as pg:
            pg.sql((ROOT/'ops/postgresql/schema-ledger.sql').read_text())
            # Establish a fixture-only management connection before switching HBA.
            # Password never appears in command arguments or server SQL logs.
            admin=self.connection(pg)
            password='SYNTHETIC_SCRAM_ONLY_4f8d7146'
            admin.execute("SET password_encryption = 'scram-sha-256'")
            admin.execute(sql.SQL('ALTER ROLE shop_test PASSWORD {}').format(sql.Literal(password)))
            self.assertTrue(admin.execute("SELECT rolpassword LIKE 'SCRAM-SHA-256$%' FROM pg_authid WHERE rolname='shop_test'").fetchone()[0])
            # Only this token-owned disposable cluster's HBA is replaced/reloaded.
            hba=pg.root/'data/pg_hba.conf'
            hba.write_text('local all all scram-sha-256\nhost all all 0.0.0.0/0 reject\nhost all all ::0/0 reject\n')
            loaded_before=admin.execute('SELECT pg_conf_load_time()').fetchone()[0]
            self.assertTrue(admin.execute('SELECT pg_reload_conf()').fetchone()[0])
            # Reload is asynchronous: wait boundedly for parsed target HBA before
            # making any authentication assertion, never retry wrong credentials.
            import time
            deadline=time.monotonic()+2
            while True:
                methods=admin.execute("SELECT auth_method FROM pg_hba_file_rules WHERE type='local' AND error IS NULL").fetchall()
                loaded_after=admin.execute('SELECT pg_conf_load_time()').fetchone()[0]
                if methods==[('scram-sha-256',)] and loaded_after>loaded_before:break
                if time.monotonic()>=deadline:self.fail('owned SCRAM HBA reload did not complete')
                time.sleep(0.01)
            # The authenticated connection itself proves the active HBA offers
            # SCRAM; require_auth rejects an accidental trust negotiation.
            value=candidate_bundle();records=value['records']
            process=records['database-process.json'];authorization=records['schema-reconciliation.json']
            uid=os.stat(pg.root).st_uid
            expected=dict(process['database'],account_uid=uid,database='postgres',role='shop_test',
                system_identifier=str(admin.execute('SELECT system_identifier FROM pg_control_system()').fetchone()[0]))
            process['database']=expected;authorization['database']=expected
            connection_record=dict(records['operator-connection.json'],database=expected,socket_directory=str(pg.socket))
            artifact=__import__('base64').b64decode(value['artifact_base64'])
            real_fd_reader=cli.read_private_fd;real_validate=self.real_validate
            opened=[]
            def connect(**kwargs):
                # Only host attestation uses a fixture path; real libpq and all
                # command-selected authentication/session options execute here.
                connection=psycopg.connect(**kwargs);opened.append(connection)
                self.assertEqual(connection.execute('SHOW default_transaction_read_only').fetchone()[0],'on')
                self.assertEqual(connection.execute('SHOW transaction_read_only').fetchone()[0],'on')
                with self.assertRaises(psycopg.errors.ReadOnlySqlTransaction):
                    connection.execute('DELETE FROM shop_control.schema_migrations')
                return connection
            def local_validate(wanted,observed):
                if wanted==observed:return real_validate(wanted,observed)
                self.assertEqual(observed['pgdata'],str(pg.root/'data'))
                return real_validate(wanted,dict(observed,pgdata='/var/lib/shop/postgres'))
            with contextlib.ExitStack() as stack:
                inputs={}
                for descriptor,data in ((0,artifact),(3,password.encode())):
                    file=stack.enter_context(tempfile.TemporaryFile(dir=pg.root))
                    file.write(data);file.flush();os.fchmod(file.fileno(),0o600)
                    if os.geteuid()==0:os.fchown(file.fileno(),uid,os.stat(pg.root).st_gid)
                    inputs[descriptor]=file
                stack.enter_context(patch.dict(os.environ,cli.SAFE_ENV,clear=True))
                stack.enter_context(patch.object(cli.os,'geteuid',return_value=uid))
                stack.enter_context(patch.object(cli,'SOCKET_DIRECTORY',str(pg.socket)))
                stack.enter_context(patch.object(cli,'load_connection',return_value=connection_record))
                stack.enter_context(patch.object(cli.process_probe,'load_record',return_value=process))
                stack.enter_context(patch.object(schema_reconciliation,'load_authorization',return_value=authorization))
                stack.enter_context(patch.object(cli.process_probe,'probe',return_value={'container_id':expected['container_id'],'account_uid':uid}))
                stack.enter_context(patch.object(cli,'socket_identity',return_value=(1,2,uid)))
                stack.enter_context(patch.object(database,'validate_database_identity',side_effect=local_validate))
                stack.enter_context(patch.object(cli,'read_private_fd',side_effect=lambda fd,maximum,minimum=1:real_fd_reader(inputs[fd].fileno(),maximum,minimum)))
                # Preserve the real function before patching the shared module.
                actual_connect=psycopg.connect
                def tracked_connect(**kwargs):
                    with patch.object(psycopg,'connect',actual_connect):return connect(**kwargs)
                stack.enter_context(patch.object(cli.psycopg,'connect',side_effect=tracked_connect))
                for status in ('not_recorded','recorded','conflict'):
                    if status=='recorded':
                        admin.execute('INSERT INTO shop_control.schema_migrations(migration_id,artifact_sha256,authorization_id,applied_at) VALUES (%s,%s,%s,clock_timestamp())',tuple(authorization[k] for k in ('migration_id','artifact_sha256','authorization_id')))
                    elif status=='conflict':
                        admin.execute("UPDATE shop_control.schema_migrations SET artifact_sha256=%s",('c'*64,))
                    before=admin.execute('SELECT * FROM shop_control.schema_migrations').fetchall()
                    result=cli.inspect_from_fds()
                    self.assertEqual(result,{'schema_version':1,'status':status,'retry_authorized':False,'reopening_authorized':False})
                    self.assertTrue(opened[-1].closed)
                    self.assertEqual(admin.execute('SELECT * FROM shop_control.schema_migrations').fetchall(),before)
                private=inputs[3];private.seek(0);private.write(b'SYNTHETIC_WRONG_PASSWORD_00');private.truncate();private.flush()
                with self.assertRaises(psycopg.OperationalError):cli.inspect_from_fds()
                self.assertEqual(len(opened),3)

                # Exercise source schema SCRAM with a distinct restricted login.
                # The admin only provisions this disposable fixture; the command
                # must connect directly as the role, never SET ROLE.
                import operator_schema as schema_command
                import schema_authorization as schema_auth
                admin.execute('TRUNCATE shop_control.schema_migrations')
                admin.execute('CREATE TABLE public.destination_probe(value integer)')
                admin.execute('CREATE ROLE schema_candidate LOGIN NOSUPERUSER NOCREATEDB '
                              'NOCREATEROLE NOREPLICATION NOBYPASSRLS')
                admin.execute(sql.SQL('ALTER ROLE schema_candidate PASSWORD {}').format(sql.Literal(password)))
                admin.execute('CREATE SCHEMA shop_app AUTHORIZATION schema_candidate')
                admin.execute('ALTER SCHEMA shop_control OWNER TO schema_candidate')
                admin.execute('ALTER TABLE shop_control.schema_migrations OWNER TO schema_candidate')
                expected=dict(expected,role='schema_candidate')
                process['database']=expected
                connection_record['database']=expected
                schema_data=json.dumps({'schema_version':1,'migration_id':'synthetic_001',
                    'statements':['CREATE TABLE shop_app.operator_schema_probe(id integer)']}).encode()
                _,write_authority=self.schema_authority(schema_data)
                write_authority['database']=expected
                for descriptor,data in ((0,schema_data),(3,password.encode())):
                    file=inputs[descriptor];file.seek(0);file.write(data);file.truncate();file.flush()
                schema_opened=[]
                def schema_connect(**kwargs):
                    connection=actual_connect(**kwargs);schema_opened.append(connection)
                    self.assertEqual(connection.execute('SHOW default_transaction_read_only').fetchone()[0],'off')
                    self.assertEqual(connection.execute('SELECT current_user, session_user').fetchone(),
                                     ('schema_candidate','schema_candidate'))
                    self.assertEqual(connection.execute('SELECT rolsuper, rolcreatedb, rolcreaterole, '
                        'rolreplication, rolbypassrls FROM pg_roles WHERE rolname=current_user').fetchone(),
                        (False,False,False,False,False))
                    return connection
                with patch.object(schema_auth,'load_authorization',return_value=write_authority), \
                     patch.object(cli.psycopg,'connect',side_effect=schema_connect):
                    # Both identity privileges are necessary; neither failed
                    # attempt may create DDL or ledger effects, and no retry is
                    # performed by the command. Each call is explicit here.
                    for grant in ('GRANT EXECUTE ON FUNCTION pg_catalog.pg_control_system() TO schema_candidate',
                                  'GRANT pg_read_all_settings TO schema_candidate'):
                        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                            schema_command.apply_from_fds()
                        self.assertTrue(schema_opened[-1].closed)
                        self.assertIsNone(admin.execute("SELECT to_regclass('shop_app.operator_schema_probe')").fetchone()[0])
                        self.assertEqual(admin.execute('SELECT count(*) FROM shop_control.schema_migrations').fetchone()[0],0)
                        admin.execute(grant)
                    self.assertEqual(schema_command.apply_from_fds(),{'schema_version':1,'status':'applied',
                        'retry_authorized':False,'reopening_authorized':False})
                    self.assertEqual(schema_command.apply_from_fds()['status'],'already_applied')
                self.assertEqual(len(schema_opened),4)
                # Ordinary PostgreSQL ACLs deny unrelated objects and privilege
                # escalation even outside the reviewed-statement prefix filter.
                restricted=schema_connect(host=str(pg.socket),port=5432,dbname='postgres',
                    user='schema_candidate',password=password,autocommit=True,client_encoding='utf8',
                    require_auth='scram-sha-256',passfile='/dev/null',connect_timeout=2)
                try:
                    for forbidden in ('CREATE DATABASE forbidden_schema_database',
                                      'CREATE ROLE forbidden_schema_role',
                                      'SET ROLE shop_test',
                                      "SELECT pg_read_file('/etc/passwd')",
                                      'CREATE TABLE public.forbidden_schema_table(id integer)',
                                      'UPDATE public.destination_probe SET value=99'):
                        with self.subTest(forbidden=forbidden), self.assertRaises(psycopg.errors.InsufficientPrivilege):
                            restricted.execute(forbidden)
                finally:
                    restricted.close()
                # A later ACL denial rolls back earlier schema and ledger work.
                failing_data=json.dumps({'schema_version':1,'migration_id':'synthetic_acl_denied',
                    'statements':['CREATE TABLE shop_app.must_rollback(id integer)',
                                  'CREATE TABLE public.forbidden_schema_table(id integer)']}).encode()
                _,failing_authority=self.schema_authority(failing_data)
                failing_authority.update(database=expected,authorization_id='d'*32,migration_id='synthetic_acl_denied')
                file=inputs[0];file.seek(0);file.write(failing_data);file.truncate();file.flush()
                with patch.object(schema_auth,'load_authorization',return_value=failing_authority), \
                     patch.object(cli.psycopg,'connect',side_effect=schema_connect):
                    with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                        schema_command.apply_from_fds()
                self.assertIsNone(admin.execute("SELECT to_regclass('shop_app.must_rollback')").fetchone()[0])
                self.assertEqual(len(schema_opened),6)
                self.assertTrue(all(connection.closed for connection in schema_opened))
                self.assertEqual(admin.execute("SELECT count(*) FROM pg_class WHERE oid=to_regclass('shop_app.operator_schema_probe')").fetchone()[0],1)
                self.assertEqual(admin.execute('SELECT count(*) FROM shop_control.schema_migrations').fetchone()[0],1)
            admin.close()

    def test_schema_transport_admission_failure_rolls_back_schema_and_ledger(self):
        for fail_at in (1,2,3,4):
            calls=[]
            def admission():
                calls.append(True)
                if len(calls)==fail_at:raise ValueError('synthetic transport changed')
                return True
            with self.subTest(fail_at=fail_at),self.assertRaises(ValueError):self.authorized_schema(admission_check=admission)
            self.assertEqual(len(calls),fail_at)
            self.assertEqual(self.schema_exists(),'0')
            self.assertEqual(self.target.sql('SELECT count(*) FROM shop_control.schema_migrations'),'0')
        with self.assertRaises(ValueError):self.authorized_schema(admission_check=lambda:False)
        self.assertEqual(self.schema_exists(),'0')
