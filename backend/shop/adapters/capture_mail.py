"""In-memory synthetic mail capture; no SMTP transport or real recipients."""
import re
from django.conf import settings


class CaptureMail:
    def __init__(self):
        self.messages = {}

    def send(self, request):
        if settings.SHOP_ENV not in {'local', 'synthetic'} or settings.MAIL_ADAPTER != 'fake':
            raise ValueError('Synthetic mail unavailable')
        if (not isinstance(request.recipient, str) or len(request.recipient) > 160
                or re.fullmatch(r'[a-z0-9._+-]+@[a-z0-9-]+(?:\.[a-z0-9-]+)*\.invalid', request.recipient) is None
                or type(request.body) is not bytes or not 1 <= len(request.body) <= 4096):
            raise ValueError('Invalid synthetic message')
        old = self.messages.setdefault(request.effect_id, request)
        if old != request:
            raise ValueError('Synthetic message identity conflict')
        return request.effect_id

    def reset(self):
        self.messages.clear()
