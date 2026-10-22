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
  for (const name of ['catalog','configuration','cart']) {
    const source = await readFile(new URL('src/lib/'+name+'.ts',root),'utf8');
    const result = ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}});
    await writeFile(join(scratch,name+'.mjs'),result.outputText.replace("'./catalog'","'./catalog.mjs'").replace("'./configuration'","'./configuration.mjs'"));
  }
  rules = await import(pathToFileURL(join(scratch,'cart.mjs')));
} finally { await rm(scratch,{recursive:true,force:true}); }
const cases = JSON.parse(await readFile(new URL('cart-conformance.json',import.meta.url),'utf8'));
const results=cases.map(c=>rules.evaluateCart(c.lines));
cases.forEach((c,index)=>test('cart: '+c.name,()=>{
 const r=results[index];assert.equal(r.status,c.status);assert.deepEqual(r.errors.map(e=>e.field+':'+e.code),c.errors);assert.equal(r.purchase_enabled,false);
}));
if(process.env.SHOP_CART_COMPARE_OUTPUT)await writeFile(process.env.SHOP_CART_COMPARE_OUTPUT,JSON.stringify(results));
