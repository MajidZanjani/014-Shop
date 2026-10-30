"""Current request capture extends existing quotations; no payment or time grant."""
import uuid
from django.db import transaction
from . import catalog,invitations,discounts
from .errors import ShbError
from .models import SupportRequest
from shop.catalog.models import DraftCart,CartSnapshot,QuotationRequest


def _submission(cleaned):
    details=dict(cleaned,discount_code='')
    code=cleaned.get('discount_code','')
    fingerprint=catalog.digest({'details':details,'discount_verifier':discounts.verifier(code) if code else None})
    return details,fingerprint


def _previous(invitation,request_id,fingerprint):
    previous=SupportRequest.objects.select_related('quotation').filter(invitation=invitation,request_id=request_id).first()
    if previous:
        stored=previous.payload.get('submission_sha256')
        if stored is None:_,stored=_submission(previous.payload['details'])
        if stored!=fingerprint:raise ShbError('request_conflict')
    return previous


def submit_asic(request,cleaned,request_id):
    invitations.fixture_guard()  # Actual intake/privacy/operational adoption is pending.
    try:request_id=uuid.UUID(str(request_id))
    except (TypeError,ValueError,AttributeError):raise ShbError('invalid_request',422) from None
    details,fingerprint=_submission(cleaned)
    # A committed retry is resolved before current pricing/code validity and
    # before the guessing budget. The locked block rechecks access and identity.
    invitation=invitations.current(request)
    if invitation is None:raise ShbError('invitation_required',403)
    if cleaned.get('discount_code') and not _previous(invitation,request_id,fingerprint):
        discounts.take_attempt(request)
    with transaction.atomic(durable=True):
        row=invitations.current(request,lock=True)
        if row is None:raise ShbError('invitation_required',403)
        if not row.asic_allowed or cleaned['variant']!='shb-asic-25h':raise ShbError('asic_request_required',422)
        if cleaned['company_name'].strip()!=row.company_name:raise ShbError('company_clarification_required')
        previous=_previous(row,request_id,fingerprint)
        if previous:return previous
        claim=discounts.claim(row,cleaned['variant'],cleaned['discount_code']) if cleaned.get('discount_code') else None
        purchase=catalog.quote(cleaned['variant'],cleaned['quantity'],offer=catalog.synthetic_offer(),
            discount_bps=claim[2]['percentage_bps'] if claim else 0)
        if claim:purchase['discount_policy']=claim[2]
        payload={'schema':1,'evidence_class':'local-synthetic','customer_id':row.customer_id,
            'invitation_id':str(row.pk),'purchase':purchase,'details':details,'submission_sha256':fingerprint,
            'known_project_reference':row.project_reference,'source_sha256':catalog.CATALOG['source_sha256'],
            'intake_privacy_revision':'synthetic-shb-privacy-v1','purchase_acceptance':False,
            'financial_confirmation':False,'effects_authorized':False}
        encoded=catalog.digest(payload)
        cart,_=DraftCart.objects.get_or_create(owner=row.customer)
        cart=DraftCart.objects.select_for_update().get(pk=cart.pk)
        if CartSnapshot.objects.filter(cart=cart,request_id=request_id).exists():raise ShbError('request_conflict')
        cart.version+=1;cart.save(update_fields=['version'])
        snapshot=CartSnapshot.objects.create(cart=cart,version=cart.version,request_id=request_id,
            catalog_revision=catalog.CATALOG['revision'],lines=[purchase],
            evaluation={'release':'shb-1.1','evidence_class':'local-synthetic','payable':False})
        quotation=QuotationRequest.objects.create(cart=cart,snapshot=snapshot,request_id=request_id)
        saved=SupportRequest.objects.create(invitation=row,quotation=quotation,request_id=request_id,payload=payload,sha256=encoded)
        if claim:discounts.reserve(saved,claim)
        return saved
