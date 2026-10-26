"""Real PostgreSQL synthetic reservation journal and archive failure checks."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Barrier
from unittest.mock import patch
import uuid
from django.db import connections, transaction, IntegrityError
from django.test import TransactionTestCase, override_settings
from shop.adapters.evidence_archive import PreparedArchive, ArchiveError
from shop.payments.bank_contract import BankError
from . import document_numbers as service, checkout
from .models import SyntheticDocumentReservation as Reservation, SyntheticDocumentIssue as Issue


class DocumentNumberTests(TransactionTestCase):
    def setUp(self):
        directory=TemporaryDirectory();self.addCleanup(directory.cleanup)
        self.archive=PreparedArchive(Path(directory.name));self.addCleanup(self.archive.__exit__,None,None,None)

    def reserve(self,kind='invoice',key=None,subject=None):
        return service.reserve(kind,key or uuid.uuid4(),subject or uuid.uuid4(),self.archive)

    def test_retry_separate_issue_and_independent_series(self):
        key=uuid.uuid4();subject=uuid.uuid4();row=self.reserve(key=key,subject=subject)
        self.assertEqual(self.reserve(key=key,subject=subject).pk,row.pk)
        self.assertEqual(Issue.objects.count(),0)
        issued=service.issue(row.pk,self.archive)
        self.assertEqual(service.issue(row.pk,self.archive).pk,issued.pk)
        self.assertFalse(issued.payload['actual_document_issued'])
        self.assertEqual(self.reserve().number,2);self.assertEqual(self.reserve('credit').number,1)
        with self.assertRaises(checkout.CheckoutError):self.reserve(key=key)
        with self.assertRaises(checkout.CheckoutError):self.reserve('credit',key,subject)

    def test_archive_failure_prevents_reservation_and_issue(self):
        with patch.object(self.archive,'publish',side_effect=ArchiveError('offline')):
            with self.assertRaises(ArchiveError):self.reserve()
        self.assertEqual(Reservation.objects.count(),0)
        row=self.reserve()
        with patch.object(self.archive,'publish',side_effect=ArchiveError('offline')):
            with self.assertRaises(ArchiveError):service.issue(row.pk,self.archive)
        self.assertEqual(Issue.objects.count(),0)
        self.assertEqual(self.reserve().number,2)

    def test_missing_retained_archive_blocks_further_allocation(self):
        self.reserve()
        with patch.object(self.archive,'recover',side_effect=ArchiveError('missing')):
            with self.assertRaises((ArchiveError,checkout.CheckoutError)):self.reserve()
        self.assertEqual(Reservation.objects.count(),1)

    def test_database_prohibits_history_mutation(self):
        row=self.reserve();issued=service.issue(row.pk,self.archive)
        for query in (Reservation.objects.filter(pk=row.pk),Issue.objects.filter(pk=issued.pk)):
            with self.assertRaises(IntegrityError),transaction.atomic():query.update(sha256='0'*64)
            with self.assertRaises(IntegrityError),transaction.atomic():query.delete()

    def test_competing_empty_series_allocations_are_unique(self):
        barrier=Barrier(2)
        def run(_):
            connections.close_all()
            try:
                barrier.wait(timeout=10)
                return self.reserve().number
            finally:connections.close_all()
        with ThreadPoolExecutor(2) as pool:self.assertEqual(sorted(pool.map(run,range(2))),[1,2])

    def test_same_request_concurrent_retry_converges(self):
        barrier=Barrier(2);key=uuid.uuid4();subject=uuid.uuid4()
        def run(_):
            connections.close_all()
            try:
                barrier.wait(timeout=10)
                return self.reserve(key=key,subject=subject).pk
            finally:connections.close_all()
        with ThreadPoolExecutor(2) as pool:results=list(pool.map(run,range(2)))
        self.assertEqual(results[0],results[1]);self.assertEqual(Reservation.objects.count(),1)

    @override_settings(SHOP_ENV='production')
    def test_live_mode_closed(self):
        with self.assertRaises(BankError):self.reserve()

    def test_competing_issue_retries_keep_one_record(self):
        row=self.reserve();barrier=Barrier(2)
        def run(_):
            connections.close_all()
            try:
                barrier.wait(timeout=10)
                return service.issue(row.pk,self.archive).pk
            finally:connections.close_all()
        with ThreadPoolExecutor(2) as pool:results=list(pool.map(run,range(2)))
        self.assertEqual(results[0],results[1]);self.assertEqual(Issue.objects.count(),1)

    def test_issue_archive_is_required_before_new_number(self):
        row=self.reserve();issued=service.issue(row.pk,self.archive)
        original=self.archive.recover
        def recover(receipt):
            if receipt.evidence_id==issued.pk:raise ArchiveError('missing issued evidence')
            return original(receipt)
        with patch.object(self.archive,'recover',side_effect=recover):
            with self.assertRaises((ArchiveError,checkout.CheckoutError)):self.reserve()
        self.assertEqual(Reservation.objects.count(),1)
