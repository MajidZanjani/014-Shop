"""Private no-JavaScript licence-change request/review forms; no automatic rights or charges."""
import json
import re
import uuid
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_GET,require_http_methods
from shop.access.staff_auth import staff_credential
from shop.adapters.evidence_archive import PreparedArchive,ArchiveError
from shop.payments.bank_contract import BankError
from . import licence_changes as service,checkout,checkout_payment as payment
from .models import SyntheticLineEntitlement,SyntheticLicenceCase,SyntheticLicenceCaseEvent,SyntheticLicenceCaseStaffGrant
from .package_views import archive_root,cursor,error_response
from .cart_editor import private,canonical_uuid
from .cart_views import reply
from .views import local_customer,unique_object


def raw(request):
    if int(request.META.get('CONTENT_LENGTH') or 0)>2048:raise ValueError()
    if request.content_type=='application/json':
        body=request.read(2049)
        if len(body)>2048:raise ValueError()
        value=json.loads(body,object_pairs_hook=unique_object,parse_constant=lambda _:(_ for _ in ()).throw(ValueError()))
    else:
        if request.content_type!='application/x-www-form-urlencoded' or len(request.body)>2048:raise ValueError()
        if any(len(request.POST.getlist(key))!=1 for key in request.POST if key!='families'):raise ValueError()
        value={k:(request.POST.getlist(k) if k=='families' else v) for k,v in request.POST.items() if k!='csrfmiddlewaretoken'}
    if not isinstance(value,dict):raise ValueError()
    return value


def integer(value,api):
    if not api:
        if not isinstance(value,str) or re.fullmatch(r'0|[1-9][0-9]{0,6}',value) is None:raise ValueError()
        value=int(value)
    if type(value) is not int:raise ValueError()
    return value


def capture_command(request):
    value=raw(request)
    if not isinstance(value.get('request_id'),str):raise ValueError()
    key=canonical_uuid(value.pop('request_id'));kind=value.get('kind');api=request.content_type=='application/json'
    if not api:
        for field in ('fixed_nodes','floating_nodes'):
            if field in value:value[field]=integer(value[field],False)
        if 'production_units' in value:value['production_units']=None if value['production_units']=='' else integer(value['production_units'],False)
        if value.get('production_band')=='':value['production_band']=None
    return key,value


def event_command(request):
    value=raw(request);action=value.get('action');api=request.content_type=='application/json'
    if not isinstance(action,str) or action not in ('review','proposal'):raise ValueError()
    if set(value)!=({'action','request_id','expected_revision','decision'} if action=='review' else {'action','request_id','expected_revision'}):raise ValueError()
    if not isinstance(value['request_id'],str):raise ValueError()
    value['request_id']=canonical_uuid(value['request_id']);value['expected_revision']=integer(value['expected_revision'],api)
    return value


def redirect(path):
    response=HttpResponseRedirect(path);response.status_code=303;return private(response)


@require_GET
def case_list(request,identity):
    denied=local_customer(request)
    if denied is not None:return private(denied)
    try:
        before=cursor(request)
        with transaction.atomic(durable=True):
            payment.locked(request.user,identity)
            query=SyntheticLicenceCase.objects.filter(entitlement__fulfilment__acceptance__checkout_id=identity).order_by('-pk')
            if before:query=query.filter(pk__lt=before)
            rows=list(query[:21])
            lines=list(SyntheticLineEntitlement.objects.filter(fulfilment__acceptance__checkout_id=identity).order_by('line_id'))
            value={'cases':[{'case_id':str(c.identity),'kind':c.kind} for c in rows[:20]],
                'lines':[{'id':str(line.pk),'vendor':line.snapshot['configuration']['vendor'],'families':line.snapshot['configuration']['families']} for line in lines],
                'next_before':rows[19].pk if len(rows)>20 else None,'checkout_id':str(identity)}
        if request.headers.get('Accept')=='application/json':return private(reply(value))
        return private(render(request,'catalog/licence_changes.html',value))
    except (checkout.CheckoutError,BankError,ValueError,TypeError) as error:return error_response(error)


