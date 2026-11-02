"""Immutable commercial scope and attributed issue/publication binding."""
from django.db import migrations

SQL="""
CREATE FUNCTION public.shb_discount_issue_scope_guard() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog AS $$
BEGIN
 IF TG_OP='DELETE' OR (to_jsonb(NEW)-'enabled') IS DISTINCT FROM (to_jsonb(OLD)-'enabled')
 THEN RAISE EXCEPTION 'shb immutable discount issuance scope'; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER shb_discount_issue_scope_guard BEFORE UPDATE OR DELETE ON public.shb_discountissuancescope
 FOR EACH ROW EXECUTE FUNCTION public.shb_discount_issue_scope_guard();

CREATE FUNCTION public.shb_discount_issue_actor_valid(actor jsonb, scope uuid) RETURNS boolean
LANGUAGE sql STABLE SET search_path=pg_catalog AS $$
 SELECT EXISTS(SELECT 1 FROM public.access_staffcredential c JOIN public.auth_user u ON u.id=c.user_id
   JOIN public.shb_discountissuegrant g ON g.user_id=u.id AND g.scope_id=scope
   JOIN public.shb_discountissuancescope s ON s.id=g.scope_id
   JOIN public.auth_user customer ON customer.id=s.customer_id
   WHERE u.id::text=actor->>'staff_id' AND u.is_active AND u.is_staff AND c.enabled
     AND c.generation::text=actor->>'credential_generation' AND s.enabled
     AND customer.is_active AND NOT customer.is_staff)
 AND EXISTS(SELECT 1 FROM public.access_accessepoch WHERE id=1 AND NOT quarantined)
$$;

CREATE FUNCTION public.shb_discount_issue_guard() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog AS $$
DECLARE s public.shb_discountissuancescope%ROWTYPE; d public.shb_discountcode%ROWTYPE;
 p jsonb; v jsonb; actor jsonb;
BEGIN
 IF TG_OP='DELETE' THEN RAISE EXCEPTION 'shb immutable discount issue'; END IF;
 SELECT * INTO s FROM public.shb_discountissuancescope WHERE id=NEW.scope_id FOR UPDATE;
 p:=NEW.payload;v:=p->'discount';actor:=p->'actor';
 IF NOT public.shb_discount_issue_actor_valid(actor,NEW.scope_id)
 THEN RAISE EXCEPTION 'shb discount issue requires exact issuance scope'; END IF;
 IF TG_OP='UPDATE' THEN
   IF OLD.discount_id IS NOT NULL OR NEW.discount_id IS DISTINCT FROM NEW.id OR NEW.archive_receipt='{}'::jsonb
      OR (to_jsonb(NEW)-ARRAY['discount_id','archive_receipt']) IS DISTINCT FROM (to_jsonb(OLD)-ARRAY['discount_id','archive_receipt'])
   THEN RAISE EXCEPTION 'shb immutable discount issue publication'; END IF;
   SELECT * INTO d FROM public.shb_discountcode WHERE id=NEW.discount_id FOR UPDATE;
   IF (d.id=NEW.id AND d.code_digest=p->>'code_digest'
     AND d.customer_id=s.customer_id AND d.issuer_id::text=actor->>'staff_id'
     AND d.percentage_bps=s.percentage_bps AND d.fpga_allowed=s.fpga_allowed AND d.asic_allowed=s.asic_allowed
     AND d.use_limit=s.use_limit AND d.policy_revision='synthetic-shb-discounts-v1'
     AND d.evidence_class='local-synthetic' AND d.issued_at=NEW.created_at AND d.starts_at=NEW.created_at
     AND d.expires_at=NEW.created_at+make_interval(days=>s.claim_period_days)
     AND d.revoked_at IS NULL) IS NOT TRUE
   THEN RAISE EXCEPTION 'shb discount issue must publish its exact discount'; END IF;
   RETURN NEW;
 END IF;
 IF (NEW.discount_id IS NULL AND NEW.archive_receipt='{}'::jsonb
   AND NEW.created_at BETWEEN clock_timestamp()-interval '5 minutes' AND clock_timestamp()
   AND p-ARRAY['schema','kind','scope','discount','code_digest','request_id','reason','actor',
       'evidence_class','effects_authorized','actual_discount_authority','actual_email_sent']='{}'::jsonb
   AND p->'schema'='1'::jsonb AND p->>'kind'='shb-discount-issue' AND p->>'request_id'=NEW.request_id::text
   AND jsonb_typeof(p->'reason')='string' AND length(btrim(p->>'reason')) BETWEEN 1 AND 512 AND p->>'reason'=btrim(p->>'reason')
   AND p->>'code_digest' ~ '^[a-f0-9]{64}$'
   AND p->>'evidence_class'='local-synthetic' AND p->'effects_authorized'='false'::jsonb
   AND p->'actual_discount_authority'='false'::jsonb AND p->'actual_email_sent'='false'::jsonb
   AND p->'scope'=((to_jsonb(s)-'enabled')- 'created_at') || jsonb_build_object('created_at',p->'scope'->'created_at')
   AND (p->'scope'->>'created_at')::timestamptz=s.created_at
   AND v-ARRAY['id','customer_id','issuer_id','percentage_bps','fpga_allowed','asic_allowed',
       'use_limit','policy_revision','evidence_class','issued_at','starts_at','expires_at']='{}'::jsonb
   AND v->>'id'=NEW.id::text AND v->>'customer_id'=s.customer_id::text AND v->>'issuer_id'=actor->>'staff_id'
   AND v->'percentage_bps'=to_jsonb(s.percentage_bps) AND v->'fpga_allowed'=to_jsonb(s.fpga_allowed)
   AND v->'asic_allowed'=to_jsonb(s.asic_allowed) AND v->'use_limit'=to_jsonb(s.use_limit)
   AND v->>'policy_revision'='synthetic-shb-discounts-v1' AND v->>'evidence_class'='local-synthetic'
   AND (v->>'issued_at')::timestamptz=NEW.created_at AND (v->>'starts_at')::timestamptz=NEW.created_at
   AND (v->>'expires_at')::timestamptz=NEW.created_at+make_interval(days=>s.claim_period_days)
   AND actor-ARRAY['staff_id','credential_generation','mfa_verified_at']='{}'::jsonb
   AND to_timestamp((actor->>'mfa_verified_at')::double precision) BETWEEN NEW.created_at-interval '5 minutes' AND NEW.created_at
   ) IS NOT TRUE
 THEN RAISE EXCEPTION 'shb discount issue needs exact attributed scope and clocks'; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER shb_discount_issue_guard BEFORE INSERT OR UPDATE OR DELETE ON public.shb_discountissue
 FOR EACH ROW EXECUTE FUNCTION public.shb_discount_issue_guard();

CREATE FUNCTION public.shb_discount_issue_publication_matches() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog AS $$
BEGIN
 IF EXISTS(SELECT 1 FROM public.shb_discountissue e JOIN public.shb_discountcode d ON d.id=e.id
     WHERE e.id=NEW.id AND (e.discount_id IS DISTINCT FROM d.id OR e.archive_receipt='{}'::jsonb))
 THEN RAISE EXCEPTION 'shb discount and issue publication must commit together'; END IF;
 RETURN NULL;
END $$;
CREATE CONSTRAINT TRIGGER shb_issued_discount_matches AFTER INSERT ON public.shb_discountcode
 DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION public.shb_discount_issue_publication_matches();
CREATE CONSTRAINT TRIGGER shb_discount_issue_publication_matches AFTER UPDATE ON public.shb_discountissue
 DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION public.shb_discount_issue_publication_matches();
"""
REVERSE="""
DROP TRIGGER shb_discount_issue_publication_matches ON public.shb_discountissue;
DROP TRIGGER shb_issued_discount_matches ON public.shb_discountcode;
DROP FUNCTION public.shb_discount_issue_publication_matches();
DROP TRIGGER shb_discount_issue_guard ON public.shb_discountissue;
DROP FUNCTION public.shb_discount_issue_guard();
DROP FUNCTION public.shb_discount_issue_actor_valid(jsonb,uuid);
DROP TRIGGER shb_discount_issue_scope_guard ON public.shb_discountissuancescope;
DROP FUNCTION public.shb_discount_issue_scope_guard();
"""


class Migration(migrations.Migration):
    dependencies=[('shb','0029_discount_issuance')]
    operations=[migrations.RunSQL(SQL,REVERSE)]
