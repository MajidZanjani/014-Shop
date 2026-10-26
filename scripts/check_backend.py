#!/usr/bin/env python3
"""Real synthetic Django/PG checks; full core requires an assigned off-host runner."""
import argparse
import contextlib
import hashlib
import json
import os
from pathlib import Path
import signal
import re
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
from check_python import frozen_environment, require
import dev_postgres


def runner_authorization(path, action='owned-synthetic-postgresql-outage'):
    """Match operator-supplied runner scope; never infer authority from privileges."""
    require(path is not None, 'PENDING_OFF_HOST: independent runner unassigned; use core-local for ordinary checks')
    path = Path(path)
    require(path.is_file() and not path.is_symlink() and path.stat().st_size < 16384,
            'bounded runner authorization file required')
    data = json.loads(path.read_text())
    expected = {'schema', 'runner_id', 'machine_id_sha256', 'checkout_commit', 'permitted_actions', 'synthetic_only', 'independent_of_mx1'}
    require(isinstance(data, dict) and set(data) == expected and data['schema'] == 1,
            'closed runner authorization schema required')
    require(data['synthetic_only'] is True and data['independent_of_mx1'] is True,
            'independent synthetic runner scope required')
    require(isinstance(data['runner_id'], str) and 1 <= len(data['runner_id']) <= 128,
            'runner identity required')
    hostname = socket.gethostname().lower()
    require(not any(x in hostname for x in ('mx1', 'claude-dev')), 'protected environment cannot execute fault tests')
    machine = Path('/etc/machine-id').read_bytes().strip()
    require(bool(machine) and data['machine_id_sha256'] == hashlib.sha256(machine).hexdigest(),
            'runner machine identity mismatch')
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True, timeout=5).strip()
    require(data['checkout_commit'] == commit, 'runner authorization must name exact checkout commit')
    require(data['permitted_actions'] == [action], 'exact fault scope required')
    return data


def run(argv, env, timeout=30):
    result = dev_postgres.run(list(map(str, argv)), env=env, cwd=ROOT / 'backend', timeout=timeout)
    return result.stdout


def get(port, path, method='GET', host=None):
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    request = urllib.request.Request(f'http://127.0.0.1:{port}{path}', method=method)
    if host:
        request.add_header('Host', host)
    try:
        response = opener.open(request, timeout=4)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        body = response.read(8193)
        require(len(body) <= 8192, 'unbounded health response')
        return response.status, body, response.headers.get('Content-Type', '')


@contextlib.contextmanager
def gunicorn(python, env, scratch, *, probe_path='/health/live', probe_host=None):
    with socket.socket() as reservation:
        reservation.bind(('127.0.0.1', 0))
        port = reservation.getsockname()[1]
    with (scratch / 'gunicorn.log').open('w+') as log:
        process = subprocess.Popen([str(python), '-m', 'gunicorn', 'shop.wsgi:application',
            '--bind', f'127.0.0.1:{port}', '--workers', '1', '--threads', '1', '--timeout', '5',
            '--graceful-timeout', '2', '--max-requests', '100'], env=env, cwd=ROOT / 'backend',
            stdout=log, stderr=log, start_new_session=True)
        try:
            deadline = time.monotonic() + 15
            while True:
                require(process.poll() is None, 'owned Gunicorn exited before readiness')
                try:
                    if get(port, probe_path, host=probe_host)[0] == 200:
                        break
                except (OSError, urllib.error.URLError):
                    pass
                require(time.monotonic() < deadline, 'bounded Gunicorn startup expired')
                time.sleep(0.05)
            yield port
        finally:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=5)


