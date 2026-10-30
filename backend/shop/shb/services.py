"""Current request capture extends existing quotations; no payment or time grant."""
import uuid
from django.db import transaction
from . import catalog,invitations
from .models import SupportRequest
from shop.catalog.models import DraftCart,CartSnapshot,QuotationRequest


class ShbError(ValueError):
    def __init__(self,code,status=409):self.code=code;self.status=status;super().__init__(code)


def submit_asic(request,cleaned,request_id):
    invitations.fixture_guard()  # Actual intake/privacy/operational adoption is pending.
    try:request_id=uuid.UUID(str(request_id))
    except (TypeError,ValueError,AttributeError):raise ShbError('invalid_request',422) from None
    with transaction.atomic(durable=True):
        row=invitations.current(request,lock=True)
        if row is None:raise ShbError('invitation_required',403)
        if not row.asic_allowed or cleaned['variant']!='shb-asic-25h':raise ShbError('asic_request_required',422)
        if cleaned['company_name'].strip()!=row.company_name:raise ShbError('company_clarification_required')
        if cleaned.get('discount_code'):raise ShbError('discount_reservations_pending',422)
        purchase=catalog.quote(cleaned['variant'],cleaned['quantity'],offer=catalog.synthetic_offer())
        payload={'schema':1,'evidence_class':'local-synthetic','customer_id':row.customer_id,
            'invitation_id':str(row.pk),'purchase':purchase,'details':cleaned,
            'known_project_reference':row.project_reference,'source_sha256':catalog.CATALOG['source_sha256'],
            'intake_privacy_revision':'synthetic-shb-privacy-v1','purchase_acceptance':False,
            'financial_confirmation':False,'effects_authorized':False}
        encoded=catalog.digest(payload)
        previous=SupportRequest.objects.select_related('quotation').filter(invitation=row,request_id=request_id).first()
        if previous:
            if previous.sha256!=encoded:raise ShbError('request_conflict')
            return previous
        cart,_=DraftCart.objects.get_or_create(owner=row.customer)
        cart=DraftCart.objects.select_for_update().get(pk=cart.pk)
        if CartSnapshot.objects.filter(cart=cart,request_id=request_id).exists():raise ShbError('request_conflict')
        cart.version+=1;cart.save(update_fields=['version'])
        snapshot=CartSnapshot.objects.create(cart=cart,version=cart.version,request_id=request_id,
            catalog_revision=catalog.CATALOG['revision'],lines=[purchase],
            evaluation={'release':'shb-1.1','evidence_class':'local-synthetic','payable':False})
        quotation=QuotationRequest.objects.create(cart=cart,snapshot=snapshot,request_id=request_id)
        return SupportRequest.objects.create(invitation=row,quotation=quotation,request_id=request_id,payload=payload,sha256=encoded)
