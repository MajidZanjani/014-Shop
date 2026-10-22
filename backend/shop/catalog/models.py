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
