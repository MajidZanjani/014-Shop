"""Match archived accepted capture, permanent coupon consumption and notice leases."""
from importlib import import_module
from django.db import migrations

SQL="""
CREATE FUNCTION public.shb_paid_order_guard() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog AS $$
DECLARE original jsonb; accepted public.catalog_syntheticcheckoutacceptance%ROWTYPE;
        payment public.payments_syntheticpaymentattempt%ROWTYPE; fact public.payments_syntheticpaymentobservation%ROWTYPE;
BEGIN
  IF TG_OP <> 'INSERT' THEN RAISE EXCEPTION 'shb immutable paid order'; END IF;
  SELECT a.* INTO accepted FROM public.catalog_syntheticcheckoutacceptance a
    JOIN public.shb_supportcheckout s ON s.checkout_id=a.checkout_id WHERE a.id=NEW.acceptance_id;
  SELECT c.snapshot INTO original FROM public.catalog_syntheticcheckout c
    WHERE c.id=accepted.checkout_id AND c.archive_receipt <> '{}'::jsonb;
  SELECT * INTO payment FROM public.payments_syntheticpaymentattempt WHERE id=accepted.attempt_id FOR UPDATE;
  SELECT * INTO fact FROM public.payments_syntheticpaymentobservation WHERE id=NEW.capture_id;
  IF original IS NULL OR accepted.simulated_accepted_at IS NULL OR accepted.archive_receipt = '{}'::jsonb
    OR payment.id IS NULL OR payment.state <> 'observed' OR payment.provider_status <> 'captured'
    OR payment.merchant <> 'synthetic-checkout' OR payment.reference IS DISTINCT FROM accepted.id
    OR payment.currency IS DISTINCT FROM original->>'currency'
    OR payment.amount_minor IS DISTINCT FROM (original->>'total_minor')::bigint
    OR fact.attempt_id IS DISTINCT FROM payment.id OR fact.archive_receipt = '{}'::jsonb
    OR fact.payload->'observation'->>'status' IS DISTINCT FROM 'captured'
    OR fact.payload->'observation'->>'provider_operation_id' IS DISTINCT FROM payment.provider_operation_id::text
    OR NEW.archive_receipt->>'evidence_id' IS DISTINCT FROM NEW.id::text
    OR NEW.archive_receipt->>'sha256' IS DISTINCT FROM NEW.sha256
    OR NEW.payload->>'kind' IS DISTINCT FROM 'shb-paid-order'
    OR NEW.payload->>'order_reference' IS DISTINCT FROM accepted.id::text
    OR NEW.payload->>'checkout_id' IS DISTINCT FROM accepted.checkout_id::text
    OR NEW.payload->>'acceptance_sha256' IS DISTINCT FROM accepted.sha256
    OR NEW.payload->>'capture_id' IS DISTINCT FROM fact.id::text
    OR NEW.payload->>'capture_sha256' IS DISTINCT FROM fact.sha256
    OR NEW.payload->>'attempt_id' IS DISTINCT FROM payment.id::text
    OR NEW.payload->'details' IS DISTINCT FROM original->'details'
    OR NEW.payload->'purchase' IS DISTINCT FROM original->'purchase'
    OR NEW.payload->>'customer_id' IS DISTINCT FROM original->>'customer_id'
    OR NEW.payload->>'support_scope' IS DISTINCT FROM original->>'eligibility_reference'
    OR NEW.payload->>'support_tracking' IS DISTINCT FROM 'manual-outside-shop'
    OR NEW.payload->'accepted_documents' IS DISTINCT FROM accepted.payload->'review'->'fixture_documents'
    OR NEW.payload->>'evidence_class' IS DISTINCT FROM 'local-synthetic'
    OR NEW.payload->'effects_authorized' IS DISTINCT FROM 'false'::jsonb
    OR NEW.payload->'financial_confirmation' IS DISTINCT FROM 'false'::jsonb
    OR NEW.payload->'notice'->>'recipient' IS DISTINCT FROM 'support-order@synthetic.invalid'
    OR NEW.payload->'notice'->'actual_email_sent' IS DISTINCT FROM 'false'::jsonb
    OR NEW.payload->'notice'->'body'->>'order_reference' IS DISTINCT FROM accepted.id::text
    OR NEW.payload->'notice'->'body'->'purchase' IS DISTINCT FROM original->'purchase'
  THEN RAISE EXCEPTION 'shb paid order requires matching accepted captured evidence'; END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER shb_paid_order_guard BEFORE INSERT OR UPDATE OR DELETE ON public.shb_paidorder
FOR EACH ROW EXECUTE FUNCTION public.shb_paid_order_guard();

CREATE OR REPLACE FUNCTION public.shb_discount_release_guard() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    IF NEW.state IS DISTINCT FROM 'reserved' OR NEW.release_review_id IS NOT NULL OR NEW.consumed_order_id IS NOT NULL
    THEN RAISE EXCEPTION 'shb new reservation must be held'; END IF;
    RETURN NEW;
  END IF;
  IF TG_OP = 'DELETE' THEN RAISE EXCEPTION 'shb immutable held discount'; END IF;
  IF (to_jsonb(NEW)-ARRAY['state','release_review_id','consumed_order_id']) IS DISTINCT FROM
      (to_jsonb(OLD)-ARRAY['state','release_review_id','consumed_order_id']) OR OLD.state <> 'reserved'
    OR OLD.release_review_id IS NOT NULL OR OLD.consumed_order_id IS NOT NULL
  THEN RAISE EXCEPTION 'shb immutable reservation or unsafe outcome'; END IF;
  IF NEW.state = 'consumed' AND NEW.release_review_id IS NULL THEN
    PERFORM 1 FROM public.shb_paidorder o JOIN public.catalog_syntheticcheckoutacceptance a ON a.id=o.acceptance_id
      WHERE o.id=NEW.consumed_order_id AND a.checkout_id=NEW.checkout_id AND NEW.request_id IS NULL
        AND o.payload->'purchase'->'discount_policy' = NEW.snapshot;
    IF NOT FOUND THEN RAISE EXCEPTION 'shb consumption requires matching paid order'; END IF;
    RETURN NEW;
  END IF;
  IF NEW.state <> 'released' OR NEW.release_review_id IS NULL OR NEW.consumed_order_id IS NOT NULL
  THEN RAISE EXCEPTION 'shb unsafe discount outcome'; END IF;
  PERFORM 1 FROM public.shb_supportrequestreview e
    JOIN public.catalog_quotationreview v ON v.id=e.review_id
    JOIN public.shb_supportrequest r ON r.id=e.request_id
    WHERE e.review_id=NEW.release_review_id AND e.request_id=NEW.request_id
      AND r.state='declined' AND v.decision='declined'
      AND e.prior_state IN ('submitted','needs_information','under_review')
      AND v.snapshot_digest=r.sha256 AND v.quotation_id=r.quotation_id;
  IF NOT FOUND THEN RAISE EXCEPTION 'shb release requires matching pre-offer decline'; END IF;
  RETURN NEW;
END $$;

CREATE FUNCTION public.shb_order_commit_guard() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog AS $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM public.shb_purchasenoticedelivery WHERE order_id=NEW.id)
  THEN RAISE EXCEPTION 'shb paid order must queue notice atomically'; END IF;
  IF NEW.payload->'purchase' ? 'discount_policy' AND NOT EXISTS (
      SELECT 1 FROM public.shb_discountreservation h JOIN public.catalog_syntheticcheckoutacceptance a
        ON a.checkout_id=h.checkout_id WHERE a.id=NEW.acceptance_id AND h.consumed_order_id=NEW.id
          AND h.state='consumed' AND h.snapshot=NEW.payload->'purchase'->'discount_policy')
  THEN RAISE EXCEPTION 'shb paid order must consume concession atomically'; END IF;
  RETURN NULL;
END $$;
CREATE CONSTRAINT TRIGGER shb_order_commit_guard AFTER INSERT ON public.shb_paidorder
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION public.shb_order_commit_guard();

CREATE FUNCTION public.shb_notice_capture_guard() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog AS $$
DECLARE original public.shb_paidorder%ROWTYPE;
BEGIN
  IF TG_OP <> 'INSERT' THEN RAISE EXCEPTION 'shb immutable notice capture'; END IF;
  SELECT * INTO original FROM public.shb_paidorder WHERE id=NEW.order_id;
  IF NEW.archive_receipt->>'evidence_id' IS DISTINCT FROM NEW.id::text
    OR NEW.archive_receipt->>'sha256' IS DISTINCT FROM NEW.sha256
    OR NEW.payload->>'kind' IS DISTINCT FROM 'shb-purchase-notice-capture'
    OR NEW.payload->>'order_id' IS DISTINCT FROM original.id::text
    OR NEW.payload->>'order_reference' IS DISTINCT FROM original.payload->>'order_reference'
    OR NEW.payload->>'order_sha256' IS DISTINCT FROM original.sha256
    OR NEW.payload->>'effect_id' IS DISTINCT FROM original.payload->'notice'->>'effect_id'
    OR NEW.payload->>'recipient' IS DISTINCT FROM 'support-order@synthetic.invalid'
    OR NEW.payload->>'status' IS DISTINCT FROM 'durably-captured'
    OR NEW.payload->>'evidence_class' IS DISTINCT FROM 'local-synthetic'
    OR NEW.payload->'actual_email_sent' IS DISTINCT FROM 'false'::jsonb
    OR NEW.payload->'effects_authorized' IS DISTINCT FROM 'false'::jsonb
    OR NEW.payload->'financial_confirmation' IS DISTINCT FROM 'false'::jsonb
    OR NOT EXISTS (SELECT 1 FROM public.shb_purchasenoticedelivery WHERE order_id=NEW.order_id
      AND state='claimed' AND lease_until > clock_timestamp())
  THEN RAISE EXCEPTION 'shb notice capture requires matching owned lease'; END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER shb_notice_capture_guard BEFORE INSERT OR UPDATE OR DELETE ON public.shb_purchasenoticecapture
FOR EACH ROW EXECUTE FUNCTION public.shb_notice_capture_guard();

CREATE FUNCTION public.shb_notice_delivery_guard() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog AS $$
BEGIN
  IF TG_OP='DELETE' THEN RAISE EXCEPTION 'shb preserve notice delivery'; END IF;
  IF TG_OP='INSERT' THEN
    IF NEW.state <> 'pending' OR NEW.attempts <> 0 THEN RAISE EXCEPTION 'shb notice must be queued first'; END IF;
    RETURN NEW;
  END IF;
  IF NEW.order_id IS DISTINCT FROM OLD.order_id THEN RAISE EXCEPTION 'shb immutable notice identity'; END IF;
  IF NEW.state='claimed' AND NEW.attempts=OLD.attempts+1 AND NEW.token IS DISTINCT FROM OLD.token
    AND NEW.lease_until > clock_timestamp() AND NEW.lease_until <= clock_timestamp()+interval '60 seconds'
    AND (OLD.state='pending' OR (OLD.state='claimed' AND OLD.lease_until <= clock_timestamp())) THEN RETURN NEW; END IF;
  IF OLD.state='claimed' AND NEW.state='claimed' AND NEW.token=OLD.token AND NEW.attempts=OLD.attempts
    AND NEW.lease_until <= OLD.lease_until THEN RETURN NEW; END IF;
  IF OLD.state='claimed' AND NEW.state='held' AND OLD.lease_until <= clock_timestamp()
    AND NEW.attempts=OLD.attempts THEN RETURN NEW; END IF;
  IF OLD.state='claimed' AND NEW.state='captured' AND OLD.lease_until > clock_timestamp()
    AND NEW.attempts=OLD.attempts AND EXISTS (SELECT 1 FROM public.shb_purchasenoticecapture WHERE order_id=NEW.order_id)
  THEN RETURN NEW; END IF;
  RAISE EXCEPTION 'shb invalid notice lease transition';
END $$;
CREATE TRIGGER shb_notice_delivery_guard BEFORE INSERT OR UPDATE OR DELETE ON public.shb_purchasenoticedelivery
FOR EACH ROW EXECUTE FUNCTION public.shb_notice_delivery_guard();
"""

_old=import_module('shop.shb.migrations.0006_review_release_provenance').SQL
_start=_old.index('CREATE FUNCTION public.shb_discount_release_guard()')
_end=_old.index('CREATE TRIGGER shb_discount_release_guard',_start)
REVERSE=_old[_start:_end].replace('CREATE FUNCTION','CREATE OR REPLACE FUNCTION',1)
for table,name in [('shb_paidorder','shb_paid_order_guard'),('shb_paidorder','shb_order_commit_guard'),
        ('shb_purchasenoticecapture','shb_notice_capture_guard'),('shb_purchasenoticedelivery','shb_notice_delivery_guard')]:
    REVERSE+=f'DROP TRIGGER {name} ON public.{table}; DROP FUNCTION public.{name}();\n'

class Migration(migrations.Migration):
    dependencies=[('shb','0009_paid_order_records')]
    operations=[migrations.RunSQL(SQL,REVERSE)]
