#!/usr/bin/env python3
"""Owned loopback SHB demonstration; fake-only, no real bank/mail/time effects."""
import argparse
from contextlib import ExitStack
import hashlib
import http.cookiejar
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

ROOT=Path(__file__).resolve().parents[1]
sys.dont_write_bytecode=True
from check_worker import prepared_database,manage
from check_backend import gunicorn


def require(value):
    if not value:raise ValueError('SHB demonstration check failed')


def fixture(python,env,capture,*,prepare_offers=False):
    # The bearer exists only in this owned private capture and memory. Never
    # print it, put it in argv or promote this fixture into real eligibility.
    child=dict(env,SHOP_SHB_FIXTURE_CAPTURE=str(capture),SHOP_SHB_PREPARE_OFFERS='1' if prepare_offers else '0')
    manage(python,child,'shell','-c','''
import json,os,re,uuid
from pathlib import Path
from django.conf import settings
from django.test import Client,override_settings
from django.contrib.auth import get_user_model
from shop.shb.invitations import issue_fixture
from shop.shb.discounts import issue_fixture as issue_discount
customer=get_user_model().objects.create_user(username='shb-demo-customer')
issuer=get_user_model().objects.create_user(username='shb-demo-issuer',password='synthetic-demo-staff-only',is_staff=True)
row,token=issue_fixture(customer=customer,issuer=issuer,company_name='Synthetic Company Limited',project_reference='SLL synthetic project')
prepare=os.environ['SHOP_SHB_PREPARE_OFFERS']=='1'
discount,code=issue_discount(customer=customer,issuer=issuer,percentage_bps=1000,fpga_allowed=True,asic_allowed=True,use_limit=6 if prepare else 2)
offer_ids=[]
if prepare:
    # Seed reviewed offers through the actual protected native request and
    # password/possession-code/MFA staff routes. No credential/session fabrication.
    from shop.shb.models import SupportRequest
    from shop.access.models import StaffCredential,StaffQuotationGrant
    from shop.config import staff_synthetic
    browser=Client(enforce_csrf_checks=True,HTTP_HOST='localhost')
    assert browser.get('/invite/'+token,secure=True).status_code==302
    requests=[]
    for _ in range(4):
        assert browser.get('/purchase/simple/',secure=True).status_code==200
        data={'variant':'shb-asic-25h','quantity':'2','company_name':'Synthetic Company Limited',
            'billing_address':'1 Synthetic Test Street','country':'GE','company_phone':'+995 555 010101',
            'contact_name':'Synthetic Customer','same_phone':'on','contact_email':'buyer@synthetic.invalid',
            'assistance':'Review SLL IP integration','privacy_acknowledged':'on','discount_code':code,
            'action':'submit','request_id':str(uuid.uuid4()),'csrfmiddlewaretoken':browser.cookies[settings.CSRF_COOKIE_NAME].value}
        assert browser.post('/purchase/simple/',data,secure=True,HTTP_ORIGIN='https://localhost').status_code==200
        requests.append(SupportRequest.objects.get(request_id=data['request_id']))
    capture_root=Path(settings.LOCAL_CHECKOUT_ARCHIVE_ROOT).parent/'staff-codes';capture_root.mkdir(mode=0o700)
    names=('ROOT_URLCONF','LOCAL_STAFF_ENABLED','ALLOWED_HOSTS','SESSION_COOKIE_NAME','CSRF_COOKIE_NAME','SESSION_COOKIE_AGE','MIDDLEWARE','TEMPLATES')
    options={name:getattr(staff_synthetic,name) for name in names}
    StaffCredential.objects.create(user=issuer)
    with override_settings(**options,LOCAL_STAFF_CAPTURE_ROOT=str(capture_root)):
        staff=Client(enforce_csrf_checks=True,HTTP_HOST='staff.localhost')
        def post(path,data):
            csrf=staff.get('/staff/session/').json()['csrf_token']
            return staff.post('/staff/'+path,data=json.dumps(data),content_type='application/json',HTTP_X_CSRFTOKEN=csrf)
        assert post('login/',{'username':issuer.username,'password':'synthetic-demo-staff-only'}).status_code==200
        captures=list(capture_root.iterdir());assert len(captures)==1
        possession=re.search(r'^Code: (.+)$',captures[0].read_text(),re.M)[1]
        assert post('verify/',{'code':possession}).status_code==200
        for request in requests:
            StaffQuotationGrant.objects.create(user=issuer,quotation=request.quotation,business_scope_version=request.revision)
            route='quotation-requests/'+str(request.quotation_id)+'/'
            assert post(route+'shb-reviews/',{'request_id':str(uuid.uuid4()),'expected_review_version':0,
                'scope_sha256':request.sha256,'decision':'ready_for_commercial_review','message':'Synthetic SLL IP feasibility reviewed.'}).status_code==201
            offer=post(route+'shb-offers/',{'request_id':str(uuid.uuid4()),'expected_review_version':1,
                'scope_sha256':request.sha256,'prerequisites':'Authorized customer tool access arranged separately.',
                'exclusions':'No tape-out, sign-off or outcome guarantee.'})
            assert offer.status_code==201
            offer_ids.append(offer.json()['id'])
fd=os.open(os.environ['SHOP_SHB_FIXTURE_CAPTURE'],os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
with os.fdopen(fd,'w') as stream:json.dump({'invitation_id':str(row.pk),'token':token,'discount_code':code,'offer_ids':offer_ids},stream)
''')



