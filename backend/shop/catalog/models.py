from django.db.models.lookups import Exact
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


class RequestEnvelope(models.Model):
    """Private prepared fact, append-only by service; never an approved offer."""
    id=models.UUIDField(primary_key=True,editable=False)
    quotation=models.ForeignKey(QuotationRequest,on_delete=models.PROTECT)
    business_version=models.PositiveIntegerField(default=0)
    schema_version=models.PositiveSmallIntegerField(default=1)
    owner=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name='+')
    captured_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name='+')
    staff_generation=models.UUIDField(null=True,editable=False)
    mfa_verified_at=models.DateTimeField(null=True)
    payload=models.BinaryField(editable=False)
    sha256=models.CharField(max_length=64)
    byte_length=models.PositiveIntegerField()
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints=[
            models.UniqueConstraint(fields=['quotation','business_version','schema_version'],name='request_envelope_semantic_unique'),
            models.CheckConstraint(condition=models.Q(schema_version=1,business_version__lte=1000000000),name='request_envelope_known_version'),
            models.CheckConstraint(condition=models.Q(byte_length__gte=1,byte_length__lte=131072),name='request_envelope_bounded_bytes'),
            models.CheckConstraint(condition=Exact(models.Func('payload',function='octet_length',output_field=models.IntegerField()),models.F('byte_length')),name='request_envelope_actual_length'),
            models.CheckConstraint(condition=models.Q(sha256__regex=r'^[0-9a-f]{64}$'),name='request_envelope_hash_shape'),
            models.CheckConstraint(condition=models.Q(staff_generation__isnull=True,mfa_verified_at__isnull=True)|models.Q(staff_generation__isnull=False,mfa_verified_at__isnull=False),name='request_envelope_staff_evidence'),
        ]


class RequestArchiveIntent(models.Model):
    """One unexecuted local archive intent; worker/destination qualification pending."""
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    envelope=models.OneToOneField(RequestEnvelope,on_delete=models.PROTECT)
    state=models.CharField(max_length=16,default='pending')
    destination_profile=models.CharField(max_length=32,default='local-prepared-v1')
    evidence_class=models.CharField(max_length=32,default='local-synthetic')
    evidence_kind=models.CharField(max_length=16,default='prepared')
    retention_qualified=models.BooleanField(default=False)
    effects_authorized=models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints=[
            models.CheckConstraint(condition=models.Q(state__in=['pending','held']),name='request_archive_unexecuted_state'),
            models.CheckConstraint(condition=models.Q(destination_profile='local-prepared-v1',evidence_class='local-synthetic',evidence_kind='prepared',retention_qualified=False,effects_authorized=False),name='request_archive_no_effects'),
        ]
