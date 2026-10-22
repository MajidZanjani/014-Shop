"""Actual Django/Psycopg SQL; synthetic runtime identity and scratch admission."""
import contextlib
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'ops/runtime'))
import control
import database
import django_transaction
import test_control_admission as admission_tests


class DjangoTransactionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import dev_postgres
        from django.conf import settings
        from django.db import connections
        cls.stack=contextlib.ExitStack()
        cls.pg=cls.stack.enter_context(dev_postgres.isolated_postgres())
        cls.pg.sql('CREATE TABLE public.orm_guard_probe (value integer PRIMARY KEY)')
        if not settings.configured:
            settings.configure(DATABASES={'default':{'ENGINE':'django.db.backends.dummy'}},USE_TZ=True)
        import django
        django.setup()
        connections.databases['guarded']={
            'ENGINE':'django.db.backends.postgresql','NAME':'postgres','USER':'shop_test',
            'PASSWORD':'','HOST':str(cls.pg.socket),'PORT':'5432','OPTIONS':{},
            'AUTOCOMMIT':True,'ATOMIC_REQUESTS':False,'CONN_MAX_AGE':0,
            'CONN_HEALTH_CHECKS':False,'TIME_ZONE':None,'TEST':{}}
        cls.runtime={'container_id':'a'*64,'account_uid':9909}
        cls.expected=dict(cls.runtime,system_identifier=cls.pg.sql('SELECT system_identifier FROM pg_control_system()'),
            pgdata=str(cls.pg.root/'data'),database='postgres',role='shop_test',
            server_address='unix-socket',server_port=5432)

    @classmethod
    def tearDownClass(cls):
        from django.db import connections
        connections['guarded'].close()
        cls.stack.close()

    def setUp(self):
        from django.db import connections
        self.wrapper=connections['guarded'];self.wrapper.ensure_connection()
        self.pg.sql('DELETE FROM public.orm_guard_probe')
        self.stack=contextlib.ExitStack();self.addCleanup(self.stack.close)
        real_validate=database.validate_database_identity
        def validate(expected,observed):
            self.assertEqual(expected['pgdata'],str(self.pg.root/'data'))
            self.assertEqual(observed['pgdata'],expected['pgdata'])
            return real_validate(dict(expected,pgdata='/var/lib/shop/postgres'),
                dict(observed,pgdata='/var/lib/shop/postgres'))
        for module in (database,django_transaction):
            self.stack.enter_context(patch.object(module,'validate_database_identity',side_effect=validate))
        self.barrier_fixture=admission_tests.ControlAdmissionTests()
        _,self.barrier,_=self.stack.enter_context(self.barrier_fixture.fixture())

    def guarded(self,probe=None,expected=None):
        return django_transaction.guarded_atomic(self.wrapper,
            self.expected if expected is None else expected,probe or (lambda:dict(self.runtime)))

    def insert(self,value):
        with self.wrapper.cursor() as cursor:
            cursor.execute('INSERT INTO public.orm_guard_probe VALUES (%s)',(value,))

    def count(self):
        return self.pg.sql('SELECT count(*) FROM public.orm_guard_probe')

    def test_multiple_django_statements_commit_in_one_owned_transaction(self):
        with self.guarded() as wrapper:
            self.assertIs(wrapper,self.wrapper)
            self.insert(1);self.insert(2)
            self.assertEqual(self.count(),'0')
        self.assertEqual(self.count(),'2')
        self.assertTrue(self.wrapper.get_autocommit())

    def test_application_exception_rolls_back_all_statements(self):
        with self.assertRaisesRegex(ValueError,'synthetic'):
            with self.guarded():
                self.insert(1);self.insert(2);raise ValueError('synthetic')
        self.assertEqual(self.count(),'0')

    def test_changed_live_identity_and_runtime_roll_back(self):
        for kind in ('database','runtime','durability'):
            with self.subTest(kind=kind):
                calls=[]
                def probe():
                    calls.append(1)
                    return dict(self.runtime,container_id='b'*64) if kind=='runtime' and len(calls)>1 else dict(self.runtime)
                expected=dict(self.expected,database='synthetic_decoy') if kind=='database' else self.expected
                with self.assertRaises(ValueError):
                    with self.guarded(probe,expected):
                        self.insert(1)
                        if kind=='durability':
                            with self.wrapper.cursor() as cursor:cursor.execute('SET LOCAL synchronous_commit=off')
                self.assertEqual(self.count(),'0')

    def test_changed_admission_aborts_before_commit(self):
        with self.assertRaises(ValueError):
            with self.guarded():
                self.insert(1);self.barrier.write_bytes(b'blocked')
        self.assertEqual(self.count(),'0')

    def test_existing_outer_and_manual_transactions_are_denied(self):
        from django.db import transaction
        with transaction.atomic(using='guarded'):
            with self.assertRaises(ValueError):
                with self.guarded():self.fail('nested outer accepted')
        self.wrapper.set_autocommit(False)
        try:
            with self.assertRaises(ValueError):
                with self.guarded():self.fail('manual transaction accepted')
        finally:self.wrapper.rollback();self.wrapper.set_autocommit(True)

    def test_no_reconnection_when_missing_connection(self):
        self.wrapper.close()
        with patch.object(self.wrapper,'ensure_connection',side_effect=AssertionError('connect')):
            with self.assertRaises(ValueError):
                with self.guarded():self.fail('missing connection accepted')

    def test_deferred_callbacks_and_rollback_only_are_denied(self):
        from django.db import transaction
        for kind in ('callback','rollback'):
            with self.subTest(kind=kind):
                called=[]
                with self.assertRaises(ValueError):
                    with self.guarded():
                        self.insert(1)
                        if kind=='callback':transaction.on_commit(lambda:called.append(1),using='guarded')
                        else:transaction.set_rollback(True,using='guarded')
                self.assertEqual(called,[]);self.assertEqual(self.count(),'0')

    def test_admission_excludes_publication_through_commit_and_rollback(self):
        for kind in ('commit','rollback'):
            with self.subTest(kind=kind):
                actual=getattr(self.wrapper,kind);calls=[]
                def finish():
                    calls.append(1)
                    self.assertEqual(self.barrier_fixture.child_lock(self.barrier,True),3)
                    return actual()
                with patch.object(self.wrapper,kind,side_effect=finish):
                    if kind=='rollback':
                        with self.assertRaises(ValueError):
                            with self.guarded():self.insert(1);raise ValueError('synthetic')
                    else:
                        with self.guarded():self.insert(2)
                self.assertEqual(calls,[1])
                self.assertEqual(self.barrier_fixture.child_lock(self.barrier,True),0)

    def test_actual_queryset_create_update_delete_share_guarded_transaction(self):
        from django.db import models
        from django.test.utils import isolate_apps
        with isolate_apps():
            class SyntheticGuardProbe(models.Model):
                value=models.IntegerField(primary_key=True)
                class Meta:
                    app_label='synthetic_guard'
                    db_table='orm_guard_probe'
                    managed=False
            rows=SyntheticGuardProbe.objects.using('guarded')
            with self.guarded():
                rows.create(value=1);rows.create(value=2)
                self.assertEqual(rows.filter(value=1).update(value=3),1)
                self.assertEqual(rows.filter(value=2).delete()[0],1)
                self.assertEqual(list(rows.values_list('value',flat=True)),[3])
                self.assertEqual(self.count(),'0')
            self.assertEqual(self.pg.sql('SELECT value FROM public.orm_guard_probe'),'3')
