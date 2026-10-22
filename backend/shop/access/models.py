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
