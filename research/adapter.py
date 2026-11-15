"""Project qualified worker leads into the existing intelligence schema, never authority."""
from datetime import datetime,timezone

def project(evidence, summary, ref):
 claims=[]
 for c in evidence['claims']:
  historical=c['status']=='historical_context'
  claims.append({'id':c['id'],'claim':('Historical source context: ' if historical else 'Source reports; current applicability unverified: ')+c['excerpt'][:220],
   'claim_type':'ownership' if c['kind']=='ownership_lead' else 'energy_experience' if c['kind']=='process_lead' else 'hvac' if c['kind']=='equipment_lead' else 'occupant_identity',
   'about':'other','status':'historical' if historical else 'found','basis':'observed',
   'source':{'name':c['source_tier'],'type':'website','url':c['url']},'observed_at':c['retrieved_at'][:10],
   'excerpt':c['excerpt'],'retrieved_at':c['retrieved_at'],'normalized_sha256':c['normalized_sha256'],'normalized_line':c['normalized_line'],
   'time_state':'historical' if historical else 'unknown','current_verified':False})
 questions=[{'question':q,'answer':answer} for q,answer in [
  ('Who appears to operate this location?','Source-supported location leads are listed below. Current occupant and exact suite remain unverified.'),
  ('Who controls the decisions?','Business ownership, operations, utility-account, property and HVAC/facilities authority remain unknown. Historical owner mentions are leads only.'),
  ('What is the energy/HVAC context?','Production descriptions, when found, are research context only. Current equipment, account and eligibility remain unknown.'),
  ('What is historical or uncertain?','Dates in source excerpts remain historical context. Retrieval dates do not establish freshness. Contradictions require review.'),
  ('What should the rep verify first?','Confirm suite and operating business, then separately verify account and HVAC authority.'),
  ('Does this change prioritization?','Verification-first research candidate only; no measured prioritization or eligibility determination.')]]
 return {'schema':'fieldmind.research','version':2,'generated':datetime.now(timezone.utc).isoformat(),'premises':[{'match':{'ref':ref},'researched_at':datetime.now(timezone.utc).date().isoformat(),'occupant':{'name':None,'status':'unknown'},'decision_route':{'route':'unknown'},'profile':{'owner':{'status':'not_checked'},'hvac':{'status':'not_checked'}},'claims':claims,'summary':'Automated public-source research: '+str(len(claims))+' qualified source leads. Current identity, authority and equipment remain unverified.','find_out_first':'Confirm exact suite and current operating business, then account and HVAC authority.','cannot_conclude':['Current HVAC equipment','Current program eligibility','Utility-account authority','Contact authorization'],'research_questions':questions,'research_method':'deterministic_public_sources','research_metrics':summary}]}
