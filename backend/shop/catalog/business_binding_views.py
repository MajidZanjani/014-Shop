"""Explicit owner preview/attach. Country and tax choices stay pending."""
import re
import uuid
from django.db import transaction
from django.db.models import F
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from . import business_rules as rules
from .business_views import LABELS
from .business_scope import current_scope, valid_business
from .models import QuotationRequest, BusinessDraftSnapshot, QuotationBusinessScope, QuotationBusinessKey
from .rules import CATALOG
from .views import local_customer
from .cart_views import reply


def page(request,quotation,*,selected=None,expected=None,key=None,status=200,message=''):
    scopes=list(QuotationBusinessScope.objects.filter(quotation=quotation,business_snapshot__draft__owner=request.user).select_related('business_snapshot').order_by('-version')[:20])
    options=list(BusinessDraftSnapshot.objects.filter(draft__owner=request.user).order_by('-version')[:20])
    attached=current_scope(quotation)
    if selected is None:selected=attached.business_snapshot if attached else options[0] if options else None
    if selected is not None and all(row.pk!=selected.pk for row in options):options.append(selected)
    preview=[]
    if selected:
        for _,label,fields,hint in rules.GROUPS:
            values=[]
            for field in fields:
                value=selected.details.get(field)
                text='Pending' if value is None else ('Yes' if value else 'No') if type(value) is bool else value or 'Not supplied'
                values.append({'label':LABELS[field],'value':text})
            preview.append({'label':label,'hint':hint,'values':values})
    response=render(request,'catalog/business_binding.html',{'quotation':quotation,'attached':attached,
        'options':options,'selected':selected,'preview':preview,'scopes':scopes,
        'expected':quotation.business_version if expected is None else expected,'request_id':str(key or uuid.uuid4()),'message':message},status=status)
    response['Cache-Control']='no-store';response['Referrer-Policy']='no-referrer';response['Vary']='Cookie'
    response['Content-Security-Policy']="default-src 'none'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'"
    return response


def redirect(quotation):
    response=HttpResponseRedirect('/purchase/quotation-business/'+str(quotation.id)+'/');response.status_code=303
    response['Cache-Control']='no-store';return response


@require_http_methods(['GET','POST'])
def bind_business(request,identity):
    denied=local_customer(request)
    if denied is not None:denied['Cache-Control']='no-store';return denied
    quotation=QuotationRequest.objects.select_related('cart').filter(pk=identity,cart__owner=request.user,snapshot__cart_id=F('cart_id')).first()
    if quotation is None:
        return reply({'error':'not_found'},404)
    if request.GET:return page(request,quotation,status=400,message='Query parameters are not accepted.')
    if request.method=='GET':return page(request,quotation)
    try:
        if request.content_type!='application/x-www-form-urlencoded' or int(request.META.get('CONTENT_LENGTH') or 0)>1024 or len(request.body)>1024:raise ValueError('body')
        value=request.POST
        if set(value)-{'csrfmiddlewaretoken'}!={'action','request_id','expected_scope_version','business_version'} or any(len(value.getlist(k))!=1 for k in value):raise ValueError('fields')
        if value['action'] not in ('preview','attach'):raise ValueError('action')
        key=uuid.UUID(value['request_id'])
        for field in ['expected_scope_version','business_version']:
            if re.fullmatch(r'0|[1-9][0-9]{0,9}',value[field]) is None:raise ValueError('version')
        expected=int(value['expected_scope_version']);version=int(value['business_version'])
        if not 0<=expected<1000000000 or not 1<=version<=1000000000:raise ValueError('version')
    except (ValueError,TypeError,UnicodeError):return page(request,quotation,status=400,message='Submission rejected. Reload and review saved revisions.')
    if value['action']=='preview':
        selected=BusinessDraftSnapshot.objects.select_related('draft').filter(draft__owner=request.user,version=version).first()
        if selected is None:return page(request,quotation,status=404,message='Saved business revision unavailable.')
        # Never rebase a previewed form onto a concurrent attachment.
        return page(request,quotation,selected=selected,expected=expected,key=key)
    with transaction.atomic():
        quotation=QuotationRequest.objects.select_for_update().select_related('cart').filter(pk=quotation.pk,cart__owner=request.user,snapshot__cart_id=F('cart_id')).first()
        if quotation is None:return reply({'error':'not_found'},404)
        old=QuotationBusinessKey.objects.select_related('scope__business_snapshot').filter(quotation=quotation,request_id=key).first()
        error=None
        if old:
            if old.expected_version!=expected or old.scope.business_snapshot.version!=version:
                error='This submission identity was used for a different attachment. Reload before editing.'
        elif quotation.business_version!=expected:
            error='The attached business scope changed. Reload and review it before attaching another revision.'
        else:
            selected=BusinessDraftSnapshot.objects.select_related('draft').filter(draft__owner=request.user,version=version).first()
            if selected is None:error='Saved business revision unavailable.'
            elif not valid_business(selected,request.user.pk) or quotation.snapshot.catalog_revision!=CATALOG['revision']:
                error='This saved scope requires review against the current source. Country/tax choices remain pending.'
            else:
                scope=current_scope(quotation)
                if scope is None or scope.business_snapshot_id!=selected.pk:
                    quotation.business_version+=1
                    scope=QuotationBusinessScope.objects.create(quotation=quotation,version=quotation.business_version,business_snapshot=selected)
                    quotation.save(update_fields=['business_version'])
                QuotationBusinessKey.objects.create(quotation=quotation,request_id=key,expected_version=expected,scope=scope)
    if error:return page(request,quotation,status=409,message=error)
    return redirect(quotation)
