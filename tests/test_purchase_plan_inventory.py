"""Only GSD root-local execution state is outside the planning inventory."""
import importlib.util
import hashlib
import json
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

    def test_archive_rejects_changed_original_and_unrewritten_active_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);archive=root/'archive';archive.mkdir()
            raw=b'original evidence\n'
            original=archive/'STATE.md';original.write_bytes(raw)
            active=root/'STATE.md';active.write_text('SHB current scope\n')
            entry={'path':'STATE.md','bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
            (archive/'manifest.json').write_text(json.dumps({'source':plan.AMENDMENT,'revision':'1.1','files':[entry]}))
            self.assertEqual(plan.check_archive(root,archive),1)
            original.write_text('accidentally overwritten archive index\n')
            with self.assertRaisesRegex(AssertionError,'original evidence changed'):
                plan.check_archive(root,archive)
            original.write_bytes(raw);active.write_bytes(raw)
            with self.assertRaisesRegex(AssertionError,'old planning not rewritten'):
                plan.check_archive(root,archive)

    def test_archive_rejects_path_escape_and_duplicate_original(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);archive=root/'archive';archive.mkdir()
            entry={'path':'../outside','bytes':0,'sha256':hashlib.sha256(b'').hexdigest()}
            manifest={'source':plan.AMENDMENT,'revision':'1.1','files':[entry]}
            record=archive/'manifest.json';record.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(AssertionError,'path escape'):plan.check_archive(root,archive)
            manifest['files']=[entry,entry];record.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(AssertionError,'duplicate'):plan.check_archive(root,archive)


if __name__ == '__main__':
    unittest.main()
