"""Archived pre-acceptance ASIC withdrawal, final expiry and offer replacement."""
from datetime import datetime, timezone as utc_timezone
from pathlib import Path
import re
import uuid

from django.conf import settings
from django.db import transaction
from django.db.models.functions import Now

from shop.access.effects import local_effect
from shop.adapters.evidence_archive import PreparedArchive, manifest
from shop.catalog import checkout_payment as payment
from shop.catalog.models import SyntheticCheckoutAcceptance
from shop.payments import attempts
from . import catalog, checkout, invitations, offers, staff_review
from .errors import ShbError
from .models import RequestClosure, SupportOffer, SupportRequest, SupportCheckout

OPEN_REQUESTS = ('submitted','needs_information','under_review','offer_issued','offer_expired')


def fail():
    raise ShbError('matching_unaccepted_request_or_offer_required')


def unfenced(row):
    if RequestClosure.objects.filter(request=row, applied_at__isnull=True).exists():
        raise ShbError('request_or_offer_closing')


def target(row, identity):
    active = SupportOffer.objects.select_for_update().filter(request=row,
        state__in=('prepared','issued','paid')).first()
    if (str(active.pk) if active else '') != identity: fail()
    if row.state not in OPEN_REQUESTS or active and active.state == 'paid': fail()
    if active:
        offers.verify(active)
        saved = SupportCheckout.objects.select_for_update().filter(offer=active).first()
        if saved and SyntheticCheckoutAcceptance.objects.select_for_update().filter(
                checkout_id=saved.pk, simulated_accepted_at__isnull=False).exists(): fail()
    return active


def verify(saved):
    if (saved.sha256 != catalog.digest(saved.payload)
            or catalog.digest(saved.request.payload) != saved.request.sha256
            or saved.payload['request_payload'] != saved.request.payload
            or saved.payload['request_id'] != str(saved.request_id)
            or saved.payload['request_sha256'] != saved.request.sha256
            or saved.payload['request_revision'] != saved.request.revision
            or saved.payload['offer_id'] != (str(saved.offer_id) if saved.offer_id else '')
            or saved.offer_id and (saved.payload['offer_sha256'] != saved.offer.sha256
                or saved.payload['offer_payload'] != saved.offer.payload)): fail()


def prepare(row, key, action, reason, actor):
    offer = target(row, actor.pop('offer_id'))
    unfenced(row)
    if action in ('expire','replace') and offer is None: fail()
    if action == 'expire' and attempts.database_now() < offer.expires_at: fail()
    hold = offers.held_request(row)
    state = 'under_review' if action == 'replace' else 'offer_expired' if action == 'expire' else 'withdrawn'
    payload = {'schema':1,'kind':'shb-request-closure','evidence_class':'local-synthetic',
        'effects_authorized':False,'financial_confirmation':False,
        'request_id':str(row.pk),'request_revision':row.revision,'request_sha256':row.sha256,
        'request_payload':row.payload, 'offer_payload':offer.payload if offer else None,
        'customer_id':row.invitation.customer_id,'review_version':row.quotation.review_version,
        'offer_id':str(offer.pk) if offer else '', 'offer_sha256':offer.sha256 if offer else '',
        'prior_state':row.state,'offer_state':offer.state if offer else '', 'action':action,
        'reason':reason,'result_state':state,'release_discount':action != 'replace',
        'reservation_id':str(hold.pk) if hold else '', 'reservation_sha256':hold.sha256 if hold else '',
        'requested_at':attempts.database_now().isoformat(), 'actor':actor}
    return RequestClosure.objects.create(id=uuid.uuid5(offer.pk if offer else row.pk,'shb-preacceptance-close-v1'),
        request=row,offer=offer,request_key=key,payload=payload,sha256=catalog.digest(payload))


@local_effect('shb-close', guard=checkout.guard, error=ShbError)
def close(request, identity, value, archive):
    try:
        key = uuid.UUID(value['request_id']); version = value['expected_review_version']
        if type(version) is not int or not 0 <= version < 1000000000: raise ValueError()
        if type(value['scope_sha256']) is not str or not re.fullmatch('[a-f0-9]{64}',value['scope_sha256']): raise ValueError()
        if type(value['offer_id']) is not str: raise ValueError()
        if value['offer_id']: uuid.UUID(value['offer_id'])
        if value['action'] not in ('withdraw','expire','replace'): raise ValueError()
        if type(value['reason']) is not str or not 1 <= len(value['reason'].strip()) <= 512: raise ValueError()
    except (KeyError,ValueError,TypeError,AttributeError): raise ShbError('invalid_request',400) from None
    with transaction.atomic(durable=True):
        row, credential = staff_review.authorized(request, identity, lock=True)
        saved = RequestClosure.objects.filter(request=row,request_key=key).select_related('request','offer').first()
        if saved:
            verify(saved)
            if (saved.payload['actor'].get('user_id') != request.user.pk
                    or saved.payload['review_version'] != version or saved.payload['request_sha256'] != value['scope_sha256']
                    or saved.payload['offer_id'] != value['offer_id'] or saved.payload['action'] != value['action']
                    or saved.payload['reason'] != value['reason'].strip()): raise ShbError('request_conflict')
            created = False
        else:
            if row.sha256 != value['scope_sha256'] or row.quotation.review_version != version: fail()
            verified = datetime.fromtimestamp(request.session['shop_staff_mfa']['verified_at'],tz=utc_timezone.utc)
            saved = prepare(row,key,value['action'],value['reason'].strip(),
                {'kind':'assigned-staff','user_id':request.user.pk,'credential_generation':str(credential.generation),
                    'mfa_verified_at':verified.isoformat(),'offer_id':value['offer_id']})
            created = True
    return apply(saved,archive), created


