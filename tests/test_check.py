"""Behavioral gates for the native check dispatcher."""
import importlib.util
from pathlib import Path
import unittest
import contextlib
import io
import os
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("shop_check", ROOT / "scripts/check.py")
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)
sys.path.insert(0, str(ROOT / "scripts"))
from dev_postgres import Cluster, validate_root, isolated_postgres


class DispatcherTests(unittest.TestCase):
    def test_quick_requires_every_producer(self):
        self.assertEqual(check.required_lanes("quick"), (
            "environment", "frontend", "core", "worker", "adapters", "contracts", "boundaries"))

    def test_all_requires_every_final_lane(self):
        self.assertEqual(set(check.required_lanes("all")), set(check.LANES) - {"worker-smoke", "core-local", "contracts-local", "catalog"})

    def test_development_excludes_qualification(self):
        self.assertEqual(check.required_lanes('dev'),check.DEVELOPMENT)
        self.assertTrue({'core-local','worker-smoke','contracts-local','catalog'} <= set(check.DEVELOPMENT))
        self.assertFalse(set(check.DEVELOPMENT) & {'core','worker','contracts','deployment-boot','reproducibility','inventory'})

    def test_missing_producer_is_nonzero(self):
        with tempfile.TemporaryDirectory() as empty, patch.object(check, "ROOT", Path(empty)):
            with contextlib.redirect_stderr(io.StringIO()) as output:
                self.assertEqual(check.main(["quick"]), 1)
            self.assertIn("missing required producer", output.getvalue())

    def test_every_mode_rejects_missing_producer(self):
        with tempfile.TemporaryDirectory() as empty, patch.object(check, "ROOT", Path(empty)):
            for mode in (*check.LANES, "quick", "all", "dev"):
                with self.subTest(mode=mode), contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(check.main([mode]), 1)

    def test_worker_and_adapter_ownership(self):
        self.assertEqual(check.LANES["worker"][1], (("python3", "scripts/check_worker.py", "worker"),))
        self.assertEqual(check.LANES["adapters"][1], (("python3", "scripts/check_backend.py", "adapters"),))

    def test_producer_must_report_positive_counts(self):
        from subprocess import CompletedProcess
        with patch.object(Path, "is_file", return_value=True):
            with patch.object(check.subprocess, "run", return_value=CompletedProcess([], 0, "FRONTEND_PASS", "")):
                with contextlib.redirect_stdout(io.StringIO()), self.assertRaisesRegex(RuntimeError, "zero"):
                    check.execute("frontend")

    def test_producer_must_report_expected_marker(self):
        from subprocess import CompletedProcess
        with patch.object(Path, "is_file", return_value=True):
            with patch.object(check.subprocess, "run", return_value=CompletedProcess([], 0, "tests=1", "")):
                with contextlib.redirect_stdout(io.StringIO()), self.assertRaisesRegex(RuntimeError, "marker"):
                    check.execute("frontend")

    def test_no_database_tools_is_nonzero(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "SHOP_POSTGRES_BIN"):
                with isolated_postgres():
                    self.fail("missing database must never yield")

    def test_unexpected_database_provenance_rejected(self):
        for path in ("/tmp", "/nix/store/../../tmp"):
            with self.subTest(path=path), patch.dict(os.environ, {"SHOP_POSTGRES_BIN": path}, clear=True):
                with self.assertRaisesRegex(RuntimeError, "provenance"):
                    with isolated_postgres():
                        self.fail("untrusted database must never start")

    def test_zero_checks_rejected(self):
        for output in ("", "OK", "tests=0 checks=0"):
            with self.assertRaisesRegex(RuntimeError, "zero"):
                check.positive_counts(output)
        self.assertEqual(check.positive_counts("checks=3 tests=2"), (2, 3))

    def test_failures_and_skips_rejected(self):
        for output in ("tests=4 failures=1", "Ran 3 tests skipped=1"):
            with self.assertRaises(RuntimeError):
                check.positive_counts(output)

    def test_unsafe_cleanup_rejected(self):
        with tempfile.TemporaryDirectory(prefix="shop-pg-", dir="/tmp") as directory:
            root = Path(directory)
            (root / "owned").write_text("expected")
            self.assertEqual(validate_root(root, "expected"), root)
            with self.assertRaises(ValueError):
                validate_root(root, "wrong")
            (root / "owned").unlink()
            (root / "owned").symlink_to(root / "absent")
            with self.assertRaises(ValueError):
                validate_root(root, "expected")
            (root / "owned").unlink()
            (root / "owned").write_text("expected")
            (root / "data").symlink_to(root.parent)
            with self.assertRaises(ValueError):
                validate_root(root, "expected")

    def test_libpq_configuration_is_scratch_only(self):
        with tempfile.TemporaryDirectory(prefix="shop-pg-", dir="/tmp") as directory:
            root = Path(directory)
            (root / "owned").write_text("token")
            pg = Cluster(root, "token", Path("/unexecuted"), [])
            with patch.dict(os.environ, {"PGHOST": "outside.invalid", "PGPASSFILE": "/unread"}):
                with patch("dev_postgres.run") as run:
                    pg.command("psql", "--version")
                    env = run.call_args.kwargs["env"]
                    self.assertNotIn("PGHOST", env)
                    self.assertEqual(env["HOME"], str(root))
                    self.assertEqual(env["PGPASSFILE"], str(root / "absent.pgpass"))

    def test_owned_subprocess_timeout_is_bounded(self):
        import subprocess
        import time
        from dev_postgres import run
        started = time.monotonic()
        with self.assertRaises(subprocess.TimeoutExpired):
            run([sys.executable, "-c", "import time; time.sleep(60)"], timeout=0.05)
        self.assertLess(time.monotonic() - started, 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
