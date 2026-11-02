// Real loopback Chromium SHB form/selector checks. No browser dependencies or app Node service.
import { spawn, execFileSync } from 'node:child_process';
import { readFile, writeFile, mkdtemp, rm, realpath } from 'node:fs/promises';
import { join } from 'node:path';
import { setTimeout as delay } from 'node:timers/promises';
import { allowedRequest } from './browser_policy.mjs';
let stage='startup';
const require=value=>{if(!value)throw new Error('SHB browser assertion');};

class Protocol {
  constructor(socket){
    this.socket=socket;this.serial=0;this.pending=new Map();this.events=[];
    socket.addEventListener('message',event=>{
      const value=JSON.parse(event.data);
      if(value.id){const pending=this.pending.get(value.id);if(!pending)return;clearTimeout(pending.timer);this.pending.delete(value.id);value.error?pending.reject(new Error('protocol refused')):pending.resolve(value.result);}
      else for(const handler of this.events)handler(value);
    });
  }
  send(method,params={},sessionId){
    const id=++this.serial;
    return new Promise((resolve,reject)=>{
      const timer=setTimeout(()=>{this.pending.delete(id);reject(new Error('protocol timeout'));},5000);
      this.pending.set(id,{resolve,reject,timer});this.socket.send(JSON.stringify({id,method,params,...(sessionId?{sessionId}:{})}));
    });
  }
}

