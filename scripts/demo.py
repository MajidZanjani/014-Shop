#!/usr/bin/env python3
"""Loopback static demo, optionally with an owned synthetic Django/PostgreSQL backend."""
import argparse
from contextlib import ExitStack
from functools import partial
import http.client
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import subprocess
import tempfile
import threading
ROOT=Path(__file__).resolve().parents[1]

class DemoHandler(SimpleHTTPRequestHandler):
    backend_port=None
    def log_message(self,format,*args):
        # Never put verification query strings, cookie data or arbitrary paths
        # in ordinary demo logs, even for malformed/manual requests.
        pass
    def approved_host(self):
        expected={'127.0.0.1:'+str(self.server.server_port),'localhost:'+str(self.server.server_port)}
        if self.headers.get('Host') not in expected:
            self.send_error(400);return False
        return True
    def backend(self):
        if self.backend_port is None:
            self.send_error(503,'Restart demo with --backend for the synthetic Django fallback');return
        try:
            size=int(self.headers.get('Content-Length','0'))
        except ValueError:
            self.send_error(400);return
        if size<0 or size>32768:
            self.send_error(413);return
        body=self.rfile.read(size) if size else None
        headers={k:self.headers[k] for k in ('Accept','Content-Type','Cookie','Origin','Referer','X-CSRFToken') if k in self.headers}
        headers['Host']=self.headers['Host']
        connection=http.client.HTTPConnection('127.0.0.1',self.backend_port,timeout=5)
        try:
            connection.request(self.command,self.path,body=body,headers=headers)
            response=connection.getresponse();data=response.read(65537)
            if len(data)>65536:
                self.send_error(502);return
            self.send_response(response.status)
            for key,value in response.getheaders():
                if key.lower() in ('content-type','set-cookie','cache-control','etag','x-content-type-options','referrer-policy','content-security-policy','location','vary'):
                    self.send_header(key,value)
            self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
        finally:connection.close()
    def do_GET(self):
        if not self.approved_host():return
        if self.path.startswith(('/api/','/purchase/')):self.backend()
        else:super().do_GET()
    def do_HEAD(self):
        if not self.approved_host():return
        super().do_HEAD()
    def do_POST(self):
        if not self.approved_host():return
        if self.path.startswith(('/api/','/purchase/')):self.backend()
        else:self.send_error(405)