def staff_fixture(python,env,capture):
    """Assign exact existing synthetic purchases; retain pre-refund facts privately."""
    manage(python,dict(env,SHOP_SHB_FIXTURE_CAPTURE=str(capture)),'shell','-c','''import json,os
from pathlib import Path
from django.contrib.auth import get_user_model
from shop.shb.models import PaidOrder,PaidOrderGrant,DiscountReservation,PurchaseNoticeCapture,TransactionNotice
from shop.payments.models import SyntheticPaymentStaffGrant
path=Path(os.environ['SHOP_SHB_FIXTURE_CAPTURE']);value=json.loads(path.read_text())
user=get_user_model().objects.get(username='shb-demo-issuer')
orders=list(PaidOrder.objects.select_related('acceptance').order_by('pk'));assert len(orders)==4
asic=[row for row in orders if row.payload['purchase']['variant_id']=='shb-asic-25h']
fpga=[row for row in orders if row.payload['purchase']['variant_id']=='shb-fpga-10h'];assert len(asic)==len(fpga)==2
value['staff_orders']=[]
for order in asic:
    PaidOrderGrant.objects.create(user=user,order=order)
    finance=SyntheticPaymentStaffGrant.objects.create(user=user,acceptance=order.acceptance,kind='refund')
    value['staff_orders'].append({'path':'/staff/shb-orders/'+str(order.pk)+'/',
        'reference':order.payload['order_reference'],'financePath':'/staff/payments/'+str(finance.pk)+'/'})
PaidOrderGrant.objects.create(user=user,order=fpga[0])
value['no_finance_path']='/staff/shb-orders/'+str(fpga[0].pk)+'/'
value['unassigned_path']='/staff/shb-orders/'+str(fpga[1].pk)+'/'
from shop.shb.invitations import issue_fixture
from shop.shb.models import Invitation,InvitationStaffGrant
from shop.shb.invitation_issuance import register_fixture
from shop.shb.models import InvitationIssueGrant
customer=Invitation.objects.get(pk=value['invitation_id']).customer
scope=register_fixture(customer=customer,registered_by=user,company_name='Synthetic Company Limited',
    project_reference='SLL synthetic revocation fixture',eligibility_reference='synthetic-eligibility-v1',
    fpga_eligible=True,asic_allowed=True)
InvitationIssueGrant.objects.create(user=user,scope=scope)
value['issuance_path']='/staff/shb-invitation-scopes/'+str(scope.pk)+'/'
from shop.shb.discount_issuance import register_fixture as register_discount_scope
from shop.shb.models import DiscountIssueGrant
discount_scope=register_discount_scope(customer=customer,registered_by=user,percentage_bps=1500,asic_allowed=True,use_limit=2,claim_period_days=30)
DiscountIssueGrant.objects.create(user=user,scope=discount_scope)
value['discount_issuance_path']='/staff/shb-discount-scopes/'+str(discount_scope.pk)+'/'
from shop.shb.discounts import issue_fixture as issue_discount
from shop.shb.models import DiscountStaffGrant
value['staff_discounts']=[]
for _ in range(2):
    discount,_=issue_discount(customer=customer,issuer=user,percentage_bps=1500,fpga_allowed=True,asic_allowed=True)
    DiscountStaffGrant.objects.create(user=user,discount=discount)
    value['staff_discounts'].append({'id':str(discount.pk),'path':'/staff/shb-discounts/'+str(discount.pk)+'/',
        'expiresAt':discount.expires_at.isoformat()})
value['staff_invitations']=[]
for _ in range(2):
    invite,token=issue_fixture(customer=customer,issuer=user,company_name='Synthetic Company Limited',project_reference='SLL synthetic revocation fixture')
    InvitationStaffGrant.objects.create(user=user,invitation=invite)
    value['staff_invitations'].append({'id':str(invite.pk),'token':token,
        'path':'/staff/shb-invitations/'+str(invite.pk)+'/','expiresAt':invite.expires_at.isoformat()})
value['original_orders']={str(row.pk):{'payload':row.payload,'sha256':row.sha256} for row in orders}
value['original_reservations']={str(row.pk):{'state':row.state,'order':str(row.consumed_order_id)} for row in DiscountReservation.objects.all()}
value['original_captures']={str(row.pk):{'payload':row.payload,'sha256':row.sha256} for row in PurchaseNoticeCapture.objects.all()}
value['original_notices']={str(row.pk):{'payload':row.payload,'sha256':row.sha256} for row in TransactionNotice.objects.all()}
path.write_text(json.dumps(value))
''')
    return json.loads(capture.read_text())


