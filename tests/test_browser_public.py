"""Public browser acceptance requires both real modes and an exact fresh frontend build."""
from pathlib import Path
import sys
import tempfile
import json
from types import SimpleNamespace
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from check_browser_access import validate_public_result,validate_result,prepare_public
from check_browser_public import toolchain,build_public
from test_browser_report import report


def public_report():
    return report()|{'public_checks':{'javascript':59,'no_javascript':14},
                     'frontend_toolchain':{'node':'24.22.0','npm':'11.19.1'}}


class PublicBrowserTests(unittest.TestCase):
    def test_closed_qualified_public_report(self):
        validate_public_result(public_report(),'155.0.8059.84','24.21.0')
        with self.assertRaises(ValueError):validate_result(public_report(),'155.0.8059.84','24.21.0')
        for changed in ({'public_checks':{'javascript':55,'no_javascript':14}}, {'public_checks':{'javascript':47,'no_javascript':14}}, {'public_checks':{'javascript':43,'no_javascript':14}}, {'public_checks':{'javascript':39,'no_javascript':14}}, {'public_checks':{'javascript':34,'no_javascript':14}}, {'public_checks':{'javascript':29,'no_javascript':14}}, {'public_checks':{'javascript':25,'no_javascript':14}}, {'public_checks':{'javascript':20}}, {'public_checks':{'javascript':59.,'no_javascript':14}},
                        {'public_checks':{'javascript':20,'no_javascript':7}},
                        {'public_checks':{'javascript':59,'no_javascript':13}},
                        {'frontend_toolchain':{'node':'24.21.0','npm':'11.19.1'}},
                        {'production_qualified':True}, {'status':'BROWSER_PUBLIC_DIAGNOSTIC_PASS'},
                        {'private_extra':'CANARY'}):
            with self.subTest(changed=changed),self.assertRaises(ValueError):
                validate_public_result(public_report()|changed,'155.0.8059.84','24.21.0')
        with self.assertRaises(ValueError):validate_public_result(report(),'155.0.8059.84','24.21.0')

    def test_toolchain_checks_executable_and_version_before_build(self):
        env={'SHOP_NODE':'/nix/store/synthetic-node/bin/node',
             'SHOP_NPM':'/nix/store/synthetic-npm/bin/npm','PATH':'/synthetic'}
        def which(name,path):return env['SHOP_'+name.upper()]
        def version(args,*unused):return {'node':'v24.22.0','npm':'11.19.1'}[Path(args[0]).name]
        with patch('check_browser_public.shutil.which',side_effect=which),patch('check_browser_public.command',side_effect=version):
            self.assertEqual(toolchain(env),{'node':'24.22.0','npm':'11.19.1'})
            with self.assertRaises(ValueError):toolchain(env|{'SHOP_NODE':'/usr/bin/node'})
        with patch('check_browser_public.shutil.which',side_effect=which),patch('check_browser_public.command',return_value='v24.21.0'):
            with self.assertRaises(ValueError):toolchain(env)
        with patch('check_browser_public.shutil.which',return_value='/usr/bin/node'):
            with self.assertRaises(ValueError):toolchain(env)

    def test_stale_or_external_output_is_not_reused(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory=Path(temporary)
            with patch('check_browser_public.ROOT',directory/'different-project'),patch('check_browser_public.toolchain') as tools:
                with self.assertRaises(ValueError):build_public(directory)
                tools.assert_not_called()

    def test_nonempty_or_symlink_public_directory_is_rejected_before_tools(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);scratch=root/'.scratch';scratch.mkdir()
            public=scratch/'public';public.mkdir();(public/'stale.html').write_text('old')
            link=scratch/'linked';link.symlink_to(public,target_is_directory=True)
            with patch('check_browser_public.ROOT',root),patch('check_browser_public.toolchain') as tools:
                for target in (public,link):
                    with self.subTest(target=target.name),self.assertRaises(ValueError):build_public(target)
                tools.assert_not_called()

    def test_public_build_receipt_must_match_actual_scanned_artifacts(self):
        receipt={'status':'PUBLIC_BROWSER_BUILD_PASS','frontend_toolchain':{'node':'24.22.0','npm':'11.19.1'},
                 'artifacts':[{'path':'index.html','bytes':5,'sha256':'a'*64}]}
        for change in ({}, {'artifacts':[]}, {'private_extra':'CANARY'},
                       {'frontend_toolchain':{'node':'24.21.0','npm':'11.19.1'}}):
            with tempfile.TemporaryDirectory() as temporary,patch('check_browser_access.subprocess.run') as run,patch('check_frontend.scan_output',return_value=(receipt['artifacts'],1)):
                run.return_value=SimpleNamespace(returncode=0,stdout=json.dumps(receipt|change))
                if change:
                    with self.assertRaises(ValueError):prepare_public(Path(temporary)/'public')
                else:
                    self.assertEqual(prepare_public(Path(temporary)/'public'),receipt['frontend_toolchain'])
                kwargs=run.call_args.kwargs
                self.assertEqual(kwargs['timeout'],720)
                self.assertNotIn('DATABASE_PASSWORD',kwargs['env'])
                self.assertTrue(kwargs['env']['TMPDIR'].startswith(temporary))

    def test_build_failure_cannot_be_promoted_to_browser_evidence(self):
        with tempfile.TemporaryDirectory() as temporary,patch('check_browser_access.subprocess.run') as run:
            run.return_value.returncode=1
            with self.assertRaises(ValueError):prepare_public(Path(temporary)/'public')
            self.assertEqual(run.call_count,1)  # No downgrade or retry after unknown build outcome.


if __name__=='__main__':unittest.main()
