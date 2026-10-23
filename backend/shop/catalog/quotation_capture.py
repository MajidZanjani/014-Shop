"""Deliberate local quote capture from the displayed saved cart; no commercial effects."""
import re
import uuid
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_http_methods
from .cart_editor import canonical_uuid,private
from .cart_views import reply
from .models import DraftCart,CartSnapshot
from .quotation_views import capture_quotation
from .rules import CATALOG
from .cart_rules import evaluate_cart
from .views import local_customer


def payload(request):
    if request.content_type!='application/x-www-form-urlencoded':raise ValueError('type')
    if int(request.META.get('CONTENT_LENGTH') or 0)>1024 or len(request.body)>1024:raise ValueError('size')
    data=request.POST
    if set(data)-{'csrfmiddlewaretoken'}!={'action','request_id','cart_id','version'}:raise ValueError('fields')
    if any(len(data.getlist(key))!=1 for key in data) or data['action']!='request':raise ValueError('fields')
    if re.fullmatch('[1-9][0-9]{0,9}',data['version']) is None or int(data['version'])>1000000000:raise ValueError('version')
    return {'request_id':str(canonical_uuid(data['request_id'])),'cart_id':str(canonical_uuid(data['cart_id'])),'version':int(data['version'])}


@require_http_methods(['GET','POST'])
@sensitive_post_parameters()
def quotation_capture(request):
    denied=local_customer(request)
    if denied is not None:return private(denied)
    error='';status=200
    if request.GET:
        error='The request was rejected. Reload without query parameters.';status=400
    elif request.method=='POST':
        try:
            result,status=capture_quotation(request.user,payload(request))
            if status in (200,201):
                response=HttpResponse(status=303)
                response['Location']='/purchase/quotation-timeline/'+result['id']+'/'
                return private(response)
            error={404:'The saved cart revision is unavailable.',409:'The cart or catalog changed. Reload and review the saved cart before requesting a quotation.',422:'Save a valid nonempty cart before requesting a quotation.'}.get(status,'The request was rejected.')
        except (ValueError,TypeError,UnicodeError):error='The request was rejected. Reload and try again.';status=400
    cart=DraftCart.objects.filter(owner=request.user).first()
    snapshot=CartSnapshot.objects.filter(cart=cart,cart__owner=request.user,version=cart.version).first() if cart and cart.version else None
    if cart and cart.version and snapshot is None:return private(reply({'error':'not_found'},404))
    eligible=bool(snapshot and snapshot.lines and snapshot.catalog_revision==CATALOG['revision'] and evaluate_cart(snapshot.lines)['valid'])
    return private(render(request,'catalog/quotation_capture.html',{
        'cart':cart,'snapshot':snapshot,'eligible':eligible,'request_id':str(uuid.uuid4()),'error':error},status=status))
