#!/usr/bin/env python3
"""Real HTTP proxy/Gunicorn/PG form regression with Fetch-standard browser headers."""
from functools import partial
from html.parser import HTMLParser
from http.cookies import SimpleCookie
from http.server import ThreadingHTTPServer
import http.client
import json
import uuid
import re
import subprocess
import threading
from urllib.parse import urlencode
from check_backend import gunicorn
from check_worker import prepared_database, manage
from demo import DemoHandler


class FormToken(HTMLParser):
    token = None
    def __init__(self):
        super().__init__();self.hidden = {}
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'input' and attrs.get('type') == 'hidden' and attrs.get('name'):
            self.hidden[attrs['name']] = attrs.get('value', '')
        if tag == 'input' and attrs.get('name') == 'csrfmiddlewaretoken':
            self.token = attrs.get('value')


def require(condition, message):
    if not condition: raise ValueError(message)


class BrowserHeaders:
    """Header-level regression, not an actual browser-engine qualification."""
    def __init__(self, port, alias):
        self.port = port;self.host = alias + ':' + str(port);self.origin = 'http://' + self.host
        self.cookies = {};self.policy = None;self.token = None

    def request(self, path, data=None, origin=None, token=True, json_body=None):
        headers = {'Host': self.host, 'Accept': 'text/html',
                   'Cookie': '; '.join(k + '=' + v for k, v in self.cookies.items())}
        body = None
        if data is not None:
            # Fetch's navigation POST under no-referrer sends Origin:null.
            headers['Origin'] = origin or ('null' if self.policy == 'no-referrer' else self.origin)
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
            if self.policy == 'same-origin': headers['Referer'] = self.origin + path
            body = urlencode(data | ({'csrfmiddlewaretoken': self.token} if token else {}))
        if json_body is not None:
            headers['Origin'] = self.origin
            headers['Content-Type'] = 'application/json'
            headers['X-CSRFToken'] = self.token
            body = json.dumps(json_body)
        connection = http.client.HTTPConnection('127.0.0.1', self.port, timeout=5)
        try:
            connection.request('POST' if data is not None or json_body is not None else 'GET', path, body=body, headers=headers)
            response = connection.getresponse();raw = response.read(65537)
            require(len(raw) <= 65536, 'unbounded response')
            for key, value in response.getheaders():
                if key.lower() == 'set-cookie':
                    cookie = SimpleCookie();cookie.load(value)
                    self.cookies.update({k: v.value for k, v in cookie.items()})
            if data is None and json_body is None and response.getheader('Content-Type', '').startswith('text/html'):
                self.policy = response.getheader('Referrer-Policy')
                parser = FormToken();parser.feed(raw.decode());self.token = parser.token;self.hidden = parser.hidden
            return response.status, response.getheader('Location'), raw
        finally: connection.close()



def fixture_delivery_control(python,env,fixture,archive,action):
    """Trusted disposable actor fixture; actual two-factor route is exercised by demo."""
    code="""from pathlib import Path
import uuid
from django.test import RequestFactory,override_settings
from django.utils import timezone
from shop.access.models import StaffCredential
from shop.catalog.models import SyntheticDeliveryStaffGrant,SyntheticDeliveryControl
from shop.catalog.delivery_controls import record
from shop.adapters.evidence_archive import PreparedArchive
scope=SyntheticDeliveryStaffGrant.objects.select_related('user','entitlement__fulfilment__acceptance__checkout__owner').get(entitlement_id=LINE_ID)
credential=StaffCredential.objects.get(user=scope.user)
saved=scope.entitlement.fulfilment.acceptance.checkout
request=RequestFactory().post('/staff/delivery/',HTTP_HOST='staff.localhost')
request.user=scope.user
request.session={'shop_staff_mfa':{'generation':str(credential.generation),'verified_at':timezone.now().timestamp()}}
with override_settings(LOCAL_STAFF_ENABLED=True,ALLOWED_HOSTS=['staff.localhost']):
    with PreparedArchive(Path(ARCHIVE_ROOT)) as retained:
        event=record(request,saved.owner,saved.pk,scope.entitlement_id,uuid.uuid4(),SyntheticDeliveryControl.objects.filter(entitlement=scope.entitlement).count(),CONTROL_ACTION,retained)
""".replace('LINE_ID',repr(fixture['entitlement_id'])).replace('ARCHIVE_ROOT',repr(str(archive))).replace('CONTROL_ACTION',repr(action))
    manage(python,env,'shell','--no-imports','-c',code,timeout=15)


