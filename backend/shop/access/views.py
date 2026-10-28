"""Local captured-email verification. No code-bearing URLs or public mailbox."""
from datetime import timedelta
import json
import re
import secrets
import uuid
from django.conf import settings
from django.contrib.auth import get_user_model,login,logout
from django.db import transaction
from django.http import JsonResponse
from django.middleware.csrf import get_token,rotate_token
from django.utils import timezone
from django.utils.crypto import constant_time_compare,salted_hmac
from django.views.decorators.http import require_GET,require_POST
from shop.adapters.capture_mail import CaptureMail
from shop.adapters.local_storage import LocalStorage
from shop.adapters.ports import MailRequest
from .models import CustomerIdentity,VerificationChallenge,VerificationThrottle
from .effects import local_effect,RecoveryEffectError

WINDOW=timedelta(minutes=10)
MAX_ATTEMPTS=5
MAX_REQUESTS=3

def local_enabled():
    return settings.SHOP_ENV in ('local','synthetic') and settings.MAIL_ADAPTER=='fake'

def reply(data,status=200):
    response=JsonResponse(data,status=status)
    response['Cache-Control']='no-store'
    response['Referrer-Policy']='no-referrer'
    if status==503 and data=={'error':'access_recovery_pending'}:
        response['X-Shop-Access-Recovery']='pending'
    return response

def digest(purpose,value):
    return salted_hmac('shop.local-verification.'+purpose,value,algorithm='sha256').hexdigest()

def read_json(request,fields):
    from shop.catalog.views import unique_object
    if request.content_type!='application/json': raise ValueError('content_type')
    if int(request.META.get('CONTENT_LENGTH') or 0)>1024: raise ValueError('size')
    raw=request.read(1025)
    if len(raw)>1024: raise ValueError('size')
    value=json.loads(raw,object_pairs_hook=unique_object)
    if not isinstance(value,dict) or set(value)!=set(fields): raise ValueError('fields')
    # Reject malformed text before credential hashing or authentication effects.
    for item in value.values():
        if isinstance(item,str):item.encode('utf-8')
    return value

def verified_identity(request):
    if not request.user.is_authenticated or not request.user.is_active or request.user.is_staff or request.user.is_superuser:
        return None
    from .recovery import current_session_epoch
    if not current_session_epoch(request):return None
    marker=request.session.get('shop_verified_identity')
    if not isinstance(marker,str): return None
    try: identity=uuid.UUID(marker)
    except ValueError:return None
    return CustomerIdentity.objects.filter(pk=identity,user=request.user).first()

@require_GET
def session_status(request):
    if not local_enabled(): return reply({'error':'unavailable'},404)
    from .recovery import recovery_held
    if recovery_held():return reply({'error':'access_recovery_pending'},503)
    return reply({'authenticated':verified_identity(request) is not None,'csrf_token':get_token(request)})

def start_verification(request,email):
    if not local_enabled(): return {'error':'unavailable'},404
    from .recovery import recovery_held
    if recovery_held():return {'error':'access_recovery_pending'},503
    try:return _start_verification_admitted(request,email)
    except RecoveryEffectError:return {'error':'access_recovery_pending'},503

@local_effect('customer-code',require_current_epoch=True)
def _start_verification_admitted(request,email):
    try:
        if not isinstance(email,str):raise ValueError('email')
        email=email.strip().lower()
        if len(email)>160 or re.fullmatch(r'[a-z0-9._+-]+@[a-z0-9-]+(?:\.[a-z0-9-]+)*\.invalid',email) is None:
            raise ValueError('synthetic_email')
    except (ValueError,UnicodeError,RecursionError):return {'error':'synthetic_email_required'},400
    capture_root=getattr(settings,'LOCAL_CAPTURE_ROOT',None)
    if not capture_root:return {'error':'capture_unavailable'},503
    # Validate private storage before reserving a challenge or mutating the session.
    try:
        with LocalStorage(capture_root):pass
    except (OSError,ValueError):return {'error':'capture_unavailable'},503
    now=timezone.now()
    # Each session can request at most three challenges per window, even when
    # the submitted email changes. Email limits span sessions and IP addresses.
    session_window=request.session.get('shop_request_window',0)
    count=request.session.get('shop_request_count',0)
    if now.timestamp()-session_window<WINDOW.total_seconds() and count>=MAX_REQUESTS:
        return {'error':'request_limit'},429
    if now.timestamp()-session_window>=WINDOW.total_seconds():count=0;session_window=now.timestamp()
    with transaction.atomic():
        throttle,_=VerificationThrottle.objects.get_or_create(email_digest=digest('email',email),defaults={'window_start':now})
        throttle=VerificationThrottle.objects.select_for_update().get(pk=throttle.pk)
        if now-throttle.window_start>=WINDOW:throttle.window_start=now;throttle.requests=0
        if throttle.requests>=MAX_REQUESTS:return {'error':'request_limit'},429
        throttle.requests+=1;throttle.save(update_fields=['requests','window_start'])
        binding=secrets.token_urlsafe(32)
        code=secrets.token_urlsafe(24)
        challenge=VerificationChallenge.objects.create(email=email,code_digest=digest('code',code),binding_digest=digest('binding',binding),expires_at=now+WINDOW)
        body=('Local synthetic verification only.\nTo: '+email+'\nVerification code: '+code+'\nValid for ten minutes, one deliberate POST, in the requesting browser only.\n').encode()
        message=MailRequest(challenge.id,email,body)
        try:
            CaptureMail().send(message)
            with LocalStorage(capture_root) as store:store.put(message.body)
        except (OSError,ValueError):
            transaction.set_rollback(True)
            return {'error':'capture_unavailable'},503
    request.session['shop_request_window']=session_window
    request.session['shop_request_count']=count+1
    request.session['shop_challenge']=str(challenge.id)
    request.session['shop_verification_binding']=binding
    request.session.set_expiry(1800)
    return {'status':'code_captured','expires_in_seconds':600},200

