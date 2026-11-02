"""Minimum-form SHB scope on shared checkout/acceptance/archived bank records."""
from datetime import datetime, timedelta
import hashlib
import uuid

from django.core import signing
from django.db import transaction
from django.utils.crypto import salted_hmac

from shop.catalog import checkout as shared_checkout, checkout_payment as payment
from shop.catalog.models import CartSnapshot, DraftCart, SyntheticCheckout, SyntheticCheckoutKey
from shop.payments import attempts
from django.contrib.auth import get_user_model
from . import catalog, discounts, invitations
from .errors import ShbError
from .models import SupportCheckout

SALT = 'shb-exact-review-v1'


def guard():
    try: invitations.fixture_guard()
    except ValueError: raise ShbError('Live checkout awaits approved commercial and provider configuration.', 503) from None


def lock_customer(owner):
    # Invitation-authorized new purchases do not claim mailbox or named identity verification.
    user=get_user_model().objects.select_for_update().filter(pk=owner.pk,is_active=True,is_staff=False,is_superuser=False).first()
    if user is None:raise shared_checkout.CheckoutError('invitation_required',403)
    return user


def session_digest(request):
    key = request.session.session_key
    if not key: raise ShbError('invitation_required', 403)
    return salted_hmac('shb-purchase-session-v1', key, algorithm='sha256').hexdigest()


def submission(cleaned):
    details = {k:v for k,v in cleaned.items() if k not in ('accept_terms', 'privacy_acknowledged', 'discount_code')}
    code = cleaned.get('discount_code', '')
    return details, catalog.digest({'details':details, 'discount_verifier':discounts.verifier(code) if code else None})


def identity(value):
    try: return uuid.UUID(str(value))
    except (ValueError, TypeError, AttributeError): raise ShbError('invalid_request', 422) from None


def eligible(request, cleaned, *, lock=False):
    row = invitations.current(request, lock=lock)
    if row is None: raise ShbError('invitation_required', 403)
    if cleaned['variant'] != 'shb-fpga-10h' or not row.fpga_eligible:
        raise ShbError('Matching approved ASIC offer required before checkout.', 422)
    if cleaned['company_name'].strip() != row.company_name: raise ShbError('company_clarification_required')
    return row


def value(invitation, cleaned, request_id, purchase, *, policy=None):
    details, fingerprint = submission(cleaned)
    policy = policy if policy is not None else catalog.synthetic_offer()
    documents = [{'id':key, 'title':title, 'version':policy[key + '_revision'],
        'body':'Synthetic test fixture only. No approved legal terms or real purchase.'}
        for key,title in (('terms','Purchase terms'), ('support','Support terms'), ('refund','Refund policy'), ('privacy','Privacy Policy'))
        if key != 'support']
    documents.append({'id':'support', 'title':'Support terms', 'version':policy['manual_charging_policy_revision'],
        'body':'Synthetic manual support terms. SLL tracks time and sends task emails manually; no online balance or SLA.'})
    if purchase['variant_id'] == 'shb-asic-25h':
        documents.append({'id':'asic', 'title':'ASIC support supplement', 'version':policy['asic_supplement_revision'],
            'body':'Synthetic ASIC terms only: 25-hour bundles for the approved SLL-IP scope. No expiry in this fixture; no tape-out, sign-off, EDA/PDK access or outcome guarantee. SLL tracks time and sends task emails manually.'})
    return {'schema':1, 'release':'shb-1.1', 'kind':'supporting-hours-bundle-checkout',
        'evidence_class':'local-synthetic', 'effects_authorized':False, 'financial_confirmation':False,
        'customer_id':invitation.customer_id, 'invitation_id':str(invitation.pk), 'request_id':str(request_id),
        'eligibility_reference':invitation.eligibility_reference, 'source_sha256':catalog.CATALOG['source_sha256'],
        'submission_sha256':fingerprint, 'details':details, 'purchase':purchase,
        'documents':{'documents':documents}, 'required_document_ids':['terms','support','refund'] + (['asic'] if purchase['variant_id']=='shb-asic-25h' else []),
        'privacy_revision':policy['privacy_revision'], 'support_terms_revision':policy['terms_revision'],
        'currency':purchase['currency'], 'total_minor':purchase['total_minor'],
        'policy':policy, 'support_tracking':'manual-outside-shop', 'named_identity_verified':False}


def review_token(request, cleaned, request_id, purchase):
    guard(); request_id = identity(request_id)
    with transaction.atomic(durable=True):
        invitation = eligible(request, cleaned, lock=True)
        base = value(invitation, cleaned, request_id, purchase)
        at = attempts.database_now()
        clocks = {'review_expires_at':(at + timedelta(minutes=30)).isoformat(),
            'order_payment_expires_at':(at + timedelta(minutes=45)).isoformat()}
        token = signing.dumps({'sha256':catalog.digest(base), 'session_digest':session_digest(request), **clocks}, salt=SALT)
        return token, dict(base, **clocks)


