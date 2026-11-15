"""Rebuilt isolated deterministic worker, NOT the unavailable original worker ZIP."""
from pathlib import Path
from datetime import datetime,timezone
from urllib.parse import urlsplit
import hashlib,json,re,subprocess,sys,time,os
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P))
from adapters.oss_retriever import fetch
from worker.evidence import extract
R=Path(os.environ['FIELDMIND_RUN_DIR']);target=json.loads(Path(os.environ['FIELDMIND_TARGET_FILE']).read_text());(R/'raw-local-only').mkdir(exist_ok=True)
start=time.perf_counter();at=datetime.now(timezone.utc).isoformat();steps={}
def stamp():return time.perf_counter()-start
subprocess.run([sys.executable,str(P/'proof/discover.py')],check=True)
d=json.loads((R/'discovery.json').read_text());(R/'discovery.json').write_text(json.dumps(d,indent=2));steps['discovery_finished_seconds']=stamp()
rows=[];seen=set()
for q in d['queries']:
 for row in q.get('response',{}).get('results',[]):
  url=row.get('url','');u=urlsplit(url);text=(row.get('title','')+' '+row.get('content','')).lower()
  if u.scheme!='https' or u.port or url in seen or not all(w in text for w in re.findall(r'[a-z0-9]+',target['name'].lower())[:2]):continue
  seen.add(url);rows.append(row)
# Primary candidate is a discoverable name-matching hostname, not a supplied website URL.
# Primary site: hostname contains the name's distinctive words (shared rule with engine/rules.py), not the whole name run together.
sys.path.insert(0,str(P/'engine'));import rules as _rules
primary=next((r for r in rows if _rules.is_primary_host(r['url'],target['name'])),None)
primary_host=urlsplit(primary['url']).hostname if primary else None
selected=[primary] if primary else [];selected_urls={primary['url']} if primary else set()
# Topic quotas keep location directories from consuming the ownership budget.
for predicate in [lambda r:bool(re.search(r'address|location',r.get('title','')+' '+r.get('content',''),re.I)),lambda r:bool(re.search(r'owner|founder|anniversary',r.get('title','')+' '+r.get('content',''),re.I)) and urlsplit(r['url']).hostname!=primary_host and bool(re.search(r'/20\d\d/|news',r['url'])),lambda r:'.gov/' in r['url']]:
 match=next((r for r in rows if r['url'] not in selected_urls and predicate(r)),None)
 if match:selected.append(match);selected_urls.add(match['url'])
targets=[(f'S{i+1}',r['url'],r.get('title','')) for i,r in enumerate(selected)]
if not targets:raise RuntimeError('No relevant public source candidates found; no manually pasted fallback')
fetch(R,targets,'retrieval-initial.json');initial=json.loads((R/'retrieval-initial.json').read_text());sources=initial['sources'];follow=[]
for source in sources:
 if urlsplit(source.get('final_url','')).hostname!=primary_host:continue
 for link in source.get('internal_links',[]):
  url=link.get('href','');u=urlsplit(url)
  if u.scheme!='https' or u.hostname!=primary_host or url in selected_urls:continue
  if not re.search(r'about|story|sourcing|factory-tours',u.path,re.I):continue
  selected_urls.add(url);follow.append((f'S{len(sources)+len(follow)+1}',url,'Primary-site context link discovered at retrieval'))
  if len(follow)>=3:break
if follow:
 fetch(R,follow,'retrieval-follow.json');sources+=json.loads((R/'retrieval-follow.json').read_text())['sources']
