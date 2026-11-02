"""Freeze shared SHB captures and require the same scoped discount provenance."""
from importlib import import_module
from django.db import migrations

SQL="""
CREATE FUNCTION public.shb_checkout_scope_guard() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog AS $$
BEGIN
  IF TG_OP <> 'INSERT' THEN RAISE EXCEPTION 'shb immutable checkout scope'; END IF;
  PERFORM 1 FROM public.catalog_syntheticcheckout c
    JOIN public.shb_invitation i ON i.id = NEW.invitation_id
    JOIN public.catalog_cartsnapshot s ON s.id = c.cart_snapshot_id
    JOIN public.catalog_draftcart d ON d.id = s.cart_id
    WHERE c.id = NEW.checkout_id AND c.owner_id = i.customer_id AND d.owner_id = i.customer_id
      AND c.business_snapshot_id IS NULL AND c.request_id = NEW.request_id AND s.request_id = NEW.request_id
      AND c.snapshot->>'release' = 'shb-1.1'
      AND c.snapshot->>'invitation_id' = i.id::text AND c.snapshot->>'customer_id' = i.customer_id::text
      AND c.snapshot->>'request_id' = NEW.request_id::text
      AND c.snapshot->>'submission_sha256' = NEW.submission_sha256
      AND c.snapshot->'purchase'->>'variant_id' = 'shb-fpga-10h'
      AND c.snapshot->'purchase'->>'hours_per_bundle' = '10'
      AND (c.snapshot->'purchase'->>'quantity')::bigint BETWEEN 1 AND 2147483647
      AND (c.snapshot->'purchase'->>'hours_purchased')::bigint = 10 * (c.snapshot->'purchase'->>'quantity')::bigint
      AND s.lines = jsonb_build_array(c.snapshot->'purchase')
      AND c.snapshot->>'total_minor' = c.snapshot->'purchase'->>'total_minor'
      AND c.snapshot->>'currency' = c.snapshot->'purchase'->>'currency'
      AND c.snapshot->>'evidence_class' = 'local-synthetic'
      AND c.snapshot->'effects_authorized' = 'false'::jsonb
      AND c.snapshot->'financial_confirmation' = 'false'::jsonb
      AND c.snapshot->>'support_tracking' = 'manual-outside-shop'
      AND c.snapshot->'named_identity_verified' = 'false'::jsonb
      AND i.fpga_eligible AND i.revoked_at IS NULL AND i.created_at <= statement_timestamp()
      AND statement_timestamp() < i.expires_at;
  IF NOT FOUND THEN RAISE EXCEPTION 'shb checkout scope provenance'; END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER shb_checkout_scope_guard BEFORE INSERT OR UPDATE OR DELETE ON public.shb_supportcheckout
FOR EACH ROW EXECUTE FUNCTION public.shb_checkout_scope_guard();

CREATE FUNCTION public.shb_checkout_parent_guard() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog AS $$
BEGIN
  IF OLD.snapshot->>'release' = 'shb-1.1' OR EXISTS (
      SELECT 1 FROM public.shb_supportcheckout WHERE checkout_id = OLD.id) THEN
    IF TG_OP = 'DELETE' THEN RAISE EXCEPTION 'shb immutable checkout'; END IF;
    IF (to_jsonb(NEW)-'archive_receipt') IS DISTINCT FROM (to_jsonb(OLD)-'archive_receipt')
       OR (OLD.archive_receipt <> '{}'::jsonb AND NEW.archive_receipt IS DISTINCT FROM OLD.archive_receipt)
    THEN RAISE EXCEPTION 'shb immutable checkout capture'; END IF;
  ELSIF TG_OP = 'UPDATE' AND NEW.snapshot->>'release' = 'shb-1.1' THEN
    RAISE EXCEPTION 'shb cannot retag historical checkout';
  END IF;
  IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER shb_checkout_parent_guard BEFORE UPDATE OR DELETE ON public.catalog_syntheticcheckout
FOR EACH ROW EXECUTE FUNCTION public.shb_checkout_parent_guard();

CREATE FUNCTION public.shb_checkout_scope_required() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog AS $$
BEGIN
  IF NEW.snapshot->>'release' = 'shb-1.1' AND NOT EXISTS (
      SELECT 1 FROM public.shb_supportcheckout WHERE checkout_id = NEW.id)
  THEN RAISE EXCEPTION 'shb checkout requires scope'; END IF;
  RETURN NULL;
END $$;
CREATE CONSTRAINT TRIGGER shb_checkout_scope_required AFTER INSERT ON public.catalog_syntheticcheckout
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION public.shb_checkout_scope_required();

CREATE FUNCTION public.shb_checkout_cart_guard() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog AS $$
BEGIN
  IF EXISTS (SELECT 1 FROM public.catalog_syntheticcheckout WHERE cart_snapshot_id = OLD.id AND snapshot->>'release' = 'shb-1.1')
  THEN RAISE EXCEPTION 'shb immutable cart capture'; END IF;
  IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER shb_checkout_cart_guard BEFORE UPDATE OR DELETE ON public.catalog_cartsnapshot
FOR EACH ROW EXECUTE FUNCTION public.shb_checkout_cart_guard();

CREATE FUNCTION public.shb_checkout_key_guard() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    IF EXISTS (SELECT 1 FROM public.shb_supportcheckout s JOIN public.catalog_syntheticcheckout c ON c.id = s.checkout_id
        WHERE c.id = NEW.checkout_id AND (NEW.owner_id IS DISTINCT FROM c.owner_id OR NEW.request_id IS DISTINCT FROM s.request_id))
    THEN RAISE EXCEPTION 'shb retry scope provenance'; END IF;
    RETURN NEW;
  END IF;
  IF EXISTS (SELECT 1 FROM public.shb_supportcheckout WHERE checkout_id = OLD.checkout_id)
     OR (TG_OP = 'UPDATE' AND EXISTS (SELECT 1 FROM public.shb_supportcheckout WHERE checkout_id = NEW.checkout_id))
  THEN RAISE EXCEPTION 'shb immutable retry identity'; END IF;
  IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER shb_checkout_key_guard BEFORE INSERT OR UPDATE OR DELETE ON public.catalog_syntheticcheckoutkey
FOR EACH ROW EXECUTE FUNCTION public.shb_checkout_key_guard();

CREATE FUNCTION public.shb_checkout_acceptance_guard() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog AS $$
DECLARE capture jsonb; scope uuid; owner_id bigint; capture_hash text;
BEGIN
  IF TG_OP <> 'INSERT' THEN
    IF EXISTS (SELECT 1 FROM public.shb_supportcheckout WHERE checkout_id = OLD.checkout_id) THEN
      IF TG_OP = 'DELETE' THEN RAISE EXCEPTION 'shb immutable acceptance'; END IF;
      IF (to_jsonb(NEW)-ARRAY['archive_receipt','simulated_accepted_at','attempt_id']) IS DISTINCT FROM
           (to_jsonb(OLD)-ARRAY['archive_receipt','simulated_accepted_at','attempt_id'])
         OR (OLD.simulated_accepted_at IS NOT NULL AND NEW.simulated_accepted_at IS DISTINCT FROM OLD.simulated_accepted_at)
         OR (OLD.archive_receipt <> '{}'::jsonb AND NEW.archive_receipt IS DISTINCT FROM OLD.archive_receipt)
         OR (OLD.attempt_id IS NOT NULL AND NEW.attempt_id IS DISTINCT FROM OLD.attempt_id)
      THEN RAISE EXCEPTION 'shb immutable acceptance capture'; END IF;
    ELSIF TG_OP = 'UPDATE' AND EXISTS (SELECT 1 FROM public.shb_supportcheckout WHERE checkout_id = NEW.checkout_id) THEN
      RAISE EXCEPTION 'shb cannot retag historical acceptance';
    END IF;
    IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
  END IF;
  SELECT c.snapshot,c.owner_id,c.sha256,s.invitation_id INTO capture,owner_id,capture_hash,scope
    FROM public.catalog_syntheticcheckout c JOIN public.shb_supportcheckout s ON s.checkout_id = c.id
    WHERE c.id = NEW.checkout_id;
  IF FOUND THEN
    IF TG_OP = 'INSERT' AND (NEW.simulated_accepted_at IS NOT NULL OR NEW.attempt_id IS NOT NULL OR NEW.archive_receipt <> '{}'::jsonb)
    THEN RAISE EXCEPTION 'shb acceptance must be prepared first'; END IF;
    IF NEW.attempt_id IS NOT NULL THEN
      PERFORM 1 FROM public.payments_syntheticpaymentattempt a WHERE a.id = NEW.attempt_id
        AND a.merchant = 'synthetic-checkout' AND a.reference = NEW.id
        AND a.currency = capture->>'currency' AND a.amount_minor = (capture->>'total_minor')::bigint
        AND a.expires_at <= (capture->>'order_payment_expires_at')::timestamptz;
      IF NOT FOUND THEN RAISE EXCEPTION 'shb payment attempt provenance'; END IF;
    END IF;
  END IF;
  IF capture IS NOT NULL AND (NEW.payload->'review'->'checkout' IS DISTINCT FROM capture
      OR NEW.payload->'review'->>'checkout_id' IS DISTINCT FROM NEW.checkout_id::text
      OR NEW.payload->'review'->>'checkout_sha256' IS DISTINCT FROM capture_hash
      OR NEW.payload->'confirmation'->>'owner_id' IS DISTINCT FROM owner_id::text
      OR NEW.payload->'confirmation'->>'invitation_id' IS DISTINCT FROM scope::text
      OR NEW.payload->'confirmation'->'confirmed' IS DISTINCT FROM 'true'::jsonb
      OR NEW.payload->'confirmation'->'privacy_acknowledged' IS DISTINCT FROM 'true'::jsonb
      OR NEW.payload->'confirmation'->>'privacy_revision' IS DISTINCT FROM capture->>'privacy_revision'
      OR NEW.payload->'confirmation'->>'attribution' IS DISTINCT FROM 'invitation-bearer-submission'
      OR NEW.payload->'confirmation'->'named_identity_verified' IS DISTINCT FROM 'false'::jsonb)
  THEN RAISE EXCEPTION 'shb acceptance provenance'; END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER shb_checkout_acceptance_guard BEFORE INSERT OR UPDATE OR DELETE ON public.catalog_syntheticcheckoutacceptance
FOR EACH ROW EXECUTE FUNCTION public.shb_checkout_acceptance_guard();

CREATE OR REPLACE FUNCTION public.shb_discount_reservation_guard() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog AS $$
DECLARE
  concession public.shb_discountcode%ROWTYPE;
  capture jsonb;
  owner_id bigint;
  variant text;
BEGIN
  IF TG_OP <> 'INSERT' THEN RAISE EXCEPTION 'shb immutable held discount'; END IF;
  SELECT * INTO concession FROM public.shb_discountcode WHERE id = NEW.discount_id FOR UPDATE;
  IF NEW.request_id IS NOT NULL AND NEW.checkout_id IS NULL THEN
    variant := 'shb-asic-25h';
    SELECT r.payload,i.customer_id INTO capture,owner_id FROM public.shb_supportrequest r
      JOIN public.shb_invitation i ON i.id = r.invitation_id WHERE r.id = NEW.request_id AND r.state = 'submitted';
  ELSIF NEW.checkout_id IS NOT NULL AND NEW.request_id IS NULL THEN
    variant := 'shb-fpga-10h';
    SELECT c.snapshot,c.owner_id INTO capture,owner_id FROM public.catalog_syntheticcheckout c
      JOIN public.shb_supportcheckout s ON s.checkout_id = c.id WHERE c.id = NEW.checkout_id;
  ELSE RAISE EXCEPTION 'shb one reservation target'; END IF;
  IF concession.id IS NULL OR capture IS NULL OR owner_id IS DISTINCT FROM concession.customer_id
     OR (variant = 'shb-asic-25h' AND NOT concession.asic_allowed)
     OR (variant = 'shb-fpga-10h' AND NOT concession.fpga_allowed)
     OR NEW.slot > concession.use_limit OR concession.revoked_at IS NOT NULL
     OR NEW.claimed_at < concession.starts_at OR NEW.claimed_at >= concession.expires_at
     OR statement_timestamp() < concession.starts_at OR statement_timestamp() >= concession.expires_at
     OR capture->'purchase'->>'variant_id' IS DISTINCT FROM variant
     OR NEW.snapshot IS DISTINCT FROM capture->'purchase'->'discount_policy'
     OR NEW.snapshot->>'discount_id' IS DISTINCT FROM concession.id::text
     OR NEW.snapshot->>'customer_id' IS DISTINCT FROM concession.customer_id::text
     OR NEW.snapshot->>'variant_id' IS DISTINCT FROM variant
     OR NEW.snapshot->>'percentage_bps' IS DISTINCT FROM concession.percentage_bps::text
     OR capture->'purchase'->>'discount_bps' IS DISTINCT FROM concession.percentage_bps::text
     OR NEW.snapshot->>'policy_revision' IS DISTINCT FROM concession.policy_revision
     OR NEW.snapshot->>'evidence_class' IS DISTINCT FROM concession.evidence_class
     OR (NEW.snapshot->>'claim_expires_at')::timestamptz IS DISTINCT FROM concession.expires_at
  THEN RAISE EXCEPTION 'shb discount reservation scope or capacity'; END IF;
  RETURN NEW;
END $$;
"""

_old=import_module('shop.shb.migrations.0004_discount_invariants').SQL
_start=_old.index('CREATE FUNCTION public.shb_discount_reservation_guard()')
_end=_old.index('CREATE TRIGGER shb_discount_reservation_guard',_start)
REVERSE=_old[_start:_end].replace('CREATE FUNCTION','CREATE OR REPLACE FUNCTION',1)
for table,name in [('catalog_syntheticcheckoutacceptance','shb_checkout_acceptance_guard'),
        ('catalog_syntheticcheckoutkey','shb_checkout_key_guard'),('catalog_cartsnapshot','shb_checkout_cart_guard'),
        ('catalog_syntheticcheckout','shb_checkout_scope_required'),('catalog_syntheticcheckout','shb_checkout_parent_guard'),
        ('shb_supportcheckout','shb_checkout_scope_guard')]:
    REVERSE+=f'DROP TRIGGER {name} ON public.{table}; DROP FUNCTION public.{name}();\n'


class Migration(migrations.Migration):
    dependencies=[('shb','0007_checkout_scope')]
    operations=[migrations.RunSQL(SQL,REVERSE)]
