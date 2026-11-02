"""Matching dated ASIC offers on the retained request/checkout/payment records."""
from datetime import datetime, timedelta, timezone as utc_timezone
import hashlib
import re
import uuid

from django.core import signing
from django.db import transaction
from django.db.models import Max

from shop.access.effects import local_effect
from shop.adapters.evidence_archive import manifest
from shop.catalog import checkout as shared, checkout_payment as payment
from shop.catalog.models import DraftCart, CartSnapshot, SyntheticCheckout, SyntheticCheckoutKey, QuotationRequest
from shop.payments import attempts
from . import catalog, checkout, invitations, staff_review
from .errors import ShbError
from .models import SupportOffer, SupportRequest, SupportRequestReview, SupportCheckout, DiscountCode, DiscountReservation

SALT = 'shb-asic-offer-review-v1'


def verify(offer):
    row = offer.request
    if (catalog.digest(offer.payload) != offer.sha256 or offer.payload['request_sha256'] != row.sha256
            or offer.payload['request_revision'] != row.revision or catalog.digest(row.payload) != row.sha256
            or offer.payload['customer_id'] != row.invitation.customer_id):
        raise ShbError('offer_scope_changed')


def recover(offer, archive):
    verify(offer)
    if offer.published_at is None: raise ShbError('offer_not_issued')
    payment.recover(archive, offer.archive_receipt, offer.pk, catalog.canonical(offer.payload))


def lock_request(identity):
    candidate = SupportRequest.objects.get(pk=identity)
    QuotationRequest.objects.select_for_update().get(pk=candidate.quotation_id)
    return SupportRequest.objects.select_for_update(of=('self',)).select_related('invitation', 'quotation').get(pk=identity)


def lock_checkout(saved):
    """Global order: owner, quotation/request, offer, checkout, acceptance, attempt, coupon."""
    scope = SupportCheckout.objects.filter(checkout=saved).first()
    if scope is None or scope.offer_id is None: return
    candidate = SupportOffer.objects.get(pk=scope.offer_id)
    lock_request(candidate.request_id)
    offer = SupportOffer.objects.select_for_update().select_related('request__invitation').get(pk=scope.offer_id)
    verify(offer)
    from .models import RequestClosure
    if RequestClosure.objects.filter(offer=offer).exists():
        raise shared.CheckoutError('request_or_offer_closing',409)
    if saved.snapshot.get('asic_offer') != reference(offer) or saved.snapshot['purchase'] != offer.payload['purchase']:
        raise shared.CheckoutError('offer_scope_changed')


def reference(offer):
    return {'id':str(offer.pk), 'sha256':offer.sha256, 'payload':offer.payload}


def held_request(row):
    hold = DiscountReservation.objects.filter(request=row, state='reserved').first()
    if hold:
        DiscountCode.objects.select_for_update().get(pk=hold.discount_id)
        hold = DiscountReservation.objects.select_for_update().get(pk=hold.pk)
        if (hold.state != 'reserved' or catalog.digest(hold.snapshot) != hold.sha256
                or hold.snapshot != row.payload['purchase'].get('discount_policy')):
            raise ShbError('discount_reservation_changed')
    return hold


