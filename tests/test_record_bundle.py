"""Offline unverified record candidates, never host publication evidence."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'ops/runtime'))
import record_bundle as bundle
import operator_inspect
import process_probe
import schema_reconciliation
from test_process_probe import candidate_bundle


class RecordBundleTests(unittest.TestCase):
    def prepare(self,value):
        return bundle.prepare_records(json.dumps(value).encode())

    def test_exact_candidate_returns_only_unverified_hash_report_and_canonical_bytes(self):
        value=candidate_bundle();data=json.dumps(value).encode()
        payloads,report=bundle.prepare_records(data)
        self.assertEqual(set(payloads),bundle.FILENAMES)
        self.assertEqual(report['bundle_sha256'],hashlib.sha256(data).hexdigest())
        self.assertEqual(report['status'],'candidate_validated')
        self.assertEqual(report['evidence_class'],'unverified-candidate')
        for flag in ('publication_authorized','retry_authorized','reopening_authorized'):
            self.assertIs(report[flag],False)
        for name,payload in payloads.items():
            self.assertEqual(json.loads(payload),value['records'][name])
            self.assertEqual(report['record_sha256'][name],hashlib.sha256(payload).hexdigest())
            self.assertTrue(payload.endswith(b'\n'))
        self.assertNotIn('synthetic_shop',json.dumps(report))
        self.assertNotIn('CREATE TABLE',json.dumps(report))

    def test_no_observed_evidence_or_publication_claim_accepted(self):
        for change in ({'evidence_class':'actual-mx1-qualified'},{'schema_version':True},
                       {'publication_authorized':True},{'credential':'synthetic-private'}):
            with self.subTest(change=change),self.assertRaises(ValueError):
                self.prepare(dict(candidate_bundle(),**change))

    def test_missing_or_extra_record_denied(self):
        for change in ('missing','extra'):
            value=candidate_bundle()
            if change=='missing':value['records'].pop('expected.json')
            else:value['records']['.env']={'password':'synthetic-private'}
            with self.subTest(change=change),self.assertRaises(ValueError):self.prepare(value)

    def test_mixed_startup_database_or_control_binary_denied(self):
        changes=(('expected.json','machine_id_sha256','b'*64),
                 ('operator-connection.json','pg_control','/nix/store/'+'c'*32+'-postgresql/bin/pg_controldata'))
        for name,key,replacement in changes:
            value=candidate_bundle();value['records'][name][key]=replacement
            with self.subTest(key=key),self.assertRaises(ValueError):self.prepare(value)
        for name in ('operator-connection.json','schema-reconciliation.json'):
            value=candidate_bundle();value['records'][name]['database']['role']='decoy'
            with self.subTest(name=name),self.assertRaises(ValueError):self.prepare(value)

    def test_expired_or_write_authority_is_not_inspection_candidate(self):
        for key,value in (('expires_at','2000-01-01T00:00:00Z'),('action','apply-reviewed-schema')):
            candidate=candidate_bundle();candidate['records']['schema-reconciliation.json'][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.prepare(candidate)

    def test_exact_original_artifact_required(self):
        for artifact in ('!!','e30='):
            value=candidate_bundle();value['artifact_base64']=artifact
            with self.subTest(artifact=artifact),self.assertRaises(ValueError):self.prepare(value)

    def test_duplicate_fields_invalid_encoding_and_bundle_bound_denied(self):
        data=json.dumps(candidate_bundle()).encode()
        duplicate=data.replace(b'"schema_version": 1',b'"schema_version": 1,"schema_version": 1',1)
        for raw in (duplicate,b'\xff',b' ',b' '* (bundle.MAX_BUNDLE+1)):
            with self.assertRaises(ValueError):bundle.prepare_records(raw)

    def test_individual_record_bound_and_unknown_nested_properties_denied(self):
        candidate=candidate_bundle();candidate['records']['database-process.json']['process']['executable']='x'*32769
        with self.assertRaises(ValueError):self.prepare(candidate)
        candidate=candidate_bundle();candidate['records']['operator-connection.json']['database']['password']='synthetic-private'
        with self.assertRaises(ValueError):self.prepare(candidate)

    def test_validation_never_loads_records_probes_or_connects(self):
        value=candidate_bundle()
        with patch.object(operator_inspect,'load_connection',side_effect=AssertionError), \
             patch.object(process_probe,'load_record',side_effect=AssertionError), \
             patch.object(process_probe,'probe',side_effect=AssertionError), \
             patch.object(schema_reconciliation,'load_authorization',side_effect=AssertionError), \
             patch.object(operator_inspect.psycopg,'connect',side_effect=AssertionError):
            _,report=self.prepare(value)
            self.assertIs(report['publication_authorized'],False)
