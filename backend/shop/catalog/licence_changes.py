"""Archived reviewed licence-change requests and held proposals, without new rights or money."""
from copy import deepcopy
import uuid
from django.db import transaction
from shop.access.models import StaffCredential
from shop.access.staff_auth import staff_credential
from shop.adapters.evidence_archive import manifest
from shop.payments import synthetic_bank
from . import checkout,private_packages as materials
from .rules import CATALOG,evaluate,MAX_COUNT
from .models import SyntheticLicenceCase,SyntheticLicenceCaseEvent,SyntheticLicenceCaseStaffGrant

KINDS=('renewal','rehost','family-addition','node-addition','production-upgrade')
DECISIONS=('needs_information','declined','ready_for_commercial_review')
PENDING=('fee_minor','currency','annual_start','expires_at','recurrence','host_profile','rehost_allowance',
         'overlap_policy','revocation_policy','maintenance_policy','approved_rights','coverage','terms_version','seller_approval')


def fail(code='licence_case_mismatch',status=409):raise checkout.CheckoutError(code,status)


def staff_locked(request,case=None):
    candidate=staff_credential(request,recent=True)
    if candidate is None:fail('recent_staff_mfa_required',403)
    credential=StaffCredential.objects.select_for_update().select_related('user').get(pk=candidate.pk)
    if (staff_credential(request,recent=True) is None or not credential.enabled
            or not credential.user.is_active or not credential.user.is_staff):fail('recent_staff_mfa_required',403)
    if case is not None and not SyntheticLicenceCaseStaffGrant.objects.select_for_update().filter(user=credential.user,case=case).exists():
        fail('case_scope_required',403)
    return {'staff_id':credential.user_id,'credential_generation':str(credential.generation),
            'mfa_verified_at':request.session['shop_staff_mfa']['verified_at']}


def source(configuration):
    vendor=next((v for v in CATALOG['vendors'] if v['id']==configuration['vendor']),None)
    if vendor is None or any(f not in [item['id'] for item in vendor['families']] for f in configuration['families']):fail('catalog_scope_changed')
    return {'revision':CATALOG['revision'],'families':[f['id'] for f in vendor['families']],
            'terms':deepcopy(CATALOG['terms']),'production_bands':deepcopy(CATALOG['production_bands'])}


def normalized(original,raw,catalog):
    if not isinstance(raw,dict) or not isinstance(raw.get('kind'),str) or raw['kind'] not in KINDS:fail('invalid_change_request',400)
    kind=raw['kind'];fields={'kind'}
    if kind=='family-addition':fields.add('families')
    elif kind=='node-addition':fields|={'fixed_nodes','floating_nodes'}
    elif kind=='production-upgrade':fields|={'term','production_band','production_units'}
    if set(raw)!=fields:fail('invalid_change_request',400)
    request=deepcopy(raw);proposed=deepcopy(original);proposed['support_packages']=0
    if kind=='renewal' and original['term'] not in ('rd-annual','rdp-yearly'):fail('renewal_not_applicable',422)
    if kind=='family-addition':
        values=raw['families'];allowed=catalog['families']
        if (not isinstance(values,list) or not 1<=len(values)<=13 or any(not isinstance(v,str) or v not in allowed or v in original['families'] for v in values)
                or len(set(values))!=len(values)):fail('invalid_family_addition',422)
        request['families']=[v for v in allowed if v in values]
        proposed['families']=[v for v in allowed if v in values or v in original['families']]
    elif kind=='node-addition':
        if (original['vendor']!='altera' or any(type(raw[k]) is not int or not 0<=raw[k]<=MAX_COUNT for k in ('fixed_nodes','floating_nodes'))
                or raw['fixed_nodes']+raw['floating_nodes']==0):fail('invalid_node_addition',422)
        for name in ('fixed_nodes','floating_nodes'):
            proposed[name]+=raw[name]
            if proposed[name]>MAX_COUNT:fail('invalid_node_addition',422)
    elif kind=='production-upgrade':
        term=raw['term'];band=raw['production_band'];units=raw['production_units']
        allowed_term=next((t for t in catalog['terms'] if t['id']==term and original['vendor'] in t['vendors']),None)
        if allowed_term is None or term not in ('rdp-yearly','perpetual') or original['term']=='perpetual':fail('invalid_production_upgrade',422)
        if term=='perpetual':
            if band is not None or units is not None:fail('invalid_production_upgrade',422)
        else:
            target=next((b for b in catalog['production_bands'] if b['id']==band),None)
            if target is None or (units is not None and (type(units) is not int or not target['minimum']<=units<=MAX_COUNT or (target['maximum'] is not None and units>target['maximum']))):fail('invalid_production_upgrade',422)
            if original['term']=='rdp-yearly':
                previous=next((b for b in catalog['production_bands'] if b['id']==original['production_band']),None)
                if previous is None or target['minimum']<previous['minimum']:fail('invalid_production_upgrade',422)
                if target['minimum']==previous['minimum'] and (units is None or (original['production_units'] is not None and units<=original['production_units'])):
                    fail('invalid_production_upgrade',422)
        proposed.update(term=term,production_band=band,production_units=units)
    return request,proposed