@local_effect('shb-offer', guard=checkout.guard, error=ShbError)
def issue(request, identity, value, archive):
    try:
        key = uuid.UUID(value['request_id'])
        version = value['expected_review_version']
        if type(version) is not int or not 0 <= version < 1000000000: raise ValueError()
        if type(value['scope_sha256']) is not str or not re.fullmatch('[a-f0-9]{64}', value['scope_sha256']): raise ValueError()
        if any(type(value[k]) is not str or not 1 <= len(value[k].strip()) <= 1000 for k in ('prerequisites', 'exclusions')): raise ValueError()
    except (KeyError, TypeError, ValueError, AttributeError): raise ShbError('invalid_request',400) from None
    with transaction.atomic(durable=True):
        row, credential = staff_review.authorized(request, identity, lock=True)
        from .lifecycle import unfenced
        unfenced(row)
        previous = SupportOffer.objects.filter(request=row, issue_key=key).select_related('request__invitation').first()
        if previous:
            if previous.state in ('closed','abandoned'): raise ShbError('offer_closed')
            if (previous.issuer_id != request.user.pk or previous.payload['review_version'] != version
                    or previous.payload['request_sha256'] != value['scope_sha256']
                    or previous.payload['scope']['prerequisites'] != value['prerequisites'].strip()
                    or previous.payload['scope']['exclusions'] != value['exclusions'].strip()):
                raise ShbError('request_conflict')
            if previous.state=='prepared' and previous.issuer_generation!=credential.generation:
                raise ShbError('offer_issuer_changed')
            offer = previous
        else:
            if row.state != 'under_review' or row.sha256 != value['scope_sha256'] or row.quotation.review_version != version:
                raise ShbError('matching_technical_review_required')
            event = SupportRequestReview.objects.select_related('review').filter(request=row,
                review__version=version, review__decision='ready_for_commercial_review').first()
            if event is None or SupportOffer.objects.filter(request=row, state__in=['prepared','issued','paid']).exists():
                raise ShbError('matching_technical_review_required')
            if SupportOffer.objects.filter(request=row,payload__review_version__gte=version).exists():
                raise ShbError('fresh_technical_review_required')
            hold = held_request(row)
            policy = catalog.synthetic_offer()
            purchase = catalog.quote('shb-asic-25h', row.payload['purchase']['quantity'], offer=policy,
                discount_bps=hold.snapshot['percentage_bps'] if hold else 0)
            if hold: purchase['discount_policy'] = hold.snapshot
            at = attempts.database_now(); until = at + timedelta(days=14)
            revision = (SupportOffer.objects.filter(request=row).aggregate(last=Max('revision'))['last'] or 0) + 1
            marker = request.session['shop_staff_mfa']
            verified_at=datetime.fromtimestamp(marker['verified_at'],tz=utc_timezone.utc)
            payload = {'schema':1, 'kind':'shb-asic-offer', 'evidence_class':'local-synthetic',
                'effects_authorized':False, 'financial_confirmation':False, 'request_id':str(row.pk),
                'request_revision':row.revision, 'request_sha256':row.sha256, 'customer_id':row.invitation.customer_id,
                'company_name':row.invitation.company_name, 'review_id':str(event.pk), 'review_version':version,
                'revision':revision, 'issued_at':at.isoformat(), 'expires_at':until.isoformat(),
                'issued_by':{'user_id':request.user.pk,'credential_generation':str(credential.generation),
                    'mfa_verified_at':verified_at.isoformat()},
                'technical_review':{'id':str(event.pk),'reviewer_id':event.review.reviewer_id,
                    'credential_generation':str(event.review.reviewer_generation),
                    'mfa_verified_at':event.review.mfa_verified_at.isoformat(),
                    'decision':event.review.decision,'scope_sha256':event.review.snapshot_digest},
                'offer_policy_revision':'synthetic-14-calendar-day-offer-v1', 'policy':policy,
                'documents':checkout.value(row.invitation,row.payload['details'],key,purchase,policy=policy)['documents'],
                'required_document_ids':['terms','support','refund','asic'],
                'purchase':purchase, 'scope':{'project_reference':row.payload['known_project_reference'] or row.payload['details']['project_reference'],
                    'assistance':row.payload['details']['assistance'], 'design_context':row.payload['details']['design_context'],
                    'requested_timing':row.payload['details']['timing'], 'prerequisites':value['prerequisites'].strip(),
                    'exclusions':value['exclusions'].strip()}, 'support_tracking':'manual-outside-shop'}
            offer = SupportOffer.objects.create(request=row, review=event, issue_key=key, revision=revision,
                issuer=request.user, issuer_generation=credential.generation,
                mfa_verified_at=verified_at,
                issued_at=at, expires_at=until, payload=payload, sha256=catalog.digest(payload))
        verify(offer)
        if offer.state != 'prepared':
            recover(offer, archive); return offer, False
    receipt = manifest(archive.publish(offer.pk, catalog.canonical(offer.payload)))
    payment.recover(archive, receipt, offer.pk, catalog.canonical(offer.payload))
    with transaction.atomic(durable=True):
        row, _ = staff_review.authorized(request, identity, lock=True)
        unfenced(row)
        current = SupportOffer.objects.select_for_update().select_related('request__invitation').get(pk=offer.pk)
        verify(current)
        if current.sha256 != offer.sha256: raise ShbError('offer_scope_changed')
        if current.state == 'prepared':
            if row.state != 'under_review' or row.quotation.review_version != current.payload['review_version']:
                raise ShbError('matching_technical_review_required')
            if attempts.database_now() >= current.expires_at: raise ShbError('offer_expired')
            current.archive_receipt = receipt; current.published_at = attempts.database_now(); current.state = 'issued'
            current.save(update_fields=['archive_receipt','published_at','state'])
            row.state = 'offer_issued'; row.save(update_fields=['state'])
            from .transaction_mail import queue
            queue('offer-issued',current)
            return current, True
        recover(current, archive); return current, False


def customer_offer(request, identity, *, lock=False):
    invitation = invitations.current(request, lock=lock)
    if invitation is None: raise ShbError('invitation_required',403)
    checkout.lock_customer(invitation.customer) if lock else None
    candidate = SupportOffer.objects.filter(pk=identity, request__invitation__customer_id=invitation.customer_id).first()
    if candidate is None or not invitation.asic_allowed: raise ShbError('not_found',404)
    if lock: lock_request(candidate.request_id)
    offers = SupportOffer.objects.select_related('request__invitation')
    if lock: offers = offers.select_for_update(of=('self',))
    offer = offers.get(pk=identity); verify(offer)
    if (offer.payload['company_name'] != invitation.company_name or invitation.project_reference
            and invitation.project_reference != offer.payload['scope']['project_reference']): raise ShbError('not_found',404)
    if offer.state not in ('issued','paid') or offer.published_at is None: raise ShbError('offer_not_issued')
    return invitation, offer


