"""Internal private prepared-request bytes. No route, offer, acceptance or outbox."""
import json
import re
import uuid
from datetime import datetime,timedelta
from django.conf import settings
from django.db import transaction
from django.db.models import F
from shop.access.models import StaffCredential,StaffQuotationGrant
from shop.access.staff_auth import staff_credential
from shop.access.views import verified_identity
from .models import QuotationRequest
from .business_scope import scope_for_version,valid_business
from . import business_rules
from .cart_rules import evaluate_cart
from .rules import CATALOG

MAX_BYTES=131072
FLAGS={'offer_enabled':False,'acceptance_enabled':False,'checkout_enabled':False,'effects_authorized':False}
COMMERCIAL={key:None for key in ('offer','prices','tax','terms','quote_valid_until','payment_start_deadline','bank_session_expiry')}

class EnvelopeError(ValueError):pass


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode('utf-8')


def identity(quotation_id,business_version):
    return uuid.uuid5(uuid.NAMESPACE_URL,'urn:sll:xspi:local-request-envelope:v1:'+str(quotation_id)+':business:'+str(business_version))


def keys(value,expected):
    if not isinstance(value,dict) or set(value)!=set(expected):raise ValueError('fields')


def positive(value):
    if type(value) is not int or not 1<=value<=1000000000:raise ValueError('integer')


def uid(value):
    if not isinstance(value,str) or str(uuid.UUID(value))!=value:raise ValueError('uuid')


def stamp(value):
    if not isinstance(value,str):raise ValueError('timestamp')
    parsed=datetime.fromisoformat(value)
    if parsed.utcoffset()!=timedelta(0) or parsed.isoformat()!=value:raise ValueError('timestamp')


def validate_envelope(raw):
    """Validate known-source bytes; unavailable historical schemas stay held, not rewritten."""
    try:
        if type(raw) is not bytes or not 1<=len(raw)<=MAX_BYTES:raise ValueError('size')
        value=json.loads(raw,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('constant')))
        if canonical(value)!=raw:raise ValueError('canonical')
        keys(value,{'schema','kind','evidence_class','envelope_id','source','request','cart','business_scope','commercial','gates'})
        if type(value['schema']) is not int or value['schema']!=1 or value['kind']!='quotation-request-prepared' or value['evidence_class']!='local-synthetic':raise ValueError('kind')
        if canonical(value['commercial'])!=canonical(COMMERCIAL) or canonical(value['gates'])!=canonical(FLAGS):raise ValueError('effects')
        source={key:CATALOG[key] for key in ('revision','source_sha256','product_id','profile_id')}
        if value['source']!=source:raise EnvelopeError('envelope_source_unavailable')
        request=value['request'];cart=value['cart'];scope=value['business_scope']
        keys(request,{'id','request_id','owner_id','created_at','business_version'})
        uid(request['id']);uid(request['request_id']);positive(request['owner_id']);stamp(request['created_at'])
        version=request['business_version']
        if type(version) is not int or not 0<=version<=1000000000:raise ValueError('version')
        if value['envelope_id']!=str(identity(request['id'],version)):raise ValueError('identity')
        keys(cart,{'id','snapshot_id','request_id','version','created_at','catalog_revision','lines','evaluation'})
        uid(cart['id']);uid(cart['request_id']);positive(cart['snapshot_id']);positive(cart['version']);stamp(cart['created_at'])
        if cart['catalog_revision']!=source['revision'] or not cart['lines']:raise ValueError('catalog')
        evaluated=evaluate_cart(cart['lines'])
        if not evaluated['valid'] or canonical(cart['evaluation'])!=canonical(evaluated):raise ValueError('cart')
        if not version:
            if scope is not None:raise ValueError('scope')
        else:
            keys(scope,{'id','version','created_at','snapshot'})
            positive(scope['id']);stamp(scope['created_at'])
            if type(scope['version']) is not int or scope['version']!=version:raise ValueError('scope')
            business=scope['snapshot']
            keys(business,{'id','draft_id','owner_id','request_id','version','created_at','schema_version','source_sha256','submission_digest','details','evaluation'})
            for key in ('id','draft_id','owner_id','version'):positive(business[key])
            uid(business['request_id']);stamp(business['created_at'])
            if business['owner_id']!=request['owner_id'] or type(business['schema_version']) is not int or business['schema_version']!=business_rules.SCHEMA_VERSION or business['source_sha256']!=business_rules.SOURCE_SHA256:raise ValueError('source')
            if not isinstance(business['submission_digest'],str) or re.fullmatch('[0-9a-f]{64}',business['submission_digest']) is None:raise ValueError('digest')
            clean,errors=business_rules.validate_details(business['details'])
            if errors or canonical(business['details'])!=canonical(business_rules.resolve_details(clean)) or canonical(business['evaluation'])!=canonical(business_rules.evaluate_details(business['details'])):raise ValueError('business')
        return value
    except EnvelopeError:raise
    except (ValueError,TypeError,KeyError,AttributeError,OverflowError,RecursionError,UnicodeError):
        raise EnvelopeError('invalid_envelope') from None


