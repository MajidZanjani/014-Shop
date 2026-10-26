#!/usr/bin/env python3
"""Counted synthetic PostgreSQL enqueue/worker producer; no host DB discovery."""
import argparse
from contextlib import contextmanager
import json
import os
import re
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import uuid
sys.dont_write_bytecode = True
from check_python import frozen_environment, require
import dev_postgres
ROOT = Path(__file__).resolve().parents[1]


@contextmanager
def prepared_database():
    parent = Path(os.environ.get('SHOP_TEST_SCRATCH', ROOT / '.scratch'))
    require(parent.is_dir() and not parent.is_symlink(), 'existing owned scratch parent required')
    parent = parent.resolve()
    require(len(str(parent)) + 50 < 108, 'short owned SHOP_TEST_SCRATCH required for Unix sockets')
    dev_postgres.SCRATCH_PARENT = parent
    with tempfile.TemporaryDirectory(prefix='worker-', dir=parent) as directory:
        scratch = Path(directory)
        with frozen_environment('runtime', scratch / 'runtime') as (python, env, expected):
            env.update(DJANGO_SETTINGS_MODULE='shop.config.synthetic', SHOP_ENV='synthetic',
                       LIVE_PAYMENTS_ENABLED='false', PAYMENT_ADAPTER='fake', MAIL_ADAPTER='fake', STORAGE_ADAPTER='fake')
            with dev_postgres.isolated_postgres() as pg:
                database = pg.create_database()
                env.update({'DATABASE_' + key: value for key, value in database.items()})
                require(pg.sql("SELECT current_setting('server_version')", database['NAME']) == '18.6', 'real PostgreSQL required')
                yield python, env, pg, database, scratch


def manage(python, env, *args, timeout=30):
    return dev_postgres.run([str(python), 'manage.py', *args], env=env, cwd=ROOT / 'backend', timeout=timeout)


def enqueue_checks(python, env, pg, database):
    manage(python, env, 'migrate', '--noinput')
    manage(python, env, 'makemigrations', '--check', '--dry-run')
    payload = json.dumps({'payload_version': 1, 'evidence_class': 'local-synthetic'})
    row = json.loads(manage(python, env, 'enqueue_probe', '--payload', payload).stdout)
    identity, effect = str(uuid.UUID(row['id'])), str(uuid.UUID(row['effect_id']))
    data = pg.sql(f"SELECT payload_version, evidence_class, state, effect_id, attempts, result FROM worker_probe WHERE id='{identity}'", database['NAME'])
    require(data == f'1|local-synthetic|pending|{effect}|0|{{}}', 'separate connection persisted row mismatch')
    tests = 1
    for invalid in ('{', '[]', '{"payload_version":2,"evidence_class":"local-synthetic"}',
                    '{"payload_version":true,"evidence_class":"local-synthetic"}',
                    '{"payload_version":1,"evidence_class":"actual-ovh"}',
                    '{"payload_version":1,"evidence_class":"local-synthetic","extra":1}',
                    '{"payload_version":1,"payload_version":1}', 'x' * 1025):
        try:
            manage(python, env, 'enqueue_probe', '--payload', invalid)
        except subprocess.CalledProcessError:
            tests += 1
        else:
            raise ValueError('invalid enqueue payload accepted')
    require(pg.sql('SELECT count(*) FROM worker_probe', database['NAME']) == '1', 'invalid payload persisted')
    # Real uniqueness errors on independent psql sessions, not model metadata inspection.
    for statement in (
        f"INSERT INTO worker_probe SELECT gen_random_uuid(), payload_version, evidence_class, state, effect_id, claim_token, lease_until, attempts, result FROM worker_probe WHERE id='{identity}'",
        f"INSERT INTO worker_fakereceipt VALUES ('{effect}', 'ok', 'synthetic-ok'), ('{effect}', 'ok', 'synthetic-ok')"):
        try:
            pg.sql(statement, database['NAME'])
        except subprocess.CalledProcessError as error:
            require('duplicate key value violates unique constraint' in error.stderr, 'uniqueness control failed for another reason')
            tests += 1
        else:
            raise ValueError('duplicate effect identity accepted')
    return 4, tests, row