def retained(case,line,archive):
    value=case.payload
    if (checkout.digest(value)!=case.sha256 or value.get('case_id')!=str(case.identity)
            or value.get('entitlement_id')!=str(line.pk) or value.get('request_id')!=str(case.request_id)
            or value.get('kind')!=case.kind or value.get('original_offer_sha256')!=checkout.digest(line.snapshot)
            or value.get('original_configuration')!=line.snapshot['configuration']
            or value.get('grant_sha256')!=line.fulfilment.sha256 or value.get('effects_authorized') is not False):fail()
    request,configuration=normalized(value['original_configuration'],value['request'],value['catalog'])
    if request!=value['request'] or configuration!=value['proposed_configuration']:fail()
    materials.payment.recover(archive,case.archive_receipt,case.identity,checkout.canonical(value))


def capture(owner,checkout_id,line_id,request_id,raw,archive):
    synthetic_bank.guard()
    if type(request_id) is not uuid.UUID:fail('invalid_change_request',400)
    with transaction.atomic(durable=True):
        line=materials.line_locked(owner,checkout_id,line_id,archive)
        previous=SyntheticLicenceCase.objects.filter(entitlement=line,request_id=request_id).first()
        if previous:
            retained(previous,line,archive)
            request,_=normalized(previous.payload['original_configuration'],raw,previous.payload['catalog'])
            if request!=previous.payload['request']:fail('case_request_conflict')
            return previous
        catalog=source(line.snapshot['configuration'])
        request,proposed=normalized(line.snapshot['configuration'],raw,catalog)
        if not evaluate({k:v for k,v in proposed.items() if k!='platform'})['valid']:fail('invalid_revised_scope',422)
        if SyntheticLicenceCase.objects.filter(entitlement=line).count()>=1000:fail('licence_case_limit',422)
        identity=uuid.uuid5(line.pk,'licence-case-'+str(request_id))
        value={'schema':1,'case_id':str(identity),'entitlement_id':str(line.pk),'request_id':str(request_id),
            'kind':request['kind'],'request':request,'original_offer_sha256':checkout.digest(line.snapshot),
            'original_configuration':line.snapshot['configuration'],'proposed_configuration':proposed,
            'grant_sha256':line.fulfilment.sha256,'catalog':catalog,'evidence_class':'local-synthetic',
            'effects_authorized':False,'actual_rights_changed':False,'financial_confirmation':False}
        body=checkout.canonical(value);receipt=archive.publish(identity,body)
        materials.payment.recover(archive,manifest(receipt),identity,body)
        return SyntheticLicenceCase.objects.create(identity=identity,entitlement=line,request_id=request_id,
            kind=request['kind'],payload=value,sha256=checkout.digest(value),archive_receipt=manifest(receipt))


def case_locked(owner,checkout_id,identity,archive):
    materials.payment.locked(owner,checkout_id)
    candidate=SyntheticLicenceCase.objects.filter(identity=identity,entitlement__fulfilment__acceptance__checkout_id=checkout_id).first()
    if candidate is None:fail('not_found',404)
    line=materials.line_locked(owner,checkout_id,candidate.entitlement_id,archive)
    case=SyntheticLicenceCase.objects.select_for_update().get(pk=candidate.pk)
    retained(case,line,archive)
    return case


def proposed_order(case,event_id,review_id):
    return {'scope_revision':{'id':str(uuid.uuid5(event_id,'revised-scope')),'parent_entitlement_id':str(case.entitlement_id),
                'configuration':case.payload['proposed_configuration'],'activation_enabled':False},
            'order':{'id':str(uuid.uuid5(event_id,'held-order')),'status':'held_pending_policy',
                'quotation_required':case.payload['proposed_configuration']['production_band']=='higher-volume',
                'policies':{key:None for key in PENDING},'payment_enabled':False},
            'review_id':str(review_id),'support_changed':False,'physical_recall_promised':False,'actual_rights_changed':False}


