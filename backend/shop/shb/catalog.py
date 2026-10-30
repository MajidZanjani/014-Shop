"""Per-order SHB calculations only; never a support balance or live approval."""
import hashlib
import json
from pathlib import Path
import re

CATALOG=json.loads(Path(__file__).with_name('revision.json').read_text())
MAX_QUANTITY=2**31-1
MAX_SAFE_MONEY=2**53-1


def require(value):
    if not value:raise ValueError('invalid_shb_value')


def canonical(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def synthetic_offer():
    """Deliberately artificial local test values, never selected for live use."""
    return {'revision':'synthetic-shb-offer-v1','evidence_class':'local-synthetic',
        'currency':'EUR','fpga_hourly_minor':10000,'asic_hourly_minor':20000,
        'tax_bps':0,'rounding':'half-up','bank_min_minor':1,'bank_max_minor':100000000,
        'terms_revision':'synthetic-shb-terms-v1','privacy_revision':'synthetic-shb-privacy-v1',
        'refund_revision':'synthetic-shb-refund-v1','asic_supplement_revision':'synthetic-shb-asic-v1',
        'manual_charging_policy_revision':'synthetic-manual-time-v1'}


def quote(variant,quantity,*,offer=None,discount_bps=0):
    require(type(quantity) is int and 1<=quantity<=MAX_QUANTITY)
    require(type(discount_bps) is int and 0<=discount_bps<10000)
    selected=next((v for v in CATALOG['variants'] if v['id']==variant),None)
    require(selected is not None)
    value={'product_id':CATALOG['product_id'],'catalog_revision':CATALOG['revision'],
        'variant_id':variant,'variant_label':selected['label'],
        'hours_per_bundle':selected['hours_per_bundle'],'quantity':quantity,
        'hours_purchased':quantity*selected['hours_per_bundle'],'workflow':selected['workflow'],
        'currency':None,'hourly_minor':None,'bundle_minor':None,'subtotal_minor':None,
        'discount_bps':0,'discount_minor':None,'tax_minor':None,'total_minor':None,
        'offer_revision':None,'live_payable':False,'evidence_class':'unapproved',
        'status':'price_to_be_confirmed'}
    if offer is None:
        require(discount_bps==0)
        return value
    # The live approved-offer selection/custody adapter is still pending. Only
    # this exact explicitly synthetic policy can currently price a local demo.
    require(type(offer) is dict and set(offer)==set(synthetic_offer()))
    require(offer['evidence_class']=='local-synthetic'
            and offer['revision']=='synthetic-shb-offer-v1'
            and offer['currency']=='EUR')
    for key in ('fpga_hourly_minor','asic_hourly_minor','bank_min_minor','bank_max_minor'):
        require(type(offer[key]) is int and 1<=offer[key]<=MAX_SAFE_MONEY)
    require(offer['asic_hourly_minor']>offer['fpga_hourly_minor']
            and offer['bank_max_minor']>=offer['bank_min_minor']
            and type(offer['tax_bps']) is int and 0<=offer['tax_bps']<=100000
            and offer['rounding']=='half-up')
    for key in ('terms_revision','privacy_revision','refund_revision','asic_supplement_revision','manual_charging_policy_revision'):
        require(type(offer[key]) is str and offer[key].startswith('synthetic-'))
    rate=offer['fpga_hourly_minor' if variant=='shb-fpga-10h' else 'asic_hourly_minor']
    bundle=rate*selected['hours_per_bundle'];subtotal=bundle*quantity
    require(subtotal<=MAX_SAFE_MONEY)
    discount=(subtotal*discount_bps+5000)//10000
    tax=((subtotal-discount)*offer['tax_bps']+5000)//10000
    total=subtotal-discount+tax
    require(offer['bank_min_minor']<=total<=offer['bank_max_minor'])
    return dict(value,currency=offer['currency'],hourly_minor=rate,bundle_minor=bundle,
        subtotal_minor=subtotal,discount_bps=discount_bps,discount_minor=discount,
        tax_minor=tax,total_minor=total,offer_revision=offer['revision'],
        evidence_class='local-synthetic',status='synthetic_estimate' if selected['workflow']=='request' else 'synthetic_review')
