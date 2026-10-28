"""Synthetic two-factor rehearsal; not an approved production MFA transport."""
from datetime import timedelta
from base64 import b64encode
from hashlib import sha256
import secrets
import uuid
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.db import transaction
from django.http import HttpResponseRedirect
from django.middleware.csrf import get_token, rotate_token
from django.template.response import TemplateResponse
from django.utils import timezone
from django.utils.crypto import constant_time_compare
from django.utils.functional import SimpleLazyObject
from django.views.decorators.http import require_GET, require_POST
from shop.adapters.local_storage import LocalStorage
from shop.catalog.presentation import CSS
from .models import StaffCredential, StaffLoginThrottle, StaffChallenge
from .views import digest, reply, read_json
from .recovery import current_session_epoch,recovery_held
from .effects import local_effect,RecoveryEffectError

LIFETIME=900
RECENT=300
MAX_ATTEMPTS=5
# Fixed reviewed CSS only: no pre-MFA asset exception or dynamic user content.
STYLE_HASH=b64encode(sha256(CSS.encode('utf-8')).digest()).decode('ascii')
ERRORS={
    'access_recovery_pending':'Staff access is temporarily paused for recovery review.',
    'unexpected_query':'The request was rejected. Return to staff sign-in and try again.',
    'invalid_request':'The request was rejected. Check the sign-in fields and try again.',
    'login_failed':'Sign-in failed. Check the username and password.',
    'login_limit':'Too many sign-in attempts. Wait ten minutes before trying again.',
    'capture_unavailable':'Local possession-code capture is temporarily unavailable. Try signing in again later.',
    'verification_failed':'The code could not be verified. Try the current code or sign in again for a new one.',
}


def staff_page(request,*,authenticated=False,error=None,status=200):
    # Defer session/template evaluation until after an auth transaction exits,
    # including a capture failure marked for rollback. No submitted values enter context.
    response=TemplateResponse(request,'access/staff.html',{'authenticated':authenticated,
        'challenge':SimpleLazyObject(lambda:bool(request.session.get('shop_staff_challenge'))),
        'staff_style':CSS,'error':ERRORS.get(error,'')},status=status)
    response['Cache-Control']='no-store';response['Referrer-Policy']='no-referrer'
    response['Content-Security-Policy']=f"default-src 'none'; style-src 'sha256-{STYLE_HASH}'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'"
    return response


def failure(request,error,status):
    if request.content_type=='application/x-www-form-urlencoded':
        return staff_page(request,error=error,status=status)
    return reply({'error':error},status)



def enabled(request):
    return (settings.SHOP_ENV in ('local','synthetic') and getattr(settings,'LOCAL_STAFF_ENABLED',False)
            and request.get_host().split(':')[0]=='staff.localhost')


def staff_credential(request, recent=False):
    if not enabled(request) or not request.user.is_authenticated or not request.user.is_active or not request.user.is_staff:
        return None
    if not current_session_epoch(request):return None
    marker=request.session.get('shop_staff_mfa')
    if not isinstance(marker,dict) or set(marker)!={'generation','verified_at'}:return None
    stamp=marker['verified_at']
    if type(stamp) not in (int,float):return None
    age=timezone.now().timestamp()-stamp
    if not 0<=age<=(RECENT if recent else LIFETIME):return None
    try:generation=uuid.UUID(marker['generation'])
    except (ValueError,TypeError,AttributeError):return None
    return StaffCredential.objects.filter(user=request.user,enabled=True,generation=generation).first()


def payload(request,fields):
    if request.content_type=='application/json':return read_json(request,fields)
    if request.content_type!='application/x-www-form-urlencoded':raise ValueError('content_type')
    if int(request.META.get('CONTENT_LENGTH') or 0)>1024:raise ValueError('size')
    value=request.POST
    if set(value)-{'csrfmiddlewaretoken'}!=set(fields) or any(len(value.getlist(k))!=1 for k in value):raise ValueError('fields')
    return {key:value[key] for key in fields}


def success(request,data):
    if request.content_type=='application/json':return reply(data)
    response=HttpResponseRedirect('/staff/');response['Cache-Control']='no-store';return response


@require_GET
def session_status(request):
    if not enabled(request):return reply({'error':'unavailable'},404)
    if recovery_held():return reply({'error':'access_recovery_pending'},503)
    return reply({'authenticated':staff_credential(request) is not None,'csrf_token':get_token(request)})


@require_POST
def password_login(request):
    if not enabled(request):return reply({'error':'unavailable'},404)
    if recovery_held():return failure(request,'access_recovery_pending',503)
    if request.GET:return failure(request,'unexpected_query',400)
    try:
        value=payload(request,{'username','password'})
        if any(not isinstance(value[k],str) or not 1<=len(value[k])<=150 for k in value):raise ValueError('input')
    except (ValueError,TypeError,UnicodeError,RecursionError):return failure(request,'invalid_request',400)
    try:return _password_login_admitted(request,value)
    except RecoveryEffectError:return failure(request,'access_recovery_pending',503)


