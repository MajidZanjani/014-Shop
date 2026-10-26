"""Explicit synthetic terms/confirmation and one archived complete-cart bank attempt."""
from datetime import datetime, timedelta
import uuid
from django.db import transaction
from shop.adapters.evidence_archive import PreparedArchive, PreparedReceipt, manifest
from shop.payments import attempts, synthetic_bank
from shop.payments.bank_contract import BankError, BankStart
from shop.payments.purchase_demo import owner_locked
from . import checkout
from .models import SyntheticCheckout, SyntheticCheckoutAcceptance

PROFILE = 'synthetic-checkout-acceptance-v1'
DECLARATION = 'I confirm this synthetic rehearsal only. No real contract, payment or licence/support rights are created.'


def locked(owner, identity):
    owner_locked(owner)
    row = SyntheticCheckout.objects.select_for_update().filter(pk=identity, owner=owner).first()
    if row is None: raise checkout.CheckoutError('not_found', 404)
    if (checkout.digest(row.snapshot) != row.sha256 or row.snapshot.get('effects_authorized') is not False
            or row.snapshot.get('financial_confirmation') is not False):
        raise checkout.CheckoutError('snapshot_mismatch')
    return row


def envelope(row):
    titles = {doc['id']: doc['title'] for doc in row.snapshot['documents']['documents']}
    documents = [{'id': identity, 'title': 'Synthetic ' + titles[identity], 'version': PROFILE,
                  'body': 'Synthetic ' + identity + ' fixture for local testing only. This is not an approved legal document.'}
                 for identity in row.snapshot['required_document_ids']]
    return {'profile': PROFILE, 'checkout_id': str(row.pk), 'checkout_sha256': row.sha256,
            'checkout': row.snapshot, 'fixture_documents': documents, 'declaration': DECLARATION,
            'offer_expires_at': (row.created_at + timedelta(minutes=30)).isoformat(),
            'order_payment_expires_at': (row.created_at + timedelta(minutes=45)).isoformat(),
            'evidence_class': 'local-synthetic', 'financial_confirmation': False, 'effects_authorized': False}


def verify(row):
    try:
        valid = (checkout.digest(row.payload) == row.sha256
            and checkout.digest(row.payload['review']) == row.review_sha256
            and row.payload['review']['checkout_sha256'] == row.checkout.sha256
            and row.payload['review']['checkout'] == row.checkout.snapshot
            and row.payload['confirmation']['confirmed'] is True
            and row.payload['confirmation']['owner_id'] == row.checkout.owner_id)
    except (KeyError, TypeError, ValueError): valid = False
    if not valid: raise checkout.CheckoutError('acceptance_mismatch')


def review(owner, identity):
    synthetic_bank.guard()
    with transaction.atomic(durable=True):
        saved = locked(owner, identity)
        row = SyntheticCheckoutAcceptance.objects.select_related('checkout', 'attempt').filter(checkout=saved).first()
        if row:
            verify(row)
            value = row.payload['review']
        else: value = envelope(saved)
        return value, checkout.digest(value), row


def recover(archive, receipt, identity, body):
    if type(archive) is not PreparedArchive: raise checkout.CheckoutError('local_archive_required', 503)
    try:
        reference = PreparedReceipt(uuid.UUID(receipt['evidence_id']), receipt['sha256'], receipt['size'])
        if manifest(reference) != receipt or reference.evidence_id != identity: raise ValueError()
    except (KeyError, ValueError, TypeError): raise checkout.CheckoutError('archive_mismatch') from None
    if archive.recover(reference) != body: raise checkout.CheckoutError('archive_mismatch')


def retained(row, archive):
    verify(row)
    recover(archive, row.checkout.archive_receipt, row.checkout_id, checkout.canonical(row.checkout.snapshot))
    recover(archive, row.archive_receipt, row.pk, checkout.canonical(row.payload))


