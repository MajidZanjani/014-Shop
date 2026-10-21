from pathlib import Path
import subprocess
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from check_locks import reject


class DiagnosticControls(unittest.TestCase):
    def test_wrong_network_error_cannot_pass(self):
        for text in ('ENOTCACHED','ENETUNREACH','No matching distribution found','unrelated error'):
            with self.assertRaises(ValueError):reject(subprocess.CompletedProcess([],1,'',text),['EINTEGRITY'])
        with self.assertRaises(ValueError):reject(subprocess.CompletedProcess([],0,'','EINTEGRITY'),['EINTEGRITY'])
    def test_expected_hash_diagnostic(self):reject(subprocess.CompletedProcess([],1,'','EINTEGRITY synthetic'),['EINTEGRITY'])
