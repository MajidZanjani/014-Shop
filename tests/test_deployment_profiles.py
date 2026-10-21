import copy
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from check_deployment import ROOT,validate_profile


class ProfileTests(unittest.TestCase):
    def setUp(self):self.profile=json.loads((ROOT/'ops/config/deployment-profiles.json').read_text())
    def test_positive_and_both_deferred_ingress_contracts(self):
        for mode in (None,'A-passthrough','B-existing-termination'):
            self.profile['ingress']['mode']=mode
            self.assertIs(validate_profile(self.profile),self.profile)
    def test_old_cloud_and_unknown_nested_fields(self):
        for section,key,value in [(None,'compute_region','GRA11'),(None,'flavor','B2-7'),(None,'cloud_volume',50),('host','billing_conversion',1),('storage','public_IP_purchase',True)]:
            bad=copy.deepcopy(self.profile);target=bad if section is None else bad[section];target[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):validate_profile(bad)
    def test_false_observation_and_ownership(self):
        for section,key,value in [('host','observed',True),('host','location','gra'),('account','uid',9909),('runtime','qualified',True),('database','existing_cluster_reuse',True),('database','system_identifier','invented')]:
            bad=copy.deepcopy(self.profile);bad[section][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):validate_profile(bad)
    def test_routing_and_generic_protected_approval(self):
        for section,key,value in [('ingress','public_activation',True),('ingress','mode',['A-passthrough','B-existing-termination']),('ingress','dns_changes',True),('ingress','dns01_proves_routing',True),('ingress','protected_proxy_change',True),('ingress','proxy_protocol_addition',True),('authorization','generic_approval',True),('authorization','protected_actions',['reload existing proxy']),('authorization','rollback','host-generation')]:
            bad=copy.deepcopy(self.profile);bad[section][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):validate_profile(bad)
    def test_resource_and_storage_escape(self):
        for section,key,value in [('resources','existing_parent_changes',True),('resources','all_descendants_qualified',True),('storage','snapshot_and_descendant_accounting',False),('storage','parent_quota_bytes',0),('listeners','allocated',True),('listeners','preserve_ports',[80,443]),('integrations','change_existing_services',True)]:
            bad=copy.deepcopy(self.profile);bad[section][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):validate_profile(bad)
