"""Read-only local recovery metadata; never sends or retries payments."""
from datetime import datetime
import json
from uuid import UUID
from django.core.management.base import BaseCommand,CommandError
from django.db import connection,DatabaseError
from shop.payments.attempts import inspect
from shop.payments.bank_contract import BankError
from shop.payments.models import SyntheticPaymentAttempt


class Command(BaseCommand):
    help='Inspect one local synthetic payment attempt without archive or provider I/O.'

    def add_arguments(self,parser):
        parser.add_argument('--attempt',required=True)

    def handle(self,*args,**options):
        try:
            value=options['attempt']
            if type(value) is not str or len(value)!=36:raise ValueError()
            attempt_id=UUID(value)
            if str(attempt_id)!=value or connection.vendor!='postgresql':raise ValueError()
            result=inspect(attempt_id)
            report={key:getattr(result,key) for key in (
                'state','expires_at','stopped_at','dispatch_held','control_revision','expiry_due','provider_status','lookup_required',
                'evidence_class','retry_authorized','financial_confirmation','effects_authorized')}
        except (ValueError,TypeError,BankError,SyntheticPaymentAttempt.DoesNotExist,DatabaseError):
            raise CommandError('Local synthetic payment inspection unavailable') from None
        report={key:(value.isoformat() if isinstance(value,datetime) else value) for key,value in report.items()}
        self.stdout.write(json.dumps(report,sort_keys=True,separators=(',',':')))
