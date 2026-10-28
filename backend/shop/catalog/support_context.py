"""Optional private/versioned synthetic support context; no uploads, work or rights effects."""
import uuid
from django.db import transaction
from shop.payments import synthetic_bank
from shop.adapters.evidence_archive import manifest
from . import checkout, checkout_payment as payment, fulfilment, support_ledger as ledger
from .models import SyntheticFulfilment, SyntheticSupportContext as Context

FIXTURES={
    'synthetic-context-v1':{'board':'Synthetic prototype A','integration':'Synthetic SLL memory integration example'},
    'synthetic-context-v2':{'board':'Synthetic prototype B','integration':'Revised synthetic SLL memory integration example'},
}
LIMIT=100
FLAGS={'evidence_class':'local-synthetic','effects_authorized':False,'actual_technical_intake':False}


def fail(code='support_context_mismatch',status=409):raise checkout.CheckoutError(code,status)


def locked(owner,identity,archive,staff_request,customer_request=None):
    ledger.authorize_customer(owner,customer_request)
    if staff_request is not None:ledger.authorize(staff_request)
    payment.locked(owner,identity)
    grant=SyntheticFulfilment.objects.select_for_update(of=('self',)).select_related(
        'acceptance__checkout','acceptance__attempt').filter(acceptance__checkout_id=identity).first()
    if grant is None:fail('synthetic_fulfilment_required',422)
    if staff_request is not None:ledger.authorize(staff_request,grant)
    fulfilment.retained(grant,grant.acceptance,archive)
    return grant


def history(grant,archive):
    rows=list(Context.objects.filter(fulfilment=grant).order_by('revision')[:LIMIT+1])
    if len(rows)>LIMIT:fail()
    previous=grant.sha256
    for revision,row in enumerate(rows,1):
        value=row.payload
        if not isinstance(value,dict):fail()
        fixture=value.get('fixture')
        expected={'schema':1,'kind':'synthetic-support-context','identity':str(row.pk),
                  'request_id':str(row.request_id),'revision':revision,'previous_sha256':previous,
                  'grant_sha256':grant.sha256,'acceptance_sha256':grant.acceptance.sha256,
                  'owner_id':grant.acceptance.checkout.owner_id,'fixture':fixture,
                  'context':FIXTURES.get(fixture) if isinstance(fixture,str) else None,**FLAGS}
        if (type(fixture) is not str or fixture not in FIXTURES or row.revision!=revision or value!=expected
                or row.pk!=uuid.uuid5(grant.pk,'support-context-'+str(row.request_id))
                or row.sha256!=checkout.digest(value)):fail()
        payment.recover(archive,row.archive_receipt,row.pk,checkout.canonical(value))
        previous=row.sha256
    return rows,previous


def snapshot(grant,key,fixture,revision,previous):
    return {'schema':1,'kind':'synthetic-support-context','identity':str(uuid.uuid5(grant.pk,'support-context-'+str(key))),
            'request_id':str(key),'revision':revision,'previous_sha256':previous,'grant_sha256':grant.sha256,
            'acceptance_sha256':grant.acceptance.sha256,'owner_id':grant.acceptance.checkout.owner_id,
            'fixture':fixture,'context':FIXTURES[fixture].copy(),**FLAGS}


def record(owner,identity,key,fixture,expected_revision,archive,*,customer_request=None):
    synthetic_bank.guard()
    if (type(key) is not uuid.UUID or type(fixture) is not str or fixture not in FIXTURES
            or type(expected_revision) is not int or not 0<=expected_revision<LIMIT):
        fail('invalid_support_context',400)
    with transaction.atomic(durable=True):
        grant=locked(owner,identity,archive,None,customer_request);rows,previous=history(grant,archive)
        prior=next((row for row in rows if row.request_id==key),None)
        if prior:
            if prior.payload['fixture']!=fixture or prior.revision!=expected_revision+1:fail('support_context_conflict')
            return prior
        if expected_revision!=len(rows):fail('support_context_conflict')
        if len(rows)>=LIMIT:fail('support_context_limit',422)
        value=snapshot(grant,key,fixture,len(rows)+1,previous);identity=uuid.UUID(value['identity'])
        receipt=manifest(archive.publish(identity,checkout.canonical(value)))
        payment.recover(archive,receipt,identity,checkout.canonical(value))
        return Context.objects.create(id=identity,fulfilment=grant,revision=value['revision'],request_id=key,
                                      payload=value,sha256=checkout.digest(value),archive_receipt=receipt)


def read(owner,identity,archive,*,staff_request=None,customer_request=None):
    synthetic_bank.guard()
    with transaction.atomic(durable=True):
        grant=locked(owner,identity,archive,staff_request,customer_request);rows,_=history(grant,archive)
        if staff_request is not None:ledger.authorize(staff_request,grant)
        return {'revision':len(rows),'versions':[{'revision':row.revision,'fixture':row.payload['fixture'],
                'context':row.payload['context'].copy()} for row in rows],**FLAGS}
