import copy
import json
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.db import connections
from django.utils import timezone
from datetime import timedelta
from types import SimpleNamespace
from django.test import Client, TransactionTestCase, override_settings
from .cart_tests import CASES, CartRecoveryMixin
from .models import QuotationRequest, QuotationRequestKey, QuotationReview
from .quotation_status import customer_review_status
from .rules import CATALOG
from .tests import verified_login

URL='/api/v1/quotation-requests/'

class QuotationTests(TransactionTestCase):
    def setUp(self):
        self.owner=get_user_model().objects.create_user(username='quotation-owner')
        self.other=get_user_model().objects.create_user(username='quotation-other')
        verified_login(self.client,self.owner)
        self.saved=self.save_cart(0,CASES[1]['lines'])
        self.payload={'request_id':str(uuid.uuid4()),'cart_id':self.saved['cart_id'],'version':1}
    def save_cart(self,version,lines):
        response=self.client.post('/api/v1/cart/',data=json.dumps({'request_id':str(uuid.uuid4()),'expected_version':version,'catalog_revision':CATALOG['revision'],'lines':copy.deepcopy(lines)}),content_type='application/json')
        self.assertEqual(response.status_code,201)
        return response.json()
    def post(self,payload=None,client=None):
        return (client or self.client).post(URL,data=json.dumps(self.payload if payload is None else payload),content_type='application/json')
    def test_exact_capture_replay_and_later_edits(self):
        first=self.post();self.assertEqual(first.status_code,201)
        self.assertEqual(first.json()['lines'],self.saved['lines'])
        self.assertEqual(first.json()['evaluation'],self.saved['evaluation'])
        self.assertFalse(first.json()['checkout_enabled']);self.assertFalse(first.json()['acceptance_enabled'])
        self.assertIsNone(first.json()['prices']);self.assertIsNone(first.json()['rights'])
        alias=dict(self.payload,request_id=str(uuid.uuid4()))
        self.assertEqual(self.post(alias).json(),first.json())
        self.save_cart(1,CASES[2]['lines'])
        with patch.dict(CATALOG,revision='f'*64):
            self.assertEqual(self.post().json(),first.json())
            self.assertEqual(self.post(alias).json(),first.json())
            self.assertEqual(self.post(dict(self.payload,request_id=str(uuid.uuid4()),version=2)).status_code,409)
        self.assertEqual(self.post(dict(alias,version=2)).status_code,409)
        self.assertEqual(self.client.get(URL+first.json()['id']+'/').json(),first.json())
        self.assertEqual(QuotationRequest.objects.count(),1)
        self.assertEqual(first['Cache-Control'],'no-store')
    def test_freshness_empty_and_support(self):
        self.save_cart(1,[])
        self.assertEqual(self.post().status_code,409)
        self.assertEqual(self.post(dict(self.payload,version=2)).status_code,422)
        self.save_cart(2,CASES[2]['lines'])
        result=self.post(dict(self.payload,version=3));self.assertEqual(result.status_code,201)
        self.assertEqual(result.json()['evaluation']['quoted_support_seconds'],72000)
        self.assertEqual(len(result.json()['lines']),1)
    def test_owner_auth_and_production_boundaries(self):
        first=self.post().json();detail=URL+first['id']+'/'
        self.assertEqual(self.post(client=Client()).status_code,401)
        strict=Client(enforce_csrf_checks=True);verified_login(strict,self.owner)
        self.assertEqual(self.post(client=strict).status_code,403)
        verified_login(self.client,self.other)
        self.assertEqual(self.client.get(URL).json()['requests'],[])
        self.assertEqual(self.client.get(detail).status_code,404)
        self.assertEqual(self.post().status_code,404)
        with override_settings(SHOP_ENV='production'):
            for path in [URL,detail]:self.assertEqual(self.client.get(path).status_code,404)
            self.assertEqual(self.post().status_code,404)
        self.other.is_staff=True;self.other.save()
        self.assertEqual(self.post().status_code,403)
        self.other.is_staff=False;self.other.save()
        session=self.client.session;session.pop('shop_verified_identity');session.save()
        self.assertEqual(self.client.get(detail).status_code,403)
    def test_parser_scope_and_methods(self):
        for payload in [dict(self.payload,version=True),dict(self.payload,owner=1),dict(self.payload,version=0),dict(self.payload,cart_id=1),dict(self.payload,version='1')]:
            self.assertEqual(self.post(payload).status_code,400)
        for raw in ['NaN','{}','{"version":1,"version":2}','x'*1025]:
            self.assertEqual(self.client.post(URL,data=raw,content_type='application/json').status_code,400)
        self.assertEqual(self.client.post(URL,data='{}',content_type='text/plain').status_code,415)
        self.assertEqual(self.client.get(URL+'?owner=1').status_code,400)
        self.assertEqual(self.client.delete(URL).status_code,405)
        self.assertEqual(QuotationRequest.objects.count(),0)
    def test_list_and_immutable_resource_methods(self):
        first=self.post().json()
        rows=self.client.get(URL).json()['requests'];self.assertEqual([r['id'] for r in rows],[first['id']])
        self.assertEqual(self.client.post(URL+first['id']+'/').status_code,405)
        self.assertEqual(self.client.get(URL+str(uuid.uuid4())+'/').status_code,404)
    def race(self,same):
        clients=[Client(),Client()]
        for client in clients:verified_login(client,self.owner)
        barrier=Barrier(2)
        def run(index):
            try:
                payload=dict(self.payload)
                if not same:payload['request_id']=str(uuid.uuid4())
                barrier.wait(timeout=10)
                response=self.post(payload,clients[index])
                return response.status_code,response.json()['id']
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(run,range(2)))
        self.assertEqual(sorted(r[0] for r in results),[200,201])
        self.assertEqual(results[0][1],results[1][1]);self.assertEqual(QuotationRequest.objects.count(),1)
        self.assertEqual(QuotationRequestKey.objects.count(),1 if same else 2)
    def test_concurrent_exact_retry(self):self.race(True)
    def test_concurrent_different_keys(self):self.race(False)

    def test_submission_racing_cart_edit_never_captures_newer_lines(self):
        clients=[Client(),Client()]
        for client in clients:verified_login(client,self.owner)
        barrier=Barrier(2)
        edit={'request_id':str(uuid.uuid4()),'expected_version':1,'catalog_revision':CATALOG['revision'],'lines':copy.deepcopy(CASES[2]['lines'])}
        def run(index):
            try:
                barrier.wait(timeout=10)
                if index==0:
                    response=self.post(client=clients[index])
                    return response.status_code,response.json()
                response=clients[index].post('/api/v1/cart/',data=json.dumps(edit),content_type='application/json')
                return response.status_code,response.json()
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(run,range(2)))
        self.assertEqual(results[1][0],201)
        self.assertIn(results[0][0],[201,409])
        if results[0][0]==201:
            self.assertEqual(results[0][1]['lines'],self.saved['lines'])
            self.assertEqual(results[0][1]['version'],1)
        else:self.assertEqual(QuotationRequest.objects.count(),0)

    def test_owner_status_corrections_without_internal_metadata_or_capture_changes(self):
        first=self.post().json()
        self.assertEqual(first['review_status'],{'code':'awaiting_review','label':'Awaiting review','version':0,'updated_at':None})
        row=QuotationRequest.objects.get()
        reviewer=get_user_model().objects.create_user(username='STAFF_IDENTITY_PRIVATE_SYNTHETIC',is_staff=True)
        generation=uuid.uuid4();private_key=uuid.uuid4();private_mfa=timezone.now()-timedelta(minutes=1)
        for version,decision in enumerate(['needs_information','ready_for_commercial_review','declined','ready_for_commercial_review'],start=1):
            review=QuotationReview.objects.create(quotation=row,version=version,request_id=private_key if version==1 else uuid.uuid4(),
                snapshot_digest='f'*64,decision=decision,reviewer=reviewer,reviewer_generation=generation,mfa_verified_at=private_mfa)
            row.review_version=version;row.save(update_fields=['review_version'])
            detail_response=self.client.get(URL+first['id']+'/');detail=detail_response.json()
            listing=self.client.get(URL).json()['requests'][0]
            status=detail['review_status']
            self.assertEqual(status['code'],decision);self.assertEqual(status['version'],version)
            self.assertEqual(status['updated_at'],review.created_at.isoformat())
            self.assertEqual(set(status),{'code','label','version','updated_at'})
            self.assertEqual(listing['review_status'],status)
            self.assertEqual(detail['lines'],first['lines']);self.assertEqual(detail['evaluation'],first['evaluation'])
            self.assertIsNone(detail['prices']);self.assertIsNone(detail['rights'])
            self.assertFalse(detail['checkout_enabled']);self.assertFalse(detail['acceptance_enabled'])
            self.assertEqual(detail_response['Cache-Control'],'no-store')
            replay=self.post().json()
            self.assertEqual(replay['id'],first['id']);self.assertEqual(replay['review_status'],status)
            for response in [detail,listing,replay]:
                raw=json.dumps(response)
                for value in ['reviewer','mfa_verified_at','reviewer_generation','snapshot_digest','request_id','reviews',reviewer.username,str(generation),str(private_key),private_mfa.isoformat(),'f'*64]:
                    self.assertNotIn(value,raw)
        self.assertEqual(QuotationRequest.objects.count(),1)
        self.assertEqual(QuotationReview.objects.count(),4)
        self.save_cart(1,CASES[2]['lines'])
        with patch.dict(CATALOG,revision='0'*64):
            detail=self.client.get(URL+first['id']+'/').json()
            self.assertEqual(detail['review_status']['version'],4)
            self.assertEqual(detail['lines'],first['lines'])
        verified_login(self.client,self.other)
        self.assertEqual(self.client.get(URL).json()['requests'],[])
        self.assertEqual(self.client.get(URL+first['id']+'/').status_code,404)

    def test_unavailable_status_fails_closed_for_missing_or_unknown_revision(self):
        first=self.post().json();row=QuotationRequest.objects.get()
        row.review_version=3;row.save(update_fields=['review_version'])
        response=self.client.get(URL+first['id']+'/').json()
        self.assertEqual(response['review_status'],{'code':'unavailable','label':'Review status unavailable','version':None,'updated_at':None})
        self.assertEqual(self.client.get(URL).json()['requests'][0]['review_status'],response['review_status'])
        unknown=SimpleNamespace(review_version=3,customer_review_decision='approved',customer_review_time=timezone.now())
        self.assertEqual(customer_review_status(unknown),response['review_status'])
        self.assertFalse(response['checkout_enabled']);self.assertFalse(response['acceptance_enabled'])


