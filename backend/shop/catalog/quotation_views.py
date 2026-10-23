"""Local/synthetic owner requests. No offer, acceptance, dispatch or credit effects."""
import json
import uuid
from django.db import transaction
from django.db.models import F
from django.views.decorators.http import require_GET, require_http_methods
from .cart_views import reply
from .models import DraftCart, CartSnapshot, QuotationRequest, QuotationRequestKey
from .rules import CATALOG
from .cart_rules import evaluate_cart
from .views import local_customer, unique_object
from .business_scope import scope_metadata
from .quotation_status import customer_review_status, with_review_status


def quotation_json(row):
    snapshot=row.snapshot
    return {'id':str(row.id),'created_at':row.created_at.isoformat(),
            'cart_id':str(row.cart_id),'version':snapshot.version,
            'catalog_revision':snapshot.catalog_revision,'lines':snapshot.lines,
            'evaluation':snapshot.evaluation,'state':'requested','review_status':customer_review_status(row),'business_scope':scope_metadata(row),
            'prices':None,'rights':None,'acceptance_enabled':False,'checkout_enabled':False}


@require_http_methods(['GET','POST'])
def quotations(request):
    denied=local_customer(request)
    if denied is not None:
        denied['Cache-Control']='no-store'
        return denied
    if request.GET:return reply({'error':'unexpected_query'},400)
    if request.method=='GET':
        rows=with_review_status(QuotationRequest.objects.filter(cart__owner=request.user,snapshot__cart_id=F('cart_id'))).select_related('snapshot').order_by('-created_at','-id')[:20]
        return reply({'requests':[{'id':str(row.id),'version':row.snapshot.version,
                                  'created_at':row.created_at.isoformat(),'state':'requested','review_status':customer_review_status(row)} for row in rows],'limit':20})
    if request.content_type!='application/json':return reply({'error':'content_type'},415)
    try:
        if int(request.META.get('CONTENT_LENGTH') or 0)>1024:raise ValueError('size')
        raw=request.read(1025)
        if len(raw)>1024:raise ValueError('size')
        value=json.loads(raw,object_pairs_hook=unique_object,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('constant')))
        if not isinstance(value,dict) or set(value)!={'request_id','cart_id','version'}:raise ValueError('fields')
        if not isinstance(value['request_id'],str) or not isinstance(value['cart_id'],str):raise ValueError('uuid')
        request_id=uuid.UUID(value['request_id']);cart_id=uuid.UUID(value['cart_id'])
        if type(value['version']) is not int or not 1<=value['version']<=1000000000:raise ValueError('version')
    except (ValueError,TypeError,UnicodeError,RecursionError):return reply({'error':'invalid_request'},400)
    with transaction.atomic():
        # Same lock as cart saves: submission cannot silently race an edit.
        cart=DraftCart.objects.select_for_update().filter(pk=cart_id,owner=request.user).first()
        if cart is None:return reply({'error':'not_found'},404)
        key=QuotationRequestKey.objects.select_related('quotation__snapshot').filter(cart=cart,request_id=request_id).first()
        old=key.quotation if key else None
        if old is not None:
            if old.cart_id!=cart.pk or old.snapshot.cart_id!=cart.pk:return reply({'error':'not_found'},404)
            if old.snapshot.version!=value['version']:return reply({'error':'request_conflict'},409)
            return reply(quotation_json(old))
        snapshot=CartSnapshot.objects.filter(cart=cart,version=value['version']).first()
        if snapshot is None:return reply({'error':'cart_changed'},409)
        # A second key/tab for the same exact snapshot returns the existing request.
        old=QuotationRequest.objects.select_related('snapshot').filter(snapshot=snapshot).first()
        if old is not None:
            if old.cart_id!=cart.pk:return reply({'error':'not_found'},404)
            QuotationRequestKey.objects.create(cart=cart,request_id=request_id,quotation=old)
            return reply(quotation_json(old))
        if cart.version!=snapshot.version:return reply({'error':'cart_changed'},409)
        if snapshot.catalog_revision!=CATALOG['revision']:return reply({'error':'stale_catalog'},409)
        if not snapshot.lines or not evaluate_cart(snapshot.lines)['valid']:
            return reply({'error':'invalid_cart'},422)
        row=QuotationRequest.objects.create(cart=cart,snapshot=snapshot,request_id=request_id)
        QuotationRequestKey.objects.create(cart=cart,request_id=request_id,quotation=row)
    return reply(quotation_json(row),201)


@require_GET
def quotation_detail(request,identity):
    denied=local_customer(request)
    if denied is not None:
        denied['Cache-Control']='no-store'
        return denied
    if request.GET:return reply({'error':'unexpected_query'},400)
    row=with_review_status(QuotationRequest.objects.filter(pk=identity,cart__owner=request.user,snapshot__cart_id=F('cart_id'))).select_related('snapshot').first()
    if row is None:return reply({'error':'not_found'},404)
    return reply(quotation_json(row))
