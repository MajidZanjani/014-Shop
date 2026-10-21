"""Synthetic configuration controls; no production files or provider requests."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, override_settings
from shop.core.checks import runtime_secret_file, safe_runtime_checks, validate_environment


class ConfigurationTests(SimpleTestCase):
    def startup(self, patch, settings='shop.config.synthetic'):
        env = dict(os.environ, DJANGO_SETTINGS_MODULE=settings)
        for key, value in patch.items():
            if value is None:
                env.pop(key, None)
            else:
                env[key] = value
        return subprocess.run([sys.executable, '-c', 'import django; django.setup()'],
            env=env, capture_output=True, text=True, timeout=8)

    def test_actual_valid_startup(self):
        for mode in ('synthetic', 'local'):
            with self.subTest(mode=mode):
                self.assertEqual(self.startup({'SHOP_ENV': mode}, 'shop.config.' + mode).returncode, 0)

    def test_actual_invalid_startup(self):
        cases = [{'SHOP_ENV': None}, {'SHOP_ENV': 'unknown'}, {'SHOP_ENV': 'production'},
                 {'LIVE_PAYMENTS_ENABLED': None}, {'LIVE_PAYMENTS_ENABLED': 'true'}, {'DEBUG': 'true'},
                 {'PAYMENT_ADAPTER': 'live'}, {'MAIL_ADAPTER': 'smtp'}, {'STORAGE_ADAPTER': 's3'},
                 {'BANK_ENDPOINT': 'https://synthetic.invalid'}, {'SECRET_KEY': 'CANARY_INLINE_SECRET'}]
        for case in cases:
            with self.subTest(case=list(case)):
                result = self.startup(case)
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn('CANARY_INLINE_SECRET', result.stdout + result.stderr)

    def test_production_modes_need_runtime_files(self):
        for mode in ('production', 'bank-sandbox'):
            for path in (None, 'relative', '/tmp/synthetic-secret-not-allowed'):
                with self.subTest(mode=mode, path=path):
                    result = self.startup({'SHOP_ENV': mode, 'SECRET_KEY_FILE': path}, 'shop.config.production')
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn('Required runtime secret', result.stderr)

    def test_bounded_runtime_secret(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            secret = root / 'synthetic'
            secret.write_text('SYNTHETIC_CANARY_' * 4)
            secret.chmod(0o600)
            self.assertEqual(runtime_secret_file(str(secret), allowed_root=root), 'SYNTHETIC_CANARY_' * 4)
            for mode in (0o644, 0o777):
                secret.chmod(mode)
                with self.assertRaises(ImproperlyConfigured):
                    runtime_secret_file(str(secret), allowed_root=root)
            secret.chmod(0o600)
            alias = root / 'alias'
            alias.symlink_to(secret)
            with self.assertRaises(ImproperlyConfigured):
                runtime_secret_file(str(alias), allowed_root=root)
            secret.write_text('x' * 4097)
            with self.assertRaises(ImproperlyConfigured):
                runtime_secret_file(str(secret), allowed_root=root)

    def test_registered_configuration_checks(self):
        self.assertEqual(safe_runtime_checks(None), [])
        for patch in ({'DEBUG': True}, {'LIVE_PAYMENTS_ENABLED': True}, {'PAYMENT_ADAPTER': 'live'},
                      {'ALLOWED_HOSTS': ['*']}, {'SHOP_ENV': 'unknown'}):
            with self.subTest(patch=patch), override_settings(**patch):
                self.assertTrue(safe_runtime_checks(None))

    def test_templates_are_nonsecret_and_fail_closed(self):
        root = Path(__file__).resolve().parents[3]
        for mode in ('production', 'bank-sandbox'):
            values = dict(line.split('=', 1) for line in (root / 'ops/config' / (mode + '.example')).read_text().splitlines()
                          if line and not line.startswith('#'))
            self.assertEqual(validate_environment(values), mode)
            self.assertEqual(values['LIVE_PAYMENTS_ENABLED'], 'false')
            self.assertTrue(values['SECRET_KEY_FILE'].startswith('/run/secrets/shop/'))
