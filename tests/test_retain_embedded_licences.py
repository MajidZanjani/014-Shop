import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import retain_embedded_licences as embedded

ROOT = Path(__file__).resolve().parents[1]


class EmbeddedTests(unittest.TestCase):
    def setUp(self):
        report = json.loads((ROOT / 'docs/evidence/t02/embedded-licences.json').read_bytes())
        self.text = (ROOT / 'docs/evidence/t02' / report['findings'][0]['retained_path']).read_bytes()

    def test_exact_bytes_and_range(self):
        for text in (self.text, self.text.replace(b'\n', b'\r\n')):
            self.assertEqual(embedded.header(text + b'import synthetic\n'), text)

    def test_every_required_clause_and_nonleading_header_denied(self):
        for phrase in (b'Copyright', b'SPDX-License-Identifier', b'Permission is hereby granted',
                       b'The above copyright notice', b'THE SOFTWARE IS PROVIDED'):
            with self.subTest(phrase=phrase), self.assertRaises(ValueError):
                embedded.header(self.text.replace(phrase, b'removed'))
        with self.assertRaises(ValueError): embedded.header(b'import synthetic\n' + self.text)
        with self.assertRaises(ValueError): embedded.header(b'# only MIT metadata\n')

    def test_leading_comment_bound(self):
        with self.assertRaises(ValueError): embedded.header(b'#' + b'x' * embedded.LIMIT + b'\n' + self.text)

    def fixture(self):
        records, archives = [], {}
        for (name, version), member in embedded.SELECTED.items():
            stream = io.BytesIO()
            with zipfile.ZipFile(stream, 'w') as archive:
                archive.writestr(member, self.text + b'import synthetic\n')
            data = stream.getvalue(); url = 'https://files.pythonhosted.org/' + name + '.whl'
            archives[url] = data
            records.append({'name': name, 'version': version, 'licence_texts': [],
                            'artifact_url': url, 'artifact_hash': 'sha256:' + embedded.sha256(data)})
        source = {'npm': [], 'python_runtime': [], 'python_tools': records}
        return source, archives

    def test_hashes_members_ranges_and_pending_flags(self):
        source, archives = self.fixture()
        report, texts = embedded.collect(json.dumps(source).encode(), lambda url, _: archives[url])
        self.assertEqual(len(report['findings']), 2)
        for key in ('inventory_complete', 'legal_approval', 'package_wide_notice_review_complete'):
            self.assertFalse(report[key])
        for record in report['findings']:
            self.assertEqual(record['byte_end_exclusive'], len(self.text))
            self.assertEqual(texts[record['text_sha256']], self.text)
            self.assertEqual(record['member_sha256'], embedded.sha256(self.text + b'import synthetic\n'))

    def test_invented_version_missing_target_and_integrity_denied(self):
        source, archives = self.fixture()
        for bad in (dict(source, python_tools=[]),
                    dict(source, python_tools=[dict(r, version='invented') for r in source['python_tools']])):
            with self.assertRaises(ValueError): embedded.collect(json.dumps(bad).encode(), lambda *_: b'')
        with patch.object(embedded, 'inspect_archive') as inspect:
            with self.assertRaisesRegex(ValueError, 'digest mismatch'):
                embedded.collect(json.dumps(source).encode(), lambda *_: b'wrong')
            inspect.assert_not_called()
        with patch.dict(embedded.SELECTED, {('pip-requirements-parser', '32.0.1'): 'missing.py'}, clear=False):
            with self.assertRaises(KeyError):
                embedded.collect(json.dumps(source).encode(), lambda url, _: archives[url])


if __name__ == '__main__': unittest.main()
