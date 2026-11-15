// Explicit public-only live proof; excluded from routine *.test.cjs suite.
const {chromium}=require('playwright'),assert=require('node:assert/strict'),fs=require('node:fs');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:'/usr/bin/chromium',args:['--no-sandbox']});
 try{
  const page=await browser.newPage({viewport:{width:390,height:844}});const errors=[];const requests=[];
  page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(r.method()==='POST'&&r.url().endsWith('/api/research'))requests.push(JSON.parse(r.postData()));});
  await page.goto('http://127.0.0.1:8765');await page.waitForFunction(()=>Store.mode==='local');
  await page.evaluate(()=>{S.accounts={'synthetic-public-proof':{id:'synthetic-public-proof',name:'Videri Chocolate Factory',addr:'327 W Davie St',city:'Raleigh',list:'rep',origin:'rep',acct:'SYNTHETIC-DO-NOT-SEND',device:'SYNTHETIC-HISTORY-DO-NOT-SEND',suppressed:false}};S.notes={};S.demo=false;render();openAccount('synthetic-public-proof');});
  await page.locator('[data-act="liveresearch"]').click();await page.locator('[data-act="beginresearch"]').click();
  await page.waitForFunction(()=>['complete','failed'].includes(UI.liveResearch?.state),{},{timeout:215000});
  let result=await page.evaluate(()=>JSON.parse(JSON.stringify(UI.liveResearch)));assert.equal(result.state,'complete',result.error);
  assert.deepEqual(Object.keys(requests[0]).sort(),['addr','city','name','ref']);assert.equal(await page.evaluate(()=>!!S.notes['synthetic-public-proof']?.brief),false);
  assert.ok(result.result.draft.premises[0].claims.length>0,'Need actual source-backed leads');
  await page.locator('[data-act="attachresearch"]').click();await page.waitForFunction(()=>UI.liveResearch.state==='saved');
  assert.equal(await page.evaluate(()=>S.notes['synthetic-public-proof'].brief.decision.route),'unknown');
  assert.equal(await page.evaluate(()=>S.accounts['synthetic-public-proof'].acct),'SYNTHETIC-DO-NOT-SEND');
  assert.ok(await page.locator('#sheetBody').innerText().then(t=>t.includes('Who controls the decisions?')));
  await page.locator('[data-act="sources"]').click();assert.ok(await page.locator('.src-card a.ext').count()>0);
  assert.equal(await page.locator('.src-card [onclick], .src-card [onerror]').count(),0);
  await page.screenshot({path:'proof/research-integration-mobile.png',fullPage:true});
  await page.reload();await page.waitForFunction(()=>Store.mode==='local');assert.equal(await page.evaluate(()=>S.notes['synthetic-public-proof'].brief.decision.route),'unknown');
  assert.deepEqual(errors,[]);
  const report={status:'PASS',job_id:result.job,metrics:result.result.metrics,claims:result.result.draft.premises[0].claims.length,failures:result.result.failures,search_failures:result.result.search_failures,assertions:['real UI start -> live search/retrieval -> draft -> explicit save -> existing sources view -> reload','public fields only','no automatic attachment','authority unknown','account unchanged','source links rendered','no injected handlers','no browser errors'],scope:'One independently selected public business; synthetic account ID/history only; no real MIMO records'};
  fs.writeFileSync('proof/research-integration-live.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
