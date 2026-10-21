"""Synthetic probe schema only; no commerce or confirmed-money semantics."""
import uuid
from django.db import models
from django.db.models import Q


class Probe(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payload_version = models.PositiveSmallIntegerField(default=1)
    evidence_class = models.CharField(max_length=32, default='local-synthetic')
    state = models.CharField(max_length=16, default='pending')
    effect_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    claim_token = models.UUIDField(null=True, editable=False)
    lease_until = models.DateTimeField(null=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    result = models.JSONField(default=dict)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(payload_version=1, evidence_class='local-synthetic'), name='probe_synthetic_v1'),
            models.CheckConstraint(condition=Q(state__in=['pending', 'claimed', 'complete', 'failed']), name='probe_known_state'),
            models.CheckConstraint(condition=Q(attempts__lte=5), name='probe_bounded_attempts'),
            models.CheckConstraint(condition=(Q(state='claimed', claim_token__isnull=False, lease_until__isnull=False)
                | (Q(state__in=['pending', 'complete', 'failed']) & Q(claim_token__isnull=True, lease_until__isnull=True))),
                name='probe_claim_consistent'),
        ]


class FakeReceipt(models.Model):
    effect_id = models.UUIDField(primary_key=True, editable=False)
    scenario = models.CharField(max_length=32)
    outcome = models.CharField(max_length=32)
