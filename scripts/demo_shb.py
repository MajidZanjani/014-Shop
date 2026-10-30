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


def fixture(python,env,capture):
    # The bearer exists only in this owned private capture and memory. Never
    # print it, put it in argv or promote this fixture into real eligibility.
    child=dict(env,SHOP_SHB_FIXTURE_CAPTURE=str(capture))
    manage(python,child,'shell','-c','''
import json,os
from django.contrib.auth import get_user_model
from shop.shb.invitations import issue_fixture
customer=get_user_model().objects.create_user(username='shb-demo-customer')
issuer=get_user_model().objects.create_user(username='shb-demo-issuer',is_staff=True)
row,token=issue_fixture(customer=customer,issuer=issuer,company_name='Synthetic Company Limited',project_reference='SLL synthetic project')
fd=os.open(os.environ['SHOP_SHB_FIXTURE_CAPTURE'],os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
with os.fdopen(fd,'w') as stream:json.dump({'invitation_id':str(row.pk),'token':token},stream)
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
    data=common_data(variant='shb-asic-25h',quantity='2',assistance='Review SLL IP integration',action='submit',csrfmiddlewaretoken=csrf)
    code,body,_,_=request(opener,base+'/purchase/simple/',data=data,origin=base)
    require(code==200 and b'50 requested hours' in body);count+=1
    code,body,_,_=request(opener,base+'/purchase/simple/',data=data,origin=base)
    require(code==200 and b'50 requested hours' in body);count+=1
    result=manage(python,env,'shell','-c',"from shop.shb.models import SupportRequest; from shop.payments.models import SyntheticPaymentAttempt; from shop.catalog.models import SyntheticFulfilment; print('SHB_COUNTS',SupportRequest.objects.count(),SyntheticPaymentAttempt.objects.count(),SyntheticFulfilment.objects.count())")
    require('SHB_COUNTS 1 0 0' in result.stdout);count+=1
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
        env=dict(env,DJANGO_SETTINGS_MODULE='shop.config.shb_synthetic')
        if args.release:
            sys.path.insert(0,str(ROOT/'backend'))
            from shop.shb.private_release import MANIFEST,read_asset,ENTRY
            release=args.release.resolve();digest=hashlib.sha256((release/MANIFEST).read_bytes()).hexdigest()
            read_asset(release,digest,ENTRY)
            env.update(SHOP_SHB_PRIVATE_RELEASE_ROOT=str(release),SHOP_SHB_PRIVATE_RELEASE_SHA256=digest)
        manage(python,env,'migrate','--noinput')
        capture=scratch/'invitation.json';fixture(python,env,capture)
        credential=json.loads(capture.read_text())
        port=stack.enter_context(gunicorn(python,env,backend_scratch));base='http://127.0.0.1:'+str(port)
        if args.check:
            if args.browser:
                require(args.release is not None)
                evidence=args.screenshot_root.resolve() if args.screenshot_root else None
                if evidence:require(evidence.is_relative_to((ROOT/'.scratch').resolve()) and evidence.is_dir() and not evidence.is_symlink() and not any(evidence.iterdir()))
                browser_env={key:os.environ[key] for key in ('PATH','LANG','HOME','TMPDIR','SHOP_NODE','SHOP_BROWSER','SHOP_BROWSER_NODE_VERSION','SHOP_BROWSER_VERSION') if key in os.environ}
                config={'origin':base,'invitationUrl':base+'/invite/'+credential['token'],'scratch':str(scratch),'evidence':str(evidence) if evidence else None}
                result=subprocess.run([browser_env['SHOP_NODE'],str(ROOT/'scripts/browser_shb.mjs')],input=json.dumps(config),text=True,capture_output=True,env=browser_env,timeout=120,check=True)
                report=json.loads(result.stdout)
                require(report['status']=='SHB_BROWSER_PASS' and report['checks']>=20 and report['modes']==2)
                print(json.dumps(report))
                retained=manage(python,env,'shell','-c',"from shop.shb.models import SupportRequest; from shop.payments.models import SyntheticPaymentAttempt; from shop.catalog.models import SyntheticFulfilment; print('SHB_COUNTS',SupportRequest.objects.count(),SyntheticPaymentAttempt.objects.count(),SyntheticFulfilment.objects.count())")
                require('SHB_COUNTS 2 0 0' in retained.stdout)
            else:
                count=checks(base,credential,python,env)
                print(f'SHB_DEMO_PASS checks={count} evidence=local-synthetic-header-level fpga=review asic=submitted payment=disabled manual_time_tracking=true')
        else:
            invitation=scratch/'invitation.txt'
            fd=os.open(invitation,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
            with os.fdopen(fd,'w') as stream:stream.write(base+'/invite/'+credential['token']+'\n')
            print('SHB loopback demo: '+base,flush=True)
            print('Open the invitation from this private file: '+str(invitation),flush=True)
            print('Use Synthetic Company Limited, any synthetic.invalid contact and the common form. FPGA review and ASIC request capture work; payments, discounts, reviewed paid offers and notification delivery remain pending. Ctrl-C removes only this demo and its disposable database.',flush=True)
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
