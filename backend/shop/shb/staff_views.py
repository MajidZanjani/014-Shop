"""Extend the existing assigned quotation screen for the SHB capture."""
import re
import uuid
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST
from shop.access.staff_auth import payload, staff_credential
from shop.access.views import reply
from . import staff_review
from .errors import ShbError


def private(response):
    response['Cache-Control'] = 'no-store'; response['Referrer-Policy'] = 'no-referrer'
    response['Vary'] = 'Cookie'
    response['Content-Security-Policy'] = "default-src 'none'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'"
    return response


def reject(error):
    return private(reply({'error': error.code}, error.status))


@require_GET
def detail(request, identity):
    if request.GET: return reject(ShbError('unexpected_query', 400))
    try:
        row, history = staff_review.details(request, identity)
    except ShbError as error: return reject(error)
    except ValueError: return reject(ShbError('shb_review_unavailable', 503))
    from .models import SupportOffer
    offers = list(SupportOffer.objects.filter(request=row).order_by('-revision')[:20])
    if 'text/html' in request.headers.get('Accept', ''):
        return private(render(request, 'shb/staff_request.html', {'record': row, 'history': history,
            'request_id': str(uuid.uuid4()), 'details': row.payload['details'],
            'known_project_reference': row.payload['known_project_reference'],
            'purchase': row.payload['purchase'], 'review_open': row.state in ('submitted', 'needs_information', 'under_review','offer_expired'),
            'offers':offers, 'can_issue_offer':row.state=='under_review' and bool(history)
                and history[0].review.decision=='ready_for_commercial_review'
                and not any(offer.state in ('prepared','issued','paid') or
                    offer.payload['review_version'] >= row.quotation.review_version for offer in offers),
            'closing_open':row.state in ('submitted','needs_information','under_review','offer_issued','offer_expired'),
            'active_offer':next((offer for offer in offers if offer.state in ('prepared','issued')),None)}))
    return private(reply({'id': str(row.pk), 'quotation_id': str(row.quotation_id), 'state': row.state,
        'scope_sha256': row.sha256, 'request_revision': row.revision, 'review_version': row.quotation.review_version,
        'details': row.payload['details'], 'purchase': row.payload['purchase'],
        'known_project_reference': row.payload['known_project_reference'],
        'offers': [{'id':str(offer.pk), 'state':offer.state, 'sha256':offer.sha256,
            'expires_at':offer.expires_at.isoformat(), 'customer_path':'/purchase/shb/offer/'+str(offer.pk)+'/'} for offer in offers],
        'checkout_enabled': False, 'reviews': [{'version': event.review.version,
            'decision': event.review.decision, 'message': event.message,
            'reviewer_id': event.review.reviewer_id, 'mfa_verified_at': event.review.mfa_verified_at.isoformat()} for event in history]}))


@require_POST
def record_review(request, identity):
    if staff_credential(request, recent=True) is None:
        return reject(ShbError('recent_staff_mfa_required', 403))
    if request.GET: return reject(ShbError('unexpected_query', 400))
    try:
        value = payload(request, {'request_id', 'expected_review_version', 'scope_sha256', 'decision', 'message'})
        if request.content_type == 'application/x-www-form-urlencoded':
            raw = value['expected_review_version']
            if not re.fullmatch(r'0|[1-9][0-9]{0,9}', raw): raise ValueError()
            value['expected_review_version'] = int(raw)
        row, event, created = staff_review.record(request, identity, value)
    except ShbError as error: return reject(error)
    except (ValueError, TypeError, UnicodeError, RecursionError): return reject(ShbError('invalid_request', 400))
    if request.content_type == 'application/x-www-form-urlencoded':
        response = HttpResponseRedirect('/staff/quotation-requests/' + str(identity) + '/')
        response.status_code = 303
        return private(response)
    return private(reply({'state': row.state, 'review_version': row.quotation.review_version,
        'decision': event.review.decision, 'checkout_enabled': False}, 201 if created else 200))


@require_POST
def issue_offer(request, identity):
    from pathlib import Path
    from django.conf import settings
    from shop.adapters.evidence_archive import PreparedArchive, ArchiveError
    from shop.catalog.checkout import CheckoutError
    from . import offers
    if staff_credential(request, recent=True) is None: return reject(ShbError('recent_staff_mfa_required',403))
    if request.GET: return reject(ShbError('unexpected_query',400))
    try:
        value=payload(request,{'request_id','expected_review_version','scope_sha256','prerequisites','exclusions'},maximum_bytes=32768)
        if request.content_type=='application/x-www-form-urlencoded':
            if not re.fullmatch(r'0|[1-9][0-9]{0,9}',value['expected_review_version']): raise ValueError()
            value['expected_review_version']=int(value['expected_review_version'])
        root=getattr(settings,'LOCAL_CHECKOUT_ARCHIVE_ROOT',None)
        if not root: raise ShbError('recovery_evidence_unavailable',503)
        with PreparedArchive(Path(root)) as archive: offer,created=offers.issue(request,identity,value,archive)
    except ShbError as error: return reject(error)
    except CheckoutError as error: return reject(ShbError(str(error),error.status))
    except (ArchiveError,OSError): return reject(ShbError('recovery_evidence_unavailable',503))
    except (ValueError,TypeError,UnicodeError,RecursionError): return reject(ShbError('invalid_request',400))
    if request.content_type=='application/x-www-form-urlencoded':
        response=HttpResponseRedirect('/staff/quotation-requests/'+str(identity)+'/');response.status_code=303
        return private(response)
    return private(reply({'id':str(offer.pk),'state':offer.state,'sha256':offer.sha256,
        'expires_at':offer.expires_at.isoformat(),'customer_path':'/purchase/shb/offer/'+str(offer.pk)+'/'},201 if created else 200))


@require_POST
def close_request(request, identity):
    from pathlib import Path
    from django.conf import settings
    from shop.adapters.evidence_archive import PreparedArchive, ArchiveError
    from shop.catalog.checkout import CheckoutError
    from . import lifecycle
    if staff_credential(request,recent=True) is None: return reject(ShbError('recent_staff_mfa_required',403))
    if request.GET: return reject(ShbError('unexpected_query',400))
    try:
        value=payload(request,{'request_id','expected_review_version','scope_sha256','offer_id','action','reason'},maximum_bytes=8192)
        if request.content_type=='application/x-www-form-urlencoded':
            if not re.fullmatch(r'0|[1-9][0-9]{0,9}',value['expected_review_version']): raise ValueError()
            value['expected_review_version']=int(value['expected_review_version'])
        root=getattr(settings,'LOCAL_CHECKOUT_ARCHIVE_ROOT',None)
        if not root: raise ShbError('recovery_evidence_unavailable',503)
        with PreparedArchive(Path(root)) as archive: saved,created=lifecycle.close(request,identity,value,archive)
    except ShbError as error: return reject(error)
    except CheckoutError as error: return reject(ShbError(str(error),error.status))
    except (ArchiveError,OSError): return reject(ShbError('recovery_evidence_unavailable',503))
    except (ValueError,TypeError,UnicodeError,RecursionError): return reject(ShbError('invalid_request',400))
    if request.content_type=='application/x-www-form-urlencoded':
        response=HttpResponseRedirect('/staff/quotation-requests/'+str(identity)+'/');response.status_code=303
        return private(response)
    return private(reply({'id':str(saved.pk),'state':saved.payload['result_state'],
        'action':saved.payload['action'],'archived':bool(saved.applied_at)},201 if created else 200))