def qualify(faults=False):
    started = time.monotonic()
    parent = Path(os.environ.get('SHOP_TEST_SCRATCH', ROOT / '.scratch'))
    require(not parent.is_symlink() and parent.is_dir(), 'existing owned scratch parent required')
    parent = parent.resolve()
    # libpq Unix socket names have a strict platform length limit. Fail before initdb.
    require(len(str(parent)) + 50 < 108, 'scratch path too long for PostgreSQL sockets; set SHOP_TEST_SCRATCH to a short owned directory')
    dev_postgres.SCRATCH_PARENT = parent
    with tempfile.TemporaryDirectory(prefix='backend-', dir=parent) as directory:
        scratch = Path(directory)
        with frozen_environment('runtime', scratch / 'runtime') as (python, env, expected):
            env['SHOP_POSTGRES_BIN'] = os.environ['SHOP_POSTGRES_BIN']
            env.update(DJANGO_SETTINGS_MODULE='shop.config.synthetic', SHOP_ENV='synthetic',
                       LIVE_PAYMENTS_ENABLED='false', PAYMENT_ADAPTER='fake', MAIL_ADAPTER='fake', STORAGE_ADAPTER='fake')
            with dev_postgres.isolated_postgres() as pg:
                database = pg.create_database()
                for key, value in database.items():
                    env['DATABASE_' + key] = value
                identity = pg.sql("SELECT current_setting('server_version'), current_database(), current_setting('server_encoding')", database['NAME'])
                require(identity == '18.6|' + database['NAME'] + '|UTF8', 'actual scratch database identity mismatch')
                run([python, 'manage.py', 'check'], env)
                run([python, 'manage.py', 'migrate', '--noinput'], env)
                run([python, 'manage.py', 'makemigrations', '--check', '--dry-run'], env)
                # Keep the finite per-process bound as the suite grows; each batch
                # creates/destroys its own test DB in the same owned scratch cluster.
                labels = ['shop.core.tests', 'shop.catalog.tests', 'shop.access.tests', 'shop.catalog.cart_tests', 'shop.catalog.quotation_tests', 'shop.access.staff_tests', 'shop.access.review_tests', 'shop.catalog.business_tests', 'shop.catalog.binding_tests', 'shop.catalog.document_tests', 'shop.catalog.timeline_tests', 'shop.access.preparation_tests', 'shop.access.preparation_snapshot_tests', 'shop.access.comparison_tests', 'shop.access.workflow_audit_tests', 'shop.access.journey_tests', 'shop.access.customer_portal_tests', 'shop.catalog.quotation_history_tests', 'shop.catalog.cart_editor_tests', 'shop.catalog.quotation_capture_tests', 'shop.adapters.evidence_archive_tests', 'shop.catalog.request_envelope_tests', 'shop.catalog.envelope_capture_tests', 'shop.adapters.archive_destination_tests', 'shop.catalog.archive_binding_tests', 'shop.catalog.archive_authority_tests', 'shop.catalog.archive_inspection_tests', 'shop.catalog.archive_claim_tests', 'shop.catalog.archive_publication_tests', 'shop.catalog.archive_reconciliation_tests', 'shop.worker.prepared_tests', 'shop.worker.prepared_command_tests', 'shop.access.archive_observation_tests', 'shop.access.request_evidence_tests', 'shop.access.staff_navigation_tests', 'shop.payments.tests', 'shop.payments.attempt_tests', 'shop.payments.recovery_command_tests','shop.payments.control_tests', 'shop.payments.purchase_flow_tests', 'shop.catalog.checkout_tests', 'shop.catalog.checkout_payment_tests', 'shop.catalog.fulfilment_tests', 'shop.catalog.support_ledger_tests', 'shop.catalog.private_package_tests', 'shop.catalog.licence_change_tests', 'shop.catalog.document_number_tests', 'shop.worker.statement_mail_tests']
                checks, tests = 4, 0
                for batch in (labels[:25], labels[25:]):
                    test_result = dev_postgres.run([str(python), 'manage.py', 'test', *batch, '--noinput'],
                        env=env, cwd=ROOT / 'backend', timeout=120)
                    test_output = test_result.stdout + test_result.stderr
                    match = re.search(r'Ran (\d+) tests?', test_output)
                    require(match is not None and int(match[1]) >= 5 and 'OK' in test_output and 'skipped' not in test_output,
                            'required Django configuration tests missing, failed or skipped')
                    tests += int(match[1])
                with gunicorn(python, env, scratch) as port:
                    for path, status, body in [('/health/live', 200, {'status': 'live'}),
                                               ('/health/ready', 200, {'status': 'ready'})]:
                        code, raw, content_type = get(port, path)
                        require(code == status and json.loads(raw) == body and content_type.startswith('application/json'), 'health contract mismatch')
                        tests += 1
                    # Product capabilities are tested directly; future commerce routes
                    # are no longer required to remain skeleton 404s.
                    for path, status in (
                        ('/api/v1/catalog/', 200),
                        ('/purchase/simple/', 200),
                        ('/purchase/access/', 200),
                        ('/purchase/cart/', 401),
                        ('/purchase/quotations/', 401),
                        ('/purchase/request-quotation/', 401),
                        ('/api/v1/configurations/validate/', 405),
                        ('/api/v1/configuration-drafts/00000000-0000-0000-0000-000000000001/', 401),
                        ('/admin/', 404)):
                        require(get(port, path)[0] == status, 'product/authentication boundary mismatch')
                        tests += 1
                    require(get(port, '/health/live', method='POST')[0] == 405, 'liveness must be GET-only')
                    require(get(port, '/health/ready', method='POST')[0] == 405, 'readiness must be GET-only')
                    require(get(port, '/health/live', host='unexpected.invalid')[0] == 400, 'unapproved host accepted')
                    tests += 3
                    if faults:
                        # Only this newly created token-validated cluster; never discover host services.
                        pg.command('pg_ctl', '-D', pg.root / 'data', '-m', 'fast', '-w', '-t', '15', 'stop')
                        try:
                            before = time.monotonic()
                            status, raw, _ = get(port, '/health/ready')
                            require(status == 503 and json.loads(raw) == {'status': 'unavailable'}, 'outage contract mismatch')
                            require(time.monotonic() - before < 4, 'outage response exceeded bound')
                            require(get(port, '/health/live')[0] == 200, 'DB outage changed liveness')
                            tests += 3
                        finally:
                            pg.command('pg_ctl', '-D', pg.root / 'data', '-l', pg.root / 'server.log',
                                '-o', f"-k {pg.socket} -h ''", '-w', '-t', '15', 'start')
                        require(get(port, '/health/ready')[0] == 200, 'scratch DB recovery failed')
                        tests += 1
                log_output = (scratch / 'gunicorn.log').read_text()
                require('"event":"health.ready"' in log_output and '"event":"health.live"' in log_output,
                        'real request safe events missing')
                checks += 1
                marker = 'CORE_PASS' if faults else 'CORE_LOCAL_PASS'
                print(f'{marker} checks={checks} tests={tests} duration_seconds={time.monotonic()-started:.3f}')
                if not faults:
                    print('PENDING_OFF_HOST: database outage/recovery unexecuted; full core qualification pending')


