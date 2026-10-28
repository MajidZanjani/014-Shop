"""Verified-owner document prerequisites. GET has no domain writes."""
from django.db import transaction
from django.db.models import F
from django.shortcuts import render
from django.views.decorators.http import require_GET
from .cart_views import current_customer, reply
from .document_preview import preview
from .models import QuotationRequest
from .views import local_customer


@require_GET
def document_preview(request, identity):
    denied = local_customer(request)
    if denied is not None:
        denied['Cache-Control'] = 'no-store'
        return denied
    if request.GET:
        return reply({'error': 'unexpected_query'}, 400)
    with transaction.atomic():
        if not current_customer(request.user, request):
            return reply({'error': 'verification_required'}, 403)
        quotation = QuotationRequest.objects.select_related('cart', 'snapshot').filter(pk=identity, cart__owner=request.user, snapshot__cart_id=F('cart_id')).first()
        if quotation is None:
            return reply({'error': 'not_found'}, 404)
        value = preview(quotation)
        response = render(request, 'catalog/document_preview.html', {'preview': value}, status=200 if value['state'] == 'preview_only' else 409)
        response['Cache-Control'] = 'no-store'
        response['Referrer-Policy'] = 'no-referrer'
        response['Vary'] = 'Cookie'
        response['Content-Security-Policy'] = "default-src 'none'; form-action 'none'; frame-ancestors 'none'; base-uri 'none'"
        return response
