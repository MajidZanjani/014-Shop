"""Close unaccepted requests/offers with immutable archived proof, never fake acceptance."""
from importlib import import_module
from django.db import migrations

previous = import_module('shop.shb.migrations.0014_offer_provenance').previous

SQL = """
CREATE FUNCTION public.shb_request_closing_guard() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog AS $$
DECLARE r public.shb_supportrequest%ROWTYPE; f public.shb_supportoffer%ROWTYPE;
        h public.shb_discountreservation%ROWTYPE; version integer; owner_id bigint; actor jsonb; action text;
BEGIN
  IF TG_OP='DELETE' THEN RAISE EXCEPTION 'shb immutable request closing'; END IF;
  SELECT * INTO r FROM public.shb_supportrequest WHERE id=NEW.request_id FOR UPDATE;
  SELECT review_version INTO version FROM public.catalog_quotationrequest WHERE id=r.quotation_id;
  SELECT customer_id INTO owner_id FROM public.shb_invitation WHERE id=r.invitation_id;
  SELECT * INTO f FROM public.shb_supportoffer WHERE id=NEW.offer_id FOR UPDATE;
  SELECT * INTO h FROM public.shb_discountreservation WHERE request_id=r.id AND state='reserved';
  actor:=NEW.payload->'actor'; action:=NEW.payload->>'action';
  IF NEW.payload->>'kind' IS DISTINCT FROM 'shb-request-closure'
    OR NEW.payload->>'request_id' IS DISTINCT FROM r.id::text
    OR NEW.payload->>'request_sha256' IS DISTINCT FROM r.sha256
    OR NEW.payload->>'request_revision' IS DISTINCT FROM r.revision::text
    OR NEW.payload->'request_payload' IS DISTINCT FROM r.payload
    OR NEW.payload->'offer_payload' IS DISTINCT FROM COALESCE(f.payload,'null'::jsonb)
    OR NEW.payload->>'customer_id' IS DISTINCT FROM owner_id::text
    OR NEW.payload->>'review_version' IS DISTINCT FROM version::text
    OR NEW.payload->>'prior_state' IS DISTINCT FROM r.state
    OR r.state NOT IN ('submitted','needs_information','under_review','offer_issued','offer_expired')
    OR NEW.payload->>'offer_id' IS DISTINCT FROM COALESCE(f.id::text,'')
    OR NEW.payload->>'offer_sha256' IS DISTINCT FROM COALESCE(f.sha256,'')
    OR NEW.payload->>'offer_state' IS DISTINCT FROM COALESCE(f.state,'')
    OR NEW.payload->>'reservation_id' IS DISTINCT FROM COALESCE(h.id::text,'')
    OR NEW.payload->>'reservation_sha256' IS DISTINCT FROM COALESCE(h.sha256,'')
    OR NEW.payload->>'evidence_class' IS DISTINCT FROM 'local-synthetic'
    OR NEW.payload->'effects_authorized' IS DISTINCT FROM 'false'::jsonb
    OR NEW.payload->'financial_confirmation' IS DISTINCT FROM 'false'::jsonb
    OR action IS NULL OR action NOT IN ('withdraw','expire','replace')
    OR COALESCE(length(trim(NEW.payload->>'reason')),0) NOT BETWEEN 1 AND 512
    OR NEW.payload->'release_discount' IS DISTINCT FROM to_jsonb(action<>'replace')
    OR NEW.payload->>'result_state' IS DISTINCT FROM (CASE action WHEN 'replace' THEN 'under_review'
      WHEN 'expire' THEN 'offer_expired' ELSE 'withdrawn' END)
    OR (f.id IS NOT NULL AND (f.request_id<>r.id OR f.state NOT IN ('prepared','issued')))
    OR (f.id IS NULL AND (action<>'withdraw' OR EXISTS(SELECT 1 FROM public.shb_supportoffer
      WHERE request_id=r.id AND state IN ('prepared','issued','paid'))))
    OR (action='expire' AND (f.id IS NULL OR f.expires_at>clock_timestamp()))
    OR (action='replace' AND f.id IS NULL)
    OR EXISTS(SELECT 1 FROM public.shb_supportcheckout s JOIN public.catalog_syntheticcheckoutacceptance a
      ON a.checkout_id=s.checkout_id WHERE s.offer_id=f.id AND a.simulated_accepted_at IS NOT NULL)
  THEN RAISE EXCEPTION 'shb request closing requires exact unaccepted scope and held concession'; END IF;
  IF TG_OP='INSERT' THEN
    IF NEW.applied_at IS NOT NULL OR NEW.archive_receipt<>'{}'::jsonb
      OR (NEW.payload->>'requested_at')::timestamptz>clock_timestamp()
      OR (NEW.payload->>'requested_at')::timestamptz<clock_timestamp()-interval '30 seconds'
    THEN RAISE EXCEPTION 'shb request closing must prepare deliberate intent'; END IF;
    IF actor->>'kind'='assigned-staff' THEN
      PERFORM 1 FROM public.access_staffcredential c JOIN public.access_staffquotationgrant g ON g.user_id=c.user_id
        WHERE c.user_id::text=actor->>'user_id' AND c.enabled AND c.generation::text=actor->>'credential_generation'
          AND g.quotation_id=r.quotation_id AND g.business_scope_version=r.revision
          AND (actor->>'mfa_verified_at')::timestamptz<=clock_timestamp()
          AND (actor->>'mfa_verified_at')::timestamptz>=clock_timestamp()-interval '5 minutes';
      IF NOT FOUND THEN RAISE EXCEPTION 'shb request closing needs assigned recent MFA'; END IF;
    ELSIF actor->>'kind'='invitation-bearer' AND action='withdraw' THEN
      PERFORM 1 FROM public.shb_invitation i WHERE i.id::text=actor->>'invitation_id'
        AND i.customer_id=owner_id AND i.asic_allowed AND i.revoked_at IS NULL
        AND i.created_at<=clock_timestamp() AND i.expires_at>clock_timestamp()
        AND f.state='issued' AND f.expires_at>clock_timestamp()
        AND i.company_name=f.payload->>'company_name'
        AND (i.project_reference='' OR i.project_reference=f.payload->'scope'->>'project_reference')
        AND actor->>'session_digest' ~ '^[a-f0-9]{64}$'
        AND actor->'named_identity_verified'='false'::jsonb;
      IF NOT FOUND THEN RAISE EXCEPTION 'shb closing needs current same-scope invitation'; END IF;
    ELSIF actor->>'kind' IS DISTINCT FROM 'deadline-worker' OR action<>'expire' THEN
      RAISE EXCEPTION 'shb request closing actor';
    END IF;
  ELSE
    IF (to_jsonb(NEW)-ARRAY['archive_receipt','applied_at']) IS DISTINCT FROM
        (to_jsonb(OLD)-ARRAY['archive_receipt','applied_at'])
      OR OLD.applied_at IS NOT NULL OR NEW.applied_at IS NULL
      OR NEW.archive_receipt->>'evidence_id' IS DISTINCT FROM NEW.id::text
      OR NEW.archive_receipt->>'sha256' IS DISTINCT FROM NEW.sha256
    THEN RAISE EXCEPTION 'shb request closing needs archived immutable intent'; END IF;
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER shb_request_closing_guard BEFORE INSERT OR UPDATE OR DELETE ON public.shb_requestclosure
FOR EACH ROW EXECUTE FUNCTION public.shb_request_closing_guard();

CREATE FUNCTION public.shb_request_closing_commit_guard() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog AS $$
BEGIN
  IF NEW.applied_at IS NOT NULL THEN
    PERFORM 1 FROM public.shb_supportrequest r WHERE r.id=NEW.request_id AND r.state=NEW.payload->>'result_state';
    IF NOT FOUND THEN RAISE EXCEPTION 'shb closing must commit exact request outcome'; END IF;
    IF NEW.offer_id IS NOT NULL THEN
      PERFORM 1 FROM public.shb_supportoffer f WHERE f.id=NEW.offer_id
        AND (f.state='closed' AND f.published_at IS NOT NULL OR f.state='abandoned' AND f.published_at IS NULL);
      IF NOT FOUND THEN RAISE EXCEPTION 'shb closing must stop exact offer'; END IF;
    END IF;
    IF NEW.payload->>'reservation_id'<>'' THEN
      PERFORM 1 FROM public.shb_discountreservation h WHERE h.id::text=NEW.payload->>'reservation_id'
        AND h.request_id=NEW.request_id AND h.sha256=NEW.payload->>'reservation_sha256'
        AND ((NEW.payload->>'release_discount'='true' AND h.state='released' AND h.release_lifecycle_id=NEW.id)
          OR (NEW.payload->>'release_discount'='false' AND h.state='reserved' AND h.release_lifecycle_id IS NULL));
      IF NOT FOUND THEN RAISE EXCEPTION 'shb closing must preserve or release exact concession atomically'; END IF;
    END IF;
  END IF;
  RETURN NULL;
END $$;
CREATE CONSTRAINT TRIGGER shb_request_closing_commit_guard AFTER UPDATE ON public.shb_requestclosure
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION public.shb_request_closing_commit_guard();

CREATE FUNCTION public.shb_preacceptance_fence() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog AS $$
BEGIN
  IF TG_TABLE_NAME='shb_supportcheckout' THEN
    PERFORM 1 FROM public.shb_requestclosure WHERE offer_id=NEW.offer_id;
  ELSE
    PERFORM 1 FROM public.shb_requestclosure c JOIN public.shb_supportcheckout s ON s.offer_id=c.offer_id
      WHERE s.checkout_id=NEW.checkout_id;
  END IF;
  IF FOUND THEN RAISE EXCEPTION 'shb closing offer cannot capture or accept checkout'; END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER shb_preacceptance_fence BEFORE INSERT ON public.shb_supportcheckout
FOR EACH ROW EXECUTE FUNCTION public.shb_preacceptance_fence();
CREATE TRIGGER shb_preacceptance_fence BEFORE INSERT OR UPDATE ON public.catalog_syntheticcheckoutacceptance
FOR EACH ROW EXECUTE FUNCTION public.shb_preacceptance_fence();
"""

