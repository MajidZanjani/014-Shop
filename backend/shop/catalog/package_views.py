"""Private local package pages; bearer material stays in POST bodies only."""
from pathlib import Path
import json
import re
import uuid
from django.conf import settings
from django.db import transaction
from django.http import HttpResponse,HttpResponseRedirect
from django.shortcuts import render
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_http_methods,require_GET
from shop.access.staff_auth import staff_credential
from shop.adapters.evidence_archive import PreparedArchive,ArchiveError
from shop.payments.bank_contract import BankError
from . import checkout,checkout_payment as payment,private_packages as packages
from .models import SyntheticDeliveryStaffGrant,SyntheticPackageRevision
from .cart_editor import private,canonical_uuid
from .cart_views import reply
from .views import local_customer,unique_object


def archive_root():
    root=getattr(settings,'LOCAL_CHECKOUT_ARCHIVE_ROOT',None)
    if not root:raise checkout.CheckoutError('local_archive_unavailable',503)
    return Path(root)


def data(request,fields):
    if int(request.META.get('CONTENT_LENGTH') or 0)>1024:raise ValueError()
    if request.content_type=='application/json':
        raw=request.read(1025)
        if len(raw)>1024:raise ValueError()
        value=json.loads(raw,object_pairs_hook=unique_object,parse_constant=lambda _:(_ for _ in ()).throw(ValueError()))
    else:
        if request.content_type!='application/x-www-form-urlencoded' or len(request.body)>1024:raise ValueError()
        if any(len(request.POST.getlist(key))!=1 for key in request.POST):raise ValueError()
        value={k:v for k,v in request.POST.items() if k!='csrfmiddlewaretoken'}
    if not isinstance(value,dict) or set(value)!=set(fields) or any(not isinstance(v,str) for v in value.values()):raise ValueError()
    return value


def cursor(request):
    if set(request.GET)-{'before'} or any(len(request.GET.getlist(k))!=1 for k in request.GET):raise ValueError()
    raw=request.GET.get('before')
    if raw is None:return None
    if re.fullmatch(r'[1-9][0-9]{0,18}',raw) is None or int(raw)>9223372036854775807:raise ValueError()
    return int(raw)


def summary(row):
    return {'id':str(row.identity),'stage':row.stage,'version':row.version,'fixture':row.payload['fixture'],
            'entitlement_id':str(row.entitlement_id),'artifacts':sorted(row.payload['artifacts']),
            'actual_delivery':False,'effects_authorized':False}


def error_response(error):
    if isinstance(error,checkout.CheckoutError):return private(reply({'error':str(error)},error.status))
    if isinstance(error,BankError):return private(reply({'error':'unavailable'},404))
    if isinstance(error,(ArchiveError,OSError)):return private(reply({'error':'archive_unavailable'},503))
    return private(reply({'error':'invalid_request'},400))


@require_GET
def package_page(request,identity):
    denied=local_customer(request)
    if denied is not None:return private(denied)
    try:
        before=cursor(request)
        with PreparedArchive(archive_root()) as archive,transaction.atomic(durable=True):
            payment.locked(request.user,identity)
            query=SyntheticPackageRevision.objects.filter(entitlement__fulfilment__acceptance__checkout_id=identity).order_by('-pk')
            if before:query=query.filter(pk__lt=before)
            rows=list(query[:21]);items=[]
            for row in rows[:20]:
                line=packages.line_locked(request.user,identity,row.entitlement_id,archive)
                packages.retained(row,line,archive);items.append(summary(row))
        value={'packages':items,'next_before':rows[19].pk if len(rows)>20 else None}
        if request.headers.get('Accept')=='application/json':return private(reply(value))
        return private(render(request,'catalog/private_packages.html',value|{'checkout_id':str(identity)}))
    except (checkout.CheckoutError,BankError,ArchiveError,OSError,ValueError,TypeError,UnicodeError,RecursionError) as error:return error_response(error)