def prepare_request_envelope(request,quotation_id,business_version):
    """Authorize exact scope and freeze read bytes under parent locks; never publish here."""
    if settings.SHOP_ENV not in ('local','synthetic') or settings.STORAGE_ADAPTER!='fake':raise EnvelopeError('envelope_unavailable')
    if type(quotation_id) is not uuid.UUID or type(business_version) is not int or not 0<=business_version<=1000000000:raise EnvelopeError('envelope_unavailable')
    privileged=request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser)
    with transaction.atomic():
        if privileged:
            admitted=staff_credential(request,recent=True)
            if admitted is None:raise EnvelopeError('envelope_unavailable')
            credential=StaffCredential.objects.select_for_update().filter(pk=admitted.pk,enabled=True,generation=admitted.generation,user__is_active=True,user__is_staff=True).first()
            if credential is None or staff_credential(request,recent=True) is None:raise EnvelopeError('envelope_unavailable')
        elif verified_identity(request) is None:raise EnvelopeError('envelope_unavailable')
        rows=QuotationRequest.objects.select_related('cart','snapshot').select_for_update(of=('self','cart')).filter(pk=quotation_id,snapshot__cart_id=F('cart_id'))
        if not privileged:rows=rows.filter(cart__owner=request.user)
        quotation=rows.first()
        if quotation is None or business_version>quotation.business_version:raise EnvelopeError('envelope_unavailable')
        if privileged:
            grant=StaffQuotationGrant.objects.filter(user=request.user,quotation=quotation).first()
            if grant is None or (business_version and grant.business_scope_version!=business_version):raise EnvelopeError('envelope_unavailable')
        return source_bytes(quotation,business_version)


def source_bytes(quotation,business_version):
    """Internal shared reconstruction; caller must hold quotation/cart locks."""
    from django.db import connection
    if not connection.in_atomic_block:raise EnvelopeError("source_transaction_required")
    scope=scope_for_version(quotation,business_version)
    if business_version and (scope is None or not valid_business(scope.business_snapshot,quotation.cart.owner_id)):raise EnvelopeError('envelope_unavailable')
    snapshot=quotation.snapshot
    evaluated=evaluate_cart(snapshot.lines)
    if snapshot.catalog_revision!=CATALOG['revision']:raise EnvelopeError('envelope_source_unavailable')
    if not evaluated['valid'] or not snapshot.lines:raise EnvelopeError('invalid_envelope')
    try:
        if canonical(snapshot.evaluation)!=canonical(evaluated):raise EnvelopeError('invalid_envelope')
    except (ValueError,TypeError,RecursionError,UnicodeError):raise EnvelopeError('invalid_envelope') from None
    value={'schema':1,'kind':'quotation-request-prepared','evidence_class':'local-synthetic',
        'envelope_id':str(identity(quotation.pk,business_version)),
        'source':{key:CATALOG[key] for key in ('revision','source_sha256','product_id','profile_id')},
        'request':{'id':str(quotation.pk),'request_id':str(quotation.request_id),'owner_id':quotation.cart.owner_id,'created_at':quotation.created_at.isoformat(),'business_version':business_version},
        'cart':{'id':str(quotation.cart_id),'snapshot_id':snapshot.pk,'request_id':str(snapshot.request_id),'version':snapshot.version,'created_at':snapshot.created_at.isoformat(),'catalog_revision':snapshot.catalog_revision,'lines':snapshot.lines,'evaluation':snapshot.evaluation},
        'business_scope':None,'commercial':dict(COMMERCIAL),'gates':dict(FLAGS)}
    if scope:
        business=scope.business_snapshot
        value['business_scope']={'id':scope.pk,'version':scope.version,'created_at':scope.created_at.isoformat(),
            'snapshot':{'id':business.pk,'draft_id':business.draft_id,'owner_id':business.draft.owner_id,'request_id':str(business.request_id),'version':business.version,'created_at':business.created_at.isoformat(),
                'schema_version':business.schema_version,'source_sha256':business.source_sha256,'submission_digest':business.submission_digest,'details':business.details,'evaluation':business.evaluation}}
    try:raw=canonical(value)
    except (ValueError,TypeError,RecursionError,UnicodeError):raise EnvelopeError('invalid_envelope') from None
    validate_envelope(raw)
    return raw



def recover_request_envelope(request,quotation_id,business_version,receipt,archive):
    """Read private bytes only after exact authorization, then reauthorize after I/O."""
    import hashlib
    from django.db import connection
    from shop.adapters.evidence_archive import PreparedReceipt,ArchiveError,manifest
    if connection.in_atomic_block:raise EnvelopeError('archive_transaction_active')
    expected=prepare_request_envelope(request,quotation_id,business_version)
    reference=PreparedReceipt(identity(quotation_id,business_version),hashlib.sha256(expected).hexdigest(),len(expected))
    try:
        manifest(receipt)
        if receipt!=reference:raise EnvelopeError('envelope_unavailable')
        raw=archive.recover(receipt)
    except ArchiveError:raise EnvelopeError('envelope_unavailable') from None
    # Revocation, ownership/source changes or altered retained data during I/O
    # cannot return bytes under the earlier authorization decision.
    current=prepare_request_envelope(request,quotation_id,business_version)
    if current!=expected or raw!=expected:raise EnvelopeError('envelope_unavailable')
    return raw
