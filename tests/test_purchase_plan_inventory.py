"""Only GSD root-local execution state is outside the planning inventory."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('purchase_plan', ROOT / 'scripts/check_purchase_plan.py')
plan = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plan)


class PlanningInventoryTests(unittest.TestCase):
    def test_root_execution_lock_excluded_with_and_without_local_state(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'phases').mkdir()
            for name in ('STATE.md', 'phases/08-PLAN.md', 'phases/milestone.lock',
                         'PURCHASE-FLOW-RECONCILIATION.json'):
                (root / name).write_text('retained')
            with patch.object(plan, 'P', root):
                expected = {'STATE.md', 'phases/08-PLAN.md', 'phases/milestone.lock'}
                paths = lambda: {p.relative_to(root).as_posix() for p in plan.planning_artifacts()}
                self.assertEqual(paths(), expected)
                (root / 'milestone.lock').write_text('local execution state')
                self.assertEqual(paths(), expected)
                (root / 'STATE.md').unlink()
                self.assertNotEqual(paths(), expected)


if __name__ == '__main__':
    unittest.main()
