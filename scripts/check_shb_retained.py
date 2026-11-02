#!/usr/bin/env python3
"""Local SHB tests using retained OCI tools; never Nix/runtime/activation qualification.

The normal check_shb.py lane remains required. This fallback verifies retained
archive/layer bytes and actual installed versions, then uses an owned disposable
PostgreSQL with current workspace source. No store registration or host activation.
"""
from contextlib import contextmanager
from pathlib import Path,PurePosixPath
import argparse
import hashlib
import importlib.metadata as metadata
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT/'scripts'))
TOOLS=ROOT/'.scratch/shb-retained-tools'
PYTHON='/nix/store/xnwil746ffmc21qrlznq7inkpn1g4zbs-shop-python-runtime/bin/python'
POSTGRES='/nix/store/r9m7pml7sjm3a91pi63wl06gjiw8ll9v-postgresql-18.6/bin'
ARCHIVES={
    '/nix/store/55fbc919a5fwhyc1gcsn1h6m63s4ipai-shop-postgres.tar.gz':'00ad3ec8402040624e9218f25fed63c5aa62a1a002a07dc3a3a1fab425021067',
    '/nix/store/6xqd75ka2v46ydd4v10wnlvq9kmbicrd-shop-app.tar.gz':'ed1878432d0eb3f75dbd4d122c6510fd0bd1034fd735aaa40ae6508e6fab905d',
}


def recover():
    assert TOOLS.parent.is_dir() and not TOOLS.is_symlink()
    TOOLS.mkdir(exist_ok=True)
    records=[]
    for name,digest in ARCHIVES.items():
        source=Path(name)
        with source.open('rb') as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==digest
        with tarfile.open(source) as archive:
            manifests=json.load(archive.extractfile('manifest.json'));assert len(manifests)==1
            manifest=manifests[0]
            config_raw=archive.extractfile(manifest['Config']).read()
            assert hashlib.sha256(config_raw).hexdigest()==Path(manifest['Config']).stem
            config=json.loads(config_raw)
            for layer,expected in zip(manifest['Layers'],config['rootfs']['diff_ids'],strict=True):
                with archive.extractfile(layer) as stream:assert expected=='sha256:'+hashlib.file_digest(stream,'sha256').hexdigest()
                with tarfile.open(fileobj=archive.extractfile(layer)) as entries:
                    for item in entries:
                        parts=PurePosixPath(item.name.lstrip('/')).parts
                        if parts[:2]!=('nix','store') or len(parts)<3:continue
                        assert '..' not in parts
                        dest=TOOLS.joinpath(*parts)
                        assert not any(p.is_symlink() for p in dest.parents if p!=TOOLS.parent)
                        if item.isdir():dest.mkdir(parents=True,exist_ok=True);continue
                        dest.parent.mkdir(parents=True,exist_ok=True)
                        if item.issym():
                            if dest.is_symlink():assert os.readlink(dest)==item.linkname
                            else:assert not dest.exists();dest.symlink_to(item.linkname)
                        elif item.isfile():
                            raw=entries.extractfile(item).read()
                            if dest.exists():assert not dest.is_symlink() and dest.read_bytes()==raw and dest.stat().st_mode&0o777==item.mode&0o777
                            else:dest.write_bytes(raw);dest.chmod(item.mode&0o777)
                        elif item.islnk():
                            target=TOOLS/item.linkname.lstrip('/')
                            assert '..' not in PurePosixPath(item.linkname).parts and target.is_relative_to(TOOLS) and not target.is_symlink() and target.is_file()
                            if dest.exists():assert not dest.is_symlink() and dest.read_bytes()==target.read_bytes()
                            else:shutil.copyfile(target,dest);dest.chmod(item.mode&0o777)
                        else:raise ValueError('unsupported retained entry')
            records.append({'source':name,'sha256':digest,'config':manifest['Config'],'layers_verified':len(manifest['Layers'])})
    (TOOLS/'records.json').write_text(json.dumps(records,indent=2)+'\n')
    print('RETAINED_SHB_TOOLS archives=2 layers=91 host_store_changed=false nix_environment_qualified=false',flush=True)


def run(command,env,timeout=180):
    result=subprocess.run(command,env=env,cwd=ROOT/'backend',text=True,capture_output=True,timeout=timeout)
    if result.returncode:
        sys.stderr.write(result.stdout+result.stderr)
        raise subprocess.CalledProcessError(result.returncode,command)
    return result.stdout+result.stderr


