import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from inventory_artifacts import reconcile


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.record={'name':'synthetic','version':'1.0','artifact_url':'https://synthetic.invalid/artifact','artifact_hash':'sha256:'+'a'*64,'licence_texts':[{'path':'LICENSE','sha256':'b'*64}]}
        self.bom={'bomFormat':'CycloneDX','specVersion':'1.6','components':[{'name':'synthetic','version':'1.0','bom-ref':'synthetic-1'}],'dependencies':[{'ref':'synthetic-1','dependsOn':[]}]}
    def test_positive_exact_inventory(self):self.assertEqual(reconcile([self.record],self.bom,'python',require_text=True),1)
    def test_missing_transitive_or_component(self):
        bad=copy.deepcopy(self.bom);bad['components'].append({'name':'transitive','version':'2','bom-ref':'transitive-2'})
        with self.assertRaises(ValueError):reconcile([self.record],bad,'python')
        with self.assertRaises(ValueError):reconcile([],self.bom,'python')
    def test_missing_artifact_hash_or_text(self):
        for key,value in [('artifact_hash',''),('artifact_hash','invented'),('artifact_url',''),('licence_texts',[])]:
            bad=copy.deepcopy(self.record);bad[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):reconcile([bad],self.bom,'python',require_text=True)
    def test_invented_or_malformed_identity(self):
        bad=copy.deepcopy(self.record);bad['version']='invented'
        with self.assertRaises(ValueError):reconcile([bad],self.bom,'python')
        bad=copy.deepcopy(self.record);bad['licence_texts'][0]['sha256']='invalid'
        with self.assertRaises(ValueError):reconcile([bad],self.bom,'python')
