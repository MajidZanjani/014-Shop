#!/usr/bin/env python3
"""Real HTTP proxy/Gunicorn/PG form regression with Fetch-standard browser headers."""
from functools import partial
from html.parser import HTMLParser
from http.cookies import SimpleCookie
from http.server import ThreadingHTTPServer
import http.client
import re
import subprocess
import threading
from urllib.parse import urlencode
from check_backend import gunicorn
from check_worker import prepared_database, manage
from demo import DemoHandler


class FormToken(HTMLParser):
    token = None
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'input' and attrs.get('name') == 'csrfmiddlewaretoken':
            self.token = attrs.get('value')


def require(condition, message):
    if not condition: raise ValueError(message)


class BrowserHeaders:
    """Header-level regression, not an actual browser-engine qualification."""
    def __init__(self, port, alias):
        self.port = port;self.host = alias + ':' + str(port);self.origin = 'http://' + self.host
        self.cookies = {};self.policy = None;self.token = None

    def request(self, path, data=None, origin=None, token=True):
        headers = {'Host': self.host, 'Accept': 'text/html',
                   'Cookie': '; '.join(k + '=' + v for k, v in self.cookies.items())}
        body = None
        if data is not None:
            # Fetch's navigation POST under no-referrer sends Origin:null.
            headers['Origin'] = origin or ('null' if self.policy == 'no-referrer' else self.origin)
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
            if self.policy == 'same-origin': headers['Referer'] = self.origin + path
            body = urlencode(data | ({'csrfmiddlewaretoken': self.token} if token else {}))
        connection = http.client.HTTPConnection('127.0.0.1', self.port, timeout=5)
        try:
            connection.request('POST' if data is not None else 'GET', path, body=body, headers=headers)
            response = connection.getresponse();raw = response.read(65537)
            require(len(raw) <= 65536, 'unbounded response')
            for key, value in response.getheaders():
                if key.lower() == 'set-cookie':
                    cookie = SimpleCookie();cookie.load(value)
                    self.cookies.update({k: v.value for k, v in cookie.items()})
            if data is None:
                self.policy = response.getheader('Referrer-Policy')
                parser = FormToken();parser.feed(raw.decode());self.token = parser.token
            return response.status, response.getheader('Location'), raw
        finally: connection.close()


def run():
    checks = 0
    with prepared_database() as (python, env, pg, database, scratch):
        manage(python, env, 'migrate', '--noinput')
        mailbox = scratch / 'mail';mailbox.mkdir(mode=0o700)
        env['SHOP_LOCAL_CAPTURE_ROOT'] = str(mailbox)
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
                    browser.request('/purchase/access/')
                    for origin in ('null', 'http://untrusted.invalid'):
                        require(browser.request('/purchase/access/', {'action': 'logout'}, origin=origin)[0] == 403, 'untrusted origin accepted')
                    require(browser.request('/purchase/access/', {'action': 'logout'}, token=False)[0] == 403, 'missing token accepted')
                    status, location, _ = browser.request('/purchase/access/', {'action': 'logout'})
                    require(status == 303 and location == '/purchase/access/', 'logout redirect failed')
                    require(b'Request a code' in browser.request(location)[2], 'logout not effective')
                    checks += 16
            finally:
                server.shutdown();server.server_close();thread.join(3)
    print('DEMO_ACCESS_PASS checks=' + str(checks) + ' aliases=2 evidence=local-synthetic-header-level')


if __name__ == '__main__':
    try: run()
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        # Fixed errors only; never output captured codes/cookies/private response bodies.
        raise SystemExit('DEMO_ACCESS_FAIL: ' + (str(error) if type(error) is ValueError else 'owned test operation failed'))
