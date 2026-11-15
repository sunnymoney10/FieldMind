"""Fixed local synthetic rehearsal, no external inputs/network/model/storage adapter."""
from pathlib import Path
from collections import Counter,defaultdict
from datetime import datetime,timezone
from time import perf_counter
import csv,hashlib,json,os,random,subprocess,sys
from build_brief import build_brief,synthetic_gate
from review import review_brief
from score import score_fixture_verdicts
P=Path(__file__).resolve().parents[1];OUT=P/'run';OUT.mkdir(exist_ok=True);os.chmod(OUT,0o700)
def read(name):return json.loads((P/name).read_text())
def write(name,value):
 path=OUT/name;path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n');os.chmod(path,0o600)
def utc():return datetime.now(timezone.utc).isoformat()
lock=read('protocol/lock.json');manifest=read('authorization-manifest.json');cohort=read('fixtures/cohort.synthetic.json');sources={s['source_id']:s for s in read('fixtures/sources.synthetic.json')['sources']};keys={k['record_id']:k for k in read('fixtures/reviewer-key.synthetic.json')['records']}
assert cohort['synthetic_only'] and not cohort['real_processing_authorized'] and len(cohort['records'])==20
assert Counter(r['stratum'] for r in cohort['records'])==lock['strata']
assert manifest['permission_to_use_list_for_ai_research_and_benchmarking']['status']=='confirmed_by_user'
assert manifest['can_process_real_records'] is False and manifest['real_data_processing_started'] is False
for item in lock['baseline_documents']:assert hashlib.sha256((P/item['file']).read_bytes()).hexdigest()==item['sha256']
assert hashlib.sha256((P/lock['normative_addendum']).read_bytes()).hexdigest()==lock['normative_sha256']
for item in lock['input_files']:assert hashlib.sha256((P/item['file']).read_bytes()).hexdigest()==item['sha256']
with (P/'protocol/assignment.synthetic.csv').open(newline='') as f:assignments=list(csv.DictReader(f))
assert all(a['researcher_A_arm']!=a['researcher_B_arm'] for a in assignments)
clusters=defaultdict(list)
for a in assignments:clusters[a['site_cluster_id']].append(a)
assert all(len({a[k] for a in group})==1 for group in clusters.values() for k in ['researcher_A_arm','researcher_B_arm'])
# Producer receives only its record/packet. The reviewer-key file is never passed to build_brief.
reviews=[];traces=[];brief_ids=[];mapping=[]
by_record={r['record_id']:r for r in cohort['records']};order=[]
for researcher,column in [('SIMULATED-RESEARCHER-A','researcher_A_arm'),('SIMULATED-RESEARCHER-B','researcher_B_arm')]:
 rows=list(assignments);random.Random(lock['synthetic_case_order_seed']+(0 if researcher.endswith('A') else 1)).shuffle(rows)
 for a in rows:order.append((researcher,by_record[a['record_id']],a[column]+'_protocol_replay'))
assert len(order)==40
for execution_index,(researcher,r,lane) in enumerate(order):
 i=cohort['records'].index(r)
 lane_index=0 if lane=='manual_protocol_replay' else 1
 blind=f'BLIND-{(i*2+lane_index)*17%41+1:03d}';start=perf_counter();started=utc();phases=[]
 phase=perf_counter();gate=synthetic_gate(r);phases.append({'phase':'synthetic_control_gate','software_seconds':perf_counter()-phase});assert gate['state']=='synthetic_clear_only'
 phase=perf_counter();brief=build_brief(r,sources,lane);phases.append({'phase':'offline_packet_to_brief','software_seconds':perf_counter()-phase})
 # No arm label passed to deterministic review.
 phase=perf_counter();blinded=dict(brief);blinded.pop('lane');result=review_brief(blinded,r,sources,keys[r['record_id']]);phases.append({'phase':'deterministic_fixture_review','software_seconds':perf_counter()-phase});assert result['pass'],result
 write(blind+'.brief.json',blinded);reviews.append({'blind_brief_id':blind,**result});mapping.append({'blind_brief_id':blind,'record_ref':r['record_id'],'protocol_lane':lane,'simulated_participant':researcher,'execution_order':execution_index});brief_ids.append(blind)
 traces.append({'synthetic':True,'record_ref':r['record_id'],'blinded_brief_id':blind,'simulated_participant':researcher,'execution_order':execution_index,'timing_kind':'software_protocol_replay_not_research_time','started_at':started,'finished_at':utc(),'software_elapsed_seconds':perf_counter()-start,'phases':phases,'human_elapsed_seconds':None,'model_endpoint_elapsed_seconds':None,'independent_human_review_seconds':None})
