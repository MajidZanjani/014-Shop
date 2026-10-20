"""Offline dependency packet contract controls; never install artifacts."""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ReviewTests(unittest.TestCase):
    def qualifier(self):
        path = ROOT / "scripts/qualify_dependencies.py"
        self.assertTrue(path.is_file(), "dependency qualifier must exist")
        spec = importlib.util.spec_from_file_location("qualifier", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_exact_artifact_contract(self):
        q = self.qualifier()
        row = q.fixture()
        self.assertEqual(q.validate_artifact(row), 1)
        for field, value in (("sha256", ""), ("upstream", "https://github.com/evil/astro"),
                             ("licence_evidence", []), ("hooks", None)):
            bad = copy.deepcopy(row)
            bad[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                q.validate_artifact(bad)

    def test_empty_and_changed_packets_rejected(self):
        q = self.qualifier()
        with self.assertRaises(ValueError):
            q.validate_packet({"artifacts": []}, [])
        packet = q.packet([q.fixture()])
        self.assertEqual(q.validate_packet(packet, [q.fixture()]), 1)
        packet["artifacts"][0]["sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            q.validate_packet(packet, [q.fixture()])

    def test_declared_ranges(self):
        q = self.qualifier()
        self.assertTrue(q.satisfies("6.0.3", "^5.0.0 || ^6.0.0"))
        self.assertFalse(q.satisfies("7.0.2", "^5.0.0 || ^6.0.0"))
        self.assertTrue(q.satisfies("3.13.13", ">=3.10"))
        self.assertFalse(q.satisfies("3.9.0", ">=3.10"))
        with self.assertRaises(ValueError):
            q.satisfies("3.13.13", "unknown syntax")

    def test_graph_rejects_incompatible_peer_and_interpreter(self):
        q = self.qualifier()
        rows = [q.fixture(), dict(q.fixture(), name="typescript", version="7.0.2",
                                 peers={}, engines={})]
        rows[0]["peers"] = {"typescript": "^5.0.0 || ^6.0.0"}
        with self.assertRaises(ValueError):
            q.validate_graph(rows, {"node": "24.21.0", "python": "3.13.13"})
        rows[0]["peers"] = {}
        rows[0]["requires_python"] = ">=3.14"
        with self.assertRaises(ValueError):
            q.validate_graph(rows, {"node": "24.21.0", "python": "3.13.13"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
