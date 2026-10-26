"""Complete-cart synthetic per-line grants/staged completion. No real package or key."""
import uuid
from django.db import transaction
from shop.payments import synthetic_bank, attempts
from . import checkout, checkout_payment as payment
from .models import SyntheticFulfilment, SyntheticLineEntitlement, SyntheticLineDelivery, SyntheticCheckoutAcceptance
from shop.adapters.evidence_archive import manifest


def funded(owner, identity):
    row = payment.accepted(owner, identity)
    if (row.attempt_id is None or row.attempt.state != 'observed' or row.attempt.provider_status != 'captured'
            or attempts.request_for(row.attempt) != payment.request_for(row)):
        raise checkout.CheckoutError('synthetic_captured_payment_required', 422)
    return row


def plan(row):
    value = row.payload['review']['checkout']
    lines = [line for line in value['priced_lines'] if line['kind'] == 'ip']
    return {'schema':1, 'kind':'synthetic-cart-fulfilment', 'acceptance_id':str(row.pk),
            'acceptance_sha256':row.sha256, 'attempt_id':str(row.attempt_id), 'attempt_amount_minor':row.attempt.amount_minor,
            'support_scope':'sll-xspi-mc', 'support_packages':value['support_packages'],
            'support_seconds':value['support_packages']*36000, 'expires_at':None,
            'entitlements':[{'id':str(uuid.uuid5(row.pk, 'licence-'+line['line_id'])),
                             'line_id':line['line_id'], 'offer':line['offer']} for line in lines],
            'evidence_class':'local-synthetic', 'financial_confirmation':False, 'effects_authorized':False}


def retained(grant, row, archive):
    payment.retained(row, archive)
    attempts.retained(row.attempt, archive)
    if (grant.payload != plan(row) or checkout.digest(grant.payload) != grant.sha256
            or grant.support_packages != grant.payload['support_packages']
            or grant.support_seconds != grant.payload['support_seconds']):
        raise checkout.CheckoutError('fulfilment_mismatch')
    payment.recover(archive, grant.archive_receipt, grant.pk, checkout.canonical(grant.payload))


def provision(owner, identity, archive):
    synthetic_bank.guard()
    row = funded(owner, identity)
    payment.retained(row, archive);attempts.retained(row.attempt, archive)
    value = plan(row);grant_id = uuid.uuid5(row.pk, 'cart-fulfilment-v1')
    body = checkout.canonical(value)
    receipt = archive.publish(grant_id, body)
    payment.recover(archive, manifest(receipt), grant_id, body)
    with transaction.atomic(durable=True):
        payment.locked(owner, identity)
        # Re-read committed acceptance/provider state before creating any simulated grant.
        current = SyntheticCheckoutAcceptance.objects.select_for_update(of=('self',)).select_related('checkout','attempt').get(pk=row.pk)
        payment.verify(current)
        if current.attempt_id is None or current.attempt.state != 'observed' or current.attempt.provider_status != 'captured' or plan(current) != value:
            raise checkout.CheckoutError('fulfilment_mismatch')
        grant, _ = SyntheticFulfilment.objects.get_or_create(acceptance=current, defaults={
            'id':grant_id, 'payload':value, 'sha256':checkout.digest(value), 'archive_receipt':manifest(receipt),
            'support_packages':value['support_packages'], 'support_seconds':value['support_seconds']})
        if (grant.payload != value or grant.sha256 != checkout.digest(value) or grant.archive_receipt != manifest(receipt)
                or grant.support_packages != value['support_packages'] or grant.support_seconds != value['support_seconds']):raise checkout.CheckoutError('fulfilment_mismatch')
        for line in value['entitlements']:
            entitlement, _ = SyntheticLineEntitlement.objects.get_or_create(fulfilment=grant, line_id=line['line_id'],
                defaults={'id':uuid.UUID(line['id']), 'snapshot':line['offer']})
            if str(entitlement.pk) != line['id'] or entitlement.snapshot != line['offer']:
                raise checkout.CheckoutError('fulfilment_mismatch')
        return grant


