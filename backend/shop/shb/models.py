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
            models.CheckConstraint(condition=models.Q(state__in=['submitted','under_review','needs_information','declined','withdrawn','approved','offer_issued','paid']),name='shb_request_known_state')]


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
    """One held slot per request. Outcome transitions await matched payments.

    No expiry job or generic update may silently free a held concession.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    discount = models.ForeignKey(DiscountCode, on_delete=models.PROTECT)
    request = models.OneToOneField(SupportRequest, on_delete=models.PROTECT)
    slot = models.PositiveSmallIntegerField()
    snapshot = models.JSONField(editable=False)
    sha256 = models.CharField(max_length=64, editable=False)
    claimed_at = models.DateTimeField(default=timezone.now, editable=False)
    state = models.CharField(max_length=16, default='reserved', editable=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['discount', 'slot'], name='shb_discount_unique_held_slot'),
            models.CheckConstraint(condition=models.Q(slot__gte=1, slot__lte=100), name='shb_discount_slot_bounds'),
            models.CheckConstraint(condition=models.Q(sha256__regex=r'^[a-f0-9]{64}$', state='reserved'), name='shb_discount_held_until_matched'),
        ]


class DiscountThrottle(models.Model):
    """Customer-wide guessing budget, shared by all of that customer's invites."""
    customer = models.OneToOneField(settings.AUTH_USER_MODEL, primary_key=True, on_delete=models.PROTECT)
    window_start = models.DateTimeField(default=timezone.now)
    attempts = models.PositiveSmallIntegerField(default=0)

    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(attempts__lte=10), name='shb_discount_attempt_bounds')]
