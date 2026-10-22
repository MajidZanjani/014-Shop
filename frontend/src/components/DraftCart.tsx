import { useEffect, useRef, useState } from 'react';
import { evaluateCart } from '../lib/cart';
import { catalog } from '../lib/catalog';
import { evaluate } from '../lib/configuration';
import type { Configuration } from '../lib/configuration';
import { ApiError, customerRequest } from '../lib/customer-api';
type Line = {id:string;kind:'ip'|'support';product_id:string;quantity:number;configuration?:Configuration};
type Snapshot = {version:number;current_version:number;catalog_revision:string;lines:Line[];evaluation:{status:string;quoted_support_seconds:number|null}};
export default function DraftCart({configuration,csrf,onResume}:{configuration:Configuration;csrf:string;onResume:(v:Configuration)=>void}) {
  const [cart,setCart]=useState<Snapshot|null>(null),[busy,setBusy]=useState(false),[message,setMessage]=useState('Loading draft cart…'),[quantity,setQuantity]=useState(1),[uncertain,setUncertain]=useState(false);
  const pending=useRef<object|null>(null);
  const [editing,setEditing]=useState<string|null>(null);
  const refresh=async()=>{setCart(await customerRequest('/api/v1/cart/'));};
  useEffect(()=>{let live=true;customerRequest('/api/v1/cart/').then(value=>{if(live){setCart(value);setMessage('');}}).catch(()=>{if(live)setMessage('Cart unavailable. Refresh and verify your session.');});return()=>{live=false;};},[]);
  const save=async(lines?:Line[])=>{
    if(busy||!cart)return;
    if(lines){if(!evaluateCart(lines).valid){setMessage('A draft cart can contain at most 20 lines.');return;}pending.current={request_id:crypto.randomUUID(),expected_version:cart.current_version,catalog_revision:catalog.revision,lines};}
    if(!pending.current)return;setBusy(true);
    try {await customerRequest('/api/v1/cart/','POST',pending.current,csrf);pending.current=null;setUncertain(false);setEditing(null);try{await refresh();setMessage('Draft cart saved. No order, payment or support credit was created.');}catch{setCart(null);setMessage('Save confirmed. Reload the cart before editing again.');}}
    catch(error){
      if(error instanceof ApiError && error.status<500){pending.current=null;setUncertain(false);setCart(null);setMessage(error.status===409?'Cart changed in another tab or catalog revision. Reload the cart and review before editing.':'Save rejected. Refresh and verify your session or configuration.');}
      else {setUncertain(true);setMessage('Save outcome uncertain. Retry the same request before making another change.');}
    }finally{setBusy(false);}
  };
  const addConfiguration=()=>{
    if(!cart||!evaluate(configuration).valid)return;
    const lines:Line[]=[...cart.lines,{id:crypto.randomUUID(),kind:'ip',product_id:catalog.product_id,quantity:1,configuration:{...configuration,families:[...configuration.families],support_packages:0}}];
    if(configuration.support_packages)lines.push({id:crypto.randomUUID(),kind:'support',product_id:catalog.support_product_id,quantity:configuration.support_packages});
    void save(lines);
  };
  return <section aria-label="Draft cart"><h3>Your draft cart</h3>
    <p>Each IP line has one vendor and quantity one. Support packages are separate, non-expiring ten-hour packages. Prices and rights await approval; checkout is disabled.</p>
    <fieldset disabled={busy||uncertain||!cart}>
      <button type="button" disabled={!evaluate(configuration).valid} onClick={addConfiguration}>Add current configuration to cart</button>
      <label>Support package quantity <input type="number" min="1" max="1000000" step="1" value={quantity} onChange={e=>setQuantity(Number(e.target.value))}/></label>
      <button type="button" disabled={!Number.isSafeInteger(quantity)||quantity<1||quantity>1000000} onClick={()=>cart&&void save([...cart.lines,{id:crypto.randomUUID(),kind:'support',product_id:catalog.support_product_id,quantity}])}>Add support packages only</button>
      {editing&&<button type="button" disabled={!evaluate(configuration).valid} onClick={()=>cart&&void save(cart.lines.map(line=>line.id===editing?{...line,configuration:{...configuration,families:[...configuration.families],support_packages:0}}:line))}>Replace selected IP line with current configuration (support unchanged)</button>}
      <ol>{cart?.lines.map(line=><li key={line.id}>
        {line.kind==='ip'?<><strong>{line.configuration?.vendor}</strong> · {line.configuration?.families.join(', ')} · {line.configuration?.term} · quantity 1 <button type="button" onClick={()=>{if(line.configuration){onResume({...line.configuration,families:[...line.configuration.families]});setEditing(line.id);}}}>Load configuration</button></>:<>Support · {line.quantity} packages · {line.quantity*10} hours <button type="button" disabled={!Number.isSafeInteger(quantity)||quantity<1||quantity>1000000} onClick={()=>void save(cart.lines.map(item=>item.id===line.id?{...item,quantity}:item))}>Use support quantity above</button></>}
        {' '}· Price pending <button type="button" onClick={()=>void save(cart.lines.filter(item=>item.id!==line.id))}>Remove line</button>
      </li>)}</ol>
    </fieldset>
    {uncertain&&<button type="button" disabled={busy} onClick={()=>void save()}>Retry last cart save</button>}
    <button type="button" disabled={busy||uncertain} onClick={()=>{setBusy(true);void refresh().then(()=>setMessage('Current cart loaded.')).catch(()=>setMessage('Unable to reload cart. Verify your session.')).finally(()=>setBusy(false));}}>Reload cart</button>
    <p>Version {cart?.current_version??0} · {cart?.evaluation.status??'loading'} · Quoted support hours: {(cart?.evaluation.quoted_support_seconds??0)/3600}</p>
    <button type="button" disabled>Checkout pending commercial approval</button><p role="status">{message}</p>
  </section>;
}
