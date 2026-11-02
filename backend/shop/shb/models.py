"""Invitation and request extensions; order/payment/quote records are reused."""
import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone


class Invitation(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    token_digest=models.CharField(max_length=64,unique=True,editable=False)
    customer=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name='+')
    issuer=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name='+')
    company_name=models.CharField(max_length=200)
    project_reference=models.CharField(max_length=160,blank=True)
    fpga_eligible=models.BooleanField(default=False)
    asic_allowed=models.BooleanField(default=False)
    eligibility_reference=models.CharField(max_length=160)
    created_at=models.DateTimeField(default=timezone.now,editable=False)
    expires_at=models.DateTimeField(editable=False)
    revoked_at=models.DateTimeField(null=True,editable=False)
    class Meta:
        constraints=[models.CheckConstraint(condition=models.Q(expires_at__gt=models.F('created_at')),name='shb_invite_positive_lifetime'),
            models.CheckConstraint(condition=models.Q(fpga_eligible=True)|models.Q(asic_allowed=True),name='shb_invite_permitted_mode'),
            models.CheckConstraint(condition=models.Q(token_digest__regex=r'^[a-f0-9]{64}$'),name='shb_invite_digest_shape')]


class SupportRequest(models.Model):
    """Private ASIC submission extending the existing quotation record."""
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    invitation=models.ForeignKey(Invitation,on_delete=models.PROTECT)
    quotation=models.OneToOneField('catalog.QuotationRequest',on_delete=models.PROTECT)
    request_id=models.UUIDField(editable=False)
    payload=models.JSONField(editable=False)
    sha256=models.CharField(max_length=64,editable=False)
    state=models.CharField(max_length=24,default='submitted')
    revision=models.PositiveIntegerField(default=1)
    created_at=models.DateTimeField(default=timezone.now,editable=False)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['invitation','request_id'],name='shb_request_retry_unique'),
            models.CheckConstraint(condition=models.Q(sha256__regex=r'^[a-f0-9]{64}$',revision__gte=1),name='shb_request_digest_revision'),
            models.CheckConstraint(condition=models.Q(state__in=['submitted','under_review','needs_information','declined','withdrawn','approved','offer_issued','offer_expired','paid']),name='shb_request_known_state')]