def verify_staff_refunds(python,env,capture):
    manage(python,dict(env,SHOP_SHB_FIXTURE_CAPTURE=str(capture)),'shell','-c','''import json,os
from pathlib import Path
from django.conf import settings
from shop.adapters.evidence_archive import PreparedArchive
from shop.shb.models import PaidOrder,DiscountReservation,PurchaseNoticeCapture,TransactionNotice,RefundReview,RefundSupportHandoff
from shop.shb import refunds
from shop.payments.models import SyntheticPaymentOperation,SyntheticOperationResult,SyntheticBankTransition,SyntheticBankOperation
from shop.catalog.models import SyntheticFulfilment,SyntheticSupportEvent
value=json.loads(Path(os.environ['SHOP_SHB_FIXTURE_CAPTURE']).read_text())
assert {str(row.pk):{'payload':row.payload,'sha256':row.sha256} for row in PaidOrder.objects.all()}==value['original_orders']
assert {str(row.pk):{'state':row.state,'order':str(row.consumed_order_id)} for row in DiscountReservation.objects.all()}==value['original_reservations']
assert {str(row.pk):{'payload':row.payload,'sha256':row.sha256} for row in PurchaseNoticeCapture.objects.all()}==value['original_captures']
assert {str(row.pk):{'payload':row.payload,'sha256':row.sha256} for row in TransactionNotice.objects.all()}==value['original_notices']
assert SyntheticBankOperation.objects.count()==4
assert SyntheticPaymentOperation.objects.count()==SyntheticOperationResult.objects.count()==SyntheticBankTransition.objects.count()==2
assert RefundReview.objects.count()==RefundSupportHandoff.objects.count()==2
with PreparedArchive(Path(settings.LOCAL_CHECKOUT_ARCHIVE_ROOT)) as archive:
    for handoff in RefundSupportHandoff.objects.select_related('review__order__acceptance','result'):
        review=handoff.review;refunds.retained_review(review,review.order.acceptance,archive)
        refunds.retained_handoff(handoff,review,handoff.result,archive)
        assert not review.payload['actual_financial_authority'] and not handoff.payload['actual_email_sent']
        assert all(item is None for item in review.payload['financial_policy'].values())
        assert handoff.result.operation.acceptance_id==review.order.acceptance_id
        assert review.order.acceptance.attempt.provider_status=='refunded'
        assert review.payload['actor']['staff_id']==handoff.payload['actor']['staff_id']
    from shop.shb.models import Invitation,InvitationRevocation,InvitationIssue
    from shop.shb import invitation_admin,invitation_issuance,discount_admin
    from shop.shb.models import DiscountRevocation
    assert InvitationRevocation.objects.count()==2
    assert InvitationIssue.objects.count()==2
    assert Invitation.objects.get(pk=value['invitation_id']).revoked_at is None
    for item in value['staff_invitations']:
        event=InvitationRevocation.objects.select_related('invitation').get(invitation_id=item['id'])
        invitation_admin.retained(event,archive)
        assert event.invitation.expires_at.isoformat()==item['expiresAt']
        assert not event.payload['actual_invitation_authority'] and not event.payload['actual_email_sent']
        issued=InvitationIssue.objects.select_related('scope','replaces','invitation').get(replaces_id=item['id'])
        invitation_issuance.retained(issued,archive)
        assert issued.invitation_id==issued.pk and issued.invitation_id!=issued.replaces_id
        assert issued.invitation.expires_at>event.invitation.expires_at
        assert not issued.payload['actual_invitation_authority'] and not issued.payload['actual_email_sent']
    assert DiscountRevocation.objects.count()==2
    for item in value['staff_discounts']:
        event=DiscountRevocation.objects.select_related('discount').get(discount_id=item['id'])
        discount_admin.retained(event,archive)
        assert event.discount.expires_at.isoformat()==item['expiresAt']
        assert not event.payload['actual_discount_authority'] and not event.payload['actual_email_sent']
assert not SyntheticFulfilment.objects.exists() and not SyntheticSupportEvent.objects.exists()
print('SHB_STAFF_REFUNDS 2 archived=true original_orders_coupons_notices=unchanged actual_money_email=false')
''')


