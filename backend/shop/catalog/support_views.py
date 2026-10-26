"""Private local support rehearsal UI/API; staff mutations require exact grants and MFA."""
from pathlib import Path
import json
import re
import uuid
from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_http_methods
from shop.access.staff_auth import staff_credential
from shop.adapters.evidence_archive import PreparedArchive, ArchiveError
from shop.payments.bank_contract import BankError
from . import checkout, support_ledger as ledger
from .models import SyntheticFulfilment
from .views import local_customer, unique_object
from .cart_editor import private, canonical_uuid
from .cart_views import reply


def command(request,staff):
    if int(request.META.get('CONTENT_LENGTH') or 0)>1024:raise ValueError()
    if request.content_type=='application/json':
        raw=request.read(1025)
        if len(raw)>1024:raise ValueError()
        value=json.loads(raw,object_pairs_hook=unique_object,parse_constant=lambda _:(_ for _ in ()).throw(ValueError()))
    else:
        if request.content_type!='application/x-www-form-urlencoded' or len(request.body)>1024:raise ValueError()
        if any(len(request.POST.getlist(k))!=1 for k in request.POST):raise ValueError()
        value={k:v for k,v in request.POST.items() if k!='csrfmiddlewaretoken'}
    if not isinstance(value,dict):raise ValueError()
    action=value.get('action')
    allowed={'work','correct','statement'} if staff else {'reserve','release'}
    if not isinstance(action,str) or action not in allowed:raise ValueError()
    fields={'action','request_id'}
    if action=='reserve':fields|={'seconds','task_id'}
    if action in ('release','work','correct'):fields.add('target_id')
    if action in ('work','correct'):fields.add('seconds')
    if set(value)!=fields:raise ValueError()
    for key in ('request_id','task_id','target_id'):
        if key in value:
            if not isinstance(value[key],str):raise ValueError()
            value[key]=canonical_uuid(value[key])
    if 'seconds' in value and request.content_type!='application/json':
        if re.fullmatch(r'0|[1-9][0-9]{0,18}',value['seconds']) is None:raise ValueError()
        value['seconds']=int(value['seconds'])
    return value


def handle(request,identity,staff=False):
    if staff:
        if staff_credential(request,recent=True) is None:return private(reply({'error':'recent_staff_mfa_required'},403))
        grant=SyntheticFulfilment.objects.select_related('acceptance__checkout__owner').filter(
            acceptance__checkout_id=identity,syntheticsupportstaffgrant__user=request.user).first()
        if grant is None:return private(reply({'error':'not_found'},404))
        owner=grant.acceptance.checkout.owner
    else:
        denied=local_customer(request)
        if denied is not None:return private(denied)
        owner=request.user
    context={'checkout_id':str(identity),'staff':staff};status=200
    api=request.content_type=='application/json' or request.headers.get('Accept')=='application/json'
    try:
        if request.GET:raise checkout.CheckoutError('unexpected_query',400)
        root=getattr(settings,'LOCAL_CHECKOUT_ARCHIVE_ROOT',None)
        if not root:raise checkout.CheckoutError('local_archive_unavailable',503)
        with PreparedArchive(Path(root)) as archive:
            if request.method=='POST':
                value=command(request,staff)
                action=value.pop('action');key=value.pop('request_id')
                ledger.record(owner,identity,key,action,archive,staff_request=request if staff else None,**value)
                if not api:
                    response=HttpResponseRedirect(request.path);response.status_code=303;return private(response)
            state=ledger.read(owner,identity,archive,staff_request=request if staff else None)
        # Customer summaries expose usage, never internal staff attribution/generation/MFA markers.
        context['ledger']=state
        context['request_id']=str(uuid.uuid4());context['task_id']=str(uuid.uuid4())
        context['reservations']=[dict(value,id=key,request_id=str(uuid.uuid4())) for key,value in state['reservations'].items() if value['remaining'] and not value['closed']]
        context['work']=[dict(value,id=key,request_id=str(uuid.uuid4())) for key,value in state['work'].items() if not value['reversed']]
    except checkout.CheckoutError as error:context['error']=str(error);status=error.status
    except (ValueError,TypeError,UnicodeError,RecursionError):context['error']='invalid_request';status=400
    except BankError:context['error']='unavailable';status=404
    except (ArchiveError,OSError):context['error']='archive_unavailable';status=503
    if api:return private(reply({'ledger':context['ledger']} if 'ledger' in context else {'error':context['error']},status))
    return private(render(request,'catalog/support_ledger.html',context,status=status))


@require_http_methods(['GET','POST'])
@sensitive_post_parameters()
def support_page(request,identity):return handle(request,identity)


@require_http_methods(['GET','POST'])
@sensitive_post_parameters()
def staff_support_page(request,identity):return handle(request,identity,True)
