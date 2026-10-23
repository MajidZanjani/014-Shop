"""Owner history privacy, stable bounded paging and append/read interleaving."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import json
from unittest.mock import patch
from urllib.parse import parse_qs, urlencode
import uuid
from django.contrib.auth import get_user_model
from django.db import connections, transaction
from django.test import Client, TransactionTestCase, override_settings
from django.utils import timezone
from . import quotation_tests as fixtures, business_rules
from .models import (QuotationRequest, QuotationRequestKey, QuotationReview, QuotationBusinessScope,
                     BusinessDraft, BusinessDraftSnapshot, DraftCart, CartSnapshot)
from .quotation_timeline import PAGE_SIZE, timeline_events
from .tests import verified_login


class TimelineTests(TransactionTestCase):
    save_cart=fixtures.QuotationTests.save_cart
    post=fixtures.QuotationTests.post
    def setUp(self):
        fixtures.QuotationTests.setUp(self)
        self.assertEqual(self.post().status_code,201)
        self.quotation=QuotationRequest.objects.get()
        self.path='/purchase/quotation-timeline/'+str(self.quotation.id)+'/'
        self.reviewer=get_user_model().objects.create_user(username='PRIVATE_REVIEWER_TIMELINE_CANARY',is_staff=True)
        self.generation=uuid.uuid4()
        draft=BusinessDraft.objects.create(owner=self.owner,version=1)
        clean=business_rules.empty_details();clean.update(legal_business_name='PRIVATE_BUSINESS_TIMELINE_CANARY',business_email='private@timeline.synthetic.invalid')
        details=business_rules.resolve_details(clean)
        self.business=BusinessDraftSnapshot.objects.create(draft=draft,version=1,request_id=uuid.uuid4(),
            schema_version=business_rules.SCHEMA_VERSION,source_sha256=business_rules.SOURCE_SHA256,
            submission_digest=business_rules.submission_digest(clean),details=details,evaluation=business_rules.evaluate_details(details))
    def review(self,decision='needs_information'):
        with transaction.atomic():
            q=QuotationRequest.objects.select_for_update().get(pk=self.quotation.pk)
            row=QuotationReview.objects.create(quotation=q,version=q.review_version+1,business_version=q.business_version,
                request_id=uuid.uuid4(),snapshot_digest='e'*64,decision=decision,reviewer=self.reviewer,
                reviewer_generation=self.generation,mfa_verified_at=timezone.now())
            q.review_version+=1;q.save(update_fields=['review_version'])
        return row
    def attach(self):
        q=QuotationRequest.objects.get(pk=self.quotation.pk)
        response=self.client.post('/purchase/quotation-business/'+str(q.id)+'/',data=urlencode({
            'action':'attach','request_id':str(uuid.uuid4()),'expected_scope_version':str(q.business_version),'business_version':'1'}),content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code,303)
    def events(self,response):
        self.assertEqual(response.status_code,200)
        return response.context['timeline']['events']
    def test_capture_empty_history_no_writes_and_security_headers(self):
        before=(QuotationRequest.objects.count(),QuotationRequestKey.objects.count(),QuotationReview.objects.count(),QuotationBusinessScope.objects.count(),BusinessDraftSnapshot.objects.count())
        for _ in range(2):
            response=self.client.get(self.path);events=self.events(response)
            self.assertEqual([e['kind'] for e in events],['capture'])
            self.assertEqual(events[0]['version'],1)
            self.assertEqual(response.context['timeline']['status']['code'],'awaiting_review')
            self.assertIsNone(response.context['timeline']['older_query'])
            self.assertEqual(response['Cache-Control'],'no-store');self.assertEqual(response['Referrer-Policy'],'no-referrer')
            self.assertEqual(response['Vary'],'Cookie');self.assertIn("form-action 'none'",response['Content-Security-Policy'])
            self.assertNotContains(response,'<form');self.assertNotContains(response,'<input')
            self.assertContains(response,'Country and tax choices remain pending')
        after=(QuotationRequest.objects.count(),QuotationRequestKey.objects.count(),QuotationReview.objects.count(),QuotationBusinessScope.objects.count(),BusinessDraftSnapshot.objects.count())
        self.assertEqual(before,after)
    def test_corrections_scope_reset_and_legacy_reviews_stay_attributed(self):
        first=self.review();second=self.review('ready_for_commercial_review')
        self.attach()
        response=self.client.get(self.path);events=self.events(response)
        self.assertEqual(response.context['timeline']['status']['code'],'awaiting_review')
        self.assertEqual([(e['kind'],e['version'],e['business_scope']) for e in events],
            [('business_attachment',1,1),('review',2,0),('review',1,0),('capture',1,0)])
        third=self.review('declined')
        response=self.client.get(self.path);events=self.events(response)
        self.assertEqual(response.context['timeline']['status']['code'],'declined')
        self.assertEqual(events[0]['version'],3);self.assertEqual(events[0]['business_scope'],1)
        self.assertEqual(QuotationReview.objects.get(pk=first.pk).decision,'needs_information')
        self.assertEqual(QuotationReview.objects.get(pk=second.pk).decision,'ready_for_commercial_review')
        self.assertEqual(QuotationReview.objects.get(pk=third.pk).business_version,1)
    def test_event_allowlist_and_private_values_keys_and_attribution_never_render(self):
        record=self.review();self.attach();self.review('ready_for_commercial_review')
        response=self.client.get(self.path);events=self.events(response)
        for event in events:
            self.assertEqual(set(event),{'kind','version','business_scope','business_draft_version','label','created_at'})
        for value in [self.reviewer.username,'PRIVATE_BUSINESS_TIMELINE_CANARY','private@timeline.synthetic.invalid',
                      str(self.generation),str(record.request_id),record.snapshot_digest,self.business.submission_digest]:
            self.assertNotContains(response,value);self.assertNotIn(value,json.dumps(events,default=str))
        for field in business_rules.PENDING:self.assertIsNone(self.business.details[field])
    def test_auth_owner_modes_methods_and_strict_cursor_validation(self):
        self.assertEqual(Client().get(self.path).status_code,401)
        verified_login(self.client,self.other)
        self.assertEqual(self.client.get(self.path).status_code,404)
        self.assertEqual(self.client.get(self.path+'?private=1').status_code,404)
        verified_login(self.client,self.owner)
        for query in ['scope_before=1','review_before=1','scope_before=1&review_before=1&owner=2',
            'scope_before=1&scope_before=1&review_before=1','scope_before=-1&review_before=1',
            'scope_before=01&review_before=1','scope_before=True&review_before=1',
            'scope_before=10000000000&review_before=1','scope_before=2&review_before=1','scope_before=1&review_before=2']:
            self.assertEqual(self.client.get(self.path+'?'+query).status_code,400,query)
        for method in ['post','put','patch','delete']:
            self.assertEqual(getattr(self.client,method)(self.path).status_code,405)
        for mode in ['production','bank-sandbox']:
            with override_settings(SHOP_ENV=mode):self.assertEqual(self.client.get(self.path).status_code,404)
        self.owner.is_staff=True;self.owner.save();self.assertEqual(self.client.get(self.path).status_code,403)
        self.owner.is_staff=False;self.owner.save()
        session=self.client.session;session.pop('shop_verified_identity');session.save()
        self.assertEqual(self.client.get(self.path).status_code,403)
    def test_full_paging_same_timestamps_no_gaps_duplicates_or_unbounded_page(self):
        q=self.quotation
        QuotationBusinessScope.objects.bulk_create([QuotationBusinessScope(quotation=q,version=i,business_snapshot=self.business) for i in range(1,26)])
        QuotationReview.objects.bulk_create([QuotationReview(quotation=q,version=i,business_version=min(i//2,25),
            request_id=uuid.uuid4(),snapshot_digest='e'*64,decision='needs_information',reviewer=self.reviewer,
            reviewer_generation=self.generation,mfa_verified_at=timezone.now()) for i in range(1,61)])
        q.business_version=25;q.review_version=60;q.save()
        # Deliberately equal and non-monotonic clock values cannot reorder revisions.
        instant=timezone.now()-timedelta(days=1)
        QuotationBusinessScope.objects.update(created_at=instant);QuotationReview.objects.update(created_at=instant)
        collected=[];path=self.path;pages=0
        while path:
            response=self.client.get(path);events=self.events(response);pages+=1
            self.assertLessEqual(len(events),PAGE_SIZE+1)
            collected.extend(events)
            older=response.context['timeline']['older_query']
            if older:
                self.assertEqual(set(parse_qs(older)),{'scope_before','review_before'})
                path=self.path+'?'+older
            else:path=None
            self.assertLess(pages,10)
        keys=[(e['kind'],e['version']) for e in collected]
        self.assertEqual(len(keys),86);self.assertEqual(len(set(keys)),86)
        self.assertEqual(keys[-1],('capture',1))
        self.assertEqual([e['version'] for e in collected if e['kind']=='review'],list(range(60,0,-1)))
        self.assertEqual([e['version'] for e in collected if e['kind']=='business_attachment'],list(range(25,0,-1)))
        ordered=[(e['business_scope'],e['kind']=='review',e['version']) for e in collected[:-1]]
        self.assertEqual(ordered,sorted(ordered,reverse=True))
    def test_cross_owner_business_link_hidden_and_cross_cart_capture_denied(self):
        self.attach();draft=self.business.draft;draft.owner=self.other;draft.save()
        response=self.client.get(self.path)
        self.assertFalse(any(e['kind']=='business_attachment' for e in self.events(response)))
        self.assertNotContains(response,'Saved business draft revision 1');self.assertNotContains(response,'PRIVATE_BUSINESS_TIMELINE_CANARY')
        cart=DraftCart.objects.create(owner=self.other,version=17)
        foreign=CartSnapshot.objects.create(cart=cart,version=17,request_id=uuid.uuid4(),catalog_revision=self.quotation.snapshot.catalog_revision,lines=[],evaluation={})
        self.quotation.snapshot=foreign;self.quotation.save(update_fields=['snapshot'])
        self.assertEqual(self.client.get(self.path).status_code,404)
    def test_missing_counter_event_is_unavailable_not_invented(self):
        self.review();self.quotation.review_version=2;self.quotation.save(update_fields=['review_version'])
        response=self.client.get(self.path);events=self.events(response)
        self.assertEqual(response.context['timeline']['status']['code'],'unavailable')
        self.assertEqual([e['version'] for e in events if e['kind']=='review'],[1])
        self.assertNotContains(response,'Review revision 2')
    def test_append_between_parent_read_and_events_keeps_committed_prefix(self):
        self.review()
        def append_after_parent(quotation,before):
            def append():
                connections.close_all()
                try:self.review('declined')
                finally:connections.close_all()
            with ThreadPoolExecutor(max_workers=1) as pool:pool.submit(append).result(timeout=5)
            return timeline_events(quotation,before)
        with patch('shop.catalog.timeline_views.timeline_events',side_effect=append_after_parent):
            response=self.client.get(self.path)
        events=self.events(response)
        self.assertEqual([e['version'] for e in events if e['kind']=='review'],[1])
        self.assertEqual(response.context['timeline']['status']['code'],'needs_information')
        latest=self.client.get(self.path)
        self.assertEqual(self.events(latest)[0]['version'],2)
        self.assertEqual(latest.context['timeline']['status']['code'],'declined')