def replay(case,events,archive):
    previous=case.sha256;review=None;proposal=None
    for revision,row in enumerate(events,1):
        value=row.payload
        if (row.revision!=revision or value.get('revision')!=revision or value.get('case_sha256')!=case.sha256
                or value.get('previous_sha256')!=previous or value.get('event_id')!=str(row.pk)
                or value.get('request_id')!=str(row.request_id) or value.get('kind')!=row.kind
                or value.get('command',{}).get('expected_revision')!=revision-1
                or checkout.digest(value)!=row.sha256 or value.get('effects_authorized') is not False):fail()
        materials.payment.recover(archive,row.archive_receipt,row.pk,checkout.canonical(value))
        if row.kind=='review':
            if value['command']['decision'] not in DECISIONS:fail()
            review=row
        elif row.kind=='proposal':
            if review is None or review.payload['command']['decision']!='ready_for_commercial_review' or value.get('proposal')!=proposed_order(case,row.pk,review.pk):fail()
            proposal=row
        else:fail()
        previous=row.sha256
    active=bool(proposal and review and proposal.payload['proposal']['review_id']==str(review.pk) and review.payload['command']['decision']=='ready_for_commercial_review')
    return {'revision':len(events),'sha256':previous,'decision':review.payload['command']['decision'] if review else 'awaiting_review',
            'review':review,'proposal':proposal,'proposal_active':active}


def event(request,owner,checkout_id,identity,request_id,expected_revision,kind,archive,*,decision=None):
    synthetic_bank.guard()
    if (type(request_id) is not uuid.UUID or type(expected_revision) is not int or not 0<=expected_revision<=1000
            or kind not in ('review','proposal') or (kind=='review' and decision not in DECISIONS) or (kind=='proposal' and decision is not None)):fail('invalid_case_action',400)
    command={'expected_revision':expected_revision,'decision':decision}
    with transaction.atomic(durable=True):
        staff_locked(request)
        if not SyntheticLicenceCaseStaffGrant.objects.filter(user=request.user,case__identity=identity).exists():fail('not_found',404)
        case=case_locked(owner,checkout_id,identity,archive);actor=staff_locked(request,case)
        events=list(SyntheticLicenceCaseEvent.objects.filter(case=case).order_by('revision'));state=replay(case,events,archive)
        prior=next((row for row in events if row.request_id==request_id),None)
        if prior:
            if prior.kind!=kind or prior.payload['command']!=command or prior.payload['actor']['staff_id']!=actor['staff_id']:fail('case_request_conflict')
            return prior
        if state['revision']!=expected_revision:fail('case_revision_changed')
        if state['revision']>=1000:fail('case_event_limit',422)
        identity=uuid.uuid5(case.identity,'event-'+str(request_id))
        value={'kind':kind,'event_id':str(identity),'request_id':str(request_id),'revision':state['revision']+1,
            'case_sha256':case.sha256,'previous_sha256':state['sha256'],'command':command,'actor':actor,
            'evidence_class':'local-synthetic','effects_authorized':False}
        if kind=='proposal':
            if case.payload['catalog']['revision']!=CATALOG['revision']:fail('catalog_scope_changed')
            if state['decision']!='ready_for_commercial_review':fail('commercial_review_required',422)
            if state['proposal_active']:fail('proposal_already_prepared')
            value['proposal']=proposed_order(case,identity,state['review'].pk)
        body=checkout.canonical(value);receipt=archive.publish(identity,body)
        materials.payment.recover(archive,manifest(receipt),identity,body)
        staff_locked(request,case)
        return SyntheticLicenceCaseEvent.objects.create(id=identity,case=case,request_id=request_id,revision=value['revision'],
            kind=kind,payload=value,sha256=checkout.digest(value),archive_receipt=manifest(receipt))


def summary(case,events,archive,before=None):
    state=replay(case,events,archive)
    visible=[row for row in reversed(events) if before is None or row.revision<before]
    proposal=deepcopy(state['proposal'].payload['proposal']) if state['proposal'] else None
    if proposal:proposal['active']=state['proposal_active'] and case.payload['catalog']['revision']==CATALOG['revision']
    return {'case_id':str(case.identity),'kind':case.kind,'request':case.payload['request'],
        'original_configuration':case.payload['original_configuration'],'proposed_configuration':case.payload['proposed_configuration'],
        'catalog_revision':case.payload['catalog']['revision'],'revision':state['revision'],'decision':state['decision'],'proposal':proposal,
        'history':[{'revision':row.revision,'kind':row.kind,'decision':row.payload['command']['decision']} for row in visible[:20]],
        'next_before':visible[19].revision if len(visible)>20 else None,
        'evidence_class':'local-synthetic','payment_enabled':False,'effects_authorized':False,'actual_rights_changed':False}
