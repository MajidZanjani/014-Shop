"""Explicit internal capture, retained reads and retry arbitration. No offer effects."""
import copy
from datetime import datetime, timezone as datetime_timezone
import hashlib
import json
import re
import uuid
from django.db import transaction
from django.db.models import F, Q
from django.http import HttpResponseRedirect
from django.views.decorators.http import require_GET, require_http_methods
from shop.catalog.business_scope import current_scope, valid_business
from shop.catalog.document_preview import preview
from shop.catalog.models import QuotationRequest, QuotationReview
from shop.catalog.rules import CATALOG
from .models import PreparationAssessment, StaffCredential, StaffQuotationGrant
from .offer_preparation import assess
from .quotation_review import snapshot_digest
from .staff_auth import payload, staff_credential
from .staff_views import page
from .views import reply

SCHEMA_VERSION = 1
DISABLED = ('offer_creation_enabled','publication_enabled','acceptance_enabled','checkout_enabled')


def blocked_assessment(value):
    return (isinstance(value,dict) and value.get('state')=='blocked'
            and value.get('country_tax_choices')=='deferred'
            and all(value.get(key) is False for key in DISABLED)
            and value.get('quote_valid_until') is None and value.get('payment_due_at') is None
            and value.get('money')=={'currency':'EUR','currency_status':'draft','subtotal_minor':None,'tax_minor':None,'total_minor':None})


def fingerprint(assessment, scope_digest, schema_version=SCHEMA_VERSION):
    value={'schema_version':schema_version,'scope_digest':scope_digest,'assessment':assessment}
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()).hexdigest()


def assignment(request, identity, quotation=None):
    rows=StaffQuotationGrant.objects.select_related('quotation__cart','quotation__snapshot')
    if quotation is not None:rows=rows.filter(quotation=quotation)
    return rows.filter(user=request.user,quotation_id=identity,quotation__snapshot__cart_id=F('quotation__cart_id')).first()


def current_error(grant):
    q=grant.quotation
    if q.business_version:
        if grant.business_scope_version!=q.business_version:return ('business_scope_access_required',403)
        if current_scope(q) is None:return ('business_scope_unavailable',409)
    return None


def retained_error(row, grant):
    q=grant.quotation
    if row.version>q.preparation_version:return ('snapshot_unavailable',409)
    if row.business_version:
        if grant.business_scope_version!=row.business_version:return ('business_scope_access_required',403)
        scope=row.business_scope
        if (scope is None or scope.quotation_id!=q.pk or scope.version!=row.business_version
            or scope.business_snapshot.draft.owner_id!=q.cart.owner_id):return ('snapshot_unavailable',409)
    elif row.business_scope_id is not None:return ('snapshot_unavailable',409)
    if row.review_version:
        if row.review is None or row.review.quotation_id!=q.pk or row.review.version!=row.review_version:return ('snapshot_unavailable',409)
    elif row.review_id is not None:return ('snapshot_unavailable',409)
    original=copy.copy(q);original.business_version=row.business_version
    if (row.schema_version!=SCHEMA_VERSION or not blocked_assessment(row.assessment)
        or fingerprint(row.assessment,row.scope_digest,row.schema_version)!=row.assessment_digest):return ('snapshot_unavailable',409)
    try:
        if snapshot_digest(original)!=row.scope_digest:return ('snapshot_unavailable',409)
    except ValueError:return ('snapshot_unavailable',409)
    return None


def response_error(request, code, status):
    if 'text/html' not in request.headers.get('Accept',''):return reply({'error':code},status)
    messages={
        'recent_staff_mfa_required':'Sign in again for recent staff verification.',
        'not_found':'This request is unavailable or no longer assigned.',
        'business_scope_access_required':'Explicit private permission is required for this exact recorded business scope.',
        'request_conflict':'This submission identity was used for different capture content or attribution. Reload before another capture.',
        'preparation_changed':'Another preparation snapshot was retained. Reload and review the current assessment.',
        'assessment_changed':'The assessed source, scope or review changed. Reload and review it before capturing.',
        'invalid_request':'Capture rejected. Use the displayed form without additional fields.',
    }
    response=page(request,'access/preparation_capture_error.html',{'message':messages.get(code,'The retained source or scope is unavailable. Reload and review it.'),'return_path':request.path.rsplit('preparation-snapshots/',1)[0]+'preparation-snapshots/'})
    response.status_code=status
    return response


def snapshot_json(row):
    return {'version':row.version,'business_version':row.business_version,'review_version':row.review_version,
            'schema_version':row.schema_version,'created_at':row.created_at.isoformat(),'captured_by':row.captured_by_id,
            'assessment':row.assessment}


def capture_result(request, row, created):
    if request.content_type=='application/x-www-form-urlencoded':
        response=HttpResponseRedirect('/staff/quotation-requests/'+str(row.quotation_id)+'/preparation-snapshots/'+str(row.version)+'/')
        response.status_code=303;response['Cache-Control']='no-store';response['Referrer-Policy']='no-referrer'
        return response
    return reply({'snapshot':snapshot_json(row),'created':created},201 if created else 200)


