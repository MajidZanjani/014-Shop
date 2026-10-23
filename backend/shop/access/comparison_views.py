"""Recent-MFA, both-scope-authorized, read-only preparation comparison."""
from django.views.decorators.http import require_GET
from .models import PreparationAssessment
from .offer_preparation import assess
from .preparation_comparison import compare
from .preparation_snapshots import assignment, current_error, retained_error, response_error, blocked_assessment
from .staff_auth import staff_credential
from .staff_views import page
from .views import reply


@require_GET
def comparison(request, identity, version):
    if staff_credential(request, recent=True) is None:
        return response_error(request, 'recent_staff_mfa_required', 403)
    if request.GET:
        return response_error(request, 'invalid_request', 400)
    grant = assignment(request, identity)
    if grant is None:
        return response_error(request, 'not_found', 404)
    q = grant.quotation
    row = PreparationAssessment.objects.select_related('business_scope__business_snapshot__draft', 'review').filter(
        quotation=q, version=version, version__lte=q.preparation_version).first()
    if row is None:
        return response_error(request, 'not_found', 404)
    for error in (retained_error(row, grant), current_error(grant)):
        if error:
            code, status = error
            if code == 'business_scope_access_required': code = 'comparison_scope_access_required'
            return response_error(request, code, status)
    current = assess(q)
    if not blocked_assessment(current):
        return response_error(request, 'assessment_changed', 409)
    value = {**compare(row.assessment, current), 'quotation_id': str(q.id), 'preparation_version': row.version,
             'retained': {'cart_version': row.assessment['cart_version'], 'business_version': row.business_version,
                          'review_version': row.review_version},
             'current': {'cart_version': q.snapshot.version, 'business_version': q.business_version,
                         'review_version': q.review_version}}
    if 'text/html' in request.headers.get('Accept', ''):
        response = page(request, 'access/preparation_comparison.html', {'comparison': value})
    else:
        response = reply(value)
    response['Vary'] = 'Cookie'
    response['Content-Security-Policy'] = "default-src 'none'; form-action 'none'; frame-ancestors 'none'; base-uri 'none'"
    return response
