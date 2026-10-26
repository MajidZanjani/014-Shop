"""Fake-provider observations only, never shop payment confirmation or orders."""
import uuid
from django.conf import settings
from django.db import models

SYNTHETIC_STATUSES=('authorized','captured','declined','pending')


class SyntheticBankOperation(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    merchant=models.CharField(max_length=50)
    reference=models.UUIDField()
    currency=models.CharField(max_length=3)
    amount_minor=models.BigIntegerField()
    status=models.CharField(max_length=16)
    evidence_class=models.CharField(max_length=32,default='local-synthetic')
    financial_confirmation=models.BooleanField(default=False)
    effects_authorized=models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints=[
            models.UniqueConstraint(fields=['merchant','reference'],name='synthetic_bank_reference_unique'),
            models.CheckConstraint(condition=models.Q(merchant__regex=r'^synthetic-[a-z0-9-]{1,40}$',currency__regex=r'^[A-Z]{3}$',amount_minor__gte=1,status__in=SYNTHETIC_STATUSES),name='synthetic_bank_bounded_value'),
            models.CheckConstraint(condition=models.Q(evidence_class='local-synthetic',financial_confirmation=False,effects_authorized=False),name='synthetic_bank_no_commerce'),
        ]


class SyntheticBankKey(models.Model):
    id=models.UUIDField(primary_key=True,editable=False)
    operation=models.ForeignKey(SyntheticBankOperation,on_delete=models.PROTECT)
    created_at=models.DateTimeField(auto_now_add=True)


class SyntheticPaymentAttempt(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    merchant=models.CharField(max_length=50)
    reference=models.UUIDField()
    idempotency_key=models.UUIDField(unique=True)
    currency=models.CharField(max_length=3)
    amount_minor=models.BigIntegerField()
    state=models.CharField(max_length=16,default='prepared')
    dispatch_held=models.BooleanField(default=False)
    control_revision=models.PositiveIntegerField(default=0)
    expires_at=models.DateTimeField(null=True)
    stopped_at=models.DateTimeField(null=True)
    archive_receipt=models.JSONField(default=dict)
    provider_operation_id=models.UUIDField(null=True)
    provider_status=models.CharField(max_length=16,blank=True,default='')
    evidence_class=models.CharField(max_length=32,default='local-synthetic')
    financial_confirmation=models.BooleanField(default=False)
    effects_authorized=models.BooleanField(default=False)
    class Meta:
        constraints=[
            models.UniqueConstraint(fields=['merchant','reference'],name='synthetic_attempt_reference_unique'),
            models.CheckConstraint(condition=models.Q(merchant__regex=r'^synthetic-[a-z0-9-]{1,40}$',currency__regex=r'^[A-Z]{3}$',amount_minor__gte=1),name='synthetic_attempt_value'),
            models.CheckConstraint(condition=models.Q(evidence_class='local-synthetic',financial_confirmation=False,effects_authorized=False),name='synthetic_attempt_no_commerce'),
            models.CheckConstraint(condition=(
                models.Q(state__in=('prepared','uncertain'),stopped_at__isnull=True,
                         provider_operation_id__isnull=True,provider_status='')
                | models.Q(state='observed',stopped_at__isnull=True,provider_operation_id__isnull=False,
                           provider_status__in=SYNTHETIC_STATUSES)
                | models.Q(state='cancelled',stopped_at__isnull=False,
                           provider_operation_id__isnull=True,provider_status='')
                | models.Q(state='expired',expires_at__isnull=False,stopped_at__isnull=False,
                           stopped_at__gte=models.F('expires_at'),provider_operation_id__isnull=True,
                           provider_status='')
            ),name='synthetic_attempt_state'),
        ]


class SyntheticAttemptControl(models.Model):
    attempt=models.ForeignKey(SyntheticPaymentAttempt,on_delete=models.PROTECT)
    revision=models.PositiveIntegerField()
    command_id=models.UUIDField()
    held=models.BooleanField()
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints=[
            models.UniqueConstraint(fields=['attempt','revision'],name='synthetic_control_revision_unique'),
            models.UniqueConstraint(fields=['attempt','command_id'],name='synthetic_control_command_unique'),
            models.CheckConstraint(condition=models.Q(revision__gte=1),name='synthetic_control_positive_revision'),
        ]


class SyntheticPurchase(models.Model):
    """Local rehearsal linked to existing drafts, never an actual accepted order."""
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    owner=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    request_id=models.UUIDField()
    draft=models.OneToOneField('catalog.ConfigurationDraft',null=True,on_delete=models.PROTECT)
    attempt=models.OneToOneField(SyntheticPaymentAttempt,on_delete=models.PROTECT)
    snapshot=models.JSONField()
    archive_receipt=models.JSONField(default=dict)
    simulated_funded=models.BooleanField(default=False)
    simulated_credit_seconds=models.BigIntegerField(default=0)
    simulated_entitlements=models.PositiveSmallIntegerField(default=0)
    initial_delivered=models.BooleanField(default=False)
    reference_delivered=models.BooleanField(default=False)
    reserved_seconds=models.BigIntegerField(default=0)
    evidence_class=models.CharField(max_length=32,default='local-synthetic')
    financial_confirmation=models.BooleanField(default=False)
    effects_authorized=models.BooleanField(default=False)
    class Meta:
        constraints=[
            models.UniqueConstraint(fields=['owner','request_id'],name='synthetic_purchase_owner_request'),
            models.CheckConstraint(condition=models.Q(evidence_class='local-synthetic',financial_confirmation=False,effects_authorized=False),name='synthetic_purchase_no_commerce'),
            models.CheckConstraint(condition=models.Q(simulated_credit_seconds__gte=0,reserved_seconds__gte=0,reserved_seconds__lte=models.F('simulated_credit_seconds'),simulated_entitlements__lte=1),name='synthetic_purchase_balances'),
            models.CheckConstraint(condition=(models.Q(simulated_funded=True)|models.Q(simulated_credit_seconds=0,simulated_entitlements=0,initial_delivered=False,reference_delivered=False)),name='synthetic_purchase_funding_gate'),
            models.CheckConstraint(condition=(models.Q(reference_delivered=False)|models.Q(initial_delivered=True)),name='synthetic_purchase_staged_delivery'),
        ]


class SyntheticCreditReservation(models.Model):
    purchase=models.ForeignKey(SyntheticPurchase,on_delete=models.PROTECT)
    request_id=models.UUIDField()
    seconds=models.BigIntegerField()
    class Meta:
        constraints=[
            models.UniqueConstraint(fields=['purchase','request_id'],name='synthetic_reservation_request'),
            models.CheckConstraint(condition=models.Q(seconds__gte=1),name='synthetic_reservation_positive'),
        ]


class SyntheticBankNotification(models.Model):
    id=models.UUIDField(primary_key=True,editable=False)
    attempt=models.ForeignKey(SyntheticPaymentAttempt,on_delete=models.PROTECT)
    payload=models.JSONField()
    sha256=models.CharField(max_length=64)
    archive_receipt=models.JSONField()


class SyntheticNotificationDelivery(models.Model):
    notification=models.OneToOneField(SyntheticBankNotification,primary_key=True,on_delete=models.PROTECT)
    state=models.CharField(max_length=16,default='pending')
    token=models.UUIDField(null=True)
    lease_until=models.DateTimeField(null=True)
    attempts=models.PositiveSmallIntegerField(default=0)
    class Meta:
        constraints=[
            models.CheckConstraint(condition=models.Q(attempts__lte=5,state__in=['pending','claimed','checked','held']),name='synthetic_notification_bounds'),
            models.CheckConstraint(condition=models.Q(state='claimed',token__isnull=False,lease_until__isnull=False)|models.Q(state__in=['pending','checked','held'],token__isnull=True,lease_until__isnull=True),name='synthetic_notification_claim'),
        ]


class SyntheticNotificationResult(models.Model):
    id=models.UUIDField(primary_key=True,editable=False)
    notification=models.OneToOneField(SyntheticBankNotification,on_delete=models.PROTECT)
    payload=models.JSONField()
    sha256=models.CharField(max_length=64)
    archive_receipt=models.JSONField()
