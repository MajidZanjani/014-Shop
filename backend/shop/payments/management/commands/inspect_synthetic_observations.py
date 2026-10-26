"""Read retained local observation metadata without provider I/O or authority."""
import json
import uuid
from pathlib import Path
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand,CommandError
from django.db import DatabaseError,transaction
from shop.adapters.evidence_archive import PreparedArchive,ArchiveError
from shop.catalog.checkout import CheckoutError
from shop.payments import synthetic_bank,observations
from shop.payments.models import SyntheticPaymentAttempt


class Command(BaseCommand):
    help='Inspect retained synthetic observations; no provider calls, values, references or retry authority.'
    def add_arguments(self,parser):parser.add_argument('--attempt',required=True)
    def handle(self,*args,**options):
        try:
            synthetic_bank.guard();identity=uuid.UUID(options['attempt'])
            if str(identity)!=options['attempt'] or not settings.LOCAL_CHECKOUT_ARCHIVE_ROOT:raise ValueError()
            with PreparedArchive(Path(settings.LOCAL_CHECKOUT_ARCHIVE_ROOT)) as archive,transaction.atomic(durable=True):
                row=SyntheticPaymentAttempt.objects.select_for_update().get(pk=identity)
                value=observations.inspect_locked(row,archive)
        except (ValueError,TypeError,ArchiveError,CheckoutError,OSError,DatabaseError,ObjectDoesNotExist):
            raise CommandError('Local synthetic observation inspection unavailable') from None
        self.stdout.write(json.dumps(value,sort_keys=True))
