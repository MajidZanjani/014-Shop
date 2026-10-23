"""Read-only quotation review, requiring explicit per-resource reviewer grants."""
from django.views.decorators.http import require_GET
from django.shortcuts import render
from shop.catalog.quotation_views import quotation_json
from .models import StaffQuotationGrant
from .staff_auth import staff_credential
from .views import reply

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
    return reply({'requests':[{'id':str(row.quotation_id),'version':row.quotation.snapshot.version,'state':'requested'} for row in rows],'limit':20})

@require_GET
def quotation_detail(request,identity):
    if staff_credential(request,recent=True) is None:return reply({'error':'recent_staff_mfa_required'},403)
    if request.GET:return reply({'error':'unexpected_query'},400)
    grant=StaffQuotationGrant.objects.select_related('quotation__snapshot').filter(user=request.user,quotation_id=identity).first()
    if grant is None:return reply({'error':'not_found'},404)
    if 'text/html' in request.headers.get('Accept',''):
        return page(request,'access/staff_quotation.html',{'quotation':grant.quotation})
    return reply(quotation_json(grant.quotation))