assert len(set(brief_ids))==40
controls=[]
for r in read('fixtures/gate-controls.synthetic.json')['records']:
 gate=synthetic_gate(r);assert gate['state']=='hold'
 try:build_brief(r,{},'assisted_protocol_replay');raise AssertionError('Gate bypass')
 except ValueError:pass
 controls.append({'control_id':r['control_id'],'state':'held_before_packet_read','source_packets_opened_for_research':0,'excluded_from_timing_and_accuracy':True})
# This known arithmetic example tests the scorer; it is explicitly not a benchmark outcome.
arithmetic=score_fixture_verdicts([{'synthetic':True,'kind':'factual','verdict':'correct','source_usefulness':2},{'synthetic':True,'kind':'factual','verdict':'incorrect','source_usefulness':0},{'synthetic':True,'kind':'factual','verdict':'unverifiable'}],[{'synthetic':True,'useful_verification_step':True,'priority_changed':True,'priority_rationale_supported':True}],[{'synthetic':True,'record_ref':'arithmetic-only','arm':a,'elapsed_seconds':n,'completion_status':'completed','timing_kind':'synthetic_scoring_test'} for a,n in [('manual',100),('assisted',75)]])
assert arithmetic['documentary_accuracy']==.5 and arithmetic['median_paired_elapsed_reduction_percent']==25
write('scoring-arithmetic-example.json',{'label':'Invented arithmetic fixture, NOT research measurements','result':arithmetic})
tests=subprocess.run([sys.executable,str(P/'tools/test_readiness.py')],capture_output=True,text=True)
(OUT/'test-output.txt').write_text(tests.stdout+tests.stderr);assert tests.returncode==0
write('assignment-execution.synthetic.json',{'synthetic':True,'seed':lock['synthetic_case_order_seed'],'participant_role_simulation_only':True,'order':[{'order':i,'simulated_participant':person,'record_ref':r['record_id'],'lane':lane} for i,(person,r,lane) in enumerate(order)]});write('fixture-reviews.json',reviews);write('coordinator-only-blind-map.synthetic.json',mapping);write('software-trace.json',traces);write('gate-control-results.json',controls)
# Measured local permissions are evidence for this synthetic folder only.
env={'inspection_kind':'local_synthetic_only','synthetic_working_directory':str(P),'run_directory_mode':oct(OUT.stat().st_mode&0o777),'run_json_modes':[oct(p.stat().st_mode&0o777) for p in OUT.glob('*.json')],'real_customer_records_loaded':0,'external_research_requests':0,'external_ai_endpoint_calls':0,'live_app_connected':False,'actual_approved_storage_service':manifest['approved_storage_environment']['service'],'actual_approved_ai_workspace':manifest['permitted_ai_tools']['workspace_or_account'],'real_environment_verified':False,'real_authentication_tested':False,'provider_retention_terms_verified':False,'production_deletion_verified':False}
write('environment-inspection.json',env)
summary={'protocol_version':lock['version'],'generated_at':utc(),'synthetic_rehearsal':'PASS','real_pilot_readiness':'BLOCKED','reported_authorization_categories':6,'permission_to_use_list_for_ai_research_benchmarking':'confirmed_by_user_no_reconfirmation_requested','primary_synthetic_cases':20,'protocol_replay_briefs':len(reviews),'fixture_reviews_passed':sum(r['pass'] for r in reviews),'fixture_attribution_checks':sum(r['source_attribution_checks'] for r in reviews),'gate_controls_held':len(controls),'unit_test_status':'PASS','test_case_count':16,'real_records_processed':0,'actual_human_research_runs':0,'actual_ai_endpoint_research_runs':0,'actual_independent_human_reviews':0,'real_documentary_accuracy':None,'real_decision_authority_accuracy':None,'real_source_usefulness':None,'real_prioritization_changes':None,'real_time_saved':None,'blocked_dependencies':['Exact approved AI/research workspace and storage locations not identified/verified','Allowed-field/source settings, participant roles and retention/deletion setup not yet recorded for that environment','Real pilot execution held for readiness review; no actual cohort opened'],'unmeasured_pilot_outcomes':['Actual manual-versus-AI research','Independent human review','Rep usefulness, priority changes and end-to-end time saved'],'next_action':'Review readiness package, finalize the approved handling setup, then explicitly release the real twenty-prospect execution step','can_process_real_records':False}
write('summary.json',summary)
print(json.dumps(summary,indent=2))