@require_http_methods(['GET','POST'])
def snapshots(request,identity):
    if staff_credential(request,recent=True) is None:return response_error(request,'recent_staff_mfa_required',403)
    if request.GET:return response_error(request,'invalid_request',400)
    if request.method=='GET':
        grant=assignment(request,identity)
        if grant is None:return response_error(request,'not_found',404)
        error=current_error(grant)
        if error:return response_error(request,*error)
        q=grant.quotation;assessment=assess(q)
        scope=current_scope(q)
        can_capture=(preview(q)['state']=='preview_only' and q.snapshot.catalog_revision==CATALOG['revision']
                     and (not q.business_version or valid_business(scope.business_snapshot,q.cart.owner_id))
                     and blocked_assessment(assessment)
                     and (not q.review_version or QuotationReview.objects.filter(quotation=q,version=q.review_version).exists()))
        digest=fingerprint(assessment,snapshot_digest(q)) if can_capture else None
        # Scope-specific list metadata; hidden historical captures are not projected.
        rows=PreparationAssessment.objects.filter(quotation=q,version__lte=q.preparation_version).filter(
            Q(business_version=0,business_scope__isnull=True)|Q(business_version=grant.business_scope_version,business_scope__quotation=q,
                business_scope__version=F('business_version'),business_scope__business_snapshot__draft__owner_id=q.cart.owner_id)
        ).order_by('-version').values('version','business_version','review_version','created_at')[:20]
        context={'quotation':q,'preparation':assessment,'expected_preparation_version':q.preparation_version,
                 'assessment_digest':digest,'request_id':str(uuid.uuid4()),'snapshots':list(rows),'history_limit':20}
        if 'text/html' in request.headers.get('Accept',''):
            response=page(request,'access/preparation_snapshots.html',context)
        else:
            response=reply({key:value for key,value in context.items() if key!='quotation'})
        response['Vary']='Cookie'
        return response
    try:
        if int(request.META.get('CONTENT_LENGTH') or 0)>1024 or len(request.body)>1024:raise ValueError('size')
        value=payload(request,{'request_id','expected_preparation_version','assessment_digest'})
        if request.content_type=='application/x-www-form-urlencoded':
            if re.fullmatch(r'0|[1-9][0-9]{0,9}',value['expected_preparation_version']) is None:raise ValueError('version')
            value['expected_preparation_version']=int(value['expected_preparation_version'])
        if not isinstance(value['request_id'],str):raise ValueError('uuid')
        key=uuid.UUID(value['request_id'])
        if type(value['expected_preparation_version']) is not int or not 0<=value['expected_preparation_version']<1000000000:raise ValueError('version')
        if not isinstance(value['assessment_digest'],str) or re.fullmatch('[0-9a-f]{64}',value['assessment_digest']) is None:raise ValueError('digest')
    except (ValueError,TypeError,UnicodeError,RecursionError):return response_error(request,'invalid_request',400)
    with transaction.atomic():
        admitted=staff_credential(request,recent=True)
        if admitted is None:return response_error(request,'recent_staff_mfa_required',403)
        credential=StaffCredential.objects.select_for_update().filter(pk=admitted.pk,enabled=True,generation=admitted.generation,user__is_active=True,user__is_staff=True).first()
        if credential is None or staff_credential(request,recent=True) is None:return response_error(request,'recent_staff_mfa_required',403)
        q=QuotationRequest.objects.select_for_update().filter(pk=identity).first()
        grant=assignment(request,identity,quotation=q) if q else None
        if grant is None:return response_error(request,'not_found',404)
        # Use the locked parent's counters, not a second unlocked object.
        grant.quotation=q
        old=PreparationAssessment.objects.select_related('business_scope__business_snapshot__draft','review').filter(quotation=q,request_id=key).first()
        if old:
            if old.captured_by_id!=request.user.pk or old.version-1!=value['expected_preparation_version'] or old.assessment_digest!=value['assessment_digest']:
                return response_error(request,'request_conflict',409)
            error=retained_error(old,grant)
            return response_error(request,*error) if error else capture_result(request,old,False)
        error=current_error(grant)
        if error:return response_error(request,*error)
        if q.preparation_version!=value['expected_preparation_version']:return response_error(request,'preparation_changed',409)
        assessment=assess(q);scope=current_scope(q)
        review=QuotationReview.objects.filter(quotation=q,version=q.review_version).first() if q.review_version else None
        if (not blocked_assessment(assessment) or preview(q)['state']!='preview_only' or q.snapshot.catalog_revision!=CATALOG['revision']
            or (q.business_version and not valid_business(scope.business_snapshot,q.cart.owner_id))
            or (q.review_version and review is None)):return response_error(request,'assessment_changed',409)
        scope_digest=snapshot_digest(q)
        digest=fingerprint(assessment,scope_digest)
        if digest!=value['assessment_digest']:return response_error(request,'assessment_changed',409)
        marker=request.session['shop_staff_mfa']
        row=PreparationAssessment.objects.create(quotation=q,version=q.preparation_version+1,request_id=key,
            schema_version=SCHEMA_VERSION,business_version=q.business_version,business_scope=scope,review_version=q.review_version,review=review,
            scope_digest=scope_digest,assessment_digest=digest,assessment=assessment,captured_by=request.user,
            staff_generation=credential.generation,mfa_verified_at=datetime.fromtimestamp(marker['verified_at'],tz=datetime_timezone.utc))
        q.preparation_version=row.version;q.save(update_fields=['preparation_version'])
    return capture_result(request,row,True)


@require_GET
def snapshot_detail(request,identity,version):
    if staff_credential(request,recent=True) is None:return response_error(request,'recent_staff_mfa_required',403)
    if request.GET:return response_error(request,'invalid_request',400)
    grant=assignment(request,identity)
    if grant is None:return response_error(request,'not_found',404)
    row=PreparationAssessment.objects.select_related('business_scope__business_snapshot__draft','review').filter(
        quotation=grant.quotation,version=version,version__lte=grant.quotation.preparation_version).first()
    if row is None:return response_error(request,'not_found',404)
    error=retained_error(row,grant)
    if error:return response_error(request,*error)
    if 'text/html' in request.headers.get('Accept',''):
        return page(request,'access/preparation_snapshot.html',{'quotation':grant.quotation,'snapshot':row,'preparation':row.assessment})
    return reply(snapshot_json(row))
