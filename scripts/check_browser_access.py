#!/usr/bin/env python3
"""Bounded pinned Chromium smoke on owned synthetic PG/Gunicorn/proxy only."""
from contextlib import ExitStack
from functools import partial
from http.server import ThreadingHTTPServer
import argparse
import json
import os
import re
from pathlib import Path
import signal
import socket
import sys
import subprocess
import threading
from check_backend import gunicorn
from check_worker import prepared_database,manage
from demo import DemoHandler,StaffDemoHandler
ROOT=Path(__file__).resolve().parents[1]


def validate_result(value,browser_version,node_version):
    fields={'status','checks','modes','roles','browser_version','node_version','evidence_class',
            'formal_accessibility','production_qualified','browser_sandbox'}
    if (not isinstance(value,dict) or set(value)!=fields or value['status']!='BROWSER_LOCAL_PASS'
            or type(value['checks']) is not int or value['checks']!=108
            or type(value['modes']) is not int or value['modes']!=2
            or type(value['roles']) is not int or value['roles']!=2
            or value['node_version']!=node_version or value['browser_version']!=browser_version
            or value['evidence_class']!='local-synthetic-browser-engine'
            or value['formal_accessibility'] is not False or value['production_qualified'] is not False
            or value['browser_sandbox']!='disabled-for-owned-local-root-smoke'):
        raise ValueError('browser evidence incomplete')


PUBLIC_FIELDS={'public_checks','frontend_toolchain'}


def validate_public_result(value,browser_version,node_version):
    if (not isinstance(value,dict) or not PUBLIC_FIELDS<=set(value)
            or value['public_checks']!={'javascript':25,'no_javascript':14}
            or any(type(count) is not int for count in value['public_checks'].values())
            or value['frontend_toolchain']!={'node':'24.22.0','npm':'11.19.1'}):
        raise ValueError('public browser evidence incomplete')
    validate_result({key:item for key,item in value.items() if key not in PUBLIC_FIELDS},browser_version,node_version)


def prepare_public(public):
    from check_frontend import scan_output
    nix_temporary=public.parent/'frontend-nix-tmp';nix_temporary.mkdir(mode=0o700)
    build_env={key:os.environ[key] for key in ('PATH','LANG','SSL_CERT_FILE','NIX_SSL_CERT_FILE','HOME') if key in os.environ}
    build_env['TMPDIR']=str(nix_temporary)
    result=subprocess.run(['nix','develop','--max-jobs','1','--cores','1','./ops/nixos#default',
                           '--command','python3','scripts/check_browser_public.py',str(public)],
                          cwd=ROOT,env=build_env,capture_output=True,text=True,timeout=720)
    if result.returncode:raise ValueError('fresh frozen public build unavailable')
    try:receipt=json.loads(result.stdout)
    except ValueError:raise ValueError('fresh frozen public build unavailable') from None
    inventory,_=scan_output(public)
    if (not isinstance(receipt,dict) or set(receipt)!={'status','frontend_toolchain','artifacts'}
            or receipt['status']!='PUBLIC_BROWSER_BUILD_PASS'
            or receipt['frontend_toolchain']!={'node':'24.22.0','npm':'11.19.1'}
            or receipt['artifacts']!=inventory):
        raise ValueError('fresh frozen public build unavailable')
    return receipt['frontend_toolchain']


CONTROL_ACTIONS=('revoke-support','grant-support','revoke')


def validate_control_request(raw,sequence):
    """Closed, ordered test-controller protocol; no caller-provided identity or scope."""
    if len(raw)>128 or sequence not in range(6):
        raise ValueError('browser control refused')
    def closed_object(pairs):
        value=dict(pairs)
        if len(value)!=len(pairs):raise ValueError('browser control refused')
        return value
    try:value=json.loads(raw,object_pairs_hook=closed_object)
    except (ValueError,UnicodeError):raise ValueError('browser control refused') from None
    if (not isinstance(value,dict) or set(value)!={'index','action'}
            or type(value['index']) is not int or value['index']!=sequence//3
            or value['action']!=CONTROL_ACTIONS[sequence%3]):
        raise ValueError('browser control refused')
    return value['index'],value['action']


