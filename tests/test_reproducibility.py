from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from check_reproducibility import payload_manifest,compare


class PayloadTests(unittest.TestCase):
    def test_actual_changed_byte_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);path=root/'synthetic';path.write_bytes(b'one')
            first=payload_manifest(root);path.write_bytes(b'two')
            with self.assertRaises(ValueError):compare(first,payload_manifest(root))
    def test_empty_and_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            with self.assertRaises(ValueError):payload_manifest(root)
            (root/'link').symlink_to('synthetic')
            with self.assertRaises(ValueError):payload_manifest(root)
    def test_positive_exact_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'synthetic').write_bytes(b'synthetic')
            self.assertTrue(compare(payload_manifest(root),payload_manifest(root)))

    def test_canonical_target_owns_and_cleans_only_new_directory(self):
        from unittest.mock import patch
        from check_reproducibility import canonical_build_root
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)/'new-target'
            with patch('check_reproducibility.CANONICAL_BUILD_PATH',target):
                with canonical_build_root() as owned:
                    self.assertEqual(owned,target)
                    self.assertTrue((owned/'.owned').is_file())
                self.assertFalse(target.exists())

    def test_existing_canonical_target_is_not_reused(self):
        from unittest.mock import patch
        from check_reproducibility import canonical_build_root
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory);(target/'existing').write_text('protected-fixture')
            with patch('check_reproducibility.CANONICAL_BUILD_PATH',target):
                with self.assertRaises(FileExistsError):
                    with canonical_build_root():self.fail('existing directory reused')
            self.assertEqual((target/'existing').read_text(),'protected-fixture')

    def backend_fixture(self):
        import check_reproducibility as producer
        from unittest.mock import patch
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        root=Path(temporary.name);source=root/'backend';source.mkdir()
        # Large enough to exercise the real nonempty tar contract with a small fixture.
        (source/'manage.py').write_bytes(b'# synthetic source\n'*2048)
        assets={'shop/catalog/templates/catalog/example.html':b'<p>synthetic</p>',
                'shop/access/templates/access/example.html':b'<p>access</p>',
                'shop/catalog/shop.css':b'p {color: black}',
                'shop/catalog/revision.json':b'{"synthetic":true}',
                'shop/catalog/document_preview.json':b'{"documents":[]}',
                'requirements/runtime.in':b'synthetic==1'}
        for name,data in assets.items():
            path=source/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
        for name in ('.env','shop/catalog/customer-hosts.json','shop/catalog/private.html'):
            path=source/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'PRIVATE_FIXTURE_MUST_NOT_PACKAGE')
        output=root/'build';output.mkdir()
        return producer,root,source,output,assets,patch

    def test_backend_release_contains_current_runtime_assets_and_excludes_private_inputs(self):
        import tarfile
        producer,root,source,output,assets,patch=self.backend_fixture()
        with patch.object(producer,'ROOT',root):rows=producer.backend_package(output,123456)
        expected={'manage.py',*assets}
        self.assertEqual({row['path'] for row in rows},expected)
        with tarfile.open(output/'payload/backend.tar') as archive:
            self.assertEqual(set(archive.getnames()),expected)
            for name,data in assets.items():self.assertEqual(archive.extractfile(name).read(),data)
            self.assertTrue(all(row.mtime==123456 and row.uid==row.gid==0 for row in archive))

    def test_selected_runtime_asset_symlink_is_rejected(self):
        producer,root,source,output,assets,patch=self.backend_fixture()
        path=source/'shop/catalog/revision.json';path.unlink();path.symlink_to(source/'.env')
        with patch.object(producer,'ROOT',root),self.assertRaises(ValueError):producer.backend_package(output,123456)

    def test_canonical_marker_initialization_failure_cleans_only_its_new_directory(self):
        import errno
        from unittest.mock import patch
        import check_reproducibility as producer
        actual_open=Path.open
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)/'new-target';marker=target/'.owned'
            class FailingWrite:
                def __init__(self,stream):self.stream=stream
                def __enter__(self):return self
                def __exit__(self,*args):return self.stream.__exit__(*args)
                def fileno(self):return self.stream.fileno()
                def write(self,value):raise OSError(errno.ENOSPC,'synthetic marker write failure')
            def opened(path,*args,**kwargs):
                stream=actual_open(path,*args,**kwargs)
                mode=args[0] if args else kwargs.get('mode','r')
                return FailingWrite(stream) if path==marker and any(flag in mode for flag in ('w','x')) else stream
            with patch.object(producer,'CANONICAL_BUILD_PATH',target),patch.object(Path,'open',opened):
                with self.assertRaises(OSError):
                    with producer.canonical_build_root():self.fail('initialization unexpectedly succeeded')
            self.assertFalse(target.exists(),'failed initialization left an owned target behind')

    def test_explicit_canonical_path_is_new_owned_recorded_input(self):
        from unittest.mock import patch
        import check_reproducibility as producer
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);owned=root/'.scratch';owned.mkdir();target=owned/'canonical'
            with patch.object(producer,'ROOT',root):
                try:
                    with producer.canonical_build_root(target) as selected:
                        self.assertEqual(selected,target);self.assertTrue((target/'.owned').is_file())
                except TypeError as error:self.fail('Explicit owned canonical path unavailable: '+str(error))
                self.assertFalse(target.exists())
                with self.assertRaises(ValueError):
                    with producer.canonical_build_root(root/'outside-owned-scratch'):self.fail('unsafe target accepted')

    def test_changed_canonical_marker_or_extra_file_prevents_cleanup(self):
        from unittest.mock import patch
        import check_reproducibility as producer
        for kind in ('marker','extra'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as directory:
                target=Path(directory)/'new-target'
                with patch.object(producer,'CANONICAL_BUILD_PATH',target),self.assertRaises(ValueError):
                    with producer.canonical_build_root():
                        if kind=='marker':(target/'.owned').write_text('different-owner')
                        else:(target/'foreign').write_text('protected-fixture')
                self.assertTrue(target.is_dir());self.assertTrue((target/'.owned').is_file())

    def test_failed_validation_never_overwrites_historical_evidence(self):
        import json,subprocess
        from contextlib import contextmanager
        from types import SimpleNamespace
        from unittest.mock import patch
        import check_reproducibility as producer
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);evidence=root/'docs/evidence/t02';evidence.mkdir(parents=True)
            originals={name:('HISTORICAL_'+name).encode() for name in ('manifest.json','reproducibility.json')}
            for name,data in originals.items():(evidence/name).write_bytes(data)
            for name in ('frontend/package-lock.json','ops/nixos/flake.lock'):
                path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('{}')
            fixture={'payload':[{'path':'synthetic','bytes':1,'sha256':'0'*64}],
                     'backend_files':[{'path':'synthetic','bytes':1,'sha256':'0'*64}],
                     'installed_graph':[{'path':'synthetic','version':'1','integrity':'synthetic'}]}
            @contextmanager
            def frozen(*args):yield Path(sys.executable),{},None
            validations=[]
            def rejected(command,**kwargs):
                validations.append(command);raise subprocess.CalledProcessError(1,command,stderr='synthetic schema rejection')
            suite=unittest.TestSuite([unittest.FunctionTestCase(lambda:None) for _ in range(3)])
            modules={'check':SimpleNamespace(tool_identities=lambda:{}),
                     'check_contracts':SimpleNamespace(artifact_record=lambda *args:{'locks':[],'artifacts':[]})}
            with patch.object(producer,'ROOT',root),patch.object(producer,'CANONICAL_BUILD_PATH',root/'canonical'),\
                 patch.object(producer,'build',return_value=fixture),patch.object(producer,'frozen_environment',frozen),\
                 patch.object(producer.subprocess,'check_output',return_value='123456\n'),\
                 patch.object(producer.subprocess,'run',side_effect=rejected),\
                 patch.object(unittest.TestLoader,'discover',return_value=suite),\
                 patch.dict(sys.modules,modules),patch.object(sys,'argv',['producer','--local','--record-evidence']):
                with self.assertRaises(subprocess.CalledProcessError):producer.main()
            self.assertEqual(len(validations),1)
            for name,data in originals.items():self.assertEqual((evidence/name).read_bytes(),data)
            self.assertEqual({path.relative_to(evidence).as_posix() for path in evidence.rglob('*.json')},set(originals))
