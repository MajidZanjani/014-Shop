from django.conf import settings
from django.db import connection
from shop.worker.models import FakeReceipt
from .ports import ProbeResult


def perform_fake_probe(request):
    if settings.SHOP_ENV not in {'local', 'synthetic'} or settings.PAYMENT_ADAPTER != 'fake':
        raise ValueError('Synthetic bank unavailable in this environment')
    if connection.in_atomic_block:
        raise ValueError('Adapter cannot run inside claim transaction')
    if request.scenario != 'ok':
        raise ValueError('Unsupported synthetic bank scenario')
    receipt, created = FakeReceipt.objects.get_or_create(effect_id=request.effect_id,
        defaults={'scenario': 'ok', 'outcome': 'synthetic-ok'})
    if receipt.scenario != request.scenario or receipt.outcome != 'synthetic-ok':
        raise ValueError('Synthetic receipt identity conflict')
    return ProbeResult(request.effect_id, receipt.outcome)
