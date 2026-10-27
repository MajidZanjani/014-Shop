"""Supported local finance rehearsal; no actual approval, money or credit authority."""
from io import StringIO
import json
import uuid
from urllib.parse import urlencode
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client, override_settings
from django.utils import timezone
from shop.access.models import CustomerIdentity
from shop.catalog import business_rules, checkout_payment, support_ledger
from shop.catalog.models import SyntheticFulfilment, SyntheticSupportEvent
from shop.catalog.rules import CATALOG
from . import synthetic_bank
from .models import (SyntheticPaymentStaffGrant, SyntheticPaymentOperation,
                     SyntheticOperationResult, SyntheticBankOperation, SyntheticBankTransition)


def require(condition):
    if not condition:
        raise RuntimeError('synthetic finance rehearsal mismatch')


def run(staff, staff_token, staff_name, staff_settings, archive):
    synthetic_bank.guard()
    owner = get_user_model().objects.create_user(username='finance-demo-' + uuid.uuid4().hex)
    identity = CustomerIdentity.objects.create(user=owner, email=uuid.uuid4().hex+'@synthetic.invalid',
                                               verified_at=timezone.now())
    customer = Client(enforce_csrf_checks=True, HTTP_HOST='localhost')
    customer.force_login(owner)
    session = customer.session
    session['shop_verified_identity'] = str(identity.pk)
    session.save()
    customer.get('/purchase/simple/')
    token = customer.cookies['csrftoken'].value

    def customer_post(url, value):
        return customer.post(url, data=json.dumps(value), content_type='application/json', HTTP_X_CSRFTOKEN=token)

    require(customer_post('/api/v1/cart/', {'request_id':str(uuid.uuid4()), 'expected_version':0,
        'catalog_revision':CATALOG['revision'], 'lines':[{'id':str(uuid.uuid4()), 'kind':'support',
        'product_id':CATALOG['support_product_id'], 'quantity':1}]}).status_code == 201)
    details = {name:'' for name in business_rules.LIMITS}
    details.update(legal_business_name='Synthetic finance demo', registered_address='Synthetic address',
                   purchasing_name='Synthetic buyer', business_email='buyer@synthetic.invalid',
                   billing_same_as_registered='on', technical_same_as_purchasing='on')
    saved = customer.post('/purchase/business/', data=urlencode(details | {'request_id':str(uuid.uuid4()),
        'expected_version':'0', 'schema_version':str(business_rules.SCHEMA_VERSION),
        'source_sha256':business_rules.SOURCE_SHA256}), content_type='application/x-www-form-urlencoded',
        HTTP_X_CSRFTOKEN=token)
    require(saved.status_code == 303)
    reviewed = customer.get('/api/v1/checkout-rehearsal/')
    require(reviewed.status_code == 200)
    captured = customer_post('/api/v1/checkout-rehearsal/', {'request_id':str(uuid.uuid4()),
                                                          'sha256':reviewed.json()['sha256']})
    require(captured.status_code == 201)
    checkout_id = uuid.UUID(captured.json()['id'])
    # Same explicit archive-before-acceptance step as the complete-cart fixture.
    from shop.catalog import checkout
    checkout.archive_capture(checkout_id, owner, archive)
    payment_url = '/api/v1/checkout-rehearsal/'+str(checkout_id)+'/payment/'
    reviewed = customer.get(payment_url)
    require(reviewed.status_code == 200)
    require(customer_post(payment_url, {'action':'accept', 'sha256':reviewed.json()['sha256'],
                                       'confirmed':True}).status_code == 200)
    original_start = synthetic_bank.start
    def authorize(request, **options):
        options['outcome'] = 'authorized'
        return original_start(request, **options)
    with patch.object(synthetic_bank, 'start', side_effect=authorize):
        authorized = customer_post(payment_url, {'action':'pay'})
    require(authorized.status_code == 200 and authorized.json()['simulated_paid'] is False)
    require(customer_post(payment_url, {'action':'provision'}).status_code != 200)
    accepted = checkout_payment.accepted(owner, checkout_id)

    def staff_post(url, value, form=False):
        with override_settings(**staff_settings):
            return staff.post(url, data=urlencode(value) if form else json.dumps(value),
                content_type='application/x-www-form-urlencoded' if form else 'application/json',
                HTTP_X_CSRFTOKEN=staff_token)

    def assignment(kind):
        call_command('local_staff', 'grant-payment', username=staff_name, acceptance=str(accepted.pk),
                     operation_kind=kind, stdout=StringIO())
        scope = SyntheticPaymentStaffGrant.objects.get(user__username=staff_name, acceptance=accepted, kind=kind)
        return '/staff/payments/'+str(scope.pk)+'/'

    capture_url = assignment('capture')
    key = str(uuid.uuid4())
    for _ in range(2):
        require(staff_post(capture_url, {'action':'prepare', 'request_id':key}, form=True).status_code == 303)
    original_mutate = synthetic_bank.mutate
    def lose_response(request, **options):
        options['fault'] = 'after_commit'
        return original_mutate(request, **options)
    with patch.object(synthetic_bank, 'mutate', side_effect=lose_response):
        uncertain = staff_post(capture_url, {'action':'dispatch'})
    require(uncertain.status_code == 409 and uncertain.json()['error'] == 'payment_operation_uncertain_use_lookup')
    with patch.object(synthetic_bank, 'mutate', side_effect=AssertionError('blind capture retry')):
        retry = staff_post(capture_url, {'action':'dispatch'})
        require(retry.status_code == 200 and retry.json()['operation']['lookup_required'])
        recovered = staff_post(capture_url, {'action':'reconcile'})
    require(recovered.status_code == 200 and recovered.json()['operation']['status'] == 'captured')
    granted = customer_post(payment_url, {'action':'provision'})
    require(granted.status_code == 200 and granted.json()['fulfilment']['support_seconds'] == 36000)
    support_url = '/purchase/checkout-rehearsal/'+str(checkout_id)+'/support/'
    reserve = {'action':'reserve', 'request_id':str(uuid.uuid4()), 'task_id':str(uuid.uuid4()), 'seconds':60}
    for _ in range(2):
        require(customer_post(support_url, reserve).status_code == 200)
    before = support_ledger.read(owner, checkout_id, archive)
    require(before['reserved_seconds'] == 60)
    retained_acceptance = accepted.sha256
    refund_url = assignment('refund')
    key = str(uuid.uuid4())
    for _ in range(2):
        require(staff_post(refund_url, {'action':'prepare', 'request_id':key}).status_code == 200)
    require(staff_post(refund_url, {'action':'dispatch'}, form=True).status_code == 303)
    with patch.object(synthetic_bank, 'mutate', side_effect=AssertionError('blind refund retry')):
        for action in ('dispatch', 'reconcile'):
            result = staff_post(refund_url, {'action':action})
            require(result.status_code == 200 and result.json()['operation']['status'] == 'refunded')
    require(all(value is None for value in result.json()['operation']['financial_policy'].values()))
    require(result.json()['operation']['effects_authorized'] is False)
    require(support_ledger.read(owner, checkout_id, archive) == before)
    require(customer_post(payment_url, {'action':'provision'}).json()['fulfilment']['support_seconds'] == 36000)
    require(SyntheticFulfilment.objects.filter(acceptance=accepted).count() == 1)
    require(SyntheticSupportEvent.objects.filter(fulfilment__acceptance=accepted).count() == 1)
    require(checkout_payment.accepted(owner, checkout_id).sha256 == retained_acceptance)
    require(SyntheticBankOperation.objects.filter(merchant='synthetic-checkout', reference=accepted.pk).count() == 1)
    require(SyntheticBankTransition.objects.filter(operation_id=accepted.attempt.provider_operation_id).count() == 2)
    require(SyntheticPaymentOperation.objects.filter(acceptance=accepted).count() == 2)
    require(SyntheticOperationResult.objects.filter(operation__acceptance=accepted).count() == 2)
    call_command('local_staff', 'revoke-payment', username=staff_name, acceptance=str(accepted.pk),
                 operation_kind='refund', stdout=StringIO())
    require(staff_post(refund_url, {'action':'reconcile'}).status_code == 404)
    return {'authorization_is_not_payment':True, 'capture_loss_lookup_only':True,
            'staff_two_factors_and_exact_assignment':True, 'form_and_json_retries_once':True,
            'provider_operations':1, 'immutable_transitions':2, 'support_seconds_unchanged':36000, 'reservation_seconds_unchanged':60,
            'actual_financial_confirmation':False, 'actual_refund':False, 'revoked_assignment_denied':True}