@contextmanager
def retained_database():
    import dev_postgres
    dev_postgres.SCRATCH_PARENT=ROOT/'.scratch'
    with tempfile.TemporaryDirectory(prefix='shb-retained-db-',dir=ROOT/'.scratch') as temporary:
        scratch=Path(temporary)
        env={key:os.environ[key] for key in ('PATH','LANG','PYTHONPATH','LD_LIBRARY_PATH','PSYCOPG_IMPL','PYTHONDONTWRITEBYTECODE','PYTHONNOUSERSITE') if key in os.environ}
        env.update(DJANGO_SETTINGS_MODULE='shop.config.synthetic',SHOP_ENV='synthetic',LIVE_PAYMENTS_ENABLED='false',
            PAYMENT_ADAPTER='fake',MAIL_ADAPTER='fake',STORAGE_ADAPTER='fake',PYTHONPATH=env.get('PYTHONPATH','')+':'+str(ROOT/'backend'))
        with dev_postgres.isolated_postgres() as pg:
            database=pg.create_database();env.update({'DATABASE_'+k:v for k,v in database.items()})
            assert pg.sql("SELECT current_setting('server_version')",database['NAME'])=='18.6'
            yield Path(sys.executable),env,pg,database,scratch


def source_snapshot():
    assets={'shop/catalog/revision.json','shop/catalog/document_preview.json','shop/catalog/shop.css','shop/shb/revision.json','shop/shb/shop.css'}
    files={}
    for path in (ROOT/'backend').rglob('*'):
        name=path.relative_to(ROOT/'backend').as_posix()
        if path.is_file() and (path.suffix=='.py' or name in assets or path.suffix=='.html' and name.startswith(('shop/catalog/templates/','shop/access/templates/','shop/shb/templates/'))):
            assert not path.is_symlink();files['backend/'+name]=hashlib.sha256(path.read_bytes()).hexdigest()
    for name in ('check_shb.py','check_shb_retained.py','demo_shb.py','browser_shb.mjs','check_worker.py','dev_postgres.py','check_backend.py','check_python.py'):
        files['scripts/'+name]=hashlib.sha256((ROOT/'scripts'/name).read_bytes()).hexdigest()
    return files


def save_record(before,result):
    assert before==source_snapshot(),'source changed during retained verification'
    from datetime import datetime,timezone
    record={'schema':1,'evidence_class':'local-synthetic-retained-tools','timestamp':datetime.now(timezone.utc).isoformat(),
        'archives':ARCHIVES,'python':'3.13.16','django':'5.2.18','postgres':'18.6','libpq':180006,'source_files':before,
        'result':result,'nix_environment_qualified':False,'runtime_qualified':False,'production_activation':False}
    raw=(json.dumps(record,sort_keys=True,indent=2)+'\n').encode()
    digest=hashlib.sha256(raw).hexdigest();directory=ROOT/'docs/evidence/shb/retained-tests';directory.mkdir(exist_ok=True)
    path=directory/(digest+'.json');path.write_bytes(raw)
    print('RETAINED_SHB_EVIDENCE '+str(path.relative_to(ROOT)),flush=True)


