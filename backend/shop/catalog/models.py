"""Local product draft snapshots. No acceptance, entitlement, hosts or payment."""
import uuid
from django.conf import settings
from django.db import models
class ConfigurationDraft(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    owner=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    request_id=models.UUIDField()
    revision=models.CharField(max_length=64)
    configuration=models.JSONField()
    evaluation=models.JSONField()
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['owner','request_id'],name='catalog_owner_request_unique')]


class DraftCart(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    owner=models.OneToOneField(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    version=models.PositiveIntegerField(default=0)

class CartSnapshot(models.Model):
    cart=models.ForeignKey(DraftCart,on_delete=models.PROTECT)
    version=models.PositiveIntegerField()
    request_id=models.UUIDField()
    catalog_revision=models.CharField(max_length=64)
    lines=models.JSONField()
    evaluation=models.JSONField()
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints=[
            models.UniqueConstraint(fields=['cart','version'],name='cart_snapshot_unique_version'),
            models.UniqueConstraint(fields=['cart','request_id'],name='cart_snapshot_unique_request'),
            models.CheckConstraint(condition=models.Q(version__gte=1),name='cart_snapshot_positive_version'),
        ]


class QuotationRequest(models.Model):
    """Unpriced request bound to a retained snapshot; never an approved offer."""
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    cart=models.ForeignKey(DraftCart,on_delete=models.PROTECT)
    snapshot=models.OneToOneField(CartSnapshot,on_delete=models.PROTECT)
    review_version=models.PositiveIntegerField(default=0)
    preparation_version=models.PositiveIntegerField(default=0)
    business_version=models.PositiveIntegerField(default=0)
    request_id=models.UUIDField()
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['cart','request_id'],name='quotation_cart_request_unique')]


class QuotationRequestKey(models.Model):
    cart=models.ForeignKey(DraftCart,on_delete=models.PROTECT)
    request_id=models.UUIDField()
    quotation=models.ForeignKey(QuotationRequest,on_delete=models.PROTECT)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['cart','request_id'],name='quotation_retry_key_unique')]


REVIEW_DECISIONS=[
    ('needs_information','Needs scope clarification'),
    ('ready_for_commercial_review','Ready for commercial review (offer not approved)'),
    ('declined','Declined request'),
]

class QuotationReview(models.Model):
    """Append-only-by-API internal decision; never commercial offer approval."""
    quotation=models.ForeignKey(QuotationRequest,on_delete=models.PROTECT)
    version=models.PositiveIntegerField()
    business_version=models.PositiveIntegerField(default=0)
    request_id=models.UUIDField()
    snapshot_digest=models.CharField(max_length=64)
    decision=models.CharField(max_length=32,choices=REVIEW_DECISIONS)
    reviewer=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    reviewer_generation=models.UUIDField()
    mfa_verified_at=models.DateTimeField()
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints=[
            models.UniqueConstraint(fields=['quotation','version'],name='quotation_review_unique_version'),
            models.UniqueConstraint(fields=['quotation','request_id'],name='quotation_review_unique_request'),
            models.CheckConstraint(condition=models.Q(version__gte=1),name='quotation_review_positive_version'),
            models.CheckConstraint(condition=models.Q(decision__in=[value for value,_ in REVIEW_DECISIONS]),name='quotation_review_known_decision'),
        ]


class BusinessDraft(models.Model):
    owner=models.OneToOneField(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    version=models.PositiveIntegerField(default=0)

class BusinessDraftSnapshot(models.Model):
    draft=models.ForeignKey(BusinessDraft,on_delete=models.PROTECT)
    version=models.PositiveIntegerField()
    request_id=models.UUIDField()
    schema_version=models.PositiveSmallIntegerField()
    source_sha256=models.CharField(max_length=64)
    submission_digest=models.CharField(max_length=64)
    details=models.JSONField()
    evaluation=models.JSONField()
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints=[
            models.UniqueConstraint(fields=['draft','version'],name='business_snapshot_unique_version'),
            models.UniqueConstraint(fields=['draft','request_id'],name='business_snapshot_unique_request'),
            models.CheckConstraint(condition=models.Q(version__gte=1),name='business_snapshot_positive_version'),
        ]


class QuotationBusinessScope(models.Model):
    quotation=models.ForeignKey(QuotationRequest,on_delete=models.PROTECT)
    version=models.PositiveIntegerField()
    business_snapshot=models.ForeignKey(BusinessDraftSnapshot,on_delete=models.PROTECT)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['quotation','version'],name='quotation_business_scope_version'),
                     models.CheckConstraint(condition=models.Q(version__gte=1),name='quotation_business_scope_positive')]

class QuotationBusinessKey(models.Model):
    quotation=models.ForeignKey(QuotationRequest,on_delete=models.PROTECT)
    request_id=models.UUIDField()
    expected_version=models.PositiveIntegerField()
    scope=models.ForeignKey(QuotationBusinessScope,on_delete=models.PROTECT)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['quotation','request_id'],name='quotation_business_key_unique')]
