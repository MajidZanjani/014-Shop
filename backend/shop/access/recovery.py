"""Access generation fence and disposable-synthetic recovery transitions.

Not a production restore/reopening adapter: external effects quarantine,
revocations, actual MFA recovery codes and off-host custody remain separate gates.
"""
import re
import uuid
from django.conf import settings
from django.contrib.sessions.models import Session
from django.db import connection,transaction
from django.db.models import Func,UUIDField
from django.utils import timezone
from .models import AccessEpoch,LocalAccessRecoveryOperation,StaffChallenge,StaffCredential,VerificationChallenge

SESSION_EPOCH='shop_access_epoch'

class AccessRecoveryError(ValueError):
    pass

def recovery_held():
    return AccessEpoch.objects.filter(pk=1,quarantined=True).exists()

def current_session_epoch(request):
    marker=request.session.get(SESSION_EPOCH)
    if not isinstance(marker,str):return False
    try:value=uuid.UUID(marker)
    except ValueError:return False
    return AccessEpoch.objects.filter(pk=1,value=value,quarantined=False).exists()

def stamp_session_epoch(sender,request,user,**kwargs):
    # Deliberate login (including trusted fixtures), never an anonymous GET.
    epoch,_=AccessEpoch.objects.get_or_create(pk=1)
    request.session.pop(SESSION_EPOCH,None)
    if not epoch.quarantined:request.session[SESSION_EPOCH]=str(epoch.value)

def _uuid(value):
    try:return uuid.UUID(str(value))
    except (ValueError,TypeError,AttributeError):raise AccessRecoveryError('invalid_request') from None

def local_recovery_operation(*,action,request_id,expected_database,basis_reset=None):
    """Fixture-only transition, requiring the exact disposable test database.

    Release represents synthetic fixture reconciliation only. It cannot authorize
    actual recovery or reopen a production/bank-sandbox app.
    """
    if (settings.SHOP_ENV not in ('local','synthetic') or settings.LIVE_PAYMENTS_ENABLED
            or any(getattr(settings,key,None)!='fake' for key in ('PAYMENT_ADAPTER','MAIL_ADAPTER','STORAGE_ADAPTER'))
            or settings.SESSION_ENGINE!='django.contrib.sessions.backends.db' or connection.vendor!='postgresql'):
        raise AccessRecoveryError('local_recovery_unavailable')
    request_id=_uuid(request_id)
    if action not in ('quarantine','release') or (action=='quarantine' and basis_reset is not None) or (action=='release' and basis_reset is None):
        raise AccessRecoveryError('invalid_request')
    basis_reset=_uuid(basis_reset) if basis_reset is not None else None
    if (not isinstance(expected_database,str) or re.fullmatch(r'(?:test_){1,2}[0-9a-f]{24}',expected_database) is None
            or expected_database!=connection.settings_dict['NAME'] or connection.settings_dict['USER']!='shop_test'):
        raise AccessRecoveryError('database_identity_mismatch')
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute('SELECT current_database(),current_user')
            if cursor.fetchone()!=(expected_database,'shop_test'):
                raise AccessRecoveryError('database_identity_mismatch')
        AccessEpoch.objects.get_or_create(pk=1)
        epoch=AccessEpoch.objects.select_for_update().get(pk=1)
        old=LocalAccessRecoveryOperation.objects.filter(pk=request_id).first()
        if old is not None:
            if old.action!=action or old.basis_reset!=basis_reset:raise AccessRecoveryError('request_conflict')
            operation=old
        else:
            if action=='release' and (not epoch.quarantined or epoch.active_reset!=basis_reset):
                raise AccessRecoveryError('recovery_changed')
            counts={'customer_challenges':VerificationChallenge.objects.filter(consumed_at__isnull=True).update(consumed_at=timezone.now()),
                'staff_challenges':StaffChallenge.objects.filter(consumed_at__isnull=True).update(consumed_at=timezone.now()),
                'staff_credentials':StaffCredential.objects.update(generation=Func(function='gen_random_uuid',output_field=UUIDField()))}
            counts['sessions']=Session.objects.all().delete()[0]
            epoch.value=uuid.uuid4();epoch.quarantined=action=='quarantine'
            epoch.active_reset=request_id if epoch.quarantined else None
            epoch.save(update_fields=['value','quarantined','active_reset'])
            operation=LocalAccessRecoveryOperation.objects.create(id=request_id,action=action,basis_reset=basis_reset,epoch=epoch.value,counts=counts)
        return {'operation_id':str(operation.pk),'action':operation.action,'invalidated':dict(operation.counts),
            'currently_quarantined':epoch.quarantined,'evidence_class':'local-synthetic','actual_recovery_qualified':False}