@local_effect('staff-password',require_current_epoch=True)
def _password_login_admitted(request,value):
    now=timezone.now()
    with transaction.atomic():
        throttle,_=StaffLoginThrottle.objects.get_or_create(identity_digest=digest('staff-login',value['username']),defaults={'window_start':now})
        throttle=StaffLoginThrottle.objects.select_for_update().get(pk=throttle.pk)
        if now-throttle.window_start>=timedelta(minutes=10):throttle.window_start=now;throttle.attempts=0
        if throttle.attempts>=MAX_ATTEMPTS:return failure(request,'login_limit',429)
        throttle.attempts+=1;throttle.save(update_fields=['attempts','window_start'])
        user=authenticate(request,username=value['username'],password=value['password'])
        credential=StaffCredential.objects.select_for_update().filter(user=user,enabled=True).first() if user and user.is_active and user.is_staff else None
        if credential is None:return failure(request,'login_failed',400)
        root=getattr(settings,'LOCAL_STAFF_CAPTURE_ROOT',None)
        if not root:return failure(request,'capture_unavailable',503)
        code=secrets.token_urlsafe(24);binding=secrets.token_urlsafe(32)
        challenge=StaffChallenge.objects.create(credential=credential,generation=credential.generation,
            code_digest=digest('staff-code',code),binding_digest=digest('staff-binding',binding),expires_at=now+timedelta(minutes=5))
        try:
            with LocalStorage(root) as store:store.put(('Synthetic staff possession challenge only.\nUsername: '+user.username+'\nCode: '+code+'\n').encode())
        except (OSError,ValueError):
            transaction.set_rollback(True);return failure(request,'capture_unavailable',503)
    # Password alone never authenticates a privileged session.
    logout(request);rotate_token(request)
    request.session['shop_staff_challenge']=str(challenge.id)
    request.session['shop_staff_binding']=binding
    request.session.set_expiry(300)
    return success(request,{'status':'code_captured','expires_in_seconds':300,'csrf_token':get_token(request)})


@require_POST
def verify(request):
    if not enabled(request):return reply({'error':'unavailable'},404)
    if recovery_held():return failure(request,'access_recovery_pending',503)
    if request.GET:return failure(request,'unexpected_query',400)
    try:
        value=payload(request,{'code'});code=value['code']
        if not isinstance(code,str) or not 1<=len(code)<=128:raise ValueError('code')
        identity=uuid.UUID(request.session.get('shop_staff_challenge',''))
        binding=request.session.get('shop_staff_binding')
        if not isinstance(binding,str) or not binding:raise ValueError('binding')
    except (ValueError,TypeError,UnicodeError,RecursionError):return failure(request,'verification_failed',400)
    try:return _verify_admitted(request,code,identity,binding)
    except RecoveryEffectError:return failure(request,'access_recovery_pending',503)


@local_effect('staff-verify',require_current_epoch=True)
def _verify_admitted(request,code,identity,binding):
    with transaction.atomic():
        # Lock credential first, matching local operator reset/revocation.
        candidate=StaffChallenge.objects.filter(pk=identity).first()
        if candidate is None:return failure(request,'verification_failed',400)
        credential=StaffCredential.objects.select_for_update().select_related('user').get(pk=candidate.credential_id)
        challenge=StaffChallenge.objects.select_for_update().get(pk=identity)
        now=timezone.now()
        if (not credential.enabled or not credential.user.is_active or not credential.user.is_staff
            or challenge.generation!=credential.generation or challenge.consumed_at is not None
            or challenge.expires_at<=now or challenge.attempts>=MAX_ATTEMPTS
            or not constant_time_compare(challenge.binding_digest,digest('staff-binding',binding))):
            return failure(request,'verification_failed',400)
        challenge.attempts+=1
        if not constant_time_compare(challenge.code_digest,digest('staff-code',code)):
            challenge.save(update_fields=['attempts']);return failure(request,'verification_failed',400)
        challenge.consumed_at=now;challenge.save(update_fields=['attempts','consumed_at'])
        request.session.cycle_key()
        login(request,credential.user,backend='django.contrib.auth.backends.ModelBackend')
        request.session['shop_staff_mfa']={'generation':str(credential.generation),'verified_at':now.timestamp()}
        for key in ('shop_staff_challenge','shop_staff_binding','shop_verified_identity'):request.session.pop(key,None)
        request.session.set_expiry(LIFETIME)
    return success(request,{'authenticated':True,'csrf_token':get_token(request)})


@require_POST
def sign_out(request):
    if not enabled(request):return reply({'error':'unavailable'},404)
    logout(request);rotate_token(request)
    return success(request,{'authenticated':False,'csrf_token':get_token(request)})


@require_GET
def home(request):
    if not enabled(request):return reply({'error':'unavailable'},404)
    if recovery_held():return staff_page(request,error='access_recovery_pending',status=503)
    return staff_page(request,authenticated=staff_credential(request) is not None)
