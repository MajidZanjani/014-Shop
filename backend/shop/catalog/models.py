from datetime import timedelta
from django.db.models.lookups import Exact
"""Local product draft snapshots. No acceptance, entitlement, hosts or payment."""
import uuid
from django.conf import settings
from django.db import models
from django.db.models.functions import Cast
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
    """One local prepared archive intent; business effects/qualification stay disabled."""
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    envelope=models.OneToOneField(RequestEnvelope,on_delete=models.PROTECT)
    state=models.CharField(max_length=16,default='pending')
    destination_profile=models.CharField(max_length=32,default='local-prepared-v1')
    evidence_class=models.CharField(max_length=32,default='local-synthetic')
    evidence_kind=models.CharField(max_length=16,default='prepared')
    retention_qualified=models.BooleanField(default=False)
    effects_authorized=models.BooleanField(default=False)
    destination=models.ForeignKey('ArchiveDestination',null=True,on_delete=models.PROTECT)
    destination_bound_by=models.ForeignKey(settings.AUTH_USER_MODEL,null=True,on_delete=models.PROTECT,related_name='+')
    destination_bound_at=models.DateTimeField(null=True)
    binding_staff_generation=models.UUIDField(null=True,editable=False)
    binding_mfa_verified_at=models.DateTimeField(null=True)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints=[
            models.CheckConstraint(condition=models.Q(destination__isnull=True,destination_bound_by__isnull=True,destination_bound_at__isnull=True,binding_staff_generation__isnull=True,binding_mfa_verified_at__isnull=True)|models.Q(destination__isnull=False,destination_bound_by__isnull=False,destination_bound_at__isnull=False),name='request_archive_binding_present'),
            models.CheckConstraint(condition=models.Q(binding_staff_generation__isnull=True,binding_mfa_verified_at__isnull=True)|models.Q(binding_staff_generation__isnull=False,binding_mfa_verified_at__isnull=False),name='request_archive_binding_mfa'),
            models.CheckConstraint(condition=models.Q(state__in=['pending','held']),name='request_archive_unexecuted_state'),
            models.CheckConstraint(condition=models.Q(destination_profile='local-prepared-v1',evidence_class='local-synthetic',evidence_kind='prepared',retention_qualified=False,effects_authorized=False),name='request_archive_no_effects'),
        ]


class ArchiveDestination(models.Model):
    """Private explicit local root reference; not provider/retention qualification."""
    id=models.UUIDField(primary_key=True,editable=False)
    device=models.PositiveBigIntegerField()
    inode=models.PositiveBigIntegerField()
    manifest_sha256=models.CharField(max_length=64)
    profile=models.CharField(max_length=32,default='local-prepared-v1')
    created_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name='+')
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints=[
            models.UniqueConstraint(fields=['device','inode'],name='archive_destination_root_unique'),
            models.CheckConstraint(condition=models.Q(inode__gte=1,profile='local-prepared-v1',manifest_sha256__regex=r'^[0-9a-f]{64}$'),name='archive_destination_known_local'),
        ]


