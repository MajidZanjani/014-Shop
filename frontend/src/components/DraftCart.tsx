import { useEffect, useRef, useState } from 'react';
import { evaluateCart } from '../lib/cart';
import { catalog } from '../lib/catalog';
import { evaluate } from '../lib/configuration';
import type { Configuration } from '../lib/configuration';
import { ApiError, customerRequest } from '../lib/customer-api';
type Line = {id:string;kind:'ip'|'support';product_id:string;quantity:number;configuration?:Configuration};
function ConfigurationSummary({value}:{value:Configuration}) {
  return <span><strong>{value.vendor}</strong> · {value.families.join(', ')} · {value.term}
    {' '}· Fixed nodes: {value.fixed_nodes} · Floating nodes: {value.floating_nodes}
    {value.production_band&&<> · Production band: {value.production_band} · Estimated units: {value.production_units??'Not supplied'}</>}
  </span>;
}
type ReviewStatus = {code:string;label:string;version:number|null;updated_at:string|null};
function ReviewStatusText({value}:{value?:ReviewStatus}) {
  let label='Review status unavailable';
  switch(value?.code){
    case 'awaiting_review':label='Awaiting review';break;
    case 'needs_information':label='Scope clarification needed';break;
    case 'ready_for_commercial_review':label='Ready for commercial review — no offer approved';break;
    case 'declined':label='Request declined';break;
  }
  return <span>{label}{value?.updated_at&&<> · Last status update: {value.updated_at}</>}</span>;
}
type Snapshot = {cart_id:string|null;version:number;current_version:number;catalog_revision:string;lines:Line[];evaluation:{status:string;quoted_support_seconds:number|null}};
export default function DraftCart({configuration,csrf,onResume}:{configuration:Configuration;csrf:string;onResume:(v:Configuration)=>void}) {
  const [cart,setCart]=useState<Snapshot|null>(null),[busy,setBusy]=useState(false),[message,setMessage]=useState('Loading draft cart…'),[quantity,setQuantity]=useState(1),[uncertain,setUncertain]=useState(false);
  const pending=useRef<object|null>(null);
  const quotePending=useRef<object|null>(null);
  const [quoteUncertain,setQuoteUncertain]=useState(false);
  const [requests,setRequests]=useState<{id:string;version:number;created_at:string;review_status?:ReviewStatus}[]>([]);
  const [receipt,setReceipt]=useState<(Snapshot & {id:string;review_status?:ReviewStatus})|null>(null);
  const loadRequests=async()=>{const value=await customerRequest('/api/v1/quotation-requests/');setRequests(value.requests);};
  const loadReceipt=async(id:string)=>{
    if(busy||uncertain||quoteUncertain)return;
    setBusy(true);
    try{setReceipt(await customerRequest('/api/v1/quotation-requests/'+id+'/'));}
    catch{setMessage('Request unavailable. Verify your session.');}
    finally{setBusy(false);}
  };
  useEffect(()=>{void loadRequests().catch(()=>setMessage('Quotation request history unavailable. Reload to retry.'));},[]);
  const requestQuote=async()=>{
    if(busy||uncertain||!cart)return;
    if(!quotePending.current){
      if(!cart.cart_id||!cart.lines.length)return;
      quotePending.current={request_id:crypto.randomUUID(),cart_id:cart.cart_id,version:cart.version};
    }
    setBusy(true);
    try{
      const value=await customerRequest('/api/v1/quotation-requests/','POST',quotePending.current,csrf);
      quotePending.current=null;setQuoteUncertain(false);setReceipt(value);
      setMessage('Quotation request captured for the saved version below. No approved offer, order, payment or support credit was created.');
      try{await loadRequests();}catch{setMessage('Request captured. Reload request history to see the latest list.');}
    }catch(error){
      if(error instanceof ApiError&&error.status<500){quotePending.current=null;setQuoteUncertain(false);setMessage('Request rejected. Reload the cart and review its saved version before requesting again.');}
      else{setQuoteUncertain(true);setMessage('Quotation request outcome uncertain. Retry the exact request before editing the cart.');}
    }finally{setBusy(false);}
  };
  const [editing,setEditing]=useState<string|null>(null);
  const refresh=async()=>{setCart(await customerRequest('/api/v1/cart/'));};
  useEffect(()=>{let live=true;customerRequest('/api/v1/cart/').then(value=>{if(live){setCart(value);setMessage('');}}).catch(()=>{if(live)setMessage('Cart unavailable. Refresh and verify your session.');});return()=>{live=false;};},[]);
  const save=async(lines?:Line[])=>{
    if(busy||quoteUncertain||!cart)return;
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
    <fieldset disabled={busy||uncertain||quoteUncertain||!cart}>
      <button type="button" disabled={!evaluate(configuration).valid} onClick={addConfiguration}>Add current configuration to cart</button>
      <label>Support package quantity <input type="number" min="1" max="1000000" step="1" value={quantity} onChange={e=>setQuantity(Number(e.target.value))}/></label>
      <button type="button" disabled={!Number.isSafeInteger(quantity)||quantity<1||quantity>1000000} onClick={()=>cart&&void save([...cart.lines,{id:crypto.randomUUID(),kind:'support',product_id:catalog.support_product_id,quantity}])}>Add support packages only</button>
      {editing&&<button type="button" disabled={!evaluate(configuration).valid} onClick={()=>cart&&void save(cart.lines.map(line=>line.id===editing?{...line,configuration:{...configuration,families:[...configuration.families],support_packages:0}}:line))}>Replace selected IP line with current configuration (support unchanged)</button>}
      <ol>{cart?.lines.map(line=><li key={line.id}>
        {line.kind==='ip'?<>{line.configuration&&<ConfigurationSummary value={line.configuration}/>} · quantity 1 <button type="button" onClick={()=>{if(line.configuration){onResume({...line.configuration,families:[...line.configuration.families]});setEditing(line.id);}}}>Load configuration</button></>:<>Support · {line.quantity} packages · {line.quantity*10} hours <button type="button" disabled={!Number.isSafeInteger(quantity)||quantity<1||quantity>1000000} onClick={()=>void save(cart.lines.map(item=>item.id===line.id?{...item,quantity}:item))}>Use support quantity above</button></>}
        {' '}· Price pending <button type="button" onClick={()=>void save(cart.lines.filter(item=>item.id!==line.id))}>Remove line</button>
      </li>)}</ol>
    </fieldset>
    {uncertain&&<button type="button" disabled={busy} onClick={()=>void save()}>Retry last cart save</button>}
    <button type="button" disabled={busy||uncertain||quoteUncertain} onClick={()=>{setBusy(true);void refresh().then(()=>setMessage('Current cart loaded.')).catch(()=>setMessage('Unable to reload cart. Verify your session.')).finally(()=>setBusy(false));}}>Reload cart</button>
    <p>Version {cart?.current_version??0} · {cart?.evaluation.status??'loading'} · Quoted support hours: {(cart?.evaluation.quoted_support_seconds??0)/3600}</p>
    <p>Request a quotation for all lines in the saved cart version shown above. Later cart edits leave that request unchanged. This local demo captures requests. Staff review is manual; no email is sent.</p>
    <button type="button" disabled={busy||uncertain||quoteUncertain||!cart?.lines.length} onClick={()=>void requestQuote()}>Request quotation for saved cart</button>
    {quoteUncertain&&<button type="button" disabled={busy} onClick={()=>void requestQuote()}>Retry quotation request</button>}
    <h4>Your quotation requests</h4>
    <button type="button" disabled={busy||uncertain||quoteUncertain} onClick={()=>{setBusy(true);void loadRequests().catch(()=>setMessage('Unable to load request history. Verify your session.')).finally(()=>setBusy(false));}}>Reload request history</button>
    <p>Showing up to 20 most recent requests. Reload history or review a captured request to load its latest status.</p>
    <ol>{requests.map(row=><li key={row.id}>Saved version {row.version} · {row.created_at} · <ReviewStatusText value={row.review_status}/> <button type="button" disabled={busy||uncertain||quoteUncertain} onClick={()=>void loadReceipt(row.id)}>Review captured request</button></li>)}</ol>
    {receipt&&<section aria-label="Captured quotation request"><h4>Captured request {receipt.id}</h4>
      <p><ReviewStatusText value={receipt.review_status}/></p>
      <p><a href={"/purchase/quotation-business/"+receipt.id+"/"}>Review and attach saved business details</a> · Country and tax choices remain pending.</p>
      <button type="button" disabled={busy||uncertain||quoteUncertain} onClick={()=>void loadReceipt(receipt.id)}>Refresh captured request status</button>
      <p>Saved version {receipt.version} · Catalogue {receipt.catalog_revision} · Prices and rights pending. Acceptance and payment disabled.</p>
      <ol>{receipt.lines.map(line=><li key={line.id}>{line.kind==='support'?`Support: ${line.quantity} ten-hour packages`:line.configuration&&<ConfigurationSummary value={line.configuration}/>} · Line {line.id} · Quantity {line.quantity}</li>)}</ol>
    </section>}
    <button type="button" disabled>Checkout pending commercial approval</button><p role="status">{message}</p>
  </section>;
}