class QuotationRecoveryMixin(CartRecoveryMixin):
    def facts(self):
        facts=super().facts()
        facts['quotations']=list(QuotationRequest.objects.order_by('id').values_list(
            'id','cart_id','snapshot_id','request_id','review_version','preparation_version','business_version','created_at'))
        facts['keys']=list(QuotationRequestKey.objects.order_by('id').values_list('id','cart_id','request_id','quotation_id'))
        facts['reviews']=list(QuotationReview.objects.order_by('id').values())
        return facts


class QuotationRecoveryTests(QuotationRecoveryMixin,TransactionTestCase):
    def setUp(self):
        self.owner=get_user_model().objects.create_user(username='quotation-recovery-owner')
        self.client=Client(enforce_csrf_checks=True)
        verified_login(self.client,self.owner)
        self.assertEqual(self.client.get('/api/v1/customer/session/').status_code,200)
        self.saved=self.save_cart(0,CASES[1]['lines'])
        self.payload={'request_id':str(uuid.uuid4()),'cart_id':self.saved['cart_id'],'version':1}

    def save_cart(self,version,lines):
        response=self.client.post('/api/v1/cart/',data=json.dumps({'request_id':str(uuid.uuid4()),
            'expected_version':version,'catalog_revision':CATALOG['revision'],'lines':copy.deepcopy(lines)}),
            content_type='application/json',HTTP_X_CSRFTOKEN=self.client.cookies['csrftoken'].value)
        self.assertEqual(response.status_code,201)
        return response.json()

    def post(self):
        return self.client.post(URL,data=json.dumps(self.payload),content_type='application/json',
            HTTP_X_CSRFTOKEN=self.client.cookies['csrftoken'].value)

    def command_overlap(self,mode,released=False):
        from . import quotation_views
        if mode in ('replay','alias'):
            self.assertEqual(self.post().status_code,201)
            if mode=='alias':self.payload['request_id']=str(uuid.uuid4())
        before=self.facts();capture=quotation_views.capture_quotation
        def interleave(*args,**kwargs):
            self.reset(released)
            return capture(*args,**kwargs)
        with patch.object(quotation_views,'capture_quotation',side_effect=interleave):response=self.post()
        with self.subTest(check='response'):
            self.assertEqual(response.status_code,403,response.content)
            self.assertEqual(response.json(),{'error':'verification_required'})
            self.assertEqual(response['Cache-Control'],'no-store')
        with self.subTest(check='facts'):self.assertEqual(self.facts(),before)
        self.fresh()
        first=self.post();self.assertEqual(first.status_code,201 if mode=='create' else 200)
        committed=self.facts();retry=self.post()
        self.assertEqual(retry.status_code,200);self.assertEqual(retry.json(),first.json())
        self.assertEqual(self.facts(),committed)
        self.assertEqual(QuotationRequest.objects.count(),1)
        self.assertEqual(QuotationRequestKey.objects.count(),2 if mode=='alias' else 1)

    def test_capture_after_quarantine_denies(self):self.command_overlap('create')
    def test_capture_after_quarantine_release_denies(self):self.command_overlap('create',True)
    def test_exact_retry_after_quarantine_denies(self):self.command_overlap('replay')
    def test_exact_retry_after_quarantine_release_denies(self):self.command_overlap('replay',True)
    def test_second_key_after_quarantine_denies(self):self.command_overlap('alias')
    def test_second_key_after_quarantine_release_denies(self):self.command_overlap('alias',True)

    def read_overlap(self,released,single=False):
        from . import quotation_views
        saved=self.post();self.assertEqual(saved.status_code,201)
        path=URL+saved.json()['id']+'/' if single else URL
        before=self.facts();access=quotation_views.local_customer
        def interleave(request):
            result=access(request);self.assertIsNone(result)
            self.reset(released)
            return result
        with patch.object(quotation_views,'local_customer',side_effect=interleave):response=self.client.get(path)
        with self.subTest(check='response'):
            self.assertEqual(response.status_code,403,response.content)
            self.assertEqual(response.json(),{'error':'verification_required'})
            self.assertEqual(response['Cache-Control'],'no-store')
        with self.subTest(check='facts'):self.assertEqual(self.facts(),before)
        self.fresh();response=self.client.get(path);self.assertEqual(response.status_code,200)
        if single:self.assertEqual(response.json(),saved.json())
        else:self.assertEqual(response.json()['requests'][0]['id'],saved.json()['id'])
        self.assertEqual(self.facts(),before)

    def test_list_after_quarantine_denies(self):self.read_overlap(False)
    def test_list_after_quarantine_release_denies(self):self.read_overlap(True)
    def test_detail_after_quarantine_denies(self):self.read_overlap(False,True)
    def test_detail_after_quarantine_release_denies(self):self.read_overlap(True,True)

    def test_epoch_locked_before_quotation_queries_and_serialization(self):
        from django.db.models.query import QuerySet
        from . import quotation_views
        from .models import DraftCart,CartSnapshot,QuotationBusinessScope
        fetch=QuerySet._fetch_all;serialize=quotation_views.quotation_json;seen=set();active=[]
        def observe(query):
            if query.model in (DraftCart,CartSnapshot,QuotationRequest,QuotationRequestKey,QuotationReview,QuotationBusinessScope):
                self.assert_epoch_locked();seen.add(active[0])
            return fetch(query)
        def materialize(row):
            self.assert_epoch_locked();seen.add(active[0]+'-json')
            return serialize(row)
        with patch.object(QuerySet,'_fetch_all',observe),patch.object(quotation_views,'quotation_json',side_effect=materialize):
            active[:]=['create'];first=self.post();self.assertEqual(first.status_code,201)
            active[:]=['replay'];self.assertEqual(self.post().status_code,200)
            self.payload['request_id']=str(uuid.uuid4())
            active[:]=['alias'];self.assertEqual(self.post().status_code,200)
            active[:]=['list'];self.assertEqual(self.client.get(URL).status_code,200)
            active[:]=['detail'];self.assertEqual(self.client.get(URL+first.json()['id']+'/').status_code,200)
        self.assertEqual(seen,{'create','create-json','replay','replay-json','alias','alias-json','list','detail','detail-json'})

    def test_trusted_internal_capture_retains_no_request_interface(self):
        from .quotation_views import capture_quotation
        self.reset(False)
        first,status=capture_quotation(self.owner,self.payload);self.assertEqual(status,201)
        before=self.facts();retry,status=capture_quotation(self.owner,self.payload)
        self.assertEqual(status,200);self.assertEqual(retry,first);self.assertEqual(self.facts(),before)

    def test_fresh_historical_retry_preserves_snapshot_and_review_history(self):
        first=self.post();self.assertEqual(first.status_code,201)
        row=QuotationRequest.objects.get()
        reviewer=get_user_model().objects.create_user(username='quotation-recovery-reviewer',is_staff=True)
        QuotationReview.objects.create(quotation=row,version=1,request_id=uuid.uuid4(),snapshot_digest='f'*64,
            decision='needs_information',reviewer=reviewer,reviewer_generation=uuid.uuid4(),mfa_verified_at=timezone.now())
        row.review_version=1;row.save(update_fields=['review_version'])
        self.save_cart(1,CASES[2]['lines'])
        self.reset(True);self.fresh();before=self.facts()
        with patch.dict(CATALOG,revision='f'*64):
            retry=self.post();self.assertEqual(retry.status_code,200)
            self.assertEqual(retry.json()['id'],first.json()['id'])
            self.assertEqual(retry.json()['lines'],first.json()['lines'])
            self.assertEqual(retry.json()['review_status']['code'],'needs_information')
            self.assertEqual(self.facts(),before)
            self.payload['request_id']=str(uuid.uuid4())
            alias=self.post();self.assertEqual(alias.status_code,200);self.assertEqual(alias.json(),retry.json())
            self.assertEqual(QuotationRequest.objects.count(),1);self.assertEqual(QuotationRequestKey.objects.count(),2)
            self.assertEqual(self.facts()['snapshots'],before['snapshots'])
            self.assertEqual(self.facts()['reviews'],before['reviews'])
