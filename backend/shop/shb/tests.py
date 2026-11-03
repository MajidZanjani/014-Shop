"""Revised SHB common form, scoped invitation and static-route controls."""
from datetime import datetime,timedelta,timezone as dt_timezone
import hashlib
import json
from unittest.mock import patch
import uuid
from django.contrib.auth import get_user_model
from django.test import Client,SimpleTestCase,TransactionTestCase,override_settings
from django.utils import timezone
from .forms import ShopForm


def form_data(**changes):
    data={'variant':'shb-fpga-10h','quantity':'1','company_name':'Synthetic Company Limited',
        'billing_address':'1 Synthetic Test Street','country':'GE','company_phone':'+995 555 010101',
        'contact_name':'Synthetic Customer','same_phone':'on','contact_email':'buyer@synthetic.invalid',
        'privacy_acknowledged':'on','accept_terms':'on','request_id':str(uuid.uuid4())}
    data.update(changes);return data


class ShopClient(Client):
    def __init__(self,*args,**kwargs):
        kwargs.setdefault('HTTP_HOST','localhost')
        super().__init__(*args,**kwargs)


class FormTests(SimpleTestCase):
    def test_common_fields_and_same_phone_are_resolved_without_dossier(self):
        form=ShopForm(form_data(),stage='checkout')
        self.assertTrue(form.is_valid(),form.errors)
        self.assertEqual(form.cleaned_data['quantity'],1)
        self.assertEqual(form.cleaned_data['contact_phone'],form.cleaned_data['company_phone'])
        self.assertEqual(form.cleaned_data['assistance'],'')
        self.assertNotIn('host_id',form.fields);self.assertNotIn('board',form.fields)

    def test_all_six_requested_contact_fields_and_billing_country(self):
        for field in ('company_name','billing_address','company_phone','contact_name','contact_email','country'):
            with self.subTest(field=field):
                form=ShopForm(form_data(**{field:''}),stage='checkout')
                self.assertFalse(form.is_valid());self.assertIn(field,form.errors)
        form=ShopForm(form_data(same_phone='',contact_phone=''),stage='checkout')
        self.assertFalse(form.is_valid());self.assertIn('contact_phone',form.errors)

    def test_asic_short_description_known_reference_and_optional_unknown_context(self):
        form=ShopForm(form_data(variant='shb-asic-25h',assistance='Help with SLL IP integration',design_context='Not yet known',timing='No fixed deadline',accept_terms=''),stage='submit',known_project=True)
        self.assertTrue(form.is_valid(),form.errors)
        form=ShopForm(form_data(variant='shb-asic-25h',assistance='Help',project_reference=''),stage='submit')
        self.assertFalse(form.is_valid());self.assertIn('project_reference',form.errors)
        form=ShopForm(form_data(variant='shb-asic-25h',project_reference='SLL test scope'),stage='submit')
        self.assertFalse(form.is_valid());self.assertIn('assistance',form.errors)

    def test_tax_rules_are_conditional_and_no_blanket_vat_requirement(self):
        self.assertTrue(ShopForm(form_data(tax_not_applicable='on')).is_valid())
        form=ShopForm(form_data(country='US'),tax_rules={'US':{'required_fields':['region','postal_code']}})
        self.assertFalse(form.is_valid());self.assertIn('region',form.errors);self.assertIn('postal_code',form.errors)
        self.assertNotIn('tax_identifier',form.errors)

    def test_exact_positive_quantity_and_forged_customer_money_or_flags(self):
        for value in ('0','-1','1.5','1e2','+1','١','2147483648','true'):
            with self.subTest(quantity=value):self.assertFalse(ShopForm(form_data(quantity=value)).is_valid())
        for field in ('customer_id','total_minor','hours_purchased','discount_bps','approved','ip_product_id'):
            with self.subTest(field=field):self.assertFalse(ShopForm(form_data(**{field:'1'})).is_valid())

    def test_privacy_and_purchase_acceptance_are_separate_and_stage_specific(self):
        form=ShopForm(form_data(privacy_acknowledged='',accept_terms=''),stage='checkout')
        self.assertFalse(form.is_valid());self.assertIn('privacy_acknowledged',form.errors);self.assertIn('accept_terms',form.errors)
        form=ShopForm(form_data(variant='shb-asic-25h',assistance='Help',accept_terms=''),stage='submit',known_project=True)
        self.assertTrue(form.is_valid(),form.errors)


