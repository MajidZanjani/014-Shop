import DraftCart from './DraftCart';
import { useEffect, useRef, useState } from 'react';
import { catalog } from '../lib/catalog';
import { evaluate, initialConfiguration } from '../lib/configuration';
import type { Configuration } from '../lib/configuration';
import { ApiError, customerRequest } from '../lib/customer-api';

type Draft = {id: string; revision: string; created_at: string};
export default function CustomerDrafts({configuration, onResume}: {configuration:Configuration; onResume:(v:Configuration)=>void}) {
  const [available,setAvailable]=useState(false);
  const [authenticated,setAuthenticated]=useState(false);
  const [csrf,setCsrf]=useState('');
  const [email,setEmail]=useState('');
  const [code,setCode]=useState('');
  const [requested,setRequested]=useState(false);
  const [busy,setBusy]=useState(false);
  const [message,setMessage]=useState('Connecting to the local backend…');
  const [drafts,setDrafts]=useState<Draft[]>([]);
  const pending=useRef<{payload:string;id:string}|null>(null);
  const mounted=useRef(true);
  useEffect(()=>{
    mounted.current=true;
    customerRequest('/api/v1/customer/session/').then(async session=>{
      if (!mounted.current) return;
      setAvailable(true);setCsrf(session.csrf_token);setAuthenticated(session.authenticated===true);setMessage('');
      if (session.authenticated) {
        const result=await customerRequest('/api/v1/configuration-drafts/');
        if (mounted.current) setDrafts(result.drafts);
      }
    }).catch(()=>{if(mounted.current)setMessage('Start the demo with --backend to use local save/resume.');});
    return ()=>{mounted.current=false;};
  },[]);
  const refresh=async()=>{
    const result=await customerRequest('/api/v1/configuration-drafts/');
    setDrafts(result.drafts);
  };
  const action=async(run:()=>Promise<void>)=>{
    if(busy)return;setBusy(true);setMessage('');
    try{await run();}
    catch(error){
      if(error instanceof ApiError && error.status===401){setAuthenticated(false);setDrafts([]);setMessage('Your session expired. Verify again to access your drafts.');}
      else if(error instanceof ApiError && error.status===429)setMessage('Verification request limit reached. Wait ten minutes before trying again.');
      else if(error instanceof ApiError && error.status===400)setMessage('Verification failed. Check the code, its expiry and the requesting browser.');
      else if(error instanceof ApiError && error.status===403)setMessage('Access or CSRF verification failed. Refresh this page and verify again.');
      else if(error instanceof ApiError && error.status===409)setMessage('The catalog or save request changed. Refresh and review the configuration.');
      else setMessage('The backend could not confirm this action. A save can be retried with the same selections; no order was placed.');
    }finally{setBusy(false);}
  };
  return <section className="customer-drafts" aria-label="Protected local drafts">
    <h3>Save your configuration</h3>
    <p className="hint">Local synthetic access only. No real email is sent. Your demo drafts remain available until the demo backend stops.</p>
    {!authenticated ? <>
      <form onSubmit={e=>{e.preventDefault();void action(async()=>{
        await customerRequest('/api/v1/customer/request-code/','POST',{email},csrf);
        setRequested(true);setCode('');setMessage('Code captured. Read the newest private email file in the directory printed by the demo terminal.');
      });}}>
        <label htmlFor="customer-email">Synthetic email address</label>
        <input id="customer-email" type="email" autoComplete="off" placeholder="engineer@synthetic.invalid" value={email} onChange={e=>setEmail(e.target.value)} required disabled={!available||busy} />
        <button disabled={!available||busy} type="submit">Request verification code</button>
      </form>
      {requested && <form onSubmit={e=>{e.preventDefault();void action(async()=>{
        const session=await customerRequest('/api/v1/customer/verify/','POST',{code},csrf);
        setAuthenticated(true);setCsrf(session.csrf_token);setCode('');setEmail('');setRequested(false);pending.current=null;
        setMessage('Verified in this browser. You can now save or resume drafts.');await refresh();
      });}}>
        <label htmlFor="customer-code">Captured verification code</label>
        <input id="customer-code" type="password" autoComplete="one-time-code" value={code} onChange={e=>setCode(e.target.value)} required maxLength={128} disabled={busy}/>
        <button type="submit" disabled={busy}>Verify and continue</button>
      </form>}
    </> : <>
      <p>Verified customer session</p>
      <DraftCart configuration={configuration} csrf={csrf} onResume={onResume}/>
      <button type="button" disabled={busy||!evaluate(configuration).valid} onClick={()=>void action(async()=>{
        const payload=JSON.stringify(configuration);
        if(pending.current?.payload!==payload)pending.current={payload,id:crypto.randomUUID()};
        await customerRequest('/api/v1/configuration-drafts/','POST',{request_id:pending.current.id,revision:catalog.revision,configuration},csrf);
        setMessage('Configuration saved as a local draft. No order or rights were created.');await refresh();
      })}>Save configuration draft</button>
      <button type="button" disabled={busy} onClick={()=>void action(refresh)}>Refresh saved drafts</button>
      <ul>{drafts.map(d=><li key={d.id}><button type="button" disabled={busy} onClick={()=>void action(async()=>{
        const snapshot=await customerRequest('/api/v1/configuration-drafts/'+d.id+'/');
        if(snapshot.revision!==catalog.revision||!evaluate(snapshot.configuration).valid){setMessage('This draft requires review against the current catalog.');return;}
        onResume(snapshot.configuration);pending.current=null;setMessage('Saved configuration resumed. Purchase approvals remain pending.');
      })}>Resume draft · {new Date(d.created_at).toLocaleString()}</button></li>)}</ul>
      {drafts.length===0&&<p className="hint">No saved drafts yet. Only this verified customer’s latest 20 drafts are listed.</p>}
      <button type="button" disabled={busy} onClick={()=>void action(async()=>{
        const session=await customerRequest('/api/v1/customer/logout/','POST',{},csrf);
        setAuthenticated(false);setCsrf(session.csrf_token);setDrafts([]);setEmail('');setCode('');setRequested(false);pending.current=null;
        onResume(initialConfiguration());setMessage('Signed out. Saved drafts remain on the running local backend.');
      })}>Sign out</button>
    </>}
    <p role="status" aria-live="polite">{message}</p>
  </section>;
}
