"""Assigned request scope and internal review history; no commercial approvals."""
import uuid
from django.db.models import F,Q
from django.views.decorators.http import require_GET
from django.shortcuts import render
from shop.catalog.quotation_views import quotation_json
from .models import StaffQuotationGrant
from .staff_auth import staff_credential
from .views import reply
from .quotation_review import snapshot_digest, review_json, history
from shop.catalog.models import REVIEW_DECISIONS
from shop.catalog.rules import CATALOG
from shop.catalog.business_scope import current_scope, valid_business, scope_for_version
from shop.catalog.business_rules import GROUPS
from shop.catalog.business_views import LABELS

PAGE_SIZE=20


def private_read(response):
    response['Cache-Control']='no-store';response['Referrer-Policy']='no-referrer';response['Vary']='Cookie'
    response['Content-Security-Policy']="default-src 'none'; form-action 'none'; frame-ancestors 'none'; base-uri 'none'"
    return response

def page(request,template,context):
    response=render(request,template,context)
    response['Cache-Control']='no-store';response['Referrer-Policy']='no-referrer'
    response['Content-Security-Policy']="default-src 'none'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'"
    return response

@require_GET
def quotations(request):
    if staff_credential(request,recent=True) is None:return private_read(reply({'error':'recent_staff_mfa_required'},403))
    rows=StaffQuotationGrant.objects.filter(user=request.user,quotation__snapshot__cart_id=F('quotation__cart_id'))
    if request.GET:
        if set(request.GET)!={'before'} or len(request.GET.getlist('before'))!=1:
            return private_read(reply({'error':'invalid_cursor'},400))
        raw=request.GET['before']
        try:
            if len(raw)!=36:raise ValueError('cursor')
            cursor=uuid.UUID(raw)
            if str(cursor)!=raw:raise ValueError('cursor')
        except ValueError:return private_read(reply({'error':'invalid_cursor'},400))
        anchor=rows.filter(quotation_id=cursor).values('quotation__created_at','quotation_id').first()
        if anchor is None:return private_read(reply({'error':'not_found'},404))
        rows=rows.filter(Q(quotation__created_at__lt=anchor['quotation__created_at'])|
            Q(quotation__created_at=anchor['quotation__created_at'],quotation_id__lt=anchor['quotation_id']))
    selected=list(rows.select_related('quotation__snapshot').order_by('-quotation__created_at','-quotation_id')[:PAGE_SIZE+1])
    rows=selected[:PAGE_SIZE]
    older=str(rows[-1].quotation_id) if len(selected)>PAGE_SIZE else None
    if 'text/html' in request.headers.get('Accept',''):
        return private_read(page(request,'access/staff_quotations.html',{'rows':rows,'older':older,'page_size':PAGE_SIZE}))
    return private_read(reply({'requests':[{'id':str(row.quotation_id),'version':row.quotation.snapshot.version,'state':'requested','review_version':row.quotation.review_version} for row in rows],'limit':PAGE_SIZE,'older':older}))

@require_GET
def quotation_detail(request,identity):
    if staff_credential(request,recent=True) is None:return reply({'error':'recent_staff_mfa_required'},403)
    if request.GET:return reply({'error':'unexpected_query'},400)
    grant=StaffQuotationGrant.objects.select_related('quotation__snapshot').filter(user=request.user,quotation_id=identity,quotation__snapshot__cart_id=F('quotation__cart_id')).first()
    if grant is None:return reply({'error':'not_found'},404)
    quotation=grant.quotation
    scope=current_scope(quotation)
    private_access=bool(scope and grant.business_scope_version==quotation.business_version and scope.business_snapshot.draft.owner_id==quotation.cart.owner_id)
    review_enabled=(not quotation.business_version or (private_access and valid_business(scope.business_snapshot,quotation.cart.owner_id)))
    digest=snapshot_digest(quotation) if review_enabled else None
    records=history(quotation)
    historical_private_version=grant.business_scope_version if scope_for_version(quotation,grant.business_scope_version) is not None else 0
    if 'text/html' in request.headers.get('Accept',''):
        return page(request,'access/staff_quotation.html',{'quotation':quotation,'reviews':records,
            'request_id':str(uuid.uuid4()),'snapshot_digest':digest,'decisions':REVIEW_DECISIONS,
            'catalog_current':quotation.snapshot.catalog_revision==CATALOG['revision'],'review_enabled':review_enabled,'private_access':private_access})
    return reply({**quotation_json(quotation),'review_version':quotation.review_version,'snapshot_digest':digest,
                  'reviews':[review_json(row,private_scope_version=historical_private_version) for row in records],'history_limit':20,'review_enabled':review_enabled,'private_business_access':private_access})


@require_GET
def quotation_business(request,identity):
    if staff_credential(request,recent=True) is None:return reply({'error':'recent_staff_mfa_required'},403)
    if request.GET:return reply({'error':'unexpected_query'},400)
    grant=StaffQuotationGrant.objects.select_related('quotation__cart').filter(user=request.user,quotation_id=identity,quotation__snapshot__cart_id=F('quotation__cart_id')).first()
    if grant is None:return reply({'error':'not_found'},404)
    quotation=grant.quotation;scope=current_scope(quotation)
    if scope is None:return reply({'error':'not_found'},404)
    if grant.business_scope_version!=scope.version or scope.business_snapshot.draft.owner_id!=quotation.cart.owner_id:
        return reply({'error':'business_scope_access_required'},403)
    snapshot=scope.business_snapshot
    if 'text/html' not in request.headers.get('Accept',''):
        return reply({'business_scope_version':scope.version,'business_draft_version':snapshot.version,
                      'details':snapshot.details,'evaluation':snapshot.evaluation,'country_tax_choices':'pending'})
    groups=[]
    for _,label,fields,hint in GROUPS:
        values=[]
        for field in fields:
            value=snapshot.details.get(field)
            text='Pending' if value is None else ('Yes' if value else 'No') if type(value) is bool else value or 'Not supplied'
            values.append({'label':LABELS[field],'value':text})
        groups.append({'label':label,'hint':hint,'values':values})
    return page(request,'access/staff_business.html',{'quotation':quotation,'scope':scope,'groups':groups})
