"""Explicit disposable staff operator actions. Never a production bootstrap."""
import re
import secrets
import uuid
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from shop.adapters.local_storage import LocalStorage
from shop.catalog.models import QuotationRequest
from shop.access.models import StaffCredential, StaffQuotationGrant

class Command(BaseCommand):
    help='Local/synthetic staff provision/reset/revoke and explicit quotation reviewer grants. Credentials go to private files only.'
    def add_arguments(self,parser):
        parser.add_argument('action',choices=['provision','reset','revoke','grant','revoke-grant','grant-business','revoke-business'])
        parser.add_argument('--username',required=True)
        parser.add_argument('--capture-root')
        parser.add_argument('--quotation')
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
                StaffQuotationGrant.objects.filter(user=user).delete()
                try:
                    with LocalStorage(root) as store:store.put(('Synthetic staff credentials only.\nUsername: '+name+'\nPassword: '+password+'\n').encode())
                except (OSError,ValueError):raise CommandError('Private synthetic capture unavailable') from None
            elif action=='revoke':
                credential.enabled=False;credential.generation=uuid.uuid4();credential.save()
                StaffQuotationGrant.objects.filter(user=user).delete()
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
                        if not credential.enabled or not user.is_active or not quotation.business_version or options.get('business_scope')!=quotation.business_version:
                            raise CommandError('Exact current business scope required')
                        grant.business_scope_version=quotation.business_version
                    else:grant.business_scope_version=0
                    grant.save(update_fields=['business_scope_version'])
                else:StaffQuotationGrant.objects.filter(user=user,quotation=quotation).delete()
        self.stdout.write('Synthetic staff action completed; credentials, when generated, are in the private capture directory.')
