"""Validate local synthetic preparation artifacts only. No prospect input, network or storage adapter."""
from pathlib import Path
from collections import Counter,defaultdict
from urllib.parse import urlsplit
import csv,json
ROOT=Path(__file__).resolve().parents[1]
def read(name):return json.loads((ROOT/name).read_text())
def rows(name):
 with (ROOT/name).open(newline='') as file:return list(csv.DictReader(file))
checks=[]
def check(name,condition):
 if not condition:raise AssertionError(name)
 checks.append(name)
p=read('fixtures/prospects.synthetic.json');records=p['records'];sources=read('fixtures/source-packets.synthetic.json')['sources'];keys=read('fixtures/reviewer-key.synthetic.json')['records']
check('Explicit synthetic-only package; real processing not authorized',p['synthetic_only'] is True and p['real_processing_authorized'] is False)
check('Twenty unique synthetic prospect references',len(records)==20 and len({r['record_id'] for r in records})==20 and all(r['synthetic'] for r in records))
check('Four balanced strata, five cases each',Counter(r['stratum'] for r in records)=={'location_identity':5,'account_relationship':5,'hvac_energy':5,'authority_control':5})
check('Sixty fictional source snippets; no retrieval claims',len(sources)==60 and len({s['source_id'] for s in sources})==60 and all(s['synthetic'] and s['retrieved_on'] is None and (s['url'] is None or urlsplit(s['url']).hostname.endswith('.invalid')) for s in sources))
index={s['source_id']:s for s in sources}
check('All source references resolve to their own synthetic record',all(len(r['source_packet_refs'])==3 and all(x in index and index[x]['record_id']==r['record_id'] for x in r['source_packet_refs']) for r in records))
check('Historical participation and equipment are independent of current state',all(r['historical_participation']['status']=='historical_list_report' and r['historical_equipment']['remains_installed']=='unknown' and r['historical_equipment']['current_compatibility']=='unknown' and r['historical_equipment']['device_raw']==r['raw_list_stub']['Device'] and r['historical_equipment']['thermostat_raw']==r['raw_list_stub']['Thermostat'] for r in records))
check('Current identity never silently accepted; current account/succession unresolved',all(r['current_identity']['accepted_business_id'] is None and r['account_relationship']['current_account_ref'] is None and r['account_relationship']['succession']=='not_inferred' for r in records))
check('Current HVAC and eligibility never inferred from MIMO',all(r['current_hvac']['status']=='unknown' and r['current_hvac']['installed_equipment'] is None and r['current_program_eligibility']['status']=='not_established' and r['current_program_eligibility']['official_rule_version'] is None for r in records))
concepts={'business_ownership','business_operations','utility_account','property','hvac_facilities'}
check('Five distinct authority concepts with qualified states',all(set(r['decision_authority'])==concepts and all(v['state'] in {'unknown','inferred','disputed','verified'} for v in r['decision_authority'].values()) for r in records))
blocked={r['record_id'] for r in records if r['control_scenario']['post_permission_disposition']!='candidate'}
check('Four gate-only controls; sixteen hypothetical candidates',blocked=={'MIMO-S04','MIMO-S10','MIMO-S18','MIMO-S19'} and all(r['control_scenario']['real_processing_permission']=='not_granted' for r in records))
check('Partial-release case retains an independent active restriction',len(records[18]['control_scenario']['suppressions'])==2 and len(records[18]['control_scenario']['releases'])==1)
check('Explicit-release case retains suppression and release history',len(records[19]['control_scenario']['suppressions'])==1 and len(records[19]['control_scenario']['releases'])==1)
check('Reviewer key separate, synthetic and complete',len(keys)==20 and all(k['synthetic'] and not k['identity_auto_accept'] and k['current_eligibility']=='not_established' for k in keys))
plan=rows('templates/cohort-plan.synthetic.csv');timings=rows('templates/timing.blank.csv');results=rows('templates/prospect-results.blank.csv')
check('Twenty planned cases and forty unexecuted timing rows',len(plan)==20 and len(timings)==40 and all(t['completion_status']=='not_run' for t in timings))
check('Opposite arms per prospect; ten of each arm per researcher',all(len([t for t in timings if t['record_ref']==r['record_id']])==2 and {t['arm'] for t in timings if t['record_ref']==r['record_id']}=={'manual','assisted'} for r in records) and all(Counter(t['arm'] for t in timings if t['researcher_ref']==person)=={'manual':10,'assisted':10} for person in ['RESEARCHER-A','RESEARCHER-B']))
bycluster=defaultdict(list)
for r in plan:bycluster[r['site_cluster_id']].append(r)
check('Related site cluster never crosses arms for one researcher',all(len({r[field] for r in group})==1 for group in bycluster.values() for field in ['researcher_A_arm','researcher_B_arm']))
check('Blocked controls labeled gate-only, not completed research',all((r['activity']=='gate_rehearsal_only')==(r['record_id'] in blocked) and r['actual_execution_status']=='not_run' for r in plan))
metadata={'record_ref','stratum','pair_id'}
check('No fabricated prospect result values',len(results)==20 and all(not value for row in results for field,value in row.items() if field not in metadata))
clock_metadata={'record_ref','pair_id','researcher_ref','arm','time_cap_seconds','completion_status'}
check('No fabricated timing values',all(not value for row in timings for field,value in row.items() if field not in clock_metadata))
for name in ['claim-review.blank.csv','source-usefulness.blank.csv','screening-ledger.blank.csv','blind-map.blank.csv']:
 check(name+' has no invented measurements',len(rows('templates/'+name))==0)
review=read('templates/authorization-review.json')
check('All six permission categories pending, real gate false',review['can_process_real_records'] is False and set(review['permissions'])=={'canvassing','ai_processing','public_source_enrichment','storage','access','retention'} and all(p['status']=='pending' and p['evidence_reference'] is None for p in review['permissions'].values()))
check('Environment unconfirmed; no research/contact/migration release',review['working_environment']['status']=='unconfirmed' and review['research_release']['status']=='not_issued' and not review['contact_authorized_by_this_package'] and not review['migration_authorized_by_this_package'])
brief=read('templates/intelligence-brief.blank.json');summary=read('templates/summary.blank.json')
check('Standard six-question brief and separate authority/eligibility',all(k in brief for k in ['q1_current_operator','q2_decision_authority','q3_energy_hvac_context','q4_uncertainty','q5_verify_first','q6_priority_judgment']) and set(brief['q2_decision_authority'])==concepts and brief['q3_energy_hvac_context']['current_eligibility']['state']=='not_established')
check('Results summary clearly not run, no real data or asserted accuracy',summary['status']=='not_run' and summary['real_data_used'] is False and summary['gate_decision']=='pending' and all(v is None for v in summary['accuracy'].values()) and all(v is None for v in summary['timing'].values()))
check('Eight protocol documents present',all((ROOT/name).is_file() for name in ['01-permissions.md','02-cohort.md','03-fixtures.md','04-brief.md','05-verification.md','06-timing.md','07-results.md','08-go-no-go.md']))
for name in checks:print('PASS '+name)
print(f'\n{len(checks)} checks passed; 0 failed. Real-record processing remains NO GO.')
