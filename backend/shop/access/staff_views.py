"""Assigned request scope and internal review history; no commercial approvals."""
import uuid
from django.views.decorators.http import require_GET
from django.shortcuts import render
from shop.catalog.quotation_views import quotation_json
from .models import StaffQuotationGrant
from .staff_auth import staff_credential
from .views import reply
from .quotation_review import snapshot_digest, review_json, history
from shop.catalog.models import REVIEW_DECISIONS
from shop.catalog.rules import CATALOG

def page(request,template,context):
    response=render(request,template,context)
    response['Cache-Control']='no-store';response['Referrer-Policy']='no-referrer'
    response['Content-Security-Policy']="default-src 'none'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'"
    return response

@require_GET
def quotations(request):
    if staff_credential(request,recent=True) is None:return reply({'error':'recent_staff_mfa_required'},403)
    if request.GET:return reply({'error':'unexpected_query'},400)
    rows=StaffQuotationGrant.objects.filter(user=request.user).select_related('quotation__snapshot').order_by('-quotation__created_at','-quotation_id')[:20]
    if 'text/html' in request.headers.get('Accept',''):
        return page(request,'access/staff_quotations.html',{'rows':rows})
    return reply({'requests':[{'id':str(row.quotation_id),'version':row.quotation.snapshot.version,'state':'requested','review_version':row.quotation.review_version} for row in rows],'limit':20})

@require_GET
def quotation_detail(request,identity):
    if staff_credential(request,recent=True) is None:return reply({'error':'recent_staff_mfa_required'},403)
    if request.GET:return reply({'error':'unexpected_query'},400)
    grant=StaffQuotationGrant.objects.select_related('quotation__snapshot').filter(user=request.user,quotation_id=identity).first()
    if grant is None:return reply({'error':'not_found'},404)
    quotation=grant.quotation
    digest=snapshot_digest(quotation)
    records=history(quotation)
    if 'text/html' in request.headers.get('Accept',''):
        return page(request,'access/staff_quotation.html',{'quotation':quotation,'reviews':records,
            'request_id':str(uuid.uuid4()),'snapshot_digest':digest,'decisions':REVIEW_DECISIONS,
            'catalog_current':quotation.snapshot.catalog_revision==CATALOG['revision']})
    return reply({**quotation_json(quotation),'review_version':quotation.review_version,'snapshot_digest':digest,
                  'reviews':[review_json(row) for row in records],'history_limit':20})