def request(opener,url,*,data=None,origin=None):
    headers={'Origin':origin} if origin else {}
    raw=urllib.parse.urlencode(data).encode() if data is not None else None
    if raw is not None:headers['Content-Type']='application/x-www-form-urlencoded'
    try:response=opener.open(urllib.request.Request(url,data=raw,headers=headers),timeout=5)
    except urllib.error.HTTPError as error:response=error
    with response:
        raw=response.read(262145);require(len(raw)<=262144)
        return response.status,raw,response.headers,response.geturl()


def common_data(**changes):
    value={'variant':'shb-fpga-10h','quantity':'3','company_name':'Synthetic Company Limited',
        'billing_address':'1 Synthetic Test Street','country':'GE','company_phone':'+995 555 010101',
        'contact_name':'Synthetic Customer','same_phone':'on','contact_email':'buyer@synthetic.invalid',
        'privacy_acknowledged':'on','request_id':str(uuid.uuid4()),'action':'review'}
    value.update(changes);return value


def checks(base,credential,python,env):
    jar=http.cookiejar.CookieJar();opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),urllib.request.HTTPCookieProcessor(jar))
    count=0
    for path in ('/','/shop/','/api/v1/catalog/','/shop/private/index.html'):
        code,body,headers,_=request(opener,base+path);require(code==403 and b'FPGA Supporting Hours Bundle' not in body);count+=1
    code,body,headers,url=request(opener,base+'/invite/'+credential['token'])
    require(code==200 and urllib.parse.urlsplit(url).path=='/shop/' and headers['Cache-Control']=='no-store');count+=1
    require(headers['Referrer-Policy']=='no-referrer');count+=1
    code,body,_,_=request(opener,base+'/api/v1/catalog/')
    require(code==200 and json.loads(body)['title']=='Supporting Hours Bundle');count+=1
    code,body,headers,_=request(opener,base+'/purchase/simple/')
    require(code==200 and b'Same as company phone' in body and b'name="assistance"' not in body);count+=1
    csrf=re.search(rb'name="csrfmiddlewaretoken" value="([^"]+)"',body).group(1).decode()
    code,body,_,_=request(opener,base+'/purchase/simple/',data=common_data(csrfmiddlewaretoken=csrf),origin=base)
    require(code==200 and b'30 hours in this order' in body and b'EUR 3,000.00' in body);count+=1
    data=common_data(variant='shb-asic-25h',quantity='2',assistance='Review SLL IP integration',action='apply_discount',discount_code=credential['discount_code'],csrfmiddlewaretoken=csrf)
    code,body,_,_=request(opener,base+'/purchase/simple/',data=data,origin=base)
    require(code==200 and b'Discount applied' in body and b'EUR 9,000.00' in body);count+=1
    data['action']='submit'
    code,body,_,_=request(opener,base+'/purchase/simple/',data=data,origin=base)
    require(code==200 and b'50 requested hours' in body);count+=1
    code,body,_,_=request(opener,base+'/purchase/simple/',data=data,origin=base)
    require(code==200 and b'50 requested hours' in body);count+=1
    result=manage(python,env,'shell','-c',"from shop.shb.models import SupportRequest,DiscountReservation; from shop.payments.models import SyntheticPaymentAttempt; from shop.catalog.models import SyntheticFulfilment; print('SHB_COUNTS',SupportRequest.objects.count(),SyntheticPaymentAttempt.objects.count(),SyntheticFulfilment.objects.count(),DiscountReservation.objects.count())")
    require('SHB_COUNTS 1 0 0 1' in result.stdout);count+=1
    for path in ('/api/v1/cart/','/api/v1/configurations/validate/','/purchase/checkout-rehearsal/'):
        code,_,_,_=request(opener,base+path,data={'product_id':'sll-xspi-mc'},origin=base);require(code==404);count+=1
    manage(python,env,'shell','-c',"from django.utils import timezone; from shop.shb.models import Invitation; Invitation.objects.filter(pk='"+credential['invitation_id']+"').update(revoked_at=timezone.now())")
    code,_,_,_=request(opener,base+'/shop/');require(code==403);count+=1
    return count


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group(required=True);mode.add_argument('--check',action='store_true');mode.add_argument('--serve',action='store_true')
    parser.add_argument('--release',type=Path,help='Previously built private Astro release directory')
    parser.add_argument('--browser',action='store_true',help='Run actual pinned Chromium in JavaScript and no-JavaScript modes')
    parser.add_argument('--screenshot-root',type=Path,help='Fresh owned .scratch directory for private empty-form screenshots')
    args=parser.parse_args()
    with ExitStack() as stack:
        scratch=Path(stack.enter_context(tempfile.TemporaryDirectory(prefix='shb-demo-',dir=ROOT/'.scratch')))
        os.chmod(scratch,0o700)
        python,env,pg,database,backend_scratch=stack.enter_context(prepared_database())
        archive=scratch/'archive';archive.mkdir(mode=0o700)
        env=dict(env,DJANGO_SETTINGS_MODULE='shop.config.shb_synthetic',SHOP_LOCAL_CHECKOUT_ARCHIVE_ROOT=str(archive))
        if args.release:
            sys.path.insert(0,str(ROOT/'backend'))
            from shop.shb.private_release import MANIFEST,read_asset,ENTRY
            release=args.release.resolve();digest=hashlib.sha256((release/MANIFEST).read_bytes()).hexdigest()
            read_asset(release,digest,ENTRY)
            env.update(SHOP_SHB_PRIVATE_RELEASE_ROOT=str(release),SHOP_SHB_PRIVATE_RELEASE_SHA256=digest)
        manage(python,env,'migrate','--noinput')
        capture=scratch/'invitation.json';fixture(python,env,capture,prepare_offers=args.browser)
        credential=json.loads(capture.read_text())
        port=stack.enter_context(gunicorn(python,env,backend_scratch));base='http://127.0.0.1:'+str(port)
        if args.check:
            if args.browser:
                require(args.release is not None)
                evidence=args.screenshot_root.resolve() if args.screenshot_root else None
                if evidence:require(evidence.is_relative_to((ROOT/'.scratch').resolve()) and evidence.is_dir() and not evidence.is_symlink() and not any(evidence.iterdir()))
                browser_env={key:os.environ[key] for key in ('PATH','LANG','HOME','TMPDIR','SHOP_NODE','SHOP_BROWSER','SHOP_BROWSER_NODE_VERSION','SHOP_BROWSER_VERSION') if key in os.environ}
                # Chromium creates a Unix SingletonSocket below TMPDIR. The Nix
                # shell's workspace path can exceed its 108-byte system limit.
                # This private directory belongs only to this browser run.
                browser_tmp=stack.enter_context(tempfile.TemporaryDirectory(prefix='shb-browser-',dir='/tmp'))
                browser_env['TMPDIR']=browser_tmp
                config={'origin':base,'invitationUrl':base+'/invite/'+credential['token'],'discountCode':credential['discount_code'],'offerIds':credential['offer_ids'],'scratch':str(scratch),'evidence':str(evidence) if evidence else None}
                result=subprocess.run([browser_env['SHOP_NODE'],str(ROOT/'scripts/browser_shb.mjs')],input=json.dumps(config),text=True,capture_output=True,env=browser_env,timeout=120,check=True)
                report=json.loads(result.stdout)
                require(report['status']=='SHB_BROWSER_PASS' and report['checks']>=20 and report['modes']==2)
                retained=manage(python,env,'shell','-c',"from shop.shb.models import SupportRequest,DiscountReservation; from shop.payments.models import SyntheticPaymentAttempt; from shop.catalog.models import SyntheticFulfilment; print('SHB_COUNTS',SupportRequest.objects.count(),SyntheticPaymentAttempt.objects.count(),SyntheticFulfilment.objects.count(),DiscountReservation.objects.count())")
                require('SHB_COUNTS 8 4 0 6' in retained.stdout)
                final=manage(python,env,'shell','-c',"from shop.shb.models import SupportCheckout; from shop.catalog.models import SyntheticCheckoutAcceptance; from shop.payments.models import SyntheticBankOperation; print('SHB_CHECKOUTS',SupportCheckout.objects.count(),SyntheticCheckoutAcceptance.objects.count(),SyntheticBankOperation.objects.count())")
                require('SHB_CHECKOUTS 6 6 4' in final.stdout)
                closed=manage(python,env,'shell','-c',"from shop.shb.models import CheckoutClosure; print('SHB_CLOSED',CheckoutClosure.objects.filter(applied_at__isnull=False).count())")
                require('SHB_CLOSED 2' in closed.stdout)
                withdrawn=manage(python,env,'shell','-c',"from shop.shb.models import RequestClosure,DiscountReservation; print('SHB_WITHDRAWN',RequestClosure.objects.filter(applied_at__isnull=False,payload__action='withdraw').count(),DiscountReservation.objects.filter(release_lifecycle__isnull=False,state='released').count())")
                require('SHB_WITHDRAWN 2 2' in withdrawn.stdout)
                revisions=manage(python,env,'shell','-c',"from shop.shb.models import RequestReplacement; rows=list(RequestReplacement.objects.select_related('request','previous')); assert len(rows)==2; assert all(row.request.revision==2 and row.previous.state=='withdrawn' and row.request.state=='submitted' and row.request.payload['purchase']['hours_purchased']==75 for row in rows); print('SHB_REVISIONS 2 fresh_unpaid=true')")
                require('SHB_REVISIONS 2 fresh_unpaid=true' in revisions.stdout)
                paid=manage(python,env,'shell','-c',"from shop.shb.models import PaidOrder,PurchaseNoticeDelivery; print('SHB_PAID',PaidOrder.objects.count(),PurchaseNoticeDelivery.objects.filter(state='pending').count())")
                require('SHB_PAID 4 4' in paid.stdout)
                for _ in range(4):manage(python,env,'run_worker','--once')
                notices=manage(python,env,'shell','-c',"from shop.shb.models import PurchaseNoticeCapture,PurchaseNoticeDelivery; print('SHB_NOTICES',PurchaseNoticeCapture.objects.count(),PurchaseNoticeDelivery.objects.filter(state='captured').count())")
                require('SHB_NOTICES 4 4' in notices.stdout)
                ordinary=manage(python,env,'shell','-c',"from shop.worker.services import execute_once; from shop.shb.models import TransactionNotice,TransactionNoticeDelivery,TransactionNoticeCapture; from collections import Counter; [execute_once() for _ in range(24)]; counts=Counter(TransactionNotice.objects.values_list('event',flat=True)); assert dict(counts)=={'request-received':8,'offer-issued':4,'request-closed':2,'checkout-closed':2,'purchase-confirmed':4}; assert TransactionNoticeDelivery.objects.exclude(state='captured').count()==0; assert TransactionNoticeCapture.objects.count()==20; assert not any(row.payload['actual_email_sent'] for row in TransactionNotice.objects.all()); print('SHB_ORDINARY_NOTICES 20 captured=true actual_email_sent=false')")
                require('SHB_ORDINARY_NOTICES 20 captured=true actual_email_sent=false' in ordinary.stdout)
                credential=staff_fixture(python,env,capture)
                staff_codes=scratch/'browser-staff-codes';staff_codes.mkdir(mode=0o700)
                staff_runtime=scratch/'staff-runtime';staff_runtime.mkdir(mode=0o700)
                # Keep staff-only routes and cookies in their existing separate app.
                (staff_runtime/'shb_browser_staff.py').write_text('from shop.config.staff_synthetic import *\nSHB_SYNTHETIC_FIXTURE=True\n')
                staff_env=dict(env,DJANGO_SETTINGS_MODULE='shb_browser_staff',
                    PYTHONPATH=str(staff_runtime)+os.pathsep+env.get('PYTHONPATH',str(ROOT/'backend')),
                    SHOP_LOCAL_STAFF_CAPTURE_ROOT=str(staff_codes))
                staff_port=stack.enter_context(gunicorn(python,staff_env,staff_runtime,probe_path='/staff/session/',probe_host='staff.localhost'))
                staff_base='http://staff.localhost:'+str(staff_port)
                invitation_sessions=[]
                for item in credential['staff_invitations']:
                    jar=http.cookiejar.CookieJar()
                    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),urllib.request.HTTPCookieProcessor(jar))
                    status,_,_,_=request(opener,base+'/invite/'+item['token']);require(status==200)
                    invitation_sessions.append(opener)
                staff_config={'origin':staff_base,'scratch':str(scratch),'evidence':str(evidence) if evidence else None,
                    'staff':{'username':'shb-demo-issuer','password':'synthetic-demo-staff-only',
                        'captureRoot':str(staff_codes),'orders':credential['staff_orders'],
                        'noFinancePath':credential['no_finance_path'],'unassignedPath':credential['unassigned_path'],
                        'issuancePath':credential['issuance_path'],
                        'discountIssuancePath':credential['discount_issuance_path'],
                        'discounts':[{key:item[key] for key in ('path','expiresAt')} for item in credential['staff_discounts']],
                        'invitations':[{key:item[key] for key in ('path','expiresAt')} for item in credential['staff_invitations']]}}
                result=subprocess.run([browser_env['SHOP_NODE'],str(ROOT/'scripts/browser_shb.mjs')],input=json.dumps(staff_config),
                    text=True,capture_output=True,env=browser_env,timeout=120,check=True)
                staff_report=json.loads(result.stdout)
                require(staff_report['status']=='SHB_BROWSER_PASS' and staff_report['modes']==2 and staff_report['staffRefund']=='archived-full-synthetic-once')
                for opener in invitation_sessions:
                    status,_,_,_=request(opener,base+'/shop/');require(status==403)
                require(staff_report['staffRevocation']=='archived-two-synthetic-invitations')
                require(staff_report['staffIssuance']=='two-deliberate-replacements-one-time-bearers')
                require(staff_report['staffDiscounts']=='two-archived-revocations-original-claim-clocks')
                require(staff_report['staffDiscountIssuance']=='two-deliberate-issues-one-time-codes')
                verify_staff_refunds(python,env,capture)
                report.update(customer_checks=report['checks'],staff_checks=staff_report['checks'],
                    checks=report['checks']+staff_report['checks'],staffRefund=staff_report['staffRefund'],
                    staffHandoff=staff_report['staffHandoff'],staffRevocation=staff_report['staffRevocation'],staffIssuance=staff_report['staffIssuance'],
                    staffDiscounts=staff_report['staffDiscounts'],
                    revoked_invitation_sessions='2-denied-on-next-request',staff_modes=2,staff_facts='original-orders-coupons-notices-unchanged')
                print(json.dumps(report))
                return report
            else:
                count=checks(base,credential,python,env)
                print(f'SHB_DEMO_PASS checks={count} evidence=local-synthetic-header-level fpga=review asic=submitted payment=not_exercised manual_time_tracking=true')
        else:
            invitation=scratch/'invitation.txt'
            fd=os.open(invitation,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
            with os.fdopen(fd,'w') as stream:stream.write(base+'/invite/'+credential['token']+'\n')
            discount_path=scratch/'discount.txt'
            fd=os.open(discount_path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
            with os.fdopen(fd,'w') as stream:stream.write(credential['discount_code']+'\n')
            print('SHB loopback demo: '+base,flush=True)
            print('Open the invitation from this private file: '+str(invitation),flush=True)
            print('Optional synthetic 10% code (two-use fixture) is in this private file: '+str(discount_path),flush=True)
            print('Use Synthetic Company Limited, any synthetic.invalid contact and the common form. FPGA review, exact acceptance and fake-only payment plus ASIC request capture work. Assigned staff can review and issue dated ASIC offers, record withdrawal or retire an offer for fresh reviewed reissue. Customers can deliberately withdraw unaccepted offers. Paid orders and durable synthetic support-team notices are available; use the configured leased worker for notices and final unaccepted offer expiry. Uncertain dispatched payments retain their holds for reconciliation. Ctrl-C removes only this demo and its disposable database.',flush=True)
            try:
                while True:time.sleep(1)
            except KeyboardInterrupt:pass


if __name__=='__main__':
    try:main()
    except subprocess.CalledProcessError as error:
        # Only a closed static stage label from the fixture browser is emitted.
        # Never print captured configuration, browser URLs, form data or bearer.
        stage=re.search(r'SHB_BROWSER_FAIL stage=([a-z-]+)',error.stderr or '')
        raise SystemExit('SHB_DEMO_FAIL'+(' browser_stage='+stage[1] if stage else ' owned fixture command failed')) from None
    except (ValueError,OSError,subprocess.SubprocessError):raise SystemExit('SHB_DEMO_FAIL: owned synthetic demonstration did not pass') from None
