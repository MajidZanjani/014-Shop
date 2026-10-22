"""Verified owner-only local draft carts. No quote acceptance or payment effects."""
import json
import uuid
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .cart_rules import evaluate_cart
from .models import DraftCart,CartSnapshot
from .rules import CATALOG
from .views import local_customer,unique_object

def reply(value,status=200):
    response=JsonResponse(value,status=status);response['Cache-Control']='no-store';return response

def snapshot_json(cart,snapshot=None):
    return {'cart_id':str(cart.id) if cart else None,'version':snapshot.version if snapshot else 0,
            'current_version':cart.version if cart else 0,'catalog_revision':snapshot.catalog_revision if snapshot else CATALOG['revision'],
            'lines':snapshot.lines if snapshot else [],'evaluation':snapshot.evaluation if snapshot else evaluate_cart([]),
            'state':'draft','checkout_enabled':False}

@require_http_methods(['GET','POST'])
def current_cart(request):
    denied=local_customer(request)
    if denied is not None:return denied
    if request.GET:return reply({'error':'unexpected_query'},400)
    if request.method=='GET':
        cart=DraftCart.objects.filter(owner=request.user).first()
        snapshot=CartSnapshot.objects.get(cart=cart,version=cart.version) if cart and cart.version else None
        return reply(snapshot_json(cart,snapshot))
    if request.content_type!='application/json':return reply({'error':'content_type'},415)
    try:
        if int(request.META.get('CONTENT_LENGTH') or 0)>32768:raise ValueError('size')
        raw=request.read(32769)
        if len(raw)>32768:raise ValueError('size')
        value=json.loads(raw,object_pairs_hook=unique_object,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('constant')))
        if not isinstance(value,dict) or set(value)!={'request_id','expected_version','catalog_revision','lines'}:raise ValueError('fields')
        if not isinstance(value['request_id'],str):raise ValueError('uuid')
        request_id=uuid.UUID(value['request_id'])
        if type(value['expected_version']) is not int or not 0<=value['expected_version']<=1000000000:raise ValueError('version')
        if not isinstance(value['catalog_revision'],str) or len(value['catalog_revision'])!=64:raise ValueError('revision')
    except (ValueError,TypeError,UnicodeError,RecursionError):return reply({'error':'invalid_request'},400)
    with transaction.atomic():
        cart,_=DraftCart.objects.get_or_create(owner=request.user)
        cart=DraftCart.objects.select_for_update().get(pk=cart.pk)
        old=CartSnapshot.objects.filter(cart=cart,request_id=request_id).first()
        # Reconcile an already committed request before current-catalog admission.
        if old is not None:
            if json.dumps(old.lines,sort_keys=True)!=json.dumps(value['lines'],sort_keys=True) or old.catalog_revision!=value['catalog_revision'] or old.version-1!=value['expected_version']:
                return reply({'error':'request_conflict'},409)
            return reply(snapshot_json(cart,old))
        if value['catalog_revision']!=CATALOG['revision']:
            transaction.set_rollback(True);return reply({'error':'stale_catalog'},409)
        evaluation=evaluate_cart(value['lines'])
        if not evaluation['valid']:
            transaction.set_rollback(True);return reply(evaluation,422)
        if cart.version!=value['expected_version']:
            transaction.set_rollback(True);return reply({'error':'cart_changed','current_version':cart.version},409)
        if cart.version>=1000000000:return reply({'error':'version_limit'},409)
        cart.version+=1
        snapshot=CartSnapshot.objects.create(cart=cart,version=cart.version,request_id=request_id,catalog_revision=value['catalog_revision'],lines=value['lines'],evaluation=evaluation)
        cart.save(update_fields=['version'])
    return reply(snapshot_json(cart,snapshot),201)
