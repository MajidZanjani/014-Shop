// Headless local browser-engine smoke. No Playwright dependency or production Node service.
import { Socket } from 'node:net';
import { spawn, execFileSync } from 'node:child_process';
import { readFile, readdir, mkdtemp, rm, realpath } from 'node:fs/promises';
import { join } from 'node:path';
import { setTimeout as delay } from 'node:timers/promises';
import { publicSmoke } from './browser_public.mjs';
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
    let checks=0;const publicChecks={};
    for (const [index,javascript] of [true,false].entries()) {
      stage='session-'+index;
      const {browserContextId}=await cdp.send('Target.createBrowserContext');
      const {targetId}=await cdp.send('Target.createTarget',{url:'about:blank',browserContextId});
      const {sessionId}=await cdp.send('Target.attachToTarget',{targetId,flatten:true});
      const send=(method,params) => cdp.send(method,params,sessionId);
      let escaped=0,blocked=0,cspDenied=0,lastDocumentStatus=0;
      const responseFault={url:null,armed:false,posts:[],dropped:0};
      cdp.events.push(event => {
        if (event.sessionId!==sessionId) return;
        if (event.method==='Network.responseReceived' && event.params.type==='Document') lastDocumentStatus=event.params.response.status;
        if (event.method==='Network.loadingFailed' && event.params.blockedReason==='csp' && event.params.type==='Image') cspDenied++;
        if (event.method!=='Fetch.requestPaused') return;
        const {requestId,request}=event.params;
        const allowed=allowedRequest(request.url,config.origin) || allowedRequest(request.url,config.staff.origin);
        if (!allowed) {blocked++; if (request.url!=='https://browser-egress-canary.invalid/pixel') escaped++;}
        const responseStage=event.params.responseStatusCode!==undefined || event.params.responseErrorReason!==undefined;
        if(allowed && responseFault.url===request.url && request.method==='POST') {
          if(!responseStage) {
            if(typeof request.postData!=='string' || request.postData.length>32768 || responseFault.posts.length>=2) {
              escaped++;void send('Fetch.failRequest',{requestId,errorReason:'BlockedByClient'});return;
            }
            responseFault.posts.push(request.postData);
          } else if(responseFault.armed && event.params.responseStatusCode>=200 && event.params.responseStatusCode<300) {
            responseFault.armed=false;responseFault.dropped++;
            void send('Fetch.failRequest',{requestId,errorReason:'ConnectionClosed'}).catch(()=>{escaped++;});return;
          }
        }
        send(allowed ? (responseStage?'Fetch.continueResponse':'Fetch.continueRequest'):'Fetch.failRequest',allowed ? {requestId}:{requestId,errorReason:'BlockedByClient'})
          .catch(() => {escaped++;});
      });
      stage='protocol-setup-'+index;
      await send('Page.enable'); await send('Runtime.enable'); await send('Network.enable');
      await send('Fetch.enable',{patterns:[{urlPattern:'*',requestStage:'Request'},...(config.frontend_toolchain?['/api/v1/cart/','/api/v1/quotation-requests/'].map(path=>({urlPattern:config.origin+path,requestStage:'Response'})):[])]});
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
      if (config.frontend_toolchain) {
        stage='public-'+index;
        publicChecks[javascript?'javascript':'no_javascript']=await publicSmoke({index,javascript,config,navigate,evaluate,wait,send,cdp,browserContextId,form,responseFault,mark:value=>{stage=value;}});
      }
      stage='probe-navigation-'+index;
      await navigate('/browser-fixture.html');
      stage='probe-script-mode-'+index;
      require(await evaluate('Boolean(window.shop_page_script_ran)')===javascript); checks++;
      const key=async (key,code,number) => {
        for(const type of ['keyDown','keyUp']) await send('Input.dispatchKeyEvent',{
          type,key,code,windowsVirtualKeyCode:number,nativeVirtualKeyCode:number,
          ...(type==='keyDown' && key==='Enter'?{text:'\r',unmodifiedText:'\r'}:{})});
      };
      const keyboardInput=async (selector,value,label,countChecks=true) => {
        stage='keyboard-'+label+'-'+index;
        await send('Page.bringToFront');
        const focused=`document.activeElement===document.querySelector(${JSON.stringify(selector)})`;
        for(let n=0;n<32 && !await evaluate(focused);n++) await key('Tab','Tab',9);
        stage='keyboard-reach-'+label+'-'+index;
        require(await evaluate(focused));
        stage='keyboard-focus-'+label+'-'+index;
        require(await evaluate(`(() => {const e=document.activeElement,s=getComputedStyle(e),r=e.getBoundingClientRect();
          return e.value==='' && e.matches(':focus-visible') && s.outlineStyle!=='none' && parseFloat(s.outlineWidth)>=2
            && r.width>0 && r.height>0 && r.top>=0 && r.bottom<=innerHeight+1;})()`));
        stage='keyboard-entry-'+label+'-'+index;
        await send('Input.insertText',{text:value});
        require(await evaluate(`document.activeElement.value===${JSON.stringify(value)}`));if(countChecks)checks++;
      };
      stage='login-'+index;
      await navigate('/purchase/access/');
      require(await evaluate('document.querySelector("h1")!==null && document.querySelector("main")!==null')); checks++;
      const before=new Set(await readdir(config.mailbox));
      await keyboardInput('input[name=email]',config.email,'email');
      stage='keyboard-request-submit-'+index;
      await key('Enter','Enter',13);
      await wait('document.querySelector("input[name=code]")!==null && document.readyState==="complete"');
      let added=[];
      for (let count=0; count<50; count++) {
        added=(await readdir(config.mailbox)).filter(name => !before.has(name));
        if (added.length) break; await delay(50);
      }
      require(added.length===1);
      const mail=await readFile(join(config.mailbox,added[0]),'utf8'); require(mail.length<16384);
      const code=mail.match(/^Verification code: ([A-Za-z0-9_-]+)$/m)?.[1]; require(code);
      const invalidCode='SYNTHETIC_KEYBOARD_INVALID_CODE';
      await keyboardInput('input[name=code]',invalidCode,'invalid-code');
      stage='keyboard-invalid-submit-'+index;
      await key('Enter','Enter',13);
      await wait('document.readyState==="complete" && document.querySelector("[role=alert]")!==null');
      stage='keyboard-invalid-denied-'+index;
      require(lastDocumentStatus===400 && await evaluate('document.querySelector("[role=alert]").innerText.includes("could not be verified") && !document.body.innerText.includes("Your customer access is verified.")'));checks++;
      require(await evaluate(`!document.body.innerText.includes(${JSON.stringify(invalidCode)}) && document.querySelector('input[name=code]').value==='' && !location.search && !location.hash`));checks++;
      await send('Accessibility.enable');
      const tree=await send('Accessibility.getFullAXTree');
      require(tree.nodes.some(n=>!n.ignored && n.role?.value==='alert'));checks++;
      await keyboardInput('input[name=code]',code,'valid-code');
      stage='keyboard-valid-submit-'+index;
      await key('Enter','Enter',13);
      await wait('document.body.innerText.includes("Your customer access is verified.")'); checks++;
      stage='business-validation-'+index;
      await navigate('/purchase/business/');
      const businessRevision=await evaluate('document.querySelector("input[name=expected_version]").value');
      await form('form[action="/purchase/business/"]',{business_email:'SYNTHETIC_REJECTED@example.com'});
      require(lastDocumentStatus===422 && await evaluate('document.querySelector("input[name=expected_version]").value')===businessRevision);checks++;
      require(await evaluate(`(() => {const f=document.querySelector('#id_business_email');return f.value==='' && f.getAttribute('aria-invalid')==='true' && document.getElementById(f.getAttribute('aria-describedby')).innerText.includes('.invalid') && document.querySelector('[role=alert] a').getAttribute('href')==='#id_business_email' && !document.body.innerText.includes('SYNTHETIC_REJECTED@example.com') && !location.search;})()`));checks++;
      await send('Accessibility.enable');
      const businessTree=await send('Accessibility.getFullAXTree');
      require(businessTree.nodes.some(n=>!n.ignored && n.role?.value==='alert'));checks++;
      await send('Emulation.setDeviceMetricsOverride',{width:320,height:900,deviceScaleFactor:1,mobile:false});
      require(await evaluate('document.documentElement.scrollWidth<=innerWidth+1 && [...document.styleSheets].some(s=>s.href?.includes("/purchase/assets/shop.css"))'));checks++;
      await send('Emulation.setDeviceMetricsOverride',{width:javascript?1280:390,height:900,deviceScaleFactor:1,mobile:!javascript});
      stage='cart-current-entry-'+index;
      await navigate('/purchase/cart/');
      const cartRevision=await evaluate('document.querySelector("form:has(input[value=add_ip]) input[name=expected_version]").value');
      const cartLines=await evaluate('document.querySelectorAll("ol.cart-items>li").length');
      await evaluate('(() => {const f=document.querySelector("form:has(input[value=add_ip])");f.noValidate=true;f.querySelector("input[name=families][value=altera-agilex-5]").checked=true;return true;})()');
      await form('form:has(input[value=add_ip])',{vendor:'altera',term:'rd-annual',fixed_nodes:'1',floating_nodes:'0',platform_choice:''});
      require(lastDocumentStatus===422
        && await evaluate('document.querySelector("form:has(input[value=add_ip]) input[name=expected_version]").value')===cartRevision
        && await evaluate('document.querySelectorAll("ol.cart-items>li").length')===cartLines);checks++;
      await evaluate('document.querySelector("form:has(input[value=add_support])").noValidate=true;true');
      await form('form:has(input[value=add_support])',{quantity:'0'});
      require(lastDocumentStatus===422
        && await evaluate('document.querySelector("form:has(input[value=add_ip]) input[name=expected_version]").value')===cartRevision
        && await evaluate('document.querySelectorAll("ol.cart-items>li").length')===cartLines);checks++;
      stage='checkout-preview-'+index;
      await navigate('/purchase/checkout-rehearsal/');
      const checkoutHash=await evaluate('document.querySelector("input[name=sha256]").value');
      require(lastDocumentStatus===200 && /^[0-9a-f]{64}$/.test(checkoutHash) && await evaluate('document.body.innerText.includes("does not accept terms, place an order, take payment or grant licence or support rights")'));checks++;
      stage='checkout-reflow-'+index;
      await send('Emulation.setDeviceMetricsOverride',{width:320,height:900,deviceScaleFactor:1,mobile:false});
      require(await evaluate('document.documentElement.scrollWidth<=innerWidth+1 && [...document.styleSheets].some(s=>s.href?.includes("/purchase/assets/shop.css"))'));checks++;
      await send('Page.bringToFront');
      const checkoutButton='document.querySelector("form[action=\'/purchase/checkout-rehearsal/\'] button")';
      // Only the submitted digest is changed; the existing reviewed fixture is never captured.
      await evaluate('document.querySelector("input[name=sha256]").value="0".repeat(64);true');
      for(let n=0;n<32 && !await evaluate(`document.activeElement===${checkoutButton}`);n++) await key('Tab','Tab',9);
      stage='checkout-keyboard-focus-'+index;
      require(await evaluate(`document.activeElement===${checkoutButton} && document.activeElement.matches(':focus-visible') && parseFloat(getComputedStyle(document.activeElement).outlineWidth)>=2`));checks++;
      await key('Enter','Enter',13);
      await wait('document.readyState==="complete" && document.querySelector("[role=alert]")!==null');
      stage='checkout-stale-denied-'+index;
      await send('Accessibility.enable');
      const checkoutTree=await send('Accessibility.getFullAXTree');
      require(lastDocumentStatus===409 && checkoutTree.nodes.some(n=>!n.ignored && n.role?.value==='alert') && await evaluate('document.querySelector("[role=alert]").innerText.includes("Checkout held") && document.querySelector("form[action=\'/purchase/checkout-rehearsal/\']")===null && !document.body.innerText.includes("0".repeat(64)) && !location.search'));checks++;
      await navigate('/purchase/checkout-rehearsal/');
      require(lastDocumentStatus===200 && await evaluate('document.querySelector("input[name=sha256]").value')===checkoutHash);checks++;
      await send('Emulation.setDeviceMetricsOverride',{width:javascript?1280:390,height:900,deviceScaleFactor:1,mobile:!javascript});
      stage='payment-retained-'+index;
      const paymentPath='/purchase/checkout-rehearsal/'+config.checkout_id+'/payment/';
      await navigate(paymentPath);
      require(lastDocumentStatus===200 && await evaluate('document.body.innerText.includes("Simulated payment captured") && document.body.innerText.includes("No real contract, payment, licence or support credit is created")'));checks++;
      await send('Emulation.setDeviceMetricsOverride',{width:320,height:900,deviceScaleFactor:1,mobile:false});
      require(await evaluate('document.documentElement.scrollWidth<=innerWidth+1'));checks++;
      stage='payment-error-'+index;
      await send('Page.navigate',{url:config.origin+paymentPath+'?invalid=synthetic'});
      await wait('location.search==="?invalid=synthetic" && document.readyState==="complete" && document.querySelector("[role=alert]")!==null');
      await send('Accessibility.enable');
      const paymentTree=await send('Accessibility.getFullAXTree');
      require(lastDocumentStatus===400 && paymentTree.nodes.some(n=>!n.ignored && n.role?.value==='alert') && await evaluate('document.querySelector("[role=alert]").innerText.includes("does not accept query parameters") && !document.body.innerText.includes("unexpected_query") && document.querySelectorAll("form").length===0'));checks++;
      stage='payment-keyboard-recovery-'+index;
      await send('Page.bringToFront');
      const paymentLink=`document.querySelector('a[href="${paymentPath}"]')`;
      for(let n=0;n<32 && !await evaluate(`document.activeElement===${paymentLink}`);n++) await key('Tab','Tab',9);
      require(await evaluate(`document.activeElement===${paymentLink} && document.activeElement.matches(':focus-visible') && parseFloat(getComputedStyle(document.activeElement).outlineWidth)>=2 && document.documentElement.scrollWidth<=innerWidth+1`));checks++;
      await key('Enter','Enter',13);
      await wait('location.search==="" && document.readyState==="complete" && document.body.innerText.includes("Simulated payment captured")');
      require(lastDocumentStatus===200 && await evaluate('document.body.innerText.includes("Real payment confirmation and licence/support effects remain disabled")'));checks++;
      await send('Emulation.setDeviceMetricsOverride',{width:javascript?1280:390,height:900,deviceScaleFactor:1,mobile:!javascript});
      const supportRecovery=async (origin,path,label) => {
        stage='support-recovery-'+label+'-'+index;
        const revision=await evaluate('document.body.innerText.match(/Committed ledger revision ([0-9]+)/)[1]');
        await send('Page.navigate',{url:origin+path+'?invalid=synthetic'});
        await wait('location.search==="?invalid=synthetic" && document.readyState==="complete" && document.querySelector("[role=alert]")!==null');
        await send('Accessibility.enable');
        const tree=await send('Accessibility.getFullAXTree');
        require(lastDocumentStatus===400 && tree.nodes.some(n=>!n.ignored && n.role?.value==='alert') && await evaluate('document.querySelector("[role=alert]").innerText.includes("does not accept query parameters") && !document.body.innerText.includes("unexpected_query") && document.querySelectorAll("form").length===0'));checks++;
        const link=`[...document.querySelectorAll('a')].find(a=>a.innerText==='Reload committed support status')`;
        require(await evaluate(`${link}.getAttribute('href')===${JSON.stringify(path)}`));checks++;
        await send('Emulation.setDeviceMetricsOverride',{width:320,height:900,deviceScaleFactor:1,mobile:false});
        await send('Page.bringToFront');
        for(let n=0;n<32 && !await evaluate(`document.activeElement===${link}`);n++) await key('Tab','Tab',9);
        require(await evaluate(`document.activeElement===${link} && document.activeElement.matches(':focus-visible') && parseFloat(getComputedStyle(document.activeElement).outlineWidth)>=2 && document.documentElement.scrollWidth<=innerWidth+1`));checks++;
        await key('Enter','Enter',13);
        await wait('location.search==="" && document.readyState==="complete" && document.body.innerText.includes("Committed ledger revision")');
        require(lastDocumentStatus===200 && await evaluate('document.body.innerText.match(/Committed ledger revision ([0-9]+)/)[1]')===revision && await evaluate('document.body.innerText.includes("Available: 70200")'));checks++;
        await send('Emulation.setDeviceMetricsOverride',{width:javascript?1280:390,height:900,deviceScaleFactor:1,mobile:!javascript});
      };
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
      await supportRecovery(config.origin,config.support,'customer');
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
      const staffReflow=async (label,countChecks) => {
        stage='staff-reflow-'+label+'-'+index;
        await send('Emulation.setDeviceMetricsOverride',{width:320,height:900,deviceScaleFactor:1,mobile:false});
        require(await evaluate('innerWidth===320 && document.documentElement.scrollWidth<=innerWidth+1'));
        if(countChecks)checks++;
        await send('Emulation.setDeviceMetricsOverride',{width:javascript?1280:390,height:900,deviceScaleFactor:1,mobile:!javascript});
      };
      const staffLogin=async (countChecks=true) => {
        stage='staff-password-'+index;
        await staffNavigate('/staff/');
        const staffBefore=new Set(await readdir(config.staff.capture));
        await staffReflow('password',countChecks);
        await keyboardInput('input[name=username]',config.staff.actors[index].username,'staff-username',countChecks);
        await keyboardInput('input[name=password]',config.staff.actors[index].password,'staff-password',countChecks);
        stage='staff-keyboard-password-submit-'+index;
        await key('Enter','Enter',13);
        await wait('document.readyState==="complete" && document.querySelector("input[name=code]")!==null');
        require(await evaluate('document.querySelector("input[name=code]")!==null')); if (countChecks) checks++;
        const staffAdded=(await readdir(config.staff.capture)).filter(name => !staffBefore.has(name));
        require(staffAdded.length===1);
        const staffMail=await readFile(join(config.staff.capture,staffAdded[0]),'utf8'); require(staffMail.length<16384);
        const staffCode=staffMail.match(/^Code: ([A-Za-z0-9_-]+)$/m)?.[1]; require(staffCode);
        await staffNavigate(config.staff.support);
        require(lastDocumentStatus===403); if (countChecks) checks++;
        stage='staff-second-factor-'+index;
        await staffNavigate('/staff/');
        await staffReflow('challenge',countChecks);
        const badStaffCode='SYNTHETIC_STAFF_KEYBOARD_INVALID';
        await keyboardInput('input[name=code]',badStaffCode,'staff-invalid-code',countChecks);
        stage='staff-keyboard-invalid-submit-'+index;
        await key('Enter','Enter',13);
        await wait('document.readyState==="complete" && document.querySelector("[role=alert]")!==null');
        require(lastDocumentStatus===400 && await evaluate('!document.body.innerText.includes("Both local factors verified.")'));if(countChecks)checks++;
        const staffAlert=await send('Accessibility.getFullAXTree');
        require(staffAlert.nodes.some(n=>!n.ignored && n.role?.value==='alert'));if(countChecks)checks++;
        require(await evaluate(`document.querySelector('input[name=code]').value==='' && !document.body.innerText.includes(${JSON.stringify(badStaffCode)}) && !location.search && !location.hash`));if(countChecks)checks++;
        await staffNavigate(config.staff.support);
        require(lastDocumentStatus===403);if(countChecks)checks++;
        await staffNavigate('/staff/');
        await keyboardInput('input[name=code]',staffCode,'staff-code',countChecks);
        stage='staff-keyboard-code-submit-'+index;
        await key('Enter','Enter',13);
        await wait('document.body.innerText.includes("Both local factors verified.")');
        require(await evaluate('document.body.innerText.includes("Both local factors verified.")')); if (countChecks) checks++;
      };
      await staffLogin();
      await staffNavigate(config.staff.support);
      require(lastDocumentStatus===200 && await evaluate('document.body.innerText.includes("Available: 70200") && document.body.innerText.includes("Optional private support follow-up")')); checks++;
      await supportRecovery(config.staff.origin,config.staff.support,'staff');
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
      browser_sandbox:'disabled-for-owned-local-root-smoke',
      ...(config.frontend_toolchain?{public_checks:publicChecks,frontend_toolchain:config.frontend_toolchain}:{})};
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
