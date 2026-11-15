"""Local-only SearXNG live discovery for one public business. No API keys or MIMO input."""
from pathlib import Path
from datetime import datetime,timezone
from time import perf_counter,sleep
import json,os,secrets,subprocess,requests,yaml,sys
P=Path(__file__).resolve().parents[1];R=Path(os.environ['FIELDMIND_RUN_DIR']);target=json.loads(Path(os.environ['FIELDMIND_TARGET_FILE']).read_text())
config={'use_default_settings':{'engines':{'keep_only':['duckduckgo','brave','bing']}},'server':{'bind_address':'127.0.0.1','port':18889,'limiter':False,'public_instance':False,'secret_key':'ephemeral-replaced-by-env'},'general':{'enable_metrics':False},'search':{'formats':['html','json']},'outgoing':{'request_timeout':8.0,'max_request_timeout':12.0},'engines':[{'name':name,'disabled':False} for name in ['duckduckgo','brave','bing']]}
cfg=R/'searxng-settings.yml';cfg.write_text(yaml.safe_dump(config));env=os.environ.copy();env.update(SEARXNG_SETTINGS_PATH=str(cfg),SEARXNG_SECRET=secrets.token_hex(32),PYTHONPATH=os.environ.get('FIELDMIND_SEARCH_SOURCE',str(P/'upstream/searxng')),XDG_CACHE_HOME='/tmp/fieldmind-research-xdg',SEARXNG_BIND_ADDRESS='127.0.0.1',SEARXNG_PORT='18889')
log=(R/'searxng-server.log').open('w');server=subprocess.Popen([sys.executable,'-m','searx.webapp'],env=env,stdout=log,stderr=subprocess.STDOUT,cwd=env['PYTHONPATH'])
try:
 ready=False
 for i in range(60):
  if server.poll() is not None:raise RuntimeError('SearXNG exited; see server log')
  try:
   response=requests.get('http://127.0.0.1:18889/config',timeout=1)
   if response.status_code==200:ready=True;break
  except requests.RequestException:pass
  sleep(.5)
 if not ready:raise RuntimeError('SearXNG not ready')
 name=target['name'].replace('"',' ');place=target['city'].replace('"',' ');street=target['addr'].replace('"',' ')
 queries=[f'"{name}" "{place}" address',f'"{name}" "{place}" owner founder',f'"{street}" "{place}" HVAC permit',f'"{name}" "{place}" energy cooling']
 started=datetime.now(timezone.utc).isoformat();(R/'proof-start.json').write_text(json.dumps({'started_at':started,'business':target['name'],'scope':'One public-business proof; no MIMO or private-account inputs','setup_excluded':True},indent=2))
 results=[];all_start=perf_counter()
 for query in queries:
  start=perf_counter();at=datetime.now(timezone.utc).isoformat()
  try:
   response=requests.get('http://127.0.0.1:18889/search',params={'q':query,'format':'json','language':'en-US','safesearch':1},timeout=30);response.raise_for_status();payload=response.json();entry={'query':query,'retrieved_at':at,'elapsed_seconds':perf_counter()-start,'http_status':response.status_code,'result_count':len(payload.get('results',[])),'response':payload}
  except Exception as e:entry={'query':query,'retrieved_at':at,'elapsed_seconds':perf_counter()-start,'error':str(e)}
  results.append(entry);(R/'discovery.json').write_text(json.dumps({'method':'SearXNG local JSON API','api_key_used':False,'queries':results,'elapsed_seconds':perf_counter()-all_start},indent=2))
  print(json.dumps({k:entry.get(k) for k in ['query','elapsed_seconds','result_count','error']}),flush=True)
finally:
 server.terminate()
 try:server.wait(timeout=10)
 except subprocess.TimeoutExpired:server.kill();server.wait()
 log.close()
