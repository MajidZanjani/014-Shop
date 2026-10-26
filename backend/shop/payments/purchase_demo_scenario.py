"""Synthetic example executed only by the fresh-owned-database demo wrapper."""
from pathlib import Path
import json,uuid
from django.contrib.auth import get_user_model
from django.test import Client
from django.utils import timezone
from shop.access.models import CustomerIdentity
from shop.adapters.evidence_archive import PreparedArchive
from shop.catalog.rules import CATALOG
from shop.catalog.purchase_policy import quote
from shop.catalog import business_rules, checkout
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
        complete_cart={'all_lines_retained':True,'business_revision':retained.snapshot['business']['version'],
            'document_revision':retained.snapshot['documents']['revision'],'archive_recovered':bool(retained.archive_receipt),
            'api_and_no_javascript_same_capture':True,'acceptance_enabled':False}

    return {'status':'PURCHASE_FLOW_DEMO_PASS','evidence_class':'local-synthetic','financial_confirmation':False,
        'effects_authorized':False,'real_email_verification':False,'ready_kit_zero_support':True,'required_support_tamper_refused':True,
        'complete_cart_checkout':complete_cart,'topup_without_platform_or_new_licence':True,'reservation_retry_once':True,'development_cases':results,
        'pending':['actual commercial/kit/rights/support/terms approvals','actual order acceptance and entitlement/ledger delivery','qualified private technical follow-up','external bank/mail/host/recovery qualification']}