def worker_checks(python, env, pg, database, *, full=False):
    manage(python, env, 'run_worker', '--once')
    require(pg.sql("SELECT state || '|' || (result->>'outcome') FROM worker_probe", database['NAME']) == 'complete|synthetic-ok', 'worker completion absent')
    manage(python, env, 'run_worker', '--once')
    require(pg.sql('SELECT count(*) FROM worker_fakereceipt', database['NAME']) == '1', 'worker receipt not stable')
    for option in ('--lease-seconds', '--max-attempts'):
        try:
            manage(python, env, 'run_worker', '--once', option, '0')
        except subprocess.CalledProcessError:
            pass
        else:
            raise ValueError('unbounded worker argument accepted')
    # This database belongs to one fresh disposable cluster. The outer context
    # destroys it; avoid DROP DATABASE hitting the application's 1s statement limit.
    args = ['test', 'shop.worker.tests', '--noinput', '--keepdb']
    if full:
        env['SHOP_OFFHOST_WORKER_AUTHORIZED'] = '1'
    else:
        args.extend(['--exclude-tag', 'offhost'])
    result = manage(python, env, *args, timeout=60)
    output = result.stdout + result.stderr
    count = re.search(r'Ran (\d+) tests?', output)
    require(count is not None and int(count[1]) >= 7 and 'OK' in output and 'skipped' not in output,
            'required PostgreSQL ownership tests missing, failed or skipped')
    return 2, 4 + int(count[1])


def mutation_checks(python, env, scratch):
    """Prove focused tests reject broken controls in a disposable source copy."""
    backend = scratch / 'mutation-backend'
    source_root = ROOT / 'backend'
    entries = list(source_root.rglob('*'))
    require(not any(path.is_symlink() for path in entries), 'symlink forbidden in mutation source copy')
    # Copy the inert app source allowlist, excluding interpreter caches and tool locks.
    # The old 200-entry bound predates the current 232-file app and counted cache directories.
    def included(path):
        relative = str(path.relative_to(source_root))
        return (path.suffix == '.py'
            or relative in {'shop/catalog/revision.json', 'shop/catalog/document_preview.json', 'shop/catalog/shop.css'}
            or path.suffix == '.html' and relative.startswith(('shop/catalog/templates/', 'shop/access/templates/')))
    files = [path for path in entries if path.is_file() and included(path)]
    require(len(files) <= 512 and sum(path.stat().st_size for path in files) <= 8388608,
            'bounded synthetic backend source copy required')
    for source in files:
        require(source.stat().st_size <= 1048576, 'oversized backend source input')
        target = backend / source.relative_to(source_root)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
    path = backend / 'shop/worker/services.py'
    original = path.read_text()
    fence = original.replace('claim_token=claim.token, lease_until__gt=Now()).update', 'lease_until__gt=Now()).update')
    old = '    result = perform_fake_probe(ProbeRequest(claim.effect_id))\n    complete_probe(claim, result)'
    new = '    with transaction.atomic():\n        Probe.objects.select_for_update().get(pk=claim.probe_id)\n        result = perform_fake_probe(ProbeRequest(claim.effect_id))\n        complete_probe(claim, result)'
    locked = original.replace(old, new)
    require(fence != original and locked != original, 'mutation targets absent')
    for source, case in ((fence, 'test_expiry_takeover_fences_old_token'),
                         (locked, 'test_claim_commits_before_adapter_wait')):
        path.write_text(source)
        try:
            dev_postgres.run([str(python), 'manage.py', 'test', 'shop.worker.tests.OwnershipTests.' + case, '--noinput', '--keepdb'],
                env=env, cwd=backend, timeout=30)
        except subprocess.CalledProcessError as error:
            require('Ran 1 test' in error.stderr and 'FAILED (' in error.stderr, 'mutation did not execute its focused test')
        else:
            raise ValueError('broken worker ownership control accepted')
    return 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--enqueue-only', action='store_true')
    parser.add_argument('--runner-authorization', type=Path)
    parser.add_argument('lane', nargs='?', choices=('worker-smoke', 'worker-local', 'worker'))
    args = parser.parse_args()
    require(bool(args.enqueue_only) != bool(args.lane), 'select enqueue-only or one worker lane')
    if args.lane == 'worker':
        from check_backend import runner_authorization
        runner_authorization(args.runner_authorization or os.environ.get('SHOP_WORKER_RUNNER_AUTHORIZATION'), action='owned-synthetic-worker-interruption')
    else:
        require(args.runner_authorization is None, 'runner authorization only applies to full worker lane')
    started = time.monotonic()
    with prepared_database() as (python, env, pg, database, scratch):
        checks, tests, row = enqueue_checks(python, env, pg, database)
        if args.lane:
            extra_checks, extra_tests = worker_checks(python, env, pg, database, full=args.lane == 'worker')
            checks += extra_checks
            tests += extra_tests
            tests += mutation_checks(python, env, scratch)
    marker = 'ENQUEUE_PROBE_PASS' if args.enqueue_only else {
        'worker-smoke': 'WORKER_SMOKE_PASS', 'worker-local': 'WORKER_LOCAL_PASS', 'worker': 'WORKER_PASS'}[args.lane]
    print(f'{marker} checks={checks} tests={tests} duration_seconds={time.monotonic()-started:.3f}')
    if args.lane in {'worker-local', 'worker-smoke'}:
        print('PENDING_OFF_HOST: forced process interruption/restart unexecuted; full worker qualification pending')

if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print('WORKER_FAIL: ' + str(error), file=sys.stderr)
        raise SystemExit(1)