def capture(request, cleaned, request_id, token):
    guard(); request_id = identity(request_id)
    if cleaned.get('accept_terms') is not True or cleaned.get('privacy_acknowledged') is not True:
        raise ShbError('Accept the reviewed terms and acknowledge privacy separately.', 422)
    if type(token) is not str or len(token) > 2048: raise ShbError('review_changed')
    details, fingerprint = submission(cleaned)
    # Existing original identity is resolved before current pricing/code validity.
    invitation = eligible(request, cleaned)
    if cleaned.get('discount_code') and not SupportCheckout.objects.filter(invitation=invitation, request_id=request_id).exists():
        discounts.take_attempt(request)
    with transaction.atomic(durable=True):
        invitation = eligible(request, cleaned, lock=True)
        lock_customer(invitation.customer)
        old = SupportCheckout.objects.select_related('checkout').filter(invitation=invitation, request_id=request_id).first()
        token_sha256 = hashlib.sha256(token.encode()).hexdigest()
        scope = session_digest(request)
        if old:
            if (old.submission_sha256 != fingerprint or old.review_sha256 != token_sha256 or old.session_digest != scope):
                raise ShbError('request_conflict')
            return old.checkout
        try:
            signed = signing.loads(token, salt=SALT)
            until = datetime.fromisoformat(signed['review_expires_at'])
            payment_until = datetime.fromisoformat(signed['order_payment_expires_at'])
            if (until.tzinfo is None or payment_until <= until or signed['session_digest'] != scope
                    or attempts.database_now() >= until): raise ValueError()
        except (signing.BadSignature, ValueError, TypeError, KeyError): raise ShbError('review_changed') from None
        claim = discounts.claim(invitation, cleaned['variant'], cleaned['discount_code']) if cleaned.get('discount_code') else None
        purchase = catalog.quote(cleaned['variant'], cleaned['quantity'], offer=catalog.synthetic_offer(),
            discount_bps=claim[2]['percentage_bps'] if claim else 0)
        if claim: purchase['discount_policy'] = claim[2]
        snapshot = value(invitation, cleaned, request_id, purchase)
        if catalog.digest(snapshot) != signed['sha256']: raise ShbError('review_changed')
        snapshot.update(review_expires_at=signed['review_expires_at'], order_payment_expires_at=signed['order_payment_expires_at'])
        cart, _ = DraftCart.objects.get_or_create(owner=invitation.customer)
        cart = DraftCart.objects.select_for_update().get(pk=cart.pk)
        if CartSnapshot.objects.filter(cart=cart, request_id=request_id).exists(): raise ShbError('request_conflict')
        cart.version += 1; cart.save(update_fields=['version'])
        saved = CartSnapshot.objects.create(cart=cart, version=cart.version, request_id=request_id,
            catalog_revision=catalog.CATALOG['revision'], lines=[purchase], evaluation={'release':'shb-1.1','evidence_class':'local-synthetic','live_payable':False})
        row = SyntheticCheckout.objects.create(owner=invitation.customer, request_id=request_id, cart_snapshot=saved,
            business_snapshot=None, snapshot=snapshot, sha256=catalog.digest(snapshot))
        SupportCheckout.objects.create(checkout=row, invitation=invitation, request_id=request_id,
            submission_sha256=fingerprint, review_sha256=token_sha256, session_digest=scope)
        SyntheticCheckoutKey.objects.create(owner=invitation.customer, request_id=request_id, checkout=row)
        if claim:
            from .models import DiscountReservation
            discount, slot, policy, at = claim
            DiscountReservation.objects.create(discount=discount, checkout=row, slot=slot,
                snapshot=policy, sha256=catalog.digest(policy), claimed_at=at)
        return row


def authorize(request, owner, checkout_id):
    """Called inside the shared transaction, before owner/resource locking."""
    guard()
    invitation = invitations.current(request, lock=True)
    if invitation is None: raise shared_checkout.CheckoutError('invitation_required', 403)
    if invitation.customer_id != owner.pk: raise shared_checkout.CheckoutError('not_found', 404)
    if not SupportCheckout.objects.filter(checkout_id=checkout_id, invitation=invitation,
            session_digest=session_digest(request)).exists(): raise shared_checkout.CheckoutError('not_found', 404)


def accept(request, row, archive):
    # Explicit form acceptance covers the same exact snapshot/documents; shared
    # confirmation retains its own timestamp and archives before admission.
    expected = shared_checkout.digest(payment.envelope(row))
    return payment.accept(row.owner, row.pk, expected, True, archive, customer_request=request)
