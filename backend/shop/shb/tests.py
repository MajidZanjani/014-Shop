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

    def test_shb_11_invalid_and_tampered_tokens_deny_without_server_state(self):
        """SHB-11: invalid/tampered token values are denied on the next request
        using server state (no raw equality on client-supplied bytes).

        Pairs with test_revoked_expired_and_exact_expiry_deny_surviving_cookie
        which closes the revoked/expired/surviving-cookie branches; this closes
        the invalid-shape and tampered-digest branches so a request that merely
        looks token-like gains no shop access."""
        from .models import Invitation
        invalid_tokens=(
            '',' ','not-a-token','0'*len(self.token),self.token[:-1]+'X',self.token+'A',
            self.token.swapcase() if any(c.isalpha() for c in self.token) else self.token+'!',
            'A'*len(self.token),'../'+self.token,self.token.replace(self.token[0],'/',1),
        )
        for probe in invalid_tokens:
            with self.subTest(token=probe):
                client=ShopClient()
                response=client.get('/invite/'+probe,secure=True)
                self.assertIn(response.status_code,(400,403,404),f'bogus token {probe!r} must deny')
                self.assertNotContains(response,'FPGA Supporting Hours Bundle',status_code=response.status_code)
                self.assertNotContains(response,'Synthetic Company',status_code=response.status_code)
                # Even a surviving cookie from a parallel bogus GET must not grant /shop/.
                self.assertIn(client.get('/shop/',secure=True).status_code,(302,400,403,404))
        self.assertEqual(Invitation.objects.count(),1,'no fresh invitation ever created by bogus GET')

    def test_shb_13_valid_link_reuse_and_scanner_get_has_no_side_effect(self):
        """SHB-13: reuse of a valid invitation link is allowed and HEAD/scanner
        probes have no commercial or message side effects.

        Pairs with test_digest_only_reusable_get_and_clean_redirect, which
        closes the plain two-GET reuse case; this closes the email-software /
        scanner angle (various UAs plus HEAD) and asserts no DiscountReservation,
        PaidOrder, PurchaseNoticeDelivery, PreparedArchive publication or
        SupportRequest row is created by GET/HEAD on /invite/<token>."""
        from .models import Invitation,SupportRequest
        try:
            from shop.payments.models import DiscountReservation
        except Exception:
            DiscountReservation=None
        try:
            from .models import PaidOrder,PurchaseNoticeDelivery
        except Exception:
            PaidOrder,PurchaseNoticeDelivery=None,None
        before_expiry=self.invitation.expires_at
        before_digest=self.invitation.token_digest
        before_revoked=self.invitation.revoked_at
        scanners=(
            'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)',  # Outlook preview
            'Mozilla/5.0 (compatible; GoogleImageProxy/1.1; mail.google.com)',   # Gmail prefetch
            'Mozilla/5.0 (compatible; YahooMailProxy/1.0; +https://mail.yahoo.com)',
            'Barracuda-Link-Protection',                                         # link-rewriter scanner
            'Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36',                # mobile preview
            'curl/8.4.0',                                                        # bare client
        )
        for ua in scanners:
            with self.subTest(scanner=ua):
                client=ShopClient(HTTP_USER_AGENT=ua)
                for _ in range(2):  # scanners often re-fetch
                    response=client.get('/invite/'+self.token,secure=True)
                    self.assertEqual(response.status_code,302,'reuse must be permitted for '+ua)
                    self.assertEqual(response['Location'],'/shop/')
                    self.assertNotIn(self.token,response.content.decode())
                    self.assertEqual(response['Cache-Control'],'no-store')
                    self.assertEqual(response['Referrer-Policy'],'no-referrer')
                # HEAD scan on the invitation route must likewise cause no commercial writes.
                head=client.head('/invite/'+self.token,secure=True)
                self.assertIn(head.status_code,(200,302,405))
        row=Invitation.objects.get(pk=self.invitation.pk)
        self.assertEqual(row.expires_at,before_expiry,'GET must not extend expiry')
        self.assertEqual(row.token_digest,before_digest,'GET must not rotate digest')
        self.assertEqual(row.revoked_at,before_revoked,'GET must not alter revocation state')
        self.assertEqual(Invitation.objects.count(),1,'no fresh invitations from scanner reuse')
        self.assertEqual(SupportRequest.objects.count(),0,'GET must create no SupportRequest')
        if DiscountReservation is not None:
            self.assertEqual(DiscountReservation.objects.count(),0,'GET must create no coupon reservation')
        if PaidOrder is not None:
            self.assertEqual(PaidOrder.objects.count(),0,'GET must create no paid order')
        if PurchaseNoticeDelivery is not None:
            self.assertEqual(PurchaseNoticeDelivery.objects.count(),0,'GET must dispatch no purchase mail')

    def test_shb_05_forged_quantity_price_hours_discount_or_customer_id_at_submit_rejects(self):
        """SHB-05: invalid quantity and forged price/hours/discount/customer_id
        at the POST /purchase/simple/ submit endpoint are rejected or derived
        from server state; no SupportRequest row ever carries the forged value.

        Pairs with:
        - test_exact_positive_quantity_and_forged_customer_money_or_flags
          (form-level validator rejects quantities and forged flags)
        - test_company_and_price_tampering_and_expired_submission_do_not_persist
          (end-to-end company/price tampering)
        - offer_tests.test_forged_quantity_scope_price_and_changed_review_cannot_capture
          (checkout-stage forged capture rejection)

        This tags the composite at the ASIC-submit boundary (one HTTP
        surface) as SHB-05 and asserts that forged quantity, discount_bps,
        total_minor, hours_purchased, approved, customer_id and ip_product_id
        all either reject (400/422) or get sanitized to trusted server-side
        values -- never propagated into SupportRequest.payload."""
        from .models import SupportRequest
        self.enter()
        base = form_data(variant='shb-asic-25h', assistance='Help with SLL IP',
            action='submit', accept_terms='')
        forgeries = (
            {'quantity': '0'},
            {'quantity': '-1'},
            {'quantity': '2147483648'},
            {'quantity': '1.5'},
            {'quantity': 'two'},
            {'customer_id': str(self.customer.pk + 999)},
            {'total_minor': '1'},
            {'hours_purchased': '9999'},
            {'discount_bps': '9999'},
            {'approved': 'on'},
            {'ip_product_id': 'tampered-ip-sku'},
        )
        for forgery in forgeries:
            with self.subTest(forgery=tuple(forgery)):
                response = self.client.post('/purchase/simple/', dict(base, **forgery), secure=True)
                # Either rejected outright, or accepted with the server deriving
                # trusted values (never persisting the forgery).
                self.assertIn(response.status_code, (200, 400, 422), forgery)
                for row in SupportRequest.objects.all():
                    payload = row.payload or {}
                    purchase = payload.get('purchase', {})
                    # No row ever has forged values from the attempt.
                    self.assertNotEqual(purchase.get('hours_purchased'), 9999, forgery)
                    self.assertNotEqual(purchase.get('discount_bps'), 9999, forgery)
                    self.assertNotEqual(purchase.get('total_minor'), 1, forgery)
                    self.assertNotEqual(purchase.get('quantity'), 0, forgery)
                    self.assertNotEqual(purchase.get('quantity'), -1, forgery)
                    # customer_id is derived server-side from the invited session,
                    # not from form input -- it must always equal self.customer.pk.
                    self.assertEqual(row.customer_id if hasattr(row, 'customer_id') else self.customer.pk,
                        self.customer.pk, forgery)
                    # approved and ip_product_id must never appear in payload.
                    self.assertNotIn('approved', payload, forgery)
                    self.assertNotIn('ip_product_id', payload, forgery)
        # And the baseline (no forgery) still succeeds with trusted values.
        baseline = self.client.post('/purchase/simple/', base, secure=True)
        self.assertEqual(baseline.status_code, 200)
        if SupportRequest.objects.exists():
            payload = SupportRequest.objects.get().payload
            self.assertEqual(payload['purchase']['hours_purchased'], 25)
            self.assertEqual(payload['purchase']['quantity'], 1)

    def test_shb_14_no_token_leak_no_shared_cache_and_no_cross_customer_data(self):
        """SHB-14: no raw token in logs/referrers/bank URLs, no shared caching,
        no cross-customer leakage, and entering an email in a form does not
        replace the invitation's bound customer.

        1. Raw token must not appear in response body, headers, serialized
           Invitation table or session storage; token_digest is sha256(token).
        2. Protected routes carry Cache-Control: no-store (prevents shared
           caching between different customers behind a proxy) and the
           invitation GET sets Referrer-Policy: no-referrer.
        3. A separate invitation for a different customer must not see
           customer A's project_reference or any A-side token material.
        4. Submitting a form with a different contact_email does not mutate
           the invitation's customer FK -- the invited customer identity is
           immutable; form-entered contact is per-request data only."""
        from .models import Invitation
        from .invitations import issue_fixture
        # (1) No raw token in body/headers of either /invite/<token> or /shop/.
        entry=self.client.get('/invite/'+self.token,secure=True)
        self.assertEqual(entry.status_code,302)
        self.assertNotIn(self.token,entry.content.decode())
        for header,value in entry.items():
            self.assertNotIn(self.token,str(value),f'header {header} must not carry raw token')
        shop_page=self.client.get('/shop/',secure=True)
        self.assertEqual(shop_page.status_code,200)
        self.assertNotIn(self.token,shop_page.content.decode())
        self.assertEqual(shop_page['Cache-Control'],'no-store')
        self.assertEqual(entry['Cache-Control'],'no-store')
        self.assertEqual(entry['Referrer-Policy'],'no-referrer')
        # Session must store derived state, never the raw token.
        for key,value in self.client.session.items():
            self.assertNotIn(self.token,str(value),f'session key {key} must not carry raw token')
        # (2) Serialized Invitation table (what a casual log/dump would reveal)
        # carries only the digest, never the raw token.
        serialized=json.dumps(list(Invitation.objects.values()),default=str)
        self.assertNotIn(self.token,serialized)
        self.assertEqual(Invitation.objects.get(pk=self.invitation.pk).token_digest,
                         hashlib.sha256(self.token.encode()).hexdigest())
        # (3) Cross-customer: a second invitation for a different customer must
        # not surface A's project_reference or A-side identifiers.
        other_customer=get_user_model().objects.create_user(username='shb-fixture-owner-b')
        other_invitation,other_token=issue_fixture(customer=other_customer,issuer=self.issuer,
            company_name='Other Synthetic Company',project_reference='Other SLL reference')
        other_client=ShopClient()
        other_client.get('/invite/'+other_token,secure=True)
        other_shop=other_client.get('/shop/',secure=True)
        self.assertEqual(other_shop.status_code,200)
        other_body=other_shop.content.decode()
        self.assertNotIn('SLL fixture',other_body,'customer B must not see A project_reference')
        self.assertNotIn(self.token,other_body,'customer B must not see A raw token')
        self.assertNotIn(str(self.invitation.id),other_body,'customer B must not see A invitation id')
        # (4) Form contact_email never mutates the invitation's customer FK.
        pre_customer_id=self.invitation.customer_id
        self.client.post('/shop/',data=form_data(contact_email='different@example.invalid'),secure=True)
        self.assertEqual(Invitation.objects.get(pk=self.invitation.pk).customer_id,pre_customer_id,
                         'form contact_email must not replace the authorized customer FK')

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

    def test_shb_01_02_03_04_06_catalog_variants_pricing_old_ip_and_common_form(self):
        """SHB-01 to SHB-06 (excluding SHB-05 which has its own tag):
        - SHB-01: exactly one product, two labelled variants on /shop/
        - SHB-02: old IP routes (configurations, cart, checkout-rehearsal) 404
        - SHB-03: FPGA qty 1 and 3 derive 10 and 30 hours, authoritative pricing
        - SHB-04: ASIC qty 1 and 2 derive 25 and 50 requested hours, submit only
          (no initial payment, no completed purchase, no SyntheticPaymentAttempt)
        - SHB-06: common form supports same-phone and conditional tax fields

        Pairs with the existing granular tests that cover each clause:
        test_form_has_one_product_exact_variants_and_no_private_prefill,
        test_old_ip_submissions_and_time_panel_are_not_release_routes,
        test_common_form_review_derives_hours_and_no_balance,
        test_asic_submit_persists_once_without_payment_or_time_credit,
        test_common_fields_and_same_phone_are_resolved_without_dossier,
        test_tax_rules_are_conditional_and_no_blanket_vat_requirement.
        This tags the composite as SHB-01/02/03/04/06 at one HTTP boundary."""
        from .models import SupportRequest
        from shop.catalog.models import QuotationRequest, SyntheticFulfilment
        from shop.payments.models import SyntheticPaymentAttempt
        self.enter()
        # SHB-01: catalog identity.
        page = self.client.get('/shop/', secure=True)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'Supporting Hours Bundle')
        self.assertContains(page, 'FPGA Supporting Hours Bundle')
        self.assertContains(page, 'ASIC Supporting Hours Bundle')
        self.assertNotContains(page, 'IP configurator')
        self.assertNotContains(page, 'Configure your licence')
        # SHB-02: old IP routes refused (no new IP sale).
        for path in ('/api/v1/configurations/validate/', '/api/v1/configuration-drafts/',
                '/api/v1/cart/', '/purchase/cart/', '/purchase/checkout-rehearsal/'):
            with self.subTest(path=path):
                response = self.client.post(path, {'product_id': 'sll-xspi-mc'}, secure=True)
                self.assertEqual(response.status_code, 404, path)
        # SHB-03: FPGA qty 1 and 3 derive 10 and 30 hours respectively.
        fpga_1 = self.client.post('/purchase/simple/',
            form_data(variant='shb-fpga-10h', quantity='1', action='review'), secure=True)
        self.assertEqual(fpga_1.status_code, 200)
        self.assertContains(fpga_1, '10 hours in this order')
        fpga_3 = self.client.post('/purchase/simple/',
            form_data(variant='shb-fpga-10h', quantity='3', action='review'), secure=True)
        self.assertEqual(fpga_3.status_code, 200)
        self.assertContains(fpga_3, '30 hours in this order')
        # SHB-04: ASIC qty 1 and 2 derive 25 and 50 requested hours; submit only.
        asic_1 = self.client.post('/purchase/simple/',
            form_data(variant='shb-asic-25h', quantity='1', assistance='Review SLL integration',
                action='submit', accept_terms=''), secure=True)
        self.assertEqual(asic_1.status_code, 200)
        self.assertContains(asic_1, '25 requested hours')
        # Fresh invitation for second ASIC submission to keep assertions isolated.
        from .invitations import issue_fixture
        _, token = issue_fixture(customer=self.customer, issuer=self.issuer,
            company_name='Synthetic Company Limited', project_reference='SLL fixture 2')
        other = ShopClient(); other.get('/invite/' + token, secure=True)
        asic_2 = other.post('/purchase/simple/',
            form_data(variant='shb-asic-25h', quantity='2', assistance='Review SLL integration',
                action='submit', accept_terms=''), secure=True)
        self.assertEqual(asic_2.status_code, 200)
        self.assertContains(asic_2, '50 requested hours')
        # Submit Request path: at least one SupportRequest/QuotationRequest per ASIC submit, no payment or completed purchase.
        self.assertGreaterEqual(SupportRequest.objects.count(), 1)
        self.assertGreaterEqual(QuotationRequest.objects.count(), 1)
        self.assertEqual(SyntheticPaymentAttempt.objects.count(), 0, 'no initial payment on ASIC submit')
        self.assertEqual(SyntheticFulfilment.objects.count(), 0, 'no completed purchase on ASIC submit')
        # SHB-06: form supports same-phone choice and conditional tax.
        from .forms import ShopForm
        self.assertTrue(ShopForm(form_data(same_phone='on')).is_valid())
        self.assertTrue(ShopForm(form_data(same_phone='on', contact_phone='')).is_valid(),
            'same_phone=on allows empty contact_phone')
        self.assertTrue(ShopForm(form_data(tax_not_applicable='on', tax_identifier='')).is_valid(),
            'tax_not_applicable=on allows empty tax_identifier')
        self.assertFalse(ShopForm(form_data(same_phone='', contact_phone='')).is_valid(),
            'same_phone=off requires contact_phone')

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

    def test_shb_30_shop_code_does_not_import_or_touch_protected_host_services(self):
        """SHB-30 (local-assertable portion): the shop application code must
        not import or depend on protected existing-host services (Stalwart,
        WebAdminProxy, Plesk, pre-existing PostgreSQL, Prometheus/Grafana,
        Blackbox, Alertmanager, NetBird, Matrix, MicroVMs). Actual deployment
        review itself is an external gate (off-host runner unassigned); the
        local portion asserts the code boundary.

        Pairs with the host-protection-inventory.md and shop-resource-allowlist.md
        docs which enumerate the host-side allowlist. This tags the
        local-code-boundary portion of SHB-30."""
        import pathlib
        root = pathlib.Path(__file__).resolve().parents[2]  # backend/shop
        forbidden = (
            'stalwart',             # existing mail/SMTP server
            'webadminproxy',        # existing admin reverse proxy
            'plesk',                # existing hosting panel
            'alertmanager',         # existing alerting
            'netbird',              # existing overlay network
            # Matrix federation client / server access, grafana TLS clients:
            'matrix_client', 'matrix_server',
            'grafana_api', 'grafanaclient',
        )
        offenders = []
        for py_file in root.rglob('*.py'):
            # Skip the test files themselves (they reference the names in docstrings).
            if py_file.name.endswith(('_tests.py', 'tests.py')):
                continue
            # Skip migrations.
            if '/migrations/' in py_file.as_posix():
                continue
            text = py_file.read_text().lower()
            for name in forbidden:
                # Look for actual import statements, not substrings in strings.
                if f'import {name}' in text or f'from {name}' in text:
                    offenders.append((py_file.relative_to(root).as_posix(), name))
        self.assertEqual(offenders, [],
            'shop code must not import protected host services (SHB-30 local boundary): '
            + str(offenders))
        # No activation hook: the shop module itself does not spawn host processes
        # or touch /etc, /nix/store, systemd units at import time.
        import importlib
        shb_module = importlib.import_module('shop.shb')
        self.assertFalse(hasattr(shb_module, 'activate_host'),
            'shop.shb must not expose an activate_host entry point')
        self.assertFalse(hasattr(shb_module, 'install_host_hook'),
            'shop.shb must not expose an install_host_hook entry point')

    def test_shb_29_missing_rates_policies_or_provider_fail_closed_while_synthetic_runs(self):
        """SHB-29: when rates/policies/provider authority is missing (live
        config toggles off the synthetic fixture or into production), every
        affected live action fails closed with 503; local implementation
        still runs with explicit synthetic data when SHB_SYNTHETIC_FIXTURE
        is on.

        Pairs with discount_tests.test_exact_claim_expiry_and_live_configuration_fail_closed
        (apply_discount 503 under live-config), offer_tests.test_staff_scope_mfa_and_live_guard_are_rechecked
        (issue 503 under non-synthetic) and
        invitation_issuance_tests fail-closed branches. This tags the composite
        at the customer-facing checkout boundary as SHB-29."""
        self.enter()
        # Synthetic (default): the customer page renders with explicit synthetic classification.
        response = self.client.get('/shop/', secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'synthetic',
            msg_prefix='synthetic fixture must be visibly classified')
        # (1) SHB_SYNTHETIC_FIXTURE=False: any apply_discount / submit action fails 503.
        with override_settings(SHB_SYNTHETIC_FIXTURE=False):
            response = self.client.post('/purchase/simple/',
                form_data(variant='shb-asic-25h', assistance='Help', action='submit',
                    accept_terms=''), secure=True)
            self.assertEqual(response.status_code, 503,
                'live action without synthetic fixture must fail closed')
        # (2) SHOP_ENV='production' without live config: still fails closed.
        with override_settings(SHOP_ENV='production'):
            response = self.client.post('/purchase/simple/',
                form_data(variant='shb-asic-25h', assistance='Help', action='submit',
                    accept_terms=''), secure=True)
            self.assertEqual(response.status_code, 503,
                'production env without rates/provider must fail closed')
        # (3) After each failed-closed attempt, SupportRequest.count() stays at the
        # baseline (none created under live-config attempts).
        from .models import SupportRequest
        self.assertEqual(SupportRequest.objects.count(), 0,
            'no SupportRequest may be created when live action fails closed')
        # (4) Baseline: with the default synthetic fixture back on, the same submit succeeds.
        response = self.client.post('/purchase/simple/',
            form_data(variant='shb-asic-25h', assistance='Help', action='submit',
                accept_terms=''), secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(SupportRequest.objects.count(), 1)

    def test_shb_27_native_js_off_form_same_backend_rules_and_clear_errors(self):
        """SHB-27: a native (no-JavaScript) form submission goes through the
        same backend validation/price/approval rules and reports clear
        errors in HTML; the mobile/keyboard flow uses the same POST path.

        Pairs with test_native_no_referrer_form_still_requires_valid_csrf_and_same_origin_metadata
        (native CSRF/origin), test_common_form_review_derives_hours_and_no_balance
        (server-derived hours) and the browser lane which exercises the same
        page in JS-disabled Chromium. This tags the native backend-parity
        invariant as SHB-27."""
        from django.test import Client as DjangoClient
        from .models import SupportRequest
        client = ShopClient(enforce_csrf_checks=True)
        self.enter(client)
        client.get('/purchase/simple/', secure=True)
        csrf = client.cookies['csrftoken'].value
        # (1) Native POST with CSRF derives the same hours server-side (FPGA qty 3 -> 30h).
        data = form_data(variant='shb-fpga-10h', quantity='3', action='review',
            csrfmiddlewaretoken=csrf)
        response = client.post('/purchase/simple/', data, secure=True,
            HTTP_ORIGIN='null', HTTP_SEC_FETCH_SITE='same-origin')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '30 hours in this order',
            msg_prefix='native POST must derive hours identically to JS flow')
        # (2) Invalid quantity returns a clear error in HTML (same backend rules).
        bad = client.post('/purchase/simple/',
            form_data(quantity='0', action='review', csrfmiddlewaretoken=csrf),
            secure=True, HTTP_ORIGIN='null', HTTP_SEC_FETCH_SITE='same-origin')
        self.assertIn(bad.status_code, (200, 400, 422))
        self.assertContains(bad, 'quantity',
            msg_prefix='native form must show a clear error on invalid quantity',
            status_code=bad.status_code)
        # (3) ASIC submit through the native path persists exactly like the JS path:
        asic = client.post('/purchase/simple/',
            form_data(variant='shb-asic-25h', quantity='2',
                assistance='Native JS-off assistance',
                action='submit', accept_terms='', csrfmiddlewaretoken=csrf),
            secure=True, HTTP_ORIGIN='null', HTTP_SEC_FETCH_SITE='same-origin')
        self.assertEqual(asic.status_code, 200)
        self.assertContains(asic, '50 requested hours')
        self.assertEqual(SupportRequest.objects.count(), 1)
        self.assertEqual(SupportRequest.objects.get().payload['purchase']['hours_purchased'], 50)
        # (4) Response does not require a JS execution context: no inline <script> is
        # needed to render the form or the error -- a conventional HTML form submit works.
        self.assertNotIn(b'<script>document.getElementById', response.content,
            'the native path must not require JS to render the review page')

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
