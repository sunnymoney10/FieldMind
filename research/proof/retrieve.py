"""Crawl4AI live public pages via fresh local Chromium; no model inference or browser login."""
from pathlib import Path
from datetime import datetime,timezone
from time import perf_counter,sleep
import asyncio,json,os,subprocess,requests,hashlib,urllib.parse,shutil
from network_guard import public_url
P=Path(__file__).resolve().parents[1];R=Path(os.environ.get('FIELDMIND_RUN_DIR',str(P/'results')));(R/'raw-local-only').mkdir(exist_ok=True)
os.environ['CRAWL4_AI_BASE_DIRECTORY']='/tmp/fieldmind-crawl4ai';os.environ['LITELLM_LOCAL_MODEL_COST_MAP']='True';os.environ['DO_NOT_TRACK']='1'
from crawl4ai import AsyncWebCrawler,BrowserConfig,CrawlerRunConfig,CacheMode
OUTPUT_NAME='retrieval.json'
TARGETS=[
 ('S1','https://viderichocolatefactory.com/contact','official business contact'),
 ('S2','https://viderichocolatefactory.com/','official business website'),
 ('S3','https://www.visitraleigh.com/listing/videri-chocolate-factory/67511/','visitor bureau listing'),
 ('S4','https://nsjonline.com/article/2017/01/a-chocolate-anniversary-videri/','dated local news'),
 ('S5','https://engage.raleighnc.gov/W5884','government rezoning; not an HVAC permit'),
 ('S6','https://downtownraleigh.org/go/the-venue','same-address different-suite control'),
 ('S7','https://frankielemmonfoundation.org/twfe-samratto/','public professional biography')]
async def run():
 from playwright.async_api import async_playwright
 async with async_playwright() as driver:
  executable=os.environ.get('FIELDMIND_CHROMIUM') or shutil.which('chromium') or shutil.which('chromium-browser') or driver.chromium.executable_path
 if not Path(executable).exists():raise RuntimeError('Chromium is missing; run python -m playwright install chromium')
 log=(R/'chromium.log').open('w');browser=subprocess.Popen([executable,'--headless','--no-sandbox','--disable-dev-shm-usage','--disable-background-networking','--no-first-run','--remote-debugging-address=127.0.0.1','--remote-debugging-port=19223','--user-data-dir='+str(R/'browser-profile'),'about:blank'],stdout=log,stderr=log)
 try:
  for _ in range(40):
   try:
    if requests.get('http://127.0.0.1:19223/json/version',timeout=1).ok:break
   except requests.RequestException:pass
   sleep(.25)
  config=BrowserConfig(browser_mode='cdp',cdp_url='http://127.0.0.1:19223',headless=True,verbose=False,user_agent='FieldMindResearchProof/0.1 (public-page evaluation)')
  run_config=CrawlerRunConfig(cache_mode=CacheMode.BYPASS,page_timeout=30000,wait_until='domcontentloaded',check_robots_txt=True,verbose=False,excluded_tags=['script','style','noscript'])
  results=[];started=perf_counter();at=datetime.now(timezone.utc).isoformat()
  async with AsyncWebCrawler(config=config,base_directory='/tmp/fieldmind-crawl4ai') as crawler:
   async def before_goto(page,context,url,**kwargs):
    async def route_public(route):
     if await asyncio.to_thread(public_url,route.request.url):await route.continue_()
     else:await route.abort()
    await page.route('**/*',route_public)
    return page
   crawler.crawler_strategy.set_hook('before_goto',before_goto)
   for sid,url,source_type in TARGETS:
    start=perf_counter();retrieved=datetime.now(timezone.utc).isoformat()
    try:
     
     if not await asyncio.to_thread(public_url,url):raise ValueError('Non-public or unsafe source URL rejected')
     result=await crawler.arun(url=url,config=run_config);html=result.html or '';markdown=result.markdown.raw_markdown if result.markdown else ''
     (R/'raw-local-only'/f'{sid}.html').write_text(html);(R/'raw-local-only'/f'{sid}.md').write_text(markdown)
     entry={'source_id':sid,'requested_url':url,'final_url':getattr(result,'redirected_url',None) or result.url,'source_type':source_type,'retrieved_at':retrieved,'finished_at':datetime.now(timezone.utc).isoformat(),'elapsed_seconds':perf_counter()-start,'success':result.success,'http_status':result.status_code,'error':result.error_message,'html_bytes':len(html.encode()),'markdown_chars':len(markdown),'html_sha256':hashlib.sha256(html.encode()).hexdigest(),'metadata':result.metadata,'response_headers':{k:v for k,v in (result.response_headers or {}).items() if k.lower() in ['last-modified','etag','content-type']},'internal_links':result.links.get('internal',[]) if result.links else []}
    except Exception as e:entry={'source_id':sid,'requested_url':url,'retrieved_at':retrieved,'elapsed_seconds':perf_counter()-start,'success':False,'error':str(e)}
    results.append(entry);(R/OUTPUT_NAME).write_text(json.dumps({'crawler':'crawl4ai==0.9.5','started_at':at,'elapsed_seconds':perf_counter()-started,'cache_mode':'BYPASS','check_robots_txt':True,'llm_calls':0,'sources':results},indent=2,default=str));print(json.dumps({k:entry.get(k) for k in ['source_id','success','http_status','elapsed_seconds','markdown_chars','error']}),flush=True)
    await asyncio.sleep(.5)
 finally:
  browser.terminate()
  try:browser.wait(timeout=10)
  except subprocess.TimeoutExpired:browser.kill();browser.wait()
  log.close()
if __name__=='__main__':asyncio.run(run())
