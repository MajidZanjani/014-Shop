"""Public configuration validation only. Never accepts host identifiers or prices."""
import json
from pathlib import Path
CATALOG = json.loads(Path(__file__).with_name('revision.json').read_text())
KEYS = {'product_id','profile_id','quantity','vendor','families','term','production_band','production_units','fixed_nodes','floating_nodes','support_packages'}
MAX_COUNT = 1000000 # parser/resource bound, not an approved commercial entitlement

def integer(value):
    return type(value) is int or (type(value) is float and value.is_integer())

def evaluate(value,*,kit_catalog=None):
    errors = []
    def error(field, code): errors.append({'field':field,'code':code})
    if not isinstance(value, dict) or set(value) not in (KEYS,KEYS|{'platform'}):
        error('configuration','fields'); value = {}
    else:
        if value['product_id'] != CATALOG['product_id']: error('product_id','invalid')
        if value['profile_id'] != CATALOG['profile_id']: error('profile_id','invalid')
        if not integer(value['quantity']) or value['quantity'] != 1: error('quantity','one_per_line')
        vendor = next((v for v in CATALOG['vendors'] if v['id'] == value['vendor']), None)
        if vendor is None: error('vendor','required')
        families = value['families']
        allowed = [f['id'] for f in vendor['families']] if vendor else []
        if not isinstance(families,list) or not 1 <= len(families) <= 13 or any(not isinstance(f,str) or f not in allowed for f in families) or len(set(f for f in families if isinstance(f,str))) != len(families):
            error('families','vendor_families')
        term = next((t for t in CATALOG['terms'] if t['id'] == value['term']),None)
        if term is None or value['vendor'] not in term['vendors']: error('term','vendor_term')
        if value['term'] == 'rdp-yearly':
            band = next((b for b in CATALOG['production_bands'] if b['id'] == value['production_band']),None)
            if band is None: error('production_band','required')
            units = value['production_units']
            if units is not None:
                if not integer(units) or not 1 <= units <= MAX_COUNT: error('production_units','positive_integer')
                elif band and not (band['minimum'] <= units and (band['maximum'] is None or units <= band['maximum'])): error('production_units','band_mismatch')
        elif value['production_band'] is not None or value['production_units'] is not None:
            error('production_band','not_applicable')
        for field in ('fixed_nodes','floating_nodes','support_packages'):
            if not integer(value[field]) or not 0 <= value[field] <= MAX_COUNT: error(field,'nonnegative_integer')
        if all(integer(value[f]) and 0 <= value[f] <= MAX_COUNT for f in ('fixed_nodes','floating_nodes')):
            if value['vendor'] == 'altera':
                if value['fixed_nodes'] + value['floating_nodes'] == 0: error('access','required')
            elif value['fixed_nodes'] or value['floating_nodes']: error('access','not_applicable')
    if 'platform' in value:
        platform=value['platform']
        if not isinstance(platform,dict) or set(platform)!={'choice','kit_id','name'}:
            error('platform','fields')
        elif platform['choice'] not in CATALOG['purchase_flow']['platform_choices']:
            error('platform','choice')
        elif platform['choice']=='listed-kit':
            if (not isinstance(platform['kit_id'],str) or platform['name'] is not None
                or not any(kit['id']==platform['kit_id'] for kit in (CATALOG['purchase_flow']['ready_kits'] if kit_catalog is None else kit_catalog))):
                error('platform','kit')
        elif platform['kit_id'] is not None:
            error('platform','kit_not_applicable')
        elif platform['choice']=='not-designed' and platform['name'] is not None:
            error('platform','name_not_applicable')
        elif platform['name'] is not None and (type(platform['name']) is not str or not 1<=len(platform['name'])<=120
                or any(ord(c)<32 or ord(c)==127 for c in platform['name'])):
            error('platform','short_name')
    reasons = ['pending_'+key for key in CATALOG['approvals']]
    higher = not errors and value.get('production_band') == 'higher-volume'
    return {'revision':CATALOG['revision'], 'status':'invalid' if errors else ('requires_quote' if higher else 'awaiting_review'),
            'valid':not errors,'errors':errors,'reasons':(['higher_volume'] if higher else [])+reasons,
            'purchase_enabled':False,'money':dict(CATALOG['money']),
            'support_seconds':value.get('support_packages',0)*36000 if not errors else None}
