"""Extend the existing private staff app; no bearer reveal, replacement or mail."""
from pathlib import Path
import uuid
from django.conf import settings
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.decorators.http import require_GET,require_http_methods
from django.views.decorators.debug import sensitive_post_parameters
from shop.access.staff_auth import payload
from shop.access.views import reply
from shop.adapters.evidence_archive import PreparedArchive,ArchiveError
from shop.catalog.checkout import CheckoutError
from . import checkout,invitation_admin as service
from .errors import ShbError
from .models import InvitationStaffGrant,InvitationRevocation
from .staff_orders import credential,error
from .staff_views import private


def summary(row):
    return {'id':str(row.pk),'company_name':row.company_name,'created_at':row.created_at.isoformat(),
        'expires_at':row.expires_at.isoformat(),'revoked_at':row.revoked_at.isoformat() if row.revoked_at else None,
        'fpga_eligible':row.fpga_eligible,'asic_allowed':row.asic_allowed}


@require_GET
def queue(request):
    try:
        checkout.guard()
        with transaction.atomic(durable=True):
            credential(request)
            scopes=InvitationStaffGrant.objects.filter(user=request.user)
            if request.GET:
                if set(request.GET)!={'before'} or len(request.GET.getlist('before'))!=1:raise ShbError('invalid_cursor',400)
                raw=request.GET['before'];key=uuid.UUID(raw)
                if str(key)!=raw:raise ValueError()
                if not scopes.filter(invitation_id=key).exists():raise ShbError('not_found',404)
                scopes=scopes.filter(invitation_id__lt=key)
            selected=list(scopes.select_related('invitation').order_by('-invitation_id')[:21])
            rows=[summary(scope.invitation) for scope in selected[:20]]
            value={'invitations':rows,'limit':20,'older':rows[-1]['id'] if len(selected)>20 else None}
        if 'text/html' in request.headers.get('Accept',''):return private(render(request,'shb/staff_invitations.html',value))
        return private(reply(value))
    except (ShbError,CheckoutError) as failure:return error(failure)
    except (ValueError,TypeError,AttributeError):return error(ShbError('invalid_cursor',400))


@require_http_methods(['GET','POST'])
@sensitive_post_parameters()
def detail(request,identity):
    try:
        checkout.guard()
        if request.GET:raise ShbError('unexpected_query',400)
        root=settings.LOCAL_CHECKOUT_ARCHIVE_ROOT
        if not root:raise ShbError('recovery_evidence_unavailable',503)
        with PreparedArchive(Path(root)) as archive:
            if request.method=='POST':
                value=payload(request,{'request_id','reason'},maximum_bytes=8192)
                saved,created=service.record(request,identity,value,archive)
                if request.content_type=='application/x-www-form-urlencoded':
                    response=HttpResponseRedirect(request.path);response.status_code=303;return private(response)
                return private(reply({'id':str(saved.pk),'invitation_id':str(identity),'revoked_at':saved.revoked_at.isoformat(),**service.FLAGS},201 if created else 200))
            with transaction.atomic(durable=True):
                row=service.authorized(request,identity)
                event=InvitationRevocation.objects.select_related('invitation').filter(invitation=row).first()
                if event:service.retained(event,archive)
                value={'invitation':summary(row),'revocation':event.payload if event else None,'request_id':str(uuid.uuid4())}
        if 'text/html' in request.headers.get('Accept',''):return private(render(request,'shb/staff_invitation.html',value))
        # Audit attribution/reason is scoped; secret/digest and customer history are absent.
        return private(reply(value))
    except (ShbError,CheckoutError) as failure:return error(failure)
    except (ArchiveError,OSError):return error(ShbError('recovery_evidence_unavailable',503))
    except (ValueError,TypeError,UnicodeError,RecursionError,KeyError):return error(ShbError('invalid_request',400))