class ArchiveWorkAuthorization(models.Model):
    """Explicit bounded local prepared-work authorization; immutable by service."""
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    intent=models.ForeignKey(RequestArchiveIntent,on_delete=models.PROTECT)
    command_id=models.UUIDField()
    generation=models.PositiveIntegerField()
    destination=models.ForeignKey(ArchiveDestination,on_delete=models.PROTECT)
    envelope_sha256=models.CharField(max_length=64)
    byte_length=models.PositiveIntegerField()
    schema_version=models.PositiveSmallIntegerField(default=1)
    owner=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name='+')
    authorized_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name='+')
    staff_generation=models.UUIDField(null=True,editable=False)
    mfa_verified_at=models.DateTimeField(null=True)
    issued_at=models.DateTimeField()
    not_after=models.DateTimeField()
    retention_qualified=models.BooleanField(default=False)
    effects_authorized=models.BooleanField(default=False)
    class Meta:
        constraints=[
            models.UniqueConstraint(fields=['intent','command_id'],name='archive_auth_command_unique'),
            models.UniqueConstraint(fields=['intent','generation'],name='archive_auth_generation_unique'),
            models.CheckConstraint(condition=models.Q(generation__gte=1,generation__lte=1000000000,schema_version=1,byte_length__gte=1,byte_length__lte=131072,envelope_sha256__regex=r'^[0-9a-f]{64}$',retention_qualified=False,effects_authorized=False),name='archive_auth_local_bounds'),
            models.CheckConstraint(condition=models.Q(not_after=models.F('issued_at')+timedelta(minutes=5)),name='archive_auth_fixed_lifetime'),
            models.CheckConstraint(condition=models.Q(staff_generation__isnull=True,mfa_verified_at__isnull=True)|models.Q(staff_generation__isnull=False,mfa_verified_at__isnull=False),name='archive_auth_staff_pair'),
        ]


class ArchiveWorkRevocation(models.Model):
    """Retained explicit revocation; retry never reactivates the grant."""
    authorization=models.OneToOneField(ArchiveWorkAuthorization,on_delete=models.PROTECT)
    revoked_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name='+')
    revoked_at=models.DateTimeField()
    reason=models.CharField(max_length=32,default='explicit-revocation')
    class Meta:
        constraints=[models.CheckConstraint(condition=models.Q(reason='explicit-revocation'),name='archive_revoke_known_reason')]


class ArchiveWorkClaim(models.Model):
    """Retained bounded local lease; no publication/completion or business effects."""
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    intent=models.ForeignKey(RequestArchiveIntent,on_delete=models.PROTECT)
    authorization=models.ForeignKey(ArchiveWorkAuthorization,on_delete=models.PROTECT)
    generation=models.PositiveIntegerField()
    token=models.UUIDField(default=uuid.uuid4,editable=False,unique=True)
    started_at=models.DateTimeField()
    expires_at=models.DateTimeField()
    retention_qualified=models.BooleanField(default=False)
    effects_authorized=models.BooleanField(default=False)
    class Meta:
        constraints=[
            models.UniqueConstraint(fields=['intent','generation'],name='archive_claim_generation_unique'),
            models.CheckConstraint(condition=models.Q(generation__gte=1,generation__lte=1000000000,retention_qualified=False,effects_authorized=False),name='archive_claim_local_bounds'),
            models.CheckConstraint(condition=models.Q(expires_at__gt=models.F('started_at'),expires_at__lte=models.F('started_at')+timedelta(seconds=30)),name='archive_claim_bounded_lifetime'),
        ]


class ArchivePreparedVerification(models.Model):
    """Retained local prepared-byte observation; no domain completion or effects."""
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    intent=models.OneToOneField(RequestArchiveIntent,on_delete=models.PROTECT)
    envelope=models.ForeignKey(RequestEnvelope,on_delete=models.PROTECT)
    destination=models.ForeignKey(ArchiveDestination,on_delete=models.PROTECT)
    claim=models.OneToOneField(ArchiveWorkClaim,on_delete=models.PROTECT)
    authorization=models.ForeignKey(ArchiveWorkAuthorization,on_delete=models.PROTECT)
    claim_generation=models.PositiveIntegerField()
    authorization_generation=models.PositiveIntegerField()
    evidence_id=models.UUIDField()
    sha256=models.CharField(max_length=64)
    byte_length=models.PositiveIntegerField()
    verified_at=models.DateTimeField()
    evidence_class=models.CharField(max_length=32,default='local-synthetic')
    evidence_kind=models.CharField(max_length=16,default='prepared')
    retention_qualified=models.BooleanField(default=False)
    effects_authorized=models.BooleanField(default=False)
    class Meta:
        constraints=[models.CheckConstraint(condition=models.Q(claim_generation__gte=1,claim_generation__lte=1000000000,
            authorization_generation__gte=1,authorization_generation__lte=1000000000,byte_length__gte=1,byte_length__lte=131072,
            sha256__regex=r'^[0-9a-f]{64}$',evidence_class='local-synthetic',evidence_kind='prepared',
            retention_qualified=False,effects_authorized=False),name='archive_verification_local_bounds')]


