"""Explicit one-job local entrypoint; existing daemon/image defaults unchanged."""
import json
import uuid
from django.conf import settings
from django.core.management.base import BaseCommand,CommandError
from django.db import connection,DatabaseError
from shop.adapters.archive_destination import BoundPreparedArchive,LocalDestination
from shop.adapters.evidence_archive import ArchiveError
from shop.catalog.models import ArchiveDestination
from shop.catalog.request_envelope import EnvelopeError
from shop.worker.prepared import execute_prepared_once

class Command(BaseCommand):
    help='Run one explicitly authorized local prepared archive job; no queue loop or retries.'

    def add_arguments(self,parser):
        parser.add_argument('--authorization',required=True)
        parser.add_argument('--destination',required=True)
        parser.add_argument('--root',required=True,help='Existing private bound root; never initialized or adopted.')

    def handle(self,*args,**options):
        if (settings.SHOP_ENV not in ('local','synthetic') or settings.STORAGE_ADAPTER!='fake'
            or connection.vendor!='postgresql' or connection.in_atomic_block or not connection.get_autocommit()):
            raise CommandError('Local prepared archive job unavailable')
        try:
            authorization=uuid.UUID(options['authorization']);destination_id=uuid.UUID(options['destination'])
            if str(authorization)!=options['authorization'] or str(destination_id)!=options['destination']:raise ValueError()
            root=options['root']
            if type(root) is not str or not 1<=len(root)<=4096 or '\x00' in root:raise ValueError()
            destination=ArchiveDestination.objects.filter(pk=destination_id,profile='local-prepared-v1').first()
            if destination is None:raise EnvelopeError('destination_unavailable')
            proof=LocalDestination(destination.pk,destination.device,destination.inode,destination.manifest_sha256)
            with BoundPreparedArchive(root,proof) as archive:
                result=execute_prepared_once(authorization,archive)
        except (ValueError,TypeError,ArchiveError,EnvelopeError,DatabaseError,OSError):
            # No private paths, UUIDs, tokens, hashes, values or provider errors.
            raise CommandError('Local prepared archive job unavailable') from None
        self.stdout.write(json.dumps({'status':'local_prepared_verified','created':result.created,
            'retention_qualified':False,'effects_authorized':False},sort_keys=True,separators=(',',':')))
