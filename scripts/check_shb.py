#!/usr/bin/env python3
"""Focused SHB release lane on an owned real PostgreSQL; no external effects."""
import os
import argparse
from pathlib import Path
import re
import sys
import subprocess
import time
import unittest

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
from check_worker import prepared_database,manage


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--shared',action='store_true',help='Also run affected shared security, recovery and bank-domain regressions; existing test commands remain unchanged')
    args=parser.parse_args()
    started=time.monotonic()
    # Pure source/money checks are useful even before Django starts.
    suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_shb_*.py')
    result=unittest.TextTestRunner(verbosity=1).run(suite)
    if not result.wasSuccessful() or result.skipped or result.testsRun<9:raise ValueError('SHB catalog/private-release controls failed')
    with prepared_database() as (python,env,pg,database,scratch):
        manage(python,env,'check')
        manage(python,env,'migrate','--noinput')
        manage(python,env,'makemigrations','--check','--dry-run')
        output=manage(python,env,'test','shop.shb.tests','--noinput','--keepdb',timeout=120)
        raw=output.stdout+output.stderr
        count=re.search(r'Ran (\d+) tests?',raw)
        if not count or int(count[1])<15 or 'OK' not in raw or 'skipped' in raw:
            raise ValueError('SHB PostgreSQL controls missing/failed/skipped')
        print(raw)
        shared=0
        if args.shared:
            batches=[['shop.core.tests','shop.access.tests','shop.access.staff_tests','shop.access.recovery_tests','shop.access.effect_tests','shop.access.startup_tests','shop.access.staff_restore_tests','shop.access.authentication_recovery_tests'],
                ['shop.payments.tests','shop.payments.attempt_tests','shop.payments.control_tests','shop.payments.notification_tests','shop.payments.observation_tests','shop.payments.operation_tests','shop.payments.overpayment_tests','shop.adapters.tests']]
            for labels in batches:
                outcome=manage(python,env,'test',*labels,'--noinput','--keepdb',timeout=120)
                log=outcome.stdout+outcome.stderr;match=re.search(r'Ran (\d+) tests?',log)
                if not match or 'OK' not in log or 'skipped' in log:raise ValueError('required shared regressions failed/empty/skipped')
                shared+=int(match[1]);print(f'SHB_SHARED_BATCH_PASS tests={match[1]}')
        print(f'SHB_LOCAL_PASS checks={4+(2 if args.shared else 0)} tests={result.testsRun+int(count[1])+shared} shared_tests={shared} duration_seconds={time.monotonic()-started:.3f} postgres=18.6 evidence=local-synthetic live_approved=false')


if __name__=='__main__':
    try:main()
    except subprocess.CalledProcessError as error:
        # This harness creates only disposable synthetic fixtures, never real
        # credentials/provider requests. Keep the actual test failure visible.
        sys.stderr.write((error.stdout or '')+(error.stderr or ''))
        raise SystemExit(1) from None
