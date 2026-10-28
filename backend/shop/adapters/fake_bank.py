from django.conf import settings
from django.db import connection
from shop.access.effects import local_effect
from shop.worker.models import FakeReceipt
from .ports import ProbeResult


@local_effect('probe-bank')
def perform_fake_probe(request):
    if settings.SHOP_ENV not in {'local', 'synthetic'} or settings.PAYMENT_ADAPTER != 'fake':
        raise ValueError('Synthetic bank unavailable in this environment')
    if connection.in_atomic_block:
        raise ValueError('Adapter cannot run inside claim transaction')
    outcomes = {'ok': 'synthetic-ok', 'rejected': 'synthetic-rejected', 'unknown': 'synthetic-unknown'}
    if request.scenario == 'timeout':
        raise TimeoutError('Synthetic timeout')
    if request.scenario not in outcomes:
        raise ValueError('Unsupported or malformed synthetic bank scenario')
    outcome = outcomes[request.scenario]
    receipt, created = FakeReceipt.objects.get_or_create(effect_id=request.effect_id,
        defaults={'scenario': request.scenario, 'outcome': outcome})
    if receipt.scenario != request.scenario or receipt.outcome != outcome:
        raise ValueError('Synthetic receipt identity conflict')
    return ProbeResult(request.effect_id, receipt.outcome)