class DiscountCode(models.Model):
    """Immutable scoped concession; only explicit synthetic issuance is wired."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code_digest = models.CharField(max_length=64, unique=True, editable=False)
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+')
    issuer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+')
    percentage_bps = models.PositiveSmallIntegerField()
    fpga_allowed = models.BooleanField(default=False)
    asic_allowed = models.BooleanField(default=False)
    use_limit = models.PositiveSmallIntegerField(default=1)
    policy_revision = models.CharField(max_length=80)
    evidence_class = models.CharField(max_length=32, default='local-synthetic', editable=False)
    issued_at = models.DateTimeField(default=timezone.now, editable=False)
    starts_at = models.DateTimeField()
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, editable=False)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(code_digest__regex=r'^[a-f0-9]{64}$'), name='shb_discount_digest_shape'),
            models.CheckConstraint(condition=models.Q(percentage_bps__gte=1, percentage_bps__lte=9999), name='shb_discount_paid_percentage'),
            models.CheckConstraint(condition=models.Q(use_limit__gte=1, use_limit__lte=100), name='shb_discount_bounded_uses'),
            models.CheckConstraint(condition=models.Q(fpga_allowed=True) | models.Q(asic_allowed=True), name='shb_discount_permitted_variant'),
            models.CheckConstraint(condition=models.Q(expires_at__gt=models.F('starts_at')), name='shb_discount_claim_window'),
            models.CheckConstraint(condition=models.Q(evidence_class='local-synthetic', policy_revision='synthetic-shb-discounts-v1'), name='shb_discount_synthetic_only'),
        ]


class DiscountReservation(models.Model):
    """One held or consumed slot; only a matched audited outcome releases it."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    discount = models.ForeignKey(DiscountCode, on_delete=models.PROTECT)
    request = models.OneToOneField(SupportRequest, null=True, on_delete=models.PROTECT)
    checkout = models.OneToOneField('catalog.SyntheticCheckout', null=True, on_delete=models.PROTECT)
    slot = models.PositiveSmallIntegerField()
    snapshot = models.JSONField(editable=False)
    sha256 = models.CharField(max_length=64, editable=False)
    claimed_at = models.DateTimeField(default=timezone.now, editable=False)
    state = models.CharField(max_length=16, default='reserved', editable=False)
    release_review = models.OneToOneField('SupportRequestReview', null=True, on_delete=models.PROTECT, editable=False)
    consumed_order = models.OneToOneField('PaidOrder', null=True, on_delete=models.PROTECT, editable=False)
    release_closure = models.OneToOneField('CheckoutClosure', null=True, on_delete=models.PROTECT, editable=False)
    release_lifecycle = models.OneToOneField('RequestClosure', null=True, on_delete=models.PROTECT, editable=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['discount', 'slot'], condition=models.Q(state__in=['reserved','consumed']), name='shb_discount_unique_held_slot'),
            models.CheckConstraint(condition=models.Q(slot__gte=1, slot__lte=100), name='shb_discount_slot_bounds'),
            models.CheckConstraint(condition=(models.Q(request__isnull=False, checkout__isnull=True) | models.Q(request__isnull=True, checkout__isnull=False)), name='shb_discount_one_claim_target'),
            models.CheckConstraint(condition=models.Q(sha256__regex=r'^[a-f0-9]{64}$') & ((models.Q(release_lifecycle__isnull=True) & (
                models.Q(state='reserved', release_review__isnull=True, release_closure__isnull=True, consumed_order__isnull=True) |
                models.Q(state='released', release_review__isnull=False, release_closure__isnull=True, consumed_order__isnull=True) |
                models.Q(state='released', release_review__isnull=True, release_closure__isnull=False, consumed_order__isnull=True) |
                models.Q(state='consumed', release_review__isnull=True, release_closure__isnull=True, consumed_order__isnull=False))) |
                models.Q(state='released', release_review__isnull=True, release_closure__isnull=True,
                    consumed_order__isnull=True, release_lifecycle__isnull=False)), name='shb_discount_held_until_matched'),
        ]


class DiscountThrottle(models.Model):
    """Customer-wide guessing budget, shared by all of that customer's invites."""
    customer = models.OneToOneField(settings.AUTH_USER_MODEL, primary_key=True, on_delete=models.PROTECT)
    window_start = models.DateTimeField(default=timezone.now)
    attempts = models.PositiveSmallIntegerField(default=0)

    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(attempts__lte=10), name='shb_discount_attempt_bounds')]


class SupportRequestReview(models.Model):
    """SHB message extends an attributed existing quotation review, append-only."""
    review = models.OneToOneField('catalog.QuotationReview', primary_key=True, on_delete=models.PROTECT)
    request = models.ForeignKey(SupportRequest, on_delete=models.PROTECT)
    message = models.CharField(max_length=512)
    prior_state = models.CharField(max_length=24, editable=False)

    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(message__regex=r'\S',
            prior_state__in=['submitted', 'needs_information', 'under_review', 'offer_expired']), name='shb_review_reason_required')]


class SupportCheckout(models.Model):
    """SHB scope on the shared immutable checkout, never a history grant."""
    checkout = models.OneToOneField('catalog.SyntheticCheckout', primary_key=True, on_delete=models.PROTECT)
    invitation = models.ForeignKey(Invitation, on_delete=models.PROTECT)
    request_id = models.UUIDField(editable=False)
    submission_sha256 = models.CharField(max_length=64, editable=False)
    review_sha256 = models.CharField(max_length=64, editable=False)
    session_digest = models.CharField(max_length=64, editable=False)
    offer = models.OneToOneField('SupportOffer', null=True, on_delete=models.PROTECT, editable=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['invitation', 'request_id'], name='shb_checkout_retry'),
            models.CheckConstraint(condition=models.Q(submission_sha256__regex=r'^[a-f0-9]{64}$',
                review_sha256__regex=r'^[a-f0-9]{64}$', session_digest__regex=r'^[a-f0-9]{64}$'), name='shb_checkout_digests'),
        ]


