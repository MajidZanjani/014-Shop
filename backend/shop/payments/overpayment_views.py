"""Recent-MFA assigned-pair investigation; no public intake or refund action."""
import uuid
from django.shortcuts import render
from django.views.decorators.http import require_GET,require_http_methods
from django.views.decorators.debug import sensitive_post_parameters
from shop.access.staff_auth import staff_credential
from shop.adapters.evidence_archive import PreparedArchive,ArchiveError
from shop.catalog import checkout
from shop.catalog.cart_editor import private,canonical_uuid
from shop.catalog.cart_views import reply
from shop.catalog.licence_change_views import raw,redirect
from shop.catalog.package_views import archive_root,cursor,error_response
from . import overpayments as service
from .bank_contract import BankError
from .models import SyntheticOverpaymentStaffGrant as StaffGrant,SyntheticOverpaymentCase as Case

ERRORS=(checkout.CheckoutError,BankError,ArchiveError,OSError,ValueError,TypeError,UnicodeError,RecursionError)


def response(request,value):
    if request.content_type=='application/json' or request.headers.get('Accept')=='application/json':return private(reply(value))
    return private(render(request,'access/overpayments.html',value))


@require_GET
def queue(request):
    if staff_credential(request,recent=True) is None:return private(reply({'error':'recent_staff_mfa_required'},403))
    try:
        service.notifications.guard();before=cursor(request)
        query=StaffGrant.objects.filter(user=request.user).order_by('-pk')
        if before:query=query.filter(pk__lt=before)
        rows=list(query[:21])
        return response(request,{'assignments':[{'id':row.pk} for row in rows[:20]],'next_before':rows[19].pk if len(rows)>20 else None})
    except ERRORS as error:return error_response(error)


@require_http_methods(['GET','POST'])
@sensitive_post_parameters()
def detail(request,identity):
    if staff_credential(request,recent=True) is None:return private(reply({'error':'recent_staff_mfa_required'},403))
    scope=StaffGrant.objects.filter(pk=identity,user=request.user).first()
    if scope is None:return private(reply({'error':'not_found'},404))
    try:
        before=cursor(request) if request.method=='GET' else None
        if request.method=='POST' and request.GET:raise ValueError()
        with PreparedArchive(archive_root()) as archive:
            if request.method=='POST':
                value=raw(request)
                if value=={'action':'capture'}:service.capture(request,scope.acceptance_id,scope.extra_attempt_id,archive)
                else:
                    if set(value)!={'action','request_id','expected_revision','decision'} or value['action']!='review':raise ValueError()
                    key=canonical_uuid(value['request_id']);revision=value['expected_revision']
                    if request.content_type!='application/json':
                        if not isinstance(revision,str) or not revision.isascii() or not revision.isdecimal() or len(revision)>4 or str(int(revision))!=revision:raise ValueError()
                        revision=int(revision)
                    service.review(request,scope.acceptance_id,scope.extra_attempt_id,key,revision,value['decision'],archive)
                if request.content_type!='application/json':return redirect(request.path)
            case=Case.objects.filter(acceptance_id=scope.acceptance_id,extra_attempt_id=scope.extra_attempt_id).first()
            state=service.inspect(request,scope.acceptance_id,scope.extra_attempt_id,archive,before) if case else None
        return response(request,{'assigned':True,'case':state,'request_id':str(uuid.uuid4()),'decisions':service.DECISIONS})
    except ERRORS as error:return error_response(error)
