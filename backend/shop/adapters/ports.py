"""Synthetic adapter values; no financial acceptance semantics."""
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class ProbeRequest:
    effect_id: UUID
    scenario: str = 'ok'


@dataclass(frozen=True)
class ProbeResult:
    effect_id: UUID
    outcome: str
