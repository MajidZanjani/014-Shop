import { catalog } from './catalog';
export type Platform = {choice:string;kit_id:string|null;name:string|null};
export type Configuration = { platform?: Platform; product_id: string; profile_id: string; quantity: number; vendor: string; families: string[]; term: string; production_band: string | null; production_units: number | null; fixed_nodes: number; floating_nodes: number; support_packages: number };
export const initialConfiguration = (): Configuration => ({ product_id: catalog.product_id, profile_id: catalog.profile_id, quantity: 1, vendor: '', families: [], term: '', production_band: null, production_units: null, fixed_nodes: 0, floating_nodes: 0, support_packages: 0 });
export function changeVendor(value: Configuration, vendor: string): Configuration {
  return { ...value, vendor, families: [], term: '', production_band: null, production_units: null, fixed_nodes: 0, floating_nodes: 0 };
}
export function changeTerm(value: Configuration, term: string): Configuration {
  return { ...value, term, production_band: null, production_units: null };
}
const keys = Object.keys(initialConfiguration()).sort().join(',');
const maxCount = 1000000;
export function evaluate(input: unknown) {
  const errors: {field: string; code: string}[] = [];
  const error = (field: string, code: string) => { errors.push({ field, code }); };
  let value = input as Configuration;
  if (!input || typeof input !== 'object' || Array.isArray(input) || Object.keys(input).filter(k=>k!=='platform').sort().join(',') !== keys) {
    error('configuration','fields'); value = initialConfiguration();
  } else {
    if (value.product_id !== catalog.product_id) error('product_id','invalid');
    if (value.profile_id !== catalog.profile_id) error('profile_id','invalid');
    if (!Number.isSafeInteger(value.quantity) || value.quantity !== 1) error('quantity','one_per_line');
    const vendor = catalog.vendors.find(v => v.id === value.vendor);
    if (!vendor) error('vendor','required');
    const families = value.families;
    const allowed: string[] = vendor ? vendor.families.map(f => f.id) : [];
    if (!Array.isArray(families) || families.length < 1 || families.length > 13 || families.some(f => typeof f !== 'string' || !allowed.includes(f)) || new Set(families).size !== families.length) error('families','vendor_families');
    const term = catalog.terms.find(t => t.id === value.term);
    if (!term || !(term.vendors as readonly string[]).includes(value.vendor)) error('term','vendor_term');
    if (value.term === 'rdp-yearly') {
      const band = catalog.production_bands.find(b => b.id === value.production_band);
      if (!band) error('production_band','required');
      const units = value.production_units;
      if (units !== null) {
        if (!Number.isSafeInteger(units) || units < 1 || units > maxCount) error('production_units','positive_integer');
        else if (band && !(band.minimum <= units && (band.maximum === null || units <= band.maximum))) error('production_units','band_mismatch');
      }
    } else if (value.production_band !== null || value.production_units !== null) error('production_band','not_applicable');
    for (const field of ['fixed_nodes','floating_nodes','support_packages'] as const) {
      if (!Number.isSafeInteger(value[field]) || value[field] < 0 || value[field] > maxCount) error(field,'nonnegative_integer');
    }
    if (['fixed_nodes','floating_nodes'].every(f => Number.isSafeInteger(value[f as keyof Configuration]) && (value[f as 'fixed_nodes'] as number) >= 0 && (value[f as 'fixed_nodes'] as number) <= maxCount)) {
      if (value.vendor === 'altera') { if (value.fixed_nodes + value.floating_nodes === 0) error('access','required'); }
      else if (value.fixed_nodes || value.floating_nodes) error('access','not_applicable');
    }
  }
  if ('platform' in value) {
    const p=value.platform;
    if(!p || typeof p!=='object' || Array.isArray(p) || Object.keys(p).sort().join(',')!=='choice,kit_id,name') error('platform','fields');
    else if(!(catalog.purchase_flow.platform_choices as readonly string[]).includes(p.choice)) error('platform','choice');
    else if(p.choice==='listed-kit') {
      if(typeof p.kit_id!=='string' || p.name!==null || !(catalog.purchase_flow.ready_kits as readonly {id:string}[]).some(k=>k.id===p.kit_id)) error('platform','kit');
    } else if(p.kit_id!==null) error('platform','kit_not_applicable');
    else if(p.choice==='not-designed' && p.name!==null) error('platform','name_not_applicable');
    else if(p.name!==null && (typeof p.name!=='string' || [...p.name].length<1 || [...p.name].length>120 || /[\x00-\x1f\x7f]/.test(p.name))) error('platform','short_name');
  }
  const reasons = Object.keys(catalog.approvals).map(k => 'pending_'+k);
  const higher = errors.length === 0 && value.production_band === 'higher-volume';
  return { revision: catalog.revision, status: errors.length ? 'invalid' : (higher ? 'requires_quote' : 'awaiting_review'), valid: errors.length === 0, errors,
    reasons: [...(higher ? ['higher_volume'] : []), ...reasons], purchase_enabled: false, money: { ...catalog.money }, support_seconds: errors.length ? null : value.support_packages * 36000 };
}
