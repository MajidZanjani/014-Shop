"""Explicit exact-scope local prepared capture; no archive I/O or work authority."""
import hashlib
import re
from django.db import DatabaseError
from django.http import HttpResponseNotAllowed
from shop.catalog.envelope_capture import capture_request_envelope, observe_request_capture
from shop.catalog.request_envelope import EnvelopeError, prepare_request_envelope, validate_envelope
from .staff_auth import payload, staff_credential
from .staff_views import page
from .views import reply


def private(response):
    response['Cache-Control']='no-store'
    response['Referrer-Policy']='no-referrer'
    response['Vary']='Cookie'
    response['Content-Security-Policy']="default-src 'none'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'"
    return response


def evidence(request,identity,version):
    if request.method not in ('GET','POST'):return private(HttpResponseNotAllowed(['GET','POST']))
    try:
        if staff_credential(request,recent=True) is None:
            return private(reply({'error':'recent_staff_mfa_required'},403))
        if request.GET:return private(reply({'error':'unexpected_query'},400))
        if request.method=='POST':
            try:
                if request.content_type!='application/x-www-form-urlencoded':raise ValueError('type')
                if int(request.META.get('CONTENT_LENGTH') or 0)>1024 or len(request.body)>1024:raise ValueError('size')
                value=payload(request,{'action','expected_source_sha256'})
                if value['action']!='capture' or re.fullmatch('[0-9a-f]{64}',value['expected_source_sha256']) is None:raise ValueError('fields')
            except (ValueError,TypeError,UnicodeError):
                return private(reply({'error':'invalid_request'},400))
            reference=capture_request_envelope(request,identity,version,expected_source_sha256=value['expected_source_sha256'])
            # Only metadata fixed by the route and committed result is projected.
            # Do not re-read source after commit: a lost response can be explicitly
            # reconciled by resubmitting the same digest-bound form.
            response=page(request,'access/request_evidence.html',{'identity':identity,'version':version,'captured':True,'created':reference.created})
            response.status_code=201 if reference.created else 200
            return private(response)
        raw=prepare_request_envelope(request,identity,version)
        source=validate_envelope(raw)
        return private(page(request,'access/request_evidence.html',{'identity':identity,'version':version,
            'cart_version':source['cart']['version'],'digest':hashlib.sha256(raw).hexdigest()}))
    except EnvelopeError as error:
        if str(error) in ('capture_preview_changed','capture_conflict'):
            return private(reply({'error':'capture_conflict'},409))
        return private(reply({'error':'not_found'},404))
    except DatabaseError:
        return private(reply({'error':'capture_unavailable'},503))


CAPTURE_LABELS={
    'capture_not_recorded':'No capture record observed for this exact retained scope.',
    'capture_recorded':'Prepared database capture recorded for this exact retained scope.',
}


def capture_status(request,identity,version):
    from .archive_observation import private as status_private
    if request.method!='GET':return status_private(HttpResponseNotAllowed(['GET']))
    try:
        if staff_credential(request,recent=True) is None:
            return status_private(reply({'error':'recent_staff_mfa_required'},403))
        if request.GET:return status_private(reply({'error':'unexpected_query'},400))
        status=observe_request_capture(request,identity,version)
    except EnvelopeError:
        return status_private(reply({'error':'not_found'},404))
    except DatabaseError:
        return status_private(reply({'error':'observation_unavailable'},503))
    if status not in CAPTURE_LABELS:
        return status_private(reply({'error':'observation_unavailable'},503))
    if 'text/html' in request.headers.get('Accept',''):
        return status_private(page(request,'access/request_evidence.html',
            {'identity':identity,'version':version,'observation':CAPTURE_LABELS[status]}))
    return status_private(reply({'status':status,'evidence_class':'local-synthetic','evidence_kind':'prepared',
        'retention_qualified':False,'effects_authorized':False}))
