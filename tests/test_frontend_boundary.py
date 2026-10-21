"""Actual source-policy/build/output mutations, using synthetic private values only."""
import importlib.util
import io
import json
import os
from pathlib import Path
import unittest
import zipfile

spec = importlib.util.spec_from_file_location('check_frontend', Path(__file__).resolve().parents[1] / 'scripts/check_frontend.py')
checks = importlib.util.module_from_spec(spec); spec.loader.exec_module(checks)

class FrontendBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(os.environ['SHOP_FRONTEND_TEST_ROOT'])
        self.env = json.loads(os.environ['SHOP_FRONTEND_TEST_ENV'])

    def test_clean_real_output(self):
        inventory, count = checks.scan_output(self.root / 'dist')
        self.assertGreater(len(inventory), 1); self.assertGreater(count, 0)

    def test_private_import_and_runtime_routes(self):
        path = self.root / 'src/pages/index.astro'; original = path.read_text()
        bad_sources = [original.replace('---\n', '---\nimport "../../private/synthetic-only.txt";\n', 1),
                       original.replace('---\n', '---\nexport const prerender = false;\n', 1),
                       original.replace('<main>', '<main server:defer>'),
                       original.replace('---\n', '---\nimport { getLiveCollection } from "astro:content";\n', 1),
                       original.replace('---\n', '---\nimport { actions } from "astro:actions";\n', 1)]
        try:
            for source in bad_sources:
                path.write_text(source)
                with self.subTest(source=source[:90]), self.assertRaises(checks.BoundaryError):
                    checks.source_policy(self.root, self.env)
        finally: path.write_text(original)

    def test_private_public_asset_copy(self):
        public = self.root / 'public'; public.mkdir(exist_ok=True)
        path = public / 'leak.txt'; path.write_bytes(checks.CANARIES[0])
        try:
            checks.command(['unshare', '--net', '--', 'npm', 'run', 'build'], self.root, self.env)
            with self.assertRaisesRegex(checks.BoundaryError, 'canary leaked'):
                checks.scan_output(self.root / 'dist')
        finally:
            path.unlink(); (self.root / 'dist/leak.txt').unlink(missing_ok=True)

    def test_source_maps_and_archives_scanned(self):
        for name in ['chunk.js.map', 'private.txt']:
            with self.subTest(name=name), self.assertRaisesRegex(checks.BoundaryError, 'canary leaked'):
                checks.scan_bytes(name, checks.CANARIES[1])
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('nested/map.json', checks.CANARIES[2])
        with self.assertRaisesRegex(checks.BoundaryError, 'canary leaked'):
            checks.scan_bytes('disguised.bin', buffer.getvalue())

    def test_private_path_and_symlink_not_copied(self):
        value = json.loads((self.root / 'build-inputs.json').read_text())
        value['files'].append('../private/synthetic-only.txt')
        with self.assertRaisesRegex(checks.BoundaryError, 'private/unsafe'):
            checks.manifest(value)
        symlink = self.root / 'src/leak.ts'; symlink.symlink_to(self.root.parent / 'private/synthetic-only.txt')
        target = self.root.parent / 'bad-context'
        try:
            with self.assertRaisesRegex(checks.BoundaryError, 'symlink'):
                checks.copy_inputs(self.root, target, ['src/leak.ts'])
        finally: symlink.unlink()

    def test_missing_empty_output_and_unknown_manifest(self):
        with self.assertRaisesRegex(checks.BoundaryError, 'missing static'):
            checks.scan_output(self.root / 'absent')
        value = json.loads((self.root / 'build-inputs.json').read_text()); value['files'] = []
        with self.assertRaises(checks.BoundaryError): checks.manifest(value)
        value['secret_source'] = '.env'
        with self.assertRaises(checks.BoundaryError): checks.manifest(value)
