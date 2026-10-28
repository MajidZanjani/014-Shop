"""Archived append-only support accounting, strictly local/synthetic and single grant."""
import uuid
from django.db import transaction
from shop.access.models import StaffCredential
from shop.access.staff_auth import staff_credential
from shop.payments import synthetic_bank
from shop.adapters.evidence_archive import manifest
from . import checkout, checkout_payment as payment, fulfilment
from .models import SyntheticFulfilment, SyntheticSupportEvent, SyntheticSupportStaffGrant

MAX_SECONDS = 9223372036854775807
KINDS = {'reserve','release','work','correct','statement'}


def fail(code='support_ledger_mismatch', status=409):
    raise checkout.CheckoutError(code, status)


def authorize_customer(owner,request):
    payment.authorize_customer(owner,request)


def authorize(request, grant=None):
    """Hold staff credential/user/scope locks through commit, matching revocation order."""
    if request is None: fail('recent_staff_mfa_required',403)
    candidate = staff_credential(request,recent=True)
    if candidate is None: fail('recent_staff_mfa_required',403)
    credential = StaffCredential.objects.select_for_update().select_related('user').get(pk=candidate.pk)
    # request.user can be a lazy object; use the credential's concrete user class.
    type(credential.user).objects.select_for_update().get(pk=credential.user_id)
    if (staff_credential(request,recent=True) is None or not credential.user.is_active
            or not credential.user.is_staff or not credential.enabled):fail('recent_staff_mfa_required',403)
    if grant is None:return None
    scope = SyntheticSupportStaffGrant.objects.select_for_update().filter(user_id=credential.user_id,fulfilment=grant).first()
    if scope is None:fail('support_scope_required',403)
    return {'staff_id':credential.user_id,'credential_generation':str(credential.generation),
            'mfa_verified_at':request.session['shop_staff_mfa']['verified_at']}


def replay(grant, events, archive=None):
    """Verify immutable hash/revision chain; derive balances only from committed facts."""
    reservations = {};work = {};spent = 0;previous = grant.sha256
    for revision,event in enumerate(events,1):
        value = event.payload
        if (event.revision != revision or event.sha256 != checkout.digest(value)
                or value.get('previous_sha256') != previous or value.get('revision') != revision
                or value.get('grant_sha256') != grant.sha256 or value.get('event_id') != str(event.pk)
                or value.get('request_id') != str(event.request_id) or value.get('kind') != event.kind
                or value.get('effects_authorized') is not False or value.get('evidence_class') != 'local-synthetic'):
            fail()
        if archive is not None:payment.recover(archive,event.archive_receipt,event.pk,checkout.canonical(value))
        command = value['command'];kind = event.kind;target = command['target_id'];seconds = command['seconds']
        if kind=='reserve':reservations[str(event.pk)] = {'task_id':command['task_id'],'remaining':seconds,'closed':False}
        elif kind in ('release','work'):
            reservation = reservations.get(target)
            if reservation is None or reservation['closed']:fail()
            if kind=='release':reservation['remaining']=0;reservation['closed']=True
            else:
                if type(seconds) is not int or not 1<=seconds<=reservation['remaining']:fail()
                reservation['remaining']-=seconds;spent+=seconds
                work[str(event.pk)]={'seconds':seconds,'task_id':reservation['task_id'],'reversed':False}
        elif kind=='correct':
            original=work.get(target)
            if original is None or original['reversed']:fail()
            if value.get('operations') != [{'kind':'reverse','event_id':target,'seconds':original['seconds']},
                                           {'kind':'replace','seconds':seconds}]:fail()
            original['reversed']=True;spent+=seconds-original['seconds']
            work[str(event.pk)]={'seconds':seconds,'task_id':original['task_id'],'reversed':False}
        elif kind=='statement':
            if value.get('statement') != snapshot(grant,revision-1,previous,reservations,work,spent):fail()
        else:fail()
        if spent<0 or sum(r['remaining'] for r in reservations.values())+spent>grant.support_seconds:fail()
        previous=event.sha256
    return snapshot(grant,len(events),previous,reservations,work,spent)


def snapshot(grant,revision,sha256,reservations,work,spent):
    reserved=sum(r['remaining'] for r in reservations.values())
    return {'grant_id':str(grant.pk),'revision':revision,'sha256':sha256,'granted_seconds':grant.support_seconds,
            'reserved_seconds':reserved,'spent_seconds':spent,'available_seconds':grant.support_seconds-reserved-spent,
            'reservations':reservations.copy(),'work':work.copy(),'expires_at':None,
            'actual_support_spendable':False,'evidence_class':'local-synthetic','effects_authorized':False}


def command(kind,request_id,seconds,task_id,target_id):
    if not isinstance(kind,str) or kind not in KINDS or type(request_id) is not uuid.UUID:fail('invalid_support_command',400)
    if kind in ('reserve','work','correct'):
        if type(seconds) is not int or not (0 if kind=='correct' else 1)<=seconds<=MAX_SECONDS:fail('invalid_support_seconds',400)
    elif seconds is not None:fail('invalid_support_command',400)
    if kind=='reserve':
        if type(task_id) is not uuid.UUID or target_id is not None:fail('invalid_support_command',400)
    elif kind in ('release','work','correct'):
        if type(target_id) is not uuid.UUID or task_id is not None:fail('invalid_support_command',400)
    elif task_id is not None or target_id is not None:fail('invalid_support_command',400)
    return {'seconds':seconds,'task_id':str(task_id) if task_id else None,'target_id':str(target_id) if target_id else None}