class SyntheticCheckout(models.Model):
    """Private frozen complete-cart rehearsal, never an accepted order."""
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    owner=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    request_id=models.UUIDField()
    cart_snapshot=models.ForeignKey(CartSnapshot,on_delete=models.PROTECT)
    business_snapshot=models.ForeignKey(BusinessDraftSnapshot,on_delete=models.PROTECT)
    snapshot=models.JSONField()
    sha256=models.CharField(max_length=64)
    archive_receipt=models.JSONField(default=dict)
    evidence_class=models.CharField(max_length=32,default='local-synthetic')
    financial_confirmation=models.BooleanField(default=False)
    effects_authorized=models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints=[
            models.UniqueConstraint(fields=['owner','request_id'],name='synthetic_checkout_request_unique'),
            models.UniqueConstraint(fields=['owner','sha256'],name='synthetic_checkout_snapshot_unique'),
            models.CheckConstraint(condition=models.Q(sha256__regex=r'^[0-9a-f]{64}$',evidence_class='local-synthetic',financial_confirmation=False,effects_authorized=False),name='synthetic_checkout_no_effects'),
        ]


class SyntheticCheckoutKey(models.Model):
    owner=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    request_id=models.UUIDField()
    checkout=models.ForeignKey(SyntheticCheckout,on_delete=models.PROTECT)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['owner','request_id'],name='synthetic_checkout_retry_unique')]


class SyntheticCheckoutAcceptance(models.Model):
    """One local fixture confirmation/order reference; never legal acceptance."""
    id=models.UUIDField(primary_key=True,editable=False)
    checkout=models.OneToOneField(SyntheticCheckout,on_delete=models.PROTECT)
    review_sha256=models.CharField(max_length=64)
    payload=models.JSONField()
    sha256=models.CharField(max_length=64)
    archive_receipt=models.JSONField(default=dict)
    simulated_accepted_at=models.DateTimeField(null=True)
    attempt=models.OneToOneField('payments.SyntheticPaymentAttempt',null=True,on_delete=models.PROTECT)
    evidence_class=models.CharField(max_length=32,default='local-synthetic')
    financial_confirmation=models.BooleanField(default=False)
    effects_authorized=models.BooleanField(default=False)
    class Meta:
        constraints=[
            models.CheckConstraint(condition=models.Q(evidence_class='local-synthetic',financial_confirmation=False,effects_authorized=False,sha256__regex=r'^[0-9a-f]{64}$',review_sha256__regex=r'^[0-9a-f]{64}$'),name='synthetic_acceptance_no_commerce'),
            models.CheckConstraint(condition=(models.Q(simulated_accepted_at__isnull=True,attempt__isnull=True)|models.Q(simulated_accepted_at__isnull=False)&~models.Q(archive_receipt={})),name='synthetic_acceptance_archive_gate'),
        ]


class SyntheticFulfilment(models.Model):
    """Archived once-only cart licence/support grants; no real rights or spendability."""
    id=models.UUIDField(primary_key=True,editable=False)
    acceptance=models.OneToOneField(SyntheticCheckoutAcceptance,on_delete=models.PROTECT)
    payload=models.JSONField()
    sha256=models.CharField(max_length=64)
    archive_receipt=models.JSONField()
    support_packages=models.PositiveIntegerField()
    support_seconds=models.BigIntegerField()
    expires_at=models.DateTimeField(null=True)
    evidence_class=models.CharField(max_length=32,default='local-synthetic')
    financial_confirmation=models.BooleanField(default=False)
    effects_authorized=models.BooleanField(default=False)
    class Meta:
        constraints=[models.CheckConstraint(condition=models.Q(support_seconds=Cast('support_packages',models.BigIntegerField())*36000,expires_at__isnull=True,evidence_class='local-synthetic',financial_confirmation=False,effects_authorized=False,sha256__regex=r'^[0-9a-f]{64}$'),name='synthetic_fulfilment_fixed_grant')]


