#!/usr/bin/env python3
"""Rehearse final purchase flow in a fresh owned PG database; no external effects."""
import json
import subprocess
from check_worker import prepared_database,manage


def main():
    with prepared_database() as (python,env,pg,database,scratch):
        manage(python,env,'migrate','--noinput')
        archive=scratch/'purchase-archive';archive.mkdir(mode=0o700)
        code='from shop.payments.purchase_demo_scenario import run; import json; print(json.dumps(run('+repr(str(archive))+'),sort_keys=True))'
        result=manage(python,env,'shell','--no-imports','-c',code,timeout=30)
        value=json.loads(result.stdout)
        if value['status']!='PURCHASE_FLOW_DEMO_PASS' or value['effects_authorized'] is not False:
            raise ValueError('synthetic demo result mismatch')
        print(json.dumps(value,sort_keys=True,indent=2))

if __name__=='__main__':
    try:main()
    except (ValueError,OSError,subprocess.SubprocessError):
        raise SystemExit('PURCHASE_FLOW_DEMO_FAIL: local fixture unavailable') from None