class PaidOrder(models.Model):
    """One archived purchase on the shared acceptance; no time entitlement."""
    id=models.UUIDField(primary_key=True,editable=False)
    acceptance=models.OneToOneField('catalog.SyntheticCheckoutAcceptance',on_delete=models.PROTECT)
    capture=models.ForeignKey('payments.SyntheticPaymentObservation',on_delete=models.PROTECT)
    payload=models.JSONField(editable=False)
    sha256=models.CharField(max_length=64,editable=False)
    archive_receipt=models.JSONField(editable=False)
    created_at=models.DateTimeField(default=timezone.now,editable=False)
    class Meta:
        constraints=[models.CheckConstraint(condition=models.Q(sha256__regex=r'^[a-f0-9]{64}$') & ~models.Q(archive_receipt={}),name='shb_order_archived_digest')]


class PurchaseNoticeDelivery(models.Model):
    """The existing worker leases this ordinary transaction notice."""
    order=models.OneToOneField(PaidOrder,primary_key=True,on_delete=models.PROTECT)
    state=models.CharField(max_length=16,default='pending')
    token=models.UUIDField(null=True,editable=False)
    lease_until=models.DateTimeField(null=True)
    attempts=models.PositiveSmallIntegerField(default=0)
    class Meta:
        constraints=[
            models.CheckConstraint(condition=models.Q(state__in=['pending','claimed','captured','held'],attempts__lte=5),name='shb_notice_delivery_bounds'),
            models.CheckConstraint(condition=models.Q(state='claimed',token__isnull=False,lease_until__isnull=False) | models.Q(state__in=['pending','captured','held'],token__isnull=True,lease_until__isnull=True),name='shb_notice_delivery_claim')]


class PurchaseNoticeCapture(models.Model):
    """Durable fake receipt for one stable notice; never an SMTP assertion."""
    id=models.UUIDField(primary_key=True,editable=False)
    order=models.OneToOneField(PaidOrder,on_delete=models.PROTECT)
    payload=models.JSONField(editable=False)
    sha256=models.CharField(max_length=64,editable=False)
    archive_receipt=models.JSONField(editable=False)
    class Meta:
        constraints=[models.CheckConstraint(condition=models.Q(sha256__regex=r'^[a-f0-9]{64}$') & ~models.Q(archive_receipt={}),name='shb_notice_capture_digest')]


class PaidOrderGrant(models.Model):
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    order=models.ForeignKey(PaidOrder,on_delete=models.PROTECT)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['user','order'],name='shb_staff_order_unique')]


class CheckoutClosure(models.Model):
    """Durable closing intent blocks dispatch; only archived application frees a hold."""
    id=models.UUIDField(primary_key=True,editable=False)
    acceptance=models.OneToOneField('catalog.SyntheticCheckoutAcceptance',on_delete=models.PROTECT)
    payload=models.JSONField(editable=False)
    sha256=models.CharField(max_length=64,editable=False)
    archive_receipt=models.JSONField(default=dict,editable=False)
    applied_at=models.DateTimeField(null=True,editable=False)
    class Meta:
        constraints=[models.CheckConstraint(condition=models.Q(sha256__regex=r'^[a-f0-9]{64}$') & (models.Q(applied_at__isnull=True)|~models.Q(archive_receipt={})),name='shb_closure_archive_gate')]


