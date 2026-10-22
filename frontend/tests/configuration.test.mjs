import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile, writeFile, mkdtemp, rm } from 'node:fs/promises';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import ts from 'typescript';
const root = new URL('../',import.meta.url);
const scratch = await mkdtemp(new URL('../.rules-test-',import.meta.url).pathname);
let rules;
try {
  for (const name of ['catalog','configuration']) {
    const source = await readFile(new URL('src/lib/'+name+'.ts',root),'utf8');
    const result = ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}});
    await writeFile(join(scratch,name+'.mjs'),result.outputText.replace("'./catalog'","'./catalog.mjs'"));
  }
  rules = await import(pathToFileURL(join(scratch,'configuration.mjs')));
} finally { await rm(scratch,{recursive:true,force:true}); }
const cases = JSON.parse(await readFile(new URL('conformance.json',import.meta.url),'utf8'));
for (const c of cases) test('configuration: '+c.name, () => {
  const r = rules.evaluate(c.value);
  assert.equal(r.status,c.status);
  assert.deepEqual(r.errors.map(e=>e.field+':'+e.code),c.errors);
  assert.equal(r.purchase_enabled,false);
  for (const [key,v] of Object.entries(r.money)) if (key.endsWith('_minor')) assert.equal(v,null);
  assert.equal(r.support_seconds,r.valid ? c.value.support_packages * 36000 : null);
});
test('vendor change clears families, term, production and access; preserves unrelated support', () => {
  const v=rules.changeVendor({...cases[1].value,term:'rdp-yearly',production_band:'higher-volume',production_units:6000},'amd-xilinx');
  assert.deepEqual(v,{...rules.initialConfiguration(),vendor:'amd-xilinx',support_packages:2});
});
test('term change resets production band and estimate', () => {
  const v=rules.changeTerm({...cases[0].value,term:'rdp-yearly',production_band:'units-1-100',production_units:100},'perpetual');
  assert.equal(v.production_band,null);assert.equal(v.production_units,null);
});
// The backend compares these full outputs, including null money/reasons/revision.
if (process.env.SHOP_COMPARE_OUTPUT) await writeFile(process.env.SHOP_COMPARE_OUTPUT,JSON.stringify(cases.map(c=>rules.evaluate(c.value))));
