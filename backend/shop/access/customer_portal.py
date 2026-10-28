"""Local captured verification forms sharing the JSON transport's operations."""
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.cache import patch_vary_headers
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_http_methods
from .views import local_enabled,verified_identity,start_verification,complete_verification,end_verification
from .recovery import recovery_held

PATH='/purchase/access/'
ERRORS={
    'access_recovery_pending':'Customer access is temporarily paused for recovery review.',
    'synthetic_email_required':'Enter a synthetic address ending in .invalid.',
    'verification_failed':'The code could not be verified. Request a new code if needed.',
    'request_limit':'Too many requests. Wait ten minutes before trying again.',
    'capture_unavailable':'Local verification is temporarily unavailable.',
    'invalid_request':'The request was rejected. Reload this page and try again.',
}
NOTICES={'request':'Code captured privately. Ask the local operator for the code.',
         'verify':'Customer access verified.', 'logout':'You have signed out.'}


def private(response):
    response['Cache-Control']='no-store'
    response['Referrer-Policy']='no-referrer'
    response['Content-Security-Policy']="default-src 'none'; style-src 'self'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'"
    patch_vary_headers(response,['Cookie'])
    return response


def form_action(request):
    if request.content_type!='application/x-www-form-urlencoded':raise ValueError('type')
    if int(request.META.get('CONTENT_LENGTH') or 0)>1024 or len(request.body)>1024:raise ValueError('size')
    data=request.POST
    if any(len(data.getlist(key))!=1 for key in data):raise ValueError('duplicate')
    action=data.get('action')
    fields={'request':{'action','email'},'verify':{'action','code'},'logout':{'action'}}
    if action not in fields or set(data)-{'csrfmiddlewaretoken'}!=fields[action]:raise ValueError('fields')
    return action,data


@require_http_methods(['GET','POST'])
@sensitive_post_parameters()
def customer_access(request):
    if not local_enabled():return private(HttpResponse('Unavailable',status=404))
    if recovery_held():return private(HttpResponse('Customer access is temporarily paused for recovery review.',status=503))
    if request.user.is_authenticated and (not request.user.is_active or request.user.is_staff or request.user.is_superuser):
        return private(HttpResponse('Unavailable',status=403))
    error=None;status=200
    if request.GET:
        error='invalid_request';status=400
    elif request.method=='POST':
        try:
            action,data=form_action(request)
            if action=='request':result,status=start_verification(request,data['email'])
            elif action=='verify':result,status=complete_verification(request,data['code'])
            else:result,status=end_verification(request)
            if status==200:
                request.session['customer_access_notice']=action
                response=HttpResponse(status=303);response['Location']=PATH
                return private(response)
            error=result.get('error','invalid_request')
        except (ValueError,UnicodeError):
            error='invalid_request';status=400
    notice=NOTICES.get(request.session.pop('customer_access_notice',None),'')
    return private(render(request,'access/customer_access.html',{
        'authenticated':verified_identity(request) is not None,
        'pending':bool(request.session.get('shop_challenge') and request.session.get('shop_verification_binding')),
        'notice':notice,'error':ERRORS.get(error,'')},status=status))
