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
from shop.catalog.cart_rules import evaluate_cart

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
    cart_cases=json.loads((ROOT/'frontend/tests/cart-conformance.json').read_text())
    cart_results=[evaluate_cart(c['lines']) for c in cart_cases]
    for c,r in zip(cart_cases,cart_results):
        assert r['status']==c['status'],c['name']
        assert [e['field']+':'+e['code'] for e in r['errors']]==c['errors'],c['name']
    with tempfile.TemporaryDirectory(prefix='cart-',dir=scratch) as directory:
        output=Path(directory)/'browser.json'
        r=subprocess.run(['node','--test','tests/cart.test.mjs'],cwd=ROOT/'frontend',env=dict(os.environ,SHOP_CART_COMPARE_OUTPUT=str(output)),text=True,capture_output=True,timeout=40)
        if r.returncode:raise RuntimeError(r.stdout+r.stderr)
        assert json.loads(output.read_text())==cart_results,'cart browser/backend outputs diverged'
    print(f'CART_CONFORMANCE_PASS cases={len(cart_cases)}')
    print(f'CATALOG_PASS checks={len(cases)+len(cart_cases)} tests={len(cases)+len(cart_cases)+2+result.testsRun} evidence_class=local-synthetic')
if __name__=='__main__':main()
