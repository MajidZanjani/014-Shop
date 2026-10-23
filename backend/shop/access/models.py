"""Synthetic customer verification; never an organization-wide or staff grant."""
import uuid
from django.conf import settings
from django.db import models
class CustomerIdentity(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    user=models.OneToOneField(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    email=models.EmailField(max_length=160,unique=True)
    verified_at=models.DateTimeField()
class VerificationChallenge(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    email=models.EmailField(max_length=160)
    code_digest=models.CharField(max_length=64)
    binding_digest=models.CharField(max_length=64)
    created_at=models.DateTimeField(auto_now_add=True)
    expires_at=models.DateTimeField()
    attempts=models.PositiveSmallIntegerField(default=0)
    consumed_at=models.DateTimeField(null=True)
class VerificationThrottle(models.Model):
    email_digest=models.CharField(max_length=64,primary_key=True)
    window_start=models.DateTimeField()
    requests=models.PositiveSmallIntegerField(default=0)


class StaffCredential(models.Model):
    user=models.OneToOneField(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    generation=models.UUIDField(default=uuid.uuid4)
    enabled=models.BooleanField(default=True)

class StaffLoginThrottle(models.Model):
    identity_digest=models.CharField(max_length=64,primary_key=True)
    window_start=models.DateTimeField()
    attempts=models.PositiveSmallIntegerField(default=0)

class StaffChallenge(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    credential=models.ForeignKey(StaffCredential,on_delete=models.PROTECT)
    generation=models.UUIDField()
    code_digest=models.CharField(max_length=64)
    binding_digest=models.CharField(max_length=64)
    expires_at=models.DateTimeField()
    attempts=models.PositiveSmallIntegerField(default=0)
    consumed_at=models.DateTimeField(null=True)

class StaffQuotationGrant(models.Model):
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    quotation=models.ForeignKey('catalog.QuotationRequest',on_delete=models.PROTECT)
    business_scope_version=models.PositiveIntegerField(default=0)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['user','quotation'],name='staff_quotation_reviewer_unique')]


class PreparationAssessment(models.Model):
    """Append-only-by-API internal evidence, never an approved commercial offer."""
    quotation=models.ForeignKey('catalog.QuotationRequest',on_delete=models.PROTECT)
    version=models.PositiveIntegerField()
    request_id=models.UUIDField()
    schema_version=models.PositiveSmallIntegerField(default=1)
    business_version=models.PositiveIntegerField(default=0)
    business_scope=models.ForeignKey('catalog.QuotationBusinessScope',null=True,on_delete=models.PROTECT)
    review_version=models.PositiveIntegerField(default=0)
    review=models.ForeignKey('catalog.QuotationReview',null=True,on_delete=models.PROTECT)
    scope_digest=models.CharField(max_length=64)
    assessment_digest=models.CharField(max_length=64)
    assessment=models.JSONField()
    captured_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    staff_generation=models.UUIDField()
    mfa_verified_at=models.DateTimeField()
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints=[
            models.UniqueConstraint(fields=['quotation','version'],name='preparation_unique_version'),
            models.UniqueConstraint(fields=['quotation','request_id'],name='preparation_unique_request'),
            models.CheckConstraint(condition=models.Q(version__gte=1),name='preparation_positive_version'),
            models.CheckConstraint(condition=models.Q(business_version=0,business_scope__isnull=True)|models.Q(business_version__gt=0,business_scope__isnull=False),name='preparation_business_reference'),
            models.CheckConstraint(condition=models.Q(review_version=0,review__isnull=True)|models.Q(review_version__gt=0,review__isnull=False),name='preparation_review_reference'),
        ]
