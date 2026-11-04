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



# The 16 shop.shb.* modules exercise SHB-reachable code directly. Kept in sync
# with scripts/check_shb_retained.py:SHB_LABELS and scripts/check_backend.py:SHB_LABELS.
SHB_LABELS=['shop.shb.tests','shop.shb.discount_tests','shop.shb.review_tests','shop.shb.checkout_tests','shop.shb.paid_order_tests','shop.shb.closure_tests','shop.shb.offer_tests','shop.shb.lifecycle_tests','shop.shb.notification_tests','shop.shb.revision_tests','shop.shb.recovery_tests','shop.shb.financial_tests','shop.shb.invitation_admin_tests','shop.shb.invitation_issuance_tests','shop.shb.discount_admin_tests','shop.shb.discount_issuance_tests']

# Shared invariants SHB depends on. Each batch below names the SHB reuse rationale.
# Modules that exercise only legacy IP/time-accounting behaviour live in
# HISTORICAL_LABELS instead (see below) and run via `check_shb.py --historical`.
SHB_SHARED_LABELS=[
    # Core request/middleware/model behaviours SHB reuses on every protected route.
    ['shop.core.tests','shop.access.tests','shop.access.staff_tests','shop.access.recovery_tests','shop.access.effect_tests','shop.access.startup_tests','shop.access.staff_restore_tests','shop.access.authentication_recovery_tests'],
    # Payment adapter boundary SHB uses for every checkout/reconcile/refund path.
    ['shop.payments.tests','shop.payments.attempt_tests','shop.payments.control_tests','shop.payments.notification_tests','shop.payments.observation_tests','shop.payments.operation_tests','shop.payments.overpayment_tests'],
    # Staff review/navigation/preparation routes SHB reuses for ASIC review + paid-order admin.
    ['shop.access.review_tests','shop.access.staff_navigation_tests','shop.access.preparation_tests'],
    # Outbox ownership invariant SHB worker uses for purchase-notice/transaction-notice delivery.
    # shop.worker.statement_mail_tests moved to HISTORICAL_LABELS (R7, 2026-11-04 — IP-era
    # monthly-statement generator; SHB uses shop.shb.transaction_mail instead).
    ['shop.worker.tests.OwnershipTests'],
    # PreparedArchive foundation for every SHB archive-before-publish path
    # (invitation issuance/revocation, discount issuance/revocation, refund handoff, paid order).
    ['shop.adapters.evidence_archive_tests'],
]

# IP-era modules preserved as historical regression per amendment §3 ("do not delete
# useful assertions"). NOT part of mandatory SHB acceptance. Run via `check_shb.py
# --historical`. The three transaction tests require legacy_transaction_environment
# (ShopGateMiddleware removed) because they exercise the old-sale routes SHB closes.
HISTORICAL_TRANSACTION_TESTS=['shop.catalog.checkout_tests','shop.catalog.checkout_payment_tests','shop.catalog.fulfilment_tests']
HISTORICAL_LABELS=[
    HISTORICAL_TRANSACTION_TESTS,       # Old IP checkout + payment + fulfilment lifecycle
    ['shop.worker.statement_mail_tests'],  # Old automated monthly support-statement generator
]