def apply(saved, archive):
    verify(saved)
    if saved.offer_id and saved.offer.published_at is not None:
        offers.recover(saved.offer,archive)
    raw = catalog.canonical(saved.payload)
    if saved.applied_at is not None:
        payment.recover(archive,saved.archive_receipt,saved.pk,raw)
        return saved
    receipt = manifest(archive.publish(saved.pk,raw)); payment.recover(archive,receipt,saved.pk,raw)
    # The committed deliberate intent is resumable after invitation/staff expiry.
    # It cannot authorize any new/replacement offer or new payment.
    with transaction.atomic(durable=True):
        row = offers.lock_request(saved.request_id)
        current = RequestClosure.objects.select_for_update(of=('self',)).select_related('request','offer').get(pk=saved.pk)
        verify(current)
        if current.sha256 != saved.sha256: fail()
        if current.applied_at is not None:
            payment.recover(archive,current.archive_receipt,current.pk,catalog.canonical(current.payload))
            return current
        offer = target(row,current.payload['offer_id'])
        if row.state != current.payload['prior_state'] or row.quotation.review_version != current.payload['review_version']: fail()
        hold = offers.held_request(row)
        if (str(hold.pk) if hold else '') != current.payload['reservation_id']: fail()
        current.archive_receipt = receipt; current.applied_at = attempts.database_now()
        current.save(update_fields=['archive_receipt','applied_at'])
        if offer:
            offer.state = 'closed' if offer.published_at else 'abandoned'
            offer.save(update_fields=['state'])
        row.state = current.payload['result_state']; row.save(update_fields=['state'])
        if hold and current.payload['release_discount']:
            hold.state='released'; hold.release_lifecycle=current
            hold.save(update_fields=['state','release_lifecycle'])
        from .transaction_mail import queue
        queue('request-closed',current)
        return current


@local_effect('shb-close', guard=checkout.guard, error=ShbError)
def customer_withdraw(request, identity, key, archive):
    key = checkout.identity(key)
    with transaction.atomic(durable=True):
        invitation = invitations.current(request,lock=True)
        if invitation is None: raise ShbError('invitation_required',403)
        checkout.lock_customer(invitation.customer)
        scope = checkout.session_digest(request)
        saved = RequestClosure.objects.select_related('request__invitation','offer').filter(
            offer_id=identity,request_key=key).first()
        if saved:
            actor=saved.payload['actor']
            if (actor.get('kind')!='invitation-bearer' or actor.get('invitation_id')!=str(invitation.pk)
                    or actor.get('session_digest')!=scope or saved.payload['action']!='withdraw'):
                raise ShbError('request_conflict')
        else:
            _,offer = offers.customer_offer(request,identity,lock=True)
            offers.open_offer(offer)
            saved = prepare(offer.request,key,'withdraw','Customer deliberately withdrew this unpaid ASIC offer.',
                {'kind':'invitation-bearer','invitation_id':str(invitation.pk),
                    'session_digest':scope,'named_identity_verified':False,'offer_id':str(offer.pk)})
    return apply(saved,archive)


def pending():
    return RequestClosure.objects.filter(applied_at__isnull=True)


def expired_pending():
    # Existing accepted checkouts have their own proved safe closing/reconciliation.
    return SupportOffer.objects.filter(state__in=('prepared','issued'),expires_at__lte=Now(),
        requestclosure__isnull=True).exclude(supportcheckout__checkout__syntheticcheckoutacceptance__simulated_accepted_at__isnull=False)


@local_effect('shb-close', guard=checkout.guard, error=ShbError)
def expire(identity, archive):
    with transaction.atomic(durable=True):
        candidate = SupportOffer.objects.get(pk=identity)
        row = offers.lock_request(candidate.request_id)
        saved = RequestClosure.objects.select_related('request','offer').filter(offer=candidate).first()
        if saved is None:
            saved = prepare(row,uuid.uuid5(candidate.pk,'shb-final-expiry-v1'),'expire',
                'Unaccepted dated offer reached its final purchase deadline.',
                {'kind':'deadline-worker','offer_id':str(candidate.pk)})
    return apply(saved,archive)


def recover_once():
    saved = pending().select_related('request','offer').order_by('pk').first()
    with PreparedArchive(Path(settings.LOCAL_CHECKOUT_ARCHIVE_ROOT)) as archive:
        if saved:
            apply(saved,archive); return True
        offer = expired_pending().order_by('pk').first()
        if offer is None: return False
        try: expire(offer.pk,archive)
        except ShbError as error:
            if error.code != 'matching_unaccepted_request_or_offer_required': raise
            return False  # Acceptance won the selection race; its own bank lifecycle applies.
        return True