def deliver(owner, identity, line_id, stage, archive):
    synthetic_bank.guard()
    if type(line_id) is not uuid.UUID or stage not in ('initial','reference'):
        raise checkout.CheckoutError('invalid_delivery', 400)
    row = funded(owner, identity)
    grant = SyntheticFulfilment.objects.filter(acceptance=row).first()
    if grant is None:raise checkout.CheckoutError('synthetic_fulfilment_required', 422)
    retained(grant, row, archive)
    entitlement = SyntheticLineEntitlement.objects.filter(fulfilment=grant, line_id=line_id).first()
    expected = next((line for line in grant.payload['entitlements'] if line['line_id'] == str(line_id)), None)
    if entitlement is None or expected is None or str(entitlement.pk) != expected['id'] or entitlement.snapshot != expected['offer']:
        raise checkout.CheckoutError('line_unavailable', 404)
    if stage == 'reference' and (not entitlement.snapshot['later_reference_design']
            or not SyntheticLineDelivery.objects.filter(entitlement=entitlement, stage='initial').exists()):
        raise checkout.CheckoutError('initial_delivery_required', 422)
    if stage == 'reference':
        initial = SyntheticLineDelivery.objects.get(entitlement=entitlement, stage='initial')
        if checkout.digest(initial.payload) != initial.sha256:raise checkout.CheckoutError('delivery_mismatch')
        payment.recover(archive, initial.archive_receipt, uuid.uuid5(entitlement.pk, 'initial-completion-v1'), checkout.canonical(initial.payload))
    value = {'kind':'synthetic-line-completion', 'grant_sha256':grant.sha256, 'entitlement_id':str(entitlement.pk),
             'line_id':str(line_id), 'stage':stage, 'version':'synthetic-completion-v1',
             'materials':['synthetic-rtl','synthetic-key','synthetic-documents'] if stage=='initial' else ['synthetic-reference-design'],
             'simulated_completion':True, 'evidence_class':'local-synthetic', 'effects_authorized':False}
    evidence_id = uuid.uuid5(entitlement.pk, stage+'-completion-v1')
    body = checkout.canonical(value);receipt = archive.publish(evidence_id, body)
    payment.recover(archive, manifest(receipt), evidence_id, body)
    with transaction.atomic(durable=True):
        payment.locked(owner, identity)
        current = SyntheticFulfilment.objects.select_for_update().get(pk=grant.pk)
        accepted_row = SyntheticCheckoutAcceptance.objects.select_related('checkout','attempt').get(pk=row.pk)
        payment.verify(accepted_row)
        if (current.payload != grant.payload or accepted_row.attempt_id is None
                or accepted_row.attempt.state != 'observed' or accepted_row.attempt.provider_status != 'captured'
                or plan(accepted_row) != current.payload):raise checkout.CheckoutError('fulfilment_mismatch')
        line = SyntheticLineEntitlement.objects.select_for_update().get(pk=entitlement.pk, fulfilment=current)
        if line.snapshot != entitlement.snapshot:raise checkout.CheckoutError('fulfilment_mismatch')
        if stage=='reference' and not SyntheticLineDelivery.objects.filter(entitlement=line,stage='initial').exists():
            raise checkout.CheckoutError('initial_delivery_required', 422)
        event, _ = SyntheticLineDelivery.objects.get_or_create(entitlement=line, stage=stage,
            defaults={'payload':value,'sha256':checkout.digest(value),'archive_receipt':manifest(receipt)})
        if event.payload != value or event.sha256 != checkout.digest(value) or event.archive_receipt != manifest(receipt):raise checkout.CheckoutError('delivery_mismatch')
        return event


def status(row):
    grant = SyntheticFulfilment.objects.filter(acceptance=row).first() if row else None
    if grant is None:return None
    lines = []
    for entitlement in SyntheticLineEntitlement.objects.filter(fulfilment=grant).order_by('line_id'):
        stages = set(SyntheticLineDelivery.objects.filter(entitlement=entitlement).values_list('stage',flat=True))
        later = entitlement.snapshot['later_reference_design']
        lines.append({'line_id':str(entitlement.line_id),'vendor':entitlement.snapshot['configuration']['vendor'],
            'families':entitlement.snapshot['configuration']['families'],'initial_delivered':'initial' in stages,
            'later_reference_design':later,'reference_delivered':'reference' in stages or ('initial' in stages and not later)})
    return {'entitlement_count':len(lines),'lines':lines,'support_packages':grant.support_packages,
            'support_seconds':grant.support_seconds,'support_hours':grant.support_seconds//3600,'expires_at':None,
            'actual_support_spendable':False,'effects_authorized':False}