@require_http_methods(['GET','POST'])
@sensitive_post_parameters()
def new_case(request,identity,line_id):
    denied=local_customer(request)
    if denied is not None:return private(denied)
    try:
        if request.GET:raise ValueError()
        with PreparedArchive(archive_root()) as archive:
            if request.method=='POST':
                key,value=capture_command(request)
                case=service.capture(request.user,identity,line_id,key,value,archive)
                if request.content_type=='application/json':return private(reply({'case_id':str(case.identity),'payment_enabled':False,'effects_authorized':False},201))
                return redirect(f'/purchase/checkout-rehearsal/{identity}/changes/{case.identity}/')
            with transaction.atomic(durable=True):
                line=service.materials.line_locked(request.user,identity,line_id,archive)
                config=line.snapshot['configuration'];catalog=service.source(config)
        context={'new':True,'checkout_id':str(identity),'line_id':str(line_id),'original':config,
            'request_ids':{kind:str(uuid.uuid4()) for kind in service.KINDS},
            'families':[family for family in catalog['families'] if family not in config['families']],
            'family_key':str(uuid.uuid4()),'node_key':str(uuid.uuid4()),'production_key':str(uuid.uuid4()),'perpetual_key':str(uuid.uuid4()),'bands':catalog['production_bands'],'can_renew':config['term'] in ('rd-annual','rdp-yearly'),'can_nodes':config['vendor']=='altera',
            'can_production':config['term']!='perpetual','can_rdp':config['vendor']=='altera'}
        return private(render(request,'catalog/licence_changes.html',context))
    except (checkout.CheckoutError,BankError,ArchiveError,OSError,ValueError,TypeError,UnicodeError,RecursionError) as error:return error_response(error)


@require_GET
def case_detail(request,identity,case_id):
    denied=local_customer(request)
    if denied is not None:return private(denied)
    try:
        before=cursor(request)
        with PreparedArchive(archive_root()) as archive,transaction.atomic(durable=True):
            case=service.case_locked(request.user,identity,case_id,archive)
            value=service.summary(case,list(SyntheticLicenceCaseEvent.objects.filter(case=case).order_by('revision')),archive,before)
        if request.headers.get('Accept')=='application/json':return private(reply(value))
        return private(render(request,'catalog/licence_changes.html',{'case':value,'checkout_id':str(identity),'next_before':value['next_before']}))
    except (checkout.CheckoutError,BankError,ArchiveError,OSError,ValueError,TypeError,UnicodeError,RecursionError) as error:return error_response(error)


@require_GET
def staff_cases(request):
    if staff_credential(request,recent=True) is None:return private(reply({'error':'recent_staff_mfa_required'},403))
    try:
        before=cursor(request)
        query=SyntheticLicenceCaseStaffGrant.objects.filter(user=request.user).select_related('case').order_by('-pk')
        if before:query=query.filter(pk__lt=before)
        rows=list(query[:21])
        value={'staff':True,'cases':[{'case_id':str(g.case.identity),'kind':g.case.kind} for g in rows[:20]],'next_before':rows[19].pk if len(rows)>20 else None}
        return private(render(request,'catalog/licence_changes.html',value))
    except (ValueError,TypeError) as error:return error_response(error)


@require_http_methods(['GET','POST'])
@sensitive_post_parameters()
def staff_case(request,identity):
    if staff_credential(request,recent=True) is None:return private(reply({'error':'recent_staff_mfa_required'},403))
    grant=SyntheticLicenceCaseStaffGrant.objects.select_related('case__entitlement__fulfilment__acceptance__checkout__owner').filter(user=request.user,case__identity=identity).first()
    if grant is None:return private(reply({'error':'not_found'},404))
    checkout_row=grant.case.entitlement.fulfilment.acceptance.checkout
    try:
        before=cursor(request) if request.method=='GET' else None
        with PreparedArchive(archive_root()) as archive:
            if request.method=='POST':
                if request.GET:raise ValueError()
                value=event_command(request)
                service.event(request,checkout_row.owner,checkout_row.pk,identity,value['request_id'],value['expected_revision'],value['action'],archive,decision=value.get('decision'))
                if request.content_type!='application/json':return redirect(request.path)
            with transaction.atomic(durable=True):
                service.staff_locked(request)
                case=service.case_locked(checkout_row.owner,checkout_row.pk,identity,archive);service.staff_locked(request,case)
                value=service.summary(case,list(SyntheticLicenceCaseEvent.objects.filter(case=case).order_by('revision')),archive,before)
        if request.content_type=='application/json' or request.headers.get('Accept')=='application/json':return private(reply(value))
        return private(render(request,'catalog/licence_changes.html',{'staff':True,'case':value,'review_key':str(uuid.uuid4()),'proposal_key':str(uuid.uuid4()),'next_before':value['next_before']}))
    except (checkout.CheckoutError,BankError,ArchiveError,OSError,ValueError,TypeError,UnicodeError,RecursionError) as error:return error_response(error)
