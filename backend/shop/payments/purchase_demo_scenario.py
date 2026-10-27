"""Synthetic example executed only by the fresh-owned-database demo wrapper."""
from pathlib import Path
from dataclasses import replace
from unittest.mock import patch
from io import StringIO
from django.core.management import call_command
import json,uuid,re,secrets,tempfile
from django.contrib.auth import get_user_model
from django.conf import settings
from django.test import Client
from django.utils import timezone
from shop.access.models import CustomerIdentity
from shop.adapters.evidence_archive import PreparedArchive
from shop.catalog.rules import CATALOG
from shop.catalog.purchase_policy import quote,FIXTURE_OFFERS
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
        # Undefined applicable terms and unsupported ready-design promises hold.
        for field in ('licence_minor','rights','delivery'):
            held_offer=replace(FIXTURE_OFFERS[1],**{field:None})
            if quote(base|{'platform':{'choice':'not-designed','kit_id':None,'name':None}},
                     held_offer.id,offers=(held_offer,))['status']!='awaiting_review':
                raise RuntimeError('undefined synthetic commercial fact accepted')
        if quote(base|{'platform':{'choice':'other-board','kit_id':None,'name':None}},
                 'synthetic-ready-kit')['status']!='unavailable':
            raise RuntimeError('unsupported ready-design promise accepted')
        topup=purchase.prepare(owner,uuid.uuid4(),support_packages=1)
        topup=purchase.fund(topup.pk,owner,archive)
        key=uuid.uuid4();first=purchase.reserve_credit(topup.pk,owner,key,36000)
        second=purchase.reserve_credit(topup.pk,owner,key,36000)
        if first.pk!=second.pk or topup.simulated_entitlements!=0:raise RuntimeError('synthetic topup result mismatch')
        from .bank_contract import BankError
        try:purchase.reserve_credit(topup.pk,owner,uuid.uuid4(),1)
        except BankError as error:
            if str(error)!='synthetic_credit_unavailable':raise
        else:raise RuntimeError('synthetic credit double allocation')
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
        original_digest=reviewed.json()['sha256']
        removed=client.post('/api/v1/cart/',data=json.dumps({'request_id':str(uuid.uuid4()),
            'expected_version':1,'catalog_revision':CATALOG['revision'],'lines':[lines[0]]}),
            content_type='application/json',HTTP_X_CSRFTOKEN=csrf)
        if removed.status_code!=201:raise RuntimeError('synthetic support removal fixture failed')
        blocked={'request_id':str(uuid.uuid4()),'sha256':original_digest}
        for url in ('/api/v1/checkout-rehearsal/','/purchase/checkout-rehearsal/'):
            review=client.get(url)
            if review.status_code!=422:raise RuntimeError('removed support allowed checkout review')
            is_api=url.startswith('/api/')
            rejected=client.post(url,data=json.dumps(blocked) if is_api else urlencode(blocked),
                content_type='application/json' if is_api else 'application/x-www-form-urlencoded',
                HTTP_X_CSRFTOKEN=csrf)
            if rejected.status_code!=422:raise RuntimeError('removed support allowed checkout capture')
        restored=client.post('/api/v1/cart/',data=json.dumps({'request_id':str(uuid.uuid4()),
            'expected_version':2,'catalog_revision':CATALOG['revision'],'lines':lines}),
            content_type='application/json',HTTP_X_CSRFTOKEN=csrf)
        if restored.status_code!=201:raise RuntimeError('synthetic support restoration failed')
        reviewed=client.get('/api/v1/checkout-rehearsal/')
        if reviewed.status_code!=200:raise RuntimeError('restored synthetic support did not unblock')
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
            original_start=synthetic_bank.start
            def lose_response(request,**options):
                options['fault']='after_commit'
                return original_start(request,**options)
            with patch.object(synthetic_bank,'start',side_effect=lose_response):
                uncertain=client.post(payment_url,data=json.dumps({'action':'pay'}),content_type='application/json',HTTP_X_CSRFTOKEN=csrf)
            if uncertain.status_code!=409 or uncertain.json()['error']!='payment_uncertain_use_lookup':raise RuntimeError('synthetic notification uncertainty fixture failed')
            pending=checkout_payment.accepted(owner,retained.pk)
            notice=uuid.uuid4()
            from . import notifications
            from shop.worker.services import execute_once as worker_once
            for _ in range(2):
                call_command('local_bank_notification','enqueue',attempt=str(pending.attempt_id),notification=str(notice),stdout=StringIO())
            if notifications.inspect(notice,archive)['state']!='pending':raise RuntimeError('synthetic hint prematurely applied money')
            with patch.object(synthetic_bank,'start',side_effect=AssertionError('blind payment retry')):
                not_paid=client.post(payment_url,data=json.dumps({'action':'pay'}),content_type='application/json',HTTP_X_CSRFTOKEN=csrf)
                if not_paid.status_code!=200 or not_paid.json()['simulated_paid']:raise RuntimeError('uncertain payment was resent or inferred')
                if not worker_once():raise RuntimeError('notification worker did not process hint')
                paid=client.get(payment_url)
                repeated=client.post(payment_url,data=json.dumps({'action':'pay'}),content_type='application/json',HTTP_X_CSRFTOKEN=csrf)
            if notifications.inspect(notice,archive)['state']!='checked':raise RuntimeError('synthetic lookup evidence not committed')
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
            from shop.catalog.models import SyntheticSupportStaffGrant,SyntheticDeliveryStaffGrant,SyntheticLineEntitlement,SyntheticLicenceCase,SyntheticLicenceCaseStaffGrant
            change_line=SyntheticLineEntitlement.objects.get(fulfilment=grant)
            change_url='/purchase/checkout-rehearsal/'+str(retained.pk)+'/changes/new/'+str(change_line.pk)+'/'
            case_bank_count=SyntheticBankOperation.objects.count()
            case_requests=[{'kind':'renewal'},{'kind':'rehost'},{'kind':'family-addition','families':['altera-cyclone-10']},
                {'kind':'node-addition','fixed_nodes':1,'floating_nodes':0},
                {'kind':'production-upgrade','term':'rdp-yearly','production_band':'higher-volume','production_units':6500}]
            case_ids=[]
            for change in case_requests:
                command=change|{'request_id':str(uuid.uuid4())}
                captured=client.post(change_url,data=json.dumps(command),content_type='application/json',HTTP_X_CSRFTOKEN=csrf)
                repeated=client.post(change_url,data=json.dumps(command),content_type='application/json',HTTP_X_CSRFTOKEN=csrf)
                if captured.status_code!=201 or repeated.json()['case_id']!=captured.json()['case_id']:
                    raise RuntimeError('synthetic licence case capture/retry failed')
                case_ids.append(captured.json()['case_id'])
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
                    delivery_line=SyntheticLineEntitlement.objects.get(fulfilment=grant)
                    delivery_url='/staff/delivery/'+str(delivery_line.pk)+'/'
                    if staff.get(delivery_url).status_code!=404:raise RuntimeError('unassigned private delivery exposed')
                    SyntheticDeliveryStaffGrant.objects.create(user=staff_user,entitlement=delivery_line)
                    for delivery_stage,fixture_version in (('initial','synthetic-materials-v1'),('reference','synthetic-materials-v1'),('initial','synthetic-materials-v2')):
                        package_command={'request_id':str(uuid.uuid4()),'stage':delivery_stage,'fixture':fixture_version}
                        for _ in range(2):
                            response=staff.post(delivery_url,data=urlencode(package_command),content_type='application/x-www-form-urlencoded',HTTP_X_CSRFTOKEN=staff_token)
                            if response.status_code!=303:raise RuntimeError('synthetic private package release/retry failed')
                    for case_id in case_ids:
                        case_url='/staff/licence-cases/'+case_id+'/'
                        if staff.get(case_url).status_code!=404:raise RuntimeError('unassigned licence case exposed')
                        change_case=SyntheticLicenceCase.objects.get(identity=case_id)
                        SyntheticLicenceCaseStaffGrant.objects.create(user=staff_user,case=change_case)
                        review_command={'action':'review','request_id':str(uuid.uuid4()),'expected_revision':0,'decision':'ready_for_commercial_review'}
                        for _ in range(2):
                            reviewed=staff.post(case_url,data=json.dumps(review_command),content_type='application/json',HTTP_X_CSRFTOKEN=staff_token)
                            if reviewed.status_code!=200 or reviewed.json()['revision']!=1:raise RuntimeError('licence case review/retry failed')
                        proposal_command={'action':'proposal','request_id':str(uuid.uuid4()),'expected_revision':1}
                        for _ in range(2):
                            proposed=staff.post(case_url,data=json.dumps(proposal_command),content_type='application/json',HTTP_X_CSRFTOKEN=staff_token)
                            if proposed.status_code!=200 or proposed.json()['revision']!=2:raise RuntimeError('held licence proposal/retry failed')
                        value=proposed.json()
                        if value['payment_enabled'] or value['actual_rights_changed'] or value['proposal']['order']['policies']['fee_minor'] is not None:
                            raise RuntimeError('licence case invented rights or financial policy')
                        if change_case.kind=='production-upgrade' and not value['proposal']['order']['quotation_required']:
                            raise RuntimeError('higher-volume quote requirement lost')
                    corrected_case_url='/staff/licence-cases/'+case_ids[0]+'/'
                    corrected=staff.post(corrected_case_url,data=json.dumps({'action':'review','request_id':str(uuid.uuid4()),
                        'expected_revision':2,'decision':'needs_information'}),content_type='application/json',HTTP_X_CSRFTOKEN=staff_token)
                    if corrected.status_code!=200 or corrected.json()['proposal']['active']:
                        raise RuntimeError('corrected licence review left prior proposal active')
                    reconsidered=staff.post(corrected_case_url,data=json.dumps({'action':'review','request_id':str(uuid.uuid4()),
                        'expected_revision':3,'decision':'ready_for_commercial_review'}),content_type='application/json',HTTP_X_CSRFTOKEN=staff_token)
                    replaced=staff.post(corrected_case_url,data=json.dumps({'action':'proposal','request_id':str(uuid.uuid4()),
                        'expected_revision':4}),content_type='application/json',HTTP_X_CSRFTOKEN=staff_token)
                    if reconsidered.status_code!=200 or replaced.status_code!=200 or replaced.json()['revision']!=5:
                        raise RuntimeError('licence proposal correction history failed')
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
            from shop.worker import statement_mail
            from shop.catalog.models import SyntheticStatementMail,SyntheticStatementCapture,SyntheticStatementDelivery
            mail=SyntheticStatementMail.objects.get(statement__fulfilment=grant)
            claimed=statement_mail.claim()
            if claimed is None or claimed.effect_id!=mail.pk:raise RuntimeError('synthetic statement claim failed')
            with PreparedArchive(Path(archive_root)) as mail_archive:
                if not statement_mail.capture(claimed,mail_archive):raise RuntimeError('synthetic durable statement capture failed')
                # Simulate response loss after durable sink commit, before acknowledgement.
                from datetime import timedelta
                SyntheticStatementDelivery.objects.filter(pk=mail.pk).update(lease_until=timezone.now()-timedelta(seconds=1))
                retried=statement_mail.claim()
                if retried is None or not statement_mail.capture(retried,mail_archive) or not statement_mail.complete(retried,mail_archive):
                    raise RuntimeError('synthetic statement recovery failed')
            if SyntheticStatementCapture.objects.filter(mail=mail).count()!=1:raise RuntimeError('synthetic statement duplicate capture')
            mail_status=client.get(support_url,HTTP_ACCEPT='application/json')
            if (mail_status.status_code!=200 or mail_status.json()['ledger']['statements'][0]['mail_capture']!='captured'
                    or mail_status.json()['ledger']['spent_seconds']!=1800 or mail_status.json()['ledger']['revision']!=5):
                raise RuntimeError('synthetic statement capture changed ledger')
            from shop.catalog.models import SyntheticSupportRefundCase,SyntheticSupportRefundStaffGrant
            refund_url=support_url+'refunds/'
            if client.get(refund_url).status_code!=200:raise RuntimeError('support refund owner form unavailable')
            refund_command={'request_id':str(uuid.uuid4()),'seconds':72000}
            refund_id=None
            for _ in range(2):
                requested=client.post(refund_url,data=json.dumps(refund_command),content_type='application/json',HTTP_X_CSRFTOKEN=csrf)
                if requested.status_code!=201 or (refund_id and requested.json()['case_id']!=refund_id):
                    raise RuntimeError('support refund request/retry mismatch')
                refund_id=requested.json()['case_id']
            refund_case=SyntheticSupportRefundCase.objects.get(identity=refund_id)
            refund_staff_url='/staff/support-refunds/'+refund_id+'/'
            with override_settings(**staff_settings,LOCAL_STAFF_CAPTURE_ROOT=capture):
                if staff.get(refund_staff_url).status_code!=404:raise RuntimeError('support refund assignment boundary failed')
                SyntheticSupportRefundStaffGrant.objects.create(user=staff_user,case=refund_case)
                refund_review={'request_id':str(uuid.uuid4()),'expected_revision':0,'ledger_revision':5,'decision':'ready_for_financial_review'}
                for _ in range(2):
                    reviewed=staff.post(refund_staff_url,data=json.dumps(refund_review),content_type='application/json',HTTP_X_CSRFTOKEN=staff_token)
                    if reviewed.status_code!=200 or reviewed.json()['case']['revision']!=1:raise RuntimeError('support refund review/retry failed')
                corrected=staff.post(refund_staff_url,data=json.dumps({'request_id':str(uuid.uuid4()),'expected_revision':1,
                    'ledger_revision':5,'decision':'needs_information'}),content_type='application/json',HTTP_X_CSRFTOKEN=staff_token)
                if corrected.status_code!=200 or corrected.json()['case']['revision']!=2:raise RuntimeError('support refund correction history failed')
            refund_state=client.get(refund_url+refund_id+'/',HTTP_ACCEPT='application/json')
            if (refund_state.status_code!=200 or not refund_state.json()['case']['consumed_support_present']
                    or not refund_state.json()['case']['request_exceeds_available'] or refund_state.json()['case']['refund_authorized']
                    or b'credential_generation' in refund_state.content):raise RuntimeError('support refund status/privacy mismatch')
            materials_url='/purchase/checkout-rehearsal/'+str(retained.pk)+'/packages/'
            listed=client.get(materials_url,HTTP_ACCEPT='application/json')
            if listed.status_code!=200 or len(listed.json()['packages'])!=3:raise RuntimeError('private package revision listing failed')
            old=next(item for item in listed.json()['packages'] if item['stage']=='initial' and item['version']==1)
            access_url=materials_url+old['id']+'/access/'
            download_url=materials_url+old['id']+'/download/'
            issued=client.post(access_url,data=json.dumps({'artifact':'sll-synthetic-rtl.txt'}),content_type='application/json',HTTP_X_CSRFTOKEN=csrf)
            if issued.status_code!=200:raise RuntimeError('private download grant failed')
            bearer=issued.json()['token']
            downloaded=client.post(download_url,data=json.dumps({'token':bearer}),content_type='application/json',HTTP_X_CSRFTOKEN=csrf)
            repeated=client.post(download_url,data=json.dumps({'token':bearer}),content_type='application/json',HTTP_X_CSRFTOKEN=csrf)
            if downloaded.status_code!=200 or b'synthetic-materials-v1' not in downloaded.content or repeated.status_code!=404:
                raise RuntimeError('private version-bound single-use download mismatch')
            waiting=client.post(access_url,data=json.dumps({'artifact':'sll-synthetic-rtl.txt'}),content_type='application/json',HTTP_X_CSRFTOKEN=csrf)
            if waiting.status_code!=200:raise RuntimeError('pre-hold download grant failed')
            old_grant=waiting.json()['token']
            with override_settings(**staff_settings,LOCAL_STAFF_CAPTURE_ROOT=capture):
                control_command={'request_id':str(uuid.uuid4()),'expected_revision':'0','action':'hold'}
                for _ in range(2):
                    held=staff.post(delivery_url+'control/',data=urlencode(control_command),content_type='application/x-www-form-urlencoded',HTTP_X_CSRFTOKEN=staff_token)
                    if held.status_code!=303:raise RuntimeError('delivery hold/retry failed')
            held_list=client.get(materials_url,HTTP_ACCEPT='application/json')
            if held_list.status_code!=200 or not all(item['delivery_held'] for item in held_list.json()['packages']):
                raise RuntimeError('held delivery owner status failed')
            if client.post(download_url,data=json.dumps({'token':old_grant}),content_type='application/json',HTTP_X_CSRFTOKEN=csrf).status_code!=423:
                raise RuntimeError('delivery hold allowed download')
            if client.post(access_url,data=json.dumps({'artifact':'sll-synthetic-rtl.txt'}),content_type='application/json',HTTP_X_CSRFTOKEN=csrf).status_code!=423:
                raise RuntimeError('delivery hold allowed grant')
            with override_settings(**staff_settings,LOCAL_STAFF_CAPTURE_ROOT=capture):
                cleared=staff.post(delivery_url+'control/',data=urlencode({'request_id':str(uuid.uuid4()),'expected_revision':'1','action':'clear'}),content_type='application/x-www-form-urlencoded',HTTP_X_CSRFTOKEN=staff_token)
                if cleared.status_code!=303:raise RuntimeError('delivery hold clear failed')
            if client.post(download_url,data=json.dumps({'token':old_grant}),content_type='application/json',HTTP_X_CSRFTOKEN=csrf).status_code!=404:
                raise RuntimeError('cleared hold resurrected old grant')
            refreshed=client.post(access_url,data=json.dumps({'artifact':'sll-synthetic-rtl.txt'}),content_type='application/json',HTTP_X_CSRFTOKEN=csrf)
            if refreshed.status_code!=200 or client.post(download_url,data=json.dumps({'token':refreshed.json()['token']}),content_type='application/json',HTTP_X_CSRFTOKEN=csrf).status_code!=200:
                raise RuntimeError('fresh post-hold download failed')
            owner_case=client.get('/purchase/checkout-rehearsal/'+str(retained.pk)+'/changes/'+case_ids[0]+'/',HTTP_ACCEPT='application/json')
            if owner_case.status_code!=200 or not owner_case.json()['proposal']['active'] or b'credential_generation' in owner_case.content:
                raise RuntimeError('owner licence case status/privacy mismatch')
            if SyntheticBankOperation.objects.count()!=case_bank_count or SyntheticLineEntitlement.objects.filter(fulfilment=grant).count()!=1:
                raise RuntimeError('licence cases duplicated money or original entitlement')
            # Independently dispatched fixture capture, never another customer pay/retry path.
            from shop.payments import attempts as payment_attempts
            from shop.payments.bank_contract import BankStart
            from shop.payments.models import SyntheticOverpaymentStaffGrant,SyntheticOverpaymentCase,SyntheticOverpaymentReview
            from shop.catalog.models import SyntheticCheckoutAcceptance
            accepted_cart=SyntheticCheckoutAcceptance.objects.get(checkout=retained)
            extra_capture=payment_attempts.prepare(BankStart('synthetic-checkout',uuid.uuid4(),uuid.uuid4(),
                accepted_cart.attempt.currency,accepted_cart.attempt.amount_minor))
            with PreparedArchive(Path(archive_root)) as finance_archive:
                payment_attempts.dispatch(extra_capture.pk,finance_archive)
            finance_scope=SyntheticOverpaymentStaffGrant.objects.create(user=staff_user,acceptance=accepted_cart,extra_attempt=extra_capture)
            finance_url='/staff/overpayments/'+str(finance_scope.pk)+'/'
            with override_settings(**staff_settings,LOCAL_STAFF_CAPTURE_ROOT=capture):
                if staff.get('/staff/overpayments/').status_code!=200:raise RuntimeError('overpayment assignment list unavailable')
                finance_command={'action':'capture'}
                for _ in range(2):
                    response=staff.post(finance_url,data=json.dumps(finance_command),content_type='application/json',HTTP_X_CSRFTOKEN=staff_token)
                    if response.status_code!=200 or response.json()['case']['capture_count']!=2:raise RuntimeError('overpayment capture/retry failed')
                finance_command={'action':'review','request_id':str(uuid.uuid4()),'expected_revision':0,'decision':'ready_for_financial_review'}
                for _ in range(2):
                    response=staff.post(finance_url,data=json.dumps(finance_command),content_type='application/json',HTTP_X_CSRFTOKEN=staff_token)
                    if response.status_code!=200 or response.json()['case']['revision']!=1:raise RuntimeError('overpayment review/retry failed')
                if response.json()['case']['refund_authorized']:raise RuntimeError('overpayment authorized a refund')
            if (SyntheticBankOperation.objects.count()!=case_bank_count+1
                    or SyntheticOverpaymentCase.objects.filter(acceptance=accepted_cart).count()!=1
                    or SyntheticOverpaymentReview.objects.filter(case__acceptance=accepted_cart).count()!=1
                    or SyntheticLineEntitlement.objects.filter(fulfilment=grant).count()!=1):raise RuntimeError('overpayment duplicated financial review or entitlement')
            from shop.payments.models import SyntheticPaymentObservation
            if (SyntheticPaymentObservation.objects.filter(attempt=accepted_cart.attempt).count()!=1
                    or SyntheticPaymentObservation.objects.filter(attempt=extra_capture).count()!=1):
                raise RuntimeError('normalized payment observations missing or duplicated')
            final=client.get(support_url,HTTP_ACCEPT='application/json').json()['ledger']
            if (final['spent_seconds']!=1800 or final['available_seconds']!=70200
                    or len(final['statements'])!=1 or final['statements'][0]['statement']['revision']!=4
                    or final['actual_support_spendable'] is not False):
                raise RuntimeError('synthetic committed ledger statement mismatch')
        with override_settings(LOCAL_CHECKOUT_ARCHIVE_ROOT=str(archive_root)):
            # Optional later context stays with this existing private support purchase.
            scope_digest=checkout_payment.accepted(owner,retained.pk).sha256
            first_context={'action':'context','request_id':str(uuid.uuid4()),
                           'fixture':'synthetic-context-v1','expected_revision':0}
            for value in (first_context,first_context|{'request_id':str(uuid.uuid4()),
                          'fixture':'synthetic-context-v2','expected_revision':1},first_context):
                response=client.post(support_url,data=json.dumps(value),content_type='application/json',HTTP_X_CSRFTOKEN=csrf)
                if response.status_code!=200:raise RuntimeError('private synthetic context/retry failed')
            if response.json()['followup']['revision']!=2 or response.json()['ledger']!=final:
                raise RuntimeError('private context changed support accounting')
            with override_settings(**staff_settings):
                staff_context=staff.get(staff_url,HTTP_ACCEPT='application/json')
                if staff_context.status_code!=200 or staff_context.json()['followup']!=response.json()['followup']:
                    raise RuntimeError('assigned staff private context read failed')
            if checkout_payment.accepted(owner,retained.pk).sha256!=scope_digest:
                raise RuntimeError('private context changed accepted scope')
        with override_settings(LOCAL_CHECKOUT_ARCHIVE_ROOT=str(archive_root)):
            from .finance_demo_scenario import run as run_finance
            finance_result=run_finance(staff,staff_token,staff_name,staff_settings,archive)
        complete_cart={'all_lines_retained':True,'business_revision':retained.snapshot['business']['version'],
            'document_revision':retained.snapshot['documents']['revision'],'archive_recovered':bool(retained.archive_receipt),
            'api_and_no_javascript_same_capture':True,'acceptance_enabled':False,
            'synthetic_acceptance_recorded':True,'simulated_payment_captured':True,'canonical_customer_payment_once':True,'cart_entitlement_once':True,
            'cart_staged_delivery_preserves_later_obligation':True,'cart_support_seconds_once':72000,'actual_support_spendable':False,
            'notification_lookup':{'uncertain_payment_recovered':True,'duplicate_hint_once':True,
                'blind_payment_retry':False,'public_callbacks_enabled':False},
            'support_ledger':{'revision':final['revision'],'reserved_seconds':final['reserved_seconds'],
                'spent_seconds':final['spent_seconds'],'available_seconds':final['available_seconds'],
                'statement_committed_revision':final['statements'][0]['statement']['revision'],
                'local_staff_two_factors_and_exact_grant':True,'reverse_replace_history_preserved':True,
                'statement_mail_capture_once_after_lost_response':True,'actual_email_sent':False},
            'normalized_observations':{'canonical_receipt_once':True,'extra_capture_receipt_once':True,'actual_financial_confirmation':False},
            'overpayment_review':{'independent_fixture_capture':True,'two_observations_retained':True,
                'exact_pair_assignment':True,'case_and_review_retry_once':True,'additional_fulfilment':False,'actual_refund':False},
            'support_refund_review':{'consumed_credit_retained':True,'separate_case_assignment':True,
                'request_and_review_retries_once':True,'correction_history_preserved':True,'actual_refund':False},
            'private_support_followup':{'versions':2,'accepted_scope_unchanged':True,'support_ledger_unchanged':True,'actual_technical_intake':False},
            'private_packages':{'retained_versions':3,'old_version_downloaded_once':True,'bearer_in_url':False,'actual_delivery':False,
                'delivery_hold_blocks_access':True,'clear_does_not_revive_old_grant':True},
            'licence_change_cases':{'kinds_captured_and_reviewed':5,'higher_volume_requires_quote':True,
                'corrected_review_supersedes_prior_proposal':True,'original_entitlement_unchanged':True,'automatic_charge':False}}

    # Source section8 numbers are distinct from the broader FLOW requirement IDs.
    source_checks=[{'source_check':number,'status':'synthetic_pass','evidence_class':'local-synthetic'}
                   for number in range(1,8)]
    source_checks.append({'source_check':8,'status':'partial','evidence_class':'local-synthetic',
        'remaining':'Qualified confidential customer technical-data intake and actual accepted-scope custody remain pending; private synthetic seller materials/history exercised.'})
    return {'source_acceptance_checks':source_checks,'status':'PURCHASE_FLOW_DEMO_PASS','evidence_class':'local-synthetic','financial_confirmation':False,
        'effects_authorized':False,'real_email_verification':False,'ready_kit_zero_support':True,'required_support_tamper_refused':True,
        'staff_finance_lifecycle':finance_result,'complete_cart_checkout':complete_cart,'topup_without_platform_or_new_licence':True,'reservation_retry_once':True,'development_cases':results,
        'pending':['actual commercial/kit/rights/support/terms approvals','actual order acceptance and entitlement/ledger delivery','qualified private technical follow-up','external bank/mail/host/recovery qualification']}