async function main(){
  let input='';for await(const chunk of process.stdin){input+=chunk;require(input.length<=8192);}
  const config=JSON.parse(input);input='';
  require(/^SLL-[A-Z2-9]{24}$/.test(config.discountCode));
  require(config.offerIds?.length===2&&config.offerIds.every(id=>/^[a-f0-9-]{36}$/.test(id)));
  require(allowedRequest(config.invitationUrl,config.origin));
  require(new URL(config.invitationUrl).pathname.match(/^\/invite\/[A-Za-z0-9_-]{43}$/));
  require(process.versions.node===process.env.SHOP_BROWSER_NODE_VERSION);
  require(await realpath(process.execPath)===await realpath(process.env.SHOP_NODE));
  const browser=process.env.SHOP_BROWSER,version=process.env.SHOP_BROWSER_VERSION;
  require(browser?.startsWith('/nix/store/')&&version&&execFileSync(browser,['--version'],{timeout:10000,encoding:'utf8'}).includes(version));
  const profile=await mkdtemp(join(config.scratch,'chromium-'));
  const child=spawn(browser,['--headless','--disable-gpu','--no-sandbox','--no-first-run','--no-default-browser-check',
    '--disable-background-networking','--disable-component-update','--disable-sync','--disable-extensions','--disable-breakpad',
    '--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE localhost, EXCLUDE 127.0.0.1',
    '--remote-debugging-address=127.0.0.1','--remote-debugging-port=0','--user-data-dir='+profile,'about:blank'],
    {env:{...process.env,XDG_CONFIG_HOME:join(profile,'config'),XDG_CACHE_HOME:join(profile,'cache')},stdio:['ignore','ignore','pipe']});
  let cdp;let checks=0;let pendingDocumentLoads=0;let startup='';let diagnose;
  child.stderr.on('data',chunk=>{if(!cdp&&startup.length<8192)startup+=chunk.toString('utf8');});
  try{
    stage='browser-ready';let lines;
    for(let index=0;index<100;index++){
      require(child.exitCode===null&&child.signalCode===null);
      try{lines=(await readFile(join(profile,'DevToolsActivePort'),'utf8')).trim().split('\n');break;}catch{await delay(50);}
    }
    require(lines?.length===2&&/^\d+$/.test(lines[0]));
    const socket=new WebSocket('ws://127.0.0.1:'+lines[0]+lines[1]);
    await new Promise((resolve,reject)=>{socket.addEventListener('open',resolve,{once:true});socket.addEventListener('error',reject,{once:true});setTimeout(()=>reject(new Error('connect timeout')),5000).unref();});
    cdp=new Protocol(socket);
    for(const javascript of [true,false]){
      stage=javascript?'javascript':'no-javascript';
      const {browserContextId}=await cdp.send('Target.createBrowserContext');
      const {targetId}=await cdp.send('Target.createTarget',{url:'about:blank',browserContextId});
      const {sessionId}=await cdp.send('Target.attachToTarget',{targetId,flatten:true});
      const send=(method,params)=>cdp.send(method,params,sessionId);
      let escaped=0,nativePosts=0,paymentPosts=0,lastStatus=0;
      cdp.events.push(event=>{
        if(event.sessionId!==sessionId)return;
        if(event.method==='Network.responseReceived'&&event.params.type==='Document')lastStatus=event.params.response.status;
        if(event.method!=='Fetch.requestPaused')return;
        const {requestId,request}=event.params;
        const allowed=allowedRequest(request.url,config.origin);
        if(!allowed)escaped++;
        if(allowed&&request.method==='POST'&&new URL(request.url).pathname==='/purchase/simple/')nativePosts++;
        if(allowed&&request.method==='POST'&&new URL(request.url).pathname.startsWith('/purchase/shb/'))paymentPosts++;
        void send(allowed?'Fetch.continueRequest':'Fetch.failRequest',allowed?{requestId}:{requestId,errorReason:'BlockedByClient'}).catch(()=>{escaped++;});
      });
      await send('Page.enable');await send('Runtime.enable');await send('Network.enable');
      await send('Network.setCacheDisabled',{cacheDisabled:true});
      await send('Fetch.enable',{patterns:[{urlPattern:'*',requestStage:'Request'}]});
      await send('Emulation.setScriptExecutionDisabled',{value:!javascript});
      await send('Emulation.setDeviceMetricsOverride',{width:320,height:850,deviceScaleFactor:1,mobile:false});
      const evaluate=async expression=>{
        const value=await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});
        require(!value.exceptionDetails);return value.result.value;
      };
      const until=async expression=>{for(let i=0;i<100;i++){if(await evaluate(expression))return;await delay(40);}throw new Error('page condition timeout');};
      // Diagnostics contain status/field names only, never values, URLs or tokens.
      diagnose=async()=>({stage,status:lastStatus,nativePosts,escaped,readyState:await evaluate('document.readyState'),stylesheets:await evaluate('document.styleSheets.length'),fields:await evaluate("Array.from(document.querySelectorAll('.errorlist')).map(element=>element.parentElement.querySelector('input,textarea,select')?.name).filter(name=>/^[a-z_]+$/.test(name||''))"),csrfDenied:await evaluate("document.body.innerText.includes('CSRF')")});
      const go=async url=>{
        lastStatus=0;const navigation=await send('Page.navigate',{url});
        require(!navigation.errorText&&navigation.loaderId);
        // The previous document can still report readyState=complete while the
        // next navigation is pending. Wait for this navigation's actual loader.
        let committed=false;
        for(let index=0;index<100;index++){
          const tree=await send('Page.getFrameTree');
          if(tree.frameTree.frame.loaderId===navigation.loaderId){committed=true;break;}
          await delay(40);
        }
        require(committed);await until("document.readyState==='complete'");await until('!!document.body');
      };
      const key=async(name,code,virtual,extra={})=>{await send('Input.dispatchKeyEvent',{type:'keyDown',key:name,code,windowsVirtualKeyCode:virtual,...(name==='Enter'?{text:'\r',unmodifiedText:'\r'}:{}),...extra});await send('Input.dispatchKeyEvent',{type:'keyUp',key:name,code,windowsVirtualKeyCode:virtual});};
      const focus=async selector=>require(await evaluate(`(()=>{const element=document.querySelector(${JSON.stringify(selector)});if(!element)return false;element.focus();return document.activeElement===element})()`));
      const type=async(selector,text)=>{await focus(selector);await key('a','KeyA',65,{modifiers:2});await send('Input.insertText',{text});};
      const toggle=async selector=>{await focus(selector);await key(' ','Space',32,{text:' '});};
      const submit=async selector=>{
        const before=(await send('Page.getFrameTree')).frameTree.frame.loaderId;
        await focus(selector);await key('Enter','Enter',13);
        let committed=false;
        for(let i=0;i<100;i++){
          if((await send('Page.getFrameTree')).frameTree.frame.loaderId!==before){committed=true;break;}
          await delay(40);
        }
        require(committed);await until('document.readyState==="complete"');
      };
      const fill=async({privacy=true}={})=>{
        for(const [name,text] of Object.entries({company_name:'Synthetic Company Limited',billing_address:'1 Synthetic Test Street',country:'GE',company_phone:'+995 555 010101',contact_name:'Synthetic Customer',contact_email:'buyer@synthetic.invalid'}))await type('[name='+name+']',text);
        await toggle('[name=same_phone]');if(privacy)await toggle('[name=privacy_acknowledged]');
      };
      await go(config.origin+'/shop/');await until('document.body.innerText.includes("Access requires")');require(lastStatus===403);checks++;
      await go(config.invitationUrl);await until('location.pathname==="/shop/"');
      require(lastStatus===200&&await evaluate('document.body.innerText.includes("Supporting Hours Bundle")'));checks++;
      require(await evaluate('localStorage.length===0&&sessionStorage.length===0'));checks++;
      if(javascript){
        stage='javascript-hydration';
        await until('!!document.querySelector("astro-island:not([ssr])")');checks++;
        await focus('#shb-variant');await key('ArrowDown','ArrowDown',40);
        await type('#shb-quantity','2');
        await until('document.body.innerText.includes("50 hours in this order")');checks++;
      }else{
        require(await evaluate('!!document.querySelector("noscript")'));checks++;
      }
      require(await evaluate('document.documentElement.scrollWidth<=document.documentElement.clientWidth'));checks++;
      if(config.evidence){const shot=await send('Page.captureScreenshot',{format:'png'});await writeFile(join(config.evidence,javascript?'shb-js.png':'shb-no-js.png'),Buffer.from(shot.data,'base64'),{flag:'wx',mode:0o600});}
      // Both modes use the same actual server form and native protected POST.
      stage=javascript?'javascript-asic-form':'no-javascript-asic-form';
      await go(config.origin+'/purchase/simple/?variant=shb-asic-25h&quantity=2');
      await until('!!document.querySelector("[name=assistance]")');await fill();await type('[name=assistance]','Review SLL IP integration');
      require(await evaluate('!document.querySelector("[name=accept_terms]")'));checks++;
      stage=javascript?'javascript-discount-apply':'no-javascript-discount-apply';
      await type('[name=discount_code]',config.discountCode);
      await submit('button[name=action][value=apply_discount]');
      await until('document.body.innerText.includes("Discount applied")');
      require(lastStatus===200&&await evaluate('document.body.innerText.includes("EUR 9,000.00")&&document.body.innerText.includes("50 hours in this order")'));checks++;
      stage=javascript?'javascript-discount-remove':'no-javascript-discount-remove';
      await submit('button[name=action][value=remove_discount]');
      await until('document.body.innerText.includes("Discount removed")');
      require(lastStatus===200&&await evaluate('document.querySelector("[name=discount_code]").value===""&&document.body.innerText.includes("EUR 10,000.00")'));checks++;
      await type('[name=discount_code]',config.discountCode);
      stage=javascript?'javascript-asic-post':'no-javascript-asic-post';
      await submit('button[name=action][value=submit]');
      await until('document.body.innerText.includes("ASIC request recorded")');
      require(lastStatus===200&&await evaluate('document.body.innerText.includes("50 requested hours")'));checks++;
      require(await evaluate('document.body.innerText.includes("Discount reserved for this request")&&document.body.innerText.includes("EUR 9,000.00")'));checks++;
      stage=javascript?'javascript-fpga-form':'no-javascript-fpga-form';
      await go(config.origin+'/purchase/simple/?variant=shb-fpga-10h&quantity=3');
      await until('!!document.querySelector("[name=company_name]")');require(await evaluate('!document.querySelector("[name=assistance]")'));checks++;
      await fill();await submit('button[name=action][value=review]');
      stage=javascript?'javascript-fpga-post':'no-javascript-fpga-post';
      await until('document.body.innerText.includes("30 hours in this order")');
      if(await evaluate('document.readyState!=="complete"'))pendingDocumentLoads++;
      await until('document.readyState==="complete"');
      stage=javascript?'javascript-fpga-price':'no-javascript-fpga-price';
      require(lastStatus===200&&await evaluate('document.body.innerText.includes("EUR 3,000.00")'));checks++;
      stage=javascript?'javascript-fpga-review':'no-javascript-fpga-review';
      require(await evaluate('!!document.querySelector("[name=review_digest]")&&!document.querySelector("[name=accept_terms]").checked&&!document.querySelector("[name=privacy_acknowledged]").checked'));checks++;
      stage=javascript?'javascript-fpga-layout':'no-javascript-fpga-layout';
      require(await evaluate('document.documentElement.scrollWidth<=document.documentElement.clientWidth'));checks++;
      stage=javascript?'javascript-fpga-storage':'no-javascript-fpga-storage';
      require(await evaluate('!document.querySelector("input[type=file]")&&localStorage.length===0&&sessionStorage.length===0'));checks++;
      stage=javascript?'javascript-fpga-requests':'no-javascript-fpga-requests';
      require(escaped===0&&nativePosts===4);checks++;
      stage=javascript?'javascript-fpga-checkout':'no-javascript-fpga-checkout';
      await toggle('[name=accept_terms]');await toggle('[name=privacy_acknowledged]');
      await submit('button[name=action][value=checkout]');
      require(lastStatus===200&&await evaluate('location.pathname.startsWith("/purchase/shb/")&&document.body.innerText.includes("30 hours in this order")&&document.body.innerText.includes("Payment has not started")'));checks++;
      stage=javascript?'javascript-fpga-payment':'no-javascript-fpga-payment';
      await submit('button[name=action][value=pay]');
      require(lastStatus===200&&await evaluate('document.body.innerText.includes("Payment state: observed")&&document.body.innerText.includes("Bank result: captured")&&document.body.innerText.includes("Paid purchase recorded")'));checks++;
      await submit('button[name=action][value=pay]');
      require(lastStatus===200&&escaped===0&&nativePosts===5&&paymentPosts===2);checks++;
      require(await evaluate('document.documentElement.scrollWidth<=document.documentElement.clientWidth&&localStorage.length===0&&sessionStorage.length===0'));checks++;
      stage=javascript?'javascript-fpga-cancel':'no-javascript-fpga-cancel';
      await go(config.origin+'/purchase/simple/?variant=shb-fpga-10h&quantity=1');
      await until('!!document.querySelector("[name=company_name]")');await fill();
      await submit('button[name=action][value=review]');
      await toggle('[name=accept_terms]');await toggle('[name=privacy_acknowledged]');
      await submit('button[name=action][value=checkout]');
      require(lastStatus===200&&await evaluate('!!document.querySelector("button[value=cancel]")'));checks++;
      await submit('button[name=action][value=cancel]');
      require(lastStatus===200&&await evaluate('document.body.innerText.includes("This unpaid checkout is closed")&&!document.querySelector("button[value=pay]")'));checks++;
      require(await evaluate('document.documentElement.scrollWidth<=document.documentElement.clientWidth&&localStorage.length===0&&sessionStorage.length===0'));checks++;
      stage=javascript?'javascript-asic-offer':'no-javascript-asic-offer';
      await go(config.origin+'/purchase/shb/offer/'+config.offerIds[javascript?0:1]+'/');
      require(lastStatus===200&&await evaluate('document.body.innerText.includes("50 hours in this order")&&document.querySelector("[name=company_name]").value===""&&!document.querySelector("[name=assistance]")&&!document.querySelector("[name=quantity]")'));checks++;
      await fill({privacy:false});await submit('button[name=action][value=review]');
      require(lastStatus===200&&await evaluate('document.body.innerText.includes("ASIC support supplement")&&document.body.innerText.includes("EUR 9,000.00")&&!document.querySelector("[name=accept_terms]").checked&&!document.querySelector("[name=privacy_acknowledged]").checked'));checks++;
      require(await evaluate('document.documentElement.scrollWidth<=document.documentElement.clientWidth'));checks++;
      await toggle('[name=accept_terms]');await toggle('[name=privacy_acknowledged]');
      stage=javascript?'javascript-asic-accept':'no-javascript-asic-accept';
      await submit('button[name=action][value=checkout]');
      require(lastStatus===200&&await evaluate('document.body.innerText.includes("50 hours in this order")&&document.body.innerText.includes("Payment has not started")'));checks++;
      stage=javascript?'javascript-asic-payment':'no-javascript-asic-payment';
      await submit('button[name=action][value=pay]');await submit('button[name=action][value=pay]');
      require(lastStatus===200&&escaped===0&&await evaluate('document.body.innerText.includes("Paid purchase recorded")&&document.body.innerText.includes("Bank result: captured")'));checks++;
      require(await evaluate('document.documentElement.scrollWidth<=document.documentElement.clientWidth&&localStorage.length===0&&sessionStorage.length===0'));checks++;
      await cdp.send('Target.disposeBrowserContext',{browserContextId});
    }
    console.log(JSON.stringify({status:'SHB_BROWSER_PASS',checks,modes:2,pendingDocumentLoads,browser:version,node:process.versions.node,evidence_class:'local-synthetic-browser',fpga:'accepted-30-hours',asic:'requested-and-accepted-50-hours',payment:'synthetic-captured-once',paidOrder:'recorded-once-per-purchase',closure:'safe-before-dispatch'}));
  }catch(error){
    if(config.evidence&&diagnose){try{await writeFile(join(config.evidence,'browser-failure.json'),JSON.stringify(await diagnose()),{flag:'wx',mode:0o600});}catch{}}
    throw error;
  }finally{
    if(!cdp&&config.evidence&&startup)await writeFile(join(config.evidence,'browser-startup.log'),startup.replace(/ws:\/\/\S+/g,'[private loopback debugger]'),{flag:'wx',mode:0o600});
    if(cdp){try{await cdp.send('Browser.close');}catch{}cdp.socket.close();}
    if(child.exitCode===null&&child.signalCode===null){child.kill('SIGTERM');await delay(300);if(child.exitCode===null&&child.signalCode===null)child.kill('SIGKILL');}
    await rm(profile,{recursive:true,force:true});
  }
}
main().catch(()=>{console.error('SHB_BROWSER_FAIL stage='+stage);process.exitCode=1;});
