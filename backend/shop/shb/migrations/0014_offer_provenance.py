"""Freeze dated reviewed ASIC offers and extend the same payment/coupon invariants."""
from importlib import import_module
from django.db import migrations

SQL = """
CREATE FUNCTION public.shb_offer_guard() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog AS $$
DECLARE r public.shb_supportrequest%ROWTYPE; q public.catalog_quotationrequest%ROWTYPE;
        p jsonb; policy jsonb; owner_id bigint; company text; project text; has_discount boolean;
BEGIN
  IF TG_OP='DELETE' THEN RAISE EXCEPTION 'shb immutable ASIC offer'; END IF;
  SELECT * INTO r FROM public.shb_supportrequest WHERE id=NEW.request_id FOR UPDATE;
  SELECT * INTO q FROM public.catalog_quotationrequest WHERE id=r.quotation_id;
  SELECT i.customer_id,i.company_name INTO owner_id,company FROM public.shb_invitation i WHERE i.id=r.invitation_id;
  p:=NEW.payload->'purchase'; policy:=NEW.payload->'policy';
  project:=COALESCE(NULLIF(r.payload->>'known_project_reference',''),r.payload->'details'->>'project_reference');
  IF TG_OP='UPDATE' THEN
    IF (to_jsonb(NEW)-ARRAY['state','published_at','archive_receipt']) IS DISTINCT FROM
        (to_jsonb(OLD)-ARRAY['state','published_at','archive_receipt'])
    THEN RAISE EXCEPTION 'shb immutable ASIC offer'; END IF;
    IF OLD.state='issued' AND NEW.state IN ('paid','closed') AND NEW.published_at=OLD.published_at
      AND NEW.archive_receipt=OLD.archive_receipt THEN
      IF NEW.state='paid' THEN
        PERFORM 1 FROM public.shb_paidorder o JOIN public.catalog_syntheticcheckoutacceptance a ON a.id=o.acceptance_id
          JOIN public.shb_supportcheckout s ON s.checkout_id=a.checkout_id WHERE s.offer_id=NEW.id;
      ELSE
        PERFORM 1 FROM public.shb_checkoutclosure c JOIN public.catalog_syntheticcheckoutacceptance a ON a.id=c.acceptance_id
          JOIN public.shb_supportcheckout s ON s.checkout_id=a.checkout_id
          WHERE s.offer_id=NEW.id AND c.applied_at IS NOT NULL AND c.archive_receipt <> '{}'::jsonb;
      END IF;
      IF NOT FOUND THEN RAISE EXCEPTION 'shb offer requires matching paid or safe closed outcome'; END IF;
      RETURN NEW;
    END IF;
    IF OLD.state <> 'prepared' OR NEW.state <> 'issued' OR OLD.published_at IS NOT NULL
      OR NEW.published_at IS NULL OR NEW.archive_receipt->>'evidence_id' IS DISTINCT FROM NEW.id::text
      OR NEW.archive_receipt->>'sha256' IS DISTINCT FROM NEW.sha256
    THEN RAISE EXCEPTION 'shb offer requires recoverable publication'; END IF;
  ELSIF NEW.state <> 'prepared' OR NEW.published_at IS NOT NULL OR NEW.archive_receipt <> '{}'::jsonb THEN
    RAISE EXCEPTION 'shb offer must prepare before publication';
  END IF;
  PERFORM 1 FROM public.shb_supportrequestreview e
    JOIN public.catalog_quotationreview v ON v.id=e.review_id
    JOIN public.access_staffcredential c ON c.user_id=NEW.issuer_id
    JOIN public.access_staffquotationgrant g ON g.user_id=NEW.issuer_id AND g.quotation_id=r.quotation_id
    WHERE e.review_id=NEW.review_id AND e.request_id=r.id AND v.quotation_id=r.quotation_id
      AND v.snapshot_digest=r.sha256 AND v.business_version=r.revision AND v.version=q.review_version
      AND v.decision='ready_for_commercial_review' AND c.enabled AND c.generation=NEW.issuer_generation
      AND g.business_scope_version=r.revision AND NEW.mfa_verified_at<=NEW.issued_at
      AND NEW.mfa_verified_at>=NEW.issued_at-interval '5 minutes'
      AND NEW.payload->'technical_review'->>'id'=e.review_id::text
      AND NEW.payload->'technical_review'->>'reviewer_id'=v.reviewer_id::text
      AND NEW.payload->'technical_review'->>'credential_generation'=v.reviewer_generation::text
      AND (NEW.payload->'technical_review'->>'mfa_verified_at')::timestamptz=v.mfa_verified_at
      AND NEW.payload->'technical_review'->>'decision'=v.decision
      AND NEW.payload->'technical_review'->>'scope_sha256'=v.snapshot_digest;
  IF NOT FOUND OR r.state <> 'under_review' OR statement_timestamp()>=NEW.expires_at
    OR NEW.issued_at>clock_timestamp() OR (TG_OP='INSERT' AND NEW.issued_at<clock_timestamp()-interval '30 seconds')
    OR NEW.payload->>'kind' IS DISTINCT FROM 'shb-asic-offer'
    OR NEW.payload->>'request_id' IS DISTINCT FROM r.id::text
    OR NEW.payload->>'request_sha256' IS DISTINCT FROM r.sha256
    OR NEW.payload->>'request_revision' IS DISTINCT FROM r.revision::text
    OR NEW.payload->>'customer_id' IS DISTINCT FROM owner_id::text
    OR NEW.payload->>'company_name' IS DISTINCT FROM company
    OR NEW.payload->>'review_id' IS DISTINCT FROM NEW.review_id::text
    OR NEW.payload->>'review_version' IS DISTINCT FROM q.review_version::text
    OR NEW.payload->>'revision' IS DISTINCT FROM NEW.revision::text
    OR NEW.payload->'issued_by'->>'user_id' IS DISTINCT FROM NEW.issuer_id::text
    OR NEW.payload->'issued_by'->>'credential_generation' IS DISTINCT FROM NEW.issuer_generation::text
    OR (NEW.payload->'issued_by'->>'mfa_verified_at')::timestamptz IS DISTINCT FROM NEW.mfa_verified_at
    OR (NEW.payload->>'issued_at')::timestamptz IS DISTINCT FROM NEW.issued_at
    OR (NEW.payload->>'expires_at')::timestamptz IS DISTINCT FROM NEW.expires_at
    OR NEW.expires_at IS DISTINCT FROM NEW.issued_at+interval '14 days'
    OR NEW.payload->>'offer_policy_revision' IS DISTINCT FROM 'synthetic-14-calendar-day-offer-v1'
    OR NEW.payload->'scope'->>'project_reference' IS DISTINCT FROM project
    OR NEW.payload->'scope'->>'assistance' IS DISTINCT FROM r.payload->'details'->>'assistance'
    OR NEW.payload->'scope'->>'design_context' IS DISTINCT FROM r.payload->'details'->>'design_context'
    OR NEW.payload->'scope'->>'requested_timing' IS DISTINCT FROM r.payload->'details'->>'timing'
    OR COALESCE(length(trim(NEW.payload->'scope'->>'prerequisites')),0) NOT BETWEEN 1 AND 1000
    OR COALESCE(length(trim(NEW.payload->'scope'->>'exclusions')),0) NOT BETWEEN 1 AND 1000
    OR p->>'variant_id' IS DISTINCT FROM 'shb-asic-25h' OR p->>'hours_per_bundle' IS DISTINCT FROM '25'
    OR p->>'quantity' IS DISTINCT FROM r.payload->'purchase'->>'quantity'
    OR (p->>'hours_purchased')::bigint IS DISTINCT FROM 25*(p->>'quantity')::bigint
    OR p->>'currency' IS DISTINCT FROM policy->>'currency' OR policy->>'currency' IS DISTINCT FROM 'EUR'
    OR p->>'hourly_minor' IS DISTINCT FROM policy->>'asic_hourly_minor'
    OR (policy->>'asic_hourly_minor')::bigint <= (policy->>'fpga_hourly_minor')::bigint
    OR (p->>'bundle_minor')::bigint IS DISTINCT FROM 25*(p->>'hourly_minor')::bigint
    OR (p->>'subtotal_minor')::bigint IS DISTINCT FROM (p->>'bundle_minor')::bigint*(p->>'quantity')::bigint
    OR (p->>'discount_bps')::bigint NOT BETWEEN 0 AND 9999
    OR (p->>'discount_minor')::bigint IS DISTINCT FROM ((p->>'subtotal_minor')::bigint*(p->>'discount_bps')::bigint+5000)/10000
    OR (p->>'tax_minor')::bigint IS DISTINCT FROM (((p->>'subtotal_minor')::bigint-(p->>'discount_minor')::bigint)*(policy->>'tax_bps')::bigint+5000)/10000
    OR (p->>'total_minor')::bigint IS DISTINCT FROM (p->>'subtotal_minor')::bigint-(p->>'discount_minor')::bigint+(p->>'tax_minor')::bigint
    OR (p->>'total_minor')::bigint NOT BETWEEN (policy->>'bank_min_minor')::bigint AND (policy->>'bank_max_minor')::bigint
    OR NEW.payload->>'evidence_class' IS DISTINCT FROM 'local-synthetic'
    OR NEW.payload->'effects_authorized' IS DISTINCT FROM 'false'::jsonb
    OR NEW.payload->'financial_confirmation' IS DISTINCT FROM 'false'::jsonb
    OR NEW.payload->>'support_tracking' IS DISTINCT FROM 'manual-outside-shop'
    OR policy->>'evidence_class' IS DISTINCT FROM 'local-synthetic'
    OR NEW.payload->'required_document_ids' IS DISTINCT FROM '["terms","support","refund","asic"]'::jsonb
    OR jsonb_array_length(NEW.payload->'documents'->'documents') <> 5
  THEN RAISE EXCEPTION 'shb offer requires exact reviewed request and synthetic standard terms'; END IF;
  SELECT EXISTS(SELECT 1 FROM public.shb_discountreservation h WHERE h.request_id=r.id AND h.state='reserved'
    AND h.snapshot=NEW.payload->'purchase'->'discount_policy'
    AND h.snapshot->>'percentage_bps'=p->>'discount_bps') INTO has_discount;
  IF (p ? 'discount_policy') IS DISTINCT FROM has_discount
    OR (NOT (p ? 'discount_policy') AND (p->>'discount_bps' <> '0' OR EXISTS(
      SELECT 1 FROM public.shb_discountreservation h WHERE h.request_id=r.id AND h.state='reserved')))
  THEN RAISE EXCEPTION 'shb offer must preserve held request concession'; END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER shb_offer_guard BEFORE INSERT OR UPDATE OR DELETE ON public.shb_supportoffer
FOR EACH ROW EXECUTE FUNCTION public.shb_offer_guard();

CREATE FUNCTION public.shb_offer_commit_guard() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog AS $$
BEGIN
  IF EXISTS(SELECT 1 FROM public.shb_supportoffer f JOIN public.shb_supportrequest r ON r.id=f.request_id
    WHERE f.id=NEW.id AND (f.state='issued' AND r.state<>'offer_issued' OR f.state='paid' AND r.state<>'paid'))
  THEN RAISE EXCEPTION 'shb offer and request outcome must commit together'; END IF;
  RETURN NULL;
END $$;
CREATE CONSTRAINT TRIGGER shb_offer_commit_guard AFTER INSERT OR UPDATE ON public.shb_supportoffer
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION public.shb_offer_commit_guard();

CREATE FUNCTION public.shb_reservation_matches(hold_checkout uuid,hold_request uuid,checkout uuid) RETURNS boolean
LANGUAGE sql STABLE SET search_path=pg_catalog AS $$
  SELECT COALESCE(hold_request IS NULL AND hold_checkout=checkout,FALSE) OR
    (hold_checkout IS NULL AND EXISTS(SELECT 1 FROM public.shb_supportcheckout s
      JOIN public.shb_supportoffer f ON f.id=s.offer_id WHERE s.checkout_id=checkout AND f.request_id=hold_request))
$$;

CREATE OR REPLACE FUNCTION public.shb_checkout_scope_guard() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog AS $$
DECLARE capture jsonb; invite public.shb_invitation%ROWTYPE; offer public.shb_supportoffer%ROWTYPE;
BEGIN
  IF TG_OP <> 'INSERT' THEN RAISE EXCEPTION 'shb immutable checkout scope'; END IF;
  SELECT * INTO invite FROM public.shb_invitation WHERE id=NEW.invitation_id;
  SELECT c.snapshot INTO capture FROM public.catalog_syntheticcheckout c
    JOIN public.catalog_cartsnapshot s ON s.id=c.cart_snapshot_id
    JOIN public.catalog_draftcart d ON d.id=s.cart_id
    WHERE c.id=NEW.checkout_id AND c.owner_id=invite.customer_id AND d.owner_id=invite.customer_id
      AND c.business_snapshot_id IS NULL AND c.request_id=NEW.request_id AND s.request_id=NEW.request_id
      AND s.lines=jsonb_build_array(c.snapshot->'purchase');
  IF capture IS NULL OR capture->>'release' IS DISTINCT FROM 'shb-1.1'
    OR capture->>'invitation_id' IS DISTINCT FROM invite.id::text
    OR capture->>'customer_id' IS DISTINCT FROM invite.customer_id::text
    OR capture->>'request_id' IS DISTINCT FROM NEW.request_id::text
    OR capture->>'submission_sha256' IS DISTINCT FROM NEW.submission_sha256
    OR capture->>'total_minor' IS DISTINCT FROM capture->'purchase'->>'total_minor'
    OR capture->>'currency' IS DISTINCT FROM capture->'purchase'->>'currency'
    OR capture->>'evidence_class' IS DISTINCT FROM 'local-synthetic'
    OR capture->'effects_authorized' IS DISTINCT FROM 'false'::jsonb
    OR capture->'financial_confirmation' IS DISTINCT FROM 'false'::jsonb
    OR capture->>'support_tracking' IS DISTINCT FROM 'manual-outside-shop'
    OR capture->'named_identity_verified' IS DISTINCT FROM 'false'::jsonb
    OR invite.revoked_at IS NOT NULL OR invite.created_at>statement_timestamp() OR statement_timestamp()>=invite.expires_at
    OR (capture->'purchase'->>'quantity')::bigint NOT BETWEEN 1 AND 2147483647
  THEN RAISE EXCEPTION 'shb checkout scope provenance'; END IF;
  IF NEW.offer_id IS NULL THEN
    IF NOT invite.fpga_eligible OR capture ? 'asic_offer'
      OR capture->'purchase'->>'variant_id' IS DISTINCT FROM 'shb-fpga-10h'
      OR capture->'purchase'->>'hours_per_bundle' IS DISTINCT FROM '10'
      OR (capture->'purchase'->>'hours_purchased')::bigint IS DISTINCT FROM 10*(capture->'purchase'->>'quantity')::bigint
    THEN RAISE EXCEPTION 'shb FPGA checkout scope provenance'; END IF;
  ELSE
    SELECT * INTO offer FROM public.shb_supportoffer WHERE id=NEW.offer_id FOR UPDATE;
    PERFORM 1 FROM public.shb_supportrequest r WHERE r.id=offer.request_id AND r.state='offer_issued'
      AND r.sha256=offer.payload->>'request_sha256' AND r.revision::text=offer.payload->>'request_revision';
    IF NOT FOUND OR NOT invite.asic_allowed OR offer.state<>'issued' OR offer.published_at IS NULL
      OR offer.archive_receipt='{}'::jsonb OR statement_timestamp()>=offer.expires_at
      OR offer.payload->>'customer_id' IS DISTINCT FROM invite.customer_id::text
      OR offer.payload->>'company_name' IS DISTINCT FROM invite.company_name
      OR (invite.project_reference <> '' AND invite.project_reference IS DISTINCT FROM offer.payload->'scope'->>'project_reference')
      OR capture->'purchase' IS DISTINCT FROM offer.payload->'purchase'
      OR capture->'documents' IS DISTINCT FROM offer.payload->'documents'
      OR capture->'required_document_ids' IS DISTINCT FROM offer.payload->'required_document_ids'
      OR capture->'policy' IS DISTINCT FROM offer.payload->'policy'
      OR capture->'asic_offer' IS DISTINCT FROM jsonb_build_object('id',offer.id::text,'sha256',offer.sha256,'payload',offer.payload)
      OR (capture->>'review_expires_at')::timestamptz>offer.expires_at
      OR (capture->>'order_payment_expires_at')::timestamptz>offer.expires_at
    THEN RAISE EXCEPTION 'shb ASIC checkout requires exact issued reviewed offer'; END IF;
  END IF;
  RETURN NEW;
END $$;

CREATE FUNCTION public.shb_asic_dispatch_guard() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog AS $$
BEGIN
  IF NEW.merchant='synthetic-checkout' AND NEW.state='uncertain' AND OLD.state='prepared' AND EXISTS(
    SELECT 1 FROM public.catalog_syntheticcheckoutacceptance a JOIN public.shb_supportcheckout s ON s.checkout_id=a.checkout_id
      JOIN public.shb_supportoffer f ON f.id=s.offer_id
      WHERE a.id=NEW.reference AND (f.state<>'issued' OR f.expires_at<=clock_timestamp()))
  THEN RAISE EXCEPTION 'shb expired or closed ASIC offer cannot dispatch'; END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER shb_asic_dispatch_guard BEFORE UPDATE ON public.payments_syntheticpaymentattempt
FOR EACH ROW EXECUTE FUNCTION public.shb_asic_dispatch_guard();

CREATE FUNCTION public.shb_offered_request_revision_guard() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog AS $$
BEGIN
  IF NEW.revision IS DISTINCT FROM OLD.revision AND EXISTS(SELECT 1 FROM public.shb_supportoffer WHERE request_id=OLD.id)
  THEN RAISE EXCEPTION 'shb preserve offered request revision; changed work requires a new matching revision'; END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER shb_offered_request_revision_guard BEFORE UPDATE ON public.shb_supportrequest
FOR EACH ROW EXECUTE FUNCTION public.shb_offered_request_revision_guard();
"""