def accept(owner, identity, expected, confirmed, archive):
    synthetic_bank.guard()
    if confirmed is not True: raise checkout.CheckoutError('synthetic_confirmation_required', 422)
    if type(archive) is not PreparedArchive: raise checkout.CheckoutError('local_archive_required', 503)
    with transaction.atomic(durable=True):
        saved = locked(owner, identity)
        row = SyntheticCheckoutAcceptance.objects.select_for_update().select_related('checkout').filter(checkout=saved).first()
        if row is None:
            value = envelope(saved)
            if checkout.digest(value) != expected: raise checkout.CheckoutError('review_changed')
            now = attempts.database_now()
            if now >= datetime.fromisoformat(value['offer_expires_at']): raise checkout.CheckoutError('synthetic_offer_expired')
            payload = {'review': value, 'confirmation': {'owner_id': owner.pk, 'confirmed': True, 'confirmed_at': now.isoformat()}}
            row = SyntheticCheckoutAcceptance.objects.create(id=uuid.uuid5(saved.pk, PROFILE), checkout=saved,
                review_sha256=expected, payload=payload, sha256=checkout.digest(payload))
        elif row.review_sha256 != expected: raise checkout.CheckoutError('review_changed')
        verify(row)
    # Both recoverable checkout and explicit fixture confirmation precede acceptance/dispatch.
    checkout.archive_capture(identity, owner, archive)
    receipt = archive.publish(row.pk, checkout.canonical(row.payload))
    recover(archive, manifest(receipt), row.pk, checkout.canonical(row.payload))
    with transaction.atomic(durable=True):
        saved = locked(owner, identity)
        current = SyntheticCheckoutAcceptance.objects.select_for_update().select_related('checkout').get(checkout=saved)
        verify(current)
        if current.sha256 != row.sha256: raise checkout.CheckoutError('acceptance_mismatch')
        if current.simulated_accepted_at is None:
            # Recheck expiry after archive I/O; a prepared row is not an accepted fixture.
            if attempts.database_now() >= datetime.fromisoformat(current.payload['review']['offer_expires_at']):
                raise checkout.CheckoutError('synthetic_offer_expired')
            current.archive_receipt = manifest(receipt)
            current.simulated_accepted_at = attempts.database_now()
            current.save(update_fields=['archive_receipt', 'simulated_accepted_at'])
        return current


def accepted(owner, identity):
    with transaction.atomic(durable=True):
        saved = locked(owner, identity)
        row = SyntheticCheckoutAcceptance.objects.select_related('checkout', 'attempt').filter(checkout=saved).first()
        if row is None or row.simulated_accepted_at is None: raise checkout.CheckoutError('synthetic_acceptance_required', 422)
        verify(row)
        return row


def request_for(row):
    value = row.payload['review']['checkout']
    return BankStart('synthetic-checkout', row.pk, uuid.uuid5(row.pk, 'bank-key'), value['currency'], value['total_minor'])


def pay(owner, identity, archive, *, fault=None):
    synthetic_bank.guard()
    row = accepted(owner, identity)
    retained(row, archive)
    deadline = datetime.fromisoformat(row.payload['review']['order_payment_expires_at'])
    expiry = min(row.simulated_accepted_at + timedelta(minutes=10), deadline)
    attempt = attempts.prepare(request_for(row), expires_at=expiry)
    with transaction.atomic(durable=True):
        saved = locked(owner, identity)
        current = SyntheticCheckoutAcceptance.objects.select_for_update().select_related('checkout').get(checkout=saved)
        verify(current)
        if current.sha256 != row.sha256 or current.simulated_accepted_at != row.simulated_accepted_at:
            raise checkout.CheckoutError('acceptance_mismatch')
        if current.attempt_id not in (None, attempt.pk): raise checkout.CheckoutError('attempt_mismatch')
        current.attempt = attempt;current.save(update_fields=['attempt'])
    # Existing one-way claim means an uncertain attempt is never sent again.
    attempts.dispatch(attempt.pk, archive, fault=fault)
    return accepted(owner, identity)


def reconcile(owner, identity, archive):
    synthetic_bank.guard()
    row = accepted(owner, identity)
    retained(row, archive)
    if row.attempt_id is None: raise checkout.CheckoutError('payment_attempt_required', 422)
    if attempts.request_for(row.attempt) != request_for(row): raise checkout.CheckoutError('attempt_mismatch')
    attempts.reconcile(row.attempt_id, archive)
    return accepted(owner, identity)