def complete_verification(request,code):
    if not local_enabled():return {'error':'unavailable'},404
    from .recovery import recovery_held
    if recovery_held():return {'error':'access_recovery_pending'},503
    try:return _complete_verification_admitted(request,code)
    except RecoveryEffectError:return {'error':'access_recovery_pending'},503

@local_effect('customer-verify',require_current_epoch=True)
def _complete_verification_admitted(request,code):
    try:
        if not isinstance(code,str) or not 1<=len(code)<=128:raise ValueError('code')
        identity=uuid.UUID(request.session.get('shop_challenge',''))
        binding=request.session.get('shop_verification_binding','')
        if not isinstance(binding,str) or not binding:raise ValueError('binding')
    except (ValueError,TypeError,UnicodeError,RecursionError):return {'error':'verification_failed'},400
    with transaction.atomic():
        challenge=VerificationChallenge.objects.select_for_update().filter(pk=identity).first()
        now=timezone.now()
        if (challenge is None or challenge.consumed_at is not None or challenge.expires_at<=now or challenge.attempts>=MAX_ATTEMPTS
            or not constant_time_compare(challenge.binding_digest,digest('binding',binding))):
            return {'error':'verification_failed'},400
        challenge.attempts+=1
        if not constant_time_compare(challenge.code_digest,digest('code',code)):
            challenge.save(update_fields=['attempts'])
            return {'error':'verification_failed'},400
        # Arbitrate same-email identity creation across independent challenges.
        VerificationThrottle.objects.select_for_update().get(pk=digest('email',challenge.email))
        customer=CustomerIdentity.objects.filter(email=challenge.email).select_related('user').first()
        if customer is None:
            user=get_user_model().objects.create_user(username='customer-'+uuid.uuid4().hex,email=challenge.email)
            customer=CustomerIdentity.objects.create(user=user,email=challenge.email,verified_at=now)
        if not customer.user.is_active or customer.user.is_staff or customer.user.is_superuser:
            return {'error':'verification_failed'},400
        challenge.consumed_at=now;challenge.save(update_fields=['attempts','consumed_at'])
    # A lost response cannot replay the consumed credential. Always rotate both
    # the session identity and CSRF token, including same-user re-verification.
    request.session.cycle_key()
    login(request,customer.user,backend='django.contrib.auth.backends.ModelBackend')
    for key in ('shop_challenge','shop_verification_binding'):request.session.pop(key,None)
    request.session['shop_verified_identity']=str(customer.id)
    request.session.set_expiry(1800)
    return {'authenticated':True,'csrf_token':get_token(request)},200

def end_verification(request):
    if not local_enabled():return {'error':'unavailable'},404
    logout(request);rotate_token(request)
    return {'authenticated':False,'csrf_token':get_token(request)},200


@require_POST
def request_code(request):
    if not local_enabled():return reply({'error':'unavailable'},404)
    try:email=read_json(request,{'email'})['email']
    except (ValueError,UnicodeError,RecursionError):return reply({'error':'synthetic_email_required'},400)
    return reply(*start_verification(request,email))

@require_POST
def verify_code(request):
    if not local_enabled():return reply({'error':'unavailable'},404)
    try:code=read_json(request,{'code'})['code']
    except (ValueError,TypeError,UnicodeError,RecursionError):return reply({'error':'verification_failed'},400)
    return reply(*complete_verification(request,code))

@require_POST
def sign_out(request):
    return reply(*end_verification(request))
