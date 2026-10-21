#!/usr/bin/env python3
"""Offline versioned contracts with actual synthetic HTTP/worker observations."""
import argparse
import datetime
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
SCHEMA_HASH = 'da01ba28852cac0de53893797cb8d1942bc3b05084f526dcc216717dec314ed0'


def load(path):
    raw = Path(path).read_bytes()
    if len(raw) > 1000000: raise ValueError('bounded contract required')
    return json.loads(raw)


def no_remote_refs(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if key in ('$ref', '$dynamicRef') and isinstance(item, str) and not item.startswith('#'):
                raise ValueError('remote reference forbidden')
            no_remote_refs(item)
    elif isinstance(value, list):
        for item in value: no_remote_refs(item)


def validator(schema):
    from jsonschema import Draft202012Validator, FormatChecker
    from referencing import Registry
    def denied(uri): raise ValueError('offline reference unavailable')
    no_remote_refs(schema)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, registry=Registry(retrieve=denied), format_checker=FormatChecker())


def contracts():
    vendor = ROOT / 'api/vendor/openapi-3.1.schema.json'
    if hashlib.sha256(vendor.read_bytes()).hexdigest() != SCHEMA_HASH:
        raise ValueError('official OpenAPI schema bytes changed')
    api = load(ROOT / 'api/v1/openapi.json')
    validator(load(vendor)).validate(api)
    if api['openapi'] != '3.1.1' or set(api['paths']) != {'/health/live', '/health/ready'}:
        raise ValueError('narrow versioned health contract required')
    for path, item in api['paths'].items():
        if set(item) != {'get'}: raise ValueError('unexpected contract operation')
        for response in item['get']['responses'].values():
            validator(response['content']['application/json']['schema'])
    probe = validator(load(ROOT / 'schemas/v1/probe.schema.json'))
    return api, probe


def validate_observations(observations):
    api, probe = contracts()
    seen = set()
    for response in observations['responses']:
        path, status = response['path'], str(response['status'])
        if response['content_type'] != 'application/json': raise ValueError('response media mismatch')
        schema = api['paths'][path]['get']['responses'][status]['content']['application/json']['schema']
        validator(schema).validate(response['body'])
        seen.add((path, status))
    if seen != {('/health/live','200'),('/health/ready','200'),('/health/ready','503')}:
        raise ValueError('required observed response absent')
    probe.validate(observations['probe'])
    probe.validate(load(ROOT / 'tests/fixtures/contracts/valid.json'))
    return 7


def environment_examples():
    schema = validator(load(ROOT / 'schemas/v1/environment.schema.json'))
    for mode in ('local', 'synthetic', 'bank-sandbox', 'production'):
        values = {}
        for line in (ROOT / 'ops/config' / (mode + '.example')).read_text().splitlines():
            if not line or line.startswith('#'): continue
            key, value = line.split('=', 1)
            if key in values: raise ValueError('duplicate template field')
            values[key] = value
        schema.validate({'schema_version': 1, 'values': values})
    return 4


def artifact_record(command, counts, started_at, duration):
    def identity(path):
        return {'path': path, 'sha256': hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}
    commit = subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True,timeout=5).strip()
    dirty = bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True,timeout=5))
    import platform
    return {'schema_version':1,'evidence_class':'local-synthetic','source':{'commit':commit,'dirty':dirty},
        'tools':{'python':platform.python_version()},
        'locks':[identity('backend/requirements/tools-linux-py313.txt'),identity('backend/requirements/runtime-linux-py313.txt')],
        'command':command,'exit_code':0,'checks':counts['checks'],'tests':counts['tests'],
        'started_at':started_at,'duration_seconds':duration,
        'artifacts':[identity('api/v1/openapi.json'),identity('schemas/v1/probe.schema.json')]}


def validate_file(path):
    checks = validate_observations(load(path)) + environment_examples()
    import unittest
    suite = unittest.TestLoader().discover(str(ROOT / 'tests'), pattern='test_contracts.py')
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream).run(suite)
    if result.testsRun < 5 or not result.wasSuccessful() or result.skipped:
        raise ValueError('contract rejection tests failed or missing: ' + stream.getvalue())
    print(json.dumps({'checks':checks,'tests':result.testsRun}))


