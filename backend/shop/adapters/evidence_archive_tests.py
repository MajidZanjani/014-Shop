"""Owned-directory synthetic evidence only; no provider or host fault tests."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import hashlib
import os
from pathlib import Path
import tempfile
from unittest.mock import patch
import uuid
from django.test import SimpleTestCase,override_settings
from .evidence_archive import PreparedArchive,PreparedReceipt,ArchiveError,ArchiveConflict,MAX_BYTES

class PreparedArchiveTests(SimpleTestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory();self.addCleanup(self.directory.cleanup)
        self.root=Path(self.directory.name);self.identity=uuid.uuid4()
        self.payload=b'PRIVATE_SYNTHETIC_PREPARED_EVIDENCE'
    def publish(self):
        with PreparedArchive(self.root) as archive:return archive.publish(self.identity,self.payload)
    def test_publish_reopen_recover_and_exact_retry_are_prepared_only(self):
        receipt=self.publish()
        self.assertEqual(receipt.sha256,hashlib.sha256(self.payload).hexdigest())
        self.assertFalse(receipt.effects_authorized);self.assertFalse(receipt.retention_qualified)
        self.assertEqual(receipt.evidence_kind,'prepared')
        with PreparedArchive(self.root) as archive:
            self.assertEqual(archive.recover(receipt),self.payload)
            self.assertEqual(archive.publish(self.identity,self.payload),receipt)
            with self.assertRaises(ArchiveConflict):archive.publish(self.identity,b'changed')
        self.assertEqual(len(list(self.root.iterdir())),2)
        self.assertTrue(all(p.stat().st_mode&0o777==0o600 for p in self.root.iterdir()))
    def test_tampered_missing_blob_or_changed_receipt_never_recovers(self):
        receipt=self.publish();blob=self.root/('blob-'+receipt.sha256)
        blob.write_bytes(b'corrupted')
        with PreparedArchive(self.root) as archive:
            with self.assertRaises(ArchiveError):archive.recover(receipt)
            with self.assertRaises(ArchiveError):archive.publish(self.identity,self.payload)
        blob.write_bytes(self.payload);blob.unlink()
        with PreparedArchive(self.root) as archive:
            with self.assertRaises(ArchiveError):archive.recover(receipt)
        path=self.root/('receipt-'+self.identity.hex+'.json');path.write_bytes(b'{}')
        with PreparedArchive(self.root) as archive:
            with self.assertRaises(ArchiveError):archive.recover(receipt)
    def test_unsafe_root_symlink_file_modes_and_hardlinks_fail_closed(self):
        self.root.chmod(0o755)
        with self.assertRaises(ArchiveError):PreparedArchive(self.root)
        self.root.chmod(0o700);receipt=self.publish();blob=self.root/('blob-'+receipt.sha256)
        blob.chmod(0o644)
        with PreparedArchive(self.root) as archive:
            with self.assertRaises(ArchiveError):archive.recover(receipt)
        blob.chmod(0o600);os.link(blob,self.root/'extra')
        with PreparedArchive(self.root) as archive:
            with self.assertRaises(ArchiveError):archive.recover(receipt)
        (self.root/'extra').unlink();blob.unlink();blob.symlink_to('/dev/null')
        with PreparedArchive(self.root) as archive:
            with self.assertRaises(ArchiveError):archive.recover(receipt)
    def test_invalid_input_receipt_and_environment_do_not_create_files_or_echo(self):
        with PreparedArchive(self.root) as archive:
            for identity,value in [('../PRIVATE_PATH',self.payload),(self.identity,b''),(self.identity,b'x'*(MAX_BYTES+1)),(self.identity,'PRIVATE_DATA')]:
                with self.assertRaises(ArchiveError) as raised:archive.publish(identity,value)
                self.assertNotIn('PRIVATE',str(raised.exception));self.assertNotIn(str(self.root),str(raised.exception))
            receipt=PreparedReceipt(self.identity,'0'*64,1)
            for altered in [replace(receipt,effects_authorized=True),replace(receipt,retention_qualified=True),replace(receipt,evidence_kind='completed'),replace(receipt,size=True)]:
                with self.assertRaises(ArchiveError):archive.recover(altered)
        for env in ('production','bank-sandbox'):
            with override_settings(SHOP_ENV=env):
                with self.assertRaises(ArchiveError):PreparedArchive(self.root)
        self.assertEqual(list(self.root.iterdir()),[])
    def test_blob_published_but_receipt_failure_is_unacknowledged_and_retry_recovers(self):
        original=PreparedArchive.publish_file
        def fail_receipt(archive,name,value):
            if name.startswith('receipt-'):raise OSError('PRIVATE_UNAVAILABLE_PATH')
            return original(archive,name,value)
        with PreparedArchive(self.root) as archive:
            with patch.object(PreparedArchive,'publish_file',fail_receipt):
                with self.assertRaises(ArchiveError) as raised:archive.publish(self.identity,self.payload)
            self.assertEqual(str(raised.exception),'archive_unavailable')
        self.assertEqual(len(list(self.root.iterdir())),1)
        receipt=self.publish()
        with PreparedArchive(self.root) as archive:self.assertEqual(archive.recover(receipt),self.payload)
    def test_fsync_failure_never_acknowledges_and_retry_verifies_published_bytes(self):
        with PreparedArchive(self.root) as archive:
            with patch('shop.adapters.evidence_archive.os.fsync',side_effect=OSError('PRIVATE_FSYNC')):
                with self.assertRaises(ArchiveError):archive.publish(self.identity,self.payload)
        self.assertFalse(any(p.name.startswith('receipt-') for p in self.root.iterdir()))
        receipt=self.publish()
        with PreparedArchive(self.root) as archive:
            with patch('shop.adapters.evidence_archive.os.fsync',side_effect=OSError('PRIVATE_FSYNC')):
                with self.assertRaises(ArchiveError):archive.publish(self.identity,self.payload)
        with PreparedArchive(self.root) as archive:self.assertEqual(archive.recover(receipt),self.payload)
    def test_late_directory_sync_failure_is_not_acknowledged_but_retry_reconciles(self):
        with PreparedArchive(self.root) as archive:
            # Blob file/directory and receipt file sync succeed; receipt directory sync fails.
            with patch('shop.adapters.evidence_archive.os.fsync',side_effect=[None,None,None,OSError('PRIVATE_LATE_SYNC')]):
                with self.assertRaises(ArchiveError):archive.publish(self.identity,self.payload)
        self.assertTrue((self.root/('receipt-'+self.identity.hex+'.json')).exists())
        receipt=self.publish()
        with PreparedArchive(self.root) as archive:self.assertEqual(archive.recover(receipt),self.payload)
        self.assertEqual(len(list(self.root.iterdir())),2)

    def test_concurrent_publishers_contend_then_reconcile_without_overwrite(self):
        def publish(value):
            try:
                with PreparedArchive(self.root) as archive:return archive.publish(self.identity,value)
            except ArchiveError:return None
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(publish,[self.payload,self.payload]))
        self.assertTrue(any(results))
        expected=self.publish()
        with PreparedArchive(self.root) as archive:self.assertEqual(archive.recover(expected),self.payload)
        self.assertEqual(len(list(self.root.iterdir())),2)
    def test_distinct_identities_concurrently_publish_then_reconcile_independently(self):
        identities=[uuid.uuid4(),uuid.uuid4()]
        def publish(identity):
            try:
                with PreparedArchive(self.root) as archive:return archive.publish(identity,self.payload)
            except ArchiveError:return None
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(publish,identities))
        self.assertTrue(any(results))
        with PreparedArchive(self.root) as archive:
            receipts=[archive.publish(identity,self.payload) for identity in identities]
            self.assertNotEqual(receipts[0].evidence_id,receipts[1].evidence_id)
            self.assertTrue(all(archive.recover(receipt)==self.payload for receipt in receipts))
        self.assertEqual(len(list(self.root.iterdir())),3)
    def test_publication_failure_cleans_only_own_temporary_and_preserves_prior_evidence(self):
        existing=self.publish()
        with PreparedArchive(self.root) as archive:
            with patch('shop.adapters.evidence_archive.os.link',side_effect=OSError('PRIVATE_LINK_ERROR')):
                with self.assertRaises(ArchiveError):archive.publish(uuid.uuid4(),b'new prepared bytes')
            self.assertEqual(archive.recover(existing),self.payload)
        self.assertEqual(len(list(self.root.iterdir())),2)