_offer = previous('0014_offer_provenance','shb_offer_guard')
SQL += _offer.replace("    IF OLD.state='issued'", """    IF (OLD.state='issued' AND NEW.state='closed' OR OLD.state='prepared' AND NEW.state='abandoned')
      AND NEW.published_at IS NOT DISTINCT FROM OLD.published_at AND NEW.archive_receipt=OLD.archive_receipt
      AND EXISTS(SELECT 1 FROM public.shb_requestclosure c WHERE c.offer_id=NEW.id
        AND c.request_id=NEW.request_id AND c.applied_at IS NOT NULL AND c.archive_receipt<>'{}'::jsonb)
    THEN RETURN NEW; END IF;
    IF OLD.state='issued'""").replace('  PERFORM 1 FROM public.shb_supportrequestreview e', """  IF EXISTS(SELECT 1 FROM public.shb_requestclosure c WHERE c.request_id=NEW.request_id AND c.applied_at IS NULL)
    OR EXISTS(SELECT 1 FROM public.shb_supportoffer f WHERE f.request_id=NEW.request_id AND f.id<>NEW.id
      AND (f.payload->>'review_version')::integer>=(NEW.payload->>'review_version')::integer)
  THEN RAISE EXCEPTION 'shb replacement requires fresh technical review and no pending closing'; END IF;
  PERFORM 1 FROM public.shb_supportrequestreview e""")

