"""Recent-MFA, explicitly assigned, read-only staff preparation screen."""
from django.db.models import F
from django.views.decorators.http import require_GET
from shop.catalog.business_scope import current_scope
from .models import StaffQuotationGrant
from .offer_preparation import assess
from .staff_auth import staff_credential
from .staff_views import page
from .views import reply


@require_GET
def preparation(request, identity):
    if staff_credential(request, recent=True) is None:
        return reply({'error': 'recent_staff_mfa_required'}, 403)
    if request.GET:
        return reply({'error': 'unexpected_query'}, 400)
    grant = StaffQuotationGrant.objects.select_related('quotation__cart', 'quotation__snapshot').filter(
        user=request.user, quotation_id=identity,
        quotation__snapshot__cart_id=F('quotation__cart_id')).first()
    if grant is None:
        return reply({'error': 'not_found'}, 404)
    quotation = grant.quotation
    if quotation.business_version:
        if grant.business_scope_version != quotation.business_version:
            return reply({'error': 'business_scope_access_required'}, 403)
        if current_scope(quotation) is None:
            return reply({'error': 'business_scope_unavailable'}, 409)
    value = assess(quotation)
    if 'text/html' in request.headers.get('Accept', ''):
        response = page(request, 'access/offer_preparation.html', {'preparation': value})
    else:
        response = reply(value)
    response['Vary'] = 'Cookie'
    response['Content-Security-Policy'] = "default-src 'none'; form-action 'none'; frame-ancestors 'none'; base-uri 'none'"
    return response
