"""Explicit local fixture intake/inspection, never a public bank callback."""
import json
import uuid
from pathlib import Path
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand,CommandError
from django.db import DatabaseError
from shop.adapters.evidence_archive import PreparedArchive,ArchiveError
from shop.payments import notifications


class Command(BaseCommand):
    help='Enqueue/inspect an archived local notification hint; no payment status input or real callbacks.'

    def add_arguments(self,parser):
        parser.add_argument('action',choices=['enqueue','inspect'])
        parser.add_argument('--notification',required=True)
        parser.add_argument('--attempt')

    def handle(self,*args,**options):
        try:
            notifications.guard()
            identity=uuid.UUID(options['notification'])
            if str(identity)!=options['notification'] or not settings.LOCAL_CHECKOUT_ARCHIVE_ROOT:raise ValueError()
            with PreparedArchive(Path(settings.LOCAL_CHECKOUT_ARCHIVE_ROOT)) as archive:
                if options['action']=='enqueue':
                    attempt=uuid.UUID(options.get('attempt') or '')
                    if str(attempt)!=options['attempt']:raise ValueError()
                    notifications.enqueue(attempt,identity,archive)
                elif options.get('attempt'):raise ValueError()
                value=notifications.inspect(identity,archive)
        except (ValueError,TypeError,ArchiveError,OSError,DatabaseError,ObjectDoesNotExist):
            raise CommandError('Local synthetic notification unavailable') from None
        # Fixed fields only; no UUID/reference/value, credentials, body, private path or bearer.
        self.stdout.write(json.dumps(value,sort_keys=True))
