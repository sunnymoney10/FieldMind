"""Loopback-only research companion. No cloud deployment or persistence replacement."""
import json,os,re,secrets,signal,subprocess,sys,threading,time,uuid
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from http.cookies import SimpleCookie
from adapter import project  # earlier lead-only projection, kept for its tests
import engine_adapter
ROOT=Path(__file__).resolve().parent;APP=ROOT.parent
JOBS={};LOCK=threading.Lock();SESSION=secrets.token_urlsafe(32)

def validate_target(data):
 if not isinstance(data,dict) or set(data)!={'name','addr','city','ref'}:raise ValueError('Only business name, street address, city and request reference are accepted.')
 out={}
 for k,limit in [('name',160),('addr',240),('city',100),('ref',80)]:
  value=data[k]
  if not isinstance(value,str) or not value.strip() or len(value)>limit or re.search(r'[\x00-\x1f\x7f]',value):raise ValueError('Invalid '+k)
  out[k]=value.strip()
 if not re.fullmatch(r'[a-zA-Z0-9_-]{8,80}',out['ref']):raise ValueError('Invalid request reference')
 return out

def run_job(job_id,target):
 run=ROOT/'runs'/job_id;run.mkdir(parents=True,mode=0o700)
 target_path=run/'target.json';target_path.write_text(json.dumps(target));os.chmod(target_path,0o600)
 env=os.environ.copy();env.update(FIELDMIND_RUN_DIR=str(run),FIELDMIND_TARGET_FILE=str(target_path),PYTHONUNBUFFERED='1')
 with LOCK:JOBS[job_id]['state']='running'
 try:
  with (run/'worker.log').open('w') as log:
   proc=subprocess.Popen([sys.executable,str(ROOT/'worker/fmworker.py')],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
   try:rc=proc.wait(timeout=180)
   except subprocess.TimeoutExpired:
    os.killpg(proc.pid,signal.SIGKILL);proc.wait();raise RuntimeError('Research timed out after 180 seconds. Nothing was attached.')
   finally:
    # Also clean browser/search descendants if an error interrupted worker cleanup.
    try:os.killpg(proc.pid,signal.SIGTERM)
    except ProcessLookupError:pass
  if rc:raise RuntimeError('Research failed. Nothing was attached; local worker log contains details.')
  evidence=json.loads((run/'evidence.json').read_text());summary=json.loads((run/'summary.json').read_text())
  summary['job_id']=job_id
  result=engine_adapter.project_run(run,target,summary)
  failures=[{'url':s['requested_url'],'status':s.get('http_status'),'reason':s.get('error') or 'Not usable as evidence'} for s in evidence['sources'] if not s.get('evidence_usable')]
  search=json.loads((run/'discovery.json').read_text())
  engine_failures=[{'query':q['query'],'engines':q.get('response',{}).get('unresponsive_engines',[]),'error':q.get('error')} for q in search['queries'] if q.get('error') or q.get('response',{}).get('unresponsive_engines')]
  with LOCK:JOBS[job_id].update(state='complete',draft=result,metrics=summary,failures=failures,search_failures=engine_failures)
 except Exception as error:
  with LOCK:JOBS[job_id].update(state='failed',error=str(error))

def expire_jobs():
 now=time.time()
 for key in list(JOBS):
  if JOBS[key]['state'] not in ('queued','running') and now-JOBS[key]['created']>3600:del JOBS[key]

class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass # Do not log business names, query strings or request bodies.
 def host_ok(self):return self.headers.get('Host')==f'127.0.0.1:{self.server.server_port}'
 def authorized(self):
  try:cookie=SimpleCookie(self.headers.get('Cookie',''));return cookie.get('fm_local') is not None and secrets.compare_digest(cookie['fm_local'].value,SESSION) and self.headers.get('X-FieldMind-Local')=='1'
  except Exception:return False
 def send(self,code,data,html=False,cookie=False):
  raw=data.encode() if html else json.dumps(data).encode();self.send_response(code)
  self.send_header('Content-Type','text/html; charset=utf-8' if html else 'application/json');self.send_header('Content-Length',str(len(raw)))
  self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Referrer-Policy','no-referrer');self.send_header('X-Frame-Options','DENY')
  if cookie:self.send_header('Set-Cookie',f'fm_local={SESSION}; HttpOnly; SameSite=Strict; Path=/')
  self.end_headers();self.wfile.write(raw)
 def do_GET(self):
  if not self.host_ok():return self.send(403,{'error':'Invalid local host'})
  if self.path in ('/','/index.html'):return self.send(200,(APP/'index.html').read_text(),html=True,cookie=True)
  if not self.authorized():return self.send(403,{'error':'Open FieldMind from this local service first.'})
  if self.path=='/api/health':return self.send(200,{'ready':True,'mode':'local_public_sources','model':'none'})
  if re.fullmatch(r'/api/research/[a-f0-9]{32}',self.path):
   with LOCK:job=JOBS.get(self.path.rsplit('/',1)[1]);response=dict(job) if job else None
   return self.send(200,response) if response else self.send(404,{'error':'Research job not found or expired. Start again.'})
  self.send(404,{'error':'Not found'})
 def do_POST(self):
  if not self.host_ok() or self.headers.get('Origin')!=f'http://127.0.0.1:{self.server.server_port}' or not self.authorized():return self.send(403,{'error':'Local session and same-origin request required.'})
  if self.path!='/api/research':return self.send(404,{'error':'Not found'})
  if self.headers.get('Content-Type','').split(';')[0]!='application/json':return self.send(415,{'error':'JSON required'})
  try:
   size=int(self.headers.get('Content-Length','0'))
   if not 0<size<=2048:return self.send(413,{'error':'Request too large or empty'})
   target=validate_target(json.loads(self.rfile.read(size)))
  except (ValueError,TypeError,json.JSONDecodeError):return self.send(400,{'error':'Expected a business name, address, city and opaque request reference; account fields are not accepted.'})
  with LOCK:
   expire_jobs()
   if any(j['state'] in ('queued','running') for j in JOBS.values()):return self.send(409,{'error':'One research job is already running. Wait for it to finish.'})
   job_id=uuid.uuid4().hex;JOBS[job_id]={'state':'queued','job_id':job_id,'created':time.time()}
  threading.Thread(target=run_job,args=(job_id,target),daemon=True).start();self.send(202,{'job_id':job_id,'state':'queued'})

if __name__=='__main__':
 port=int(os.environ.get('FIELDMIND_PORT','8765'));server=ThreadingHTTPServer(('127.0.0.1',port),Handler)
 print(f'FieldMind research: http://127.0.0.1:{server.server_port}',flush=True)
 try:server.serve_forever()
 except KeyboardInterrupt:pass
 finally:server.server_close()