@require_http_methods(['POST'])
@sensitive_post_parameters()
def package_access(request,identity,package_id):
    denied=local_customer(request)
    if denied is not None:return private(denied)
    try:
        if request.GET:raise ValueError()
        value=data(request,{'artifact'})
        with PreparedArchive(archive_root()) as archive:token=packages.issue(request,identity,package_id,value['artifact'],archive)
        if request.content_type=='application/json':return private(reply({'token':token,'expires_in_seconds':packages.LIFETIME}))
        return private(render(request,'catalog/package_download.html',{'token':token,'checkout_id':str(identity),'package_id':str(package_id)}))
    except (checkout.CheckoutError,BankError,ArchiveError,OSError,ValueError,TypeError,UnicodeError,RecursionError) as error:return error_response(error)


@require_http_methods(['POST'])
@sensitive_post_parameters()
def package_download(request,identity,package_id):
    denied=local_customer(request)
    if denied is not None:return private(denied)
    try:
        if request.GET:raise ValueError()
        value=data(request,{'token'})
        with PreparedArchive(archive_root()) as archive:name,body=packages.download(request,identity,package_id,value['token'],archive)
        response=HttpResponse(body,content_type='application/octet-stream')
        response['Content-Disposition']='attachment; filename="'+name+'"'
        response['X-Content-Type-Options']='nosniff'
        return private(response)
    except (checkout.CheckoutError,BankError,ArchiveError,OSError,ValueError,TypeError,UnicodeError,RecursionError) as error:return error_response(error)


@require_GET
def delivery_queue(request):
    if staff_credential(request,recent=True) is None:return private(reply({'error':'recent_staff_mfa_required'},403))
    try:
        before=cursor(request)
        query=SyntheticDeliveryStaffGrant.objects.filter(user=request.user).order_by('-pk')
        if before:query=query.filter(pk__lt=before)
        rows=list(query[:21]);items=[{'entitlement_id':str(row.entitlement_id)} for row in rows[:20]]
        return private(render(request,'catalog/private_packages.html',{'staff':True,'assignments':items,'next_before':rows[19].pk if len(rows)>20 else None}))
    except (ValueError,TypeError) as error:return error_response(error)


@require_http_methods(['GET','POST'])
@sensitive_post_parameters()
def delivery_page(request,identity):
    if staff_credential(request,recent=True) is None:return private(reply({'error':'recent_staff_mfa_required'},403))
    scope=SyntheticDeliveryStaffGrant.objects.select_related('entitlement__fulfilment__acceptance__checkout__owner').filter(user=request.user,entitlement_id=identity).first()
    if scope is None:return private(reply({'error':'not_found'},404))
    checkout_row=scope.entitlement.fulfilment.acceptance.checkout
    try:
        before=cursor(request) if request.method=='GET' else None
        if request.method=='POST':
            if request.GET:raise ValueError()
            value=data(request,{'request_id','stage','fixture'})
            key=canonical_uuid(value['request_id'])
            with PreparedArchive(archive_root()) as archive:
                packages.release(request,checkout_row.owner,checkout_row.pk,identity,key,value['stage'],value['fixture'],archive)
            response=HttpResponseRedirect(request.path);response.status_code=303;return private(response)
        with PreparedArchive(archive_root()) as archive,transaction.atomic(durable=True):
            packages.staff_locked(request)
            line=packages.line_locked(checkout_row.owner,checkout_row.pk,identity,archive)
            packages.staff_locked(request,line)
            query=SyntheticPackageRevision.objects.filter(entitlement=line).order_by('-pk')
            if before:query=query.filter(pk__lt=before)
            rows=list(query[:21])
            for row in rows[:20]:packages.retained(row,line,archive)
            context={'staff':True,'entitlement_id':str(identity),'packages':[summary(row) for row in rows[:20]],
                'next_before':rows[19].pk if len(rows)>20 else None,'request_id':str(uuid.uuid4()),'fixtures':packages.FIXTURES,
                'later_reference_design':line.snapshot['later_reference_design']}
        return private(render(request,'catalog/private_packages.html',context))
    except (checkout.CheckoutError,BankError,ArchiveError,OSError,ValueError,TypeError,UnicodeError,RecursionError) as error:return error_response(error)
