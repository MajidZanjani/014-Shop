"""Owner navigation, safe projection and stable bounded read-only pages."""
import uuid
from django.test import Client,TransactionTestCase,override_settings
from django.utils import timezone
from . import quotation_tests as fixtures
from .models import QuotationRequest,QuotationRequestKey,QuotationReview,CartSnapshot,DraftCart
from .quotation_history import PAGE_SIZE
from .tests import verified_login

PATH='/purchase/quotations/'

class QuotationHistoryTests(TransactionTestCase):
    save_cart=fixtures.QuotationTests.save_cart
    post=fixtures.QuotationTests.post
    def setUp(self):
        fixtures.QuotationTests.setUp(self)
        self.assertEqual(self.post().status_code,201)
        self.quotation=QuotationRequest.objects.get()

    def test_safe_projection_links_headers_and_no_domain_writes(self):
        before=(QuotationRequest.objects.count(),QuotationRequestKey.objects.count(),QuotationReview.objects.count(),CartSnapshot.objects.count())
        response=self.client.get(PATH)
        self.assertEqual(response.status_code,200)
        item=response.context['items'][0]
        self.assertEqual(set(item),{'id','created_at','cart_version','status'})
        self.assertEqual(item['status']['code'],'awaiting_review')
        for part in ('timeline','business','documents'):
            self.assertContains(response,'/purchase/quotation-'+part+'/'+str(self.quotation.id)+'/')
        self.assertNotContains(response,str(self.quotation.request_id))
        self.assertNotContains(response,self.owner.username)
        for value in ('<form','<input','<script','snapshot_digest','reviewer','mfa_verified_at'):
            self.assertNotContains(response,value)
        self.assertEqual(response['Cache-Control'],'no-store');self.assertEqual(response['Referrer-Policy'],'no-referrer')
        self.assertEqual(response['Vary'],'Cookie');self.assertIn("form-action 'none'",response['Content-Security-Policy'])
        self.assertEqual(before,(QuotationRequest.objects.count(),QuotationRequestKey.objects.count(),QuotationReview.objects.count(),CartSnapshot.objects.count()))

    def test_auth_owner_privileged_and_environment_boundaries(self):
        self.assertEqual(Client().get(PATH).status_code,401)
        verified_login(self.client,self.other)
        self.assertEqual(self.client.get(PATH).context['items'],[])
        self.assertEqual(self.client.get(PATH+'?before='+str(self.quotation.pk)).status_code,404)
        self.assertEqual(self.client.get(PATH+'?before='+str(uuid.uuid4())).status_code,404)
        self.other.is_staff=True;self.other.save(update_fields=['is_staff'])
        self.assertEqual(self.client.get(PATH).status_code,403)
        for env in ('production','bank-sandbox'):
            with override_settings(SHOP_ENV=env):self.assertEqual(self.client.get(PATH).status_code,404)
        for method in ('post','put','patch','delete'):
            self.assertEqual(getattr(self.client,method)(PATH).status_code,405)

    def test_query_is_strict_and_cursor_canonical(self):
        for query in ('before=','before=bad','before='+str(self.quotation.pk).upper(),
                      'before='+self.quotation.pk.hex,'before=1&before=2','owner=1',
                      'before='+str(self.quotation.pk)+'&next=/private'):
            self.assertEqual(self.client.get(PATH+'?'+query).status_code,400,query)

    def add(self,version):
        original=self.quotation
        snapshot=CartSnapshot.objects.create(cart=original.cart,version=version,request_id=uuid.uuid4(),
            catalog_revision=original.snapshot.catalog_revision,lines=original.snapshot.lines,evaluation=original.snapshot.evaluation)
        return QuotationRequest.objects.create(cart=original.cart,snapshot=snapshot,request_id=uuid.uuid4())

    def test_tied_timestamps_new_insertions_and_empty_tail_have_no_skips(self):
        rows=[self.quotation]+[self.add(n) for n in range(2,PAGE_SIZE+4)]
        QuotationRequest.objects.update(created_at=timezone.now())
        expected=sorted((str(q.pk) for q in rows),reverse=True)
        first=self.client.get(PATH)
        self.assertEqual([q['id'] for q in first.context['items']],expected[:PAGE_SIZE])
        cursor=first.context['older'];self.assertEqual(cursor,expected[PAGE_SIZE-1])
        newest=self.add(PAGE_SIZE+4)
        second=self.client.get(PATH+'?before='+cursor)
        self.assertEqual([q['id'] for q in second.context['items']],expected[PAGE_SIZE:])
        self.assertIsNone(second.context['older'])
        self.assertEqual(self.client.get(PATH).context['items'][0]['id'],str(newest.pk))
        tail=self.client.get(PATH+'?before='+expected[-1]);self.assertEqual(tail.context['items'],[])
        self.assertContains(tail,'No quotation requests on this page.')

    def test_changed_parent_ownership_and_cross_cart_snapshot_stay_hidden(self):
        old=self.quotation.snapshot
        from django.contrib.auth import get_user_model
        third=get_user_model().objects.create_user(username='history-third')
        newcart=DraftCart.objects.create(owner=third)
        QuotationRequest.objects.filter(pk=self.quotation.pk).update(cart=newcart)
        self.assertEqual(self.client.get(PATH).context['items'],[])
        self.assertEqual(self.client.get(PATH+'?before='+str(self.quotation.pk)).status_code,404)
        QuotationRequest.objects.filter(pk=self.quotation.pk).update(cart=old.cart)
        DraftCart.objects.filter(pk=old.cart_id).update(owner=self.other)
        self.assertEqual(self.client.get(PATH).context['items'],[])
