import io
from pathlib import Path
import sys
import unittest
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from check_frontend import CANARIES,scan_bytes
from check_boundaries import child_counts


class BoundaryCompositionTests(unittest.TestCase):
    def test_canary_control_clean_and_leaks(self):
        scan_bytes('clean.js',b'console.log("synthetic")')
        for canary in CANARIES:
            with self.assertRaises(ValueError):scan_bytes('synthetic.map',canary)

    def test_archive_leak_rejection(self):
        stream=io.BytesIO()
        with zipfile.ZipFile(stream,'w') as output:output.writestr('synthetic.txt',CANARIES[0])
        with self.assertRaises(ValueError):scan_bytes('disguised.bin',stream.getvalue())

    def test_missing_zero_failed_producers_rejected(self):
        for text in ('', 'FRONTEND_PASS checks=0 tests=0','FRONTEND_PASS failures=1 tests=1'):
            with self.assertRaises((ValueError,RuntimeError)):child_counts(text,'FRONTEND_PASS')
        self.assertEqual(child_counts('FRONTEND_PASS checks=1 tests=1','FRONTEND_PASS'),(1,1))
