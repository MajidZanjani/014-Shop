"""Keep conceded prices immutable and enforce per-code slot capacity in SQL."""
from django.db import migrations


SQL = """
CREATE FUNCTION public.shb_discount_immutable_policy() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN RAISE EXCEPTION 'shb immutable discount'; END IF;
  IF (to_jsonb(NEW) - 'revoked_at') IS DISTINCT FROM (to_jsonb(OLD) - 'revoked_at')
     OR (OLD.revoked_at IS NOT NULL AND NEW.revoked_at IS DISTINCT FROM OLD.revoked_at)
  THEN RAISE EXCEPTION 'shb immutable discount policy'; END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER shb_discount_immutable_policy BEFORE UPDATE OR DELETE ON public.shb_discountcode
FOR EACH ROW EXECUTE FUNCTION public.shb_discount_immutable_policy();

CREATE FUNCTION public.shb_discount_reservation_guard() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog AS $$
DECLARE
  concession public.shb_discountcode%ROWTYPE;
  capture jsonb;
  owner_id bigint;
BEGIN
  IF TG_OP <> 'INSERT' THEN RAISE EXCEPTION 'shb immutable held discount'; END IF;
  SELECT * INTO concession FROM public.shb_discountcode WHERE id = NEW.discount_id FOR UPDATE;
  SELECT r.payload, i.customer_id INTO capture, owner_id
    FROM public.shb_supportrequest r JOIN public.shb_invitation i ON i.id = r.invitation_id
    WHERE r.id = NEW.request_id AND r.state = 'submitted';
  IF concession.id IS NULL OR capture IS NULL OR owner_id IS DISTINCT FROM concession.customer_id
     OR NOT concession.asic_allowed OR NEW.slot > concession.use_limit
     OR concession.revoked_at IS NOT NULL
     OR NEW.claimed_at < concession.starts_at OR NEW.claimed_at >= concession.expires_at
     OR statement_timestamp() < concession.starts_at OR statement_timestamp() >= concession.expires_at
     OR capture->'purchase'->>'variant_id' IS DISTINCT FROM 'shb-asic-25h'
     OR NEW.snapshot IS DISTINCT FROM capture->'purchase'->'discount_policy'
     OR NEW.snapshot->>'discount_id' IS DISTINCT FROM concession.id::text
     OR NEW.snapshot->>'customer_id' IS DISTINCT FROM concession.customer_id::text
     OR NEW.snapshot->>'variant_id' IS DISTINCT FROM 'shb-asic-25h'
     OR NEW.snapshot->>'percentage_bps' IS DISTINCT FROM concession.percentage_bps::text
     OR capture->'purchase'->>'discount_bps' IS DISTINCT FROM concession.percentage_bps::text
     OR NEW.snapshot->>'policy_revision' IS DISTINCT FROM concession.policy_revision
     OR NEW.snapshot->>'evidence_class' IS DISTINCT FROM concession.evidence_class
     OR (NEW.snapshot->>'claim_expires_at')::timestamptz IS DISTINCT FROM concession.expires_at
  THEN RAISE EXCEPTION 'shb discount reservation scope or capacity'; END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER shb_discount_reservation_guard BEFORE INSERT OR UPDATE OR DELETE ON public.shb_discountreservation
FOR EACH ROW EXECUTE FUNCTION public.shb_discount_reservation_guard();
"""

REVERSE = """
DROP TRIGGER shb_discount_reservation_guard ON public.shb_discountreservation;
DROP FUNCTION public.shb_discount_reservation_guard();
DROP TRIGGER shb_discount_immutable_policy ON public.shb_discountcode;
DROP FUNCTION public.shb_discount_immutable_policy();
"""


class Migration(migrations.Migration):
    dependencies = [('shb', '0003_scoped_discount_reservations')]
    operations = [migrations.RunSQL(SQL, REVERSE)]
