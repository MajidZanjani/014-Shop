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
