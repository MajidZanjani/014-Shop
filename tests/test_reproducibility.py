from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from check_reproducibility import payload_manifest,compare


class PayloadTests(unittest.TestCase):
    def test_actual_changed_byte_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);path=root/'synthetic';path.write_bytes(b'one')
            first=payload_manifest(root);path.write_bytes(b'two')
            with self.assertRaises(ValueError):compare(first,payload_manifest(root))
    def test_empty_and_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            with self.assertRaises(ValueError):payload_manifest(root)
            (root/'link').symlink_to('synthetic')
            with self.assertRaises(ValueError):payload_manifest(root)
    def test_positive_exact_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'synthetic').write_bytes(b'synthetic')
            self.assertTrue(compare(payload_manifest(root),payload_manifest(root)))

    def test_canonical_target_owns_and_cleans_only_new_directory(self):
        from unittest.mock import patch
        from check_reproducibility import canonical_build_root
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)/'new-target'
            with patch('check_reproducibility.CANONICAL_BUILD_PATH',target):
                with canonical_build_root() as owned:
                    self.assertEqual(owned,target)
                    self.assertTrue((owned/'.owned').is_file())
                self.assertFalse(target.exists())

    def test_existing_canonical_target_is_not_reused(self):
        from unittest.mock import patch
        from check_reproducibility import canonical_build_root
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory);(target/'existing').write_text('protected-fixture')
            with patch('check_reproducibility.CANONICAL_BUILD_PATH',target):
                with self.assertRaises(FileExistsError):
                    with canonical_build_root():self.fail('existing directory reused')
            self.assertEqual((target/'existing').read_text(),'protected-fixture')
