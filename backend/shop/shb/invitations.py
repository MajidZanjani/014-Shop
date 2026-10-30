"""Reusable bearer entry, calendar expiry and current-state session authority."""
import calendar
from datetime import datetime,timedelta,timezone as utc_timezone
import hashlib
import re
import secrets
from zoneinfo import ZoneInfo
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from shop.access.models import AccessEpoch
from shop.access.recovery import SESSION_EPOCH,current_session_epoch
from shop.access.startup import restore_startup_pending
from .models import Invitation

TBILISI=ZoneInfo('Asia/Tbilisi')
now=timezone.now


def six_month_expiry(created):
    if not isinstance(created,datetime) or timezone.is_naive(created):raise ValueError('aware_creation_required')
    local=created.astimezone(TBILISI)
    index=local.year*12+local.month-1+6;year,month=divmod(index,12);month+=1
    return local.replace(year=year,month=month,day=min(local.day,calendar.monthrange(year,month)[1])).astimezone(utc_timezone.utc)


def fixture_guard():
    if (settings.SHOP_ENV not in ('local','synthetic') or not getattr(settings,'SHB_SYNTHETIC_FIXTURE',False)
            or settings.LIVE_PAYMENTS_ENABLED or any(getattr(settings,key,None)!='fake' for key in ('PAYMENT_ADAPTER','MAIL_ADAPTER','STORAGE_ADAPTER'))):
        raise ValueError('synthetic_shb_unavailable')


def issue_fixture(*,customer,issuer,company_name,project_reference='',fpga_eligible=True,asic_allowed=True,created_at=None):
    """Explicit disposable fixture only; not an actual policy/eligibility issuer."""
    fixture_guard()
    if (not customer.is_active or customer.is_staff or not issuer.is_active or not issuer.is_staff
            or type(company_name) is not str or not 1<=len(company_name)<=200):raise ValueError('invalid_fixture_scope')
    created=created_at or now();token=secrets.token_urlsafe(32)
    with transaction.atomic():
        AccessEpoch.objects.get_or_create(pk=1)
        row=Invitation.objects.create(token_digest=hashlib.sha256(token.encode('ascii')).hexdigest(),
            customer=customer,issuer=issuer,company_name=company_name,project_reference=project_reference,
            eligibility_reference='synthetic-eligibility-v1',fpga_eligible=fpga_eligible,asic_allowed=asic_allowed,
            created_at=created,expires_at=six_month_expiry(created))
    return row,token


def eligible(row,at=None):
    at=at or now()
    return bool(row and row.revoked_at is None and row.created_at<=at<row.expires_at
        and row.customer.is_active and not row.customer.is_staff)


def exchange(request,token):
    if not re.fullmatch(r'[A-Za-z0-9_-]{43}',token):return None
    row=Invitation.objects.select_related('customer').filter(token_digest=hashlib.sha256(token.encode('ascii')).hexdigest()).first()
    epoch=AccessEpoch.objects.filter(pk=1,quarantined=False).first()
    if not eligible(row) or epoch is None or restore_startup_pending(epoch):return None
    request.session.cycle_key()
    # A new entry never logs in as the invited company or adopts entered email.
    for key in tuple(request.session.keys()):
        if key.startswith('shb_'):request.session.pop(key,None)
    at=now();limit=min(row.expires_at,at+timedelta(seconds=settings.SESSION_COOKIE_AGE))
    request.session['shb_invitation']=str(row.pk)
    request.session['shb_session_until']=limit.isoformat()
    request.session[SESSION_EPOCH]=str(epoch.value)
    request.session.set_expiry(limit)
    return row


def current(request,*,lock=False):
    if not current_session_epoch(request,lock=lock):return None
    identity=request.session.get('shb_invitation');deadline=request.session.get('shb_session_until')
    try:
        import uuid
        identity=uuid.UUID(identity);deadline=datetime.fromisoformat(deadline)
        if timezone.is_naive(deadline) or now()>=deadline:return None
    except (ValueError,TypeError,AttributeError):return None
    rows=Invitation.objects.select_related('customer').filter(pk=identity)
    if lock:rows=rows.select_for_update(of=('self',))
    row=rows.first()
    return row if eligible(row) and deadline<=row.expires_at else None
