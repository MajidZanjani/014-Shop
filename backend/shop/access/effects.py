"""Durable fake-only call admission, without locks held across adapter execution.

A quarantine closes admission, not calls already in progress. Missing exits stay
unfinished indefinitely. An exit proves only that a local call scope unwound;
it does not confirm money, delivery, reconciliation or actual recovery.
"""
from functools import wraps
from uuid import UUID
from django.conf import settings
from django.db import connection,transaction
from django.db.models.functions import Now
from .models import AccessEpoch,LocalEffectAdmission,LOCAL_EFFECT_KINDS
from .startup import restore_startup_pending


class RecoveryEffectError(ValueError):
    pass


_RAISE=object()


def _guard():
    if (settings.SHOP_ENV not in ('local','synthetic') or settings.LIVE_PAYMENTS_ENABLED
            or any(getattr(settings,key,None)!='fake' for key in ('PAYMENT_ADAPTER','MAIL_ADAPTER','STORAGE_ADAPTER'))
            or connection.vendor!='postgresql'):
        raise RecoveryEffectError('local_effects_unavailable')
    if connection.in_atomic_block or not connection.get_autocommit():
        raise RecoveryEffectError('effect_transaction_active')


def _begin(kind, *, expected_epoch=None):
    _guard()
    if kind not in LOCAL_EFFECT_KINDS:raise RecoveryEffectError('invalid_effect_kind')
    if expected_epoch is not None and type(expected_epoch) is not UUID:raise RecoveryEffectError('recovery_effects_pending')
    with transaction.atomic(durable=True):
        epoch=AccessEpoch.objects.select_for_update().filter(pk=1).first()
        if epoch is None:
            if expected_epoch is not None or restore_startup_pending(None):raise RecoveryEffectError('recovery_effects_pending')
            AccessEpoch.objects.get_or_create(pk=1)
            epoch=AccessEpoch.objects.select_for_update().get(pk=1)
        if (epoch.quarantined or restore_startup_pending(epoch)
                or expected_epoch is not None and epoch.value!=expected_epoch):raise RecoveryEffectError('recovery_effects_pending')
        return LocalEffectAdmission.objects.create(kind=kind,epoch=epoch.value).pk


def _finish(identity,status):
    _guard()
    with transaction.atomic(durable=True):
        if LocalEffectAdmission.objects.filter(pk=identity,finished_at__isnull=True).update(finished_at=Now(),exit_status=status)!=1:
            raise RecoveryEffectError('effect_exit_conflict')


def local_effect(kind,*,guard=None,error=RecoveryEffectError,held_result=_RAISE,require_current_epoch=False,epoch_kwarg=None):
    """Admit before the existing claim/mutation; record exit after its scope ends.

    Nested boundaries admit separately and therefore recheck a new quarantine.
    A denial after a one-way claim leaves that claim uncertain, never retryable.
    Authentication additionally requires its original unheld epoch on return.
    An optional dispatch keyword binds admission to its originating epoch.
    """
    if kind not in LOCAL_EFFECT_KINDS:raise RecoveryEffectError('invalid_effect_kind')
    def decorate(function):
        @wraps(function)
        def wrapped(*args,**kwargs):
            if guard is not None:guard()
            expected=kwargs.get(epoch_kwarg) if epoch_kwarg is not None else None
            try:identity=_begin(kind) if expected is None else _begin(kind,expected_epoch=expected)
            except RecoveryEffectError as failure:
                if str(failure)=='recovery_effects_pending' and held_result is not _RAISE:return held_result
                raise error(str(failure)) from None
            status='raised'
            try:
                epoch=LocalEffectAdmission.objects.values_list('epoch',flat=True).get(pk=identity) if require_current_epoch else None
                result=function(*args,**kwargs)
                if require_current_epoch:
                    current=AccessEpoch.objects.filter(pk=1,value=epoch,quarantined=False).first()
                    if current is None or restore_startup_pending(current):raise RecoveryEffectError('recovery_effects_pending')
                status='returned'
                return result
            finally:
                # A process loss or failed commit leaves the admission unfinished.
                # Never expire it or infer permission for another adapter call.
                _finish(identity,status)
        return wrapped
    return decorate


def drain_state(*,quarantined):
    """Caller holds the epoch lock; concurrent exits can only reduce this count."""
    unfinished=LocalEffectAdmission.objects.filter(finished_at__isnull=True).count()
    return {'unfinished_effects':unfinished,'local_effects_drained':quarantined and unfinished==0}


def inspect_local_effects():
    """Read-only internal fixture inspection; never initializes the epoch."""
    _guard()
    with transaction.atomic(durable=True):
        epoch=AccessEpoch.objects.select_for_update().filter(pk=1).first()
        held=bool(epoch and epoch.quarantined)
        return {'currently_quarantined':held,**drain_state(quarantined=held),
            'startup_recovery_pending':restore_startup_pending(epoch),
            'evidence_class':'local-synthetic','actual_recovery_qualified':False,'retry_authorized':False}
