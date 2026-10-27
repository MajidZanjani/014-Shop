#!/usr/bin/env python3
"""Rehearse final purchase flow in a fresh owned PG database; no external effects."""
import json
import subprocess
from check_worker import prepared_database,manage


def validate_result(value):
    """Fail closed on omitted/duplicated source cases or unqualified promotion."""
    if (not isinstance(value,dict) or value.get('status')!='PURCHASE_FLOW_DEMO_PASS'
            or value.get('evidence_class')!='local-synthetic'
            or any(value.get(key) is not False for key in ('effects_authorized','financial_confirmation','real_email_verification'))):
        raise ValueError('synthetic demo result mismatch')
    checks=value.get('source_acceptance_checks')
    if not isinstance(checks,list) or len(checks)!=8:
        raise ValueError('eight source checks required')
    for number,row in enumerate(checks,1):
        if (not isinstance(row,dict) or type(row.get('source_check')) is not int or row['source_check']!=number
                or row.get('evidence_class')!='local-synthetic'
                or row.get('status')!=('synthetic_pass' if number<8 else 'partial')):
            raise ValueError('source check scope mismatch')
    if not isinstance(checks[-1].get('remaining'),str) or not checks[-1]['remaining'].strip():
        raise ValueError('private intake qualification must remain explicit')


def main():
    with prepared_database() as (python,env,pg,database,scratch):
        manage(python,env,'migrate','--noinput')
        archive=scratch/'purchase-archive';archive.mkdir(mode=0o700)
        code='from shop.payments.purchase_demo_scenario import run; import json; print(json.dumps(run('+repr(str(archive))+'),sort_keys=True))'
        result=manage(python,env,'shell','--no-imports','-c',code,timeout=30)
        value=json.loads(result.stdout)
        validate_result(value)
        print(json.dumps(value,sort_keys=True,indent=2))

if __name__=='__main__':
    try:main()
    except (ValueError,OSError,subprocess.SubprocessError):
        raise SystemExit('PURCHASE_FLOW_DEMO_FAIL: local fixture unavailable') from None
