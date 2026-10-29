"""Real restricted PostgreSQL login/Django SQL; synthetic runtime and admission."""
import importlib
from pathlib import Path
import sys
import subprocess
import unittest
import psycopg
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'ops/runtime'))
import database
import django_transaction
import test_django_transaction as transactions

ROOT = Path(__file__).resolve().parents[1]


class ApplicationObserverTests(transactions.DjangoTransactionTests):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.addClassCleanup(cls.stack.close)
        cls.pg.sql('CREATE ROLE sll_app LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS')
        cls.pg.sql('CREATE ROLE sll_other LOGIN')
        cls.pg.sql('GRANT SELECT, INSERT, UPDATE, DELETE ON public.orm_guard_probe TO sll_app')
        from django.db import connections
        connections['guarded'].close()
        del connections['guarded']
        connections.databases['guarded']['USER'] = 'sll_app'
        cls.expected = dict(cls.expected, role='sll_app')

    def setUp(self):
        self.pg.sql('ALTER ROLE sll_app NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS')
        self.pg.sql('REVOKE shop_test, pg_read_all_settings FROM sll_app')
        self.pg.sql('REVOKE CREATE ON SCHEMA public FROM sll_app')
        self.pg.sql('DROP SCHEMA IF EXISTS shop_runtime CASCADE')
        self.pg.sql((ROOT / 'ops/postgresql/application-observer.sql').read_text())
        self.pg.sql('GRANT USAGE ON SCHEMA shop_runtime TO sll_app')
        self.pg.sql('GRANT EXECUTE ON FUNCTION shop_runtime.database_identity_v1() TO sll_app')
        super().setUp()

    def producer(self):
        return importlib.import_module('application_observer')

    def guarded(self, probe=None, expected=None):
        return django_transaction.guarded_application_atomic(
            self.wrapper, self.expected if expected is None else expected,
            probe or (lambda: dict(self.runtime)), observer_owner='shop_test')

    def observed(self, owner='shop_test'):
        with self.wrapper.connection.cursor() as cursor:
            return self.producer().observe_application_database(cursor, self.runtime, owner)

    def test_real_restricted_login_observes_identity_without_broad_metadata_privileges(self):
        with self.wrapper.connection.cursor() as cursor:
            cursor.execute('SELECT current_user, session_user')
            self.assertEqual(cursor.fetchone(), ('sll_app', 'sll_app'))
            cursor.execute('SELECT system_identifier::text FROM pg_catalog.pg_control_system()')
            self.assertEqual(cursor.fetchone(), (self.expected['system_identifier'],))
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                cursor.execute("SELECT pg_catalog.current_setting('data_directory')")
        self.assertEqual(self.observed(), self.expected)
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            with self.wrapper.connection.cursor() as cursor:
                database.observe_database(cursor, self.runtime)

    def test_wrong_or_invalid_approved_owner_denies_without_application_write(self):
        for owner in ('sll_app', 'sll_other', 'public; SELECT 1', '', None):
            with self.subTest(owner=owner), self.assertRaises(ValueError):
                self.observed(owner)
        self.assertEqual(self.count(), '0')

    def test_missing_function_denies_without_adoption_or_fallback(self):
        self.pg.sql('DROP FUNCTION shop_runtime.database_identity_v1()')
        with self.assertRaises(ValueError):
            with self.guarded(): self.insert(1)
        self.assertEqual(self.count(), '0')

    def reinstall_observer(self):
        self.pg.sql('DROP SCHEMA shop_runtime CASCADE')
        self.pg.sql((ROOT / 'ops/postgresql/application-observer.sql').read_text())
        self.pg.sql('GRANT USAGE ON SCHEMA shop_runtime TO sll_app')
        self.pg.sql('GRANT EXECUTE ON FUNCTION shop_runtime.database_identity_v1() TO sll_app')

    def test_changed_body_or_search_path_or_execution_mode_denies(self):
        for change in ('body', 'search_path', 'invoker'):
            with self.subTest(change=change):
                if change == 'body':
                    self.pg.sql("CREATE OR REPLACE FUNCTION shop_runtime.database_identity_v1() RETURNS TABLE(system_identifier text, pgdata text) LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $$SELECT '9999999999999999999'::text, '/wrong'::text$$")
                elif change == 'search_path':
                    self.pg.sql('ALTER FUNCTION shop_runtime.database_identity_v1() SET search_path=public,pg_catalog')
                else:
                    self.pg.sql('ALTER FUNCTION shop_runtime.database_identity_v1() SECURITY INVOKER')
                with self.assertRaises(ValueError): self.observed()
                self.reinstall_observer()
                self.assertEqual(self.observed(), self.expected)

    def test_public_other_role_and_grant_option_function_access_deny(self):
        for grant in ('PUBLIC', 'sll_other', 'sll_app WITH GRANT OPTION'):
            with self.subTest(grant=grant):
                self.pg.sql('GRANT EXECUTE ON FUNCTION shop_runtime.database_identity_v1() TO ' + grant)
                with self.assertRaises(ValueError): self.observed()
                self.pg.sql('REVOKE ALL ON FUNCTION shop_runtime.database_identity_v1() FROM PUBLIC, sll_other, sll_app')
                self.pg.sql('GRANT EXECUTE ON FUNCTION shop_runtime.database_identity_v1() TO sll_app')

    def test_schema_create_or_public_usage_denies(self):
        for grant in ('CREATE TO sll_app', 'USAGE TO PUBLIC'):
            with self.subTest(grant=grant):
                self.pg.sql('GRANT ' + grant.split(' TO ')[0] + ' ON SCHEMA shop_runtime TO ' + grant.split(' TO ')[1])
                with self.assertRaises(ValueError): self.observed()
                self.pg.sql('REVOKE ALL ON SCHEMA shop_runtime FROM PUBLIC, sll_app')
                self.pg.sql('GRANT USAGE ON SCHEMA shop_runtime TO sll_app')

    def test_role_membership_or_broad_role_attributes_deny(self):
        for statement in ('GRANT pg_read_all_settings TO sll_app', 'GRANT shop_test TO sll_app',
                          'ALTER ROLE sll_app CREATEDB'):
            with self.subTest(statement=statement):
                self.pg.sql(statement)
                with self.assertRaises(ValueError): self.observed()
                self.pg.sql('REVOKE shop_test, pg_read_all_settings FROM sll_app')
                self.pg.sql('ALTER ROLE sll_app NOCREATEDB')

    def test_late_execute_revocation_rolls_back_both_writes(self):
        with self.assertRaises((ValueError, psycopg.Error)):
            with self.guarded():
                self.insert(1); self.insert(2)
                self.pg.sql('REVOKE EXECUTE ON FUNCTION shop_runtime.database_identity_v1() FROM sll_app')
        self.assertEqual(self.count(), '0')

    def test_temporary_type_cannot_execute_as_the_function_owner(self):
        self.pg.sql('CREATE TABLE public.observer_escalation_probe (who text)')
        self.addCleanup(self.pg.sql, 'DROP TABLE public.observer_escalation_probe')
        raw = self.wrapper.connection
        def cleanup():
            with raw.cursor() as cursor:
                cursor.execute('DROP DOMAIN IF EXISTS pg_temp.text')
                cursor.execute('DROP FUNCTION IF EXISTS pg_temp.observer_domain_check(pg_catalog.text)')
                cursor.execute('DROP TABLE IF EXISTS pg_temp.observer_temp_sentinel')
        self.addCleanup(cleanup)
        with raw.cursor() as cursor:
            cursor.execute('CREATE TEMP TABLE observer_temp_sentinel (v integer)')
            cursor.execute("""CREATE FUNCTION pg_temp.observer_domain_check(value pg_catalog.text)
                RETURNS boolean LANGUAGE plpgsql AS $$ BEGIN
                INSERT INTO public.observer_escalation_probe VALUES (current_user::pg_catalog.text);
                RETURN true; END $$""")
            cursor.execute('CREATE DOMAIN pg_temp.text AS pg_catalog.text CHECK(pg_temp.observer_domain_check(VALUE))')
            cursor.execute('SELECT * FROM shop_runtime.database_identity_v1()')
            self.assertEqual(cursor.fetchone(), (self.expected['system_identifier'], self.expected['pgdata']))
        self.assertEqual(self.pg.sql('SELECT count(*) FROM public.observer_escalation_probe'), '0')
        self.assertEqual(self.observed(), self.expected)

    def test_unrelated_session_role_cannot_use_definer(self):
        conn = psycopg.connect(host=str(self.pg.socket), port=5432, dbname='postgres',
                               user='sll_other', autocommit=True, client_encoding='utf8')
        self.addCleanup(conn.close)
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            conn.execute('SELECT * FROM shop_runtime.database_identity_v1()')

    def test_source_has_no_implicit_login_grant_or_idempotent_adoption(self):
        data = (ROOT / 'ops/postgresql/application-observer.sql').read_text()
        self.assertNotIn('GRANT ', data)
        self.assertNotIn('IF NOT EXISTS', data)
        self.assertNotIn('CREATE OR REPLACE', data)
        with self.assertRaises(subprocess.CalledProcessError): self.pg.sql(data)
        self.assertEqual(self.observed(), self.expected)


if __name__ == '__main__':
    unittest.main()
