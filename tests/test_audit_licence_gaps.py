import base64
import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile
import unittest
import zipfile
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import audit_licence_gaps as audit


def tar(entries):
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode='w:gz') as archive:
        for name, data, kind in entries:
            member = tarfile.TarInfo(name)
            member.type = kind
            member.size = len(data)
            archive.addfile(member, io.BytesIO(data))
    return stream.getvalue()


class AuditTests(unittest.TestCase):
    def test_verified_archive_and_candidate_texts(self):
        data = tar([('package/LICENSE', b'synthetic notice', tarfile.REGTYPE),
                    ('package/COPYRIGHT.txt', b'synthetic copyright', tarfile.REGTYPE),
                    ('package/index.js', b'code', tarfile.REGTYPE)])
        audit.verify(data, 'sha512-' + base64.b64encode(hashlib.sha512(data).digest()).decode())
        members, found = audit.inspect_archive(data, 'npm')
        self.assertEqual(len(members), 3)
        self.assertEqual(set(found), {'package/LICENSE', 'package/COPYRIGHT.txt'})

    def test_digest_mismatch_precedes_archive_parsing(self):
        record = {'name': 'synthetic', 'version': '1', 'licence_texts': [],
                  'artifact_url': 'https://registry.npmjs.org/synthetic.tgz', 'artifact_hash': 'sha256:' + '0' * 64}
        source = json.dumps({'npm': [record], 'python_runtime': [], 'python_tools': []}).encode()
        with patch.object(audit, 'inspect_archive') as inspect:
            with self.assertRaisesRegex(ValueError, 'digest mismatch'):
                audit.audit(source, lambda *_: b'wrong bytes')
            inspect.assert_not_called()

    def test_exact_gap_selection_and_duplicates(self):
        record = {'name': 'synthetic', 'version': '1', 'licence_texts': []}
        value = {'npm': [record], 'python_runtime': [], 'python_tools': [dict(record, licence_texts=['present'])]}
        self.assertEqual(audit.targets(value), [('npm', record)])
        value['npm'].append(record)
        with self.assertRaises(ValueError): audit.targets(value)

    def test_unsafe_names_duplicates_and_links(self):
        for entries in [ [('..//escape', b'x', tarfile.REGTYPE)],
                         [('/absolute', b'x', tarfile.REGTYPE)],
                         [('package\\escape', b'x', tarfile.REGTYPE)],
                         [('package/x', b'', tarfile.SYMTYPE)],
                         [('package/x', b'x', tarfile.REGTYPE)] * 2 ]:
            with self.subTest(entries=entries), self.assertRaises(ValueError):
                audit.inspect_archive(tar(entries), 'npm')

    def test_zip_notice_and_symlink_denial(self):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, 'w') as archive:
            archive.writestr('synthetic.dist-info/licenses/LICENSES.txt', b'synthetic notice')
        _, found = audit.inspect_archive(stream.getvalue(), 'python_tools')
        self.assertEqual(len(found), 1)
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, 'w') as archive:
            member = zipfile.ZipInfo('LICENSE'); member.external_attr = 0o120777 << 16
            archive.writestr(member, b'target')
        with self.assertRaises(ValueError): audit.inspect_archive(stream.getvalue(), 'python_tools')

    def test_bounds_and_absent_notice_are_explicit(self):
        data = tar([('package/index.js', b'code', tarfile.REGTYPE)])
        self.assertEqual(audit.inspect_archive(data, 'npm')[1], {})
        for name, limit in [('MAX_MEMBERS', 0), ('MAX_TOTAL', 2)]:
            with patch.object(audit, name, limit), self.assertRaises(ValueError):
                audit.inspect_archive(data, 'npm')
        with patch.object(audit, 'MAX_TEXT', 2), self.assertRaises(ValueError):
            audit.inspect_archive(tar([('LICENSE', b'long', tarfile.REGTYPE)]), 'npm')
        with patch.object(audit, 'MAX_ARCHIVE', 1), self.assertRaises(ValueError):
            audit.verify(data, 'sha256:' + audit.sha256(data))

    def test_only_exact_official_https_origins(self):
        for url in ('http://registry.npmjs.org/a', 'https://registry.npmjs.org.evil/a',
                    'https://user@registry.npmjs.org/a', 'https://registry.npmjs.org/a?token=x'):
            with self.assertRaises(ValueError): audit.artifact_url(url, 'npm')
        with self.assertRaises(ValueError): audit.artifact_url('https://registry.npmjs.org/a', 'python_tools')

    def test_report_never_grants_completeness_or_legal_approval(self):
        data = tar([('package/LICENSE', b'synthetic notice', tarfile.REGTYPE)])
        record = {'name': 'synthetic', 'version': '1', 'licence_texts': [],
                  'artifact_url': 'https://registry.npmjs.org/a', 'artifact_hash': 'sha256:' + audit.sha256(data)}
        report, payloads = audit.audit(json.dumps({'npm': [record], 'python_runtime': [], 'python_tools': []}).encode(), lambda *_: data)
        self.assertFalse(report['inventory_complete']); self.assertFalse(report['legal_approval'])
        self.assertEqual(len(payloads), 1)
        self.assertEqual(report['findings'][0]['status'], 'candidate-text-found-review-pending')


if __name__ == '__main__': unittest.main()
