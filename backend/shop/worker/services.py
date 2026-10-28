"""Finite leased ownership; stable fake identity is separate from claim tokens."""
from dataclasses import dataclass
from datetime import timedelta
import uuid
import tempfile
from pathlib import Path
from django.conf import settings
from django.db import connection, transaction
from django.db.models import F, Q
from django.db.models.functions import Now
from shop.access.effects import local_effect
from shop.adapters.capture_mail import CaptureMail
from shop.adapters.local_storage import LocalStorage
from shop.adapters.ports import MailRequest, ProbeRequest
from shop.adapters.fake_bank import perform_fake_probe
from .models import Probe


@dataclass(frozen=True)
class Claim:
    probe_id: uuid.UUID
    effect_id: uuid.UUID
    token: uuid.UUID


@local_effect('probe-claim',held_result=None)
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
    if settings.SHOP_ENV not in {'local','synthetic'} or connection.vendor!='postgresql':
        raise ValueError('Synthetic PostgreSQL worker required')
    if connection.in_atomic_block or not connection.get_autocommit():
        raise ValueError('Worker must own its short transactions')
    if type(lease_seconds) is not int or not 1<=lease_seconds<=60 or type(max_attempts) is not int or not 1<=max_attempts<=5:
        raise ValueError('Invalid finite worker bounds')
    eligible=Q(state='pending')|Q(state='claimed',lease_until__lte=Now())
    # Read-only idle check avoids durable admission/WAL growth on every poll.
    # A stale miss only defers work to the next poll; every write still admits.
    available=Probe.objects.filter(eligible).exists()
    if not available and settings.LOCAL_CHECKOUT_ARCHIVE_ROOT:
        from shop.catalog.models import SyntheticStatementDelivery
        from shop.payments.models import SyntheticNotificationDelivery
        available=(SyntheticStatementDelivery.objects.filter(eligible).exists()
            or SyntheticNotificationDelivery.objects.filter(eligible).exists())
    if not available:return False
    return _execute_admitted(lease_seconds=lease_seconds,max_attempts=max_attempts)


@local_effect('worker-run',held_result=False)
def _execute_admitted(*,lease_seconds,max_attempts):
    if settings.LOCAL_CHECKOUT_ARCHIVE_ROOT:
        from .statement_mail import execute_once as capture_statement
        if capture_statement(lease_seconds=lease_seconds,max_attempts=max_attempts):return True
        from shop.payments.notifications import execute_once as check_notification
        if check_notification(lease_seconds=lease_seconds,max_attempts=max_attempts):return True
    claim = claim_probe(lease_seconds=lease_seconds, max_attempts=max_attempts)
    if claim is None:
        return False
    # Disposable fixtures only; not durable delivery, archival evidence or real mail.
    with tempfile.TemporaryDirectory(prefix='shop-probe-') as directory:
        with LocalStorage(Path(directory).resolve()) as storage:
            key = storage.put(b'synthetic-probe')
            if storage.get(key) != b'synthetic-probe':
                raise ValueError('Synthetic storage round-trip failed')
            mail = CaptureMail()
            mail.send(MailRequest(claim.effect_id, 'probe@synthetic.invalid', storage.get(key)))
            if len(mail.messages) != 1:
                raise ValueError('Synthetic mail capture failed')
    result = perform_fake_probe(ProbeRequest(claim.effect_id))
    complete_probe(claim, result)
    return True
