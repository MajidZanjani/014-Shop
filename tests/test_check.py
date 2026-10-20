"""Behavioral gates for the native check dispatcher."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("shop_check", ROOT / "scripts/check.py")
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)


class DispatcherTests(unittest.TestCase):
    def test_quick_requires_every_producer(self):
        self.assertEqual(check.required_lanes("quick"), (
            "environment", "frontend", "core", "worker", "adapters", "contracts", "boundaries"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
