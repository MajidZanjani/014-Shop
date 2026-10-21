"""Console privacy tests; no rootless container or runtime fault qualification."""
import json
import os
from pathlib import Path
import subprocess
import sys
import secrets
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'ops/runtime'))
import bootstrap
import postgres_entrypoint as entry

CANARY='SYNTHETIC-private-host-key-password-bearer-token-'+secrets.token_hex(16)


class DiagnosticTests(unittest.TestCase):
    def setUp(self):
        self.assertGreater(os.geteuid(),0)
        self.temp=tempfile.TemporaryDirectory(prefix='diagnostics-',dir=os.environ['SHOP_DIAGNOSTIC_TEST_ROOT'])
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)

    def events(self,result):
        self.assertNotIn(CANARY,result.stdout+result.stderr)
        self.assertEqual(result.stderr,'')
        events=[json.loads(line) for line in result.stdout.splitlines()]
        self.assertTrue(events)
        self.assertTrue(all(value in ({'event':'postgres.diagnostic'},{'event':'postgres.diagnostic_stream_closed'},
            {'event':'postgres.diagnostic_failed'},{'event':'postgres.startup_failed'}) for value in events))
        return events

    def fake(self,code,env=None):
        launcher="import sys;sys.dont_write_bytecode=True;sys.path.insert(0,"+repr(str(ROOT/'ops/runtime'))+");import postgres_entrypoint as e;e._exec_filtered("+repr([os.environ['SHOP_PYTHON'],'-I','-c',code])+")"
        return subprocess.run([os.environ['SHOP_PYTHON'],'-I','-c',launcher],capture_output=True,text=True,
            timeout=10,env=env)

    def test_stdout_stderr_multiline_binary_and_forged_json_discarded(self):
        code="import os;os.write(1,"+repr((CANARY+'\n{"event":"'+CANARY+'"}\n').encode())+");os.write(2,"+repr((CANARY+'\nDETAIL: '+CANARY).encode()+b'\xff\x00')+")"
        result=self.fake(code);self.assertEqual(result.returncode,0);self.events(result)

    def test_large_line_is_bounded_and_rate_limited(self):
        # Avoid command-line size limits: emit the synthetic pattern in the child.
        code="import os;os.write(2,"+repr(CANARY.encode())+"*20000)"
        result=self.fake(code);self.events(result)
        self.assertLess(len(result.stdout),1024)

    def test_native_exit_status_preserved(self):
        result=self.fake('import sys;sys.exit(7)')
        self.assertEqual(result.returncode,7);self.events(result)

    def test_native_pid_and_environment_are_not_wrapped(self):
        output=self.root/'identity.json'
        code="import json,os;open("+repr(str(output)) +",'w').write(json.dumps({'pid':os.getpid(),'secret':os.environ.get('PGPASSWORD')}))"
        launcher="import sys;sys.dont_write_bytecode=True;sys.path.insert(0,"+repr(str(ROOT/'ops/runtime'))+");import postgres_entrypoint as e;e._exec_filtered("+repr([os.environ['SHOP_PYTHON'],'-I','-c',code])+")"
        env=dict(os.environ,PGPASSWORD=CANARY)
        process=subprocess.Popen([os.environ['SHOP_PYTHON'],'-I','-c',launcher],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env)
        stdout,stderr=process.communicate(timeout=10)
        self.events(subprocess.CompletedProcess([],process.returncode,stdout,stderr))
        identity=json.loads(output.read_text());self.assertEqual(identity['pid'],process.pid);self.assertIsNone(identity['secret'])

    def test_read_failure_never_serializes_exception(self):
        with patch.object(entry.os,'read',side_effect=OSError(CANARY)),patch.object(entry.os,'write') as write:
            with self.assertRaises(OSError):entry.filter_stream(99,100)
            write.assert_not_called()

    def test_event_interface_rejects_arbitrary_content(self):
        with patch.object(entry.os,'write') as write:
            with self.assertRaises(ValueError):entry.emit(1,CANARY.encode())
            write.assert_not_called()

    def test_actual_postgresql_error_has_canary_in_control_but_not_filtered(self):
        data=self.root/'data';spool=self.root/'spool';data.mkdir(mode=0o700);spool.mkdir(mode=0o700)
        bootstrap.initialize_empty(data,spool,os.environ['SHOP_POSTGRES_BIN'],'c'*32)
        argv=[str(Path(os.environ['SHOP_POSTGRES_BIN'])/'postgres'),'--single','-D',str(data),'postgres']
        sql="SELECT '"+CANARY+"'::integer;\n"
        env={'PATH':os.defpath,'HOME':'/nonexistent','LANG':'C','LC_ALL':'C'}
        control=subprocess.run(argv,input=sql,capture_output=True,text=True,timeout=10,env=env)
        self.assertIn(CANARY,control.stdout+control.stderr)
        result=subprocess.run([os.environ['SHOP_PYTHON'],'-I',str(ROOT/'ops/runtime/postgres_entrypoint.py'),*argv],
            input=sql,capture_output=True,text=True,timeout=10,env=env)
        events=self.events(result);self.assertEqual(result.returncode,control.returncode)
        self.assertIn({'event':'postgres.diagnostic'},events)
        self.assertFalse((data/'postmaster.pid').exists())

    def test_public_entrypoint_rejects_other_program_without_echo(self):
        result=subprocess.run([os.environ['SHOP_PYTHON'],'-I',str(ROOT/'ops/runtime/postgres_entrypoint.py'),CANARY],
            capture_output=True,text=True,timeout=5)
        self.assertEqual(result.returncode,1)
        self.assertNotIn(CANARY,result.stdout+result.stderr)
        self.assertEqual(json.loads(result.stderr),{'event':'postgres.startup_failed'})