steps['retrieval_finished_seconds']=stamp();claims=[]
for src in sources:
 path=R/'raw-local-only'/f"{src['source_id']}.html";html=path.read_text() if path.exists() else ''
 challenge=bool(re.search(r'checking the site connection security|verify you are human',html,re.I))
 src['evidence_usable']=src.get('success',False) and src.get('http_status')==200 and len(html)>500 and not challenge
 if not src['evidence_usable']:continue
 normalized,leads=extract(html,src,primary=bool(primary_host and urlsplit(src['final_url']).hostname==primary_host),street_number=(re.findall(r'\d+',target['addr']) or [''])[0])
 (R/'raw-local-only'/f"{src['source_id']}.normalized.txt").write_text(normalized)
 for lead in leads:
  lead['id']=f'C{len(claims)+1}';lead['source_tier']='primary-site candidate' if urlsplit(src['final_url']).hostname==primary_host else 'external publisher';claims.append(lead)
(R/'selection.json').write_text(json.dumps({'primary_host_candidate':primary_host,'rule':'Name-matching hostname; topic quotas: location, dated ownership context, government; follow up to 3 primary-site context links. No accepted identity link inferred.','initial':targets,'follow':follow},indent=2))
(R/'evidence.json').write_text(json.dumps({'sources':sources,'claims':claims,'normalization':'Whitespace-collapsed HTML block text after navigation/footer/form exclusion. Excerpts exactly match normalized source lines; raw HTML and hashes retained.','limitations':['Deterministic candidate extraction, not open-ended semantic verification','Publication dates and contradictions require review','Source-supported address does not establish current occupancy','No automatic identity merge']},indent=2))
brief=['# Six-question precontact intelligence brief','Requested business: '+target['name']+', '+target['addr']+', '+target['city']+'. No utility-account or historical MIMO fields were sent.','Generated by a deterministic worker, with no model calls. Source excerpts are leads; source publication does not establish a current verified fact.']
for title,kinds in [('Who appears to operate this location?',{'location_lead'}),('Who likely controls the relevant decisions?',{'ownership_lead'}),('What is known about energy/HVAC context?',{'process_lead','equipment_lead'})]:
 brief.append('\n## '+title)
 matching=[c for c in claims if c['kind'] in kinds]
 for c in matching[:5]:brief.append(f"- [{c['id']}] “{c['excerpt']}” — {c['status']}; [source]({c['url']}), retrieved {c['retrieved_at']}.")
 if not matching:brief.append('Unknown: no qualified source excerpt retrieved.')
 if 'decisions' in title:brief.append('Current ownership and all five authority categories remain unknown. A founder/owner mention does not establish account, property, operations or facilities authority.')
 if 'HVAC' in title:brief.append('Any production signal is context only. Current installed equipment, energy consumption, utility account, prior participation and program eligibility are unknown.')
brief.extend(['\n## What is historical, uncertain or contradicted?','Mentioned years are preserved in evidence.json; a retrieval date is not an effective date. Owner references with years are historical context. Current occupant and exact suite require confirmation; no building/suite/account merge occurs. The worker does not resolve semantic contradictions or certify that none exist.','\n## What should the representative verify first?','Confirm the suite and current operating business, then separately verify utility-account authority and HVAC/facilities authority. Confirm any historical equipment still exists before using it. Research cannot grant manager approval or release suppression.','\n## Does this change opportunity prioritization?','Context supports a verification-first research candidate only. No measured change from a representative baseline is available. No eligibility or enrollment conclusion is made.'])
(R/'BRIEF.md').write_text('\n'.join(brief)+'\n');steps['brief_finished_seconds']=stamp()
summary={'status':'PARTIAL PASS: bounded deterministic public research; BLOCKED: authenticated Claude Code execution and general semantic verification','started_at':at,'finished_at':datetime.now(timezone.utc).isoformat(),'elapsed_seconds':stamp(),'stage_cumulative_seconds':steps,'searches':len(d['queries']),'pages_requested':len(sources),'usable_pages':sum(s.get('evidence_usable',False) for s in sources),'qualified_leads':len(claims),'model_api_calls':0,'model_tokens':0,'external_service_incremental_charges_usd':0,'unmetered_costs':['existing workspace compute','assistant inference','engineering and independent review'],'claude_code_used':False,'manual_source_transfer':False}
(R/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
