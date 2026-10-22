"""Reject malformed draft catalogs without altering any committed input/output."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('catalog_compiler',ROOT/'scripts/compile_catalog.py')
compiler=importlib.util.module_from_spec(spec);spec.loader.exec_module(compiler)

class CompilerTests(unittest.TestCase):
    def test_committed_revision(self):
        with contextlib.redirect_stdout(io.StringIO()): result=compiler.compile_catalog(check=True)
        self.assertEqual(len(result['vendors']),3)
        self.assertEqual(sum(len(v['families']) for v in result['vendors']),13)

    def test_schema_source_and_approval_tampering_rejected(self):
        original=json.loads(compiler.SOURCE.read_text().split('---',2)[1])
        def unknown(d):d['arbitrary_expression']='execute'
        def source(d):d['source_sha256']='0'*64
        def approval(d):d['approvals']['prices']='approved'
        def rates(d):d['money']['node_minor']=5000
        def family(d):d['vendors'][0]['families'][0]['id']='invented'
        def order(d):d['vendors'][0]['families'].reverse()
        def term(d):d['terms'][1]['vendors'].append('microchip')
        def bands(d):d['production_bands'][1]['minimum']=100
        for mutate in (unknown,source,approval,rates,family,order,term,bands):
            with self.subTest(mutation=mutate.__name__),tempfile.TemporaryDirectory() as directory:
                value=json.loads(json.dumps(original));mutate(value)
                source_path=Path(directory)/'catalog.md'
                source_path.write_text('---\n'+json.dumps(value)+'\n---\n')
                with patch.object(compiler,'SOURCE',source_path),self.assertRaises((AssertionError,KeyError,TypeError)):
                    compiler.compile_catalog(check=True)
