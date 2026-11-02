"""Immutable eligibility facts and attributed issue/publication binding."""
from django.db import migrations

SQL="""
CREATE FUNCTION public.shb_issue_scope_guard() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog AS $$
BEGIN
 IF TG_OP='DELETE' OR (to_jsonb(NEW)-'enabled') IS DISTINCT FROM (to_jsonb(OLD)-'enabled')
 THEN RAISE EXCEPTION 'shb immutable issuance eligibility scope'; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER shb_issue_scope_guard BEFORE UPDATE OR DELETE ON public.shb_invitationissuancescope
 FOR EACH ROW EXECUTE FUNCTION public.shb_issue_scope_guard();

CREATE FUNCTION public.shb_issue_actor_valid(actor jsonb, scope uuid) RETURNS boolean
LANGUAGE sql STABLE SET search_path=pg_catalog AS $$
 SELECT EXISTS(SELECT 1 FROM public.access_staffcredential c JOIN public.auth_user u ON u.id=c.user_id
   JOIN public.shb_invitationissuegrant g ON g.user_id=u.id AND g.scope_id=scope
   JOIN public.shb_invitationissuancescope s ON s.id=g.scope_id
   JOIN public.auth_user customer ON customer.id=s.customer_id
   WHERE u.id::text=actor->>'staff_id' AND u.is_active AND u.is_staff AND c.enabled
     AND c.generation::text=actor->>'credential_generation' AND s.enabled
     AND customer.is_active AND NOT customer.is_staff)
 AND EXISTS(SELECT 1 FROM public.access_accessepoch WHERE id=1 AND NOT quarantined)
$$;

CREATE FUNCTION public.shb_invitation_issue_guard() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog AS $$
DECLARE s public.shb_invitationissuancescope%ROWTYPE; i public.shb_invitation%ROWTYPE;
 p jsonb; v jsonb; actor jsonb; prior public.shb_invitation%ROWTYPE;
BEGIN
 IF TG_OP='DELETE' THEN RAISE EXCEPTION 'shb immutable invitation issue'; END IF;
 SELECT * INTO s FROM public.shb_invitationissuancescope WHERE id=NEW.scope_id FOR UPDATE;
 p:=NEW.payload;v:=p->'invitation';actor:=p->'actor';
 IF NOT public.shb_issue_actor_valid(actor,NEW.scope_id)
 THEN RAISE EXCEPTION 'shb invitation issue requires exact issuance scope'; END IF;
 IF TG_OP='UPDATE' THEN
   IF OLD.invitation_id IS NOT NULL OR NEW.invitation_id IS DISTINCT FROM NEW.id OR NEW.archive_receipt='{}'::jsonb
      OR (to_jsonb(NEW)-ARRAY['invitation_id','archive_receipt']) IS DISTINCT FROM (to_jsonb(OLD)-ARRAY['invitation_id','archive_receipt'])
   THEN RAISE EXCEPTION 'shb immutable invitation issue publication'; END IF;
   SELECT * INTO i FROM public.shb_invitation WHERE id=NEW.invitation_id FOR UPDATE;
   IF (i.id=NEW.id AND i.token_digest=p->>'token_digest'
     AND i.customer_id=s.customer_id AND i.issuer_id::text=actor->>'staff_id'
     AND i.company_name=s.company_name AND i.project_reference=s.project_reference
     AND i.eligibility_reference=s.eligibility_reference AND i.fpga_eligible=s.fpga_eligible AND i.asic_allowed=s.asic_allowed
     AND i.created_at=NEW.created_at AND i.expires_at=(v->>'expires_at')::timestamptz
     AND i.revoked_at IS NULL) IS NOT TRUE
   THEN RAISE EXCEPTION 'shb invitation issue must publish its exact invitation'; END IF;
   RETURN NEW;
 END IF;
 IF NEW.replaces_id IS NOT NULL THEN
   SELECT * INTO prior FROM public.shb_invitation WHERE id=NEW.replaces_id FOR UPDATE;
   IF (prior.id IS NOT NULL AND prior.customer_id=s.customer_id AND prior.company_name=s.company_name
       AND prior.project_reference=s.project_reference AND prior.eligibility_reference=s.eligibility_reference
       AND prior.fpga_eligible=s.fpga_eligible AND prior.asic_allowed=s.asic_allowed
       AND (prior.expires_at<=NEW.created_at OR prior.revoked_at<=NEW.created_at)) IS NOT TRUE
   THEN RAISE EXCEPTION 'shb replacement needs inactive matching invitation'; END IF;
 END IF;
 IF (NEW.invitation_id IS NULL AND NEW.archive_receipt='{}'::jsonb
   AND NEW.created_at BETWEEN clock_timestamp()-interval '5 minutes' AND clock_timestamp()
   AND p-ARRAY['schema','kind','scope','invitation','token_digest','replacement','request_id','reason','actor',
       'evidence_class','effects_authorized','actual_invitation_authority','actual_email_sent']='{}'::jsonb
   AND p->'schema'='1'::jsonb AND p->>'kind'='shb-invitation-issue' AND p->>'request_id'=NEW.request_id::text
   AND jsonb_typeof(p->'reason')='string' AND length(btrim(p->>'reason')) BETWEEN 1 AND 512 AND p->>'reason'=btrim(p->>'reason')
   AND p->>'token_digest' ~ '^[a-f0-9]{64}$'
   AND p->>'evidence_class'='local-synthetic' AND p->'effects_authorized'='false'::jsonb
   AND p->'actual_invitation_authority'='false'::jsonb AND p->'actual_email_sent'='false'::jsonb
   AND p->'scope'=((to_jsonb(s)-'enabled')- 'created_at') || jsonb_build_object('created_at',p->'scope'->'created_at')
   AND (p->'scope'->>'created_at')::timestamptz=s.created_at
   AND v-ARRAY['id','customer_id','issuer_id','company_name','project_reference','eligibility_reference',
       'fpga_eligible','asic_allowed','created_at','expires_at']='{}'::jsonb
   AND v->>'id'=NEW.id::text AND v->>'customer_id'=s.customer_id::text AND v->>'issuer_id'=actor->>'staff_id'
   AND v->>'company_name'=s.company_name AND v->>'project_reference'=s.project_reference
   AND v->>'eligibility_reference'=s.eligibility_reference AND v->'fpga_eligible'=to_jsonb(s.fpga_eligible)
   AND v->'asic_allowed'=to_jsonb(s.asic_allowed) AND (v->>'created_at')::timestamptz=NEW.created_at
   AND (v->>'expires_at')::timestamptz=((NEW.created_at AT TIME ZONE 'Asia/Tbilisi')+interval '6 months') AT TIME ZONE 'Asia/Tbilisi'
   AND actor-ARRAY['staff_id','credential_generation','mfa_verified_at']='{}'::jsonb
   AND to_timestamp((actor->>'mfa_verified_at')::double precision) BETWEEN NEW.created_at-interval '5 minutes' AND NEW.created_at
   AND ((NEW.replaces_id IS NULL AND p->'replacement'='null'::jsonb)
     OR NEW.replaces_id IS NOT NULL AND p->'replacement'->>'id'=NEW.replaces_id::text)) IS NOT TRUE
 THEN RAISE EXCEPTION 'shb invitation issue needs exact attributed scope and clocks'; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER shb_invitation_issue_guard BEFORE INSERT OR UPDATE OR DELETE ON public.shb_invitationissue
 FOR EACH ROW EXECUTE FUNCTION public.shb_invitation_issue_guard();

CREATE FUNCTION public.shb_issue_publication_matches() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog AS $$
BEGIN
 IF EXISTS(SELECT 1 FROM public.shb_invitationissue e JOIN public.shb_invitation i ON i.id=e.id
     WHERE e.id=NEW.id AND (e.invitation_id IS DISTINCT FROM i.id OR e.archive_receipt='{}'::jsonb))
 THEN RAISE EXCEPTION 'shb invitation and issue publication must commit together'; END IF;
 RETURN NULL;
END $$;
CREATE CONSTRAINT TRIGGER shb_issued_invitation_matches AFTER INSERT ON public.shb_invitation
 DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION public.shb_issue_publication_matches();
CREATE CONSTRAINT TRIGGER shb_issue_publication_matches AFTER UPDATE ON public.shb_invitationissue
 DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION public.shb_issue_publication_matches();
"""
REVERSE="""
DROP TRIGGER shb_issue_publication_matches ON public.shb_invitationissue;
DROP TRIGGER shb_issued_invitation_matches ON public.shb_invitation;
DROP FUNCTION public.shb_issue_publication_matches();
DROP TRIGGER shb_invitation_issue_guard ON public.shb_invitationissue;
DROP FUNCTION public.shb_invitation_issue_guard();
DROP FUNCTION public.shb_issue_actor_valid(jsonb,uuid);
DROP TRIGGER shb_issue_scope_guard ON public.shb_invitationissuancescope;
DROP FUNCTION public.shb_issue_scope_guard();
"""


class Migration(migrations.Migration):
    dependencies=[('shb','0025_invitation_issuance')]
    operations=[migrations.RunSQL(SQL,REVERSE)]
