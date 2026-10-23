"""Typed synthetic boundary; these capabilities make no real-provider claim."""
from dataclasses import dataclass,field
import re
from uuid import UUID


class BankError(ValueError):pass


@dataclass(frozen=True)
class BankStart:
    merchant: str
    reference: UUID
    idempotency_key: UUID
    currency: str
    amount_minor: int


@dataclass(frozen=True)
class BankObservation:
    provider_operation_id: UUID
    merchant: str
    reference: UUID
    currency: str
    amount_minor: int
    status: str
    evidence_class: str=field(default='local-synthetic',init=False)
    financial_confirmation: bool=field(default=False,init=False)
    effects_authorized: bool=field(default=False,init=False)


@dataclass(frozen=True)
class SyntheticCapabilities:
    adapter: str=field(default='synthetic-bank-v1',init=False)
    reference_lookup: bool=field(default=True,init=False)
    idempotent_start: bool=field(default=True,init=False)
    authorization_status: bool=field(default=True,init=False)
    capture_status: bool=field(default=True,init=False)
    separate_capture: bool=field(default=False,init=False)
    refunds: bool=field(default=False,init=False)
    callbacks: bool=field(default=False,init=False)
    evidence_class: str=field(default='local-synthetic',init=False)
    financial_confirmation: bool=field(default=False,init=False)


def identity(merchant,reference):
    if (type(merchant) is not str or re.fullmatch(r'synthetic-[a-z0-9-]{1,40}',merchant) is None
        or type(reference) is not UUID):raise BankError('invalid_synthetic_request')


def validate(request):
    if type(request) is not BankStart:raise BankError('invalid_synthetic_request')
    identity(request.merchant,request.reference)
    if (type(request.idempotency_key) is not UUID or type(request.currency) is not str
        or re.fullmatch('[A-Z]{3}',request.currency) is None or type(request.amount_minor) is not int
        or not 1<=request.amount_minor<=9223372036854775807):raise BankError('invalid_synthetic_request')


def correlates(request,observation):
    """Exact synthetic identity/value comparison, never authentication or payment proof."""
    validate(request)
    if type(observation) is not BankObservation:return False
    try:
        validate(BankStart(observation.merchant,observation.reference,request.idempotency_key,
            observation.currency,observation.amount_minor))
    except BankError:return False
    return (type(observation.provider_operation_id) is UUID
        and observation.status in ('authorized','captured','declined','pending')
        and observation.evidence_class=='local-synthetic' and observation.financial_confirmation is False
        and observation.effects_authorized is False
        and (request.merchant,request.reference,request.currency,request.amount_minor)==
            (observation.merchant,observation.reference,observation.currency,observation.amount_minor))
