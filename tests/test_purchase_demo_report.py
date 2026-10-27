"""Reject incomplete or overclaimed source acceptance evidence."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from demo_purchase_flow import validate_result


def report():
    return {'status':'PURCHASE_FLOW_DEMO_PASS','evidence_class':'local-synthetic',
            'effects_authorized':False,'financial_confirmation':False,'real_email_verification':False,
            'source_acceptance_checks':[
                {'source_check':number,'status':'synthetic_pass' if number<8 else 'partial',
                 'evidence_class':'local-synthetic',**({'remaining':'Actual confidential intake pending'} if number==8 else {})}
                for number in range(1,9)]}


class PurchaseDemoReportTests(unittest.TestCase):
    def test_partial_local_report_is_valid(self):
        validate_result(report())

    def test_missing_duplicate_reordered_and_boolean_case_ids_fail(self):
        good=report()
        variants=[good['source_acceptance_checks'][:-1],
                  good['source_acceptance_checks'][:7]+[good['source_acceptance_checks'][0]],
                  list(reversed(good['source_acceptance_checks']))]
        for rows in variants:
            with self.subTest(rows=rows),self.assertRaises(ValueError):
                validate_result(good|{'source_acceptance_checks':rows})
        changed=deepcopy(good);changed['source_acceptance_checks'][0]['source_check']=True
        with self.assertRaises(ValueError):validate_result(changed)

    def test_intake_cannot_be_promoted_or_omitted(self):
        for update in ({'status':'synthetic_pass'},{'remaining':''},{'evidence_class':'production'}):
            changed=report();changed['source_acceptance_checks'][-1].update(update)
            with self.subTest(update=update),self.assertRaises(ValueError):validate_result(changed)

    def test_actual_authority_or_missing_boundaries_fail(self):
        for key in ('effects_authorized','financial_confirmation','real_email_verification'):
            changed=report();changed[key]=True
            with self.subTest(key=key),self.assertRaises(ValueError):validate_result(changed)
            del changed[key]
            with self.assertRaises(ValueError):validate_result(changed)
        for value in (None,[],{},report()|{'status':'FULL_PASS'},report()|{'evidence_class':'production'}):
            with self.assertRaises(ValueError):validate_result(value)


if __name__=='__main__':unittest.main()
