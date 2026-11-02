"""Append-only attributed revocation, bound atomically to the original concession."""
from django.db import migrations

SQL="""
CREATE FUNCTION public.shb_discount_actor_valid(actor jsonb, discount uuid) RETURNS boolean
LANGUAGE sql STABLE SET search_path=pg_catalog AS $$
 SELECT (actor-ARRAY['staff_id','credential_generation','mfa_verified_at']='{}'::jsonb)
 AND EXISTS(SELECT 1 FROM public.access_staffcredential c JOIN public.auth_user u ON u.id=c.user_id
   JOIN public.shb_discountstaffgrant g ON g.user_id=u.id AND g.discount_id=discount
   WHERE u.id::text=actor->>'staff_id' AND u.is_active AND u.is_staff AND c.enabled
     AND c.generation::text=actor->>'credential_generation'
     AND to_timestamp((actor->>'mfa_verified_at')::double precision)
       BETWEEN clock_timestamp()-interval '5 minutes' AND clock_timestamp())
 AND EXISTS(SELECT 1 FROM public.access_accessepoch WHERE id=1 AND NOT quarantined)
$$;
CREATE FUNCTION public.shb_discount_revocation_guard() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog AS $$
DECLARE d public.shb_discountcode%ROWTYPE; p jsonb; s jsonb;
BEGIN
 IF TG_OP<>'INSERT' THEN RAISE EXCEPTION 'shb immutable discount revocation'; END IF;
 SELECT * INTO d FROM public.shb_discountcode WHERE id=NEW.discount_id FOR UPDATE;
 p:=NEW.payload;s:=p->'discount';
 IF (d.id IS NOT NULL AND d.revoked_at IS NULL
   AND p-ARRAY['schema','kind','discount','request_id','revoked_at','reason','actor',
       'evidence_class','effects_authorized','actual_discount_authority','actual_email_sent']='{}'::jsonb
   AND p->'schema'='1'::jsonb AND p->>'kind'='shb-discount-revocation'
   AND p->>'request_id'=NEW.request_id::text AND (p->>'revoked_at')::timestamptz=NEW.revoked_at
   AND jsonb_typeof(p->'reason')='string' AND length(btrim(p->>'reason')) BETWEEN 1 AND 512 AND p->>'reason'=btrim(p->>'reason')
   AND p->>'evidence_class'='local-synthetic' AND p->'effects_authorized'='false'::jsonb
   AND p->'actual_discount_authority'='false'::jsonb AND p->'actual_email_sent'='false'::jsonb
   AND s-ARRAY['issued_at','starts_at','expires_at']=to_jsonb(d)-ARRAY['code_digest','revoked_at','issued_at','starts_at','expires_at']
   AND (s->>'issued_at')::timestamptz=d.issued_at AND (s->>'starts_at')::timestamptz=d.starts_at
   AND (s->>'expires_at')::timestamptz=d.expires_at
   AND public.shb_discount_actor_valid(p->'actor',d.id)) IS NOT TRUE
 THEN RAISE EXCEPTION 'shb discount revocation needs current exact staff scope'; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER shb_discount_revocation_guard BEFORE INSERT OR UPDATE OR DELETE ON public.shb_discountrevocation
 FOR EACH ROW EXECUTE FUNCTION public.shb_discount_revocation_guard();
CREATE FUNCTION public.shb_discount_revocation_matches() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog AS $$
DECLARE identity uuid;
BEGIN
 IF TG_TABLE_NAME='shb_discountrevocation' THEN identity:=NEW.discount_id; ELSE identity:=NEW.id; END IF;
 IF EXISTS(SELECT 1 FROM public.shb_discountrevocation r JOIN public.shb_discountcode d ON d.id=r.discount_id
     WHERE d.id=identity AND d.revoked_at IS DISTINCT FROM r.revoked_at)
 THEN RAISE EXCEPTION 'shb discount audit and revocation must commit together'; END IF;
 RETURN NULL;
END $$;
CREATE CONSTRAINT TRIGGER shb_discount_revocation_matches AFTER INSERT ON public.shb_discountrevocation
 DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION public.shb_discount_revocation_matches();
CREATE CONSTRAINT TRIGGER shb_discount_revoked_state_matches AFTER UPDATE ON public.shb_discountcode
 DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION public.shb_discount_revocation_matches();
"""
REVERSE="""
DROP TRIGGER shb_discount_revoked_state_matches ON public.shb_discountcode;
DROP TRIGGER shb_discount_revocation_matches ON public.shb_discountrevocation;
DROP TRIGGER shb_discount_revocation_guard ON public.shb_discountrevocation;
DROP FUNCTION public.shb_discount_revocation_matches();
DROP FUNCTION public.shb_discount_revocation_guard();
DROP FUNCTION public.shb_discount_actor_valid(jsonb,uuid);
"""


class Migration(migrations.Migration):
    dependencies=[('shb','0027_discount_staff_revocation')]
    operations=[migrations.RunSQL(SQL,REVERSE)]