def inside(args):
    from check_python import read_lock
    from psycopg import pq
    assert platform.python_version()=='3.13.16' and pq.version()==180006 and pq.__impl__=='python'
    expected=read_lock(ROOT/'backend/requirements/runtime-linux-py313.txt')
    installed=list(metadata.distributions())
    actual={dist.metadata['Name'].lower().replace('_','-').replace('.','-'):dist.version for dist in installed}
    assert actual=={name:value['version'] for name,value in expected.items()}
    assert all(dist.version==actual[dist.metadata['Name'].lower().replace('_','-').replace('.','-')] for dist in installed)
    print('RETAINED_SHB_RUNTIME python=3.13.16 django=5.2.18 postgres=18.6 libpq=180006 installed_inventory=locked nix_environment_qualified=false',flush=True)
    before=source_snapshot()
    if args.browser:
        assert args.release and args.browser_binary and args.browser_node
        # These are actual local browser versions, recorded separately from pinned qualification.
        browser=str(Path(args.browser_binary).resolve());node=str(Path(args.browser_node).resolve())
        assert browser.startswith('/nix/store/') and node.startswith('/nix/store/')
        browser_version=subprocess.check_output([browser,'--version'],text=True,timeout=10).strip()
        node_version=subprocess.check_output([node,'-p','process.versions.node'],text=True,timeout=10).strip()
        os.environ.update(SHOP_BROWSER=browser,SHOP_NODE=node,SHOP_BROWSER_VERSION=browser_version,SHOP_BROWSER_NODE_VERSION=node_version)
        import demo_shb
        demo_shb.prepared_database=retained_database
        evidence=Path(tempfile.mkdtemp(prefix='shb-checkout-browser-',dir=ROOT/'.scratch'))
        sys.argv=[sys.argv[0],'--check','--browser','--release',str(args.release),'--screenshot-root',str(evidence)]
        print('RETAINED_SHB_BROWSER_EVIDENCE '+str(evidence),flush=True)
        try:report=demo_shb.main()
        except subprocess.CalledProcessError as error:
            stage=re.search(r'SHB_BROWSER_FAIL stage=([a-z-]+)',error.stderr or '')
            raise SystemExit('RETAINED_SHB_BROWSER_FAIL'+(' stage='+stage[1] if stage else ' owned fixture command failed')) from None
        save_record(before,{'kind':'browser','browser':browser_version,'node':node_version,'evidence_directory':str(evidence),'observed':report})
        return
    started=time.monotonic();total=0
    suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_shb_*.py')
    result=unittest.TextTestRunner(verbosity=1).run(suite)
    assert result.wasSuccessful() and not result.skipped and result.testsRun>=9
    total+=result.testsRun
    labels=[['shop.shb.tests','shop.shb.discount_tests','shop.shb.review_tests','shop.shb.checkout_tests','shop.shb.paid_order_tests','shop.shb.closure_tests','shop.shb.offer_tests','shop.shb.lifecycle_tests','shop.shb.notification_tests','shop.shb.revision_tests','shop.shb.recovery_tests','shop.shb.financial_tests']]
    if args.shared:
        labels.extend([
            ['shop.core.tests','shop.access.tests','shop.access.staff_tests','shop.access.recovery_tests','shop.access.effect_tests','shop.access.startup_tests','shop.access.staff_restore_tests','shop.access.authentication_recovery_tests'],
            ['shop.payments.tests','shop.payments.attempt_tests','shop.payments.control_tests','shop.payments.notification_tests','shop.payments.observation_tests','shop.payments.operation_tests','shop.payments.overpayment_tests'],
            ['shop.access.review_tests','shop.access.staff_navigation_tests','shop.access.preparation_tests'],
                ['shop.worker.tests.OwnershipTests','shop.worker.statement_mail_tests'],
            ['shop.catalog.checkout_tests','shop.catalog.checkout_payment_tests','shop.catalog.fulfilment_tests','shop.adapters.evidence_archive_tests'],
        ])
    with retained_database() as (python,env,pg,database,scratch):
        for argv in (['check'],['migrate','--noinput'],['makemigrations','--check','--dry-run']):run([str(python),'manage.py',*argv],env)
        print('RETAINED_SHB_SCHEMA_PASS check=true migrate=true makemigrations_clean=true',flush=True)
        for batch in labels:
            batch_env=env
            if 'shop.catalog.checkout_tests' in batch:
                # Exercise preserved legacy services/HTTP checks in isolation from
                # the new-sale route closure. Production settings/routes stay closed;
                # the SHB suite separately proves that closure on the actual boundary.
                from check_shb import legacy_transaction_environment
                batch_env=legacy_transaction_environment(env,scratch)
            output=run([str(python),'manage.py','test',*batch,'--noinput','--keepdb'],batch_env)
            count=re.search(r'Ran (\d+) tests?',output)
            assert count and 'OK' in output and 'skipped' not in output
            total+=int(count[1]);print('RETAINED_SHB_BATCH_PASS tests='+count[1]+' labels='+','.join(batch),flush=True)
        if args.shared:
            network_env=dict(env,SHOP_ADAPTER_NETWORK_ISOLATED='1',RES_OPTIONS='attempts:1 timeout:1')
            output=run(['unshare','--net',str(python),'manage.py','test','shop.adapters.tests','--noinput','--keepdb'],network_env)
            assert 'Ran 6 tests' in output and 'OK' in output and 'skipped' not in output
            total+=6;print('RETAINED_SHB_ADAPTER_PASS tests=6 actual_unshare_net=true',flush=True)
    save_record(before,{'kind':'postgresql-tests','tests':total,'shared':args.shared,'schema_consistent':True})
    print(f'RETAINED_SHB_TEST_PASS tests={total} duration_seconds={time.monotonic()-started:.3f} evidence=local-synthetic nix_environment_qualified=false',flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inside',action='store_true',help=argparse.SUPPRESS)
    parser.add_argument('--shared',action='store_true')
    parser.add_argument('--browser',action='store_true')
    parser.add_argument('--release',type=Path)
    parser.add_argument('--browser-binary')
    parser.add_argument('--browser-node')
    args=parser.parse_args()
    if args.inside:return inside(args)
    recover()
    command=['bwrap','--die-with-parent','--ro-bind','/','/',
        '--overlay-src','/nix/store','--overlay-src',str(TOOLS/'nix/store'),'--ro-overlay','/nix/store',
        '--bind',str(ROOT),str(ROOT),'--bind','/tmp','/tmp','--proc','/proc','--dev','/dev','--clearenv',
        '--setenv','SHOP_POSTGRES_BIN',POSTGRES,'--setenv','PATH',POSTGRES+':/run/current-system/sw/bin:/usr/bin:/bin',
        '--',PYTHON,str(Path(__file__).resolve()),'--inside',*sys.argv[1:]]
    raise SystemExit(subprocess.run(command,cwd=ROOT).returncode)


if __name__=='__main__':main()
