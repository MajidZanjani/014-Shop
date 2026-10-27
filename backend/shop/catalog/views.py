import json
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .rules import CATALOG, evaluate

@require_GET
def catalog(request):
    response = JsonResponse(CATALOG)
    response['ETag'] = '"'+CATALOG['revision']+'"'
    return response

def unique_object(pairs):
    value = {}
    for key,item in pairs:
        if key in value: raise ValueError('duplicate')
        value[key] = item
    return value

# Public pure evaluator: no session, secrets, persistence, cookies or side effects.
@csrf_exempt
@require_POST
def validate(request):
    if request.content_type != 'application/json': return JsonResponse({'error':'content_type'},status=415)
    try:
        if int(request.META.get('CONTENT_LENGTH') or 0) > 8192: raise ValueError('size')
        raw = request.read(8193)
        if len(raw) > 8192: raise ValueError('size')
        value = json.loads(raw,object_pairs_hook=unique_object,parse_constant=lambda _: (_ for _ in ()).throw(ValueError('constant')))
        result = evaluate(value)
    except (ValueError,UnicodeError,RecursionError):
        return JsonResponse({'error':'invalid_json'},status=400)
    response = JsonResponse(result,status=200 if result['valid'] else 422)
    response['Cache-Control'] = 'no-store'
    return response


def local_customer(request):
    from django.conf import settings
    def denied(error,status):
        response=JsonResponse({'error':error},status=status)
        response['Cache-Control']='no-store'
        return response
    if settings.SHOP_ENV not in ('local','synthetic'):
        return denied('unavailable',404)
    if not request.user.is_authenticated:
        return denied('authentication_required',401)
    if request.user.is_staff or request.user.is_superuser or not request.user.is_active:
        return denied('customer_access_required',403)
    from shop.access.views import verified_identity
    if verified_identity(request) is None:
        return denied('verification_required',403)
    return None


def draft_json(row):
    return {'id':str(row.id),'revision':row.revision,'configuration':row.configuration,
            'evaluation':row.evaluation,'created_at':row.created_at.isoformat(),'state':'draft'}


@require_http_methods(['GET','POST'])
def save_draft(request):
    from uuid import UUID
    from django.db import transaction
    from .models import ConfigurationDraft
    denied=local_customer(request)
    if denied is not None: return denied
    if request.method=='GET':
        rows=ConfigurationDraft.objects.filter(owner=request.user).order_by('-created_at','-id')[:20]
        response=JsonResponse({'drafts':[{'id':str(row.id),'revision':row.revision,'created_at':row.created_at.isoformat()} for row in rows],'limit':20})
        response['Cache-Control']='no-store'
        return response
    if request.content_type != 'application/json': return JsonResponse({'error':'content_type'},status=415)
    try:
        if int(request.META.get('CONTENT_LENGTH') or 0)>8192: raise ValueError('size')
        raw=request.read(8193)
        if len(raw)>8192: raise ValueError('size')
        value=json.loads(raw,object_pairs_hook=unique_object,parse_constant=lambda _: (_ for _ in ()).throw(ValueError('constant')))
        if not isinstance(value,dict) or set(value)!={'request_id','revision','configuration'}: raise ValueError('fields')
        if not isinstance(value['request_id'],str): raise ValueError('uuid')
        request_id=UUID(value['request_id'])
    except (ValueError,TypeError,UnicodeError,RecursionError):
        return JsonResponse({'error':'invalid_request'},status=400)
    if value['revision']!=CATALOG['revision']: return JsonResponse({'error':'stale_catalog'},status=409)
    evaluation=evaluate(value['configuration'])
    if not evaluation['valid']: return JsonResponse(evaluation,status=422)
    # This is an unaccepted local draft, never an approved offer or host binding.
    # get_or_create's unique-key arbitration handles concurrent retries on PostgreSQL.
    with transaction.atomic():
        row,created=ConfigurationDraft.objects.get_or_create(owner=request.user,request_id=request_id,defaults={
            'revision':CATALOG['revision'],'configuration':value['configuration'],'evaluation':evaluation})
        if row.revision!=value['revision'] or row.configuration!=value['configuration']:
            return JsonResponse({'error':'request_conflict'},status=409)
    response=JsonResponse(draft_json(row),status=201 if created else 200)
    response['Cache-Control']='no-store'
    return response


@require_GET
def get_draft(request,identity):
    from .models import ConfigurationDraft
    denied=local_customer(request)
    if denied is not None: return denied
    row=ConfigurationDraft.objects.filter(pk=identity,owner=request.user).first()
    if row is None: return JsonResponse({'error':'not_found'},status=404)
    response=JsonResponse(draft_json(row))
    response['Cache-Control']='no-store'
    return response