def qualify_adapters():
    from check_worker import prepared_database, manage
    started = time.monotonic()
    with prepared_database() as (python, env, pg, database, scratch):
        manage(python, env, 'migrate', '--noinput')
        manage(python, env, 'makemigrations', '--check', '--dry-run')
        env['SHOP_ADAPTER_NETWORK_ISOLATED'] = '1'
        env['RES_OPTIONS'] = 'attempts:1 timeout:1'
        result = dev_postgres.run(['unshare', '--net', '--', str(python), 'manage.py', 'test',
            'shop.adapters.tests', '--noinput'], env=env, cwd=ROOT / 'backend', timeout=45)
        output = result.stdout + result.stderr
        count = re.search(r'Ran (\d+) tests?', output)
        require(count is not None and int(count[1]) >= 6 and 'OK' in output and 'skipped' not in output,
                'required isolated adapter tests absent, failed or skipped')
    print(f'ADAPTERS_PASS checks=3 tests={int(count[1])} duration_seconds={time.monotonic()-started:.3f}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('lane', choices=('core', 'core-local', 'adapters'))
    parser.add_argument('--runner-authorization', type=Path)
    args = parser.parse_args()
    if args.lane == 'adapters':
        require((ROOT / 'backend/shop/adapters/tests.py').is_file(), 'required adapter producer missing until 02-11')
        require(args.runner_authorization is None, 'adapter fixtures do not use fault authorization')
        qualify_adapters()
        return
    if args.lane == 'core':
        runner_authorization(args.runner_authorization or os.environ.get("SHOP_CORE_RUNNER_AUTHORIZATION"))
    elif args.runner_authorization:
        raise ValueError('runner authorization is only valid for the full core lane')
    qualify(faults=args.lane == 'core')

if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        print('BACKEND_FAIL: ' + str(error), file=sys.stderr)
        raise SystemExit(1)
