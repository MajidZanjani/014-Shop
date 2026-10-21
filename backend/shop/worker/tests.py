"""Real independent-session ownership tests; off-host process fault separately tagged."""
from datetime import timedelta
import os
import queue
import subprocess
import sys
import threading
from django.db import connection, connections, transaction
from django.db.models.functions import Now
from django.test import TransactionTestCase, tag
from shop.adapters.fake_bank import perform_fake_probe
from shop.adapters.ports import ProbeRequest, ProbeResult
from .models import FakeReceipt, Probe
from .services import claim_probe, complete_probe


class OwnershipTests(TransactionTestCase):
    def setUp(self):
        self.assertEqual(connection.vendor, 'postgresql')
        self.probe = Probe.objects.create()

    def test_simultaneous_independent_claimants(self):
        barrier = threading.Barrier(2, timeout=5)
        values = queue.Queue()
        def claimant():
            try:
                conn = connections['default']
                with conn.cursor() as cursor:
                    cursor.execute('SELECT pg_backend_pid()')
                    pid = cursor.fetchone()[0]
                barrier.wait()
                values.put((pid, claim_probe()))
            except BaseException as error:
                values.put(error)
            finally:
                connections.close_all()
        threads = [threading.Thread(target=claimant, daemon=True) for _ in range(2)]
        for thread in threads: thread.start()
        for thread in threads:
            thread.join(7)
            self.assertFalse(thread.is_alive(), 'bounded claimant wait expired')
        rows = [values.get_nowait(), values.get_nowait()]
        for row in rows:
            if isinstance(row, BaseException): raise row
        self.assertNotEqual(rows[0][0], rows[1][0])
        self.assertEqual(sum(claim is not None for pid, claim in rows), 1)
        self.probe.refresh_from_db()
        self.assertEqual(self.probe.attempts, 1)

    def test_expiry_takeover_fences_old_token(self):
        old = claim_probe()
        Probe.objects.filter(pk=self.probe.pk).update(lease_until=Now() - timedelta(seconds=1))
        new = claim_probe()
        self.assertNotEqual(old.token, new.token)
        self.assertEqual(old.effect_id, new.effect_id)
        result = perform_fake_probe(ProbeRequest(old.effect_id))
        self.assertFalse(complete_probe(old, result))
        self.assertTrue(complete_probe(new, result))
        self.assertFalse(complete_probe(new, result))
        self.assertEqual(FakeReceipt.objects.count(), 1)

    def test_claim_rejects_outer_transaction(self):
        with transaction.atomic():
            with self.assertRaises(ValueError): claim_probe()

    def test_claim_rejects_autocommit_disabled(self):
        connection.set_autocommit(False)
        try:
            with self.assertRaises(ValueError): claim_probe()
        finally:
            connection.rollback()
            connection.set_autocommit(True)

    def test_claim_commits_before_adapter_wait(self):
        from unittest.mock import patch
        from .services import execute_once
        entered, release = threading.Event(), threading.Event()
        outcomes = queue.Queue()
        def blocked_fake(request):
            with connection.cursor() as cursor:
                cursor.execute('SELECT pg_backend_pid()')
                outcomes.put(cursor.fetchone()[0])
            entered.set()
            if not release.wait(5):
                raise RuntimeError('bounded fake wait expired')
            return perform_fake_probe(request)
        def execute():
            try:
                execute_once()
            except BaseException as error:
                outcomes.put(error)
            finally:
                connections.close_all()
        with patch('shop.worker.services.perform_fake_probe', side_effect=blocked_fake):
            thread = threading.Thread(target=execute, daemon=True)
            thread.start()
            try:
                self.assertTrue(entered.wait(5), 'fake was not entered')
                pid = outcomes.get_nowait()
                with transaction.atomic(), connection.cursor() as cursor:
                    cursor.execute("SET LOCAL lock_timeout = '1000ms'")
                    cursor.execute('SELECT pg_backend_pid()')
                    self.assertNotEqual(pid, cursor.fetchone()[0])
                    Probe.objects.select_for_update(nowait=True).get(pk=self.probe.pk)
            finally:
                release.set()
                thread.join(7)
            self.assertFalse(thread.is_alive())
        if not outcomes.empty():
            raise outcomes.get_nowait()
        self.probe.refresh_from_db()
        self.assertEqual(self.probe.state, 'complete')

    def test_finite_attempts_and_expired_completion(self):
        claim = claim_probe(max_attempts=1)
        Probe.objects.filter(pk=self.probe.pk).update(lease_until=Now() - timedelta(seconds=1))
        self.assertFalse(complete_probe(claim, ProbeResult(claim.effect_id, 'synthetic-ok')))
        self.assertIsNone(claim_probe(max_attempts=1))
        self.probe.refresh_from_db()
        self.assertEqual(self.probe.state, 'failed')
        self.assertIsNone(self.probe.claim_token)

    def test_stable_fake_receipt_and_identity_rejection(self):
        claim = claim_probe()
        request = ProbeRequest(claim.effect_id)
        result = perform_fake_probe(request)
        self.assertEqual(perform_fake_probe(request), result)
        self.assertEqual(FakeReceipt.objects.count(), 1)
        with self.assertRaises(ValueError): complete_probe(claim, ProbeResult(self.probe.pk, 'wrong'))
        with transaction.atomic():
            with self.assertRaises(ValueError): perform_fake_probe(request)


@tag('offhost')
class OffhostInterruptionTests(TransactionTestCase):
    def test_receipt_before_completion_process_interruption(self):
        self.assertEqual(os.environ.get('SHOP_OFFHOST_WORKER_AUTHORIZED'), '1', 'off-host authorization required')
        probe = Probe.objects.create()
        code = '''import os,django; django.setup()
from shop.worker.services import claim_probe
from shop.adapters.fake_bank import perform_fake_probe
from shop.adapters.ports import ProbeRequest
claim=claim_probe(); perform_fake_probe(ProbeRequest(claim.effect_id)); os._exit(17)
'''
        # This code is prepared only: executed solely by the separately authorized full lane.
        env = dict(os.environ, DATABASE_NAME=connection.settings_dict['NAME'])
        child = subprocess.run([sys.executable, '-c', code], env=env, timeout=15)
        self.assertEqual(child.returncode, 17)
        self.assertEqual(FakeReceipt.objects.filter(effect_id=probe.effect_id).count(), 1)
        Probe.objects.filter(pk=probe.pk).update(lease_until=Now() - timedelta(seconds=1))
        new = claim_probe()
        result = perform_fake_probe(ProbeRequest(new.effect_id))
        self.assertTrue(complete_probe(new, result))
        self.assertEqual(FakeReceipt.objects.count(), 1)
