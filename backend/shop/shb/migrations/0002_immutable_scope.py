from django.db import migrations

SQL="""
CREATE FUNCTION public.shb_invitation_immutable_scope() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN RAISE EXCEPTION 'shb immutable invitation'; END IF;
  IF (to_jsonb(NEW) - 'revoked_at') IS DISTINCT FROM (to_jsonb(OLD) - 'revoked_at')
     OR (OLD.revoked_at IS NOT NULL AND NEW.revoked_at IS DISTINCT FROM OLD.revoked_at)
  THEN RAISE EXCEPTION 'shb immutable invitation scope'; END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER shb_invitation_immutable_scope BEFORE UPDATE OR DELETE ON public.shb_invitation
FOR EACH ROW EXECUTE FUNCTION public.shb_invitation_immutable_scope();
CREATE FUNCTION public.shb_request_immutable_capture() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN RAISE EXCEPTION 'shb immutable request'; END IF;
  IF (to_jsonb(NEW) - ARRAY['state','revision']) IS DISTINCT FROM (to_jsonb(OLD) - ARRAY['state','revision'])
  THEN RAISE EXCEPTION 'shb immutable request capture'; END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER shb_request_immutable_capture BEFORE UPDATE OR DELETE ON public.shb_supportrequest
FOR EACH ROW EXECUTE FUNCTION public.shb_request_immutable_capture();
"""
REVERSE="""
DROP TRIGGER shb_request_immutable_capture ON public.shb_supportrequest;
DROP FUNCTION public.shb_request_immutable_capture();
DROP TRIGGER shb_invitation_immutable_scope ON public.shb_invitation;
DROP FUNCTION public.shb_invitation_immutable_scope();
"""


class Migration(migrations.Migration):
    dependencies=[('shb','0001_initial')]
    operations=[migrations.RunSQL(SQL,REVERSE)]
