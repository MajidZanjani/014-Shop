"""Synthetic example executed only by the fresh-owned-database demo wrapper."""
from pathlib import Path
import json,uuid,re,secrets,tempfile
from django.contrib.auth import get_user_model
from django.conf import settings
from django.test import Client
from django.utils import timezone
from shop.access.models import CustomerIdentity
from shop.adapters.evidence_archive import PreparedArchive
from shop.catalog.rules import CATALOG
from shop.catalog.purchase_policy import quote
from shop.catalog import business_rules, checkout, checkout_payment, fulfilment
from django.test import override_settings
from . import purchase_demo as purchase,synthetic_bank


def run(archive_root):
    synthetic_bank.guard()
    owner=get_user_model().objects.create_user(username='synthetic-demo-'+uuid.uuid4().hex)
    # Deliberate local fixture identity, not real email/access-delivery evidence.
    identity=CustomerIdentity.objects.create(user=owner,email='demo-'+uuid.uuid4().hex+'@synthetic.invalid',verified_at=timezone.now())
    client=Client(enforce_csrf_checks=True,HTTP_HOST='localhost');client.force_login(owner)
    session=client.session;session['shop_verified_identity']=str(identity.pk);session.save()
    client.get('/purchase/simple/');csrf=client.cookies['csrftoken'].value
    base={'product_id':CATALOG['product_id'],'profile_id':CATALOG['profile_id'],'quantity':1,
        'vendor':'altera','families':['altera-max-10'],'term':'rd-annual','production_band':None,
        'production_units':None,'fixed_nodes':1,'floating_nodes':0,'support_packages':2}
    results=[]
    with PreparedArchive(Path(archive_root)) as archive:
        for choice in ('not-designed','other-board'):
            configuration=base|{'platform':{'choice':choice,'kit_id':None,'name':None}}
            response=client.post('/api/v1/configuration-drafts/',data=json.dumps({'request_id':str(uuid.uuid4()),
                'revision':CATALOG['revision'],'configuration':configuration}),content_type='application/json',HTTP_X_CSRFTOKEN=csrf)
            if response.status_code!=201:raise RuntimeError('synthetic demo draft rejected')
            row=purchase.prepare(owner,uuid.uuid4(),draft_id=response.json()['id'],offer_id='synthetic-development')
            row=purchase.fund(row.pk,owner,archive)
            row=purchase.deliver(row.pk,owner,archive,'initial')
            outstanding=not row.reference_delivered
            row=purchase.deliver(row.pk,owner,archive,'reference')
            if not (row.simulated_funded and outstanding and row.reference_delivered and row.simulated_entitlements==1):
                raise RuntimeError('synthetic staged result mismatch')
            results.append({'platform':choice,'status':'synthetic_funded','support_seconds':row.simulated_credit_seconds,
                'initial_leaves_reference_outstanding':outstanding,'later_delivery_entitlements':row.simulated_entitlements})
        ready=base|{'support_packages':0,'platform':{'choice':'listed-kit','kit_id':'synthetic-kit-rev-a','name':None}}
        if quote(ready,'synthetic-ready-kit')['status']!='synthetic_purchasable':raise RuntimeError('synthetic ready-kit rule mismatch')
        tampered=base|{'support_packages':0,'platform':{'choice':'not-designed','kit_id':None,'name':None}}
        if 'required_support_minimum' not in quote(tampered,'synthetic-development')['errors']:raise RuntimeError('synthetic support rule mismatch')
        topup=purchase.prepare(owner,uuid.uuid4(),support_packages=1)
        topup=purchase.fund(topup.pk,owner,archive)
        key=uuid.uuid4();first=purchase.reserve_credit(topup.pk,owner,key,36000)
        second=purchase.reserve_credit(topup.pk,owner,key,36000)
        if first.pk!=second.pk or topup.simulated_entitlements!=0:raise RuntimeError('synthetic topup result mismatch')
        # Use the same supported cart/business/checkout routes as API and no-JavaScript customers.
        ip_configuration=base|{'support_packages':0,'platform':{'choice':'not-designed','kit_id':None,'name':None}}
        lines=[{'id':str(uuid.uuid4()),'kind':'ip','product_id':CATALOG['product_id'],'quantity':1,'configuration':ip_configuration},
               {'id':str(uuid.uuid4()),'kind':'support','product_id':CATALOG['support_product_id'],'quantity':2}]
        response=client.post('/api/v1/cart/',data=json.dumps({'request_id':str(uuid.uuid4()),'expected_version':0,
            'catalog_revision':CATALOG['revision'],'lines':lines}),content_type='application/json',HTTP_X_CSRFTOKEN=csrf)
        if response.status_code!=201:raise RuntimeError('synthetic complete cart rejected')
        details={name:'' for name in business_rules.LIMITS}
        details.update(legal_business_name='Synthetic demo organisation',registered_address='Synthetic address',
            purchasing_name='Synthetic buyer',business_email='buyer@synthetic.invalid',
            billing_same_as_registered='on',technical_same_as_purchasing='on')
        from urllib.parse import urlencode
        response=client.post('/purchase/business/',data=urlencode(details|{'request_id':str(uuid.uuid4()),
            'expected_version':'0','schema_version':str(business_rules.SCHEMA_VERSION),'source_sha256':business_rules.SOURCE_SHA256}),
            content_type='application/x-www-form-urlencoded',HTTP_X_CSRFTOKEN=csrf)
        if response.status_code!=303:raise RuntimeError('synthetic business details rejected')
        reviewed=client.get('/api/v1/checkout-rehearsal/')
        if reviewed.status_code!=200:raise RuntimeError('synthetic checkout held')
        command={'request_id':str(uuid.uuid4()),'sha256':reviewed.json()['sha256']}
        response=client.post('/api/v1/checkout-rehearsal/',data=json.dumps(command),content_type='application/json',HTTP_X_CSRFTOKEN=csrf)
        if response.status_code!=201:raise RuntimeError('synthetic checkout capture rejected')
        retained=checkout.archive_capture(uuid.UUID(response.json()['id']),owner,archive)
        replay=client.post('/purchase/checkout-rehearsal/',data=urlencode(command),
            content_type='application/x-www-form-urlencoded',HTTP_X_CSRFTOKEN=csrf)
        if replay.status_code!=200 or retained.snapshot['cart']['lines']!=lines:raise RuntimeError('synthetic checkout replay mismatch')
        payment_url='/api/v1/checkout-rehearsal/'+str(retained.pk)+'/payment/'
        page_url='/purchase/checkout-rehearsal/'+str(retained.pk)+'/payment/'
        with override_settings(LOCAL_CHECKOUT_ARCHIVE_ROOT=str(archive_root)):
            review=client.get(payment_url)
            if review.status_code!=200:raise RuntimeError('synthetic acceptance review failed')
            confirmed=client.post(page_url,data=urlencode({'action':'accept','sha256':review.json()['sha256'],'confirmed':'on'}),
                content_type='application/x-www-form-urlencoded',HTTP_X_CSRFTOKEN=csrf)
            if confirmed.status_code!=200:raise RuntimeError('synthetic confirmation rejected')
            paid=client.post(payment_url,data=json.dumps({'action':'pay'}),content_type='application/json',HTTP_X_CSRFTOKEN=csrf)
            repeated=client.post(payment_url,data=json.dumps({'action':'pay'}),content_type='application/json',HTTP_X_CSRFTOKEN=csrf)
            if paid.status_code!=200 or not paid.json()['simulated_paid'] or repeated.json()['order_reference']!=paid.json()['order_reference']:
                raise RuntimeError('synthetic complete-cart payment mismatch')
            row=checkout_payment.accepted(owner,retained.pk);checkout_payment.retained(row,archive)
            granted=client.post(payment_url,data=json.dumps({'action':'provision'}),content_type='application/json',HTTP_X_CSRFTOKEN=csrf)
            if granted.status_code!=200 or granted.json()['fulfilment']['support_seconds']!=72000:
                raise RuntimeError('synthetic cart grant mismatch')
            line_id=lines[0]['id']
            initial=client.post(payment_url,data=json.dumps({'action':'deliver_initial','line_id':line_id}),content_type='application/json',HTTP_X_CSRFTOKEN=csrf)
            if initial.status_code!=200 or initial.json()['fulfilment']['lines'][0]['reference_delivered']:
                raise RuntimeError('synthetic cart later obligation lost')
            later=client.post(payment_url,data=json.dumps({'action':'deliver_reference','line_id':line_id}),content_type='application/json',HTTP_X_CSRFTOKEN=csrf)
            if later.status_code!=200 or later.json()['fulfilment']['entitlement_count']!=1 or not later.json()['fulfilment']['lines'][0]['reference_delivered']:
                raise RuntimeError('synthetic cart staged completion mismatch')
            repeated=client.post(payment_url,data=json.dumps({'action':'provision'}),content_type='application/json',HTTP_X_CSRFTOKEN=csrf)
            if repeated.json()['fulfilment']['support_seconds']!=72000:raise RuntimeError('synthetic support duplicate grant')

            from .models import SyntheticBankOperation
            if SyntheticBankOperation.objects.filter(merchant='synthetic-checkout',reference=row.pk).count()!=1:
                raise RuntimeError('duplicate synthetic complete-cart payment')
        # Drive the new ledger through supported customer/staff routes, with both
        # local staff factors and one explicit support assignment. No MFA bypass.
        support_url='/purchase/checkout-rehearsal/'+str(retained.pk)+'/support/'
        grant=fulfilment.SyntheticFulfilment.objects.get(acceptance=row)
        with override_settings(LOCAL_CHECKOUT_ARCHIVE_ROOT=str(archive_root)):
            key=str(uuid.uuid4());task=str(uuid.uuid4())
            reserve={'action':'reserve','request_id':key,'task_id':task,'seconds':7200}
            reserved=client.post(support_url,data=json.dumps(reserve),content_type='application/json',HTTP_X_CSRFTOKEN=csrf)
            repeated=client.post(support_url,data=json.dumps(reserve),content_type='application/json',HTTP_X_CSRFTOKEN=csrf)
            if reserved.status_code!=200 or repeated.json()['ledger']['revision']!=1:
                raise RuntimeError('synthetic ledger reservation/retry failed')
            reservation_id=next(iter(reserved.json()['ledger']['reservations']))
            from shop.access.models import StaffCredential
            from shop.catalog.models import SyntheticSupportStaffGrant
            staff_name='support-demo-'+uuid.uuid4().hex;password=secrets.token_urlsafe(32)
            staff_user=get_user_model().objects.create_user(username=staff_name,password=password,is_staff=True)
            StaffCredential.objects.create(user=staff_user)
            staff=Client(enforce_csrf_checks=True,HTTP_HOST='staff.localhost')
            staff_url='/staff/support/'+str(retained.pk)+'/'
            middleware=[settings.MIDDLEWARE[0],'shop.access.staff_middleware.StaffHostMiddleware',
                *settings.MIDDLEWARE[1:],'shop.access.staff_middleware.StaffMFAMiddleware']
            staff_settings={'ROOT_URLCONF':'shop.staff_urls','LOCAL_STAFF_ENABLED':True,
                'ALLOWED_HOSTS':['staff.localhost'],'MIDDLEWARE':middleware,
                'SESSION_COOKIE_NAME':'shop_staff_sessionid','CSRF_COOKIE_NAME':'shop_staff_csrftoken'}
            with tempfile.TemporaryDirectory(prefix='staff-ledger-',dir=Path(archive_root).parent) as capture:
                with override_settings(**staff_settings,LOCAL_STAFF_CAPTURE_ROOT=capture):
                    staff_token=staff.get('/staff/session/').json()['csrf_token']
                    logged=staff.post('/staff/login/',data=json.dumps({'username':staff_name,'password':password}),
                        content_type='application/json',HTTP_X_CSRFTOKEN=staff_token)
                    if logged.status_code!=200:raise RuntimeError('synthetic ledger staff password failed')
                    files=list(Path(capture).iterdir())
                    if len(files)!=1:raise RuntimeError('synthetic ledger possession capture failed')
                    code=re.search(r'^Code: (.+)$',files[0].read_text(),re.M)[1]
                    verified=staff.post('/staff/verify/',data=json.dumps({'code':code}),
                        content_type='application/json',HTTP_X_CSRFTOKEN=logged.json()['csrf_token'])
                    if verified.status_code!=200:raise RuntimeError('synthetic ledger staff second factor failed')
                    staff_token=verified.json()['csrf_token']
                    if staff.get(staff_url).status_code!=404:raise RuntimeError('unassigned synthetic ledger exposed')
                    SyntheticSupportStaffGrant.objects.create(user=staff_user,fulfilment=grant)
                    work_command={'action':'work','request_id':str(uuid.uuid4()),'target_id':reservation_id,'seconds':3600}
                    worked=staff.post(staff_url,data=json.dumps(work_command),content_type='application/json',HTTP_X_CSRFTOKEN=staff_token)
                    repeated=staff.post(staff_url,data=json.dumps(work_command),content_type='application/json',HTTP_X_CSRFTOKEN=staff_token)
                    if worked.status_code!=200 or repeated.json()['ledger']['revision']!=2:
                        raise RuntimeError('synthetic ledger work/retry failed')
                    work_id=next(iter(worked.json()['ledger']['work']))
                    corrected=staff.post(staff_url,data=json.dumps({'action':'correct','request_id':str(uuid.uuid4()),
                        'target_id':work_id,'seconds':1800}),content_type='application/json',HTTP_X_CSRFTOKEN=staff_token)
                    if corrected.status_code!=200 or corrected.json()['ledger']['spent_seconds']!=1800:
                        raise RuntimeError('synthetic ledger correction failed')
                released=client.post(support_url,data=json.dumps({'action':'release','request_id':str(uuid.uuid4()),
                    'target_id':reservation_id}),content_type='application/json',HTTP_X_CSRFTOKEN=csrf)
                if released.status_code!=200 or released.json()['ledger']['reserved_seconds']!=0:
                    raise RuntimeError('synthetic ledger remainder release failed')
                with override_settings(**staff_settings,LOCAL_STAFF_CAPTURE_ROOT=capture):
                    statement_command={'action':'statement','request_id':str(uuid.uuid4())}
                    for _ in range(2):
                        published=staff.post(staff_url,data=json.dumps(statement_command),content_type='application/json',HTTP_X_CSRFTOKEN=staff_token)
                        if published.status_code!=200 or published.json()['ledger']['revision']!=5:
                            raise RuntimeError('synthetic ledger statement/retry failed')
            final=client.get(support_url,HTTP_ACCEPT='application/json').json()['ledger']
            if (final['spent_seconds']!=1800 or final['available_seconds']!=70200
                    or len(final['statements'])!=1 or final['statements'][0]['statement']['revision']!=4
                    or final['actual_support_spendable'] is not False):
                raise RuntimeError('synthetic committed ledger statement mismatch')
        complete_cart={'all_lines_retained':True,'business_revision':retained.snapshot['business']['version'],
            'document_revision':retained.snapshot['documents']['revision'],'archive_recovered':bool(retained.archive_receipt),
            'api_and_no_javascript_same_capture':True,'acceptance_enabled':False,
            'synthetic_acceptance_recorded':True,'simulated_payment_captured':True,'single_order_reference_and_bank_operation':True,'cart_entitlement_once':True,
            'cart_staged_delivery_preserves_later_obligation':True,'cart_support_seconds_once':72000,'actual_support_spendable':False,
            'support_ledger':{'revision':final['revision'],'reserved_seconds':final['reserved_seconds'],
                'spent_seconds':final['spent_seconds'],'available_seconds':final['available_seconds'],
                'statement_committed_revision':final['statements'][0]['statement']['revision'],
                'local_staff_two_factors_and_exact_grant':True,'reverse_replace_history_preserved':True}}

    return {'status':'PURCHASE_FLOW_DEMO_PASS','evidence_class':'local-synthetic','financial_confirmation':False,
        'effects_authorized':False,'real_email_verification':False,'ready_kit_zero_support':True,'required_support_tamper_refused':True,
        'complete_cart_checkout':complete_cart,'topup_without_platform_or_new_licence':True,'reservation_retry_once':True,'development_cases':results,
        'pending':['actual commercial/kit/rights/support/terms approvals','actual order acceptance and entitlement/ledger delivery','qualified private technical follow-up','external bank/mail/host/recovery qualification']}
