"""Closing intent fences dispatch; only archived proved closure releases its hold."""
from importlib import import_module
from django.db import migrations

SQL="""
CREATE FUNCTION public.shb_closure_guard() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog AS $$
DECLARE accepted public.catalog_syntheticcheckoutacceptance%ROWTYPE;
        payment public.payments_syntheticpaymentattempt%ROWTYPE; original jsonb; until_at timestamptz;
BEGIN
  IF TG_OP='DELETE' THEN RAISE EXCEPTION 'shb immutable checkout closure'; END IF;
  SELECT a.* INTO accepted FROM public.catalog_syntheticcheckoutacceptance a
    JOIN public.shb_supportcheckout s ON s.checkout_id=a.checkout_id WHERE a.id=NEW.acceptance_id FOR UPDATE OF a;
  SELECT c.snapshot INTO original FROM public.catalog_syntheticcheckout c WHERE c.id=accepted.checkout_id;
  IF accepted.attempt_id IS NOT NULL THEN
    SELECT * INTO payment FROM public.payments_syntheticpaymentattempt WHERE id=accepted.attempt_id FOR UPDATE;
    until_at:=payment.expires_at;
  ELSE until_at:=(original->>'order_payment_expires_at')::timestamptz; END IF;
  IF original IS NULL OR accepted.simulated_accepted_at IS NULL
    OR EXISTS(SELECT 1 FROM public.shb_paidorder WHERE acceptance_id=accepted.id)
    OR (payment.id IS NOT NULL AND payment.state NOT IN ('prepared','cancelled','expired'))
    OR NEW.payload->>'kind' IS DISTINCT FROM 'shb-checkout-closure'
    OR NEW.payload->>'checkout_id' IS DISTINCT FROM accepted.checkout_id::text
    OR NEW.payload->>'acceptance_id' IS DISTINCT FROM accepted.id::text
    OR NEW.payload->>'acceptance_sha256' IS DISTINCT FROM accepted.sha256
    OR NEW.payload->>'checkout_sha256' IS DISTINCT FROM accepted.payload->'review'->>'checkout_sha256'
    OR NEW.payload->>'attempt_id' IS DISTINCT FROM payment.id::text
    OR NEW.payload->>'customer_id' IS DISTINCT FROM original->>'customer_id'
    OR NEW.payload->>'invitation_id' IS DISTINCT FROM original->>'invitation_id'
    OR NEW.payload->>'reason' IS NULL OR NEW.payload->>'reason' NOT IN ('cancelled','expired')
    OR (NEW.payload->>'reason'='expired' AND (until_at IS NULL OR until_at>clock_timestamp()))
    OR NEW.payload->>'evidence_class' IS DISTINCT FROM 'local-synthetic'
    OR NEW.payload->'effects_authorized' IS DISTINCT FROM 'false'::jsonb
    OR NEW.payload->'financial_confirmation' IS DISTINCT FROM 'false'::jsonb
  THEN RAISE EXCEPTION 'shb closure requires matching never-dispatched acceptance'; END IF;
  IF TG_OP='INSERT' THEN
    IF NEW.applied_at IS NOT NULL OR NEW.archive_receipt <> '{}'::jsonb
    THEN RAISE EXCEPTION 'shb closure must prepare intent first'; END IF;
  ELSE
    IF (to_jsonb(NEW)-ARRAY['archive_receipt','applied_at']) IS DISTINCT FROM
        (to_jsonb(OLD)-ARRAY['archive_receipt','applied_at'])
      OR OLD.applied_at IS NOT NULL OR NEW.applied_at IS NULL
      OR NEW.archive_receipt->>'evidence_id' IS DISTINCT FROM NEW.id::text
      OR NEW.archive_receipt->>'sha256' IS DISTINCT FROM NEW.sha256
      OR (payment.id IS NOT NULL AND (payment.state NOT IN ('cancelled','expired') OR payment.stopped_at IS NULL))
    THEN RAISE EXCEPTION 'shb closure needs archived safe terminal outcome'; END IF;
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER shb_closure_guard BEFORE INSERT OR UPDATE OR DELETE ON public.shb_checkoutclosure
FOR EACH ROW EXECUTE FUNCTION public.shb_closure_guard();

CREATE FUNCTION public.shb_closed_acceptance_guard() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog AS $$
BEGIN
  IF NEW.attempt_id IS DISTINCT FROM OLD.attempt_id AND EXISTS(
      SELECT 1 FROM public.shb_checkoutclosure WHERE acceptance_id=OLD.id)
  THEN RAISE EXCEPTION 'shb closed checkout cannot attach payment'; END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER shb_closed_acceptance_guard BEFORE UPDATE ON public.catalog_syntheticcheckoutacceptance
FOR EACH ROW EXECUTE FUNCTION public.shb_closed_acceptance_guard();

CREATE FUNCTION public.shb_closed_attempt_guard() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog AS $$
BEGIN
  IF NEW.state IN ('uncertain','observed') AND NEW.merchant='synthetic-checkout' AND EXISTS(
      SELECT 1 FROM public.shb_checkoutclosure WHERE acceptance_id=NEW.reference)
  THEN RAISE EXCEPTION 'shb closed checkout cannot dispatch payment'; END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER shb_closed_attempt_guard BEFORE UPDATE ON public.payments_syntheticpaymentattempt
FOR EACH ROW EXECUTE FUNCTION public.shb_closed_attempt_guard();

CREATE FUNCTION public.shb_closed_paid_order_guard() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog AS $$
BEGIN
  IF EXISTS(SELECT 1 FROM public.shb_checkoutclosure WHERE acceptance_id=NEW.acceptance_id)
  THEN RAISE EXCEPTION 'shb closed checkout cannot finalize purchase'; END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER shb_closed_paid_order_guard BEFORE INSERT ON public.shb_paidorder
FOR EACH ROW EXECUTE FUNCTION public.shb_closed_paid_order_guard();

CREATE OR REPLACE FUNCTION public.shb_discount_release_guard() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog AS $$
BEGIN
  IF TG_OP='INSERT' THEN
    IF NEW.state <> 'reserved' OR NEW.release_review_id IS NOT NULL OR NEW.consumed_order_id IS NOT NULL OR NEW.release_closure_id IS NOT NULL
    THEN RAISE EXCEPTION 'shb new reservation must be held'; END IF;
    RETURN NEW;
  END IF;
  IF TG_OP='DELETE' THEN RAISE EXCEPTION 'shb immutable held discount'; END IF;
  IF (to_jsonb(NEW)-ARRAY['state','release_review_id','consumed_order_id','release_closure_id']) IS DISTINCT FROM
      (to_jsonb(OLD)-ARRAY['state','release_review_id','consumed_order_id','release_closure_id'])
    OR OLD.state <> 'reserved' OR OLD.release_review_id IS NOT NULL OR OLD.consumed_order_id IS NOT NULL OR OLD.release_closure_id IS NOT NULL
  THEN RAISE EXCEPTION 'shb immutable reservation or unsafe outcome'; END IF;
  IF NEW.state='consumed' AND NEW.release_review_id IS NULL AND NEW.release_closure_id IS NULL THEN
    PERFORM 1 FROM public.shb_paidorder o JOIN public.catalog_syntheticcheckoutacceptance a ON a.id=o.acceptance_id
      WHERE o.id=NEW.consumed_order_id AND a.checkout_id=NEW.checkout_id AND NEW.request_id IS NULL
        AND o.payload->'purchase'->'discount_policy'=NEW.snapshot;
    IF NOT FOUND THEN RAISE EXCEPTION 'shb consumption requires matching paid order'; END IF;
    RETURN NEW;
  END IF;
  IF NEW.state <> 'released' OR NEW.consumed_order_id IS NOT NULL THEN RAISE EXCEPTION 'shb unsafe discount outcome'; END IF;
  IF NEW.release_closure_id IS NOT NULL AND NEW.release_review_id IS NULL THEN
    PERFORM 1 FROM public.shb_checkoutclosure c
      JOIN public.catalog_syntheticcheckoutacceptance a ON a.id=c.acceptance_id
      JOIN public.catalog_syntheticcheckout o ON o.id=a.checkout_id
      WHERE c.id=NEW.release_closure_id AND a.checkout_id=NEW.checkout_id AND NEW.request_id IS NULL
        AND c.applied_at IS NOT NULL AND c.archive_receipt <> '{}'::jsonb
        AND o.snapshot->'purchase'->'discount_policy'=NEW.snapshot;
    IF NOT FOUND THEN RAISE EXCEPTION 'shb release requires archived safe closure'; END IF;
    RETURN NEW;
  END IF;
  IF NEW.release_review_id IS NULL OR NEW.release_closure_id IS NOT NULL THEN RAISE EXCEPTION 'shb unsafe discount outcome'; END IF;
  PERFORM 1 FROM public.shb_supportrequestreview e JOIN public.catalog_quotationreview v ON v.id=e.review_id
    JOIN public.shb_supportrequest r ON r.id=e.request_id
    WHERE e.review_id=NEW.release_review_id AND e.request_id=NEW.request_id AND r.state='declined' AND v.decision='declined'
      AND e.prior_state IN ('submitted','needs_information','under_review') AND v.snapshot_digest=r.sha256 AND v.quotation_id=r.quotation_id;
  IF NOT FOUND THEN RAISE EXCEPTION 'shb release requires matching pre-offer decline'; END IF;
  RETURN NEW;
END $$;

CREATE FUNCTION public.shb_closure_commit_guard() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog AS $$
BEGIN
  IF NEW.applied_at IS NOT NULL AND EXISTS (
      SELECT 1 FROM public.catalog_syntheticcheckoutacceptance a JOIN public.catalog_syntheticcheckout o ON o.id=a.checkout_id
      WHERE a.id=NEW.acceptance_id AND o.snapshot->'purchase' ? 'discount_policy') AND NOT EXISTS (
      SELECT 1 FROM public.shb_discountreservation h JOIN public.catalog_syntheticcheckoutacceptance a ON a.checkout_id=h.checkout_id
      WHERE a.id=NEW.acceptance_id AND h.release_closure_id=NEW.id AND h.state='released')
  THEN RAISE EXCEPTION 'shb safe closure must release concession atomically'; END IF;
  RETURN NULL;
END $$;
CREATE CONSTRAINT TRIGGER shb_closure_commit_guard AFTER UPDATE ON public.shb_checkoutclosure
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION public.shb_closure_commit_guard();
"""

_old=import_module('shop.shb.migrations.0010_paid_order_provenance').SQL
_start=_old.index('CREATE OR REPLACE FUNCTION public.shb_discount_release_guard()')
_end=_old.index('CREATE FUNCTION public.shb_order_commit_guard()',_start)
REVERSE=_old[_start:_end]
for table,name in [('shb_checkoutclosure','shb_closure_guard'),('catalog_syntheticcheckoutacceptance','shb_closed_acceptance_guard'),
        ('payments_syntheticpaymentattempt','shb_closed_attempt_guard'),('shb_paidorder','shb_closed_paid_order_guard'),('shb_checkoutclosure','shb_closure_commit_guard')]:
    REVERSE+=f'DROP TRIGGER {name} ON public.{table}; DROP FUNCTION public.{name}();\n'

class Migration(migrations.Migration):
    dependencies=[('shb','0011_checkout_closure')]
    operations=[migrations.RunSQL(SQL,REVERSE)]