class StaffDemoHandler(DemoHandler):
    def approved_host(self):
        if self.headers.get('Host')!='staff.localhost:'+str(self.server.server_port):
            self.send_error(400);return False
        return True
    def do_GET(self):
        if self.approved_host():self.backend()
    def do_HEAD(self):
        if self.approved_host():self.send_error(405)
    def do_POST(self):
        if self.approved_host():self.backend()

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--backend',action='store_true');parser.add_argument('--staff',action='store_true');args=parser.parse_args()
    if args.staff and not args.backend:parser.error('--staff requires --backend')
    (ROOT/'.scratch').mkdir(exist_ok=True)
    with ExitStack() as stack:
        scratch=Path(stack.enter_context(tempfile.TemporaryDirectory(prefix='demo-',dir=ROOT/'.scratch')))
        env={key:os.environ[key] for key in ('PATH','LANG','SSL_CERT_FILE','NIX_SSL_CERT_FILE') if key in os.environ}
        env.update(ASTRO_TELEMETRY_DISABLED='1',TMPDIR=str(scratch),NPM_CONFIG_USERCONFIG=str(scratch/'absent.npmrc'),NPM_CONFIG_GLOBALCONFIG=str(scratch/'global.npmrc'),NPM_CONFIG_CACHE=str(scratch/'cache'),XDG_CONFIG_HOME=str(scratch))
        subprocess.run(['python3','scripts/compile_catalog.py','--check'],cwd=ROOT,env=env,check=True,timeout=15)
        subprocess.run(['npm','ci','--no-audit','--no-fund'],cwd=ROOT/'frontend',env=env,check=True,timeout=150)
        subprocess.run(['npm','run','build'],cwd=ROOT/'frontend',env=env,check=True,timeout=90)
        from check_frontend import scan_output
        scan_output(ROOT/'frontend/dist')
        if args.backend:
            from check_worker import prepared_database, manage
            from check_backend import gunicorn
            python,runtime,pg,database,backend_scratch=stack.enter_context(prepared_database())
            manage(python,runtime,'migrate','--noinput')
            mailbox=scratch/'captured-mail';mailbox.mkdir(mode=0o700)
            runtime['SHOP_LOCAL_CAPTURE_ROOT']=str(mailbox)
            checkout_archive=scratch/'checkout-archive';checkout_archive.mkdir(mode=0o700)
            runtime['SHOP_LOCAL_CHECKOUT_ARCHIVE_ROOT']=str(checkout_archive)
            print('Private synthetic email capture directory: '+str(mailbox),flush=True)
            print('Read the newest private file there to obtain the verification code. No real email is sent.',flush=True)
            DemoHandler.backend_port=stack.enter_context(gunicorn(python,runtime,backend_scratch))
        if args.staff:
            staff_capture=scratch/'staff-capture';staff_capture.mkdir(mode=0o700)
            staff_scratch=scratch/'staff-runtime';staff_scratch.mkdir(mode=0o700)
            staff_runtime=dict(runtime,DJANGO_SETTINGS_MODULE='shop.config.staff_synthetic',SHOP_LOCAL_STAFF_CAPTURE_ROOT=str(staff_capture))
            manage(python,staff_runtime,'local_staff','provision','--username','demo-reviewer','--capture-root',str(staff_capture))
            # A new owned support-only fixture; never assign all existing requests.
            manage(python,staff_runtime,'shell','-c','''
import uuid
from django.contrib.auth import get_user_model
from shop.access.models import CustomerIdentity,StaffQuotationGrant
from django.utils import timezone
from shop.catalog.models import DraftCart,CartSnapshot,QuotationRequest
from shop.catalog.cart_rules import evaluate_cart
from shop.catalog.rules import CATALOG
owner=get_user_model().objects.create_user(username='staff-demo-owner-'+uuid.uuid4().hex)
CustomerIdentity.objects.create(user=owner,email='staff-demo-owner@synthetic.invalid',verified_at=timezone.now())
cart=DraftCart.objects.create(owner=owner,version=1)
lines=[{'id':str(uuid.uuid4()),'kind':'support','product_id':CATALOG['support_product_id'],'quantity':1}]
snapshot=CartSnapshot.objects.create(cart=cart,version=1,request_id=uuid.uuid4(),catalog_revision=CATALOG['revision'],lines=lines,evaluation=evaluate_cart(lines))
quotation=QuotationRequest.objects.create(cart=cart,snapshot=snapshot,request_id=uuid.uuid4())
StaffQuotationGrant.objects.create(user=get_user_model().objects.get(username='demo-reviewer'),quotation=quotation)
''')
            StaffDemoHandler.backend_port=stack.enter_context(gunicorn(python,staff_runtime,staff_scratch,probe_path='/staff/session/',probe_host='staff.localhost'))
            staff_server=ThreadingHTTPServer(('127.0.0.1',4322),StaffDemoHandler)
            staff_thread=threading.Thread(target=staff_server.serve_forever,daemon=True);staff_thread.start()
            def stop_staff():
                staff_server.shutdown();staff_server.server_close();staff_thread.join(3)
            stack.callback(stop_staff)
            print('Fixture customer: staff-demo-owner@synthetic.invalid · verify through the customer page to view the assigned fixture request and its review status.',flush=True)
            print('Local staff preview: http://staff.localhost:4322/staff/ · private credentials/codes directory: '+str(staff_capture),flush=True)
        server=ThreadingHTTPServer(('127.0.0.1',4321),partial(DemoHandler,directory=str(ROOT/'frontend/dist')))
        print('Local preview: http://127.0.0.1:4321 · fallback: /purchase/simple/ with --backend (Ctrl-C stops owned processes)',flush=True)
        try:server.serve_forever()
        except KeyboardInterrupt:pass
        finally:server.server_close()