def previous(module, name):
    body=import_module('shop.shb.migrations.'+module).SQL
    start=body.index('FUNCTION public.'+name+'(')
    begin=body.rfind('CREATE',0,start)
    end=body.index('END $$;',start)+len('END $$;')
    return body[begin:end].replace('CREATE FUNCTION','CREATE OR REPLACE FUNCTION',1)+'\n'


_discount=previous('0012_closure_provenance','shb_discount_release_guard')
_order=previous('0010_paid_order_provenance','shb_order_commit_guard')
_closure=previous('0012_closure_provenance','shb_closure_commit_guard')
_paid=previous('0010_paid_order_provenance','shb_paid_order_guard')
SQL+=_discount.replace('a.checkout_id=NEW.checkout_id AND NEW.request_id IS NULL',
    'public.shb_reservation_matches(NEW.checkout_id,NEW.request_id,a.checkout_id)')
SQL+=_order.replace('a.checkout_id=h.checkout_id', 'public.shb_reservation_matches(h.checkout_id,h.request_id,a.checkout_id)')
SQL+=_closure.replace('a.checkout_id=h.checkout_id', 'public.shb_reservation_matches(h.checkout_id,h.request_id,a.checkout_id)')
SQL+=_paid.replace("OR NEW.payload->>'kind' IS DISTINCT FROM 'shb-paid-order'", """OR NEW.payload->'asic_offer' IS DISTINCT FROM original->'asic_offer'
    OR NEW.payload->'notice'->'body'->'asic_offer' IS DISTINCT FROM original->'asic_offer'
    OR NEW.payload->>'kind' IS DISTINCT FROM 'shb-paid-order'""")

REVERSE=_discount+_order+_closure+_paid+previous('0008_checkout_provenance','shb_checkout_scope_guard')
for table,name in [('shb_supportoffer','shb_offer_guard'),('shb_supportoffer','shb_offer_commit_guard'),
        ('payments_syntheticpaymentattempt','shb_asic_dispatch_guard'),('shb_supportrequest','shb_offered_request_revision_guard')]:
    REVERSE+=f'DROP TRIGGER {name} ON public.{table}; DROP FUNCTION public.{name}();\n'
REVERSE+='DROP FUNCTION public.shb_reservation_matches(uuid,uuid,uuid);\n'


class Migration(migrations.Migration):
    dependencies=[('shb','0013_supportoffer_supportcheckout_offer_and_more'),
        ('access','0010_remove_localeffectadmission_local_effect_kind_and_more')]
    operations=[migrations.RunSQL(SQL,REVERSE)]
