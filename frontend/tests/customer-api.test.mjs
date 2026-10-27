import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile,writeFile,mkdtemp,rm} from 'node:fs/promises';
import {pathToFileURL} from 'node:url';
import ts from 'typescript';
const scratch=await mkdtemp(new URL('../.customer-test-',import.meta.url).pathname);
let api;
try{
  const source=await readFile(new URL('../src/lib/customer-api.ts',import.meta.url),'utf8');
  const output=ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText;
  await writeFile(scratch+'/api.mjs',output);api=await import(pathToFileURL(scratch+'/api.mjs'));
}finally{await rm(scratch,{recursive:true,force:true});}
test('customer transport cannot run during static builds',async()=>{
  await assert.rejects(api.customerRequest('/api/v1/customer/session/'),/browser-only/);
});
test('customer transport restricts paths, sends same-origin CSRF and hides error bodies',async()=>{
  const old=globalThis.window;const calls=[];
  globalThis.window={fetch:async(path,options)=>{calls.push({path,options});return {ok:true,headers:new Headers({'content-type':'application/json','X-Shop-Access-Context':'a'.repeat(64)}),json:async()=>({authenticated:false})};}};
  try{
    for(const path of ['https://external.invalid/','//external.invalid/','/api/v1/configuration-drafts/../../private/','/api/v1/customer/session/?code=secret','/api/v1/quotation-requests/?owner=other','/api/v1/quotation-requests/../../private/'])await assert.rejects(api.customerRequest(path),/Unapproved/);
    assert.equal(calls.length,0);
    await assert.rejects(api.customerRequest('/api/v1/customer/verify/','POST',{code:'synthetic'}),/CSRF/);
    await api.customerRequest('/api/v1/customer/verify/','POST',{code:'synthetic'},'synthetic-csrf');
    assert.equal(calls[0].options.credentials,'same-origin');assert.equal(calls[0].options.cache,'no-store');assert.equal(calls[0].options.redirect,'error');
    assert.equal(calls[0].options.headers['X-CSRFToken'],'synthetic-csrf');
    assert.equal(calls[0].path,'/api/v1/customer/verify/');assert.deepEqual(JSON.parse(calls[0].options.body),{code:'synthetic'});
    await api.customerRequest('/api/v1/quotation-requests/','POST',{request_id:'synthetic',cart_id:'synthetic',version:1},'synthetic-csrf');
    await api.customerRequest('/api/v1/quotation-requests/22222222-2222-4222-8222-222222222222/');
    assert.equal(calls[1].options.cache,'no-store');assert.equal(calls[2].options.credentials,'same-origin');
    globalThis.window.fetch=async()=>({ok:false,status:403});
    await assert.rejects(api.customerRequest('/api/v1/customer/session/'),error=>error.status===403&&error.message==='Customer request failed');
  }finally{if(old===undefined)delete globalThis.window;else globalThis.window=old;}
});

test('private responses cannot cross access context or expose mismatched bodies',async()=>{
 const old=globalThis.window;let context='a'.repeat(64),parsed=0;
 globalThis.window={fetch:async()=>({ok:true,headers:new Headers({'content-type':'application/json','X-Shop-Access-Context':context}),json:async()=>{parsed++;return {};}})};
 try{
  await api.customerRequest('/api/v1/customer/session/');
  await api.customerRequest('/api/v1/cart/');
  const before=parsed;context='b'.repeat(64);
  await assert.rejects(api.customerRequest('/api/v1/cart/'),e=>e.status===403);
  assert.equal(parsed,before);
  await api.customerRequest('/api/v1/customer/session/');
  await api.customerRequest('/api/v1/cart/');
  for(context of ['', 'b'.repeat(63), 'b'.repeat(65), 'z'.repeat(64)]){
   await assert.rejects(api.customerRequest('/api/v1/cart/'),e=>e.status===403);
  }
  context='b'.repeat(64);
  let release,started;
  const waiting=new Promise(resolve=>{started=resolve;});
  globalThis.window.fetch=async path=>({ok:true,headers:new Headers({'content-type':'application/json','X-Shop-Access-Context':context}),json:async()=>{
   if(path==='/api/v1/cart/'){started();await new Promise(resolve=>{release=resolve;});}
   return {};
  }});
  const pending=api.customerRequest('/api/v1/cart/');await waiting;
  context='c'.repeat(64);await api.customerRequest('/api/v1/customer/session/');
  release();await assert.rejects(pending,e=>e.status===403);
 }finally{if(old===undefined)delete globalThis.window;else globalThis.window=old;}
});
