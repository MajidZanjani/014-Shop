"""Synthetic scoped-code preview and request reservations; never money effects."""
from datetime import timedelta
import re
import secrets

from django.db import connection, transaction
from django.utils import timezone
from django.utils.crypto import salted_hmac

from . import catalog, invitations
from .errors import ShbError
from .models import DiscountCode, DiscountReservation, DiscountThrottle

now = timezone.now
MAX_ATTEMPTS = 10
WINDOW = timedelta(minutes=10)
POLICY = 'synthetic-shb-discounts-v1'


def guard():
    try:
        invitations.fixture_guard()
    except ValueError:
        raise ShbError('Discount configuration is not available.', 503) from None


def verifier(code):
    if type(code) is not str or not re.fullmatch(r'[A-Za-z0-9-]{1,48}', code):
        raise ShbError('Discount unavailable. Check the code or contact SLL.', 422)
    return salted_hmac('shb-discount-code-v1', code.upper(), algorithm='sha256').hexdigest()


def issue_fixture(*, customer, issuer, percentage_bps, fpga_allowed=False,
        asic_allowed=False, use_limit=1, starts_at=None, expires_at=None):
    """Returns a raw random code once, for an explicitly disposable fixture."""
    guard()
    issued = now()
    start = starts_at if starts_at is not None else issued
    expiry = expires_at if expires_at is not None else start + timedelta(days=30)
    if (not customer.is_active or customer.is_staff or not issuer.is_active or not issuer.is_staff
            or type(percentage_bps) is not int or not 1 <= percentage_bps < 10000
            or type(use_limit) is not int or not 1 <= use_limit <= 100
            or type(fpga_allowed) is not bool or type(asic_allowed) is not bool
            or not (fpga_allowed or asic_allowed)
            or timezone.is_naive(start) or timezone.is_naive(expiry) or expiry <= start):
        raise ShbError('Invalid synthetic discount scope.', 422)
    code = 'SLL-' + ''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(24))
    row = DiscountCode.objects.create(customer=customer, issuer=issuer, code_digest=verifier(code),
        percentage_bps=percentage_bps, fpga_allowed=fpga_allowed, asic_allowed=asic_allowed,
        use_limit=use_limit, policy_revision=POLICY, issued_at=issued, starts_at=start, expires_at=expiry)
    return row, code


def take_attempt(request):
    """Commit the guessing budget even when later validation/capture rolls back."""
    guard()
    limited = False
    with transaction.atomic(durable=True):
        invitation = invitations.current(request, lock=True)
        if invitation is None:
            raise ShbError('invitation_required', 403)
        throttle, _ = DiscountThrottle.objects.get_or_create(customer_id=invitation.customer_id)
        throttle = DiscountThrottle.objects.select_for_update().get(pk=throttle.pk)
        at = now()
        if at - throttle.window_start >= WINDOW:
            throttle.window_start = at
            throttle.attempts = 0
        if throttle.attempts >= MAX_ATTEMPTS:
            limited = True
        else:
            throttle.attempts += 1
            throttle.save(update_fields=['window_start', 'attempts'])
    if limited:
        raise ShbError('Too many discount attempts. Please try again later.', 429)


def claim(invitation, variant, code):
    """Caller holds access/invitation locks. Lock code before counting its slots."""
    guard()
    if connection.vendor != 'postgresql' or not connection.in_atomic_block:
        raise ShbError('Discount transaction unavailable.', 503)
    row = DiscountCode.objects.select_for_update().filter(code_digest=verifier(code)).first()
    at = now()
    allowed = bool(row and row.customer_id == invitation.customer_id
        and row.revoked_at is None and row.starts_at <= at < row.expires_at
        and row.evidence_class == 'local-synthetic' and row.policy_revision == POLICY
        and (variant == 'shb-fpga-10h' and row.fpga_allowed
            or variant == 'shb-asic-25h' and row.asic_allowed))
    if not allowed:
        raise ShbError('Discount unavailable. Check the code or contact SLL.', 422)
    occupied = set(DiscountReservation.objects.filter(discount=row).values_list('slot', flat=True))
    slot = next((number for number in range(1, row.use_limit + 1) if number not in occupied), None)
    if slot is None:
        raise ShbError('Discount unavailable. Check the code or contact SLL.', 422)
    snapshot = {'schema': 1, 'discount_id': str(row.pk), 'customer_id': row.customer_id,
        'variant_id': variant, 'percentage_bps': row.percentage_bps,
        'policy_revision': row.policy_revision, 'evidence_class': row.evidence_class,
        'claim_expires_at': row.expires_at.isoformat()}
    return row, slot, snapshot, at


def preview(request, cleaned):
    take_attempt(request)
    with transaction.atomic(durable=True):
        invitation = invitations.current(request, lock=True)
        if invitation is None:
            raise ShbError('invitation_required', 403)
        if (cleaned['variant'] == 'shb-fpga-10h' and not invitation.fpga_eligible
                or cleaned['variant'] == 'shb-asic-25h' and not invitation.asic_allowed):
            raise ShbError('support_eligibility_required', 422)
        _, _, snapshot, _ = claim(invitation, cleaned['variant'], cleaned['discount_code'])
        purchase = catalog.quote(cleaned['variant'], cleaned['quantity'], offer=catalog.synthetic_offer(),
            discount_bps=snapshot['percentage_bps'])
        return dict(purchase, discount_policy=snapshot)


def reserve(request_row, claim_value):
    """Create only within the same transaction as the immutable request capture."""
    discount, slot, snapshot, claimed_at = claim_value
    return DiscountReservation.objects.create(discount=discount, request=request_row, slot=slot,
        snapshot=snapshot, sha256=catalog.digest(snapshot), claimed_at=claimed_at)