class SyntheticLineEntitlement(models.Model):
    id=models.UUIDField(primary_key=True,editable=False)
    fulfilment=models.ForeignKey(SyntheticFulfilment,on_delete=models.PROTECT)
    line_id=models.UUIDField()
    snapshot=models.JSONField()
    class Meta:
        constraints=[models.UniqueConstraint(fields=['fulfilment','line_id'],name='synthetic_entitlement_line_unique')]


class SyntheticLineDelivery(models.Model):
    entitlement=models.ForeignKey(SyntheticLineEntitlement,on_delete=models.PROTECT)
    stage=models.CharField(max_length=16)
    payload=models.JSONField()
    sha256=models.CharField(max_length=64)
    archive_receipt=models.JSONField()
    class Meta:
        constraints=[models.UniqueConstraint(fields=['entitlement','stage'],name='synthetic_delivery_stage_unique'),
            models.CheckConstraint(condition=models.Q(stage__in=['initial','reference'],sha256__regex=r'^[0-9a-f]{64}$'),name='synthetic_delivery_stage_known')]


class SyntheticSupportEvent(models.Model):
    """Append-only, archived local support ledger; never actual spendable credit."""
    id=models.UUIDField(primary_key=True,editable=False)
    fulfilment=models.ForeignKey(SyntheticFulfilment,on_delete=models.PROTECT)
    revision=models.PositiveIntegerField()
    request_id=models.UUIDField()
    kind=models.CharField(max_length=16)
    payload=models.JSONField()
    sha256=models.CharField(max_length=64)
    archive_receipt=models.JSONField()
    evidence_class=models.CharField(max_length=32,default='local-synthetic')
    effects_authorized=models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints=[
            models.UniqueConstraint(fields=['fulfilment','revision'],name='synthetic_support_revision_unique'),
            models.UniqueConstraint(fields=['fulfilment','request_id'],name='synthetic_support_request_unique'),
            models.CheckConstraint(condition=models.Q(revision__gte=1,kind__in=['reserve','release','work','correct','statement'],sha256__regex=r'^[0-9a-f]{64}$',evidence_class='local-synthetic',effects_authorized=False),name='synthetic_support_event_bounds'),
        ]


class SyntheticSupportStaffGrant(models.Model):
    """Explicit local staff authority over one synthetic support grant."""
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    fulfilment=models.ForeignKey(SyntheticFulfilment,on_delete=models.PROTECT)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['user','fulfilment'],name='synthetic_support_staff_unique')]


class SyntheticDeliveryStaffGrant(models.Model):
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    entitlement=models.ForeignKey(SyntheticLineEntitlement,on_delete=models.PROTECT)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['user','entitlement'],name='synthetic_delivery_staff_unique')]


class SyntheticPackageRevision(models.Model):
    identity=models.UUIDField(unique=True,editable=False)
    entitlement=models.ForeignKey(SyntheticLineEntitlement,on_delete=models.PROTECT)
    request_id=models.UUIDField()
    stage=models.CharField(max_length=16)
    version=models.PositiveIntegerField()
    payload=models.JSONField()
    sha256=models.CharField(max_length=64)
    archive_receipt=models.JSONField()
    evidence_class=models.CharField(max_length=32,default='local-synthetic')
    effects_authorized=models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints=[
            models.UniqueConstraint(fields=['entitlement','request_id'],name='synthetic_package_request_unique'),
            models.UniqueConstraint(fields=['entitlement','stage','version'],name='synthetic_package_version_unique'),
            models.CheckConstraint(condition=models.Q(version__gte=1,stage__in=['initial','reference'],sha256__regex=r'^[0-9a-f]{64}$',evidence_class='local-synthetic',effects_authorized=False),name='synthetic_package_local_bounds'),
        ]


