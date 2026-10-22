import { catalog } from './catalog';
import { evaluate } from './configuration';
export function evaluateCart(lines: unknown) {
  const errors:{field:string;code:string}[]=[],statuses:string[]=[];let seconds=0;
  const error=(field:string,code:string)=>errors.push({field,code});
  if(!Array.isArray(lines)||lines.length>20)error('lines','bounded_array');
  else {const seen=new Set<string>();lines.forEach((line,index)=>{
    const prefix='lines.'+index;
    if(!line||typeof line!=='object'||Array.isArray(line)){error(prefix,'fields');return;}
    const keys=['id','kind','product_id','quantity',...(line.kind==='ip'?['configuration']:[])].sort().join(',');
    if(Object.keys(line).sort().join(',')!==keys){error(prefix,'fields');return;}
    if(typeof line.id!=='string'||! /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(line.id))error(prefix+'.id','uuid');
    else {if(seen.has(line.id))error(prefix+'.id','duplicate');seen.add(line.id);}
    if(line.kind==='ip'){
      if(line.product_id!==catalog.product_id)error(prefix+'.product_id','invalid');
      if(!Number.isSafeInteger(line.quantity)||line.quantity!==1)error(prefix+'.quantity','one_per_line');
      const result=evaluate(line.configuration);result.errors.forEach(item=>error(prefix+'.configuration.'+item.field,item.code));
      if(result.valid&&line.configuration.support_packages!==0)error(prefix+'.configuration.support_packages','separate_line_required');
      statuses.push(result.status);
    }else if(line.kind==='support'){
      if(line.product_id!==catalog.support_product_id)error(prefix+'.product_id','invalid');
      if(!Number.isSafeInteger(line.quantity)||line.quantity<1||line.quantity>1000000)error(prefix+'.quantity','positive_integer');
      else seconds+=line.quantity*catalog.support_seconds_per_package;
      statuses.push('awaiting_review');
    }else error(prefix+'.kind','invalid');
  });}
  return {revision:catalog.revision,valid:!errors.length,errors,status:errors.length?'invalid':(!(lines as unknown[]).length?'draft':statuses.includes('requires_quote')?'requires_quote':'awaiting_review'),purchase_enabled:false,money:{...catalog.money},reasons:Object.keys(catalog.approvals).map(key=>'pending_'+key),quoted_support_seconds:errors.length?null:seconds};
}
