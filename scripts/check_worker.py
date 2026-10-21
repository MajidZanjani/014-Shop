#!/usr/bin/env python3
"""Counted synthetic PostgreSQL enqueue/worker producer; no host DB discovery."""
import argparse
from contextlib import contextmanager
import json
import os
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--enqueue-only', action='store_true')
    parser.add_argument('lane', nargs='?', choices=('worker-smoke', 'worker-local', 'worker'))
    args = parser.parse_args()
    require(args.enqueue_only and args.lane is None, 'worker execution producer pending 02-10')
    started = time.monotonic()
    with prepared_database() as (python, env, pg, database, scratch):
        checks, tests, row = enqueue_checks(python, env, pg, database)
    print(f'ENQUEUE_PROBE_PASS checks={checks} tests={tests} duration_seconds={time.monotonic()-started:.3f}')

if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print('WORKER_FAIL: ' + str(error), file=sys.stderr)
        raise SystemExit(1)
