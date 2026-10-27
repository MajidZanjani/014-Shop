// Headless local browser-engine smoke. No Playwright dependency or production Node service.
import { Socket } from 'node:net';
import { spawn, execFileSync } from 'node:child_process';
import { readFile, readdir, mkdtemp, rm, realpath } from 'node:fs/promises';
import { join } from 'node:path';
import { setTimeout as delay } from 'node:timers/promises';
import { allowedRequest } from './browser_policy.mjs';
let stage = 'startup';
const require = value => { if (!value) throw new Error('local browser assertion'); };
class Protocol {
  constructor(socket) {
    this.socket=socket; this.serial=0; this.pending=new Map(); this.events=[];
    socket.addEventListener('message', event => {
      const value=JSON.parse(event.data);
      if (value.id) {
        const request=this.pending.get(value.id); if (!request) return;
        clearTimeout(request.timer); this.pending.delete(value.id);
        if (value.error) {stage='protocol-'+request.method;request.reject(new Error('protocol refused'));}
        else request.resolve(value.result);
      } else for (const handler of this.events) handler(value);
    });
  }
  send(method, params={}, sessionId) {
    const id=++this.serial;
    return new Promise((resolve,reject) => {
      const timer=setTimeout(() => {this.pending.delete(id); reject(new Error('protocol timeout'));},5000);
      this.pending.set(id,{resolve,reject,timer,method});
      this.socket.send(JSON.stringify({id,method,params,...(sessionId ? {sessionId}: {})}));
    });
  }
}
async function connect(url) {
  const socket=new WebSocket(url);
  await new Promise((resolve,reject) => {
    socket.addEventListener('open',resolve,{once:true}); socket.addEventListener('error',reject,{once:true});
    setTimeout(() => reject(new Error('connection timeout')),5000).unref();
  });
  return new Protocol(socket);
}
async function smoke() {
  const config=JSON.parse(await readFile(process.argv[2],'utf8'));
  require(process.versions.node === process.env.SHOP_BROWSER_NODE_VERSION);
  require(await realpath(process.execPath) === await realpath(process.env.SHOP_NODE));
  const browser=process.env.SHOP_BROWSER, version=process.env.SHOP_BROWSER_VERSION;
  require(browser?.startsWith('/nix/store/') && version);
  require(execFileSync(browser,['--version'],{timeout:10000,encoding:'utf8'}).trim().includes(version));
  const control=new Socket({fd:Number(process.env.SHOP_BROWSER_CONTROL_FD),readable:true,writable:true});
  control.on('error',() => {});
  const operator=async (index,action) => {
    await new Promise((resolve,reject) => {
      let response='';
      const cleanup=() => {clearTimeout(timer);control.off('data',data);control.off('error',fail);control.off('end',fail);};
      const fail=() => {cleanup();reject(new Error('operator refused'));};
      const data=chunk => {
        response+=chunk.toString('utf8');
        if (response.length>128) return fail();
        if (response.endsWith('\n')) {
          cleanup();
          if (response!=='{"ok":true}\n') reject(new Error('operator refused')); else resolve();
        }
      };
      const timer=setTimeout(fail,15000);
      control.on('data',data);control.once('error',fail);control.once('end',fail);
      control.write(JSON.stringify({index,action})+'\n');
    });
  };
  const profile=await mkdtemp(join(config.scratch,'chromium-'));
  const child=spawn(browser,['--headless','--disable-gpu','--no-sandbox','--no-first-run',
    '--no-default-browser-check','--disable-background-networking','--disable-component-update',
    '--disable-sync','--disable-extensions','--disable-breakpad','--disable-features=MediaRouter',
    '--metrics-recording-only','--host-resolver-rules=MAP staff.localhost 127.0.0.1, MAP * ~NOTFOUND, EXCLUDE localhost, EXCLUDE 127.0.0.1',
    '--remote-debugging-address=127.0.0.1','--remote-debugging-port=0','--user-data-dir='+profile,'about:blank'],
    {env:{...process.env,XDG_CONFIG_HOME:join(profile,'config'),XDG_CACHE_HOME:join(profile,'cache')},stdio:'ignore'});
  let cdp;
  try {
    stage='browser-ready'; let lines;
    for (let count=0; count<100; count++) {
      require(child.exitCode===null && child.signalCode===null);
      try { lines=(await readFile(join(profile,'DevToolsActivePort'),'utf8')).trim().split('\n'); break; } catch { await delay(50); }
    }
    require(lines?.length===2 && /^\d+$/.test(lines[0]));
    cdp=await connect('ws://127.0.0.1:'+lines[0]+lines[1]);
    let checks=0;
    for (const [index,javascript] of [true,false].entries()) {
      stage='session-'+index;
      const {browserContextId}=await cdp.send('Target.createBrowserContext');
      const {targetId}=await cdp.send('Target.createTarget',{url:'about:blank',browserContextId});
      const {sessionId}=await cdp.send('Target.attachToTarget',{targetId,flatten:true});
      const send=(method,params) => cdp.send(method,params,sessionId);
      let escaped=0,blocked=0,cspDenied=0,lastDocumentStatus=0;
      cdp.events.push(event => {
        if (event.sessionId!==sessionId) return;
        if (event.method==='Network.responseReceived' && event.params.type==='Document') lastDocumentStatus=event.params.response.status;
        if (event.method==='Network.loadingFailed' && event.params.blockedReason==='csp' && event.params.type==='Image') cspDenied++;
        if (event.method!=='Fetch.requestPaused') return;
        const {requestId,request}=event.params;
        const allowed=allowedRequest(request.url,config.origin) || allowedRequest(request.url,config.staff.origin);
        if (!allowed) {blocked++; if (request.url!=='https://browser-egress-canary.invalid/pixel') escaped++;}
        send(allowed ? 'Fetch.continueRequest':'Fetch.failRequest',allowed ? {requestId}:{requestId,errorReason:'BlockedByClient'})
          .catch(() => {escaped++;});
      });
      stage='protocol-setup-'+index;
      await send('Page.enable'); await send('Runtime.enable'); await send('Network.enable');
      await send('Fetch.enable',{patterns:[{urlPattern:'*',requestStage:'Request'}]});
      await send('Emulation.setDeviceMetricsOverride',{width:javascript ? 1280:390,height:900,deviceScaleFactor:1,mobile:!javascript});
      await send('Emulation.setScriptExecutionDisabled',{value:!javascript});
      const evaluate=async expression => {
        const result=await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});
        require(!result.exceptionDetails); return result.result.value;
      };
      const wait=async predicate => {
        for (let count=0; count<100; count++) {
          try {if (await evaluate(predicate)) return;} catch { /* navigation can replace the execution context */ }
          await delay(50);
        }
        throw new Error('bounded page wait');
      };
      const navigateTo=async (origin,path) => {
        await send('Page.navigate',{url:origin+path});
        await wait('location.origin==='+JSON.stringify(origin)+' && location.pathname==='+JSON.stringify(path)+' && document.readyState==="complete"');
      };
      const navigate=path => navigateTo(config.origin,path);
      const staffNavigate=path => navigateTo(config.staff.origin,path);
      const form=async (selector,values) => {
        const loader=(await send('Page.getFrameTree')).frameTree.frame.loaderId;
        await evaluate(`(() => { const f=document.querySelector(${JSON.stringify(selector)}); if (!f) throw Error();
          for (const [name,value] of Object.entries(${JSON.stringify(values)})) {const e=f.elements.namedItem(name); if (!e) throw Error(); e.value=value;}
          f.requestSubmit(); return true; })()`);
        let navigated=false;
        for (let count=0; count<100; count++) {
          if ((await send('Page.getFrameTree')).frameTree.frame.loaderId!==loader) {navigated=true;break;}
          await delay(50);
        }
        require(navigated); await wait('document.readyState==="complete"');
      };
      stage='probe-navigation-'+index;
      await navigate('/browser-fixture.html');
      stage='probe-script-mode-'+index;
      require(await evaluate('Boolean(window.shop_page_script_ran)')===javascript); checks++;
      stage='login-'+index;
      await navigate('/purchase/access/');
      require(await evaluate('document.querySelector("h1")!==null && document.querySelector("main")!==null')); checks++;
      const before=new Set(await readdir(config.mailbox));
      await form('form:has(input[value="request"])',{email:config.email});
      await wait('document.querySelector("input[name=code]")!==null && document.readyState==="complete"');
      let added=[];
      for (let count=0; count<50; count++) {
        added=(await readdir(config.mailbox)).filter(name => !before.has(name));
        if (added.length) break; await delay(50);
      }
      require(added.length===1);
      const mail=await readFile(join(config.mailbox,added[0]),'utf8'); require(mail.length<16384);
      const code=mail.match(/^Verification code: ([A-Za-z0-9_-]+)$/m)?.[1]; require(code);
      await form('form:has(input[value="verify"])',{code});
      await wait('document.body.innerText.includes("Your customer access is verified.")'); checks++;
      stage='support-'+index;
      await navigate(config.support);
      require(await evaluate('document.body.innerText.includes("Optional private support follow-up") && document.body.innerText.includes("Available: 70200")')); checks++;
      require(await evaluate('document.documentElement.scrollWidth<=innerWidth+1')); checks++;
      require(await evaluate(`document.documentElement.lang && document.title.trim() && document.querySelectorAll('h1').length===1
        && [...document.querySelectorAll('input:not([type=hidden]),select,textarea,button')].every(element =>
          element.disabled || element.getAttribute('aria-label') || element.getAttribute('aria-labelledby')
          || element.labels?.length || (element.tagName==='BUTTON' && element.textContent.trim()))`)); checks++;
      await send('Input.dispatchKeyEvent',{type:'keyDown',key:'Tab',code:'Tab',windowsVirtualKeyCode:9,nativeVirtualKeyCode:9});
      await send('Input.dispatchKeyEvent',{type:'keyUp',key:'Tab',code:'Tab',windowsVirtualKeyCode:9,nativeVirtualKeyCode:9});
      require(await evaluate(`(() => {const element=document.activeElement; const bounds=element.getBoundingClientRect();
        return element.matches('a,button,input,select,textarea') && bounds.width>0 && bounds.height>0
          && getComputedStyle(element).outlineStyle!=='none';})()`)); checks++;
      const initial=await evaluate('Number(document.querySelector("input[name=expected_revision]").value)');
      const requestId=await evaluate('document.querySelector("form:has(input[value=context]) input[name=request_id]").value');
      await form('form:has(input[value="context"])',{fixture:'synthetic-context-v2'});
      await wait('Number(document.querySelector("input[name=expected_revision]")?.value)==='+String(initial+1)); checks++;
      await form('form:has(input[value="context"])',{fixture:'synthetic-context-v2',request_id:requestId,expected_revision:String(initial)});
      await wait('document.readyState==="complete" && Number(document.querySelector("input[name=expected_revision]")?.value)==='+String(initial+1)); checks++;
      require(await evaluate('document.body.innerText.includes("Spent: 1800") && document.body.innerText.includes("Available: 70200")')); checks++;
      stage='customer-staff-boundary-'+index;
      await staffNavigate(config.staff.support);
      require(lastDocumentStatus===403 && await evaluate('!document.body.innerText.includes("Available: 70200")')); checks++;
      await navigate(config.support);
      stage='privacy-storage-'+index;
      require(await evaluate('localStorage.length===0 && sessionStorage.length===0 && !location.search && !location.hash')); checks++;
      stage='privacy-cookie-'+index;
      const cookies=await cdp.send('Storage.getCookies',{browserContextId});
      require(cookies.cookies.some(cookie => cookie.name===config.session_cookie && cookie.httpOnly)); checks++;
      stage='privacy-egress-'+index;
      await evaluate('document.body.appendChild(Object.assign(document.createElement("img"),{src:"https://browser-egress-canary.invalid/pixel"})); true');
      for (let count=0; count<50 && !cspDenied; count++) await delay(20);
      require(cspDenied===1 && blocked===0 && escaped===0); checks++;
      // Top-level canary navigation separately exercises interception before DNS/network.
      await send('Page.navigate',{url:'https://browser-egress-canary.invalid/pixel'});
      for (let count=0; count<50 && !blocked; count++) await delay(20);
      require(blocked===1 && escaped===0); checks++;
      stage='logout-'+index;
      await navigate('/purchase/access/');
      await form('form:has(input[value="logout"])',{});
      require(await evaluate('document.querySelector("input[name=email]")!==null && !document.body.innerText.includes("Your customer access is verified.")')); checks++;
      await navigate(config.support);
      require(lastDocumentStatus===401 && await evaluate('!document.body.innerText.includes("Available: 70200") && !document.body.innerText.includes("Synthetic prototype")')); checks++;
      const staffLogin=async (countChecks=true) => {
        stage='staff-password-'+index;
        await staffNavigate('/staff/');
        const staffBefore=new Set(await readdir(config.staff.capture));
        await form('form[action="/staff/login/"]',{username:config.staff.actors[index].username,password:config.staff.actors[index].password});
        require(await evaluate('document.querySelector("input[name=code]")!==null')); if (countChecks) checks++;
        const staffAdded=(await readdir(config.staff.capture)).filter(name => !staffBefore.has(name));
        require(staffAdded.length===1);
        const staffMail=await readFile(join(config.staff.capture,staffAdded[0]),'utf8'); require(staffMail.length<16384);
        const staffCode=staffMail.match(/^Code: ([A-Za-z0-9_-]+)$/m)?.[1]; require(staffCode);
        await staffNavigate(config.staff.support);
        require(lastDocumentStatus===403); if (countChecks) checks++;
        stage='staff-second-factor-'+index;
        await staffNavigate('/staff/');
        await form('form[action="/staff/verify/"]',{code:staffCode});
        require(await evaluate('document.body.innerText.includes("Both local factors verified.")')); if (countChecks) checks++;
      };
      await staffLogin();
      await staffNavigate(config.staff.support);
      require(lastDocumentStatus===200 && await evaluate('document.body.innerText.includes("Available: 70200") && document.body.innerText.includes("Optional private support follow-up")')); checks++;
      await staffNavigate(config.staff.unassigned);
      require(lastDocumentStatus===404 && await evaluate('!document.body.innerText.includes("Optional private support follow-up")')); checks++;
      await staffNavigate('/staff/');
      const staffCookies=await cdp.send('Storage.getCookies',{browserContextId});
      require(staffCookies.cookies.some(cookie => cookie.name===config.staff.session_cookie && cookie.httpOnly)
        && await evaluate('localStorage.length===0 && sessionStorage.length===0 && !location.search && !location.hash')); checks++;
      const staffCookie=async () => (await cdp.send('Storage.getCookies',{browserContextId})).cookies
        .find(cookie => cookie.name===config.staff.session_cookie)?.value;
      const scopeCookie=await staffCookie(); require(scopeCookie);
      stage='staff-scope-revoke-'+index;
      await operator(index,'revoke-support');
      await staffNavigate(config.staff.support);
      require(lastDocumentStatus===404 && await staffCookie()===scopeCookie
        && await evaluate('!document.body.innerText.includes("Available: 70200")')); checks++;
      stage='staff-scope-regrant-'+index;
      await operator(index,'grant-support');
      await staffNavigate(config.staff.support);
      require(lastDocumentStatus===200 && await staffCookie()===scopeCookie
        && await evaluate('document.body.innerText.includes("Available: 70200")')); checks++;
      await staffNavigate('/staff/');
      stage='staff-logout-'+index;
      await form('form[action="/staff/logout/"]',{});
      await staffNavigate(config.staff.support);
      require(lastDocumentStatus===403 && escaped===0 && blocked===1 && await evaluate('!document.body.innerText.includes("Available: 70200")')); checks++;
      // Reauthenticate through both supported forms after the ordinary logout check.
      await staffLogin(false);
      const staleCookie=await staffCookie(); require(staleCookie);
      stage='staff-credential-revoke-'+index;
      await operator(index,'revoke');
      await staffNavigate(config.staff.support);
      require(lastDocumentStatus===403 && await staffCookie()===staleCookie
        && await evaluate('!document.body.innerText.includes("Available: 70200")')); checks++;
      await cdp.send('Target.disposeBrowserContext',{browserContextId});
    }
    control.end();
    return {status:'BROWSER_LOCAL_PASS',checks,modes:2,roles:2,browser_version:version,node_version:process.versions.node,
      evidence_class:'local-synthetic-browser-engine',formal_accessibility:false,production_qualified:false,
      browser_sandbox:'disabled-for-owned-local-root-smoke'};
  } finally {
    control.destroy();
    cdp?.socket.close(); child.kill('SIGTERM');
    for (let count=0; count<50 && child.exitCode===null && child.signalCode===null; count++) await delay(50);
    if (child.exitCode===null && child.signalCode===null) child.kill('SIGKILL');
    await rm(profile,{recursive:true,force:true});
  }
}
try { console.log(JSON.stringify(await smoke())); }
catch { console.error('BROWSER_ENGINE_FAIL stage='+stage); process.exitCode=1; }
