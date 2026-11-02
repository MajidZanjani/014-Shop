"""Native/JSON staff discount issuance; raw code appears only on a successful POST."""
import uuid
from pathlib import Path
from django.conf import settings
from django.db import transaction
from django.shortcuts import render
from django.views.decorators.http import require_GET,require_http_methods
from django.views.decorators.debug import sensitive_post_parameters,sensitive_variables
from shop.access.staff_auth import payload
from shop.access.views import reply
from shop.adapters.evidence_archive import PreparedArchive,ArchiveError
from shop.catalog.checkout import CheckoutError
from . import checkout,discount_issuance as service
from .errors import ShbError
from .models import DiscountIssueGrant,DiscountIssue
from .staff_orders import credential,error
from .staff_views import private


def summary(scope):
    from decimal import Decimal
    return {'id':str(scope.pk),'percentage_bps':scope.percentage_bps,
        'percentage':format(Decimal(scope.percentage_bps)/100,'f'),
        'fpga_allowed':scope.fpga_allowed,'asic_allowed':scope.asic_allowed,
        'use_limit':scope.use_limit,'claim_period_days':scope.claim_period_days,'enabled':scope.enabled}


def issue_summary(event):
    return {'id':str(event.pk),'created_at':event.created_at.isoformat(),
        'expires_at':event.payload['discount']['expires_at'],
        'published':event.discount_id is not None}


@require_GET
def queue(request):
    try:
        checkout.guard()
        with transaction.atomic(durable=True):
            credential(request);scopes=DiscountIssueGrant.objects.filter(user=request.user)
            if request.GET:
                if set(request.GET)!={'before'} or len(request.GET.getlist('before'))!=1:raise ShbError('invalid_cursor',400)
                raw=request.GET['before'];key=uuid.UUID(raw)
                if str(key)!=raw:raise ValueError()
                if not scopes.filter(scope_id=key).exists():raise ShbError('not_found',404)
                scopes=scopes.filter(scope_id__lt=key)
            selected=list(scopes.select_related('scope').order_by('-scope_id')[:21])
            rows=[summary(grant.scope) for grant in selected[:20]]
            value={'scopes':rows,'older':rows[-1]['id'] if len(selected)>20 else None,'limit':20}
        if 'text/html' in request.headers.get('Accept',''):return private(render(request,'shb/staff_discount_scopes.html',value))
        return private(reply(value))
    except (ShbError,CheckoutError) as failure:return error(failure)
    except (ValueError,TypeError,AttributeError):return error(ShbError('invalid_cursor',400))


@require_http_methods(['GET','POST'])
@sensitive_post_parameters()
@sensitive_variables()
def detail(request,identity):
    try:
        checkout.guard()
        if request.GET:raise ShbError('unexpected_query',400)
        if request.method=='POST':
            value=payload(request,{'request_id','reason'},maximum_bytes=8192)
            root=settings.LOCAL_CHECKOUT_ARCHIVE_ROOT
            if not root:raise ShbError('recovery_evidence_unavailable',503)
            with PreparedArchive(Path(root)) as archive:event,code=service.record(request,identity,value,archive)
            value={'issue':issue_summary(event),'discount_code':code,**service.FLAGS}
            if request.content_type=='application/x-www-form-urlencoded':
                return private(render(request,'shb/staff_discount_issued.html',value,status=201 if code else 200))
            return private(reply(value,201 if code else 200))
        with transaction.atomic(durable=True):
            scope=service.authorized(request,identity)
            events=list(DiscountIssue.objects.filter(scope=scope).order_by('-created_at','-id')[:20])
            value={'scope':summary(scope),'issues':[issue_summary(event) for event in events],
                'request_id':str(uuid.uuid4())}
        if 'text/html' in request.headers.get('Accept',''):return private(render(request,'shb/staff_discount_scope.html',value))
        return private(reply(value))
    except (ShbError,CheckoutError) as failure:return error(failure)
    except (ArchiveError,OSError):return error(ShbError('recovery_evidence_unavailable',503))
    except (ValueError,TypeError,UnicodeError,RecursionError,KeyError):return error(ShbError('invalid_request',400))