# Use the immediately preceding evolved discount function, not an obsolete FPGA-only copy.
_module = import_module('shop.shb.migrations.0014_offer_provenance')
_start = _module.SQL.index('CREATE OR REPLACE FUNCTION public.shb_discount_release_guard()')
_end = _module.SQL.index('END $$;',_start)+len('END $$;')
_discount = _module.SQL[_start:_end]
SQL += _discount.replace('BEGIN\n', """BEGIN
  IF TG_OP='INSERT' AND NEW.release_lifecycle_id IS NOT NULL
  THEN RAISE EXCEPTION 'shb new reservation must be held'; END IF;
  IF TG_OP='UPDATE' AND NEW.release_lifecycle_id IS NOT NULL THEN
    IF (to_jsonb(NEW)-ARRAY['state','release_lifecycle_id']) IS DISTINCT FROM
        (to_jsonb(OLD)-ARRAY['state','release_lifecycle_id'])
      OR OLD.state<>'reserved' OR OLD.release_lifecycle_id IS NOT NULL OR NEW.state<>'released'
      OR NEW.release_review_id IS NOT NULL OR NEW.release_closure_id IS NOT NULL OR NEW.consumed_order_id IS NOT NULL
    THEN RAISE EXCEPTION 'shb immutable reservation or unsafe lifecycle outcome'; END IF;
    PERFORM 1 FROM public.shb_requestclosure c JOIN public.shb_supportrequest r ON r.id=c.request_id
      WHERE c.id=NEW.release_lifecycle_id AND c.request_id=NEW.request_id AND NEW.checkout_id IS NULL
        AND c.applied_at IS NOT NULL AND c.archive_receipt<>'{}'::jsonb
        AND c.payload->>'release_discount'='true' AND c.payload->>'reservation_id'=NEW.id::text
        AND c.payload->>'reservation_sha256'=NEW.sha256 AND r.state=c.payload->>'result_state';
    IF NOT FOUND THEN RAISE EXCEPTION 'shb release requires exact archived request closing'; END IF;
    RETURN NEW;
  END IF;
""",1)

_review = previous('0006_review_release_provenance','shb_review_provenance')
SQL += _review.replace("  PERFORM 1 FROM public.shb_supportrequest r", """  IF EXISTS(SELECT 1 FROM public.shb_requestclosure WHERE request_id=NEW.request_id AND applied_at IS NULL)
  THEN RAISE EXCEPTION 'shb request closing blocks review'; END IF;
  PERFORM 1 FROM public.shb_supportrequest r""")

REVERSE = _offer + _discount + _review
REVERSE += """
DROP TRIGGER shb_preacceptance_fence ON public.shb_supportcheckout;
DROP TRIGGER shb_preacceptance_fence ON public.catalog_syntheticcheckoutacceptance;
DROP FUNCTION public.shb_preacceptance_fence();
DROP TRIGGER shb_request_closing_commit_guard ON public.shb_requestclosure;
DROP FUNCTION public.shb_request_closing_commit_guard();
DROP TRIGGER shb_request_closing_guard ON public.shb_requestclosure;
DROP FUNCTION public.shb_request_closing_guard();
"""


class Migration(migrations.Migration):
    dependencies = [('shb','0015_requestclosure_and_more')]
    operations = [migrations.RunSQL(SQL,REVERSE)]
