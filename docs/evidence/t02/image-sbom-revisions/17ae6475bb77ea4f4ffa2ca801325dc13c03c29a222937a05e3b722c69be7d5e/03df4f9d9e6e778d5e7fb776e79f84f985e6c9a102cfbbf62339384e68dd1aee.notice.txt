"""Real PostgreSQL reviewed licence change cases; no original rights or financial effects."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from threading import Barrier
from unittest.mock import patch
import json
import uuid
from django.db import connections,transaction,IntegrityError
from django.test import Client,TransactionTestCase,override_settings
from django.utils import timezone
from shop.adapters.evidence_archive import ArchiveError
from shop.payments.models import SyntheticBankOperation,SyntheticPaymentAttempt
from . import licence_changes as service,checkout,support_ledger_tests as fixture
from .models import (SyntheticLineEntitlement,SyntheticLicenceCase,SyntheticLicenceCaseEvent,
                     SyntheticLicenceCaseStaffGrant,SyntheticSupportEvent,SyntheticPackageRevision)


class LicenceChangeTests(TransactionTestCase):
    save_cart=fixture.SupportLedgerTests.save_cart
    preview=fixture.SupportLedgerTests.preview
    accept=fixture.SupportLedgerTests.accept

    def setUp(self):
        fixture.SupportLedgerTests.setUp(self)
        self.line=SyntheticLineEntitlement.objects.get(fulfilment=self.grant)
        self.base=f'/purchase/checkout-rehearsal/{self.saved.pk}/changes/'

    def capture(self,raw=None,key=None):
        return service.capture(self.owner,self.saved.pk,self.line.pk,key or uuid.uuid4(),raw or {'kind':'renewal'},self.archive)

    def assign(self,case):SyntheticLicenceCaseStaffGrant.objects.get_or_create(user=self.staff,case=case)

    def event(self,case,kind='review',decision='ready_for_commercial_review',key=None,expected=None):
        if expected is None:expected=SyntheticLicenceCaseEvent.objects.filter(case=case).count()
        return service.event(self.request,self.owner,self.saved.pk,case.identity,key or uuid.uuid4(),expected,kind,self.archive,
            decision=decision if kind=='review' else None)

    def state(self,case,before=None):
        with transaction.atomic(durable=True):
            locked=service.case_locked(self.owner,self.saved.pk,case.identity,self.archive)
            return service.summary(locked,list(SyntheticLicenceCaseEvent.objects.filter(case=locked).order_by('revision')),self.archive,before)

    def form(self,browser,path,value):
        from urllib.parse import urlencode
        return browser.post(path,data=urlencode(value,doseq=True),content_type='application/x-www-form-urlencoded')

    def test_five_narrow_case_types_keep_accepted_history_grants_and_money_unchanged(self):
        original=deepcopy(self.line.snapshot);accepted=deepcopy(self.saved.snapshot)
        requests=[{'kind':'renewal'},{'kind':'rehost'},{'kind':'family-addition','families':['altera-cyclone-10']},
            {'kind':'node-addition','fixed_nodes':1,'floating_nodes':1},
            {'kind':'production-upgrade','term':'rdp-yearly','production_band':'higher-volume','production_units':6500}]
        for raw in requests:
            case=self.capture(raw);self.assign(case);self.event(case);proposal=self.event(case,'proposal')
            value=self.state(case)
            self.assertTrue(value['proposal']['active']);self.assertFalse(value['payment_enabled'])
            self.assertFalse(value['actual_rights_changed']);self.assertFalse(value['proposal']['support_changed'])
            self.assertFalse(value['proposal']['physical_recall_promised'])
            self.assertTrue(all(v is None for v in value['proposal']['order']['policies'].values()))
            self.assertFalse(proposal.payload['proposal']['scope_revision']['activation_enabled'])
            self.assertEqual(value['proposal']['order']['quotation_required'],raw['kind']=='production-upgrade')
        self.line.refresh_from_db();self.saved.refresh_from_db();self.grant.refresh_from_db()
        self.assertEqual(self.line.snapshot,original);self.assertEqual(self.saved.snapshot,accepted)
        self.assertEqual(self.grant.support_seconds,72000);self.assertEqual(SyntheticLineEntitlement.objects.count(),1)
        self.assertEqual(SyntheticSupportEvent.objects.count(),0);self.assertEqual(SyntheticBankOperation.objects.count(),1)
        self.assertEqual(SyntheticPaymentAttempt.objects.count(),1);self.assertEqual(SyntheticPackageRevision.objects.count(),0)

    def test_case_retry_normalizes_family_order_and_conflicting_request_denied(self):
        raw={'kind':'family-addition','families':['altera-cyclone-10','altera-cyclone-10-lp-c10lp']};key=uuid.uuid4()
        first=self.capture(raw,key)
        self.assertEqual(self.capture(dict(raw,families=list(reversed(raw['families']))),key).pk,first.pk)
        self.assertEqual(first.payload['proposed_configuration']['families'],['altera-cyclone-10-lp-c10lp','altera-max-10','altera-cyclone-10'])
        with self.assertRaisesRegex(checkout.CheckoutError,'case_request_conflict'):self.capture({'kind':'rehost'},key)
        with patch.dict(service.CATALOG,revision='f'*64):
            self.assertEqual(self.capture(raw,key).pk,first.pk)
        self.assertEqual(SyntheticLicenceCase.objects.count(),1)

    def test_exact_review_retry_and_append_only_correction_supersede_proposal(self):
        case=self.capture();self.assign(case);key=uuid.uuid4()
        review=self.event(case,key=key,expected=0)
        self.assertEqual(self.event(case,key=key,expected=0).pk,review.pk)
        proposal_key=uuid.uuid4();proposal=self.event(case,'proposal',key=proposal_key,expected=1)
        self.assertEqual(self.event(case,'proposal',key=proposal_key,expected=1).pk,proposal.pk)
        with self.assertRaisesRegex(checkout.CheckoutError,'proposal_already_prepared'):self.event(case,'proposal')
        correction=self.event(case,decision='needs_information')
        state=self.state(case);self.assertFalse(state['proposal']['active']);self.assertEqual(state['decision'],'needs_information')
        self.assertEqual(SyntheticLicenceCaseEvent.objects.get(pk=review.pk).payload['command']['decision'],'ready_for_commercial_review')
        with self.assertRaisesRegex(checkout.CheckoutError,'commercial_review_required'):self.event(case,'proposal')
        self.event(case);new=self.event(case,'proposal')
        self.assertNotEqual(new.payload['proposal']['order']['id'],proposal.payload['proposal']['order']['id'])
        self.assertTrue(self.state(case)['proposal']['active'])
        with self.assertRaisesRegex(checkout.CheckoutError,'case_request_conflict'):self.event(case,decision='declined',key=key,expected=0)

    def test_original_scope_and_family_node_production_constraints(self):
        invalid=[{'kind':'rehost','host_id':'RAW_HOST_CANARY'}, {'kind':'renewal','fee_minor':0},
            {'kind':'family-addition','families':['altera-max-10']},{'kind':'family-addition','families':['microchip-polarfire']},
            {'kind':'family-addition','families':['altera-cyclone-10','altera-cyclone-10']},
            {'kind':'node-addition','fixed_nodes':True,'floating_nodes':0},{'kind':'node-addition','fixed_nodes':0,'floating_nodes':0},
            {'kind':'node-addition','fixed_nodes':1000000,'floating_nodes':0},
            {'kind':'production-upgrade','term':'rdp-yearly','production_band':'units-1-100','production_units':6500},
            {'kind':'production-upgrade','term':'perpetual','production_band':'higher-volume','production_units':6500},
            {'kind':'production-upgrade','term':'rd-annual','production_band':None,'production_units':None}]
        for raw in invalid:
            with self.assertRaises(checkout.CheckoutError):self.capture(raw)
        self.assertEqual(SyntheticLicenceCase.objects.count(),0)
        original=deepcopy(self.line.snapshot['configuration']);catalog=service.source(original)
        original['vendor']='amd-xilinx'
        with self.assertRaisesRegex(checkout.CheckoutError,'invalid_production_upgrade'):
            service.normalized(original,{'kind':'production-upgrade','term':'rdp-yearly','production_band':'units-1-100','production_units':50},catalog)
        original['term']='perpetual'
        with self.assertRaisesRegex(checkout.CheckoutError,'renewal_not_applicable'):service.normalized(original,{'kind':'renewal'},catalog)

    def test_rehosting_case_does_not_collect_binding_or_recall_materials(self):
        case=self.capture({'kind':'rehost'});self.assign(case);self.event(case);self.event(case,'proposal')
        state=self.state(case)
        self.assertIsNone(state['proposal']['order']['policies']['host_profile'])
        self.assertIsNone(state['proposal']['order']['policies']['revocation_policy'])
        self.assertFalse(state['proposal']['physical_recall_promised'])
        self.assertEqual(case.payload['proposed_configuration']['fixed_nodes'],self.line.snapshot['configuration']['fixed_nodes'])

    def test_archive_failure_or_bad_readback_prevents_case_review_and_proposal(self):
        with patch.object(self.archive,'publish',side_effect=ArchiveError('unavailable')):
            with self.assertRaises(ArchiveError):self.capture()
        self.assertEqual(SyntheticLicenceCase.objects.count(),0)
        case=self.capture();self.assign(case)
        with patch.object(self.archive,'publish',side_effect=ArchiveError('unavailable')):
            with self.assertRaises(ArchiveError):self.event(case)
        self.assertEqual(SyntheticLicenceCaseEvent.objects.count(),0)
        self.event(case);original=self.archive.recover
        def bad(receipt):return b'bad' if receipt.evidence_id==case.identity else original(receipt)
        with patch.object(self.archive,'recover',side_effect=bad):
            with self.assertRaisesRegex(checkout.CheckoutError,'archive_mismatch'):self.event(case,'proposal')
        self.assertEqual(SyntheticLicenceCaseEvent.objects.count(),1)

    def test_recent_mfa_expiry_assignment_and_generation_required_even_on_retry(self):
        case=self.capture()
        with self.assertRaisesRegex(checkout.CheckoutError,'not_found'):self.event(case)
        self.assign(case);key=uuid.uuid4();self.event(case,key=key,expected=0)
        SyntheticLicenceCaseStaffGrant.objects.all().delete()
        with self.assertRaisesRegex(checkout.CheckoutError,'not_found'):self.event(case,key=key,expected=0)
        self.assign(case);self.request.session['shop_staff_mfa']['verified_at']-=301
        with self.assertRaisesRegex(checkout.CheckoutError,'recent_staff_mfa_required'):self.event(case)
        self.request.session['shop_staff_mfa']['verified_at']=timezone.now().timestamp()
        from shop.access.models import StaffCredential
        StaffCredential.objects.filter(pk=self.credential.pk).update(generation=uuid.uuid4())
        with self.assertRaisesRegex(checkout.CheckoutError,'recent_staff_mfa_required'):self.event(case)

    def test_expiry_during_archive_rolls_back_review(self):
        case=self.capture();self.assign(case);original=self.archive.publish
        def expired(identity,body):
            receipt=original(identity,body);self.request.session['shop_staff_mfa']['verified_at']-=301;return receipt
        with patch.object(self.archive,'publish',side_effect=expired):
            with self.assertRaisesRegex(checkout.CheckoutError,'recent_staff_mfa_required'):self.event(case)
        self.assertEqual(SyntheticLicenceCaseEvent.objects.count(),0)

    def test_catalog_change_holds_new_proposal_and_preserves_retained_case(self):
        case=self.capture();self.assign(case);self.event(case)
        with patch.dict(service.CATALOG,revision='f'*64):
            with self.assertRaisesRegex(checkout.CheckoutError,'catalog_scope_changed'):self.event(case,'proposal')
            self.assertEqual(self.state(case)['catalog_revision'],case.payload['catalog']['revision'])
        self.event(case,'proposal')
        with patch.dict(service.CATALOG,revision='f'*64):self.assertFalse(self.state(case)['proposal']['active'])

    def test_competing_capture_review_and_proposal_never_duplicate(self):
        key=uuid.uuid4();barrier=Barrier(2)
        def capture(_):
            try:barrier.wait(timeout=10);return self.capture(key=key).pk
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:ids=list(pool.map(capture,range(2)))
        self.assertEqual(ids[0],ids[1]);case=SyntheticLicenceCase.objects.get();self.assign(case);barrier=Barrier(2)
        def review(_):
            try:
                barrier.wait(timeout=10)
                try:return self.event(case,expected=0).kind
                except checkout.CheckoutError as e:return str(e)
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:outcomes=list(pool.map(review,range(2)))
        self.assertCountEqual(outcomes,['review','case_revision_changed'])
        key=uuid.uuid4();barrier=Barrier(2)
        def proposal(_):
            try:barrier.wait(timeout=10);return self.event(case,'proposal',expected=1,key=key).pk
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:ids=list(pool.map(proposal,range(2)))
        self.assertEqual(ids[0],ids[1]);self.assertEqual(SyntheticLicenceCaseEvent.objects.count(),2)

    def test_case_and_review_history_are_database_immutable(self):
        case=self.capture();self.assign(case);event=self.event(case)
        for model,pk in ((SyntheticLicenceCase,case.pk),(SyntheticLicenceCaseEvent,event.pk)):
            for mutate in (lambda:model.objects.filter(pk=pk).update(payload={}),lambda:model.objects.filter(pk=pk).delete()):
                with self.assertRaises(IntegrityError),transaction.atomic():mutate()
        self.assertEqual(self.state(case)['revision'],1)

    def test_owner_closed_no_js_form_json_history_scope_csrf_and_production_guards(self):
        route=self.base+'new/'+str(self.line.pk)+'/'
        page=self.client.get(route);self.assertContains(page,'Capture renewal request');self.assertContains(page,'Capture rehosting request')
        self.assertNotContains(page,'name="host_id"')
        key=str(uuid.uuid4())
        for _ in range(2):
            response=self.form(self.client,route,{'kind':'renewal','request_id':key});self.assertEqual(response.status_code,303)
        case=SyntheticLicenceCase.objects.get();self.assign(case);self.event(case);self.event(case,'proposal')
        detail=self.base+str(case.identity)+'/'
        result=self.client.get(detail,HTTP_ACCEPT='application/json')
        self.assertEqual(result.status_code,200,result.content)
        for forbidden in ('staff_id','mfa_verified_at','credential_generation','archive_receipt','SYNTHETIC_BUSINESS_CANARY'):
            self.assertNotIn(forbidden,result.content.decode())
        self.assertIsNone(result.json()['proposal']['order']['policies']['fee_minor'])
        csrf=Client(enforce_csrf_checks=True);csrf.cookies=self.client.cookies.copy()
        self.assertEqual(self.form(csrf,route,{'kind':'renewal','request_id':str(uuid.uuid4())}).status_code,403)
        for raw in ({'kind':'rehost','request_id':1},{'kind':'rehost','request_id':str(uuid.uuid4()),'key':'RAW_KEY_CANARY'}):
            self.assertEqual(self.client.post(route,data=json.dumps(raw),content_type='application/json').status_code,400)
        from .tests import verified_login
        verified_login(self.client,self.other)
        self.assertEqual(self.client.get(detail).status_code,404);self.assertEqual(self.client.get(self.base).status_code,404)
        with override_settings(SHOP_ENV='production'):self.assertEqual(self.client.get(route).status_code,404)

    def test_staff_forms_scope_operator_grants_and_reset(self):
        from shop.access.staff_tests import STAFF_SETTINGS
        from django.core.management import call_command
        case=self.capture();path='/staff/licence-cases/'+str(case.identity)+'/'
        with override_settings(**STAFF_SETTINGS):
            staff=Client(HTTP_HOST='staff.localhost');self.assertEqual(staff.get(path).status_code,403)
            staff.force_login(self.staff);session=staff.session;session['shop_staff_mfa']=self.request.session['shop_staff_mfa'];session.save()
            self.assertEqual(staff.get(path).status_code,404)
            call_command('local_staff','grant-case',username=self.staff.username,case=str(case.identity),verbosity=0)
            self.assertContains(staff.get('/staff/licence-cases/'),str(case.identity))
            self.assertContains(staff.get(path),'Record attributed review')
            value={'action':'review','request_id':str(uuid.uuid4()),'expected_revision':'0','decision':'ready_for_commercial_review'}
            for _ in range(2):self.assertEqual(self.form(staff,path,value).status_code,303)
            self.assertEqual(self.form(staff,path,{'action':'proposal','request_id':str(uuid.uuid4()),'expected_revision':'1'}).status_code,303)
            self.assertContains(staff.get(path),'Payment and licence activation remain disabled')
            call_command('local_staff','revoke-case',username=self.staff.username,case=str(case.identity),verbosity=0)
            self.assertEqual(staff.get(path).status_code,404)
            call_command('local_staff','grant-case',username=self.staff.username,case=str(case.identity),verbosity=0)
            call_command('local_staff','reset',username=self.staff.username,capture_root=str(self.root),verbosity=0)
            self.assertFalse(SyntheticLicenceCaseStaffGrant.objects.exists());self.assertEqual(staff.get(path).status_code,403)

    def test_review_history_paging_preserves_latest_state_and_all_events(self):
        case=self.capture();self.assign(case)
        for _ in range(21):self.event(case,decision='needs_information')
        first=self.state(case);self.assertEqual(len(first['history']),20);self.assertEqual(first['next_before'],2)
        second=self.state(case,first['next_before']);self.assertEqual([r['revision'] for r in second['history']],[1])
        self.assertEqual(second['revision'],21);self.assertEqual(SyntheticLicenceCaseEvent.objects.count(),21)

    def test_new_catalog_cannot_silently_drop_a_previously_licensed_family(self):
        case=self.capture();key=case.request_id
        vendors=deepcopy(service.CATALOG['vendors'])
        for vendor in vendors:
            if vendor['id']=='altera':vendor['families']=[family for family in vendor['families'] if family['id']!='altera-max-10']
        with patch.dict(service.CATALOG,vendors=vendors,revision='f'*64):
            with self.assertRaisesRegex(checkout.CheckoutError,'catalog_scope_changed'):
                self.capture({'kind':'family-addition','families':['altera-cyclone-10']})
            self.assertEqual(self.capture(key=key).pk,case.pk)
        self.line.refresh_from_db();self.assertEqual(self.line.snapshot['configuration']['families'],['altera-max-10'])

    def test_same_band_higher_known_unit_request_is_reviewed_without_inventing_policy(self):
        original=deepcopy(self.line.snapshot['configuration']);original.update(term='rdp-yearly',production_band='units-1-100',production_units=10)
        catalog=service.source(original)
        raw={'kind':'production-upgrade','term':'rdp-yearly','production_band':'units-1-100','production_units':50}
        request,proposed=service.normalized(original,raw,catalog)
        self.assertEqual(proposed['production_units'],50);self.assertEqual(original['production_units'],10)
        with self.assertRaisesRegex(checkout.CheckoutError,'invalid_production_upgrade'):
            service.normalized(original,dict(raw,production_units=10),catalog)
        original['production_units']=None
        self.assertEqual(service.normalized(original,raw,catalog)[1]['production_units'],50)
