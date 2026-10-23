"""Local no-JavaScript cart commands over retained owner revisions."""
import copy
import re
import uuid
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_http_methods
from .cart_views import store_cart,snapshot_json,reply
from .models import DraftCart,CartSnapshot
from .rules import CATALOG
from .simple import ConfigurationForm
from .views import local_customer

PATH='/purchase/cart/'

class IPForm(ConfigurationForm):
    support_packages=None


def canonical_uuid(raw):
    value=uuid.UUID(raw)
    if str(value)!=raw:raise ValueError('uuid')
    return value


def command(request):
    if request.content_type!='application/x-www-form-urlencoded':raise ValueError('type')
    if int(request.META.get('CONTENT_LENGTH') or 0)>8192 or len(request.body)>8192:raise ValueError('size')
    data=request.POST
    action=data.get('action')
    common={'action','request_id','expected_version','catalog_revision','line_id'}
    ip_fields=set(IPForm.base_fields)
    extra={'add_ip':ip_fields,'save_ip':ip_fields,'add_support':{'quantity'},'save_support':{'quantity'},'remove':set()}
    if action not in extra or set(data)-{'csrfmiddlewaretoken'}!=common|extra[action]:raise ValueError('fields')
    for key in data:
        if key!='families' and len(data.getlist(key))!=1:raise ValueError('duplicate')
    line_id=str(canonical_uuid(data['line_id']));request_id=str(canonical_uuid(data['request_id']))
    raw=data['expected_version']
    if re.fullmatch(r'0|[1-9][0-9]{0,9}',raw) is None or int(raw)>1000000000:raise ValueError('version')
    version=int(raw)
    revision=data['catalog_revision']
    if re.fullmatch('[0-9a-f]{64}',revision) is None:raise ValueError('revision')
    cart=DraftCart.objects.filter(owner=request.user).first()
    base=CartSnapshot.objects.filter(cart=cart,cart__owner=request.user,version=version).first() if cart and version else None
    if version and base is None:return None,404
    lines=copy.deepcopy(base.lines if base else [])
    index=next((n for n,line in enumerate(lines) if line['id']==line_id),None)
    if action in ('save_ip','save_support','remove') and index is None:return None,404
    if action in ('add_ip','add_support') and index is not None:raise ValueError('duplicate_line')
    if action=='remove':lines.pop(index)
    elif action in ('add_ip','save_ip'):
        # Pass only configuration fields to the shared form, excluding command metadata.
        values=data.copy()
        for key in list(values):
            if key not in ip_fields:values.pop(key)
        form=IPForm(values)
        if not form.is_valid():return None,422
        config=dict(form.cleaned_data,product_id=CATALOG['product_id'],profile_id=CATALOG['profile_id'],quantity=1,support_packages=0)
        config['production_band']=config['production_band'] or None
        line={'id':line_id,'kind':'ip','product_id':CATALOG['product_id'],'quantity':1,'configuration':config}
        if action=='save_ip':
            if lines[index]['kind']!='ip':return None,404
            lines[index]=line
        else:lines.append(line)
    else:
        raw=data['quantity']
        if re.fullmatch('[1-9][0-9]{0,6}',raw) is None or int(raw)>1000000:return None,422
        line={'id':line_id,'kind':'support','product_id':CATALOG['support_product_id'],'quantity':int(raw)}
        if action=='save_support':
            if lines[index]['kind']!='support':return None,404
            lines[index]=line
        else:lines.append(line)
    return {'request_id':request_id,'expected_version':version,'catalog_revision':revision,'lines':lines},200


def private(response):
    response['Cache-Control']='no-store';response['Referrer-Policy']='no-referrer';response['Vary']='Cookie'
    response['Content-Security-Policy']="default-src 'none'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'"
    return response


@require_http_methods(['GET','POST'])
@sensitive_post_parameters()
def cart_editor(request):
    denied=local_customer(request)
    if denied is not None:return private(denied)
    error='';status=200
    if request.method=='POST':
        if request.GET:return private(reply({'error':'unexpected_query'},400))
        try:
            value,status=command(request)
            if value is not None:result,status=store_cart(request.user,value)
            if status in (200,201):
                request.session['cart_saved_notice']={'version':result['version'],'replayed':status==200}
                response=HttpResponse(status=303);response['Location']=PATH
                return private(response)
            error={404:'The saved line or cart revision is unavailable.',409:'The cart or catalog changed. Reload and review before submitting a new change.',422:'Check the configuration, support quantity and cart limits.'}.get(status,'The request was rejected.')
        except (ValueError,TypeError,UnicodeError):error='The request was rejected. Reload this page and try again.';status=400
    cart=DraftCart.objects.filter(owner=request.user).first()
    snapshot=CartSnapshot.objects.filter(cart=cart,cart__owner=request.user,version=cart.version).first() if cart and cart.version else None
    if cart and cart.version and snapshot is None:return private(reply({'error':'not_found'},404))
    value=snapshot_json(cart,snapshot)
    edit=None
    if request.method=='GET' and request.GET:
        try:
            if set(request.GET)!={'edit'} or len(request.GET.getlist('edit'))!=1:raise ValueError('query')
            target=str(canonical_uuid(request.GET['edit']))
        except ValueError:return private(reply({'error':'invalid_request'},400))
        edit=next((line for line in value['lines'] if line['id']==target),None)
        if edit is None:return private(reply({'error':'not_found'},404))
    items=[dict(line,remove_id=str(uuid.uuid4()),save_id=str(uuid.uuid4())) for line in value['lines']]
    saved=request.session.pop('cart_saved_notice',None)
    if (not isinstance(saved,dict) or set(saved)!={'version','replayed'}
        or type(saved['version']) is not int or not 1<=saved['version']<=1000000000
        or type(saved['replayed']) is not bool):saved=None
    response=render(request,'catalog/cart_editor.html',{
        'cart':value,'items':items,'ip_form':IPForm(initial=edit['configuration'] if edit and edit['kind']=='ip' else None),
        'ip_action':'save_ip' if edit and edit['kind']=='ip' else 'add_ip',
        'ip_line_id':edit['id'] if edit and edit['kind']=='ip' else str(uuid.uuid4()),
        'ip_request_id':str(uuid.uuid4()),'support_request_id':str(uuid.uuid4()),'support_line_id':str(uuid.uuid4()),
        'revision':CATALOG['revision'],'error':error,'saved':saved},status=status)
    return private(response)
