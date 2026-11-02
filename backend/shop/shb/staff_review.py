"""Assigned recent-MFA ASIC triage. No commercial approval or payment effects."""
from datetime import datetime, timezone as utc_timezone
import re
import uuid

from django.db import transaction
from django.db.models import F

from shop.access.models import StaffCredential, StaffQuotationGrant
from shop.access.recovery import current_session_epoch
from shop.access.staff_auth import staff_credential
from shop.catalog.models import QuotationReview
from . import catalog, invitations
from .errors import ShbError
from .models import DiscountCode, DiscountReservation, SupportRequest, SupportRequestReview

DECISIONS = {'needs_information': 'needs_information',
    'ready_for_commercial_review': 'under_review', 'declined': 'declined'}


def authorized(request, identity, *, lock=False):
    invitations.fixture_guard()
    if lock and not current_session_epoch(request, lock=True):
        raise ShbError('recent_staff_mfa_required', 403)
    admitted = staff_credential(request, recent=True)
    if admitted is None:
        raise ShbError('recent_staff_mfa_required', 403)
    if lock:
        credential = StaffCredential.objects.select_for_update().filter(pk=admitted.pk,
            enabled=True, generation=admitted.generation).first()
        if credential is None or staff_credential(request, recent=True) is None:
            raise ShbError('recent_staff_mfa_required', 403)
    rows = SupportRequest.objects.select_related('invitation', 'quotation__snapshot').filter(
        quotation_id=identity, quotation__snapshot__cart_id=F('quotation__cart_id'),
        quotation__cart__owner_id=F('invitation__customer_id'))
    if lock:
        # Lock the existing quotation counter before the SHB request extension.
        from shop.catalog.models import QuotationRequest
        QuotationRequest.objects.select_for_update().filter(pk=identity).first()
        rows = rows.select_for_update(of=('self',))
    row = rows.first()
    grants = StaffQuotationGrant.objects.filter(user=request.user, quotation_id=identity)
    if lock: grants = grants.select_for_update()
    grant = grants.first()
    if row is None or grant is None:
        raise ShbError('not_found', 404)
    # A bare quotation assignment does not reveal SHB's private form. Its
    # existing business-scope grant must name this exact captured revision.
    if grant.business_scope_version != row.revision:
        raise ShbError('business_scope_access_required', 403)
    if (catalog.digest(row.payload) != row.sha256
            or row.payload['customer_id'] != row.invitation.customer_id
            or row.quotation.snapshot.lines != [row.payload['purchase']]
            or row.quotation.business_version != 0):
        raise ShbError('request_scope_changed')
    return row, admitted


def details(request, identity):
    with transaction.atomic(durable=True):
        row, _ = authorized(request, identity, lock=True)
        return row, list(SupportRequestReview.objects.filter(request=row)
            .select_related('review__reviewer').order_by('-review__version')[:20])


def record(request, identity, value):
    try:
        key = uuid.UUID(value['request_id'])
        version = value['expected_review_version']
        if type(version) is not int or not 0 <= version < 1000000000: raise ValueError()
        if not isinstance(value['scope_sha256'], str) or not re.fullmatch('[a-f0-9]{64}', value['scope_sha256']): raise ValueError()
        if type(value['decision']) is not str or value['decision'] not in DECISIONS: raise ValueError()
        if type(value['message']) is not str or not 1 <= len(value['message'].strip()) <= 512: raise ValueError()
        message = value['message'].strip()
    except (ValueError, TypeError, KeyError, AttributeError):
        raise ShbError('invalid_request', 400) from None
    with transaction.atomic(durable=True):
        row, credential = authorized(request, identity, lock=True)
        previous = SupportRequestReview.objects.select_related('review').filter(
            request=row, review__request_id=key).first()
        if previous:
            old = previous.review
            if (old.reviewer_id != request.user.pk or old.version - 1 != version
                    or old.snapshot_digest != value['scope_sha256'] or old.decision != value['decision']
                    or previous.message != message):
                raise ShbError('request_conflict')
            return row, previous, False
        if row.quotation.review_version != version:
            raise ShbError('review_changed')
        if row.sha256 != value['scope_sha256']:
            raise ShbError('request_scope_changed')
        if row.state not in ('submitted', 'needs_information', 'under_review'):
            raise ShbError('request_closed_or_offer_review_required')
        from .models import SupportOffer
        if SupportOffer.objects.filter(request=row,state__in=['prepared','issued','paid']).exists():
            raise ShbError('request_closed_or_offer_review_required')
        marker = request.session['shop_staff_mfa']
        review = QuotationReview.objects.create(quotation=row.quotation, version=version + 1,
            business_version=row.revision, request_id=key, snapshot_digest=row.sha256,
            decision=value['decision'], reviewer=request.user, reviewer_generation=credential.generation,
            mfa_verified_at=datetime.fromtimestamp(marker['verified_at'], tz=utc_timezone.utc))
        event = SupportRequestReview.objects.create(review=review, request=row, message=message, prior_state=row.state)
        row.state = DECISIONS[value['decision']]
        row.save(update_fields=['state'])
        if row.state == 'declined':
            # Only the pre-offer states above can reach this path. Future
            # accepted/payment lifecycles must use their matched reconciliation.
            hold = DiscountReservation.objects.filter(request=row, state='reserved').first()
            if hold:
                DiscountCode.objects.select_for_update().get(pk=hold.discount_id)
                hold = DiscountReservation.objects.select_for_update().get(pk=hold.pk)
                hold.state = 'released'; hold.release_review = event
                hold.save(update_fields=['state', 'release_review'])
        row.quotation.review_version = review.version
        row.quotation.save(update_fields=['review_version'])
        return row, event, True