def open_offer(offer):
    from .lifecycle import unfenced
    unfenced(offer.request)
    if offer.state != 'issued' or attempts.database_now() >= offer.expires_at: raise ShbError('offer_expired_or_closed')


def snapshot(invitation, offer, data, key):
    value = checkout.value(invitation, data, key, offer.payload['purchase'], policy=offer.payload['policy'])
    value['asic_offer'] = reference(offer)
    value['documents'] = offer.payload['documents']
    value['required_document_ids'] = offer.payload['required_document_ids']
    return value


def review(request, identity, data, key, archive):
    checkout.guard(); key = checkout.identity(key)
    with transaction.atomic(durable=True):
        invitation, offer = customer_offer(request, identity, lock=True); open_offer(offer); recover(offer,archive)
        if data['company_name'] != invitation.company_name: raise ShbError('company_clarification_required')
        value = snapshot(invitation,offer,data,key); at = attempts.database_now()
        clocks = {'review_expires_at':min(at+timedelta(minutes=30),offer.expires_at).isoformat(),
            'order_payment_expires_at':min(at+timedelta(minutes=45),offer.expires_at).isoformat()}
        token = signing.dumps({'sha256':catalog.digest(value),'session_digest':checkout.session_digest(request),**clocks},salt=SALT)
        return token, dict(value,**clocks)


def capture(request, identity, data, key, token, archive):
    checkout.guard(); key = checkout.identity(key)
    if data.get('accept_terms') is not True or data.get('privacy_acknowledged') is not True:
        raise ShbError('separate_acceptance_required',422)
    if type(token) is not str or len(token)>2048: raise ShbError('review_changed')
    with transaction.atomic(durable=True):
        invitation, offer = customer_offer(request,identity,lock=True); recover(offer,archive)
        _, fingerprint = checkout.submission(data); scope=checkout.session_digest(request)
        token_hash=hashlib.sha256(token.encode()).hexdigest()
        previous=SupportCheckout.objects.select_related('checkout').filter(offer=offer).first()
        if previous:
            if (previous.invitation_id != invitation.pk or previous.request_id != key or previous.session_digest != scope
                    or previous.submission_sha256 != fingerprint or previous.review_sha256 != token_hash): raise ShbError('request_conflict')
            return previous.checkout
        open_offer(offer)
        if data['company_name'] != invitation.company_name: raise ShbError('company_clarification_required')
        try:
            signed=signing.loads(token,salt=SALT); until=datetime.fromisoformat(signed['review_expires_at'])
            deadline=datetime.fromisoformat(signed['order_payment_expires_at'])
            if (until.tzinfo is None or deadline.tzinfo is None or not until<=deadline<=offer.expires_at
                    or signed['session_digest']!=scope or attempts.database_now()>=until): raise ValueError()
        except (signing.BadSignature,ValueError,TypeError,KeyError): raise ShbError('review_changed') from None
        hold=held_request(offer.request)
        if (hold.snapshot if hold else None)!=offer.payload['purchase'].get('discount_policy'): raise ShbError('discount_reservation_changed')
        value=snapshot(invitation,offer,data,key)
        if catalog.digest(value)!=signed['sha256']: raise ShbError('review_changed')
        value.update(review_expires_at=signed['review_expires_at'],order_payment_expires_at=signed['order_payment_expires_at'])
        cart,_=DraftCart.objects.get_or_create(owner=invitation.customer)
        cart=DraftCart.objects.select_for_update().get(pk=cart.pk)
        if CartSnapshot.objects.filter(cart=cart,request_id=key).exists(): raise ShbError('request_conflict')
        cart.version+=1;cart.save(update_fields=['version'])
        saved=CartSnapshot.objects.create(cart=cart,version=cart.version,request_id=key,
            catalog_revision=catalog.CATALOG['revision'],lines=[value['purchase']],
            evaluation={'release':'shb-1.1','evidence_class':'local-synthetic','live_payable':False})
        row=SyntheticCheckout.objects.create(owner=invitation.customer,request_id=key,cart_snapshot=saved,
            business_snapshot=None,snapshot=value,sha256=catalog.digest(value))
        SupportCheckout.objects.create(checkout=row,invitation=invitation,request_id=key,
            submission_sha256=fingerprint,review_sha256=token_hash,session_digest=scope,offer=offer)
        SyntheticCheckoutKey.objects.create(owner=invitation.customer,request_id=key,checkout=row)
        return row


def ensure_payment_open(saved):
    scope=SupportCheckout.objects.filter(checkout=saved).select_related('offer__request__invitation').first()
    if scope and scope.offer_id:
        from .models import PaidOrder
        if scope.offer.state=='paid' and PaidOrder.objects.filter(acceptance__checkout=saved).exists(): return
        try: open_offer(scope.offer)
        except ShbError as error: raise shared.CheckoutError(error.code,error.status) from None
