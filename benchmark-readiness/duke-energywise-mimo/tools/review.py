"""Separate deterministic fixture reviewer; not an independent human or actual ground-truth check."""
CONCEPTS={'business_ownership','business_operations','utility_account','property','hvac_facilities'}
def review_brief(brief,record,sources,key):
 errors=[];rid=record['record_id']
 def require(ok,code):
  if not ok:errors.append(code)
 allowed={'schema','synthetic','record_ref','lane','record_scope','identity_acceptance','manager_authorization_from_output','current_equipment','eligibility','q1','q2','q3','q4','q5','q6','claims','source_usefulness','research_kind'}
 require(set(brief).issubset(allowed),'unknown_output_field')
 require(set(brief.get('q1',{}))=={'candidate_names','status','source_ids','limitation'},'unknown_identity_field')
 require(brief.get('q1',{}).get('status')=='source_reported_not_accepted','identity_report_became_verified')
 require(set(brief.get('q3',{}))=={'historical_participation','historical_equipment','current_account','current_hvac','eligibility'},'unknown_equipment_or_eligibility_field')
 require(brief.get('q6',{}).get('before') is None and brief.get('q6',{}).get('after') is None and brief.get('q6',{}).get('changed') is None,'invented_rep_priority_result')
 require(brief.get('synthetic') is True and brief.get('record_ref')==rid,'wrong_business_reference')
 require(brief.get('record_scope')==record['raw_list_stub']['service_address_raw'],'wrong_suite_scope')
 require(brief.get('identity_acceptance') is None,'identity_auto_acceptance')
 require(brief.get('manager_authorization_from_output') is None,'research_created_authorization')
 require(brief.get('eligibility')=='not_established' and brief.get('q3',{}).get('eligibility')=='not_established','research_created_eligibility')
 require(brief.get('current_equipment') is None and brief.get('q3',{}).get('current_hvac')=='unknown','unsupported_current_equipment')
 require(brief.get('q3',{}).get('current_account')=='unknown','historical_account_became_current')
 require(brief.get('q3',{}).get('historical_equipment')==record['historical_equipment'],'historical_equipment_overwritten')
 require(brief.get('q3',{}).get('historical_participation')==record['historical_participation'],'historical_participation_overwritten')
 require(set(brief.get('q2',{}))==CONCEPTS,'authority_concepts_missing')
 for concept,a in brief.get('q2',{}).items():
  require(a.get('state') in ['unknown','inferred','disputed'],'unsupported_verified_authority')
  require(a==record['decision_authority'].get(concept),'authority_not_supported_by_fixture')
  if a.get('state')=='inferred':require(bool(a.get('source_refs')) and all(x in sources and sources[x]['record_id']==rid for x in a['source_refs']),'unsupported_authority_inference')
 require(brief.get('q1',{}).get('candidate_names')==record['current_identity']['candidate_names'],'wrong_business_candidate')
 if record['current_identity']['status']=='conflicting' or 'conflict' in record['scenario']:require(any('conflict' in x.lower() for x in brief.get('q4',[])),'contradiction_hidden')
 require(all('q'+str(i) in brief for i in range(1,7)),'six_question_incomplete')
 require(bool(brief.get('q5',{}).get('verification_step')) and bool(brief.get('q5',{}).get('why')),'missing_useful_verification_structure')
 require(brief.get('q5',{}).get('contact_performed') is False,'unauthorized_contact')
 require(key['current_eligibility']=='not_established' and key['identity_auto_accept'] is False,'review_key_invalid')
 require(len(brief.get('claims',[]))>=3,'missing_findings')
 for claim in brief.get('claims',[]):
  source=sources.get(claim.get('source_id'))
  require(source is not None,'missing_or_fabricated_source')
  if source is None:continue
  require(source['record_id']==rid and source.get('synthetic') is True,'cross_business_source')
  require(claim.get('exact_quote')==source['excerpt'],'source_misquotation')
  require(claim.get('source_scope')==source['scope'],'source_scope_expansion')
  require(claim.get('verification')=='not_independently_verified','citation_became_verification')
  if claim.get('kind')=='historical_participation':require(claim.get('epistemic')=='historical','history_presented_as_current')
 return {'synthetic':True,'record_ref':rid,'review_type':'automated_fixture_contract_not_human_verification','pass':not errors,'errors':sorted(set(errors)),'source_attribution_checks':len(brief.get('claims',[])),'independent_current_fact_accuracy':None,'human_decision_authority_accuracy':None,'human_verification_step_usefulness':None}
