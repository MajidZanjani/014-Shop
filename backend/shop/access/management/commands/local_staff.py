"""Explicit disposable staff operator actions. Never a production bootstrap."""
import re
import secrets
import uuid
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from shop.adapters.local_storage import LocalStorage
from shop.catalog.models import QuotationRequest, SyntheticFulfilment, SyntheticSupportStaffGrant, SyntheticDeliveryStaffGrant, SyntheticLineEntitlement, SyntheticLicenceCase, SyntheticLicenceCaseStaffGrant, SyntheticSupportRefundCase, SyntheticSupportRefundStaffGrant
from shop.payments.models import SyntheticOverpaymentStaffGrant, SyntheticPaymentAttempt, SyntheticPaymentStaffGrant
from shop.catalog.models import SyntheticCheckoutAcceptance
from shop.access.models import StaffCredential, StaffQuotationGrant
from shop.access.grants import revoke_staff_resource_grants

class Command(BaseCommand):
    help='Local/synthetic staff provision/reset/revoke and explicit quotation reviewer grants. Credentials go to private files only.'
    def add_arguments(self,parser):
        parser.add_argument('action',choices=['provision','reset','revoke','grant','revoke-grant','grant-business','revoke-business','grant-support','revoke-support','grant-delivery','revoke-delivery','grant-case','revoke-case','grant-refund','revoke-refund','grant-overpayment','revoke-overpayment','grant-payment','revoke-payment','grant-shb-order','revoke-shb-order','grant-invitation','revoke-invitation-grant','grant-invitation-issue','revoke-invitation-issue'])
        parser.add_argument('--username',required=True)
        parser.add_argument('--capture-root')
        parser.add_argument('--quotation')
        parser.add_argument('--checkout')
        parser.add_argument('--order')
        parser.add_argument('--invitation')
        parser.add_argument('--issuance-scope')
        parser.add_argument('--entitlement')
        parser.add_argument('--case')
        parser.add_argument('--attempt')
        parser.add_argument('--acceptance')
        parser.add_argument('--operation-kind',choices=['capture','refund'])
        parser.add_argument('--business-scope',type=int)
    def handle(self,*args,**options):
        if settings.SHOP_ENV not in ('local','synthetic'):raise CommandError('Synthetic staff operation unavailable')
        name=options['username'];action=options['action']
        if re.fullmatch(r'[a-zA-Z0-9_.-]{1,100}',name) is None:raise CommandError('Invalid synthetic staff username')
        with transaction.atomic():
            if action=='provision':
                if get_user_model().objects.filter(username=name).exists():raise CommandError('Existing identity cannot be provisioned')
                user=get_user_model().objects.create_user(username=name,is_staff=True)
                credential=StaffCredential.objects.create(user=user)
            else:
                credential=StaffCredential.objects.select_for_update().select_related('user').filter(user__username=name).first()
                if credential is None or not credential.user.is_staff or credential.user.is_superuser:
                    raise CommandError('Synthetic staff identity unavailable')
                user=credential.user
            if action in ('provision','reset'):
                root=options.get('capture_root')
                if not root:raise CommandError('Private synthetic capture root required')
                password=secrets.token_urlsafe(32)
                user.set_password(password);user.save(update_fields=['password'])
                credential.generation=uuid.uuid4();credential.enabled=True;credential.save()
                # Recovery never silently restores old resource authority.
                revoke_staff_resource_grants(user_id=user.pk)
                try:
                    with LocalStorage(root) as store:store.put(('Synthetic staff credentials only.\nUsername: '+name+'\nPassword: '+password+'\n').encode())
                except (OSError,ValueError):raise CommandError('Private synthetic capture unavailable') from None
            elif action=='revoke':
                credential.enabled=False;credential.generation=uuid.uuid4();credential.save()
                revoke_staff_resource_grants(user_id=user.pk)
            elif action in ('grant-invitation-issue','revoke-invitation-issue'):
                from shop.shb.models import InvitationIssuanceScope,InvitationIssueGrant
                from shop.shb.invitations import fixture_guard
                try:
                    fixture_guard();identity=uuid.UUID(options.get('issuance_scope') or '')
                except (ValueError,TypeError):raise CommandError('Exact synthetic issuance scope required') from None
                scope=InvitationIssuanceScope.objects.filter(pk=identity).first()
                if scope is None:raise CommandError('Synthetic issuance scope unavailable')
                if action=='grant-invitation-issue':
                    if not credential.enabled or not user.is_active or not scope.enabled:raise CommandError('Active staff and issuance scope required')
                    InvitationIssueGrant.objects.get_or_create(user=user,scope=scope)
                else:InvitationIssueGrant.objects.filter(user=user,scope=scope).delete()
            elif action in ('grant-invitation','revoke-invitation-grant'):
                from shop.shb.models import Invitation,InvitationStaffGrant
                from shop.shb.invitations import fixture_guard
                try:
                    fixture_guard();identity=uuid.UUID(options.get('invitation') or '')
                except (ValueError,TypeError):raise CommandError('Exact synthetic invitation required') from None
                invite=Invitation.objects.filter(pk=identity).first()
                if invite is None:raise CommandError('Synthetic invitation unavailable')
                if action=='grant-invitation':
                    if not credential.enabled or not user.is_active:raise CommandError('Staff identity disabled')
                    InvitationStaffGrant.objects.get_or_create(user=user,invitation=invite)
                else:InvitationStaffGrant.objects.filter(user=user,invitation=invite).delete()
            elif action in ('grant-shb-order','revoke-shb-order'):
                from shop.shb.models import PaidOrder,PaidOrderGrant
                try:identity=uuid.UUID(options.get('order') or '')
                except (ValueError,TypeError):raise CommandError('Exact SHB order required') from None
                order=PaidOrder.objects.filter(pk=identity).first()
                if order is None:raise CommandError('SHB order unavailable')
                if action=='grant-shb-order':
                    if not credential.enabled or not user.is_active:raise CommandError('Staff identity disabled')
                    PaidOrderGrant.objects.get_or_create(user=user,order=order)
                else:PaidOrderGrant.objects.filter(user=user,order=order).delete()
            elif action in ('grant-payment','revoke-payment'):
                try:identity=uuid.UUID(options.get('acceptance') or '')
                except (ValueError,TypeError):raise CommandError('Exact acceptance required') from None
                accepted=SyntheticCheckoutAcceptance.objects.filter(pk=identity).first();kind=options.get('operation_kind')
                if accepted is None or kind not in ('capture','refund'):raise CommandError('Synthetic payment scope unavailable')
                if action=='grant-payment':
                    if not credential.enabled or not user.is_active:raise CommandError('Staff identity disabled')
                    SyntheticPaymentStaffGrant.objects.get_or_create(user=user,acceptance=accepted,kind=kind)
                else:SyntheticPaymentStaffGrant.objects.filter(user=user,acceptance=accepted,kind=kind).delete()
            elif action in ('grant-overpayment','revoke-overpayment'):
                try:
                    acceptance_id=uuid.UUID(options.get('acceptance') or '')
                    attempt_id=uuid.UUID(options.get('attempt') or '')
                except (ValueError,TypeError):raise CommandError('Exact synthetic acceptance and extra attempt required') from None
                accepted=SyntheticCheckoutAcceptance.objects.filter(pk=acceptance_id).first()
                extra=SyntheticPaymentAttempt.objects.filter(pk=attempt_id).first()
                if accepted is None or extra is None or accepted.attempt_id==extra.pk:raise CommandError('Synthetic pair unavailable')
                if action=='grant-overpayment':
                    if not credential.enabled or not user.is_active:raise CommandError('Staff identity disabled')
                    SyntheticOverpaymentStaffGrant.objects.get_or_create(user=user,acceptance=accepted,extra_attempt=extra)
                else:SyntheticOverpaymentStaffGrant.objects.filter(user=user,acceptance=accepted,extra_attempt=extra).delete()
            elif action in ('grant-refund','revoke-refund'):
                try:identity=uuid.UUID(options.get('case') or '')
                except (ValueError,TypeError):raise CommandError('Support refund case identity required') from None
                case=SyntheticSupportRefundCase.objects.select_for_update().filter(identity=identity).first()
                if case is None:raise CommandError('Synthetic support refund case unavailable')
                if action=='grant-refund':
                    if not credential.enabled or not user.is_active:raise CommandError('Staff identity disabled')
                    SyntheticSupportRefundStaffGrant.objects.get_or_create(user=user,case=case)
                else:SyntheticSupportRefundStaffGrant.objects.filter(user=user,case=case).delete()
            elif action in ('grant-case','revoke-case'):

                try:identity=uuid.UUID(options.get('case') or '')
                except (ValueError,TypeError):raise CommandError('Licence case identity required') from None
                case=SyntheticLicenceCase.objects.select_for_update().filter(identity=identity).first()
                if case is None:raise CommandError('Synthetic licence case unavailable')
                if action=='grant-case':
                    if not credential.enabled or not user.is_active:raise CommandError('Staff identity disabled')
                    SyntheticLicenceCaseStaffGrant.objects.get_or_create(user=user,case=case)
                else:SyntheticLicenceCaseStaffGrant.objects.filter(user=user,case=case).delete()
            elif action in ('grant-delivery','revoke-delivery'):
                try:identity=uuid.UUID(options.get('entitlement') or '')
                except (ValueError,TypeError):raise CommandError('Entitlement identity required') from None
                line=SyntheticLineEntitlement.objects.select_for_update().filter(pk=identity).first()
                if line is None:raise CommandError('Synthetic entitlement unavailable')
                if action=='grant-delivery':
                    if not credential.enabled or not user.is_active:raise CommandError('Staff identity disabled')
                    SyntheticDeliveryStaffGrant.objects.get_or_create(user=user,entitlement=line)
                else:SyntheticDeliveryStaffGrant.objects.filter(user=user,entitlement=line).delete()
            elif action in ('grant-support','revoke-support'):
                try:identity=uuid.UUID(options.get('checkout') or '')
                except (ValueError,TypeError):raise CommandError('Checkout identity required') from None
                grant=SyntheticFulfilment.objects.select_for_update().filter(acceptance__checkout_id=identity).first()
                if grant is None:raise CommandError('Synthetic support grant unavailable')
                if action=='grant-support':
                    if not credential.enabled or not user.is_active:raise CommandError('Staff identity disabled')
                    SyntheticSupportStaffGrant.objects.get_or_create(user=user,fulfilment=grant)
                else:SyntheticSupportStaffGrant.objects.filter(user=user,fulfilment=grant).delete()
            else:
                try:identity=uuid.UUID(options.get('quotation') or '')
                except (ValueError,TypeError):raise CommandError('Quotation identity required') from None
                quotation=QuotationRequest.objects.select_for_update().filter(pk=identity).first()
                if quotation is None:raise CommandError('Quotation unavailable')
                if action=='grant':
                    if not credential.enabled or not user.is_active:raise CommandError('Staff identity disabled')
                    StaffQuotationGrant.objects.get_or_create(user=user,quotation=quotation)
                elif action in ('grant-business','revoke-business'):
                    grant=StaffQuotationGrant.objects.filter(user=user,quotation=quotation).first()
                    if grant is None:raise CommandError('Explicit quotation assignment required')
                    if action=='grant-business':
                        scope_version=quotation.business_version
                        from shop.shb.models import SupportRequest
                        support=SupportRequest.objects.filter(quotation=quotation).first()
                        if support is not None:
                            from shop.shb.invitations import fixture_guard
                            try:fixture_guard()
                            except ValueError:raise CommandError('Synthetic SHB assignment unavailable') from None
                            scope_version=support.revision
                        if not credential.enabled or not user.is_active or not scope_version or options.get('business_scope')!=scope_version:
                            raise CommandError('Exact current business scope required')
                        grant.business_scope_version=scope_version
                    else:grant.business_scope_version=0
                    grant.save(update_fields=['business_scope_version'])
                else:StaffQuotationGrant.objects.filter(user=user,quotation=quotation).delete()
        self.stdout.write('Synthetic staff action completed; credentials, when generated, are in the private capture directory.')
