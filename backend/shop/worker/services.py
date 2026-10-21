"""Finite leased ownership; stable fake identity is separate from claim tokens."""
from dataclasses import dataclass
from datetime import timedelta
import uuid
from django.conf import settings
from django.db import connection, transaction
from django.db.models import F, Q
from django.db.models.functions import Now
from shop.adapters.ports import ProbeRequest
from shop.adapters.fake_bank import perform_fake_probe
from .models import Probe


@dataclass(frozen=True)
class Claim:
    probe_id: uuid.UUID
    effect_id: uuid.UUID
    token: uuid.UUID


def claim_probe(*, lease_seconds=10, max_attempts=3):
    if settings.SHOP_ENV not in {'local', 'synthetic'} or connection.vendor != 'postgresql':
        raise ValueError('Synthetic PostgreSQL worker required')
    if connection.in_atomic_block or not connection.get_autocommit():
        raise ValueError('Claim must own its short transaction')
    if type(lease_seconds) is not int or not 1 <= lease_seconds <= 60 or type(max_attempts) is not int or not 1 <= max_attempts <= 5:
        raise ValueError('Invalid finite worker bounds')
    eligible = Q(state='pending') | Q(state='claimed', lease_until__lte=Now())
    with transaction.atomic():
        # Lock only one claim row; no external adapter executes in this transaction.
        row = (Probe.objects.select_for_update(skip_locked=True).filter(eligible)
               .order_by('id').first())
        if row is None:
            return None
        if row.attempts >= max_attempts:
            Probe.objects.filter(pk=row.pk).update(state='failed', claim_token=None, lease_until=None)
            return None
        token = uuid.uuid4()
        Probe.objects.filter(pk=row.pk).update(state='claimed', claim_token=token,
            lease_until=Now() + timedelta(seconds=lease_seconds), attempts=F('attempts') + 1)
        return Claim(row.pk, row.effect_id, token)


def complete_probe(claim, result):
    if result.effect_id != claim.effect_id or result.outcome != 'synthetic-ok':
        raise ValueError('Invalid synthetic result identity')
    if connection.in_atomic_block:
        raise ValueError('Completion must own its transaction')
    return Probe.objects.filter(pk=claim.probe_id, effect_id=claim.effect_id, state='claimed',
        claim_token=claim.token, lease_until__gt=Now()).update(state='complete', claim_token=None,
            lease_until=None, result={'outcome': result.outcome}) == 1


def execute_once(*, lease_seconds=10, max_attempts=3):
    claim = claim_probe(lease_seconds=lease_seconds, max_attempts=max_attempts)
    if claim is None:
        return False
    result = perform_fake_probe(ProbeRequest(claim.effect_id))
    complete_probe(claim, result)
    return True
