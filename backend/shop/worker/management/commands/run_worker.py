import signal
import threading
from django.core.management.base import BaseCommand, CommandError
from shop.core.logging import safe_event
from shop.worker.services import execute_once


class Command(BaseCommand):
    help = 'One foreground synthetic leased worker; no real external effects.'

    def add_arguments(self, parser):
        parser.add_argument('--once', action='store_true')
        parser.add_argument('--poll-interval', type=float, default=1)
        parser.add_argument('--lease-seconds', type=int, default=10)
        parser.add_argument('--max-attempts', type=int, default=3)

    def handle(self, *args, **options):
        if not 0.05 <= options['poll_interval'] <= 10 or not 1 <= options['lease_seconds'] <= 60 or not 1 <= options['max_attempts'] <= 5:
            raise CommandError('Invalid finite worker bounds')
        stop = threading.Event()
        old = signal.signal(signal.SIGTERM, lambda *_: stop.set())
        try:
            while not stop.is_set():
                try:
                    execute_once(lease_seconds=options['lease_seconds'], max_attempts=options['max_attempts'])
                except Exception:
                    safe_event('adapter.failed', 503)
                    if options['once']:
                        raise CommandError('Synthetic worker attempt failed') from None
                if options['once']:
                    break
                stop.wait(options['poll_interval'])
        finally:
            signal.signal(signal.SIGTERM, old)
