"""Source-section8 partial drafts. Unknown country/tax applicability never becomes approval."""
from copy import deepcopy
import hashlib
import json
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from .rules import CATALOG

SCHEMA_VERSION=1
SOURCE_SHA256=CATALOG['source_sha256']
# Source groups225–249: address components are group7, separately for registered/billing.
GROUPS=[
 ('legal_business_name','Legal business / organisation name',['legal_business_name'],'Required for checkout'),
 ('trading_name','Trading name',['trading_name'],'Optional'),
 ('registration_number','Business registration number',['registration_number'],'Where applicable; entities without one are allowed'),
 ('registration_country','Country of registration / establishment',['registration_country'],'Required for checkout; approved choices pending'),
 ('registered_address','Registered business address',['registered_address'],'Required for checkout'),
 ('billing_address','Billing address',['billing_same_as_registered','billing_address'],'Required for checkout; helper copies address and components'),
 ('address_components','City, region and postcode',['registered_city','registered_region','registered_postcode','billing_city','billing_region','billing_postcode'],'Country-specific applicability pending'),
 ('tax_number','VAT / tax identification number',['tax_number'],'Where applicable; applicability pending'),
 ('tax_status','VAT / tax registration status',['tax_status'],'Required for checkout; location-appropriate choices pending'),
 ('purchasing_name','Purchasing contact name',['purchasing_name'],'Required for checkout'),
 ('business_email','Business email address',['business_email'],'Required for checkout; synthetic .invalid addresses only'),
 ('telephone','Telephone number',['telephone'],'Optional unless needed for fulfilment'),
 ('purchase_order','Purchase order reference',['purchase_order'],'Optional'),
 ('invoice_email','Accounts / invoice email',['invoice_email'],'Optional; defaults to purchasing contact email'),
 ('technical_contact','Technical / licence administrator name and email',['technical_same_as_purchasing','technical_name','technical_email'],'Name and email required for checkout'),
 ('licensed_entity','Licensed legal entity',['licensed_entity'],'Defaults to purchasing business; differences require review'),
 ('deployment_country','Deployment / end-use country',['deployment_country'],'Required for order review; approved choices pending'),
 ('application','Intended application',['application'],'Short non-confidential description; no design details'),
 ('notes','Additional order notes',['notes'],'Optional; no host IDs, credentials, identity documents or sensitive technical material'),
]
LIMITS={'legal_business_name':200,'trading_name':200,'registration_number':128,'registered_address':500,
        'billing_address':500,'registered_city':120,'registered_region':120,'registered_postcode':40,
        'billing_city':120,'billing_region':120,'billing_postcode':40,'tax_number':128,'purchasing_name':160,
        'business_email':160,'telephone':60,'purchase_order':120,'invoice_email':160,'technical_name':160,
        'technical_email':160,'licensed_entity':200,'application':300,'notes':500}
PENDING=('registration_country','tax_status','deployment_country')
HELPERS=('billing_same_as_registered','technical_same_as_purchasing')
MULTILINE={'registered_address','billing_address','notes'}

def empty_details():return {**{key:'' for key in LIMITS},**{key:None for key in PENDING},**{key:False for key in HELPERS}}


def validate_details(value):
    errors=[];clean=empty_details()
    if not isinstance(value,dict) or set(value)!=set(clean):return clean,['fields']
    for key,limit in LIMITS.items():
        item=value[key]
        if isinstance(item,str) and key in MULTILINE:item=item.replace('\r\n','\n')
        if (not isinstance(item,str) or len(item)>limit or any((ord(c)<32 and not (c=='\n' and key in MULTILINE)) or ord(c)==127 for c in item)):
            errors.append(key);continue
        item=item.strip()
        if key.endswith('email') and item:
            try:
                validate_email(item)
                if not item.lower().endswith('.invalid'):raise ValidationError('synthetic only')
            except ValidationError:errors.append(key);continue
        clean[key]=item
    for key in PENDING:
        if value[key] is not None:errors.append(key)
    for key in HELPERS:
        if type(value[key]) is not bool:errors.append(key)
        else:clean[key]=value[key]
    return clean,errors


def resolve_details(clean):
    value=deepcopy(clean)
    if value['billing_same_as_registered']:
        for suffix in ('address','city','region','postcode'):value['billing_'+suffix]=value['registered_'+suffix]
    if value['technical_same_as_purchasing']:
        value['technical_name']=value['purchasing_name'];value['technical_email']=value['business_email']
    if not value['invoice_email']:value['invoice_email']=value['business_email']
    if not value['licensed_entity']:value['licensed_entity']=value['legal_business_name']
    return value


def evaluate_details(value):
    required=['legal_business_name','registered_address','billing_address','purchasing_name','business_email','technical_name','technical_email',*PENDING]
    return {'state':'partial_draft','missing_required':[key for key in required if not value[key]],
            'pending':['country_choices','tax_status_choices','country_address_applicability','registration_tax_applicability','contact_roles','terms'],
            'licensed_entity_review_required':bool(value['licensed_entity'] and value['licensed_entity']!=value['legal_business_name']),
            'checkout_enabled':False,'acceptance_enabled':False}


def submission_digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()).hexdigest()
