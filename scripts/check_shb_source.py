#!/usr/bin/env python3
"""Build/compare/import the actual inert backend source; no live runtime claim."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import tempfile
import time
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
from check_python import frozen_environment


def main():
    started=time.monotonic()
    result=subprocess.run(['nix','build','--offline','./ops/nixos#shop-app-source','--no-link','--json'],cwd=ROOT,text=True,capture_output=True,timeout=180,check=True)
    built=Path(json.loads(result.stdout)[0]['outputs']['out']);app=built/'app'
    assets={'shop/catalog/revision.json','shop/catalog/document_preview.json','shop/catalog/shop.css','shop/shb/revision.json','shop/shb/shop.css'}
    expected={}
    for path in (ROOT/'backend').rglob('*'):
        name=path.relative_to(ROOT/'backend').as_posix()
        if path.is_file() and (path.suffix=='.py' or name in assets or path.suffix=='.html' and name.startswith(('shop/catalog/templates/','shop/access/templates/','shop/shb/templates/'))):
            assert not path.is_symlink();expected[name]=hashlib.sha256(path.read_bytes()).hexdigest()
    actual={}
    for path in app.rglob('*'):
        assert not path.is_symlink()
        if path.is_file():actual[path.relative_to(app).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
    assert expected==actual and len(actual)>250,'exact source/asset identity mismatch'
    with tempfile.TemporaryDirectory(prefix='shb-source-import-',dir=ROOT/'.scratch') as temporary:
        with frozen_environment('runtime',Path(temporary)/'runtime') as (python,env,_):
            env=dict(env,DJANGO_SETTINGS_MODULE='shop.config.synthetic',SHOP_ENV='synthetic',
                LIVE_PAYMENTS_ENABLED='false',PAYMENT_ADAPTER='fake',MAIL_ADAPTER='fake',STORAGE_ADAPTER='fake',
                DATABASE_NAME='synthetic_import_only',DATABASE_USER='synthetic_import_only',DATABASE_HOST='/absent-import-only',DATABASE_PORT='5432')
            program='''
import sys,importlib
from pathlib import Path
sys.path.insert(0,sys.argv[1])
import django
django.setup()
names=('catalog','forms','models','invitations','middleware','private_release','errors','discounts','services','views','staff_review','staff_views')
for name in names:
 module=importlib.import_module('shop.shb.'+name)
 assert Path(module.__file__).is_relative_to(Path(sys.argv[1]))
print('PACKAGED_SHB_IMPORT_PASS modules='+str(len(names)))
'''
            imported=subprocess.run([str(python),'-I','-c',program,str(app)],env=env,text=True,capture_output=True,timeout=30,check=True)
            assert 'PACKAGED_SHB_IMPORT_PASS modules=12' in imported.stdout
    record={'schema':1,'evidence_class':'local-inert-source','source':str(built),'files':actual,
        'imported_modules':12,'runtime_qualified':False,'production_activation':False,
        'duration_seconds':round(time.monotonic()-started,3)}
    encoded=(json.dumps(record,sort_keys=True,indent=2)+'\n').encode();digest=hashlib.sha256(encoded).hexdigest()
    destination=ROOT/'docs/evidence/shb/source-revisions'/f'{digest}.json';destination.parent.mkdir(parents=True,exist_ok=True)
    if destination.exists():assert destination.read_bytes()==encoded
    else:destination.write_bytes(encoded)
    print(f'SHB_SOURCE_PASS checks=2 files={len(actual)} imported_modules=12 source={built} evidence={destination.relative_to(ROOT)} duration_seconds={record["duration_seconds"]}')


if __name__=='__main__':main()
