"""Read-only owner history with bounded keyset pagination and a closed projection."""
import uuid
from django.db.models import F,Q
from django.shortcuts import render
from django.views.decorators.http import require_GET
from .cart_views import reply
from .models import QuotationRequest
from .quotation_status import with_review_status,customer_review_status
from .views import local_customer

PAGE_SIZE=20


@require_GET
def quotation_history(request):
    denied=local_customer(request)
    if denied is not None:
        denied['Cache-Control']='no-store'
        return denied
    rows=QuotationRequest.objects.filter(cart__owner=request.user,snapshot__cart_id=F('cart_id'))
    if request.GET:
        if set(request.GET)!={'before'} or len(request.GET.getlist('before'))!=1:
            return reply({'error':'invalid_cursor'},400)
        raw=request.GET['before']
        try:
            cursor=uuid.UUID(raw)
            if str(cursor)!=raw:raise ValueError('canonical')
        except ValueError:return reply({'error':'invalid_cursor'},400)
        anchor=rows.filter(pk=cursor).values('created_at','id').first()
        if anchor is None:return reply({'error':'not_found'},404)
        rows=rows.filter(Q(created_at__lt=anchor['created_at'])|Q(created_at=anchor['created_at'],id__lt=anchor['id']))
    selected=list(with_review_status(rows).select_related('snapshot').order_by('-created_at','-id')[:PAGE_SIZE+1])
    page=selected[:PAGE_SIZE]
    items=[{'id':str(row.id),'created_at':row.created_at,'cart_version':row.snapshot.version,
            'status':customer_review_status(row)} for row in page]
    response=render(request,'catalog/quotation_history.html',{
        'items':items,'page_size':PAGE_SIZE,'older':str(page[-1].id) if len(selected)>PAGE_SIZE else None})
    response['Cache-Control']='no-store'
    response['Referrer-Policy']='no-referrer'
    response['Vary']='Cookie'
    response['Content-Security-Policy']="default-src 'none'; form-action 'none'; frame-ancestors 'none'; base-uri 'none'"
    return response
