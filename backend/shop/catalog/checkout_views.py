"""One guarded checkout service for local API and no-JavaScript rehearsals."""
import json
import re
import uuid
from django.shortcuts import render
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_http_methods
from shop.payments.bank_contract import BankError
from . import checkout
from .cart_editor import private, canonical_uuid
from .cart_views import reply
from .views import local_customer, unique_object


def result(row):
    # No business fields or document bodies in command receipts.
    return {'id': str(row.pk), 'sha256': row.sha256, 'cart_version': row.cart_snapshot.version,
            'business_version': row.business_snapshot.version, 'evidence_class': 'local-synthetic',
            'state': 'synthetic_checkout_recorded', 'acceptance_enabled': False,
            'financial_confirmation': False, 'effects_authorized': False}


def controls(value):
    if not isinstance(value, dict) or set(value) != {'request_id', 'sha256'}:
        raise ValueError('fields')
    key = canonical_uuid(value['request_id'])
    if not isinstance(value['sha256'], str) or re.fullmatch('[0-9a-f]{64}', value['sha256']) is None:
        raise ValueError('sha256')
    return key, value['sha256']


@require_http_methods(['GET', 'POST'])
@sensitive_post_parameters()
def checkout_api(request):
    denied = local_customer(request)
    if denied is not None: return private(denied)
    if request.GET: return private(reply({'error': 'unexpected_query'}, 400))
    try:
        if request.method == 'GET':
            value, sha256 = checkout.current(request.user)
            return private(reply({'snapshot': value, 'sha256': sha256}))
        if request.content_type != 'application/json': return private(reply({'error': 'content_type'}, 415))
        if int(request.META.get('CONTENT_LENGTH') or 0) > 1024: raise ValueError('size')
        raw = request.read(1025)
        if len(raw) > 1024: raise ValueError('size')
        value = json.loads(raw, object_pairs_hook=unique_object, parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
        row, created = checkout.capture(request.user, *controls(value))
        return private(reply(result(row), 201 if created else 200))
    except checkout.CheckoutError as error:
        return private(reply({'error': str(error)}, error.status))
    except BankError:
        return private(reply({'error': 'unavailable'}, 403))
    except (ValueError, TypeError, UnicodeError, RecursionError, AttributeError):
        return private(reply({'error': 'invalid_request'}, 400))


@require_http_methods(['GET', 'POST'])
@sensitive_post_parameters()
def checkout_page(request):
    denied = local_customer(request)
    if denied is not None: return private(denied)
    context = {};status = 200
    try:
        if request.GET: raise checkout.CheckoutError('unexpected_query', 400)
        if request.method == 'POST':
            if (request.content_type != 'application/x-www-form-urlencoded'
                    or int(request.META.get('CONTENT_LENGTH') or 0) > 1024 or len(request.body) > 1024):
                raise ValueError('body')
            value = request.POST
            if any(len(value.getlist(k)) != 1 for k in value): raise ValueError('duplicate')
            row, created = checkout.capture(request.user, *controls({k: v for k, v in value.items() if k != 'csrfmiddlewaretoken'}))
            context['receipt'] = result(row)
        else:
            context['snapshot'], context['sha256'] = checkout.current(request.user)
            context['request_id'] = str(uuid.uuid4())
    except checkout.CheckoutError as error:
        context['error'] = str(error);status = error.status
        from .business_views import LABELS
        context['missing_fields'] = [LABELS.get(field, field) for field in error.fields]
    except BankError:
        context['error'] = 'unavailable';status = 403
    except (ValueError, TypeError, UnicodeError, AttributeError):
        context['error'] = 'invalid_request';status = 400
    return private(render(request, 'catalog/checkout.html', context, status=status))
