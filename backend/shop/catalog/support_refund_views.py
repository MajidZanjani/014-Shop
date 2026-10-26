"""Private local refund-review requests; no refund execution route."""
import uuid
from django.db import transaction
from django.shortcuts import render
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_GET,require_http_methods
from shop.access.staff_auth import staff_credential
from shop.adapters.evidence_archive import PreparedArchive,ArchiveError
from shop.payments import synthetic_bank
from shop.payments.bank_contract import BankError
from . import support_refunds as service,checkout
from .models import SyntheticSupportRefundCase as Case,SyntheticSupportRefundStaffGrant as StaffGrant
from .licence_change_views import raw,redirect
from .package_views import archive_root,cursor,error_response
from .cart_editor import private,canonical_uuid
from .cart_views import reply
from .views import local_customer

ERRORS=(checkout.CheckoutError,BankError,ArchiveError,OSError,ValueError,TypeError,UnicodeError,RecursionError)


def command(request,staff):
    value=raw(request)
    fields={'request_id','expected_revision','ledger_revision','decision'} if staff else {'request_id','seconds'}
    if set(value)!=fields or not isinstance(value['request_id'],str):raise ValueError()
    value['request_id']=canonical_uuid(value['request_id'])
    for key in ('expected_revision','ledger_revision') if staff else ('seconds',):
        # Refund quantities use the existing bounded integer-second resource limits.
        if request.content_type!='application/json':
            text=value[key]
            if not isinstance(text,str) or not text.isascii() or not text.isdecimal() or len(text)>19 or str(int(text))!=text:raise ValueError()
            value[key]=int(text)
        elif type(value[key]) is not int:raise ValueError()
    return value


def response(request,value,context=None,status=200):
    if request.content_type=='application/json' or request.headers.get('Accept')=='application/json':return private(reply(value,status))
    return private(render(request,'catalog/support_refunds.html',(context or {})|value,status=status))


@require_http_methods(['GET','POST'])
@sensitive_post_parameters()
def refunds(request,identity):
    denied=local_customer(request)
    if denied is not None:return private(denied)
    try:
        before=cursor(request) if request.method=='GET' else None
        with PreparedArchive(archive_root()) as archive:
            if request.method=='POST':
                if request.GET:raise ValueError()
                case=service.capture(request.user,identity,archive=archive,**command(request,False))
                if request.content_type!='application/json':return redirect(f'{request.path}{case.identity}/')
                return private(reply({'case_id':str(case.identity),'refund_authorized':False,'balance_hold_created':False,'effects_authorized':False,'evidence_class':'local-synthetic'},201))
            synthetic_bank.guard()
            with transaction.atomic(durable=True):
                grant,state=service.grant_locked(request.user,identity,archive)
                query=Case.objects.filter(fulfilment=grant).order_by('-pk')
                if before:query=query.filter(pk__lt=before)
                rows=list(query[:21])
                for row in rows[:20]:service.retained(row,row.identity,archive)
                value={'checkout_id':str(identity),'effects_authorized':False,'evidence_class':'local-synthetic','current_credit':state,'cases':[{'case_id':str(row.identity),'requested_seconds':row.payload['requested_seconds']} for row in rows[:20]],
                       'next_before':rows[19].pk if len(rows)>20 else None}
        return response(request,value,{'request_id':str(uuid.uuid4())})
    except ERRORS as error:return error_response(error)


@require_GET
def detail(request,identity,case_id):
    denied=local_customer(request)
    if denied is not None:return private(denied)
    try:
        before=cursor(request);synthetic_bank.guard()
        with PreparedArchive(archive_root()) as archive,transaction.atomic(durable=True):
            case,state=service.case_locked(request.user,identity,case_id,archive)
            value=service.summary(case,state,archive,before)
        return response(request,{'case':value,'checkout_id':str(identity),'next_before':value['next_before']})
    except ERRORS as error:return error_response(error)


@require_GET
def staff_refunds(request):
    if staff_credential(request,recent=True) is None:return private(reply({'error':'recent_staff_mfa_required'},403))
    try:
        before=cursor(request)
        query=StaffGrant.objects.filter(user=request.user).select_related('case').order_by('-pk')
        if before:query=query.filter(pk__lt=before)
        rows=list(query[:21]);value={'staff':True,'cases':[{'case_id':str(row.case.identity),'requested_seconds':row.case.payload['requested_seconds']} for row in rows[:20]],'next_before':rows[19].pk if len(rows)>20 else None}
        return response(request,value)
    except ERRORS as error:return error_response(error)


@require_http_methods(['GET','POST'])
@sensitive_post_parameters()
def staff_detail(request,identity):
    if staff_credential(request,recent=True) is None:return private(reply({'error':'recent_staff_mfa_required'},403))
    scope=StaffGrant.objects.select_related('case__fulfilment__acceptance__checkout__owner').filter(user=request.user,case__identity=identity).first()
    if scope is None:return private(reply({'error':'not_found'},404))
    saved=scope.case.fulfilment.acceptance.checkout
    try:
        before=cursor(request) if request.method=='GET' else None
        with PreparedArchive(archive_root()) as archive:
            if request.method=='POST':
                if request.GET:raise ValueError()
                service.review(request,saved.owner,saved.pk,identity,archive=archive,**command(request,True))
                if request.content_type!='application/json':return redirect(request.path)
            synthetic_bank.guard()
            with transaction.atomic(durable=True):
                service.staff_locked(request)
                case,state=service.case_locked(saved.owner,saved.pk,identity,archive);service.staff_locked(request,case)
                value=service.summary(case,state,archive,before)
        return response(request,{'staff':True,'case':value,'next_before':value['next_before']},{'request_id':str(uuid.uuid4()),'decisions':service.DECISIONS})
    except ERRORS as error:return error_response(error)
