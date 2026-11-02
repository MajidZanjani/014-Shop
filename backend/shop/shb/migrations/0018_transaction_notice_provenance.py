"""Ordinary notices commit with their source; stable archived fake capture only."""
from django.db import migrations

SQL = """
CREATE FUNCTION public.shb_transaction_notice_value(event text, source text) RETURNS jsonb
LANGUAGE plpgsql STABLE SET search_path=pg_catalog AS $$
DECLARE r public.shb_supportrequest%ROWTYPE; e public.shb_supportrequestreview%ROWTYPE;
        v public.catalog_quotationreview%ROWTYPE; f public.shb_supportoffer%ROWTYPE;
        c public.shb_requestclosure%ROWTYPE; k public.shb_checkoutclosure%ROWTYPE;
        o public.shb_paidorder%ROWTYPE; data jsonb; p jsonb; body jsonb;
        owner_id bigint; recipient text; hash text;
BEGIN
  IF event='request-received' THEN
    SELECT * INTO r FROM public.shb_supportrequest WHERE id=source::uuid;
    hash:=r.sha256;
    body:=jsonb_build_object('reference',r.id::text,'status','Request received; no charge or engineering availability reserved.');
  ELSIF event IN ('request-question','request-declined') THEN
    SELECT * INTO e FROM public.shb_supportrequestreview WHERE review_id=source::bigint;
    SELECT * INTO v FROM public.catalog_quotationreview WHERE id=e.review_id;
    SELECT * INTO r FROM public.shb_supportrequest WHERE id=e.request_id;
    IF v.decision IS DISTINCT FROM (CASE event WHEN 'request-question' THEN 'needs_information' ELSE 'declined' END)
    THEN RETURN NULL; END IF;
    hash:=r.sha256;
    body:=jsonb_build_object('reference',r.id::text,'review_version',v.version,'message',e.message,
      'status',CASE event WHEN 'request-question' THEN 'More information requested.' ELSE 'Request declined.' END);
  ELSIF event='offer-issued' THEN
    SELECT * INTO f FROM public.shb_supportoffer WHERE id=source::uuid AND published_at IS NOT NULL AND archive_receipt<>'{}'::jsonb;
    SELECT * INTO r FROM public.shb_supportrequest WHERE id=f.request_id;
    hash:=f.sha256;
    body:=jsonb_build_object('reference',f.id::text,'request_reference',r.id::text,'status','Reviewed ASIC offer issued.',
      'path','/purchase/shb/offer/'||f.id::text||'/','expires_at',f.payload->'expires_at');
  ELSIF event='request-closed' THEN
    SELECT * INTO c FROM public.shb_requestclosure WHERE id=source::uuid AND applied_at IS NOT NULL AND archive_receipt<>'{}'::jsonb;
    SELECT * INTO r FROM public.shb_supportrequest WHERE id=c.request_id;
    hash:=c.sha256;
    body:=jsonb_build_object('reference',r.id::text,'offer_reference',c.payload->>'offer_id','action',c.payload->>'action',
      'status',CASE c.payload->>'action' WHEN 'withdraw' THEN 'Request withdrawn.' WHEN 'expire' THEN 'Unaccepted offer expired.'
        ELSE 'Old offer closed for fresh review and reissue.' END);
  ELSIF event='checkout-closed' THEN
    SELECT * INTO k FROM public.shb_checkoutclosure WHERE id=source::uuid AND applied_at IS NOT NULL AND archive_receipt<>'{}'::jsonb;
    SELECT s.snapshot,s.owner_id INTO data,owner_id FROM public.catalog_syntheticcheckout s
      JOIN public.catalog_syntheticcheckoutacceptance a ON a.checkout_id=s.id WHERE a.id=k.acceptance_id;
    recipient:=data->'details'->>'contact_email'; hash:=k.sha256;
    body:=jsonb_build_object('reference',k.acceptance_id::text,'action',k.payload->>'reason','status','Unpaid checkout cancelled or expired.');
  ELSIF event='purchase-confirmed' THEN
    SELECT * INTO o FROM public.shb_paidorder WHERE id=source::uuid;
    owner_id:=(o.payload->>'customer_id')::bigint; recipient:=o.payload->'details'->>'contact_email';
    hash:=o.sha256; p:=o.payload->'purchase';
    body:=jsonb_build_object('reference',o.payload->>'order_reference','status','Accepted paid purchase recorded.',
      'variant_label',p->'variant_label','quantity',p->'quantity','hours_per_bundle',p->'hours_per_bundle',
      'hours_purchased',p->'hours_purchased','total_minor',p->'total_minor','currency',p->'currency','support_tracking','manual-outside-shop');
  ELSE RETURN NULL;
  END IF;
  IF r.id IS NOT NULL THEN
    SELECT customer_id INTO owner_id FROM public.shb_invitation WHERE id=r.invitation_id;
    recipient:=r.payload->'details'->>'contact_email';
  END IF;
  IF owner_id IS NULL OR recipient IS NULL OR hash IS NULL THEN RETURN NULL; END IF;
  RETURN jsonb_build_object('schema',1,'kind','shb-transaction-notice','event',event,'source_id',source::text,
    'source_sha256',hash,'customer_id',owner_id,'recipient',recipient,'recipient_scope','this-transaction-only',
    'named_identity_verified',false,'actual_email_sent',false,'body',body,
    'evidence_class','local-synthetic','financial_confirmation',false,'effects_authorized',false);
END $$;

CREATE FUNCTION public.shb_transaction_notice_guard() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog AS $$
DECLARE expected jsonb;
BEGIN
  IF TG_OP<>'INSERT' THEN RAISE EXCEPTION 'shb immutable transaction notice'; END IF;
  expected:=public.shb_transaction_notice_value(NEW.event,NEW.source_id);
  IF expected IS NULL OR NEW.payload IS DISTINCT FROM expected
  THEN RAISE EXCEPTION 'shb transaction notice requires exact source and transaction recipient'; END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER shb_transaction_notice_guard BEFORE INSERT OR UPDATE OR DELETE ON public.shb_transactionnotice
FOR EACH ROW EXECUTE FUNCTION public.shb_transaction_notice_guard();

CREATE FUNCTION public.shb_transaction_notice_commit_guard() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog AS $$
BEGIN
  PERFORM 1 FROM public.shb_transactionnoticedelivery WHERE notice_id=NEW.id;
  IF NOT FOUND THEN RAISE EXCEPTION 'shb transaction notice must queue delivery atomically'; END IF;
  RETURN NULL;
END $$;
CREATE CONSTRAINT TRIGGER shb_transaction_notice_commit_guard AFTER INSERT ON public.shb_transactionnotice
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION public.shb_transaction_notice_commit_guard();

CREATE FUNCTION public.shb_transaction_source_commit_guard() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog AS $$
DECLARE expected_event text; identity text; decision text;
BEGIN
  expected_event:=TG_ARGV[0];
  IF expected_event='review' THEN
    identity:=NEW.review_id::text;
    SELECT v.decision INTO decision FROM public.catalog_quotationreview v WHERE v.id=identity::bigint;
    IF decision='needs_information' THEN expected_event:='request-question';
    ELSIF decision='declined' THEN expected_event:='request-declined'; ELSE RETURN NULL; END IF;
  ELSE
    identity:=NEW.id::text;
    IF expected_event='offer-issued' THEN
      IF NEW.state<>'issued' THEN RETURN NULL; END IF;
    END IF;
    IF expected_event IN ('request-closed','checkout-closed') THEN
      IF NEW.applied_at IS NULL THEN RETURN NULL; END IF;
    END IF;
  END IF;
  PERFORM 1 FROM public.shb_transactionnotice n WHERE n.event=expected_event AND n.source_id=identity;
  IF NOT FOUND THEN RAISE EXCEPTION 'shb transaction event must queue its ordinary notice atomically'; END IF;
  RETURN NULL;
END $$;
"""

