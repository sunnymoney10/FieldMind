"""Offline synthetic protocol replay. No model endpoint, browsing, actor verification or reviewer key."""
import copy
CONCEPTS=['business_ownership','business_operations','utility_account','property','hvac_facilities']
def synthetic_gate(record):
 if not record.get('synthetic') or record.get('actual_real_processing_authorized') is not False:raise ValueError('Synthetic records only')
 c=record['control_scenario'];released={x['suppression_id'] for x in c['releases']}
 active=[s for s in c['suppressions'] if s['id'] not in released]
 exact=c.get('scope_attestation',{}).get('mode')=='exact_common_areas_only' and c.get('scope_attestation',{}).get('explicitly_excludes_subject_suite') is True
 held=[s for s in active if not (s['scope']=='building_ambiguous' and exact)]
 return {'state':'hold' if held else 'synthetic_clear_only','active_restriction_ids':[s['id'] for s in held],'real_permission':False}
def build_brief(record,sources,lane):
 if lane not in ['manual_protocol_replay','assisted_protocol_replay']:raise ValueError('Unknown replay lane')
 if synthetic_gate(record)['state']!='synthetic_clear_only':raise ValueError('Research blocked before source reading')
 rid=record['record_id'];packet={k:copy.deepcopy(sources[k]) for k in record['source_packet_refs']}
 for s in packet.values():
  if not s.get('synthetic') or s['record_id']!=rid:raise ValueError('Synthetic source boundary')
 claims=[]
 for suffix,kind in [('H','historical_participation'),('P','listing_report'),('X','qualified_context')]:
  s=packet[rid+'-'+suffix];claims.append({'claim_id':rid+'-'+suffix+'-CLAIM','kind':kind,'source_id':s['source_id'],'exact_quote':s['excerpt'],'source_scope':s['scope'],'epistemic':'historical' if suffix=='H' else 'source_reported','verification':'not_independently_verified'})
 uncertainty=['Current account, installed HVAC/controls and current program eligibility are not established','No automatic identity acceptance; source report is not verification']
 if record['current_identity']['status']=='conflicting' or 'conflict' in record['scenario']:uncertainty.append('Conflicting identity/context sources require review; do not choose a convenient winner')
 if 'suite' in record['scenario'] or 'building_permit' in record['scenario']:uncertainty.append('Building/address evidence cannot be silently attached to a suite')
 first='Confirm exact operator/suite and utility-account authority before relying on historical participation'
 if 'historical_thermostat' in record['scenario']:first='Establish current HVAC/control equipment; the old device field does not show what remains installed'
 if 'building_permit' in record['scenario']:first='Establish whether the building permit actually concerns this suite before drawing HVAC conclusions'
 return {'schema':'fieldmind.synthetic-readiness-brief/v1','synthetic':True,'record_ref':rid,'lane':lane,'record_scope':record['raw_list_stub']['service_address_raw'],'identity_acceptance':None,'manager_authorization_from_output':None,'current_equipment':None,'eligibility':'not_established','q1':{'candidate_names':record['current_identity']['candidate_names'],'status':'source_reported_not_accepted','source_ids':[rid+'-P'],'limitation':'Fictional listing, not independent current-operator verification'},'q2':copy.deepcopy(record['decision_authority']),'q3':{'historical_participation':copy.deepcopy(record['historical_participation']),'historical_equipment':copy.deepcopy(record['historical_equipment']),'current_account':'unknown','current_hvac':'unknown','eligibility':'not_established'},'q4':uncertainty,'q5':{'verification_step':first,'why':'Avoid unsupported identity, authority and history-to-current conclusions','contact_performed':False,'requires_separate_contact_authorization':True},'q6':{'before':None,'after':None,'changed':None,'human_assessment':'not_performed','qualitative_note':'Use uncertainty and evidence to review priority; no enrollment or route recommendation'},'claims':claims,'source_usefulness':[{'source_id':s['source_id'],'human_rating':None,'observed_in_replay':True} for s in packet.values()],'research_kind':'offline_protocol_replay_not_human_or_model_research'}
