"""Private owner-only partial business drafts. No business values in ordinary summaries."""
import re
import uuid
from django import forms
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_http_methods
from . import business_rules as rules
from .models import BusinessDraft, BusinessDraftSnapshot
from .views import local_customer

class BusinessForm(forms.Form):
    pass

LABELS={field:label for _,label,fields,_ in rules.GROUPS for field in fields}
LABELS.update({'registered_city':'Registered city','registered_region':'Registered region','registered_postcode':'Registered postcode',
    'billing_city':'Billing city','billing_region':'Billing region','billing_postcode':'Billing postcode',
    'billing_same_as_registered':'Same as registered address (including city, region and postcode)',
    'technical_same_as_purchasing':'Same as purchasing contact','technical_name':'Technical / licence administrator name',
    'technical_email':'Technical / licence administrator email'})
for name,limit in rules.LIMITS.items():
    widget=forms.Textarea(attrs={'rows':3,'autocomplete':'off'}) if name in rules.MULTILINE else (forms.EmailInput(attrs={'autocomplete':'off'}) if name.endswith('email') else forms.TextInput(attrs={'autocomplete':'off'}))
    BusinessForm.base_fields[name]=forms.CharField(required=False,max_length=limit,label=LABELS[name],widget=widget)
for name in rules.PENDING:
    BusinessForm.base_fields[name]=forms.ChoiceField(required=False,disabled=True,label=LABELS[name],choices=[('','Pending approval')])
for name in rules.HELPERS:
    BusinessForm.base_fields[name]=forms.BooleanField(required=False,label=LABELS[name])


def current(owner):
    draft=BusinessDraft.objects.filter(owner=owner).first()
    snapshot=BusinessDraftSnapshot.objects.filter(draft=draft,version=draft.version).first() if draft else None
    return draft,snapshot


def page(request,*,status=200,message='',initial=None,errors=None,expected_version=None,submitted_source=None):
    draft,snapshot=current(request.user)
    details=initial if initial is not None else snapshot.details if snapshot else rules.empty_details()
    form=BusinessForm(initial=details)
    groups=[{'id':key,'label':label,'hint':hint,'fields':[form[field] for field in fields],'required':key in ('legal_business_name','registered_address','billing_address','purchasing_name','business_email','technical_contact'),'pending':key in rules.PENDING,'wide':key in ('registered_address','billing_address','notes')} for key,label,fields,hint in rules.GROUPS]
    response=render(request,'catalog/business.html',{'groups':groups,'version':draft.version if draft else 0,
        'expected_version':expected_version if expected_version is not None else draft.version if draft else 0,
        'request_id':str(uuid.uuid4()),'schema_version':rules.SCHEMA_VERSION,'source_sha256':submitted_source if submitted_source is not None else rules.SOURCE_SHA256,
        'message':message,'errors':[LABELS.get(key,'Submission') for key in (errors or [])],
        'evaluation':rules.evaluate_details(details),'confirmation':request.session.get('business_last_confirmed_version')},status=status)
    response['Cache-Control']='no-store';response['Referrer-Policy']='no-referrer';response['Vary']='Cookie'
    response['Content-Security-Policy']="default-src 'none'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'"
    return response


def read_submission(request):
    if request.content_type!='application/x-www-form-urlencoded':raise ValueError('content_type')
    if int(request.META.get('CONTENT_LENGTH') or 0)>32768 or len(request.body)>32768:raise ValueError('size')
    controls={'request_id','expected_version','schema_version','source_sha256','csrfmiddlewaretoken'}
    fields=set(rules.empty_details())
    value=request.POST
    if set(value)-controls-fields or any(len(value.getlist(key))!=1 for key in value):raise ValueError('fields')
    if re.fullmatch(r'0|[1-9][0-9]{0,9}',value.get('expected_version','')) is None:raise ValueError('version')
    version=int(value['expected_version'])
    if version>=1000000000:raise ValueError('version')
    if value.get('schema_version')!=str(rules.SCHEMA_VERSION):raise ValueError('schema')
    source=value.get('source_sha256','')
    if re.fullmatch('[0-9a-f]{64}',source) is None:raise ValueError('source')
    request_id=uuid.UUID(value.get('request_id',''))
    details={name:value.get(name,'') for name in rules.LIMITS}
    for name in rules.HELPERS:
        if name in value and value[name]!='on':raise ValueError('helper')
        details[name]=name in value
    for name in rules.PENDING:
        if value.get(name,'')!='':raise ValueError('pending')
        details[name]=None
    return request_id,version,source,details


@require_http_methods(['GET','POST'])
@sensitive_post_parameters()
def business_editor(request):
    denied=local_customer(request)
    if denied is not None:
        denied['Cache-Control']='no-store';return denied
    if request.GET:return page(request,status=400,message='Query parameters are not accepted. Only the saved owner draft is shown.')
    if request.method=='GET':return page(request)
    try:request_id,expected,source,raw=read_submission(request)
    except (ValueError,TypeError,UnicodeError,RecursionError):
        return page(request,status=400,message='Submission rejected. Current saved draft loaded; submitted values were not saved.')
    clean,errors=rules.validate_details(raw)
    if errors:return page(request,status=422,message='Check the listed fields. Nothing was saved.',initial=clean,errors=errors,expected_version=expected,submitted_source=source)
    digest=rules.submission_digest(clean)
    with transaction.atomic():
        draft,_=BusinessDraft.objects.get_or_create(owner=request.user)
        draft=BusinessDraft.objects.select_for_update().get(pk=draft.pk)
        old=BusinessDraftSnapshot.objects.filter(draft=draft,request_id=request_id).first()
        error=None
        if old is not None:
            if old.submission_digest!=digest or old.version-1!=expected or old.source_sha256!=source or old.schema_version!=rules.SCHEMA_VERSION:
                error='This submission identity was used for different values. Reload the saved draft before editing.'
            else:confirmed=old.version
        elif source!=rules.SOURCE_SHA256:
            error='The source changed. Reload and review the current draft before saving.'
        elif draft.version!=expected:
            error='The business draft changed in another tab. Reload and review the current draft before saving.'
        else:
            details=rules.resolve_details(clean)
            draft.version+=1
            BusinessDraftSnapshot.objects.create(draft=draft,version=draft.version,request_id=request_id,
                schema_version=rules.SCHEMA_VERSION,source_sha256=source,submission_digest=digest,details=details,evaluation=rules.evaluate_details(details))
            draft.save(update_fields=['version']);confirmed=draft.version
        if error:
            transaction.set_rollback(True)
    if error:return page(request,status=409,message=error)
    # Confirmation contains version metadata only; private values remain in DB snapshots.
    request.session['business_last_confirmed_version']=confirmed
    response=HttpResponseRedirect('/purchase/business/');response.status_code=303
    response['Cache-Control']='no-store';return response
