"""Actual built launcher process controls and metadata rejection cases."""
import importlib.util
import json
import os
from pathlib import Path
import secrets
import subprocess
import tempfile
import unittest
SPEC=importlib.util.spec_from_file_location('check_operator_runtime',Path(__file__).resolve().parents[1]/'scripts/check_operator_runtime.py')
checks=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(checks)


class OperatorRuntimeTests(unittest.TestCase):
    def metadata(self):
        prefix='/nix/store/'+'a'*32+'-synthetic'
        value={key:prefix for key in checks.FIELDS}
        value.update(package=prefix,executable=prefix+'/bin/shop-operator-inspect',
            python=prefix+'/bin/python3',libpq=prefix+'/lib/libpq.so.5',libc=prefix+'/lib/libc.so.6',
            pythonVersion='3.13.16',psycopgVersion='3.3.6',libpqVersion=180006,
            readOnly=True,installed=False,runtimeQualified=False,productionActivation=False)
        return value

    def run_command(self,args,*,failure=False,env=None,stdin=None):
        key='SHOP_OPERATOR_FAILURE_EXECUTABLE' if failure else 'SHOP_OPERATOR_EXECUTABLE'
        executable=os.environ[key]
        self.assertTrue(executable.startswith('/nix/store/'))
        return subprocess.run([executable,*args],env={} if env is None else env,
            stdin=subprocess.DEVNULL if stdin is None else stdin,capture_output=True,timeout=8)

    def test_closed_unqualified_runtime_metadata(self):
        self.assertEqual(checks.validate_metadata(self.metadata()),self.metadata())

    def test_installed_qualified_or_write_claim_denied(self):
        for key,value in (('installed',True),('runtimeQualified',True),('productionActivation',True),('readOnly',False)):
            with self.subTest(key=key),self.assertRaises(ValueError):
                checks.validate_metadata(dict(self.metadata(),**{key:value}))

    def test_different_native_or_python_dependency_pin_denied(self):
        for patch in ({'pythonVersion':'3.12.0'},{'psycopgVersion':'0'},{'libpqVersion':True},{'libpqVersion':170000}):
            with self.assertRaises(ValueError):checks.validate_metadata(dict(self.metadata(),**patch))

    def test_unexpected_path_or_metadata_denied(self):
        for patch in ({'extra':True},{'python':'/usr/bin/python3'},{'executable':'/tmp/other'},
                      {'driver':'/nix/store/../tmp/other'}):
            with self.assertRaises(ValueError):checks.validate_metadata(dict(self.metadata(),**patch))

    def test_actual_launcher_help_ignores_environment_and_shadow_module(self):
        parent=Path(os.environ.get('SHOP_TEST_SCRATCH',checks.ROOT/'.scratch'))
        with tempfile.TemporaryDirectory(prefix='operator-shadow-',dir=parent) as directory:
            (Path(directory)/'operator_inspect.py').write_text('raise RuntimeError("unexpected shadow import")')
            result=self.run_command(['--help'],env={'PATH':'/nonexistent','HOME':directory,
                'PYTHONPATH':directory,'PYTHONHOME':directory,'PGHOST':'synthetic.invalid',
                'PGPASSWORD':'synthetic-'+secrets.token_hex(16),'LD_LIBRARY_PATH':'/nonexistent'})
            self.assertEqual(result.returncode,0)
            self.assertEqual(result.stdout,checks.HELP)
            self.assertEqual(result.stderr,b'')

    def test_actual_launcher_denies_mutation_or_secret_option_without_echo(self):
        canary='synthetic-'+secrets.token_hex(16)
        for args in (['apply'],['bootstrap'],['--password',canary]):
            result=self.run_command(args)
            self.assertEqual(result.returncode,2)
            self.assertEqual(result.stdout,b'')
            self.assertEqual(result.stderr,checks.ERROR)
            self.assertNotIn(canary.encode(),result.stdout+result.stderr)

    def test_actual_launcher_inspect_has_no_fallback_without_private_input(self):
        # /dev/null FD0 is not a private regular artifact; even a nonroot caller
        # cannot reach probing/credential use/connect through this negative case.
        result=self.run_command(['inspect'])
        self.assertEqual(result.returncode,1)
        self.assertEqual(result.stdout,b'')
        self.assertEqual(result.stderr,checks.ERROR)

    def test_actual_synthetic_import_failure_is_fixed_denial_without_traceback(self):
        result=self.run_command(['--help'],failure=True)
        self.assertEqual(result.returncode,1)
        self.assertEqual(result.stdout,b'')
        self.assertEqual(result.stderr,checks.ERROR)
        self.assertNotIn(b'synthetic startup detail',result.stderr)


    def test_actual_candidate_validation_reads_private_fd_and_never_grants_publication(self):
        from test_process_probe import candidate_bundle
        parent=Path(os.environ.get('SHOP_TEST_SCRATCH',checks.ROOT/'.scratch'))
        with tempfile.TemporaryFile(dir=parent) as file:
            file.write(json.dumps(candidate_bundle()).encode());file.flush();os.fchmod(file.fileno(),0o600)
            result=self.run_command(['validate-records'],stdin=file)
        self.assertEqual(result.returncode,0)
        self.assertEqual(result.stderr,b'')
        report=json.loads(result.stdout)
        self.assertEqual(report['status'],'candidate_validated')
        self.assertEqual(report['evidence_class'],'unverified-candidate')
        self.assertIs(report['publication_authorized'],False)
        self.assertIs(report['retry_authorized'],False)
        self.assertIs(report['reopening_authorized'],False)
        self.assertNotIn(b'synthetic_shop',result.stdout)

    def test_actual_candidate_mixed_record_denies_without_private_echo(self):
        from test_process_probe import candidate_bundle
        candidate=candidate_bundle()
        candidate['records']['operator-connection.json']['database']['role']='private_mixed_decoy'
        parent=Path(os.environ.get('SHOP_TEST_SCRATCH',checks.ROOT/'.scratch'))
        with tempfile.TemporaryFile(dir=parent) as file:
            file.write(json.dumps(candidate).encode());file.flush();os.fchmod(file.fileno(),0o600)
            result=self.run_command(['validate-records'],stdin=file)
        self.assertEqual(result.returncode,1)
        self.assertEqual(result.stdout,b'')
        self.assertEqual(result.stderr,checks.ERROR)
        self.assertNotIn(b'private_mixed_decoy',result.stderr)