def serve_controls(connection,perform,errors):
    # Dedicated inherited socket only; no listener, HTTP route or DB credentials in Node.
    connection.settimeout(90)
    try:
        for sequence in range(6):
            raw=b''
            while not raw.endswith(b'\n'):
                part=connection.recv(129-len(raw))
                if not part or len(raw)+len(part)>128:
                    raise ValueError('browser control refused')
                raw+=part
            index,action=validate_control_request(raw,sequence)
            perform(index,action)  # Never retry an uncertain operator operation.
            connection.sendall(b'{"ok":true}\n')
        if connection.recv(1):raise ValueError('browser control refused')
    except (ValueError,OSError,subprocess.SubprocessError):
        errors.append('browser control failed')
    finally:connection.close()


class OwnedBrowserServer(ThreadingHTTPServer):
    def handle_error(self,request,client_address):
        # Page navigation can cancel an already queued stylesheet response.
        # Keep unexpected server failures visible; do not print cancelled-client traces.
        if isinstance(sys.exception(),(BrokenPipeError,ConnectionResetError)):
            return
        super().handle_error(request,client_address)


def main(include_public=False):
    node=os.environ.get('SHOP_NODE','');browser=os.environ.get('SHOP_BROWSER','')
    if not node.startswith('/nix/store/') or not browser.startswith('/nix/store/'):
        raise ValueError('pinned browser shell required')
    with prepared_database() as (python,env,pg,database,scratch):
        manage(python,env,'migrate','--noinput')
        mailbox=scratch/'mail';mailbox.mkdir(mode=0o700)
        archive=scratch/'archive';archive.mkdir(mode=0o700)
        env['SHOP_LOCAL_CAPTURE_ROOT']=str(mailbox)
        env['SHOP_LOCAL_CHECKOUT_ARCHIVE_ROOT']=str(archive)
        code='''from shop.payments.purchase_demo_scenario import run
from shop.catalog.models import SyntheticPackageRevision,SyntheticFulfilment
from django.conf import settings
import argparse
import json
run(ARCHIVE_ROOT)
p=SyntheticPackageRevision.objects.select_related('entitlement__fulfilment__acceptance__checkout__owner__customeridentity').filter(stage='initial',version=1).latest('pk')
c=p.entitlement.fulfilment.acceptance.checkout
print(json.dumps({'email':c.owner.customeridentity.email,'support':'/purchase/checkout-rehearsal/'+str(c.pk)+'/support/',
                 'session_cookie':settings.SESSION_COOKIE_NAME,'checkout_id':str(c.pk),
                 'unassigned_checkout_id':str(SyntheticFulfilment.objects.get(acceptance__checkout__owner__username__startswith='finance-demo-').acceptance.checkout_id)}))
'''.replace('ARCHIVE_ROOT',repr(str(archive)))
        fixture=json.loads(manage(python,env,'shell','--no-imports','-c',code,timeout=30).stdout)
        capture=scratch/'staff-capture';capture.mkdir(mode=0o700)
        staff_scratch=scratch/'staff-runtime';staff_scratch.mkdir(mode=0o700)
        staff_env=dict(env,DJANGO_SETTINGS_MODULE='shop.config.staff_synthetic',SHOP_LOCAL_STAFF_CAPTURE_ROOT=str(capture))
        actors=[]
        for index in range(2):
            username='browser-reviewer-'+str(index)
            before=set(capture.iterdir())
            manage(python,staff_env,'local_staff','provision','--username',username,'--capture-root',str(capture))
            files=list(set(capture.iterdir())-before)
            if len(files)!=1:raise ValueError('owned staff fixture unavailable')
            credentials=files[0].read_text()
            password=re.search(r'^Password: ([A-Za-z0-9_-]+)$',credentials,re.M)
            if password is None:raise ValueError('owned staff fixture unavailable')
            manage(python,staff_env,'local_staff','grant-support','--username',username,'--checkout',fixture['checkout_id'])
            actors.append({'username':username,'password':password[1]})
        fixture['staff']={'actors':actors,'capture':str(capture),
                          'support':'/staff/support/'+fixture['checkout_id']+'/',
                          'unassigned':'/staff/support/'+fixture['unassigned_checkout_id']+'/',
                          'session_cookie':'shop_staff_sessionid'}
        def perform(index,action):
            arguments=['local_staff',action,'--username',actors[index]['username']]
            if action!='revoke':arguments+=['--checkout',fixture['checkout_id']]
            manage(python,staff_env,*arguments,timeout=10)
        public=scratch/'public';public.mkdir(mode=0o700)
        if include_public:
            fixture['frontend_toolchain']=prepare_public(public)
        (public/'browser-fixture.html').write_text('<!doctype html><html lang="en"><title>Owned browser mode probe</title><main><h1>Owned local mode probe</h1></main><script>window.shop_page_script_ran=true;</script></html>')
        with ExitStack() as stack:
            backend_port=stack.enter_context(gunicorn(python,env,scratch))
            staff_port=stack.enter_context(gunicorn(python,staff_env,staff_scratch,probe_path='/staff/session/',probe_host='staff.localhost'))
            handler=type('OwnedBrowserHandler',(DemoHandler,),{'backend_port':backend_port})
            server=OwnedBrowserServer(('127.0.0.1',0),partial(handler,directory=str(scratch/'public')))
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            staff_handler=type('OwnedStaffBrowserHandler',(StaffDemoHandler,),{'backend_port':staff_port})
            staff_server=OwnedBrowserServer(('127.0.0.1',0),staff_handler)
            staff_thread=threading.Thread(target=staff_server.serve_forever,daemon=True);staff_thread.start()
            fixture['staff']['origin']='http://staff.localhost:'+str(staff_server.server_port)
            process=None
            controller,client=socket.socketpair()
            control_errors=[]
            control_thread=threading.Thread(target=serve_controls,args=(controller,perform,control_errors),daemon=True)
            control_thread.start()
            try:
                fixture.update(origin='http://127.0.0.1:'+str(server.server_port),scratch=str(scratch),mailbox=str(mailbox))
                configuration=scratch/'browser.json';configuration.write_text(json.dumps(fixture));configuration.chmod(0o600)
                child_env={key:os.environ[key] for key in ('PATH','LANG','HOME','SHOP_NODE','SHOP_BROWSER','SHOP_BROWSER_VERSION','SHOP_BROWSER_NODE_VERSION') if key in os.environ}
                child_env['SHOP_BROWSER_CONTROL_FD']=str(client.fileno())
                process=subprocess.Popen([node,str(ROOT/'scripts/browser_purchase.mjs'),str(configuration)],
                    env=child_env,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True,pass_fds=(client.fileno(),))
                client.close()
                stdout,stderr=process.communicate(timeout=90)
                if process.returncode:
                    # Driver emits only its fixed stage marker; no captured body, code, cookie or URL.
                    marker=stderr.strip()
                    if marker.startswith('BROWSER_ENGINE_FAIL stage=') and len(marker)<100:
                        raise ValueError(marker)
                    raise ValueError('browser driver failed')
                control_thread.join(2)
                if control_thread.is_alive() or control_errors:raise ValueError('browser control failed')
                value=json.loads(stdout)
                validator=validate_public_result if include_public else validate_result
                validator(value,os.environ['SHOP_BROWSER_VERSION'],os.environ['SHOP_BROWSER_NODE_VERSION'])
                print(json.dumps(value,sort_keys=True))
            finally:
                if process is not None:
                    try:os.killpg(process.pid,signal.SIGTERM)
                    except ProcessLookupError:pass
                    try:process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        try:os.killpg(process.pid,signal.SIGKILL)
                        except ProcessLookupError:pass
                        process.wait(timeout=5)
                client.close()
                try:controller.shutdown(socket.SHUT_RDWR)
                except OSError:pass
                controller.close();control_thread.join(2)
                staff_server.shutdown();staff_server.server_close();staff_thread.join(3)
                server.shutdown();server.server_close();thread.join(3)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--public',action='store_true',help='Require a fresh exact frontend build and public React/browser checks')
    arguments=parser.parse_args()
    try:main(include_public=arguments.public)
    except (ValueError,OSError,subprocess.SubprocessError) as error:
        raise SystemExit('BROWSER_LOCAL_FAIL: '+(str(error) if type(error) is ValueError else 'owned operation failed')) from None
