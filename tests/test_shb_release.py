"""Private release byte identity, public-origin denial and symlink controls."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))


class PrivateReleaseTests(unittest.TestCase):
    def setUp(self):
        from shop.shb import private_release
        self.release=private_release
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        self.root=Path(temporary.name)
        for name,body in {'index.html':b'<h1>Access requires an invitation</h1>',
            'support/index.html':b'<h1>Access requires an invitation</h1>',
            'private-storefront/index.html':b'<h1>Supporting Hours Bundle</h1><script type="module">void 0</script>',
            '_astro/shb.synthetic.js':b'void 0;'}.items():
            path=self.root/name;path.parent.mkdir(exist_ok=True);path.write_bytes(body)
        self.manifest=self.release.make_manifest(self.root)
        self.encoded=self.release.encode_manifest(self.manifest)
        (self.root/self.release.MANIFEST).write_bytes(self.encoded)
        self.expected=hashlib.sha256(self.encoded).hexdigest()

    def test_exact_bytes_and_only_protected_entry_and_assets_are_served(self):
        raw,mime,policy=self.release.read_asset(self.root,self.expected,'private-storefront/index.html')
        self.assertIn(b'Supporting Hours Bundle',raw);self.assertEqual(mime,'text/html; charset=utf-8')
        self.assertIn('sha256-',policy)
        self.assertEqual(self.release.read_asset(self.root,self.expected,'_astro/shb.synthetic.js')[0],b'void 0;')
        for path in ('index.html','support/index.html','../index.html','_astro/../index.html','missing.js'):
            with self.subTest(path=path),self.assertRaises(ValueError):self.release.read_asset(self.root,self.expected,path)

    def test_actual_changed_file_or_manifest_and_unpinned_config_are_denied(self):
        (self.root/'_astro/shb.synthetic.js').write_bytes(b'changed')
        with self.assertRaises(ValueError):self.release.read_asset(self.root,self.expected,'_astro/shb.synthetic.js')
        (self.root/self.release.MANIFEST).write_bytes(self.encoded+b' ')
        with self.assertRaises(ValueError):self.release.read_asset(self.root,self.expected,'private-storefront/index.html')
        with self.assertRaises(ValueError):self.release.read_asset(self.root,None,'private-storefront/index.html')

    def test_symlink_file_directory_and_unknown_source_map_are_denied(self):
        path=self.root/'_astro/shb.synthetic.js';path.unlink();path.symlink_to(self.root/'index.html')
        with self.assertRaises((ValueError,OSError)):self.release.read_asset(self.root,self.expected,'_astro/shb.synthetic.js')
        with self.assertRaises(ValueError):self.release.make_manifest(self.root)
        path.unlink();path.write_bytes(b'void 0;')
        (self.root/'_astro/private.js.map').write_text('{}')
        with self.assertRaises(ValueError):self.release.make_manifest(self.root)

    def test_protected_copy_in_public_root_is_rejected(self):
        (self.root/'index.html').write_text('<h1>FPGA Supporting Hours Bundle</h1>')
        with self.assertRaises(ValueError):self.release.make_manifest(self.root)


if __name__=='__main__':unittest.main()
