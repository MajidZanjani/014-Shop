#!/usr/bin/env python3
"""Bounded catalog schema/conformance and full Python/JS output agreement."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'scripts')]
from compile_catalog import compile_catalog
from shop.catalog.rules import evaluate

def main():
    compile_catalog(check=True)
    import unittest
    import io
    suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_catalog_compiler.py')
    stream=io.StringIO()
    result=unittest.TextTestRunner(stream=stream,verbosity=1).run(suite)
    if not result.wasSuccessful() or result.skipped: raise RuntimeError('catalog schema tests failed: '+stream.getvalue())
    cases=json.loads((ROOT/'frontend/tests/conformance.json').read_text())
    results=[]
    for c in cases:
        r=evaluate(c['value'])
        assert r['status']==c['status'],c['name']
        assert [e['field']+':'+e['code'] for e in r['errors']]==c['errors'],c['name']
        results.append(r)
    scratch=ROOT/'.scratch';scratch.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='catalog-',dir=scratch) as directory:
        output=Path(directory)/'browser.json'
        env=dict(os.environ,SHOP_COMPARE_OUTPUT=str(output))
        r=subprocess.run(['node','--test','tests/configuration.test.mjs'],cwd=ROOT/'frontend',env=env,text=True,capture_output=True,timeout=40)
        if r.returncode: raise RuntimeError(r.stdout+r.stderr)
        assert json.loads(output.read_text())==results,'browser/backend outputs diverged'
    print(f'CATALOG_PASS checks={len(cases)} tests={len(cases)+2+result.testsRun} evidence_class=local-synthetic')
if __name__=='__main__':main()