class CalendarExpiryTests(SimpleTestCase):
    """SHB-12: six-month calendar expiry handles month-end and leap-year cases."""

    def _expiry(self,year,month,day,hour=6):
        from datetime import datetime,timezone as utc
        from .invitations import six_month_expiry
        return six_month_expiry(datetime(year,month,day,hour,tzinfo=utc.utc))

    def test_six_month_expiry_rejects_naive_or_non_datetime(self):
        from datetime import datetime
        from .invitations import six_month_expiry
        with self.assertRaises(ValueError):six_month_expiry(datetime(2026,1,1,6))
        with self.assertRaises(ValueError):six_month_expiry('2026-01-01T06:00:00Z')

    def test_normal_same_day_six_month_shift(self):
        from datetime import datetime,timezone as utc
        self.assertEqual(self._expiry(2026,1,15),datetime(2026,7,15,6,tzinfo=utc.utc))
        self.assertEqual(self._expiry(2026,6,1),datetime(2026,12,1,6,tzinfo=utc.utc))

    def test_year_boundary_crossing(self):
        from datetime import datetime,timezone as utc
        self.assertEqual(self._expiry(2026,9,15),datetime(2027,3,15,6,tzinfo=utc.utc))
        self.assertEqual(self._expiry(2026,12,1),datetime(2027,6,1,6,tzinfo=utc.utc))

    def test_month_end_clamps_to_last_day_of_target_month(self):
        from datetime import datetime,timezone as utc
        self.assertEqual(self._expiry(2025,8,31),datetime(2026,2,28,6,tzinfo=utc.utc))
        self.assertEqual(self._expiry(2026,3,31),datetime(2026,9,30,6,tzinfo=utc.utc))
        self.assertEqual(self._expiry(2026,5,31),datetime(2026,11,30,6,tzinfo=utc.utc))
        self.assertEqual(self._expiry(2026,10,31),datetime(2027,4,30,6,tzinfo=utc.utc))

    def test_leap_target_month_keeps_day_29_available(self):
        from datetime import datetime,timezone as utc
        self.assertEqual(self._expiry(2027,8,31),datetime(2028,2,29,6,tzinfo=utc.utc))
        self.assertEqual(self._expiry(2027,8,30),datetime(2028,2,29,6,tzinfo=utc.utc))
        self.assertEqual(self._expiry(2027,8,28),datetime(2028,2,28,6,tzinfo=utc.utc))

    def test_leap_source_day_29_shifts_cleanly(self):
        from datetime import datetime,timezone as utc
        self.assertEqual(self._expiry(2024,2,29),datetime(2024,8,29,6,tzinfo=utc.utc))

    def test_expiry_is_strictly_after_creation(self):
        from datetime import datetime,timezone as utc
        from .invitations import six_month_expiry
        for year,month,day in ((2024,2,29),(2025,8,31),(2026,3,31),(2026,6,15),(2027,12,1)):
            created=datetime(year,month,day,6,tzinfo=utc.utc)
            self.assertGreater(six_month_expiry(created),created)


