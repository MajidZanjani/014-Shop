"""One finite set of mutable local staff assignments, cleared atomically by callers."""
from django.conf import settings
from django.db import connection


def revoke_staff_resource_grants(*,user_id):
    """Explicit None clears all restored assignments; a user ID scopes an operator reset.

    Internal fixture primitive, never request authority or a production reset.
    Immutable accepted/work/payment/archive history is outside this set.
    """
    if (settings.SHOP_ENV not in ('local','synthetic') or settings.LIVE_PAYMENTS_ENABLED
            or any(getattr(settings,key,None)!='fake' for key in ('PAYMENT_ADAPTER','MAIL_ADAPTER','STORAGE_ADAPTER'))
            or connection.vendor!='postgresql' or not connection.in_atomic_block):
        raise ValueError('local_staff_reset_unavailable')
    from .models import StaffQuotationGrant
    from shop.catalog.models import (SyntheticSupportStaffGrant,SyntheticDeliveryStaffGrant,
        SyntheticLicenceCaseStaffGrant,SyntheticSupportRefundStaffGrant)
    from shop.payments.models import SyntheticOverpaymentStaffGrant,SyntheticPaymentStaffGrant
    from shop.shb.models import PaidOrderGrant,InvitationStaffGrant,InvitationIssueGrant,DiscountStaffGrant,DiscountIssueGrant
    scopes=(('quotation',StaffQuotationGrant),('support',SyntheticSupportStaffGrant),
        ('delivery',SyntheticDeliveryStaffGrant),('licence_case',SyntheticLicenceCaseStaffGrant),
        ('support_refund',SyntheticSupportRefundStaffGrant),('overpayment',SyntheticOverpaymentStaffGrant),
        ('payment',SyntheticPaymentStaffGrant),('shb_order',PaidOrderGrant),('shb_invitation',InvitationStaffGrant),
        ('shb_invitation_issue',InvitationIssueGrant),('shb_discount',DiscountStaffGrant),
        ('shb_discount_issue',DiscountIssueGrant))
    query={} if user_id is None else {'user_id':user_id}
    return {name:model.objects.filter(**query).delete()[0] for name,model in scopes}