def run():
    checks = 0
    with prepared_database() as (python, env, pg, database, scratch):
        manage(python, env, 'migrate', '--noinput')
        mailbox = scratch / 'mail';mailbox.mkdir(mode=0o700)
        env['SHOP_LOCAL_CAPTURE_ROOT'] = str(mailbox)
        archive = scratch / 'checkout-archive';archive.mkdir(mode=0o700)
        env['SHOP_LOCAL_CHECKOUT_ARCHIVE_ROOT'] = str(archive)
        # Fresh complete-cart fixture, released through supported two-factor staff routes.
        seed_code = '''
from shop.payments.purchase_demo_scenario import run
from shop.catalog.models import SyntheticPackageRevision
import json
run(ARCHIVE_ROOT)
p=SyntheticPackageRevision.objects.select_related('entitlement__fulfilment__acceptance__checkout__owner__customeridentity').filter(stage='initial',version=1).latest('pk')
c=p.entitlement.fulfilment.acceptance.checkout
print(json.dumps({'email':c.owner.customeridentity.email,'checkout_id':str(c.pk),'package_id':str(p.identity),'entitlement_id':str(p.entitlement_id)}))
'''.replace('ARCHIVE_ROOT', repr(str(archive)))
        material_fixture=json.loads(manage(python,env,'shell','--no-imports','-c',seed_code,timeout=30).stdout)
        with gunicorn(python, env, scratch) as backend_port:
            handler = type('OwnedDemoHandler', (DemoHandler,), {'backend_port': backend_port})
            server = ThreadingHTTPServer(('127.0.0.1', 0), partial(handler, directory=str(scratch)))
            thread = threading.Thread(target=server.serve_forever, daemon=True);thread.start()
            try:
                for alias in ('127.0.0.1', 'localhost'):
                    browser = BrowserHeaders(server.server_port, alias)
                    status, _, _ = browser.request('/purchase/access/')
                    require(status == 200 and browser.token, 'access form unavailable')
                    before = set(mailbox.iterdir())
                    status, location, _ = browser.request('/purchase/access/', {'action': 'request', 'email': alias + '@synthetic.invalid'})
                    require(status == 303, 'request-code form rejected with browser navigation headers')
                    require(location == '/purchase/access/', 'proxy lost request-code redirect')
                    require(browser.policy == 'same-origin', 'form policy cannot preserve same-origin POST origin')
                    added = set(mailbox.iterdir()) - before
                    require(len(added) == 1, 'synthetic mail capture missing')
                    match = re.search(r'^Verification code: ([A-Za-z0-9_-]+)$', added.pop().read_text(), re.M)
                    require(match is not None, 'synthetic code missing')
                    browser.request(location)
                    status, location, _ = browser.request('/purchase/access/', {'action': 'verify', 'code': match[1]})
                    require(status == 303 and location == '/purchase/access/', 'verification redirect failed')
                    require(b'Your customer access is verified.' in browser.request(location)[2], 'verified page missing')
                    for path in ('/purchase/cart/', '/purchase/business/', '/purchase/checkout-rehearsal/'):
                        status, _, _ = browser.request(path)
                        require(status in (200, 422) and browser.policy == 'same-origin', 'private form policy missing')
                    # Continue through business, support-only cart, frozen checkout and fixture payment.
                    catalog = json.loads(browser.request('/api/v1/catalog/')[2])
                    browser.request('/purchase/business/')
                    details = {key: browser.hidden[key] for key in ('request_id','expected_version','schema_version','source_sha256')}
                    details.update(legal_business_name='Synthetic proxy organisation', registered_address='Synthetic address',
                        billing_same_as_registered='on', purchasing_name='Synthetic buyer', business_email=alias+'@synthetic.invalid',
                        technical_same_as_purchasing='on')
                    require(browser.request('/purchase/business/', details)[0] == 303, 'business form save failed')
                    cart = {'request_id':str(uuid.uuid4()), 'expected_version':0, 'catalog_revision':catalog['revision'],
                            'lines':[{'id':str(uuid.uuid4()), 'kind':'support', 'product_id':catalog['support_product_id'], 'quantity':1}]}
                    require(browser.request('/api/v1/cart/', json_body=cart)[0] == 201, 'cart API save failed')
                    browser.request('/purchase/checkout-rehearsal/')
                    command = {key:browser.hidden[key] for key in ('request_id','sha256')}
                    status, _, raw = browser.request('/purchase/checkout-rehearsal/', command)
                    require(status == 200, 'checkout form capture failed')
                    match = re.search(r'href="(/purchase/checkout-rehearsal/[0-9a-f-]+/payment/)"', raw.decode())
                    require(match is not None, 'acceptance navigation missing')
                    payment = match[1];browser.request(payment)
                    require(browser.request(payment, {'action':'accept','sha256':browser.hidden['sha256'],'confirmed':'on'})[0] == 200, 'fixture confirmation failed')
                    status, _, raw = browser.request(payment, {'action':'pay'})
                    require(status == 200 and b'Simulated payment captured' in raw, 'fixture payment failed')
                    require(browser.request(payment, {'action':'pay'})[0] == 200, 'fixture payment retry failed')
                    status, _, raw = browser.request(payment, {'action':'provision'})
                    require(status == 200 and b'36000 integer seconds' in raw, 'support-only grant failed')
                    require(browser.request(payment, {'action':'provision'})[0] == 200, 'support grant retry failed')
                    support = payment.replace('/payment/', '/support/')
                    status, _, raw = browser.request(support)
                    require(status == 200 and browser.policy == 'same-origin' and b'Simulate support reservation' in raw, 'support form/policy unavailable')
                    reserve = {key:browser.hidden[key] for key in ('request_id','task_id')}
                    reserve.update(action='reserve',seconds='3600')
                    status, location, _ = browser.request(support, reserve)
                    require(status == 303 and location == support, 'support reservation redirect failed')
                    require(browser.request(support, reserve)[0] == 303, 'support reservation retry failed')
                    status, _, raw = browser.request(support)
                    require(status == 200 and b'Reserved: 3600' in raw and b'Available: 32400' in raw, 'support reservation balance mismatch')
                    release = {key:browser.hidden[key] for key in ('request_id','target_id')}
                    release['action'] = 'release'
                    require(browser.request(support, release)[0] == 303, 'support release failed')
                    require(browser.request(support, release)[0] == 303, 'support release retry failed')
                    status, _, raw = browser.request(support)
                    require(status == 200 and b'Reserved: 0' in raw and b'Available: 36000' in raw, 'support release balance mismatch')
                    require(browser.request(support, reserve, origin='null')[0] == 403, 'support null origin accepted')
                    checks += 8
                    browser.request('/purchase/access/')
                    for origin in ('null', 'http://untrusted.invalid'):
                        require(browser.request('/purchase/access/', {'action': 'logout'}, origin=origin)[0] == 403, 'untrusted origin accepted')
                    require(browser.request('/purchase/access/', {'action': 'logout'}, token=False)[0] == 403, 'missing token accepted')
                    status, location, _ = browser.request('/purchase/access/', {'action': 'logout'})
                    require(status == 303 and location == '/purchase/access/', 'logout redirect failed')
                    require(b'Request a code' in browser.request(location)[2], 'logout not effective')
                    materials=BrowserHeaders(server.server_port,alias)
                    require(materials.request('/purchase/access/')[0]==200,'private material login form missing')
                    before=set(mailbox.iterdir())
                    require(materials.request('/purchase/access/',{'action':'request','email':material_fixture['email']})[0]==303,'private material verification request failed')
                    added=set(mailbox.iterdir())-before
                    require(len(added)==1,'private material verification capture missing')
                    match=re.search(r'^Verification code: ([A-Za-z0-9_-]+)$',added.pop().read_text(),re.M)
                    require(match is not None,'private material code unavailable')
                    materials.request('/purchase/access/')
                    require(materials.request('/purchase/access/',{'action':'verify','code':match[1]})[0]==303,'private material verification failed')
                    material_base='/purchase/checkout-rehearsal/'+material_fixture['checkout_id']+'/packages/'
                    status,_,raw=materials.request(material_base)
                    require(status==200 and materials.policy=='same-origin' and b'Prepare private download' in raw,'private material page/policy unavailable')
                    access=material_base+material_fixture['package_id']+'/access/'
                    download=material_base+material_fixture['package_id']+'/download/'
                    status,_,raw=materials.request(access,{'artifact':'sll-synthetic-rtl.txt'})
                    parsed=FormToken();parsed.feed(raw.decode());bearer=parsed.hidden.get('token')
                    require(status==200 and bearer and bearer not in download,'private download form or body-only bearer missing')
                    status,_,raw=materials.request(download,{'token':bearer})
                    require(status==200 and b'synthetic-materials-v1' in raw,'private archived-version download failed')
                    require(materials.request(download,{'token':bearer})[0]==404,'private download replay accepted')
                    require(materials.request(access,{'artifact':'sll-synthetic-rtl.txt'},token=False)[0]==403,'private download missing-CSRF accepted')
                    require(materials.request(download)[0]==405,'private download GET accepted')
                    checks += 11
                    materials.request(material_base)
                    status,_,raw=materials.request(access,{'artifact':'sll-synthetic-rtl.txt'})
                    pending=FormToken();pending.feed(raw.decode());old_grant=pending.hidden.get('token')
                    require(status==200 and old_grant,'pre-hold proxy grant unavailable')
                    retained_csrf=materials.token
                    fixture_delivery_control(python,env,material_fixture,archive,'hold')
                    status,_,raw=materials.request(material_base)
                    require(status==200 and b'Delivery held' in raw and b'Prepare private download' not in raw,'held proxy material listing incorrect')
                    materials.token=retained_csrf
                    require(materials.request(access,{'artifact':'sll-synthetic-rtl.txt'},origin=materials.origin)[0]==423,'held proxy grant accepted')
                    require(materials.request(download,{'token':old_grant},origin=materials.origin)[0]==423,'held proxy download accepted')
                    fixture_delivery_control(python,env,material_fixture,archive,'clear')
                    require(materials.request(download,{'token':old_grant},origin=materials.origin)[0]==404,'cleared proxy hold resurrected old token')
                    materials.request(material_base)
                    status,_,raw=materials.request(access,{'artifact':'sll-synthetic-rtl.txt'})
                    fresh=FormToken();fresh.feed(raw.decode());fresh_grant=fresh.hidden.get('token')
                    require(status==200 and fresh_grant,'fresh post-hold proxy grant unavailable')
                    require(materials.request(download,{'token':fresh_grant})[0]==200,'fresh post-hold proxy download failed')
                    checks += 7
                    refunds='/purchase/checkout-rehearsal/'+material_fixture['checkout_id']+'/support/refunds/'
                    status,_,raw=materials.request(refunds)
                    require(status==200 and materials.policy=='same-origin' and b'Request simulated refund review' in raw,'refund request form/policy unavailable')
                    refund_command={'request_id':str(uuid.uuid4()),'seconds':'72000'}
                    status,location,_=materials.request(refunds,refund_command)
                    require(status==303 and location and location.startswith(refunds),'refund request redirect failed')
                    require(materials.request(refunds,refund_command)[1]==location,'refund request retry changed identity')
                    status,_,raw=materials.request(location)
                    require(status==200 and b'Consumed support requires explicit review' in raw and b'awaiting_review' in raw,'refund consumed-credit status failed')
                    status,_,raw=materials.request(refunds)
                    require(status==200 and location.rsplit('/',2)[1].encode() in raw,'refund owner list missing request')
                    require(materials.request(refunds,refund_command,origin='null')[0]==403,'refund null origin accepted')
                    require(materials.request(refunds,refund_command,token=False)[0]==403,'refund missing-CSRF accepted')
                    status,_,raw=materials.request(refunds.removesuffix('refunds/'))
                    require(status==200 and b'Spent: 1800' in raw and b'Available: 70200' in raw,'refund request changed support balance')
                    checks += 8
                    support=refunds.removesuffix('refunds/')
                    status,_,raw=materials.request(support)
                    require(status==200 and b'Optional private support follow-up' in raw and b'No actual technical data' in raw,
                            'private follow-up boundary unavailable')
                    context_command={'action':'context','request_id':str(uuid.uuid4()),
                        'fixture':'synthetic-context-v1','expected_revision':materials.hidden['expected_revision']}
                    require(materials.request(support,context_command,origin='null')[0]==403,'private context null origin accepted')
                    require(materials.request(support,context_command,token=False)[0]==403,'private context missing CSRF accepted')
                    require(materials.request(support,context_command)[0]==303,'private context form rejected')
                    require(materials.request(support,context_command)[0]==303,'private context retry rejected')
                    stale=context_command|{'request_id':str(uuid.uuid4())}
                    require(materials.request(support,stale)[0]==409,'stale private context accepted')
                    status,_,raw=materials.request(support,json_body=context_command|{'expected_revision':int(context_command['expected_revision']),
                        'technical_text':'PRIVATE_HTTP_CANARY'})
                    require(status==400 and b'PRIVATE_HTTP_CANARY' not in raw,'actual technical text accepted or echoed')
                    status,_,raw=materials.request(support)
                    require(status==200 and b'Spent: 1800' in raw and b'Available: 70200' in raw,
                            'private context changed ledger')
                    checks += 8
                    changes='/purchase/checkout-rehearsal/'+material_fixture['checkout_id']+'/changes/'
                    create=changes+'new/'+material_fixture['entitlement_id']+'/'
                    status,_,raw=materials.request(create)
                    require(status==200 and materials.policy=='same-origin' and b'Capture rehosting request' in raw,'licence change form/policy unavailable')
                    change_command={'kind':'rehost','request_id':str(uuid.uuid4())}
                    status,location,_=materials.request(create,change_command)
                    require(status==303 and location and location.startswith(changes),'licence case capture redirect failed')
                    require(materials.request(create,change_command)[1]==location,'licence case retry changed identity')
                    status,_,raw=materials.request(location)
                    require(status==200 and b'awaiting_review' in raw,'licence case owner status failed')
                    require(materials.request(create,change_command,origin='null')[0]==403,'licence case null origin accepted')
                    require(materials.request(create,change_command,token=False)[0]==403,'licence case missing-CSRF accepted')
                    require(materials.request(changes)[0]==200,'owner licence case list unavailable')
                    checks += 7
                    checks += 25
            finally:
                server.shutdown();server.server_close();thread.join(3)
    print('DEMO_ACCESS_PASS checks=' + str(checks) + ' aliases=2 evidence=local-synthetic-header-level')


if __name__ == '__main__':
    try: run()
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        # Fixed errors only; never output captured codes/cookies/private response bodies.
        raise SystemExit('DEMO_ACCESS_FAIL: ' + (str(error) if type(error) is ValueError else 'owned test operation failed'))