@override_settings(SHB_SYNTHETIC_FIXTURE=True)
class InvitationTests(TransactionTestCase):
    reset_sequences=True
    client_class=ShopClient

    def setUp(self):
        from .invitations import issue_fixture
        self.customer=get_user_model().objects.create_user(username='shb-fixture-owner')
        self.issuer=get_user_model().objects.create_user(username='shb-fixture-issuer',is_staff=True)
        self.invitation,self.token=issue_fixture(customer=self.customer,issuer=self.issuer,company_name='Synthetic Company Limited',project_reference='SLL fixture')

    def enter(self,client=None):
        return (client or self.client).get('/invite/'+self.token,secure=True)

    def test_calendar_six_months_month_end_and_leap_year(self):
        from .invitations import six_month_expiry
        for created,expected in [('2026-10-30T06:00:00+00:00','2027-04-30T06:00:00+00:00'),('2026-08-31T06:00:00+00:00','2027-02-28T06:00:00+00:00'),('2027-08-31T06:00:00+00:00','2028-02-29T06:00:00+00:00')]:
            self.assertEqual(six_month_expiry(datetime.fromisoformat(created)),datetime.fromisoformat(expected))

    def test_digest_only_reusable_get_and_clean_redirect(self):
        from .models import Invitation,SupportRequest
        before=self.invitation.expires_at
        for _ in range(2):
            response=self.enter();self.assertEqual(response.status_code,302)
            self.assertEqual(response['Location'],'/shop/')
            self.assertNotIn(self.token,response.content.decode())
            self.assertEqual(response['Cache-Control'],'no-store')
            self.assertEqual(response['Referrer-Policy'],'no-referrer')
        row=Invitation.objects.get(pk=self.invitation.pk)
        self.assertEqual(row.expires_at,before)
        self.assertEqual(row.token_digest,hashlib.sha256(self.token.encode()).hexdigest())
        self.assertNotIn(self.token,json.dumps(list(Invitation.objects.values()),default=str))
        self.assertEqual(SupportRequest.objects.count(),0)
        self.assertFalse(self.client.session.get('_auth_user_id'))

    def test_no_unauthorized_base_deep_catalog_or_asset_routes(self):
        for path in ('/','/shop/','/purchase/simple/','/api/v1/catalog/','/api/v1/shb/catalog/','/shop/assets/shop.css','/shop/private/index.html','/static/catalog.json'):
            with self.subTest(path=path):
                response=self.client.get(path,secure=True)
                self.assertIn(response.status_code,(403,404))
                self.assertNotContains(response,'FPGA Supporting Hours Bundle',status_code=response.status_code)

    def test_shb_11_private_release_resists_bypass_vectors_against_manifest(self):
        """SHB-11-01: no bypass of manifest-controlled private release through
        traversal, encoding, trailing-slash, query strings, fragments or
        alternate base paths."""
        bypass_paths=(
            '/_astro/../index.html',
            '/_astro/..%2fprivate-storefront%2findex.html',
            '/_astro/anything.js?preview=true',
            '/_astro/anything.js?sourcemap=1',
            '/_astro/anything.js#preview',
            '/shop/private/support/index.html',
            '/shop/private/_astro/anything.js',
            '/shop/private/index.html.map',
            '/shop/private/private-storefront/index.html',
            '/shop/private/build-probe/index.html',
            '/_astro/.index.html',
            '/_astro//index.html',
            '/_astro/anything.js/../../etc/passwd',
            '/SHOP/private/index.html',
            '/shop/PRIVATE/index.html',
        )
        for path in bypass_paths:
            with self.subTest(path=path):
                try:
                    response=self.client.get(path,secure=True)
                    self.assertIn(response.status_code,(301,302,400,403,404),
                        f'{path} must not expose private content')
                    body=response.content.decode(errors='replace') if response.content else ''
                    for leak in ('FPGA Supporting Hours Bundle','Supporting Hours Bundle','Synthetic Company','shb-fpga-10h','shb-asic-25h','discount_code','order_reference','purchase_token'):
                        self.assertNotIn(leak,body,f'{path} leaked {leak!r} with status {response.status_code}')
                except Exception as error:
                    self.assertIn(type(error).__name__,('DisallowedHost','SuspiciousFileOperation','SuspiciousOperation','ValueError','ResolverMatch'),f'{path} raised unexpected {type(error).__name__}')

    def test_shb_10_private_release_and_astro_assets_refuse_without_invitation(self):
        """SHB-10: deep private release routes and _astro assets refuse without invitation; alt host 404s."""
        import uuid
        private_paths=('/shop/private/index.html','/_astro/'+uuid.uuid4().hex[:16]+'.js','/_astro/'+uuid.uuid4().hex[:16]+'.css','/purchase/shb/'+str(uuid.uuid4())+'/')
        for path in private_paths:
            with self.subTest(path=path):
                response=self.client.get(path,secure=True)
                self.assertIn(response.status_code,(403,404),f'{path} must deny without invitation')
                self.assertNotContains(response,'FPGA Supporting Hours Bundle',status_code=response.status_code)
                self.assertNotContains(response,'Supporting Hours Bundle',status_code=response.status_code)
                self.assertNotContains(response,'Synthetic Company',status_code=response.status_code)
        for path in ('/shop/','/shop/private/index.html','/_astro/anything.js','/invite/'+'A'*43):
            with self.subTest(path=path,host='other.example'):
                try:
                    response=self.client.get(path,secure=True,HTTP_HOST='other.example')
                    self.assertIn(response.status_code,(400,404),f'{path} on alt host must deny')
                except Exception as error:
                    self.assertIn('DisallowedHost',type(error).__name__)

    def test_revoked_expired_and_exact_expiry_deny_surviving_cookie(self):
        from .models import Invitation
        self.enter();self.assertEqual(self.client.get('/shop/',secure=True).status_code,200)
        Invitation.objects.filter(pk=self.invitation.pk).update(revoked_at=timezone.now())
        self.assertEqual(self.client.get('/shop/',secure=True).status_code,403)
        from .invitations import issue_fixture
        self.invitation,self.token=issue_fixture(customer=self.customer,issuer=self.issuer,company_name='Synthetic Company Limited',project_reference='SLL fixture')
        self.enter()
        with patch('shop.shb.invitations.now',return_value=self.invitation.expires_at):
            self.assertEqual(self.enter().status_code,403)
            self.assertEqual(self.client.get('/shop/',secure=True).status_code,403)

    def test_shorter_session_hard_deadline_and_wrong_host(self):
        self.enter()
        deadline=datetime.fromisoformat(self.client.session['shb_session_until'])
        with patch('shop.shb.invitations.now',return_value=deadline):
            self.assertEqual(self.client.get('/shop/',secure=True).status_code,403)
        self.assertEqual(self.client.get('/invite/'+self.token,secure=True,HTTP_HOST='other.example').status_code,400)

    def test_form_has_one_product_exact_variants_and_no_private_prefill(self):
        self.enter();response=self.client.get('/shop/',secure=True)
        self.assertEqual(response.status_code,200)
        for label in ('Supporting Hours Bundle','FPGA Supporting Hours Bundle','ASIC Supporting Hours Bundle','Company Phone','Same as company phone','Contact Email'):
            self.assertContains(response,label)
        self.assertNotContains(response,'Synthetic Company Limited')
        self.assertNotContains(response,'SLL fixture')
        self.assertNotContains(response,'Configure your licence')
        self.assertEqual(response['Cache-Control'],'no-store')

    def test_old_ip_submissions_and_time_panel_are_not_release_routes(self):
        self.enter()
        for path in ('/api/v1/configurations/validate/','/api/v1/configuration-drafts/','/api/v1/cart/','/purchase/cart/','/purchase/checkout-rehearsal/'):
            with self.subTest(path=path):
                self.assertEqual(self.client.post(path,{'product_id':'sll-xspi-mc'},secure=True).status_code,404)
        self.assertEqual(self.client.get('/purchase/checkout-rehearsal/'+str(uuid.uuid4())+'/support/',secure=True).status_code,404)

    def test_common_form_review_derives_hours_and_no_balance(self):
        self.enter()
        response=self.client.post('/purchase/simple/',form_data(quantity='3',action='review'),secure=True)
        self.assertEqual(response.status_code,200)
        self.assertContains(response,'30 hours in this order')
        self.assertContains(response,'local synthetic')
        self.assertNotContains(response,'Available hours')

    def test_asic_submit_persists_once_without_payment_or_time_credit(self):
        from .models import SupportRequest
        from shop.payments.models import SyntheticPaymentAttempt
        from shop.catalog.models import QuotationRequest,SyntheticFulfilment
        self.enter();data=form_data(variant='shb-asic-25h',quantity='2',assistance='Review SLL integration',action='submit',accept_terms='')
        first=self.client.post('/purchase/simple/',data,secure=True)
        self.assertEqual(first.status_code,200)
        self.assertContains(first,'50 requested hours')
        again=self.client.post('/purchase/simple/',data,secure=True)
        self.assertEqual(again.status_code,200)
        self.assertEqual(SupportRequest.objects.count(),1);self.assertEqual(QuotationRequest.objects.count(),1)
        self.assertEqual(SyntheticPaymentAttempt.objects.count(),0);self.assertEqual(SyntheticFulfilment.objects.count(),0)
        row=SupportRequest.objects.get();self.assertEqual(row.quotation.cart.owner_id,self.customer.pk)
        self.assertEqual(row.state,'submitted');self.assertEqual(row.payload['purchase']['hours_purchased'],50)
        self.assertNotIn('remaining_hours',row.payload)
        changed=self.client.post('/purchase/simple/',dict(data,quantity='1'),secure=True)
        self.assertEqual(changed.status_code,409)

    def test_company_and_price_tampering_and_expired_submission_do_not_persist(self):
        from .models import SupportRequest
        self.enter()
        for changes in ({'company_name':'Another Company'},{'customer_id':str(self.customer.pk)},{'total_minor':'1'}):
            response=self.client.post('/purchase/simple/',form_data(variant='shb-asic-25h',assistance='Help',action='submit',**changes),secure=True)
            self.assertIn(response.status_code,(409,422))
        with patch('shop.shb.invitations.now',return_value=self.invitation.expires_at):
            self.assertEqual(self.client.post('/purchase/simple/',form_data(action='submit'),secure=True).status_code,403)
        self.assertEqual(SupportRequest.objects.count(),0)

    def test_unsafe_post_needs_csrf_and_https_and_recovers_from_hold(self):
        from django.test import Client
        from shop.access.models import AccessEpoch
        from shop.shb.models import SupportRequest
        client=ShopClient(enforce_csrf_checks=True)
        self.enter(client)
        self.assertEqual(client.post('/purchase/simple/',form_data(),secure=True,HTTP_ORIGIN='https://localhost').status_code,403)
        self.assertEqual(self.client.get('/invite/'+self.token).status_code,403)
        self.enter()
        from django.db import connection
        from shop.access.recovery import local_recovery_operation
        local_recovery_operation(action='quarantine',request_id=uuid.uuid4(),expected_database=connection.settings_dict['NAME'])
        self.assertEqual(self.client.get('/shop/',secure=True).status_code,503)
        self.assertEqual(self.client.post('/purchase/simple/',form_data(action='submit'),secure=True).status_code,503)
        self.assertEqual(SupportRequest.objects.count(),0)

    def test_native_no_referrer_form_still_requires_valid_csrf_and_same_origin_metadata(self):
        from django.test import Client
        client=ShopClient(enforce_csrf_checks=True);self.enter(client)
        client.get('/purchase/simple/',secure=True)
        token=client.cookies['csrftoken'].value
        data=form_data(action='review',csrfmiddlewaretoken=token)
        self.assertEqual(client.post('/purchase/simple/',data,secure=True,HTTP_ORIGIN='null').status_code,403)
        self.assertEqual(client.post('/purchase/simple/',data,secure=True,HTTP_ORIGIN='null',HTTP_SEC_FETCH_SITE='cross-site').status_code,403)
        self.assertEqual(client.post('/purchase/simple/',data,secure=True,HTTP_ORIGIN='null',HTTP_SEC_FETCH_SITE='same-origin').status_code,200)
        self.assertEqual(client.post('/purchase/simple/',form_data(action='review'),secure=True,HTTP_ORIGIN='null',HTTP_SEC_FETCH_SITE='same-origin').status_code,403)

    def test_immutable_scope_no_extension_unrevoke_or_request_rewrite(self):
        from django.db import DatabaseError,transaction
        from .models import Invitation,SupportRequest
        for change in ({'expires_at':self.invitation.expires_at+timedelta(days=1)},{'company_name':'Different Company'},{'asic_allowed':False}):
            with self.subTest(change=tuple(change)),self.assertRaises(DatabaseError),transaction.atomic():
                Invitation.objects.filter(pk=self.invitation.pk).update(**change)
        self.enter();self.client.post('/purchase/simple/',form_data(variant='shb-asic-25h',assistance='Help',action='submit'),secure=True)
        row=SupportRequest.objects.get()
        with self.assertRaises(DatabaseError),transaction.atomic():SupportRequest.objects.filter(pk=row.pk).update(payload={})
        Invitation.objects.filter(pk=self.invitation.pk).update(revoked_at=timezone.now())
        with self.assertRaises(DatabaseError),transaction.atomic():Invitation.objects.filter(pk=self.invitation.pk).update(revoked_at=None)

    def test_concurrent_same_asic_request_is_one_retained_quotation(self):
        from concurrent.futures import ThreadPoolExecutor
        from django.db import connections
        from django.test import Client
        from threading import Barrier
        from .models import SupportRequest
        from shop.catalog.models import QuotationRequest
        self.enter();cookies=self.client.cookies.copy();barrier=Barrier(2)
        data=form_data(variant='shb-asic-25h',quantity='2',assistance='Shared retry',action='submit')
        def submit():
            try:
                client=ShopClient();client.cookies=cookies.copy();barrier.wait(timeout=5)
                return client.post('/purchase/simple/',data,secure=True).status_code
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:statuses=list(pool.map(lambda _:submit(),range(2)))
        self.assertEqual(statuses,[200,200])
        self.assertEqual(SupportRequest.objects.count(),1);self.assertEqual(QuotationRequest.objects.count(),1)
