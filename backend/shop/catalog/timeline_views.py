"""Read-only owner timeline; no staff records serialized."""
from django.db.models import F
from django.shortcuts import render
from django.views.decorators.http import require_GET
from .cart_views import reply
from .models import QuotationRequest
from .quotation_status import with_review_status
from .quotation_timeline import cursors, timeline_events
from .views import local_customer


@require_GET
def quotation_timeline(request, identity):
    denied = local_customer(request)
    if denied is not None:
        denied['Cache-Control'] = 'no-store'
        return denied
    quotation = with_review_status(QuotationRequest.objects.filter(pk=identity, cart__owner=request.user, snapshot__cart_id=F('cart_id'))).select_related('cart', 'snapshot').first()
    if quotation is None:
        return reply({'error': 'not_found'}, 404)
    try:
        before = cursors(request.GET, quotation)
    except ValueError:
        return reply({'error': 'invalid_cursor'}, 400)
    value = timeline_events(quotation, before)
    response = render(request, 'catalog/quotation_timeline.html', {'quotation': quotation, 'timeline': value})
    response['Cache-Control'] = 'no-store'
    response['Referrer-Policy'] = 'no-referrer'
    response['Vary'] = 'Cookie'
    response['Content-Security-Policy'] = "default-src 'none'; form-action 'none'; frame-ancestors 'none'; base-uri 'none'"
    return response
