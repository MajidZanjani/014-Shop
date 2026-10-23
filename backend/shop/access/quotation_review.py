"""Recent-MFA, exact-snapshot internal review; no payable or approved offers."""
from datetime import datetime, timezone as datetime_timezone
import hashlib
import json
import re
import uuid
from django.db import transaction
from django.db.models import F
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.decorators.http import require_POST
from shop.catalog.models import QuotationRequest, QuotationReview, REVIEW_DECISIONS
from shop.catalog.rules import CATALOG
from shop.catalog.business_scope import current_scope, valid_business, scope_for_version
from .models import StaffCredential, StaffQuotationGrant
from .staff_auth import staff_credential, payload
from .views import reply


def snapshot_digest(quotation):
    snapshot=quotation.snapshot
    value={'quotation_id':str(quotation.id),'snapshot_id':snapshot.id,'cart_id':str(snapshot.cart_id),
           'version':snapshot.version,'catalog_revision':snapshot.catalog_revision,
           'lines':snapshot.lines,'evaluation':snapshot.evaluation}
    if quotation.business_version:
        scope=current_scope(quotation)
        if scope is None:raise ValueError('business_scope_missing')
        business=scope.business_snapshot
        value['business_scope']={'version':scope.version,'snapshot_id':business.pk,'schema_version':business.schema_version,
                                 'source_sha256':business.source_sha256,'details':business.details,'evaluation':business.evaluation}
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()).hexdigest()


def review_json(row,private_scope_version=0):
    return {'version':row.version,'decision':row.decision,'label':row.get_decision_display(),
            'business_version':row.business_version,'snapshot_digest':row.snapshot_digest if not row.business_version or row.business_version==private_scope_version else None,'reviewer_id':str(row.reviewer_id),
            'mfa_verified_at':row.mfa_verified_at.isoformat(),'created_at':row.created_at.isoformat()}


def history_rows(quotation):
    return QuotationReview.objects.filter(quotation=quotation,version__lte=quotation.review_version).order_by('-version')


def history(quotation):
    return history_rows(quotation)[:20]


def result(request,quotation,row,created):
    if request.content_type=='application/json':
        return reply({'review':review_json(row,private_scope_version=row.business_version),'current_review_version':quotation.review_version,
                      'checkout_enabled':False,'acceptance_enabled':False},201 if created else 200)
    response=HttpResponseRedirect('/staff/quotation-requests/'+str(quotation.id)+'/')
    response.status_code=303;response['Cache-Control']='no-store';return response


def reject(request,code,status,**details):
    if request.content_type!='application/x-www-form-urlencoded':return reply({'error':code,**details},status)
    messages={
        'recent_staff_mfa_required':'Recent verification is required. Sign in again, then review the request.',
        'business_scope_access_required':'Private business access is required for this exact attached revision before it can be reviewed.',
        'business_scope_changed':'The business scope changed or requires source review. Reload the request and its attached details.',
        'not_found':'This request is unavailable or is no longer assigned to you.',
        'invalid_request':'The decision was not recorded. Choose a listed outcome and use the current form.',
        'request_conflict':'This submission was already used for a different decision. Reload the request and review its history.',
        'review_changed':'Another decision was recorded. Review the current history before making a correction.',
        'snapshot_changed':'The captured request differs from the form you reviewed. Reload and review its exact lines.',
        'stale_catalog':'The catalogue changed. A new current request is needed before recording another decision.',
    }
    response=render(request,'access/staff_review_error.html',{'message':messages.get(code,messages['invalid_request']),
        'return_path':request.path.removesuffix('reviews/')},status=status)
    response['Cache-Control']='no-store';response['Referrer-Policy']='no-referrer'
    response['Content-Security-Policy']="default-src 'none'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'"
    return response

@require_POST
def record_review(request,identity):
    if staff_credential(request,recent=True) is None:return reject(request,'recent_staff_mfa_required',403)
    if request.GET:return reject(request,'invalid_request',400)
    try:
        value=payload(request,{'request_id','expected_review_version','snapshot_digest','decision'})
        if request.content_type=='application/x-www-form-urlencoded':
            raw=value['expected_review_version']
            if re.fullmatch(r'0|[1-9][0-9]{0,9}',raw) is None:raise ValueError('version')
            value['expected_review_version']=int(raw)
        if not isinstance(value['request_id'],str):raise ValueError('uuid')
        request_id=uuid.UUID(value['request_id'])
        if type(value['expected_review_version']) is not int or not 0<=value['expected_review_version']<1000000000:raise ValueError('version')
        if not isinstance(value['snapshot_digest'],str) or re.fullmatch('[0-9a-f]{64}',value['snapshot_digest']) is None:raise ValueError('digest')
        if not isinstance(value['decision'],str) or value['decision'] not in dict(REVIEW_DECISIONS):raise ValueError('decision')
    except (ValueError,TypeError,UnicodeError,RecursionError):return reject(request,'invalid_request',400)
    with transaction.atomic():
        # Same credential-first lock order as operator reset/grant/revocation.
        admitted=staff_credential(request,recent=True)
        if admitted is None:return reject(request,'recent_staff_mfa_required',403)
        credential=StaffCredential.objects.select_for_update().filter(pk=admitted.pk,enabled=True,
            generation=admitted.generation,user__is_active=True,user__is_staff=True).first()
        if credential is None or staff_credential(request,recent=True) is None:
            return reject(request,'recent_staff_mfa_required',403)
        quotation=QuotationRequest.objects.select_for_update().filter(pk=identity,snapshot__cart_id=F('cart_id')).first()
        grant=StaffQuotationGrant.objects.filter(user=request.user,quotation=quotation).first() if quotation else None
        if grant is None:return reject(request,'not_found',404)
        old=QuotationReview.objects.filter(quotation=quotation,request_id=request_id).first()
        if old is not None:
            if (old.reviewer_id!=request.user.pk or old.version-1!=value['expected_review_version']
                or old.snapshot_digest!=value['snapshot_digest'] or old.decision!=value['decision']):
                return reject(request,'request_conflict',409)
            if old.business_version and grant.business_scope_version!=old.business_version:
                return reject(request,'business_scope_access_required',403)
            if old.business_version and scope_for_version(quotation,old.business_version) is None:
                return reject(request,'business_scope_changed',409)
            return result(request,quotation,old,False)
        if quotation.review_version!=value['expected_review_version']:
            return reject(request,'review_changed',409,current_review_version=quotation.review_version)
        if quotation.business_version:
            if grant.business_scope_version!=quotation.business_version:return reject(request,'business_scope_access_required',403)
            scope=current_scope(quotation)
            if scope is None or not valid_business(scope.business_snapshot,quotation.cart.owner_id):return reject(request,'business_scope_changed',409)
        if snapshot_digest(quotation)!=value['snapshot_digest']:return reject(request,'snapshot_changed',409)
        if quotation.snapshot.catalog_revision!=CATALOG['revision']:return reject(request,'stale_catalog',409)
        quotation.review_version+=1
        marker=request.session['shop_staff_mfa']
        row=QuotationReview.objects.create(quotation=quotation,version=quotation.review_version,business_version=quotation.business_version,request_id=request_id,
            snapshot_digest=value['snapshot_digest'],decision=value['decision'],reviewer=request.user,
            reviewer_generation=credential.generation,mfa_verified_at=datetime.fromtimestamp(marker['verified_at'],tz=datetime_timezone.utc))
        quotation.save(update_fields=['review_version'])
    return result(request,quotation,row,True)
