"""Append-only manual attestations and SQL binding on new SHB refund intents."""
from django.db import migrations

SQL = """
CREATE FUNCTION public.shb_refund_actor_valid(actor jsonb, purchase uuid) RETURNS boolean
LANGUAGE sql STABLE SET search_path=pg_catalog AS $$
 SELECT EXISTS(SELECT 1 FROM public.access_staffcredential c
   JOIN public.auth_user u ON u.id=c.user_id
   JOIN public.shb_paidordergrant g ON g.user_id=u.id AND g.order_id=purchase
   JOIN public.shb_paidorder o ON o.id=purchase
   JOIN public.payments_syntheticpaymentstaffgrant f ON f.user_id=u.id
     AND f.acceptance_id=o.acceptance_id AND f.kind='refund'
   WHERE u.id::text=actor->>'staff_id' AND u.is_active AND u.is_staff AND c.enabled
     AND c.generation::text=actor->>'credential_generation'
     AND to_timestamp((actor->>'mfa_verified_at')::double precision)
       BETWEEN clock_timestamp()-interval '5 minutes' AND clock_timestamp())
   AND EXISTS(SELECT 1 FROM public.access_accessepoch WHERE id=1 AND NOT quarantined)
$$;

CREATE FUNCTION public.shb_refund_review_guard() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog AS $$
DECLARE o public.shb_paidorder%ROWTYPE; a public.catalog_syntheticcheckoutacceptance%ROWTYPE;
        t public.payments_syntheticpaymentattempt%ROWTYPE; p jsonb;
BEGIN
  IF TG_OP<>'INSERT' THEN RAISE EXCEPTION 'shb immutable refund review'; END IF;
  SELECT * INTO o FROM public.shb_paidorder WHERE id=NEW.order_id FOR UPDATE;
  SELECT * INTO a FROM public.catalog_syntheticcheckoutacceptance WHERE id=o.acceptance_id;
  SELECT * INTO t FROM public.payments_syntheticpaymentattempt WHERE id=a.attempt_id;
  p:=NEW.payload;
  IF o.id IS NULL OR a.simulated_accepted_at IS NULL OR t.state<>'observed' OR t.provider_status<>'captured'
    OR p->>'kind' IS DISTINCT FROM 'shb-refund-review' OR p->>'request_id' IS DISTINCT FROM NEW.request_id::text
    OR p->>'order_id' IS DISTINCT FROM o.id::text OR p->>'order_sha256' IS DISTINCT FROM o.sha256
    OR p->>'order_reference' IS DISTINCT FROM o.payload->>'order_reference'
    OR p->>'acceptance_id' IS DISTINCT FROM a.id::text OR p->>'acceptance_sha256' IS DISTINCT FROM a.sha256
    OR p->>'attempt_id' IS DISTINCT FROM t.id::text OR p->'amount_minor' IS DISTINCT FROM to_jsonb(t.amount_minor)
    OR p->>'currency' IS DISTINCT FROM t.currency OR p->'manual_records_checked' IS DISTINCT FROM 'true'::jsonb
    OR length(btrim(COALESCE(p->>'manual_record_reference',''))) NOT BETWEEN 1 AND 200
    OR length(btrim(COALESCE(p->>'reason',''))) NOT BETWEEN 1 AND 512
    OR p->>'support_tracking' IS DISTINCT FROM 'manual-outside-shop'
    OR p->>'evidence_class' IS DISTINCT FROM 'local-synthetic'
    OR p->'financial_confirmation' IS DISTINCT FROM 'false'::jsonb
    OR p->'effects_authorized' IS DISTINCT FROM 'false'::jsonb
    OR p->'actual_financial_authority' IS DISTINCT FROM 'false'::jsonb
    OR p->'rights_or_support_mutated' IS DISTINCT FROM 'false'::jsonb
    OR p->'actual_email_sent' IS DISTINCT FROM 'false'::jsonb
    OR p->'financial_policy' IS DISTINCT FROM '{"actual_capture_authority":null,"refund_eligibility":null,"seller_approval":null,"tax_credit_document":null,"provider_qualification":null}'::jsonb
    OR NOT public.shb_refund_actor_valid(p->'actor',o.id)
    OR NEW.archive_receipt->>'evidence_id' IS DISTINCT FROM NEW.id::text
    OR NEW.archive_receipt->>'sha256' IS DISTINCT FROM NEW.sha256
  THEN RAISE EXCEPTION 'shb refund review requires original paid order and exact staff manual attestation'; END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER shb_refund_review_guard BEFORE INSERT OR UPDATE OR DELETE ON public.shb_refundreview
FOR EACH ROW EXECUTE FUNCTION public.shb_refund_review_guard();

CREATE FUNCTION public.shb_refund_operation_guard() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog AS $$
DECLARE r public.shb_refundreview%ROWTYPE; o public.shb_paidorder%ROWTYPE; expected jsonb;
BEGIN
  IF NEW.kind<>'refund' OR NOT EXISTS(SELECT 1 FROM public.catalog_syntheticcheckoutacceptance a
    JOIN public.catalog_syntheticcheckout c ON c.id=a.checkout_id
    WHERE a.id=NEW.acceptance_id AND c.snapshot->>'release'='shb-1.1') THEN RETURN NEW; END IF;
  SELECT * INTO o FROM public.shb_paidorder WHERE acceptance_id=NEW.acceptance_id;
  SELECT * INTO r FROM public.shb_refundreview WHERE order_id=o.id;
  expected:=jsonb_build_object('id',r.id::text,'sha256',r.sha256,'order_id',o.id::text,
    'order_reference',o.payload->>'order_reference');
  IF r.id IS NULL OR NEW.payload->'shb_refund_review' IS DISTINCT FROM expected
    OR NOT public.shb_refund_actor_valid(NEW.payload->'actor',o.id)
  THEN RAISE EXCEPTION 'shb new refund operation needs archived manual review'; END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER shb_refund_operation_guard BEFORE INSERT ON public.payments_syntheticpaymentoperation
FOR EACH ROW EXECUTE FUNCTION public.shb_refund_operation_guard();

CREATE FUNCTION public.shb_refund_handoff_guard() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog AS $$
DECLARE r public.shb_refundreview%ROWTYPE; o public.shb_paidorder%ROWTYPE;
        v public.payments_syntheticoperationresult%ROWTYPE; f public.payments_syntheticpaymentoperation%ROWTYPE;
        expected jsonb; p jsonb;
BEGIN
  IF TG_OP<>'INSERT' THEN RAISE EXCEPTION 'shb immutable refund handoff'; END IF;
  SELECT * INTO r FROM public.shb_refundreview WHERE id=NEW.review_id;
  SELECT * INTO o FROM public.shb_paidorder WHERE id=r.order_id;
  SELECT * INTO v FROM public.payments_syntheticoperationresult WHERE operation_id=NEW.result_id;
  SELECT * INTO f FROM public.payments_syntheticpaymentoperation WHERE id=v.operation_id;
  expected:=jsonb_build_object('id',r.id::text,'sha256',r.sha256,'order_id',o.id::text,
    'order_reference',o.payload->>'order_reference');
  p:=NEW.payload;
  IF r.id IS NULL OR v.operation_id IS NULL OR f.acceptance_id IS DISTINCT FROM o.acceptance_id
    OR f.kind<>'refund' OR v.payload->'observation'->>'status' IS DISTINCT FROM 'refunded'
    OR NOT EXISTS(SELECT 1 FROM public.payments_syntheticoperationdispatch WHERE operation_id=f.id AND state='observed')
    OR p->>'kind' IS DISTINCT FROM 'shb-refund-support-handoff'
    OR p->>'request_id' IS DISTINCT FROM NEW.request_id::text
    OR p->'refund_review' IS DISTINCT FROM expected OR f.payload->'shb_refund_review' IS DISTINCT FROM expected
    OR p->>'result_id' IS DISTINCT FROM v.operation_id::text OR p->>'result_sha256' IS DISTINCT FROM v.sha256
    OR p->'support_team_informed' IS DISTINCT FROM 'true'::jsonb
    OR length(btrim(COALESCE(p->>'communication_reference',''))) NOT BETWEEN 1 AND 200
    OR p->>'support_tracking' IS DISTINCT FROM 'manual-outside-shop'
    OR p->>'evidence_class' IS DISTINCT FROM 'local-synthetic'
    OR p->'financial_confirmation' IS DISTINCT FROM 'false'::jsonb
    OR p->'effects_authorized' IS DISTINCT FROM 'false'::jsonb
    OR p->'actual_financial_authority' IS DISTINCT FROM 'false'::jsonb
    OR p->'rights_or_support_mutated' IS DISTINCT FROM 'false'::jsonb
    OR p->'actual_email_sent' IS DISTINCT FROM 'false'::jsonb
    OR NOT public.shb_refund_actor_valid(p->'actor',o.id)
    OR NEW.archive_receipt->>'evidence_id' IS DISTINCT FROM NEW.id::text
    OR NEW.archive_receipt->>'sha256' IS DISTINCT FROM NEW.sha256
  THEN RAISE EXCEPTION 'shb handoff requires exact confirmed refund and attributed support communication'; END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER shb_refund_handoff_guard BEFORE INSERT OR UPDATE OR DELETE ON public.shb_refundsupporthandoff
FOR EACH ROW EXECUTE FUNCTION public.shb_refund_handoff_guard();
"""

REVERSE = ''
for table,name in [('shb_refundsupporthandoff','shb_refund_handoff_guard'),
    ('payments_syntheticpaymentoperation','shb_refund_operation_guard'),('shb_refundreview','shb_refund_review_guard')]:
    REVERSE += f'DROP TRIGGER {name} ON public.{table}; DROP FUNCTION public.{name}();\n'
REVERSE += 'DROP FUNCTION public.shb_refund_actor_valid(jsonb,uuid);'


class Migration(migrations.Migration):
    dependencies = [('shb','0021_refund_review_records')]
    operations = [migrations.RunSQL(SQL, REVERSE)]
