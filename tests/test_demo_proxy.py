"""Real loopback requests verify demo Host handling without any backend or credentials."""
from functools import partial
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import http.client
from pathlib import Path
import sys
import tempfile
import threading
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from demo import DemoHandler, StaffDemoHandler

class DemoHostTests(unittest.TestCase):
    def test_loopback_aliases_and_rebinding_hosts(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory,'index.html').write_text('synthetic public preview')
            server=ThreadingHTTPServer(('127.0.0.1',0),partial(DemoHandler,directory=directory))
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            def request(method,host):
                conn=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=3)
                try:
                    conn.request(method,'/',headers={'Host':host});r=conn.getresponse();r.read();return r.status
                finally:conn.close()
            try:
                for alias in ('127.0.0.1','localhost'):
                    self.assertEqual(request('GET',alias+':'+str(server.server_port)),200)
                for method in ('GET','POST','HEAD'):
                    self.assertEqual(request(method,'unapproved.invalid:'+str(server.server_port)),400)
            finally:server.shutdown();server.server_close();thread.join(3)

            staff=ThreadingHTTPServer(('127.0.0.1',0),StaffDemoHandler)
            staff_thread=threading.Thread(target=staff.serve_forever,daemon=True);staff_thread.start()
            try:
                for method in ('GET','POST','HEAD'):
                    for host in ('127.0.0.1','localhost','unapproved.invalid'):
                        conn=http.client.HTTPConnection('127.0.0.1',staff.server_port,timeout=3)
                        try:
                            conn.request(method,'/staff/',headers={'Host':host+':'+str(staff.server_port)})
                            response=conn.getresponse();response.read();self.assertEqual(response.status,400)
                        finally:conn.close()
                conn=http.client.HTTPConnection('127.0.0.1',staff.server_port,timeout=3)
                try:
                    conn.request('GET','/staff/',headers={'Host':'staff.localhost:'+str(staff.server_port)})
                    response=conn.getresponse();response.read();self.assertEqual(response.status,503)
                finally:conn.close()
                class AcceptBackend(BaseHTTPRequestHandler):
                    def log_message(self,*args):pass
                    def do_GET(self):
                        is_html=self.headers.get('Accept')=='text/html'
                        body=b'synthetic staff HTML' if is_html else b'{}'
                        self.send_response(303 if self.path == '/staff/redirect/' else 200)
                        if self.path == '/staff/redirect/':self.send_header('Location','/staff/')
                        self.send_header('Vary','Cookie')
                        self.send_header('Content-Type','text/html' if is_html else 'application/json')
                        self.send_header('Content-Security-Policy',"default-src 'none'")
                        self.end_headers();self.wfile.write(body)
                backend=ThreadingHTTPServer(('127.0.0.1',0),AcceptBackend)
                backend_thread=threading.Thread(target=backend.serve_forever,daemon=True);backend_thread.start()
                StaffDemoHandler.backend_port=backend.server_port
                conn=http.client.HTTPConnection('127.0.0.1',staff.server_port,timeout=3)
                try:
                    conn.request('GET','/staff/quotation-requests/',headers={'Host':'staff.localhost:'+str(staff.server_port),'Accept':'text/html'})
                    response=conn.getresponse()
                    self.assertEqual(response.status,200)
                    self.assertEqual(response.getheader('Content-Type'),'text/html')
                    self.assertEqual(response.getheader('Content-Security-Policy'),"default-src 'none'")
                    self.assertEqual(response.getheader('Vary'),'Cookie')
                    self.assertEqual(response.read(),b'synthetic staff HTML')
                    conn.request('GET','/staff/redirect/',headers={'Host':'staff.localhost:'+str(staff.server_port)})
                    response=conn.getresponse();response.read()
                    self.assertEqual(response.status,303)
                    self.assertEqual(response.getheader('Location'),'/staff/')
                finally:
                    conn.close();StaffDemoHandler.backend_port=None
                    backend.shutdown();backend.server_close();backend_thread.join(3)
            finally:staff.shutdown();staff.server_close();staff_thread.join(3)