def qualify(local, authorization):
    from check_python import frozen_environment
    from check_backend import runner_authorization, gunicorn, get
    from check_worker import prepared_database, manage
    if not local: runner_authorization(authorization)
    elif authorization is not None: raise ValueError('local subset cannot accept fault authorization')
    start = time.monotonic()
    started_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    parent = ROOT / '.scratch'; parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='contracts-',dir=parent) as directory:
        scratch = Path(directory)
        with prepared_database() as (python,env,pg,database,runtime_scratch):
            manage(python,env,'migrate','--noinput')
            request = {'payload_version':1,'evidence_class':'local-synthetic'}
            row = json.loads(manage(python,env,'enqueue_probe','--payload',json.dumps(request)).stdout)
            manage(python,env,'run_worker','--once')
            result = json.loads(pg.sql("SELECT json_build_object('effect_id', effect_id, 'outcome', result->>'outcome') FROM worker_probe", database['NAME']))
            observations = {'responses':[], 'probe':{'request':request,'result':result}}
            with gunicorn(python,env,scratch) as port:
                for name in ('live','ready'):
                    status,body,content = get(port,'/health/'+name)
                    observations['responses'].append({'path':'/health/'+name,'status':status,'content_type':content,'body':json.loads(body)})
                if local:
                    code = '''import django,json;django.setup()
from unittest.mock import patch
from django.db import DatabaseError
from django.test import RequestFactory
from shop.core.health import readiness
with patch('shop.core.health.connection') as conn:
 conn.cursor.side_effect=DatabaseError('synthetic-only')
 r=readiness(RequestFactory().get('/health/ready',HTTP_HOST='127.0.0.1'))
 print(json.dumps({'path':'/health/ready','status':r.status_code,'content_type':r['Content-Type'],'body':json.loads(r.content)}))
'''
                    import dev_postgres
                    observed = dev_postgres.run([str(python),'-c',code],cwd=ROOT/'backend',env=env,timeout=10)
                    observations['responses'].append(json.loads(observed.stdout))
                else:
                    pg.command('pg_ctl','-D',pg.root/'data','-m','fast','-w','-t','15','stop')
                    try:
                        status,body,content = get(port,'/health/ready')
                        observations['responses'].append({'path':'/health/ready','status':status,'content_type':content,'body':json.loads(body)})
                    finally:
                        pg.command('pg_ctl','-D',pg.root/'data','-l',pg.root/'server.log','-o',f"-k {pg.socket} -h ''",'-w','-t','15','start')
        path=scratch/'observed.json';path.write_text(json.dumps(observations))
        with frozen_environment('tools',scratch/'tools') as (python,env,expected):
            # Offline validation/tests get an isolated network namespace as well as denied refs.
            completed=subprocess.run(['unshare','--net','--',str(python),str(Path(__file__).resolve()),'--validate-file',str(path)],
                env=env,cwd=ROOT,capture_output=True,text=True,timeout=30,check=True)
            counts=json.loads(completed.stdout)
            record = artifact_record(['unshare', '--net', '--', str(python), str(Path(__file__).resolve()), '--validate-file', str(path)],
                counts, started_at, time.monotonic()-start)
            manifest = scratch/'artifact-record.json';manifest.write_text(json.dumps(record))
            check = 'import sys;sys.path.insert(0,sys.argv[1]);from check_contracts import validator,load,ROOT;validator(load(ROOT/"schemas/v1/artifact-manifest.schema.json")).validate(load(sys.argv[2]))'
            subprocess.run(['unshare','--net','--',str(python),'-c',check,str(ROOT/'scripts'),str(manifest)],
                cwd=ROOT,env=env,capture_output=True,text=True,timeout=15,check=True)
            counts['checks'] += 1
    marker='CONTRACTS_LOCAL_PASS' if local else 'CONTRACTS_PASS'
    print(f'{marker} checks={counts["checks"]} tests={counts["tests"]} duration_seconds={time.monotonic()-start:.3f}')
    if local: print('PENDING_OFF_HOST: 503 is a synthetic handler exception, not actual HTTP database-outage evidence')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--local',action='store_true');p.add_argument('--runner-authorization',type=Path);p.add_argument('--validate-file',type=Path);a=p.parse_args()
    if a.validate_file: validate_file(a.validate_file)
    else: qualify(a.local,a.runner_authorization or (os.environ.get('SHOP_CONTRACTS_RUNNER_AUTHORIZATION') if not a.local else None))

if __name__=='__main__':
    try: main()
    except (ValueError,OSError,subprocess.SubprocessError) as error:
        print('CONTRACTS_FAIL: '+str(error),file=sys.stderr);raise SystemExit(1)