for table, event, operation in [
    ('shb_supportrequest','request-received','INSERT'),
    ('shb_supportrequestreview','review','INSERT'),
    ('shb_supportoffer','offer-issued','UPDATE'),
    ('shb_requestclosure','request-closed','UPDATE'),
    ('shb_checkoutclosure','checkout-closed','UPDATE'),
    ('shb_paidorder','purchase-confirmed','INSERT'),
]:
    SQL += f"""
CREATE CONSTRAINT TRIGGER shb_transaction_source_commit_guard AFTER {operation} ON public.{table}
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION public.shb_transaction_source_commit_guard('{event}');
"""

SQL += """
CREATE FUNCTION public.shb_transaction_capture_guard() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog AS $$
DECLARE n public.shb_transactionnotice%ROWTYPE; expected jsonb;
BEGIN
  IF TG_OP<>'INSERT' THEN RAISE EXCEPTION 'shb immutable transaction capture'; END IF;
  SELECT * INTO n FROM public.shb_transactionnotice WHERE id=NEW.notice_id;
  expected:=jsonb_build_object('schema',1,'kind','shb-transaction-notice-capture','notice_id',n.id::text,
    'notice_sha256',n.sha256,'recipient',n.payload->>'recipient','status','durably-captured','actual_email_sent',false,
    'evidence_class','local-synthetic','financial_confirmation',false,'effects_authorized',false);
  IF NEW.payload IS DISTINCT FROM expected
    OR NEW.notice_archive_receipt->>'evidence_id' IS DISTINCT FROM n.id::text
    OR NEW.notice_archive_receipt->>'sha256' IS DISTINCT FROM n.sha256
    OR NEW.archive_receipt->>'evidence_id' IS DISTINCT FROM NEW.id::text
    OR NEW.archive_receipt->>'sha256' IS DISTINCT FROM NEW.sha256
    OR NOT EXISTS(SELECT 1 FROM public.shb_transactionnoticedelivery d WHERE d.notice_id=n.id
      AND d.state='claimed' AND d.lease_until>clock_timestamp())
  THEN RAISE EXCEPTION 'shb transaction capture requires leased archived envelope and proof'; END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER shb_transaction_capture_guard BEFORE INSERT OR UPDATE OR DELETE ON public.shb_transactionnoticecapture
FOR EACH ROW EXECUTE FUNCTION public.shb_transaction_capture_guard();

CREATE FUNCTION public.shb_transaction_delivery_guard() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog AS $$
BEGIN
  IF TG_OP='DELETE' THEN RAISE EXCEPTION 'shb retain transaction delivery'; END IF;
  IF TG_OP='INSERT' THEN
    IF NEW.state<>'pending' OR NEW.attempts<>0 THEN RAISE EXCEPTION 'shb new notice starts pending'; END IF;
    RETURN NEW;
  END IF;
  IF NEW.notice_id<>OLD.notice_id OR OLD.state IN ('captured','held')
  THEN RAISE EXCEPTION 'shb immutable terminal transaction delivery'; END IF;
  IF OLD.state='claimed' AND NEW.state='claimed' AND NEW.token=OLD.token AND NEW.attempts=OLD.attempts
    AND NEW.lease_until<=OLD.lease_until THEN RETURN NEW; END IF;
  IF NEW.state='claimed' AND NEW.attempts=OLD.attempts+1 AND NEW.token IS DISTINCT FROM OLD.token
    AND (OLD.state='pending' OR OLD.lease_until<=clock_timestamp()) AND NEW.lease_until>clock_timestamp()
    AND NEW.lease_until<=clock_timestamp()+interval '60 seconds' THEN RETURN NEW; END IF;
  IF NEW.state='held' AND NEW.attempts=OLD.attempts AND NEW.attempts>=1 THEN RETURN NEW; END IF;
  IF NEW.state='captured' AND OLD.state='claimed' AND OLD.lease_until>clock_timestamp() AND NEW.attempts=OLD.attempts
    AND EXISTS(SELECT 1 FROM public.shb_transactionnoticecapture WHERE notice_id=NEW.notice_id) THEN RETURN NEW; END IF;
  RAISE EXCEPTION 'shb invalid transaction delivery transition';
END $$;
CREATE TRIGGER shb_transaction_delivery_guard BEFORE INSERT OR UPDATE OR DELETE ON public.shb_transactionnoticedelivery
FOR EACH ROW EXECUTE FUNCTION public.shb_transaction_delivery_guard();
"""

REVERSE = ''
for table in ('shb_supportrequest','shb_supportrequestreview','shb_supportoffer','shb_requestclosure','shb_checkoutclosure','shb_paidorder'):
    REVERSE += f'DROP TRIGGER shb_transaction_source_commit_guard ON public.{table};\n'
for table, name in [('shb_transactionnotice','shb_transaction_notice_guard'),
        ('shb_transactionnotice','shb_transaction_notice_commit_guard'),
        ('shb_transactionnoticecapture','shb_transaction_capture_guard'),
        ('shb_transactionnoticedelivery','shb_transaction_delivery_guard')]:
    REVERSE += f'DROP TRIGGER {name} ON public.{table}; DROP FUNCTION public.{name}();\n'
REVERSE += 'DROP FUNCTION public.shb_transaction_source_commit_guard(); DROP FUNCTION public.shb_transaction_notice_value(text,text);\n'


class Migration(migrations.Migration):
    dependencies = [('shb','0017_transactionnotice_transactionnoticecapture_and_more')]
    operations = [migrations.RunSQL(SQL,REVERSE)]
