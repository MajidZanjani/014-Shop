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


def run():
    checks = 0
    with prepared_database() as (python, env, pg, database, scratch):
        manage(python, env, 'migrate', '--noinput')
        mailbox = scratch / 'mail';mailbox.mkdir(mode=0o700)
        env['SHOP_LOCAL_CAPTURE_ROOT'] = str(mailbox)
        archive = scratch / 'checkout-archive';archive.mkdir(mode=0o700)
        env['SHOP_LOCAL_CHECKOUT_ARCHIVE_ROOT'] = str(archive)
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
                    checks += 25
            finally:
                server.shutdown();server.server_close();thread.join(3)
    print('DEMO_ACCESS_PASS checks=' + str(checks) + ' aliases=2 evidence=local-synthetic-header-level')


if __name__ == '__main__':
    try: run()
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        # Fixed errors only; never output captured codes/cookies/private response bodies.
        raise SystemExit('DEMO_ACCESS_FAIL: ' + (str(error) if type(error) is ValueError else 'owned test operation failed'))