class SyntheticPackageAccess(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    package=models.ForeignKey(SyntheticPackageRevision,on_delete=models.PROTECT)
    owner=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    artifact=models.CharField(max_length=64)
    token_digest=models.CharField(max_length=64,unique=True)
    session_digest=models.CharField(max_length=64)
    expires_at=models.DateTimeField()
    consumed_at=models.DateTimeField(null=True)
    authority_revision=models.PositiveIntegerField(default=0)
    class Meta:
        constraints=[models.CheckConstraint(condition=models.Q(token_digest__regex=r'^[0-9a-f]{64}$',session_digest__regex=r'^[0-9a-f]{64}$'),name='synthetic_package_access_digests')]


class SyntheticLicenceCase(models.Model):
    identity=models.UUIDField(unique=True,editable=False)
    entitlement=models.ForeignKey(SyntheticLineEntitlement,on_delete=models.PROTECT)
    request_id=models.UUIDField()
    kind=models.CharField(max_length=24)
    payload=models.JSONField()
    sha256=models.CharField(max_length=64)
    archive_receipt=models.JSONField()
    evidence_class=models.CharField(max_length=32,default='local-synthetic')
    effects_authorized=models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints=[
            models.UniqueConstraint(fields=['entitlement','request_id'],name='synthetic_licence_case_retry'),
            models.CheckConstraint(condition=models.Q(kind__in=['renewal','rehost','family-addition','node-addition','production-upgrade'],sha256__regex=r'^[0-9a-f]{64}$',evidence_class='local-synthetic',effects_authorized=False),name='synthetic_licence_case_local'),
        ]


class SyntheticLicenceCaseEvent(models.Model):
    id=models.UUIDField(primary_key=True,editable=False)
    case=models.ForeignKey(SyntheticLicenceCase,on_delete=models.PROTECT)
    revision=models.PositiveIntegerField()
    request_id=models.UUIDField()
    kind=models.CharField(max_length=16)
    payload=models.JSONField()
    sha256=models.CharField(max_length=64)
    archive_receipt=models.JSONField()
    evidence_class=models.CharField(max_length=32,default='local-synthetic')
    effects_authorized=models.BooleanField(default=False)
    class Meta:
        constraints=[
            models.UniqueConstraint(fields=['case','revision'],name='synthetic_case_event_revision'),
            models.UniqueConstraint(fields=['case','request_id'],name='synthetic_case_event_retry'),
            models.CheckConstraint(condition=models.Q(revision__gte=1,kind__in=['review','proposal'],sha256__regex=r'^[0-9a-f]{64}$',evidence_class='local-synthetic',effects_authorized=False),name='synthetic_case_event_local'),
        ]


class SyntheticLicenceCaseStaffGrant(models.Model):
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    case=models.ForeignKey(SyntheticLicenceCase,on_delete=models.PROTECT)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['user','case'],name='synthetic_licence_case_staff')]


class SyntheticDocumentReservation(models.Model):
    id=models.UUIDField(primary_key=True,editable=False)
    kind=models.CharField(max_length=8)
    number=models.PositiveBigIntegerField()
    request_id=models.UUIDField(unique=True)
    subject=models.UUIDField()
    payload=models.JSONField()
    sha256=models.CharField(max_length=64)
    archive_receipt=models.JSONField()
    class Meta:
        constraints=[
            models.UniqueConstraint(fields=['kind','number'],name='synthetic_document_number_unique'),
            models.CheckConstraint(condition=models.Q(kind__in=['invoice','credit'],number__gte=1),name='synthetic_document_number_bounds'),
        ]


class SyntheticDocumentIssue(models.Model):
    id=models.UUIDField(primary_key=True,editable=False)
    reservation=models.OneToOneField(SyntheticDocumentReservation,on_delete=models.PROTECT)
    payload=models.JSONField()
    sha256=models.CharField(max_length=64)
    archive_receipt=models.JSONField()


