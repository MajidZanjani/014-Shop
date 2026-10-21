"""Actual fake adapters under network isolation; only owned Unix PostgreSQL transport."""
import os
from pathlib import Path
import socket
import tempfile
import uuid
from unittest.mock import patch
from django.test import TransactionTestCase, override_settings
from shop.worker.models import FakeReceipt, Probe
from shop.worker.services import execute_once
from .capture_mail import CaptureMail
from .fake_bank import perform_fake_probe
from .local_storage import LocalStorage
from .ports import MailRequest, ProbeRequest


class AdapterTests(TransactionTestCase):
    def setUp(self):
        self.assertEqual(os.environ.get('SHOP_ADAPTER_NETWORK_ISOLATED'), '1')

    def test_active_network_namespace_blocks_ip(self):
        with socket.socket() as client:
            client.settimeout(1)
            with self.assertRaises(OSError): client.connect(('192.0.2.1', 443))

    def test_actual_adapters_never_request_network(self):
        def denied(*args, **kwargs):
            raise AssertionError('Synthetic outbound denied')
        with patch('socket.create_connection', side_effect=denied), patch('socket.getaddrinfo', side_effect=denied):
            # Guard controls execute attempted HTTP/SMTP/object/DNS entry points.
            import urllib.request, smtplib
            for attempt in (lambda: urllib.request.urlopen('https://synthetic.invalid', timeout=1),
                            lambda: smtplib.SMTP('synthetic.invalid', timeout=1),
                            lambda: socket.create_connection(('synthetic.invalid', 443)),
                            lambda: socket.getaddrinfo('synthetic.invalid', 443)):
                with self.assertRaises(AssertionError): attempt()
            probe = Probe.objects.create()
            self.assertTrue(execute_once())
            probe.refresh_from_db()
            self.assertEqual(probe.state, 'complete')
            self.assertEqual(FakeReceipt.objects.count(), 1)

    def test_deterministic_fake_scenarios(self):
        for scenario in ('ok', 'rejected', 'unknown'):
            request = ProbeRequest(uuid.uuid4(), scenario)
            result = perform_fake_probe(request)
            self.assertEqual(perform_fake_probe(request), result)
            self.assertEqual(result.outcome, 'synthetic-' + scenario)
        for scenario, exception in (('timeout', TimeoutError), ('malformed', ValueError), ('unimplemented', ValueError)):
            with self.assertRaises(exception): perform_fake_probe(ProbeRequest(uuid.uuid4(), scenario))
        self.assertEqual(FakeReceipt.objects.count(), 3)

    def test_capture_mail_is_bounded_and_resettable(self):
        capture = CaptureMail()
        request = MailRequest(uuid.uuid4(), 'probe@synthetic.invalid', b'synthetic')
        self.assertEqual(capture.send(request), capture.send(request))
        self.assertEqual(len(capture.messages), 1)
        for address in ('real@example.com', 'a@synthetic.invalid\r\nBcc: x', 'https://synthetic.invalid'):
            with self.assertRaises(ValueError): capture.send(MailRequest(uuid.uuid4(), address, b'synthetic'))
        with self.assertRaises(ValueError): capture.send(MailRequest(uuid.uuid4(), 'probe@synthetic.invalid', b'x' * 4097))
        capture.reset(); self.assertFalse(capture.messages)

    def test_storage_roundtrip_escape_and_reset(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            with LocalStorage(root) as storage:
                key = storage.put(b'synthetic')
                self.assertRegex(key, '^[0-9a-f]{32}$')
                self.assertEqual(storage.get(key), b'synthetic')
                for invalid in ('../escape', '/etc/passwd', 'x', key + '/child'):
                    with self.assertRaises(ValueError): storage.get(invalid)
                alias = uuid.uuid4().hex
                (root / alias).symlink_to(root / key)
                with self.assertRaises(OSError): storage.get(alias)
                for body in (b'', b'x' * 1048577, 'not-bytes'):
                    with self.assertRaises(ValueError): storage.put(body)
                storage.reset(); self.assertFalse((root / key).exists())
                self.assertTrue((root / alias).is_symlink())
            linked = root / 'linked'; linked.symlink_to(root, target_is_directory=True)
            with self.assertRaises(ValueError): LocalStorage(linked)

    def test_live_modes_and_conflicting_identity_rejected(self):
        request = ProbeRequest(uuid.uuid4())
        perform_fake_probe(request)
        with self.assertRaises(ValueError): perform_fake_probe(ProbeRequest(request.effect_id, 'rejected'))
        with override_settings(SHOP_ENV='production'):
            with self.assertRaises(ValueError): perform_fake_probe(request)
            with tempfile.TemporaryDirectory() as directory:
                with self.assertRaises(ValueError): LocalStorage(Path(directory).resolve())
            with self.assertRaises(ValueError): CaptureMail().send(MailRequest(uuid.uuid4(), 'probe@synthetic.invalid', b'synthetic'))
