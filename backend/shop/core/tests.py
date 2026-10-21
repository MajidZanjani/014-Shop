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


class SafeLoggingTests(SimpleTestCase):
    canaries = ('HOST_CANARY_SYNTHETIC', 'KEY_CANARY_SYNTHETIC', 'https://synthetic.invalid/bearer/CANARY',
                'TAX_BUSINESS_CANARY', 'postgresql://CANARY:CANARY@synthetic.invalid/shop')

    def test_formatter_drops_untrusted_fields_and_exception(self):
        import json
        import logging
        from shop.core.logging import SafeFormatter
        record = logging.LogRecord('synthetic', logging.ERROR, __file__, 1, ' '.join(self.canaries), (),
                                   (ValueError, ValueError(' '.join(self.canaries)), None))
        record.event = self.canaries[0]
        record.correlation_id = self.canaries[1]
        record.request = self.canaries[2]
        raw = SafeFormatter().format(record)
        self.assertEqual(json.loads(raw), {'event': 'runtime.event', 'status': None, 'correlation_id': None})
        for value in self.canaries:
            self.assertNotIn(value, raw)
        self.assertLess(len(raw), 128)
        record.event = ['untrusted']
        self.assertEqual(json.loads(SafeFormatter().format(record))['event'], 'runtime.event')

    def test_real_readiness_exception_path_is_safe(self):
        import io
        import json
        import logging
        from unittest.mock import patch
        from django.db import DatabaseError
        from django.test import RequestFactory
        from shop.core.health import readiness
        from shop.core.logging import SafeFormatter
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(SafeFormatter())
        logger = logging.getLogger('shop')
        logger.addHandler(handler)
        try:
            with patch('shop.core.health.connection') as synthetic_connection:
                synthetic_connection.cursor.side_effect = DatabaseError(' '.join(self.canaries))
                response = readiness(RequestFactory().get('/health/ready', HTTP_HOST='127.0.0.1'))
            self.assertEqual(response.status_code, 503)
            self.assertEqual(json.loads(response.content), {'status': 'unavailable'})
            data = json.loads(stream.getvalue())
            self.assertEqual(data['event'], 'health.ready')
            self.assertEqual(data['status'], 503)
            self.assertRegex(data['correlation_id'], '^[0-9a-f]{32}$')
            for value in self.canaries:
                self.assertNotIn(value, stream.getvalue() + response.content.decode())
        finally:
            logger.removeHandler(handler)

    def test_actual_django_security_log_is_redacted(self):
        import io
        import json
        import logging
        from shop.core.logging import SafeFormatter
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(SafeFormatter())
        root = logging.getLogger()
        root.addHandler(handler)
        try:
            response = self.client.get('/health/live', HTTP_HOST='HOST_CANARY_SYNTHETIC.invalid')
            self.assertEqual(response.status_code, 400)
            self.assertTrue(stream.getvalue())
            self.assertEqual(json.loads(stream.getvalue().splitlines()[0])['event'], 'runtime.event')
            self.assertNotIn('HOST_CANARY_SYNTHETIC', stream.getvalue() + response.content.decode())
        finally:
            root.removeHandler(handler)

    def test_startup_errors_do_not_echo_canaries(self):
        env = dict(os.environ, BANK_ENDPOINT=self.canaries[2])
        result = subprocess.run([sys.executable, '-c', 'import django; django.setup()'], env=env,
                                capture_output=True, text=True, timeout=8)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('startup rejected', result.stderr)
        for value in self.canaries:
            self.assertNotIn(value, result.stdout + result.stderr)


class UnqualifiedDatabaseTests(SimpleTestCase):
    def test_no_connection_or_cursor_before_attestation(self):
        from unittest.mock import patch
        from shop.db.unqualified.base import DatabaseWrapper
        for database in ('synthetic_decoy', None):
            connection = DatabaseWrapper({
                'ENGINE': 'shop.db.unqualified', 'NAME': database,
                'USER': 'synthetic', 'PASSWORD': 'SYNTHETIC_PRIVATE_CANARY',
                'HOST': 'synthetic.invalid', 'PORT': '5432',
                'OPTIONS': {}, 'AUTOCOMMIT': True, 'ATOMIC_REQUESTS': False,
                'CONN_MAX_AGE': 0, 'CONN_HEALTH_CHECKS': False,
                'TIME_ZONE': None, 'TEST': {},
            }, alias='unqualified')
            with patch('django.db.backends.postgresql.base.Database.connect') as connect:
                with self.assertRaisesMessage(ImproperlyConfigured,
                        'pending destination-guard integration') as error:
                    connection.ensure_connection()
                self.assertNotIn('SYNTHETIC_PRIVATE_CANARY', str(error.exception))
                self.assertIsNone(connection.connection)
                connect.assert_not_called()
                with self.assertRaises(ImproperlyConfigured):
                    connection.cursor()
                connect.assert_not_called()

    def test_both_production_modes_select_closed_backend(self):
        program = """
from unittest.mock import patch
with patch('shop.core.checks.runtime_secret_file', return_value='synthetic-only-' * 5):
    import shop.config.production as config
    assert config.DATABASES['default']['ENGINE'] == 'shop.db.unqualified'
"""
        for mode in ('production', 'bank-sandbox'):
            env = dict(os.environ, SHOP_ENV=mode, DATABASE_NAME='synthetic',
                       DATABASE_USER='synthetic', DATABASE_HOST='synthetic.invalid')
            result = subprocess.run([sys.executable, '-c', program], env=env,
                                    capture_output=True, text=True, timeout=8)
            self.assertEqual(result.returncode, 0, result.stderr)
