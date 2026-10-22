"""Synthetic command transport controls; real transaction admission tested separately."""
import contextlib
import copy
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'ops/runtime'))
import operator_schema as command
import test_operator_inspect as inspect_tests


class OperatorSchemaTests(unittest.TestCase):
    @contextlib.contextmanager
    def fixture(self):
        connection_record = inspect_tests.OperatorInspectTests().record()
        process = {'database': connection_record['database'], 'process': {
            'executable': connection_record['pg_control'].replace('/pg_controldata', '/postgres')}}
        transport = command.transport
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(command.control,'admission',contextlib.nullcontext))
            stack.enter_context(patch.object(command.control,'check_admission'))
            stack.enter_context(patch.dict(os.environ, transport.SAFE_ENV, clear=True))
            stack.enter_context(patch.object(command.os, 'geteuid', return_value=9909))
            loaded = stack.enter_context(patch.object(transport, 'load_connection', return_value=connection_record))
            stack.enter_context(patch.object(transport.process_probe, 'load_record', return_value=process))
            authority = stack.enter_context(patch.object(command.schema, 'load_authorization', return_value={'database': connection_record['database']}))
            artifact = stack.enter_context(patch.object(command.schema, 'read_artifact'))
            stack.enter_context(patch.object(transport.process_probe, 'probe'))
            stack.enter_context(patch.object(transport, 'require_peer'))
            socket = stack.enter_context(patch.object(transport, 'socket_identity', return_value=(1, 2, 9909)))
            reader = stack.enter_context(patch.object(transport, 'read_private_fd', side_effect=[b'EXACT_ARTIFACT', b'SYNTHETIC_PRIVATE_PASSWORD']))
            connection = Mock()
            connection.execute.return_value.fetchone.return_value = (True,)
            connect = stack.enter_context(patch.object(transport.psycopg, 'connect', return_value=connection))
            def apply(*args, **kwargs):
                self.assertTrue(kwargs['admission_check']())
                return 'applied'
            mutation = stack.enter_context(patch.object(command.schema, 'execute_authorized_schema', side_effect=apply))
            yield dict(record=connection_record, loaded=loaded, authority=authority, artifact=artifact,
                       reader=reader, socket=socket, connection=connection, connect=connect, mutation=mutation)

    def test_explicit_private_transport_and_fresh_admission(self):
        with self.fixture() as case:
            result = command.apply_from_fds()
            self.assertEqual(result['status'], 'applied')
            self.assertFalse(result['retry_authorized']); self.assertFalse(result['reopening_authorized'])
            self.assertEqual(case['connect'].call_count, 1)
            self.assertEqual(case['mutation'].call_count, 1)
            self.assertGreaterEqual(case['loaded'].call_count, 5)
            options = case['connect'].call_args.kwargs
            self.assertIn('default_transaction_read_only=off', options['options'])
            self.assertEqual(options['require_auth'], 'scram-sha-256')
            self.assertEqual(options['passfile'], '/dev/null')
            self.assertEqual(options['host'], command.transport.SOCKET_DIRECTORY)
            case['connection'].close.assert_called_once()

    def test_invalid_exact_artifact_denied_before_credentials_or_connect(self):
        with self.fixture() as case:
            case['artifact'].side_effect = ValueError('SYNTHETIC_PRIVATE_PASSWORD')
            with self.assertRaises(ValueError): command.apply_from_fds()
            self.assertEqual(case['reader'].call_count, 1)
            case['connect'].assert_not_called(); case['mutation'].assert_not_called()

    def test_record_change_during_admission_denies_before_connect(self):
        with self.fixture() as case:
            changed = copy.deepcopy(case['record']); changed['database']['role'] = 'changed'
            case['loaded'].side_effect = [case['record'], changed]
            with self.assertRaises(ValueError): command.apply_from_fds()
            case['connect'].assert_not_called()

    def test_socket_change_inside_mutation_and_postcommit_close_without_retry(self):
        for changed_at in (4, 5):
            with self.subTest(changed_at=changed_at), self.fixture() as case:
                case['socket'].side_effect = [(1,2,9909)] * (changed_at-1) + [(1,3,9909)]
                with self.assertRaises(ValueError): command.apply_from_fds()
                self.assertEqual(case['connect'].call_count, 1)
                self.assertEqual(case['mutation'].call_count, 1)
                case['connection'].close.assert_called_once()

    def test_root_and_ambient_defaults_denied(self):
        for env, uid in (({'PGPASSWORD':'SYNTHETIC'},9909), (command.transport.SAFE_ENV,0)):
            with patch.dict(os.environ,env,clear=True), patch.object(command.os,'geteuid',return_value=uid), patch.object(command.transport,'load_connection') as loaded:
                with self.assertRaises(ValueError): command.apply_from_fds()
                loaded.assert_not_called()

    def test_closed_result_and_no_private_exception_or_argument_echo(self):
        report = {'schema_version':1,'status':'applied','retry_authorized':False,'reopening_authorized':False}
        for change in ({'extra':'PRIVATE'}, {'retry_authorized':True}, {'reopening_authorized':True}, {'status':'unknown'}):
            with self.assertRaises(ValueError): command.validate_report(dict(report,**change))
        output = []
        with patch.object(command.os,'write',side_effect=lambda fd,data:output.append((fd,data))):
            self.assertEqual(command.main(['--password','SYNTHETIC_PRIVATE_PASSWORD']),2)
            with patch.object(command,'apply_from_fds',side_effect=RuntimeError('SYNTHETIC_PRIVATE_PASSWORD')):
                self.assertEqual(command.main(['apply-reviewed-schema']),1)
        self.assertEqual(output,[(2,command.ERROR),(2,command.ERROR)])

    def test_connect_failure_has_one_attempt_and_no_mutation(self):
        with self.fixture() as case:
            case['connect'].side_effect=RuntimeError('SYNTHETIC_PRIVATE_PASSWORD')
            with self.assertRaises(RuntimeError):command.apply_from_fds()
            self.assertEqual(case['connect'].call_count,1)
            case['mutation'].assert_not_called()

    def test_entrypoint_scrubs_environment(self):
        with patch.dict(os.environ,{'PGPASSWORD':'SYNTHETIC_PRIVATE_PASSWORD'},clear=True), \
             patch.object(command.sys,'argv',['operator','--help']),patch.object(command,'main') as main:
            def check(argv):
                self.assertEqual(dict(os.environ),command.transport.SAFE_ENV)
                self.assertEqual(argv,['--help'])
                return 0
            main.side_effect=check
            self.assertEqual(command.entrypoint(),0)


    def test_schema_role_predicate_denies_absent_or_false_observation(self):
        for row in (None, (False,), (True, False)):
            connection=Mock()
            connection.execute.return_value.fetchone.return_value=row
            with self.subTest(row=row), self.assertRaises(ValueError):
                command.require_schema_role(connection)
        connection.execute.assert_called_once()
        self.assertTrue(connection.execute.call_args.kwargs['prepare'])


    def test_rejected_schema_role_closes_before_mutation(self):
        with self.fixture() as case:
            case['connection'].execute.return_value.fetchone.return_value=(False,)
            with self.assertRaises(ValueError):command.apply_from_fds()
            self.assertEqual(case['connect'].call_count,1)
            case['mutation'].assert_not_called()
            case['connection'].close.assert_called_once()


    def test_peer_denial_closes_before_schema_mutation(self):
        with self.fixture() as case, patch.object(command.transport,'require_peer',side_effect=ValueError):
            with self.assertRaises(ValueError):command.apply_from_fds()
            case['mutation'].assert_not_called()
            case['connection'].close.assert_called_once()
