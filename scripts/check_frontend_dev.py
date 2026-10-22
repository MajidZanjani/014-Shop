#!/usr/bin/env python3
"""Ordinary credential-free frontend build/test; no outage/exhaustion operations."""
import os
from pathlib import Path
import subprocess
import tempfile
ROOT=Path(__file__).resolve().parents[1]
def main():
    parent=ROOT/'.scratch';parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='frontend-dev-',dir=parent) as directory:
        env={key:os.environ[key] for key in ('PATH','LANG','SSL_CERT_FILE','NIX_SSL_CERT_FILE') if key in os.environ}
        env.update(ASTRO_TELEMETRY_DISABLED='1',NPM_CONFIG_USERCONFIG=directory+'/absent.npmrc',NPM_CONFIG_GLOBALCONFIG=directory+'/global.npmrc',NPM_CONFIG_CACHE=directory+'/cache',XDG_CONFIG_HOME=directory,TMPDIR=directory)
        from check_frontend import manifest, source_policy, scan_output
        import json
        names=manifest(json.loads((ROOT/'frontend/build-inputs.json').read_text()))
        for cmd in (['npm','ci','--no-audit','--no-fund'],['npm','run','check'],['npm','run','build'],['npm','test']):
            r=subprocess.run(cmd,cwd=ROOT/'frontend',env=env,text=True,capture_output=True,timeout=150)
            print(r.stdout,flush=True)
            if r.returncode: raise RuntimeError(r.stderr)
        source_policy(ROOT/'frontend',env)
        inventory,count=scan_output(ROOT/'frontend/dist')
        import io,unittest
        output=io.StringIO()
        result=unittest.TextTestRunner(stream=output).run(unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_demo_proxy.py'))
        if not result.wasSuccessful() or result.testsRun!=1 or result.skipped: raise RuntimeError(output.getvalue())
        print(f'DEMO_PROXY_PASS checks=5 tests={result.testsRun}')
    print(f'FRONTEND_PASS checks={4+len(names)+count} evidence_class=local-synthetic')
if __name__=='__main__':main()
