const {test}=require('node:test');const assert=require('node:assert/strict');const {chromium}=require('playwright');const fs=require('node:fs');const path=require('node:path');
test('browser: mobile workflows and hostile imported evidence',async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.FIELDMIND_CHROMIUM?{executablePath:process.env.FIELDMIND_CHROMIUM}:{}),args:['--no-sandbox']});
 try{
  const page=await browser.newPage({viewport:{width:390,height:844}});const errors=[];page.on('pageerror',e=>errors.push(e.message));
  // Serve only synthetic app data; block fonts and all external network requests.
  await page.route('**/*',route=>route.request().url()==='https://fieldmind.test/'?route.fulfill({contentType:'text/html',body:fs.readFileSync(process.env.FIELDMIND_TEST_HTML||path.join(__dirname,'../index.html'),'utf8')}):route.abort());
  await page.goto('https://fieldmind.test/');
  await page.waitForFunction(()=>Store.mode==='local');
  assert.equal(await page.locator('nav.tabs button[data-tab]').count(),4);
  await page.locator('nav.tabs button[data-tab="search"]').click();
  await page.locator('#q').fill('Brightline');await page.locator('[data-open]').first().click();
  await page.locator('[data-btab="business"]').click();await page.locator('[data-btab="energy"]').click();await page.locator('[data-btab="notes"]').click();
  await page.locator('[data-act="sources"]').click();assert.ok(await page.locator('.src-card').count()>0);
  await page.evaluate(()=>{
   window.__injected=false;
   S.accounts.synthetic={id:'synthetic',name:'Synthetic Browser Tenant',addr:'100 Fictional Way',city:'Exampleton'};
   note('synthetic').evidence=[{id:'" onclick="window.__injected=true',source:'<img src=x onerror="window.__injected=true">',claim:'Synthetic claim',detail:'<svg onload="window.__injected=true">',dim:'business',basis:'observed',link:'javascript:window.__injected=true'}];openSources('synthetic');
  });
  assert.equal(await page.locator('.src-card img, .src-card [onerror], .src-card [onload], .src-card [onclick]').count(),0);
  assert.equal(await page.locator('.src-card a.ext').count(),0);assert.equal(await page.evaluate(()=>window.__injected),false);
  await page.locator('#sheetBack').click();await page.locator('[data-act="visit"]').click();assert.equal(await page.locator('#vform').count(),1);
  assert.deepEqual(errors,[]);
 }finally{await browser.close();}
});
