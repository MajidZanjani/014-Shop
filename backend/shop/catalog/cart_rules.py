"""Bounded draft-only cart rules. Quoted support seconds are not granted credits."""
import uuid
from .rules import CATALOG,evaluate,integer
MAX_LINES=20

def evaluate_cart(lines):
    errors=[];statuses=[];seconds=0
    def error(field,code):errors.append({'field':field,'code':code})
    if not isinstance(lines,list) or len(lines)>MAX_LINES:
        error('lines','bounded_array')
    else:
        seen=set()
        for index,line in enumerate(lines):
            prefix='lines.'+str(index)
            if not isinstance(line,dict):error(prefix,'fields');continue
            kind=line.get('kind')
            keys={'id','kind','product_id','quantity'}|({'configuration'} if kind=='ip' else set())
            if set(line)!=keys:error(prefix,'fields');continue
            identity=line['id']
            try:
                if not isinstance(identity,str) or str(uuid.UUID(identity))!=identity:raise ValueError('id')
                if identity in seen:error(prefix+'.id','duplicate')
                seen.add(identity)
            except (ValueError,TypeError,AttributeError):error(prefix+'.id','uuid')
            if kind=='ip':
                if line['product_id']!=CATALOG['product_id']:error(prefix+'.product_id','invalid')
                if not integer(line['quantity']) or line['quantity']!=1:error(prefix+'.quantity','one_per_line')
                result=evaluate(line['configuration'])
                for item in result['errors']:error(prefix+'.configuration.'+item['field'],item['code'])
                if result['valid'] and line['configuration']['support_packages']!=0:error(prefix+'.configuration.support_packages','separate_line_required')
                statuses.append(result['status'])
            elif kind=='support':
                if line['product_id']!=CATALOG['support_product_id']:error(prefix+'.product_id','invalid')
                quantity=line['quantity']
                if not integer(quantity) or not 1<=quantity<=1000000:error(prefix+'.quantity','positive_integer')
                else:seconds+=quantity*CATALOG['support_seconds_per_package']
                statuses.append('awaiting_review')
            else:error(prefix+'.kind','invalid')
    return {'revision':CATALOG['revision'],'valid':not errors,'errors':errors,
            'status':'invalid' if errors else ('draft' if not lines else ('requires_quote' if 'requires_quote' in statuses else 'awaiting_review')),
            'purchase_enabled':False,'money':dict(CATALOG['money']),
            'reasons':['pending_'+key for key in CATALOG['approvals']],
            'quoted_support_seconds':None if errors else seconds}
