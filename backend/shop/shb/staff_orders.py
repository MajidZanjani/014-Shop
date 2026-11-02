"""Assigned paid-order visibility for manual support handoff; no usage controls."""
from pathlib import Path
import uuid
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.shortcuts import render
from django.views.decorators.http import require_GET
from shop.access.recovery import current_session_epoch
from shop.access.staff_auth import staff_credential
from shop.access.models import StaffCredential
from shop.access.views import reply
from shop.adapters.evidence_archive import PreparedArchive,ArchiveError
from shop.catalog.checkout import CheckoutError
from . import checkout,paid_orders
from .errors import ShbError
from .models import PaidOrderGrant,PurchaseNoticeDelivery
from .staff_views import private


def credential(request):
    if not current_session_epoch(request,lock=True):raise ShbError('recent_staff_mfa_required',403)
    admitted=staff_credential(request,recent=True)
    if admitted is None:raise ShbError('recent_staff_mfa_required',403)
    row=StaffCredential.objects.select_for_update().filter(pk=admitted.pk,enabled=True,generation=admitted.generation).first()
    if row is None or staff_credential(request,recent=True) is None:raise ShbError('recent_staff_mfa_required',403)


def error(value):return private(reply({'error':getattr(value,'code',str(value))},getattr(value,'status',503)))


@require_GET
def orders(request):
    try:
        checkout.guard()
        with transaction.atomic(durable=True):
            credential(request)
            scope=PaidOrderGrant.objects.filter(user=request.user)
            if request.GET:
                if set(request.GET)!={'before'} or len(request.GET.getlist('before'))!=1:raise ShbError('invalid_cursor',400)
                try:
                    raw=request.GET['before'];key=uuid.UUID(raw)
                    if str(key)!=raw:raise ValueError()
                except (ValueError,TypeError,AttributeError):raise ShbError('invalid_cursor',400) from None
                anchor=scope.select_related('order').filter(order_id=key).first()
                if anchor is None:raise ShbError('not_found',404)
                scope=scope.filter(Q(order__created_at__lt=anchor.order.created_at)|Q(order__created_at=anchor.order.created_at,order_id__lt=key))
            selected=list(scope.select_related('order').order_by('-order__created_at','-order_id')[:21])
            grants=selected[:20];older=str(grants[-1].order_id) if len(selected)>20 else None
            rows=[{'id':str(grant.order_id),'order_reference':grant.order.payload['order_reference'],
                'variant':grant.order.payload['purchase']['variant_label'],
                'hours_purchased':grant.order.payload['purchase']['hours_purchased']} for grant in grants]
        if 'text/html' in request.headers.get('Accept',''):
            return private(render(request,'shb/staff_orders.html',{'orders':rows,'older':older}))
        return private(reply({'orders':rows,'limit':20,'older':older}))
    except (ShbError,CheckoutError) as failure:return error(failure)


@require_GET
def detail(request,identity):
    if request.GET:return error(ShbError('unexpected_query',400))
    try:
        checkout.guard()
        root=settings.LOCAL_CHECKOUT_ARCHIVE_ROOT
        if not root:raise ShbError('recovery_evidence_unavailable',503)
        with transaction.atomic(durable=True):
            credential(request)
            grant=PaidOrderGrant.objects.filter(user=request.user,order_id=identity).select_related('order__acceptance__checkout__owner').first()
            if grant is None:raise ShbError('not_found',404)
            order=grant.order
            with PreparedArchive(Path(root)) as archive:
                accepted,capture=paid_orders.accepted_locked(order.acceptance.checkout.owner,order.acceptance.checkout_id,archive)
                if not PaidOrderGrant.objects.select_for_update().filter(pk=grant.pk).exists():raise ShbError('not_found',404)
                paid_orders.retained(order,accepted,capture,archive)
            notice=PurchaseNoticeDelivery.objects.get(order=order)
            value={**order.payload,'payment_state':accepted.attempt.provider_status,'notice_state':notice.state,'id':str(order.pk)}
        if 'text/html' in request.headers.get('Accept',''):
            return private(render(request,'shb/staff_order.html',value))
        return private(reply(value))
    except (ShbError,CheckoutError) as failure:return error(failure)
    except (ArchiveError,OSError,ValueError):return error(ShbError('recovery_evidence_unavailable',503))
