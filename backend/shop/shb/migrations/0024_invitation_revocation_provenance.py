"""Append-only attributed audit and atomic invitation-state binding."""
from django.db import migrations

SQL="""
CREATE FUNCTION public.shb_invitation_actor_valid(actor jsonb, invite uuid) RETURNS boolean
LANGUAGE sql STABLE SET search_path=pg_catalog AS $$
 SELECT (actor - ARRAY['staff_id','credential_generation','mfa_verified_at']='{}'::jsonb)
 AND EXISTS(SELECT 1 FROM public.access_staffcredential c
   JOIN public.auth_user u ON u.id=c.user_id
   JOIN public.shb_invitationstaffgrant g ON g.user_id=u.id AND g.invitation_id=invite
   WHERE u.id::text=actor->>'staff_id' AND u.is_active AND u.is_staff AND c.enabled
     AND c.generation::text=actor->>'credential_generation'
     AND to_timestamp((actor->>'mfa_verified_at')::double precision)
       BETWEEN clock_timestamp()-interval '5 minutes' AND clock_timestamp())
 AND EXISTS(SELECT 1 FROM public.access_accessepoch WHERE id=1 AND NOT quarantined)
$$;

CREATE FUNCTION public.shb_invitation_revocation_guard() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog AS $$
DECLARE i public.shb_invitation%ROWTYPE; p jsonb; s jsonb;
BEGIN
 IF TG_OP<>'INSERT' THEN RAISE EXCEPTION 'shb immutable invitation revocation'; END IF;
 SELECT * INTO i FROM public.shb_invitation WHERE id=NEW.invitation_id FOR UPDATE;
 p:=NEW.payload; s:=p->'invitation';
 IF (i.id IS NOT NULL AND i.revoked_at IS NULL
   AND p - ARRAY['schema','kind','invitation','request_id','revoked_at','reason','actor',
       'evidence_class','effects_authorized','actual_invitation_authority','actual_email_sent']='{}'::jsonb
   AND p->'schema'='1'::jsonb AND p->>'kind'='shb-invitation-revocation'
   AND p->>'request_id'=NEW.request_id::text
   AND (p->>'revoked_at')::timestamptz=NEW.revoked_at
   AND jsonb_typeof(p->'reason')='string' AND length(btrim(p->>'reason')) BETWEEN 1 AND 512
   AND p->>'reason'=btrim(p->>'reason')
   AND p->>'evidence_class'='local-synthetic' AND p->'effects_authorized'='false'::jsonb
   AND p->'actual_invitation_authority'='false'::jsonb AND p->'actual_email_sent'='false'::jsonb
   AND s - ARRAY['id','customer_id','issuer_id','company_name','project_reference',
       'eligibility_reference','fpga_eligible','asic_allowed','created_at','expires_at']='{}'::jsonb
   AND s->>'id'=i.id::text AND s->>'customer_id'=i.customer_id::text
   AND s->>'issuer_id'=i.issuer_id::text AND s->>'company_name'=i.company_name
   AND s->>'project_reference'=i.project_reference AND s->>'eligibility_reference'=i.eligibility_reference
   AND s->'fpga_eligible'=to_jsonb(i.fpga_eligible) AND s->'asic_allowed'=to_jsonb(i.asic_allowed)
   AND (s->>'created_at')::timestamptz=i.created_at AND (s->>'expires_at')::timestamptz=i.expires_at
   AND public.shb_invitation_actor_valid(p->'actor',i.id)) IS NOT TRUE
 THEN RAISE EXCEPTION 'shb invitation revocation needs current exact staff scope'; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER shb_invitation_revocation_guard BEFORE INSERT OR UPDATE OR DELETE
 ON public.shb_invitationrevocation FOR EACH ROW EXECUTE FUNCTION public.shb_invitation_revocation_guard();

CREATE FUNCTION public.shb_invitation_revocation_matches() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog AS $$
DECLARE identity uuid;
BEGIN
 IF TG_TABLE_NAME='shb_invitationrevocation' THEN identity:=NEW.invitation_id; ELSE identity:=NEW.id; END IF;
 IF EXISTS(SELECT 1 FROM public.shb_invitationrevocation r JOIN public.shb_invitation i ON i.id=r.invitation_id
   WHERE i.id=identity AND i.revoked_at IS DISTINCT FROM r.revoked_at)
 THEN RAISE EXCEPTION 'shb invitation audit and revocation must commit together'; END IF;
 RETURN NULL;
END $$;
CREATE CONSTRAINT TRIGGER shb_invitation_revocation_matches AFTER INSERT
 ON public.shb_invitationrevocation DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
 EXECUTE FUNCTION public.shb_invitation_revocation_matches();
CREATE CONSTRAINT TRIGGER shb_invitation_revoked_state_matches AFTER UPDATE
 ON public.shb_invitation DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
 EXECUTE FUNCTION public.shb_invitation_revocation_matches();
"""
REVERSE="""
DROP TRIGGER shb_invitation_revoked_state_matches ON public.shb_invitation;
DROP TRIGGER shb_invitation_revocation_matches ON public.shb_invitationrevocation;
DROP TRIGGER shb_invitation_revocation_guard ON public.shb_invitationrevocation;
DROP FUNCTION public.shb_invitation_revocation_matches();
DROP FUNCTION public.shb_invitation_revocation_guard();
DROP FUNCTION public.shb_invitation_actor_valid(jsonb,uuid);
"""


class Migration(migrations.Migration):
    dependencies=[('shb','0023_invitation_staff_revocation')]
    operations=[migrations.RunSQL(SQL,REVERSE)]
