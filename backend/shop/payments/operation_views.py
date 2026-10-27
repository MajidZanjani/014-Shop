"""Private synthetic finance actions; exact staff scope/recent MFA, no customer authority."""
import uuid
from django.shortcuts import render
from django.views.decorators.http import require_GET,require_http_methods
from django.views.decorators.debug import sensitive_post_parameters
from django.core.exceptions import ObjectDoesNotExist
from shop.access.staff_auth import staff_credential
from shop.adapters.evidence_archive import PreparedArchive,ArchiveError
from shop.catalog import checkout
from shop.catalog.cart_editor import private,canonical_uuid
from shop.catalog.cart_views import reply
from shop.catalog.licence_change_views import raw,redirect
from shop.catalog.package_views import archive_root,cursor,error_response
from . import operations as service
from .bank_contract import BankError
from .models import SyntheticPaymentStaffGrant as StaffGrant,SyntheticPaymentOperation as Operation


@require_GET
def queue(request):
    if staff_credential(request,recent=True) is None:return private(reply({'error':'recent_staff_mfa_required'},403))
    try:
        service.synthetic_bank.guard();before=cursor(request)
        rows=StaffGrant.objects.filter(user=request.user).order_by('-pk')
        if before:rows=rows.filter(pk__lt=before)
        rows=list(rows[:21])
        return private(render(request,'access/payments.html',{'assignments':rows[:20],'next_before':rows[19].pk if len(rows)>20 else None}))
    except (ValueError,TypeError,BankError) as error:return error_response(error)


@require_http_methods(['GET','POST'])
@sensitive_post_parameters()
def detail(request,identity):
    if staff_credential(request,recent=True) is None:return private(reply({'error':'recent_staff_mfa_required'},403))
    scope=StaffGrant.objects.filter(pk=identity,user=request.user).first()
    if scope is None:return private(reply({'error':'not_found'},404))
    try:
        if request.GET:raise ValueError()
        with PreparedArchive(archive_root()) as archive:
            row=Operation.objects.filter(acceptance_id=scope.acceptance_id,kind=scope.kind).first()
            if request.method=='POST':
                value=raw(request);action=value.get('action')
                if action=='prepare' and set(value)=={'action','request_id'}:
                    row=service.prepare(request,scope.acceptance_id,scope.kind,canonical_uuid(value['request_id']),archive)
                elif action in ('dispatch','reconcile') and set(value)=={'action'} and row is not None:
                    row=getattr(service,action)(request,row.pk,archive)
                else:raise ValueError()
                if request.content_type!='application/json':return redirect(request.path)
            state=service.inspect(request,row.pk,archive) if row else None
        context={'assigned':True,'kind':scope.kind,'operation':state,'request_id':str(uuid.uuid4())}
        if request.content_type=='application/json' or request.headers.get('Accept')=='application/json':return private(reply(context))
        return private(render(request,'access/payments.html',context))
    except TimeoutError:return private(reply({'error':'payment_operation_uncertain_use_lookup'},409))
    except ObjectDoesNotExist:return private(reply({'error':'not_found'},404))
    except (checkout.CheckoutError,BankError,ArchiveError,OSError,ValueError,TypeError,UnicodeError) as error:return error_response(error)
