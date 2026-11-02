"""Changed work is a fresh scoped request after explicit archived unpaid withdrawal."""
import uuid
from . import checkout, invitations, offers
from .errors import ShbError
from .models import RequestClosure, RequestReplacement


def project(row):
    return row.payload['known_project_reference'] or row.payload['details']['project_reference']


def authorized(request, identity, *, lock=False):
    checkout.guard()
    invitation=invitations.current(request,lock=lock)
    if invitation is None: raise ShbError('invitation_required',403)
    rows=RequestClosure.objects.select_related('request__invitation').filter(pk=identity,
        request__invitation__customer_id=invitation.customer_id,applied_at__isnull=False,
        payload__action='withdraw',request__state='withdrawn')
    saved=rows.first()
    if (saved is None or not invitation.asic_allowed or invitation.company_name!=saved.request.invitation.company_name
            or invitation.project_reference and invitation.project_reference!=project(saved.request)):
        raise ShbError('not_found',404)
    if lock:
        offers.lock_request(saved.request_id)
        saved=rows.select_for_update(of=('self',)).get(pk=identity)
    return invitation,saved


def validate(invitation, previous, cleaned):
    if (cleaned['variant']!='shb-asic-25h'
            or (invitation.project_reference or cleaned['project_reference'])!=project(previous.request)):
        raise ShbError('matching_asic_project_required',422)
    if previous.request.revision>=2147483647: raise ShbError('request_revision_limit')
    if RequestReplacement.objects.filter(previous=previous.request).exists():
        raise ShbError('request_already_revised')


def link(request, previous, child):
    return RequestReplacement.objects.create(id=uuid.uuid5(child.pk,'shb-request-replacement-v1'),
        previous=previous.request,request=child,closure=previous,invitation=child.invitation,
        session_digest=checkout.session_digest(request))