class SyntheticStatementMail(models.Model):
    id=models.UUIDField(primary_key=True,editable=False)
    statement=models.OneToOneField(SyntheticSupportEvent,on_delete=models.PROTECT)
    payload=models.JSONField()
    sha256=models.CharField(max_length=64)
    archive_receipt=models.JSONField()


class SyntheticStatementDelivery(models.Model):
    mail=models.OneToOneField(SyntheticStatementMail,primary_key=True,on_delete=models.PROTECT)
    state=models.CharField(max_length=16,default='pending')
    token=models.UUIDField(null=True)
    lease_until=models.DateTimeField(null=True)
    attempts=models.PositiveSmallIntegerField(default=0)
    class Meta:
        constraints=[
            models.CheckConstraint(condition=models.Q(attempts__lte=5,state__in=['pending','claimed','captured','held']),name='synthetic_statement_delivery_bounds'),
            models.CheckConstraint(condition=models.Q(state='claimed',token__isnull=False,lease_until__isnull=False)|models.Q(state__in=['pending','captured','held'],token__isnull=True,lease_until__isnull=True),name='synthetic_statement_delivery_claim'),
        ]


class SyntheticStatementCapture(models.Model):
    id=models.UUIDField(primary_key=True,editable=False)
    mail=models.OneToOneField(SyntheticStatementMail,on_delete=models.PROTECT)
    payload=models.JSONField()
    sha256=models.CharField(max_length=64)
    archive_receipt=models.JSONField()


class SyntheticSupportRefundCase(models.Model):
    identity=models.UUIDField(unique=True,editable=False)
    fulfilment=models.ForeignKey(SyntheticFulfilment,on_delete=models.PROTECT)
    request_id=models.UUIDField()
    payload=models.JSONField()
    sha256=models.CharField(max_length=64)
    archive_receipt=models.JSONField()
    class Meta:
        constraints=[models.UniqueConstraint(fields=['fulfilment','request_id'],name='synthetic_support_refund_request')]


class SyntheticSupportRefundReview(models.Model):
    id=models.UUIDField(primary_key=True,editable=False)
    case=models.ForeignKey(SyntheticSupportRefundCase,on_delete=models.PROTECT)
    request_id=models.UUIDField()
    revision=models.PositiveIntegerField()
    payload=models.JSONField()
    sha256=models.CharField(max_length=64)
    archive_receipt=models.JSONField()
    class Meta:
        constraints=[
            models.UniqueConstraint(fields=['case','request_id'],name='synthetic_support_refund_review_retry'),
            models.UniqueConstraint(fields=['case','revision'],name='synthetic_support_refund_review_revision'),
            models.CheckConstraint(condition=models.Q(revision__gte=1),name='synthetic_support_refund_review_positive'),
        ]


class SyntheticSupportRefundStaffGrant(models.Model):
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    case=models.ForeignKey(SyntheticSupportRefundCase,on_delete=models.PROTECT)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['user','case'],name='synthetic_support_refund_staff')]


class SyntheticDeliveryControl(models.Model):
    id=models.UUIDField(primary_key=True,editable=False)
    entitlement=models.ForeignKey(SyntheticLineEntitlement,on_delete=models.PROTECT)
    revision=models.PositiveIntegerField()
    request_id=models.UUIDField()
    payload=models.JSONField()
    sha256=models.CharField(max_length=64)
    archive_receipt=models.JSONField()
    class Meta:
        constraints=[
            models.UniqueConstraint(fields=['entitlement','revision'],name='synthetic_delivery_control_revision'),
            models.UniqueConstraint(fields=['entitlement','request_id'],name='synthetic_delivery_control_retry'),
            models.CheckConstraint(condition=models.Q(revision__gte=1),name='synthetic_delivery_control_positive'),
        ]
