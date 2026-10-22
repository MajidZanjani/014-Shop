"""Real loopback requests verify demo Host handling without any backend or credentials."""
from functools import partial
from http.server import ThreadingHTTPServer
import http.client
from pathlib import Path
import sys
import tempfile
import threading
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from demo import DemoHandler

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
