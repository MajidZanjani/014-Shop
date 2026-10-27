import { useState } from 'react';
import CustomerDrafts from './CustomerDrafts';
import { catalog } from '../lib/catalog';
import { initialConfiguration, changeVendor, changeTerm, evaluate } from '../lib/configuration';

export default function Configurator() {
  const [value, setValue] = useState(initialConfiguration);
  // Old saved snapshots may omit platform; new saves still need an explicit answer.
  const configuration = {...value, platform: value.platform ?? {choice:'',kit_id:null,name:null}};
  const result = evaluate(configuration);
  const vendor = catalog.vendors.find(v => v.id === value.vendor);
  const term = catalog.terms.find(t => t.id === value.term);
  const update = (key: 'fixed_nodes' | 'floating_nodes' | 'support_packages', raw: string) => setValue(v => ({...v, [key]: raw === '' ? NaN : Number(raw)}));
  return <div className="configurator">
    <div className="controls">
      <fieldset><legend>01 / FPGA platform</legend>
        <label htmlFor="vendor">One vendor per licence</label>
        <select id="vendor" value={value.vendor} onChange={e => setValue(changeVendor(value,e.target.value))}>
          <option value="">Choose your vendor</option>{catalog.vendors.map(v => <option key={v.id} value={v.id}>{v.label}</option>)}
        </select>
        {vendor && <div className="families"><p>Select one or more families</p>{vendor.families.map(f => <label className="choice" key={f.id}>
          <input type="checkbox" checked={value.families.includes(f.id)} onChange={e => setValue(v => ({...v, families: e.target.checked ? [...v.families,f.id] : v.families.filter(id => id !== f.id)}))} />{f.label}
        </label>)}</div>}
        <p className="hint">A different vendor requires a separate licence line. Cyclone 10 coverage overlap remains subject to review.</p>
      </fieldset>
      <fieldset><legend>02 / Licence term &amp; use</legend>
        {catalog.terms.filter(t => (t.vendors as readonly string[]).includes(value.vendor)).map(t => <label className="choice" key={t.id}>
          <input type="radio" name="term" value={t.id} checked={value.term === t.id} onChange={() => setValue(changeTerm(value,t.id))} />{t.label}
        </label>)}
        {!vendor && <p>Choose a vendor to see applicable terms.</p>}
        {term && <p className="hint">{term.description}</p>}
        {value.term === 'rdp-yearly' && <div>
          <label htmlFor="band">Production band for the licence period</label>
          <select id="band" value={value.production_band ?? ''} onChange={e => setValue(v => ({...v,production_band:e.target.value || null,production_units:null}))}>
            <option value="">Choose a band</option>{catalog.production_bands.map(b => <option key={b.id} value={b.id}>{b.label}</option>)}
          </select>
          <label htmlFor="units">Expected production units (optional)</label>
          <input id="units" type="number" min="1" max="1000000" step="1" value={value.production_units ?? ''} onChange={e => setValue(v => ({...v,production_units:e.target.value === '' ? null : Number(e.target.value)}))} />
          <p className="hint">Above 5,000 units requires a quotation. Unit counting, period and aggregation require agreed terms.</p>
        </div>}
      </fieldset>
      {value.vendor === 'altera' && <fieldset><legend>03 / Development access</legend>
        {(['fixed_nodes','floating_nodes'] as const).map(key => <div key={key}>
          <label className="choice"><input type="checkbox" checked={value[key] !== 0} onChange={e => setValue(v => ({...v,[key]:e.target.checked ? 1 : 0}))} />{key === 'fixed_nodes' ? 'Fixed / node-locked licences' : 'Floating / concurrent seats'}</label>
          {value[key] !== 0 && <label>Number of {key === 'fixed_nodes' ? 'fixed nodes' : 'floating seats'}<input aria-label={key === 'fixed_nodes' ? 'Fixed nodes' : 'Floating seats'} type="number" min="1" max="1000000" step="1" value={Number.isNaN(value[key]) ? '' : value[key]} onChange={e => update(key,e.target.value)} /></label>}
        </div>)}
        <p className="hint">Select either mode or both. Development seats are separate from production units. Host identifiers will be requested only through a protected workflow; none are collected here.</p>
        <p className="hint">Node allowances and charges await approval. No provisional rate is applied.</p>
      </fieldset>}
      {vendor && value.vendor !== 'altera' && <p className="notice">Licence-access conditions for {vendor.label} await review. No host identifiers are requested.</p>}
      <fieldset><legend>04 / Board or development kit</legend>
        <label htmlFor="platform">Which board or development kit will you use?</label>
        <select id="platform" value={value.platform?.choice ?? ''} onChange={e=>setValue(v=>({...v,platform:{choice:e.target.value,kit_id:null,name:null}}))}>
          <option value="">Choose a platform</option><option value="listed-kit">A listed development kit</option>
          <option value="other-board">Another kit or a custom/modified board</option>
          <option value="not-designed">Board not designed or selected / I need board-design guidance</option>
        </select>
        {value.platform?.choice==='listed-kit' && <p>No approved ready-kit entries have been supplied yet. A ready-design offer remains pending.</p>}
        {value.platform?.choice==='other-board' && <label htmlFor="board-name">Short board name/model (optional; blank means not yet named/unknown)
          <input id="board-name" maxLength={120} value={value.platform.name ?? ''} onChange={e=>setValue(v=>({...v,platform:{choice:'other-board',kit_id:null,name:e.target.value || null}}))}/></label>}
        <p className="hint">An approved standard R&amp;D development offer can cover an unknown or unfinished board. Detailed pinouts and engineering information are requested privately when the work needs them.</p>
      </fieldset>
      <fieldset><legend>05 / Support for SLL IP</legend>
        <label htmlFor="support">10-hour packages</label><input id="support" type="number" min="0" max="1000000" step="1" value={Number.isNaN(value.support_packages) ? '' : value.support_packages} onChange={e => update('support_packages',e.target.value)} />
        <p className="hint">Additional support is optional or required according to the seller offer. Its approved minimum and price will be shown before purchase. Current policy is pending. Purchased hours do not expire. Support never extends IP rights. Each package grants exactly 10 hours once accepted and paid.</p>
      </fieldset>
    </div>
    <aside aria-label="Configuration summary">
      <div className="summary"><p className="eyebrow">YOUR CONFIGURATION</p><h2>Review your licence</h2>
        <dl><dt>Vendor</dt><dd>{vendor?.label ?? 'Not selected'}</dd><dt>Families</dt><dd>{vendor?.families.filter(f => value.families.includes(f.id)).map(f => f.label).join(', ') || 'Not selected'}</dd>
        <dt>Term</dt><dd>{term?.label ?? 'Not selected'}</dd><dt>Production</dt><dd>{catalog.production_bands.find(b => b.id === value.production_band)?.label ?? 'Not applicable'}</dd>
        <dt>Access</dt><dd>{value.vendor === 'altera' ? `${value.fixed_nodes} fixed / ${value.floating_nodes} floating` : 'Conditions pending'}</dd>
        <dt>Platform</dt><dd>{value.platform?.choice==='not-designed'?'Board not designed or selected':value.platform?.choice==='other-board'?(value.platform.name || 'Other/custom board · not yet named'):value.platform?.choice==='listed-kit'?'Ready-kit offer pending':'Not selected'}</dd>
        <dt>Reference design</dt><dd>Approved kit design or an agreed later design. Initial R&amp;D materials do not complete a promised later design.</dd>
        <dt>Support</dt><dd>{Number.isSafeInteger(value.support_packages) && value.support_packages >= 0 ? `${value.support_packages * 10} hours` : 'Check quantity'}</dd><dt>Price &amp; VAT</dt><dd>Pending approval · EUR draft</dd></dl>
        <div aria-live="polite" aria-atomic="true" className="validation">
          <strong>{result.valid ? (result.status === 'requires_quote' ? 'Quotation required' : 'Configuration ready for review') : 'Complete your configuration'}</strong>
          {result.errors.length > 0 && <ul>{result.errors.map(e => <li key={e.field+e.code}>{({vendor:'Choose a vendor.',families:'Select families from this vendor.',term:'Choose an applicable term.',production_band:'Choose an RDP production band.',production_units:'Enter whole units within the selected band.',access:'Enable at least one development access mode.',fixed_nodes:'Enter a whole fixed-node count.',floating_nodes:'Enter a whole floating-seat count.',support_packages:'Enter a whole support quantity.',platform:'Choose an applicable platform and only its relevant detail.'} as Record<string,string>)[e.field] ?? 'Check your configuration.'}</li>)}</ul>}
        </div>
        <p>{result.status === 'requires_quote' ? 'Higher-volume configurations require a reviewed quotation.' : 'Actual prices, rights, access, coverage and delivery terms are pending. Applicable approved standard offers do not require individual engineering approval.'}</p>
        <button type="button" disabled>Purchase unavailable · approvals pending</button>
        <p className="hint">Local preview. No order is submitted, no payment is collected, and unsaved selections stay in memory only.</p>
        <CustomerDrafts configuration={configuration} onResume={setValue} />
      </div>
    </aside>
  </div>;
}
