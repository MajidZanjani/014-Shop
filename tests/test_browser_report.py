"""Browser evidence cannot promote diagnostics or omit qualification boundaries."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from check_browser_access import validate_result


def report():
    return {'status':'BROWSER_LOCAL_PASS','checks':54,'modes':2,'roles':2,'browser_version':'155.0.8059.84',
            'node_version':'24.21.0','evidence_class':'local-synthetic-browser-engine',
            'formal_accessibility':False,'production_qualified':False,
            'browser_sandbox':'disabled-for-owned-local-root-smoke'}


class BrowserReportTests(unittest.TestCase):
    def test_complete_bounded_local_report_is_accepted(self):
        validate_result(report(),'155.0.8059.84','24.21.0')

    def test_diagnostic_or_different_toolchain_is_not_acceptance(self):
        for update in ({'status':'BROWSER_DIAGNOSTIC_PASS'},{'node_version':'24.15.0'},
                       {'browser_version':'151.0.0'},{'evidence_class':'production'}):
            with self.subTest(update=update),self.assertRaises(ValueError):validate_result(report()|update,'155.0.8059.84','24.21.0')

    def test_incomplete_counts_and_promoted_boundaries_fail(self):
        for update in ({'checks':53}, {'checks':48},{'modes':1},{'roles':1},{'roles':True},{'modes':True},{'formal_accessibility':True},
                       {'production_qualified':True},{'browser_sandbox':'qualified'}):
            with self.subTest(update=update),self.assertRaises(ValueError):validate_result(report()|update,'155.0.8059.84','24.21.0')

    def test_missing_fields_and_private_extra_output_fail(self):
        for name in report():
            value=report();del value[name]
            with self.subTest(name=name),self.assertRaises(ValueError):validate_result(value,'155.0.8059.84','24.21.0')
        for value in (None,[],{},report()|{'cookie':'PRIVATE_CANARY'}):
            with self.assertRaises(ValueError):validate_result(value,'155.0.8059.84','24.21.0')


if __name__=='__main__':unittest.main()
