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
        if size<0 or size>8192:
            self.send_error(413);return
        body=self.rfile.read(size) if size else None
        headers={k:self.headers[k] for k in ('Content-Type','Cookie','Origin','Referer','X-CSRFToken') if k in self.headers}
        headers['Host']=self.headers['Host']
        connection=http.client.HTTPConnection('127.0.0.1',self.backend_port,timeout=5)
        try:
            connection.request(self.command,self.path,body=body,headers=headers)
            response=connection.getresponse();data=response.read(65537)
            if len(data)>65536:
                self.send_error(502);return
            self.send_response(response.status)
            for key,value in response.getheaders():
                if key.lower() in ('content-type','set-cookie','cache-control','etag','x-content-type-options','referrer-policy'):
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

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--backend',action='store_true');args=parser.parse_args()
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
            print('Private synthetic email capture directory: '+str(mailbox),flush=True)
            print('Read the newest private file there to obtain the verification code. No real email is sent.',flush=True)
            DemoHandler.backend_port=stack.enter_context(gunicorn(python,runtime,backend_scratch))
        server=ThreadingHTTPServer(('127.0.0.1',4321),partial(DemoHandler,directory=str(ROOT/'frontend/dist')))
        print('Local preview: http://127.0.0.1:4321 · fallback: /purchase/simple/ with --backend (Ctrl-C stops owned processes)',flush=True)
        try:server.serve_forever()
        except KeyboardInterrupt:pass
        finally:server.server_close()
