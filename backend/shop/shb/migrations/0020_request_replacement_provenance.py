"""Changed work has one fresh linked request, without reusing old approval."""
from django.db import migrations

SQL = """
CREATE FUNCTION public.shb_request_replacement_guard() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog AS $$
DECLARE old_request public.shb_supportrequest%ROWTYPE; child public.shb_supportrequest%ROWTYPE;
        c public.shb_requestclosure%ROWTYPE; old_invite public.shb_invitation%ROWTYPE;
        invite public.shb_invitation%ROWTYPE;
BEGIN
  IF TG_OP<>'INSERT' THEN RAISE EXCEPTION 'shb immutable request replacement'; END IF;
  SELECT * INTO old_request FROM public.shb_supportrequest WHERE id=NEW.previous_id FOR UPDATE;
  SELECT * INTO child FROM public.shb_supportrequest WHERE id=NEW.request_id;
  SELECT * INTO c FROM public.shb_requestclosure WHERE id=NEW.closure_id;
  SELECT * INTO old_invite FROM public.shb_invitation WHERE id=old_request.invitation_id;
  SELECT * INTO invite FROM public.shb_invitation WHERE id=NEW.invitation_id;
  IF old_request.id=child.id OR old_request.state<>'withdrawn' OR child.state<>'submitted'
    OR c.request_id IS DISTINCT FROM old_request.id OR c.applied_at IS NULL OR c.archive_receipt='{}'::jsonb
    OR c.payload->>'action' IS DISTINCT FROM 'withdraw' OR child.invitation_id IS DISTINCT FROM invite.id
    OR invite.customer_id IS DISTINCT FROM old_invite.customer_id
    OR invite.company_name IS DISTINCT FROM old_invite.company_name OR NOT invite.asic_allowed
    OR invite.revoked_at IS NOT NULL OR invite.created_at>clock_timestamp() OR invite.expires_at<=clock_timestamp()
    OR child.revision::bigint IS DISTINCT FROM old_request.revision::bigint+1
    OR child.payload->>'request_revision' IS DISTINCT FROM child.revision::text
    OR child.payload->>'replaces_request_id' IS DISTINCT FROM old_request.id::text
    OR child.payload->>'replaces_closure_id' IS DISTINCT FROM c.id::text
    OR child.payload->>'replaces_request_sha256' IS DISTINCT FROM old_request.sha256
    OR child.payload->'purchase'->>'variant_id' IS DISTINCT FROM 'shb-asic-25h'
    OR COALESCE(NULLIF(child.payload->>'known_project_reference',''),child.payload->'details'->>'project_reference')
      IS DISTINCT FROM COALESCE(NULLIF(old_request.payload->>'known_project_reference',''),old_request.payload->'details'->>'project_reference')
    OR EXISTS(SELECT 1 FROM public.shb_discountreservation WHERE request_id=old_request.id AND state IN ('reserved','consumed'))
  THEN RAISE EXCEPTION 'shb replacement needs matching withdrawn scope and fresh request'; END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER shb_request_replacement_guard BEFORE INSERT OR UPDATE OR DELETE ON public.shb_requestreplacement
FOR EACH ROW EXECUTE FUNCTION public.shb_request_replacement_guard();

CREATE FUNCTION public.shb_request_replacement_commit_guard() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog AS $$
BEGIN
  IF NEW.payload ? 'replaces_request_id' AND NOT EXISTS(SELECT 1 FROM public.shb_requestreplacement
    WHERE request_id=NEW.id AND previous_id::text=NEW.payload->>'replaces_request_id'
      AND closure_id::text=NEW.payload->>'replaces_closure_id')
  THEN RAISE EXCEPTION 'shb revised request must commit immutable predecessor link'; END IF;
  RETURN NULL;
END $$;
CREATE CONSTRAINT TRIGGER shb_request_replacement_commit_guard AFTER INSERT ON public.shb_supportrequest
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION public.shb_request_replacement_commit_guard();

CREATE FUNCTION public.shb_linked_revision_guard() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog AS $$
BEGIN
  IF NEW.revision IS DISTINCT FROM OLD.revision AND EXISTS(SELECT 1 FROM public.shb_requestreplacement
    WHERE request_id=OLD.id OR previous_id=OLD.id)
  THEN RAISE EXCEPTION 'shb immutable linked request revision'; END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER shb_linked_revision_guard BEFORE UPDATE ON public.shb_supportrequest
FOR EACH ROW EXECUTE FUNCTION public.shb_linked_revision_guard();
"""

REVERSE = ''
for table,name in [('shb_requestreplacement','shb_request_replacement_guard'),
        ('shb_supportrequest','shb_request_replacement_commit_guard'),('shb_supportrequest','shb_linked_revision_guard')]:
    REVERSE+=f'DROP TRIGGER {name} ON public.{table}; DROP FUNCTION public.{name}();\n'


class Migration(migrations.Migration):
    dependencies = [('shb','0019_requestreplacement')]
    operations = [migrations.RunSQL(SQL,REVERSE)]
