"""Only explicit owned disposable roots; no provider/host operations."""
from dataclasses import replace
from pathlib import Path
import shutil
import tempfile
from unittest.mock import patch
import uuid
from django.test import SimpleTestCase,override_settings
from .archive_destination import initialize_destination,BoundPreparedArchive,MARKER
from .evidence_archive import ArchiveError,ArchiveConflict

class LocalDestinationTests(SimpleTestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory();self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name)/'archive';self.root.mkdir(mode=0o700)
        self.identity=uuid.uuid4()
    def test_explicit_initialize_reopen_and_exact_publication(self):
        destination=initialize_destination(self.root,self.identity)
        self.assertEqual(initialize_destination(self.root,self.identity),destination)
        with BoundPreparedArchive(self.root,destination) as archive:
            receipt=archive.publish(uuid.uuid4(),b'PRIVATE_LOCAL_PREPARED_BYTES')
        with BoundPreparedArchive(self.root,destination) as archive:
            self.assertEqual(archive.attest(),destination)
            self.assertEqual(archive.recover(receipt),b'PRIVATE_LOCAL_PREPARED_BYTES')
        self.assertFalse(receipt.effects_authorized);self.assertFalse(receipt.retention_qualified)
        with self.assertRaises(ArchiveConflict):initialize_destination(self.root,uuid.uuid4())
    def test_copy_or_replacement_cannot_reuse_identity(self):
        destination=initialize_destination(self.root,self.identity)
        copied=self.root.parent/'copy';shutil.copytree(self.root,copied)
        with self.assertRaises(ArchiveError):BoundPreparedArchive(copied,destination)
        self.root.rename(self.root.parent/'original');self.root.mkdir(mode=0o700)
        shutil.copyfile(self.root.parent/'original'/MARKER,self.root/MARKER);(self.root/MARKER).chmod(0o600)
        with self.assertRaises(ArchiveError):BoundPreparedArchive(self.root,destination)
    def test_no_automatic_adoption_and_unsafe_marker_or_mode_fails(self):
        (self.root/'old-object').write_bytes(b'PRIVATE_OLD_DATA')
        with self.assertRaises(ArchiveError):initialize_destination(self.root,self.identity)
        self.assertEqual((self.root/'old-object').read_bytes(),b'PRIVATE_OLD_DATA')
        (self.root/'old-object').unlink();destination=initialize_destination(self.root,self.identity)
        marker=self.root/MARKER;marker.chmod(0o644)
        with self.assertRaises(ArchiveError):BoundPreparedArchive(self.root,destination)
        marker.chmod(0o600)
        with BoundPreparedArchive(self.root,destination) as archive:
            self.root.chmod(0o755)
            with self.assertRaises(ArchiveError):archive.attest()
        self.root.chmod(0o700)
        marker.unlink();marker.symlink_to('/dev/null')
        with self.assertRaises(ArchiveError):BoundPreparedArchive(self.root,destination)
    def test_change_during_publication_is_unacknowledged_and_bytes_remain(self):
        destination=initialize_destination(self.root,self.identity)
        with BoundPreparedArchive(self.root,destination) as archive:
            original=archive.publish_file
            def changed(name,value):
                original(name,value)
                if name.startswith('receipt-'):(self.root/MARKER).write_bytes(b'{}')
            with patch.object(archive,'publish_file',changed):
                with self.assertRaises(ArchiveError):archive.publish(uuid.uuid4(),b'private prepared fact')
        self.assertEqual(len(list(self.root.iterdir())),3)
    def test_forged_reference_environment_and_lost_initialization_ack(self):
        destination=initialize_destination(self.root,self.identity)
        with self.assertRaises(ArchiveError):BoundPreparedArchive(self.root,replace(destination,manifest_sha256='0'*64))
        for mode in ('production','bank-sandbox'):
            with override_settings(SHOP_ENV=mode):
                with self.assertRaises(ArchiveError):BoundPreparedArchive(self.root,destination)
        with patch('shop.adapters.archive_destination.os.fsync',side_effect=OSError('PRIVATE_FSYNC')):
            with self.assertRaises(ArchiveError) as raised:initialize_destination(self.root,self.identity)
        self.assertNotIn('PRIVATE',str(raised.exception));self.assertNotIn(str(self.root),str(raised.exception))
        self.assertEqual(initialize_destination(self.root,self.identity),destination)
