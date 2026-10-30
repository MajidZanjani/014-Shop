"""SHB source authority, per-order bundle math and money tamper controls."""
import copy
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))


class ShbCatalogTests(unittest.TestCase):
    def setUp(self):
        from shop.shb import catalog
        self.catalog=catalog

    def test_exact_one_product_two_variants_and_no_live_price(self):
        data=self.catalog.CATALOG
        self.assertEqual(data['title'],'Supporting Hours Bundle')
        self.assertEqual([(v['label'],v['hours_per_bundle'],v['workflow']) for v in data['variants']],
            [('FPGA Supporting Hours Bundle',10,'checkout'),('ASIC Supporting Hours Bundle',25,'request')])
        for variant in ('shb-fpga-10h','shb-asic-25h'):
            value=self.catalog.quote(variant,1)
            self.assertIsNone(value['total_minor']);self.assertFalse(value['live_payable'])

    def test_purchase_hours_are_per_order_and_discount_never_changes_hours(self):
        offer=self.catalog.synthetic_offer()
        for variant,quantity,hours,subtotal in [('shb-fpga-10h',1,10,100000),('shb-fpga-10h',3,30,300000),('shb-asic-25h',1,25,500000),('shb-asic-25h',2,50,1000000)]:
            with self.subTest(variant=variant,quantity=quantity):
                value=self.catalog.quote(variant,quantity,offer=offer,discount_bps=1250)
                self.assertEqual((value['hours_purchased'],value['subtotal_minor']),(hours,subtotal))
                self.assertEqual(value['discount_minor'],subtotal//8)
                self.assertEqual(value['total_minor'],subtotal-subtotal//8)
                self.assertFalse(value['live_payable'])
                self.assertNotIn('remaining_hours',value)

    def test_invalid_quantity_and_old_sku_are_rejected(self):
        for quantity in (0,-1,True,False,1.0,'1','1.5',None,2**31):
            with self.subTest(quantity=quantity),self.assertRaises(ValueError):
                self.catalog.quote('shb-fpga-10h',quantity)
        with self.assertRaises(ValueError):self.catalog.quote('sll-xspi-mc',1)

    def test_unapproved_or_inconsistent_money_policy_is_rejected(self):
        offer=self.catalog.synthetic_offer()
        for key,value in [('asic_hourly_minor',10000),('fpga_hourly_minor',True),('currency','eur'),('evidence_class','production'),('bank_max_minor',0)]:
            candidate=copy.deepcopy(offer);candidate[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):
                self.catalog.quote('shb-fpga-10h',1,offer=candidate)
        for discount in (-1,True,1.5,10000):
            with self.subTest(discount=discount),self.assertRaises(ValueError):
                self.catalog.quote('shb-fpga-10h',1,offer=offer,discount_bps=discount)
        with self.assertRaises(ValueError):self.catalog.quote('shb-asic-25h',2**30,offer=offer)

    def test_source_compiler_rejects_commercial_approval_in_content(self):
        spec=importlib.util.spec_from_file_location('compile_shb',ROOT/'scripts/compile_shb_catalog.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        source=module.read_source()
        self.assertEqual(module.validate(source)['product_id'],'supporting-hours-bundle')
        for field,value in [('currency','EUR'),('fpga_hourly_minor',10000),('approved_offer_revision','claimed-approved')]:
            candidate=copy.deepcopy(source);candidate['commercial'][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):module.validate(candidate)


if __name__=='__main__':unittest.main()
