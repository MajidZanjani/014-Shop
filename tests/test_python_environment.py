"""Behavioral rejection controls for locks and actual environment inventories."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location('check_python', Path(__file__).resolve().parents[1] / 'scripts/check_python.py')
checks = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checks)

class PythonEnvironmentTests(unittest.TestCase):
    def lock(self, text):
        with tempfile.TemporaryDirectory() as scratch:
            path = Path(scratch) / 'lock.txt'
            path.write_text(text)
            return checks.read_lock(path)

    def fixture(self):
        lock = {'pip': {'version': checks.PIP_VERSION, 'hashes': ['a' * 64]}}
        data = {'python': checks.PYTHON_VERSION, 'platform': 'linux', 'machine': 'x86_64',
                'isolated': True, 'user_site': False, 'distributions': {'pip': checks.PIP_VERSION}}
        return lock, data

    def test_complete_lock_and_inventory(self):
        self.assertEqual(self.lock('pip==26.2.1 --hash=sha256:' + 'a' * 64 + '\n')['pip']['version'], '26.2.1')
        expected, data = self.fixture()
        self.assertGreater(checks.validate_environment(data, expected, {'pip': checks.PIP_VERSION}), 0)

    def test_missing_hash(self):
        with self.assertRaisesRegex(checks.QualificationError, 'missing hash'):
            self.lock('pip==26.2.1\n')

    def test_empty_inventory(self):
        with self.assertRaisesRegex(checks.QualificationError, 'empty lock'):
            self.lock('# absent\n')
        expected, data = self.fixture(); data['distributions'] = {}
        with self.assertRaisesRegex(checks.QualificationError, 'empty installed'):
            checks.validate_environment(data, expected, {})

    def test_missing_installed_dependency(self):
        expected, data = self.fixture(); expected['missing'] = {'version': '1', 'hashes': ['a' * 64]}
        with self.assertRaisesRegex(checks.QualificationError, 'missing or unexpected'):
            checks.validate_environment(data, expected, {})

    def test_mismatched_interpreter_and_tool(self):
        expected, data = self.fixture(); data['python'] = '3.12.0'
        with self.assertRaisesRegex(checks.QualificationError, 'interpreter'):
            checks.validate_environment(data, expected, {})
        expected, data = self.fixture(); data['distributions']['pip'] = '0.0.0'
        with self.assertRaisesRegex(checks.QualificationError, 'identity mismatch'):
            checks.validate_environment(data, expected, {'pip': checks.PIP_VERSION})

    def test_global_environment_rejected(self):
        expected, data = self.fixture(); data['isolated'] = False
        with self.assertRaisesRegex(checks.QualificationError, 'exclude global'):
            checks.validate_environment(data, expected, {})

    def test_options_urls_and_duplicate_locks_rejected(self):
        for text in ['--index-url https://example.invalid', 'pip @ https://example.invalid/package.whl',
                     ('pip==26.2.1 --hash=sha256:' + 'a' * 64 + '\n') * 2]:
            with self.subTest(text=text), self.assertRaises(checks.QualificationError):
                self.lock(text)

if __name__ == '__main__':
    unittest.main()
