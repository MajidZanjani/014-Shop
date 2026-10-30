"""Release only from an attributed pre-offer decline; never from a clock."""
from django.db import migrations


SQL = """
CREATE FUNCTION public.shb_review_provenance() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog AS $$
BEGIN
  IF TG_OP <> 'INSERT' THEN RAISE EXCEPTION 'shb immutable review'; END IF;
  PERFORM 1 FROM public.shb_supportrequest r
    JOIN public.catalog_quotationrequest q ON q.id = r.quotation_id
    JOIN public.catalog_quotationreview v ON v.id = NEW.review_id AND v.quotation_id = q.id
    JOIN public.access_staffcredential c ON c.user_id = v.reviewer_id
    JOIN public.access_staffquotationgrant g ON g.user_id = v.reviewer_id AND g.quotation_id = q.id
    WHERE r.id = NEW.request_id AND r.state = NEW.prior_state
      AND v.snapshot_digest = r.sha256 AND v.business_version = r.revision
      AND g.business_scope_version = r.revision
      AND v.version = q.review_version + 1
      AND c.enabled AND c.generation = v.reviewer_generation
      AND v.mfa_verified_at <= clock_timestamp()
      AND v.mfa_verified_at >= clock_timestamp() - interval '5 minutes'
      AND v.decision IN ('needs_information', 'ready_for_commercial_review', 'declined');
  IF NOT FOUND THEN RAISE EXCEPTION 'shb review scope or provenance'; END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER shb_review_provenance BEFORE INSERT OR UPDATE OR DELETE ON public.shb_supportrequestreview
FOR EACH ROW EXECUTE FUNCTION public.shb_review_provenance();

CREATE FUNCTION public.shb_parent_review_immutable() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog AS $$
BEGIN
  IF EXISTS (SELECT 1 FROM public.shb_supportrequestreview WHERE review_id = OLD.id)
  THEN RAISE EXCEPTION 'shb immutable parent review'; END IF;
  IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER shb_parent_review_immutable BEFORE UPDATE OR DELETE ON public.catalog_quotationreview
FOR EACH ROW EXECUTE FUNCTION public.shb_parent_review_immutable();

DROP TRIGGER shb_discount_reservation_guard ON public.shb_discountreservation;
CREATE TRIGGER shb_discount_reservation_guard BEFORE INSERT ON public.shb_discountreservation
FOR EACH ROW EXECUTE FUNCTION public.shb_discount_reservation_guard();

CREATE FUNCTION public.shb_discount_release_guard() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    IF NEW.state IS DISTINCT FROM 'reserved' OR NEW.release_review_id IS NOT NULL
    THEN RAISE EXCEPTION 'shb new reservation must be held'; END IF;
    RETURN NEW;
  END IF;
  IF TG_OP = 'DELETE' THEN RAISE EXCEPTION 'shb immutable held discount'; END IF;
  IF (to_jsonb(NEW) - ARRAY['state', 'release_review_id']) IS DISTINCT FROM
       (to_jsonb(OLD) - ARRAY['state', 'release_review_id'])
     OR OLD.state IS DISTINCT FROM 'reserved' OR NEW.state IS DISTINCT FROM 'released'
     OR OLD.release_review_id IS NOT NULL OR NEW.release_review_id IS NULL
  THEN RAISE EXCEPTION 'shb immutable reservation or unsafe outcome'; END IF;
  PERFORM 1 FROM public.shb_supportrequestreview e
    JOIN public.catalog_quotationreview v ON v.id = e.review_id
    JOIN public.shb_supportrequest r ON r.id = e.request_id
    WHERE e.review_id = NEW.release_review_id AND e.request_id = NEW.request_id
      AND r.state = 'declined' AND v.decision = 'declined'
      AND e.prior_state IN ('submitted', 'needs_information', 'under_review')
      AND v.snapshot_digest = r.sha256 AND v.quotation_id = r.quotation_id;
  IF NOT FOUND THEN RAISE EXCEPTION 'shb release requires matching pre-offer decline'; END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER shb_discount_release_guard BEFORE INSERT OR UPDATE OR DELETE ON public.shb_discountreservation
FOR EACH ROW EXECUTE FUNCTION public.shb_discount_release_guard();
"""

REVERSE = """
DROP TRIGGER shb_discount_release_guard ON public.shb_discountreservation;
DROP FUNCTION public.shb_discount_release_guard();
DROP TRIGGER shb_discount_reservation_guard ON public.shb_discountreservation;
CREATE TRIGGER shb_discount_reservation_guard BEFORE INSERT OR UPDATE OR DELETE ON public.shb_discountreservation
FOR EACH ROW EXECUTE FUNCTION public.shb_discount_reservation_guard();
DROP TRIGGER shb_parent_review_immutable ON public.catalog_quotationreview;
DROP FUNCTION public.shb_parent_review_immutable();
DROP TRIGGER shb_review_provenance ON public.shb_supportrequestreview;
DROP FUNCTION public.shb_review_provenance();
"""


class Migration(migrations.Migration):
    dependencies = [('shb', '0005_request_review_closure')]
    operations = [migrations.RunSQL(SQL, REVERSE)]