class SupportOffer(models.Model):
    """Dated immutable offer on an existing reviewed quotation; no new engine."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request = models.ForeignKey(SupportRequest, on_delete=models.PROTECT)
    review = models.ForeignKey(SupportRequestReview, on_delete=models.PROTECT)
    issue_key = models.UUIDField(editable=False)
    revision = models.PositiveIntegerField(editable=False)
    issuer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+')
    issuer_generation = models.UUIDField(editable=False)
    mfa_verified_at = models.DateTimeField(editable=False)
    issued_at = models.DateTimeField(editable=False)
    expires_at = models.DateTimeField(editable=False)
    payload = models.JSONField(editable=False)
    sha256 = models.CharField(max_length=64, editable=False)
    archive_receipt = models.JSONField(default=dict, editable=False)
    published_at = models.DateTimeField(null=True, editable=False)
    state = models.CharField(max_length=16, default='prepared', editable=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['request', 'issue_key'], name='shb_offer_retry'),
            models.UniqueConstraint(fields=['request', 'revision'], name='shb_offer_revision'),
            models.UniqueConstraint(fields=['request'], condition=models.Q(state__in=['prepared', 'issued', 'paid']), name='shb_offer_one_active'),
            models.CheckConstraint(condition=models.Q(revision__gte=1, expires_at__gt=models.F('issued_at'), sha256__regex=r'^[a-f0-9]{64}$'), name='shb_offer_digest_dates'),
            models.CheckConstraint(condition=models.Q(state__in=['prepared','abandoned'], published_at__isnull=True, archive_receipt={}) | (models.Q(state__in=['issued', 'closed', 'paid'], published_at__isnull=False) & ~models.Q(archive_receipt={})), name='shb_offer_publication'),
        ]


class RequestClosure(models.Model):
    """Committed pre-acceptance closing intent; no fabricated checkout acceptance."""
    id = models.UUIDField(primary_key=True, editable=False)
    request = models.ForeignKey(SupportRequest, on_delete=models.PROTECT)
    offer = models.OneToOneField(SupportOffer, null=True, on_delete=models.PROTECT)
    request_key = models.UUIDField(editable=False)
    payload = models.JSONField(editable=False)
    sha256 = models.CharField(max_length=64, editable=False)
    archive_receipt = models.JSONField(default=dict, editable=False)
    applied_at = models.DateTimeField(null=True, editable=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['request','request_key'], name='shb_request_closing_retry'),
            models.UniqueConstraint(fields=['request'], condition=models.Q(offer__isnull=True), name='shb_request_preoffer_closing'),
            models.UniqueConstraint(fields=['request'], condition=models.Q(applied_at__isnull=True), name='shb_request_one_closing'),
            models.CheckConstraint(condition=models.Q(sha256__regex=r'^[a-f0-9]{64}$') &
                (models.Q(applied_at__isnull=True) | ~models.Q(archive_receipt={})), name='shb_request_closing_archive'),
        ]


class TransactionNotice(models.Model):
    """Immutable ordinary mail intent bound to one retained transaction event."""
    id = models.UUIDField(primary_key=True, editable=False)
    source_id = models.CharField(max_length=64, editable=False)
    event = models.CharField(max_length=24, editable=False)
    payload = models.JSONField(editable=False)
    sha256 = models.CharField(max_length=64, editable=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['source_id','event'], name='shb_transaction_notice_once'),
            models.CheckConstraint(condition=models.Q(sha256__regex=r'^[a-f0-9]{64}$', event__in=[
                'request-received','request-question','request-declined','offer-issued',
                'request-closed','checkout-closed','purchase-confirmed']), name='shb_transaction_notice_event'),
        ]


class TransactionNoticeDelivery(models.Model):
    notice = models.OneToOneField(TransactionNotice, primary_key=True, on_delete=models.PROTECT)
    state = models.CharField(max_length=16, default='pending')
    token = models.UUIDField(null=True, editable=False)
    lease_until = models.DateTimeField(null=True)
    attempts = models.PositiveSmallIntegerField(default=0)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(state__in=['pending','claimed','captured','held'],attempts__lte=5), name='shb_transaction_delivery_bounds'),
            models.CheckConstraint(condition=models.Q(state='claimed',token__isnull=False,lease_until__isnull=False) |
                models.Q(state__in=['pending','captured','held'],token__isnull=True,lease_until__isnull=True), name='shb_transaction_delivery_claim'),
        ]


class TransactionNoticeCapture(models.Model):
    """Durable fake capture proof, including the recoverable original envelope."""
    id = models.UUIDField(primary_key=True, editable=False)
    notice = models.OneToOneField(TransactionNotice, on_delete=models.PROTECT)
    payload = models.JSONField(editable=False)
    sha256 = models.CharField(max_length=64, editable=False)
    notice_archive_receipt = models.JSONField(editable=False)
    archive_receipt = models.JSONField(editable=False)

    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(sha256__regex=r'^[a-f0-9]{64}$') &
            ~models.Q(archive_receipt={}) & ~models.Q(notice_archive_receipt={}), name='shb_transaction_capture_archived')]


class RequestReplacement(models.Model):
    """Append-only link between a withdrawn request and its freshly captured revision."""
    id = models.UUIDField(primary_key=True, editable=False)
    previous = models.OneToOneField(SupportRequest, on_delete=models.PROTECT, related_name='replacement_child')
    request = models.OneToOneField(SupportRequest, on_delete=models.PROTECT, related_name='replacement_origin')
    closure = models.OneToOneField(RequestClosure, on_delete=models.PROTECT)
    invitation = models.ForeignKey(Invitation, on_delete=models.PROTECT)
    session_digest = models.CharField(max_length=64, editable=False)

    class Meta:
        constraints = [models.CheckConstraint(condition=~models.Q(previous=models.F('request')) &
            models.Q(session_digest__regex=r'^[a-f0-9]{64}$'), name='shb_replacement_distinct_request')]


class RefundReview(models.Model):
    """Archived staff attestation about manual records; no usage amounts or live approval."""
    id = models.UUIDField(primary_key=True, editable=False)
    order = models.OneToOneField(PaidOrder, on_delete=models.PROTECT)
    request_id = models.UUIDField(editable=False)
    payload = models.JSONField(editable=False)
    sha256 = models.CharField(max_length=64, editable=False)
    archive_receipt = models.JSONField(editable=False)
    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(sha256__regex=r'^[a-f0-9]{64}$') &
            ~models.Q(archive_receipt={}), name='shb_refund_review_archived')]


class RefundSupportHandoff(models.Model):
    """Staff records informing the support team about a confirmed financial result."""
    id = models.UUIDField(primary_key=True, editable=False)
    review = models.OneToOneField(RefundReview, on_delete=models.PROTECT)
    result = models.OneToOneField('payments.SyntheticOperationResult', on_delete=models.PROTECT)
    request_id = models.UUIDField(editable=False)
    payload = models.JSONField(editable=False)
    sha256 = models.CharField(max_length=64, editable=False)
    archive_receipt = models.JSONField(editable=False)
    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(sha256__regex=r'^[a-f0-9]{64}$') &
            ~models.Q(archive_receipt={}), name='shb_refund_handoff_archived')]


class InvitationStaffGrant(models.Model):
    """Exact invitation assignment; no general customer or historical access."""
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    invitation=models.ForeignKey(Invitation,on_delete=models.PROTECT)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['user','invitation'],name='shb_invitation_staff_once')]


class InvitationRevocation(models.Model):
    """Append-only archived staff revocation; the bearer is never retained."""
    id=models.UUIDField(primary_key=True,editable=False)
    invitation=models.OneToOneField(Invitation,on_delete=models.PROTECT)
    request_id=models.UUIDField(editable=False)
    revoked_at=models.DateTimeField(editable=False)
    payload=models.JSONField(editable=False)
    sha256=models.CharField(max_length=64,editable=False)
    archive_receipt=models.JSONField(editable=False)
    class Meta:
        constraints=[models.CheckConstraint(condition=models.Q(sha256__regex=r'^[a-f0-9]{64}$') &
            ~models.Q(archive_receipt={}),name='shb_invitation_revocation_archive')]
