import { useState } from 'react';
import { shb } from '../lib/shb';

export default function ShbSelector() {
  const [variant,setVariant]=useState<string>('shb-fpga-10h');
  const [quantity,setQuantity]=useState('1');
  const selected=shb.variants.find(item=>item.id===variant)!;
  const count=/^[1-9][0-9]{0,9}$/.test(quantity) ? Number(quantity) : 0;
  const valid=Number.isSafeInteger(count) && count>=1 && count<=2147483647;
  const href='/purchase/simple/?variant='+encodeURIComponent(variant)+'&quantity='+encodeURIComponent(quantity);
  return <section aria-label="Select support bundle">
    <label htmlFor="shb-variant">Bundle</label><select id="shb-variant" value={variant} onChange={event=>setVariant(event.target.value)}>{shb.variants.map(item=><option key={item.id} value={item.id}>{item.label}</option>)}</select>
    <label htmlFor="shb-quantity">Bundle quantity</label><input id="shb-quantity" type="number" min="1" step="1" inputMode="numeric" value={quantity} onChange={event=>setQuantity(event.target.value)} />
    <div aria-live="polite"><p>{selected.hours_per_bundle} hours per whole bundle.</p>{valid ? <p><strong>{count*selected.hours_per_bundle} hours in this order</strong></p> : <p role="alert">Enter a positive whole number of bundles.</p>}
    <p>{selected.workflow==='request' ? 'Price to be confirmed. Estimated totals are subject to technical review and an approved offer.' : 'Live rates and final policies await approval.'}</p>
    {valid && <a href={href}>{selected.workflow==='request' ? 'Submit Request' : 'Checkout'}</a>}</div>
    <p>The protected form reviews your company/contact details before any action. Submitting an ASIC request does not charge you or reserve engineering availability.</p>
  </section>;
}