def legacy_transaction_environment(env,scratch):
    """Test preserved services apart from intentional new-IP route denial.

    Only the old-sale gate is excluded in this disposable fake-only test module.
    SHB tests still use the actual middleware and assert old routes stay closed.
    """
    if env.get('SHOP_ENV')!='synthetic':raise ValueError('synthetic regression environment required')
    setting=Path(scratch)/'legacy_checkout_regression.py'
    setting.write_text("from shop.config.synthetic import *\nMIDDLEWARE=[name for name in MIDDLEWARE if name!='shop.shb.middleware.ShopGateMiddleware']\n")
    return dict(env,DJANGO_SETTINGS_MODULE='legacy_checkout_regression',PYTHONPATH=env.get('PYTHONPATH','')+':'+str(scratch))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group()
    mode.add_argument('--shared',action='store_true',help='Also run affected shared security, recovery and bank-domain regressions; existing test commands remain unchanged')
    mode.add_argument('--historical',action='store_true',help='Run only preserved IP-era regressions (catalog checkout/payment/fulfilment + worker statement-mail). Not part of mandatory SHB acceptance.')
    parser.add_argument('--test-label',action='append',default=[],help='Run exact SHB test labels without claiming the shared lane')
    args=parser.parse_args()
    if args.test_label:
        if args.shared or args.historical or not all(re.fullmatch(r'shop\.shb\.[a-z_]+(?:\.[A-Za-z_][A-Za-z0-9_]*){0,2}',name) for name in args.test_label):raise ValueError('invalid focused SHB lane')
    started=time.monotonic()
    if args.historical:
        with prepared_database() as (python,env,pg,database,scratch):
            manage(python,env,'check')
            manage(python,env,'migrate','--noinput')
            historical=0
            for labels in HISTORICAL_LABELS:
                batch_env=legacy_transaction_environment(env,scratch) if labels==HISTORICAL_TRANSACTION_TESTS else env
                outcome=manage(python,batch_env,'test',*labels,'--noinput','--keepdb',timeout=120)
                log=outcome.stdout+outcome.stderr;match=re.search(r'Ran (\d+) tests?',log)
                if not match or 'OK' not in log or 'skipped' in log:raise ValueError('preserved historical regression failed/empty/skipped')
                historical+=int(match[1]);print(f'SHB_HISTORICAL_BATCH_PASS tests={match[1]} labels='+','.join(labels))
            print(f'SHB_HISTORICAL_PASS checks={1+len(HISTORICAL_LABELS)} tests={historical} duration_seconds={time.monotonic()-started:.3f} postgres=18.6 evidence=local-synthetic-historical shb_acceptance=false')
        return
    # Pure source/money checks are useful even before Django starts.
    suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_shb_*.py')
    result=unittest.TextTestRunner(verbosity=1).run(suite)
    if not result.wasSuccessful() or result.skipped or result.testsRun<9:raise ValueError('SHB catalog/private-release controls failed')
    with prepared_database() as (python,env,pg,database,scratch):
        manage(python,env,'check')
        manage(python,env,'migrate','--noinput')
        manage(python,env,'makemigrations','--check','--dry-run')
        labels=args.test_label or SHB_LABELS
        output=manage(python,env,'test',*labels,'--noinput','--keepdb',timeout=300)
        raw=output.stdout+output.stderr
        count=re.search(r'Ran (\d+) tests?',raw)
        if not count or int(count[1])<(1 if args.test_label else 71) or 'OK' not in raw or 'skipped' in raw:
            raise ValueError('SHB PostgreSQL controls missing/failed/skipped')
        print(raw)
        shared=0
        shared_checks=0
        if args.shared:
            for labels in SHB_SHARED_LABELS:
                outcome=manage(python,env,'test',*labels,'--noinput','--keepdb',timeout=120)
                log=outcome.stdout+outcome.stderr;match=re.search(r'Ran (\d+) tests?',log)
                if not match or 'OK' not in log or 'skipped' in log:raise ValueError('required shared regressions failed/empty/skipped')
                shared+=int(match[1]);print(f'SHB_SHARED_BATCH_PASS tests={match[1]}')
            # This lane actually enters an empty network namespace. Never claim
            # adapter isolation by setting its guard in the shared DB process.
            from check_backend import qualify_adapters
            shared+=qualify_adapters()
            shared_checks=len(SHB_SHARED_LABELS)+1
        print(f'SHB_LOCAL_PASS checks={4+shared_checks} tests={result.testsRun+int(count[1])+shared} shared_tests={shared} duration_seconds={time.monotonic()-started:.3f} postgres=18.6 evidence=local-synthetic live_approved=false')


if __name__=='__main__':
    try:main()
    except subprocess.CalledProcessError as error:
        # This harness creates only disposable synthetic fixtures, never real
        # credentials/provider requests. Keep the actual test failure visible.
        sys.stderr.write((error.stdout or '')+(error.stderr or ''))
        raise SystemExit(1) from None