def record(owner,identity,request_id,kind,archive,*,seconds=None,task_id=None,target_id=None,staff_request=None,customer_request=None):
    synthetic_bank.guard()
    supplied=command(kind,request_id,seconds,task_id,target_id)
    # Local archive I/O while holding this grant lock serializes preflight/archive/commit.
    # No bank, mail, network archive or actual technical work runs inside this transaction.
    with transaction.atomic(durable=True):
        authorize_customer(owner,customer_request)
        if staff_request is not None:authorize(staff_request)
        payment.locked(owner,identity)
        grant = SyntheticFulfilment.objects.select_for_update(of=('self',)).select_related('acceptance__checkout','acceptance__attempt').filter(acceptance__checkout_id=identity).first()
        if grant is None:fail('synthetic_fulfilment_required',422)
        accepted=grant.acceptance
        if accepted.attempt_id is None or accepted.attempt.state!='observed' or accepted.attempt.provider_status not in ('captured','refunded'):fail('synthetic_captured_payment_required',422)
        fulfilment.retained(grant,accepted,archive)
        actor=authorize(staff_request,grant) if kind in ('work','correct','statement') else {'owner_id':owner.pk}
        events=list(SyntheticSupportEvent.objects.filter(fulfilment=grant).order_by('revision'))
        state=replay(grant,events,archive)
        previous=next((event for event in events if event.request_id==request_id),None)
        if previous:
            prior_actor=previous.payload['actor']
            # MFA freshness/generation must still pass; refreshed MFA time is not a new operation.
            actor_key='staff_id' if 'staff_id' in actor else 'owner_id'
            if (previous.kind!=kind or previous.payload['command']!=supplied
                    or prior_actor.get(actor_key)!=actor[actor_key]):fail('support_request_conflict')
            if kind=='statement':
                from shop.worker.statement_mail import enqueue
                enqueue(previous,archive)
                authorize(staff_request,grant)
            return previous
        if len(events)>=10000:fail('support_ledger_limit',422)
        value={'schema':1,'kind':kind,'command':supplied,'actor':actor,'grant_sha256':grant.sha256,
               'revision':state['revision']+1,'previous_sha256':state['sha256'],'request_id':str(request_id),
               'event_id':str(uuid.uuid5(grant.pk,'support-'+str(request_id))),
               'evidence_class':'local-synthetic','effects_authorized':False}
        if kind=='reserve':
            if seconds>state['available_seconds']:fail('support_credit_unavailable',422)
        elif kind in ('release','work'):
            reservation=state['reservations'].get(str(target_id))
            if reservation is None or reservation['closed'] or reservation['remaining']==0:fail('support_reservation_unavailable',422)
            if kind=='work' and seconds>reservation['remaining']:fail('support_credit_unavailable',422)
            if kind=='work':value['completion']={'simulated_completed':True,'actual_completion':False,'scope':'sll-xspi-mc'}
        elif kind=='correct':
            original=state['work'].get(str(target_id))
            if original is None or original['reversed']:fail('support_work_unavailable',422)
            if seconds>state['available_seconds']+original['seconds']:fail('support_credit_unavailable',422)
            value['operations']=[{'kind':'reverse','event_id':str(target_id),'seconds':original['seconds']}, {'kind':'replace','seconds':seconds}]
            value['completion']={'simulated_completed':True,'actual_completion':False,'scope':'sll-xspi-mc'}
        else:value['statement']=state
        event_id=uuid.UUID(value['event_id']);body=checkout.canonical(value)
        receipt=archive.publish(event_id,body)
        payment.recover(archive,manifest(receipt),event_id,body)
        event=SyntheticSupportEvent(fulfilment=grant,id=event_id,revision=value['revision'],request_id=request_id,
             kind=kind,payload=value,sha256=checkout.digest(value),archive_receipt=manifest(receipt))
        replay(grant,[*events,event],archive)
        # Recheck staff session age after local archive work, before committing chargeable facts.
        if kind in ('work','correct','statement'):authorize(staff_request,grant)
        event.save(force_insert=True)
        if kind=='statement':
            from shop.worker.statement_mail import enqueue
            enqueue(event,archive)
            authorize(staff_request,grant)
        return event


def read(owner,identity,archive,*,staff_request=None,customer_request=None):
    synthetic_bank.guard()
    with transaction.atomic(durable=True):
        authorize_customer(owner,customer_request)
        if staff_request is not None:authorize(staff_request)
        payment.locked(owner,identity)
        grant=SyntheticFulfilment.objects.select_for_update(of=('self',)).select_related('acceptance__checkout','acceptance__attempt').filter(acceptance__checkout_id=identity).first()
        if grant is None:fail('synthetic_fulfilment_required',422)
        if staff_request is not None:authorize(staff_request,grant)
        fulfilment.retained(grant,grant.acceptance,archive)
        events=list(SyntheticSupportEvent.objects.filter(fulfilment=grant).order_by('revision'))
        result=replay(grant,events,archive)
        from shop.worker.statement_mail import status
        result['statements']=[{'event_id':str(e.pk),'statement':e.payload['statement'],'mail_capture':status(e,archive)} for e in events if e.kind=='statement']
        return result
