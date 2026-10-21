import json
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from shop.worker.models import Probe


class Command(BaseCommand):
    help = 'Enqueue one bounded local/synthetic probe; no business effect.'

    def add_arguments(self, parser):
        parser.add_argument('--payload', required=True)

    def handle(self, *args, **options):
        if settings.SHOP_ENV not in {'local', 'synthetic'}:
            raise CommandError('Probe enqueue requires local/synthetic mode')
        raw = options['payload']
        if len(raw.encode()) > 1024:
            raise CommandError('Probe payload exceeds limit')
        try:
            pairs = json.loads(raw, object_pairs_hook=list)
            # Exact pair shape also rejects duplicate keys, arrays and nested data.
            if (not isinstance(pairs, list) or len(pairs) != 2
                    or any(not isinstance(p, tuple) or len(p) != 2 for p in pairs)):
                raise ValueError()
            value = dict(pairs)
            if (set(value) != {'payload_version', 'evidence_class'} or type(value['payload_version']) is not int
                    or value['payload_version'] != 1 or value['evidence_class'] != 'local-synthetic'):
                raise ValueError()
        except (ValueError, TypeError):
            raise CommandError('Invalid synthetic probe payload') from None
        probe = Probe.objects.create(payload_version=1, evidence_class='local-synthetic')
        self.stdout.write(json.dumps({'id': str(probe.pk), 'effect_id': str(probe.effect_id), 'state': probe.state}))
