"""Local synthetic acceptance/payment actions; no customer-supplied money or terms."""
from pathlib import Path
import json
import re
from django.conf import settings
from django.shortcuts import render
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_http_methods
from shop.adapters.evidence_archive import PreparedArchive, ArchiveError
from shop.payments.bank_contract import BankError
from . import checkout, checkout_payment as service, fulfilment
from .cart_editor import private
from .cart_views import reply
from .views import local_customer, unique_object



# Fixed HTML guidance only; API codes and all service decisions remain unchanged.
ERROR_MESSAGES = {
    'unexpected_query': 'This page does not accept query parameters. Reload the retained rehearsal status.',
    'invalid_request': 'This submission could not be read. Reload the retained rehearsal status before continuing.',
    'synthetic_confirmation_required': 'Confirm the synthetic declaration before recording this rehearsal.',
    'review_changed': 'The synthetic review has changed. Reload and review the retained details before continuing.',
    'synthetic_offer_expired': 'This synthetic offer has expired. Return to the current checkout rehearsal to review the available scope.',
    'synthetic_acceptance_required': 'Review and record the synthetic acceptance before simulating payment.',
    'payment_attempt_required': 'There is no retained payment attempt to look up. Reload the rehearsal status.',
    'payment_uncertain_use_lookup': 'The simulated payment result is uncertain. Use lookup from the retained status; do not start another payment.',
    'archive_unavailable': 'Required recovery evidence is unavailable. This rehearsal is on hold; reload the retained status before continuing.',
    'local_archive_unavailable': 'Required recovery evidence is unavailable. This rehearsal is on hold; reload the retained status before continuing.',
    'synthetic_operation_unavailable': 'This synthetic operation is unavailable. Reload the retained rehearsal status before continuing.',
    'not_found': 'This rehearsal is unavailable for your customer access.',
}
DEFAULT_ERROR_MESSAGE = 'This rehearsal is on hold. Reload the retained status before continuing. If payment is uncertain, use lookup; do not start another payment.'


def command(request, api):
    limit = 1024
    if int(request.META.get('CONTENT_LENGTH') or 0) > limit: raise ValueError('size')
    if api:
        if request.content_type != 'application/json': raise ValueError('type')
        raw = request.read(limit + 1)
        if len(raw) > limit: raise ValueError('size')
        value = json.loads(raw, object_pairs_hook=unique_object,
                           parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
    else:
        if request.content_type != 'application/x-www-form-urlencoded' or len(request.body) > limit: raise ValueError('type')
        if any(len(request.POST.getlist(key)) != 1 for key in request.POST): raise ValueError('duplicate')
        value = {k: v for k, v in request.POST.items() if k != 'csrfmiddlewaretoken'}
    if not isinstance(value, dict): raise ValueError('fields')
    action = value.get('action')
    if action == 'accept':
        if set(value) != {'action', 'sha256', 'confirmed'}: raise ValueError('fields')
        if not isinstance(value['sha256'], str) or re.fullmatch('[0-9a-f]{64}', value['sha256']) is None: raise ValueError('sha256')
        if not api: value['confirmed'] = value['confirmed'] == 'on'
    elif action in ('deliver_initial', 'deliver_reference'):
        if set(value) != {'action','line_id'} or not isinstance(value['line_id'],str): raise ValueError('fields')
        from .cart_editor import canonical_uuid
        value['line_id'] = canonical_uuid(value['line_id'])
    elif action in ('pay', 'reconcile', 'provision'):

        if set(value) != {'action'}: raise ValueError('fields')
    else: raise ValueError('action')
    return value


def summary(value, sha256, row):
    attempt = row.attempt if row and row.attempt_id else None
    return {'review': value, 'sha256': sha256, 'synthetic_accepted': bool(row and row.simulated_accepted_at),
            'order_reference': str(row.pk) if row and row.simulated_accepted_at else None,
            'attempt_state': attempt.state if attempt else None,
            'bank_session_expires_at': attempt.expires_at.isoformat() if attempt and attempt.expires_at else None,
            'provider_status': attempt.provider_status if attempt else None,
            'fulfilment': fulfilment.status(row),
            'simulated_paid': bool(attempt and attempt.state == 'observed' and attempt.provider_status == 'captured'),
            'evidence_class': 'local-synthetic', 'acceptance_enabled': False,
            'financial_confirmation': False, 'effects_authorized': False}


def handle(request, identity, api):
    denied = local_customer(request)
    if denied is not None: return private(denied)
    context = {};status = 200
    try:
        if request.GET: raise checkout.CheckoutError('unexpected_query', 400)
        if request.method == 'POST':
            value = command(request, api)
            root = getattr(settings, 'LOCAL_CHECKOUT_ARCHIVE_ROOT', None)
            if not root: raise checkout.CheckoutError('local_archive_unavailable', 503)
            with PreparedArchive(Path(root)) as archive:
                if value['action'] == 'accept': service.accept(request.user, identity, value['sha256'], value['confirmed'], archive)
                elif value['action'] == 'pay': service.pay(request.user, identity, archive)
                elif value['action'] == 'reconcile': service.reconcile(request.user, identity, archive)
                elif value['action'] == 'provision': fulfilment.provision(request.user, identity, archive)
                else: fulfilment.deliver(request.user, identity, value['line_id'], 'initial' if value['action']=='deliver_initial' else 'reference', archive)
        value, sha256, row = service.review(request.user, identity)
        context = summary(value, sha256, row)
    except checkout.CheckoutError as error:
        context = {'error': str(error)};status = error.status
    except BankError:
        context = {'error': 'synthetic_operation_unavailable'};status = 409
    except TimeoutError:
        context = {'error': 'payment_uncertain_use_lookup'};status = 409
    except (ArchiveError, OSError):
        context = {'error': 'archive_unavailable'};status = 503
    except (ValueError, TypeError, UnicodeError, RecursionError):
        context = {'error': 'invalid_request'};status = 400
    if api: return private(reply(context, status))
    if 'error' in context:
        context['error_message'] = ERROR_MESSAGES.get(context['error'], DEFAULT_ERROR_MESSAGE)
    context['checkout_id'] = str(identity)
    return private(render(request, 'catalog/checkout_payment.html', context, status=status))


@require_http_methods(['GET', 'POST'])
@sensitive_post_parameters()
def payment_page(request, identity):
    return handle(request, identity, False)


@require_http_methods(['GET', 'POST'])
@sensitive_post_parameters()
def payment_api(request, identity):
    return handle(request, identity, True)
