"""Recent-MFA exact-attempt observation only; no archive I/O or work controls."""
from django.db import DatabaseError
from django.http import HttpResponseNotAllowed
from shop.catalog.archive_reconciliation import reconcile_archive_publication
from shop.catalog.request_envelope import EnvelopeError
from .staff_auth import staff_credential
from .staff_views import page
from .views import reply

LABELS={
    'verification_recorded':'Prepared-byte verification recorded for this attempt.',
    'verification_recorded_by_other_claim':'Prepared-byte verification recorded for another retained attempt.',
    'verification_not_recorded':'No prepared-byte verification recorded. Physical publication may still exist or be in progress.',
}


def private(response):
    response['Cache-Control']='no-store'
    response['Referrer-Policy']='no-referrer'
    response['Vary']='Cookie'
    response['Content-Security-Policy']="default-src 'none'; form-action 'none'; frame-ancestors 'none'; base-uri 'none'"
    return response


def reconciliation(request,identity,claim_id):
    if request.method!='GET':return private(HttpResponseNotAllowed(['GET']))
    try:
        if staff_credential(request,recent=True) is None:
            return private(reply({'error':'recent_staff_mfa_required'},403))
        if request.GET:return private(reply({'error':'unexpected_query'},400))
        observed=reconcile_archive_publication(request,identity,claim_id)
    except EnvelopeError:
        return private(reply({'error':'not_found'},404))
    except DatabaseError:
        return private(reply({'error':'observation_unavailable'},503))
    if observed.status not in LABELS:
        return private(reply({'error':'observation_unavailable'},503))
    value={'status':observed.status,'evidence_class':'local-synthetic','evidence_kind':'prepared',
           'retention_qualified':False,'effects_authorized':False}
    if 'text/html' in request.headers.get('Accept',''):
        return private(page(request,'access/archive_observation.html',{'label':LABELS[observed.status]}))
    return private(reply(value))
