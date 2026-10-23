"""Fake-provider observations only, never shop payment confirmation or orders."""
import uuid
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
