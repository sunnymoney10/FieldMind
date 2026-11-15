import copy,json,unittest
from pathlib import Path
from build_brief import build_brief,synthetic_gate
from review import review_brief
from score import score_fixture_verdicts
P=Path(__file__).resolve().parents[1]
class ReadinessTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.records=json.loads((P/'fixtures/cohort.synthetic.json').read_text())['records'];cls.sources={s['source_id']:s for s in json.loads((P/'fixtures/sources.synthetic.json').read_text())['sources']};cls.keys={r['record_id']:r for r in json.loads((P/'fixtures/reviewer-key.synthetic.json').read_text())['records']}
 def review(self,brief,r=None):
  r=r or self.records[0];return review_brief(brief,r,self.sources,self.keys[r['record_id']])
 def test_all_twenty_two_lanes(self):
  for r in self.records:
   for lane in ['manual_protocol_replay','assisted_protocol_replay']:
    with self.subTest(record=r['record_id'],lane=lane):self.assertTrue(self.review(build_brief(r,self.sources,lane),r)['pass'])
 def test_four_gate_controls_stop_before_research(self):
  controls=json.loads((P/'fixtures/gate-controls.synthetic.json').read_text())['records'];self.assertEqual(len(controls),4)
  for r in controls:
   self.assertEqual(synthetic_gate(r)['state'],'hold')
   with self.assertRaises(ValueError):build_brief(r,{},'assisted_protocol_replay')
 def test_wrong_business_and_wrong_suite_rejected(self):
  b=build_brief(self.records[0],self.sources,'assisted_protocol_replay')
  for key,value in [('record_ref','MIMO-S02'),('record_scope',self.records[1]['raw_list_stub']['service_address_raw'])]:
   x=copy.deepcopy(b);x[key]=value;self.assertFalse(self.review(x)['pass'])
 def test_single_candidate_does_not_accept_identity(self):
  b=build_brief(self.records[4],self.sources,'manual_protocol_replay');self.assertIsNone(b['identity_acceptance']);b['identity_acceptance']='accepted';self.assertIn('identity_auto_acceptance',self.review(b,self.records[4])['errors'])
 def test_fabricated_cross_record_and_misquoted_sources_fail(self):
  b=build_brief(self.records[0],self.sources,'assisted_protocol_replay')
  for field,value in [('source_id','missing'),('source_id','MIMO-S02-P'),('exact_quote','Invented current eligibility'),('source_scope','all suites')]:
   x=copy.deepcopy(b);x['claims'][1][field]=value;self.assertFalse(self.review(x)['pass'])
 def test_history_cannot_become_current_account_or_equipment(self):
  b=build_brief(self.records[10],self.sources,'assisted_protocol_replay')
  for mutation in ['account','device','history']:
   x=copy.deepcopy(b)
   if mutation=='account':x['q3']['current_account']=self.records[10]['historical_participation']['historical_account_ref']
   if mutation=='device':x['current_equipment']=self.records[10]['historical_equipment']['device_raw']
   if mutation=='history':x['claims'][0]['epistemic']='current'
   self.assertFalse(self.review(x,self.records[10])['pass'])
 def test_research_cannot_create_eligibility_or_authorization(self):
  b=build_brief(self.records[0],self.sources,'assisted_protocol_replay')
  x=copy.deepcopy(b);x['eligibility']='eligible';self.assertIn('research_created_eligibility',self.review(x)['errors'])
  x=copy.deepcopy(b);x['manager_authorization_from_output']='AI approves';self.assertIn('research_created_authorization',self.review(x)['errors'])
  x=copy.deepcopy(b);x['q3']['current_equipment_from_history']='SYNTH-T01';self.assertIn('unknown_equipment_or_eligibility_field',self.review(x)['errors'])
  x=copy.deepcopy(b);x['q1']['status']='verified';self.assertIn('identity_report_became_verified',self.review(x)['errors'])
 def test_website_owner_cannot_become_verified_account_authority(self):
  b=build_brief(self.records[15],self.sources,'assisted_protocol_replay');b['q2']['utility_account']={'state':'verified','candidate':'website owner','source_refs':['MIMO-S16-X']};self.assertIn('unsupported_verified_authority',self.review(b,self.records[15])['errors'])
 def test_citation_and_missing_premise_cannot_verify_inference(self):
  b=build_brief(self.records[13],self.sources,'assisted_protocol_replay');b['q2']['hvac_facilities']['source_refs']=[];self.assertIn('unsupported_authority_inference',self.review(b,self.records[13])['errors']);b['claims'][0]['verification']='verified';self.assertIn('citation_became_verification',self.review(b,self.records[13])['errors'])
 def test_contradiction_and_uncertainty_must_stay_visible(self):
  b=build_brief(self.records[12],self.sources,'assisted_protocol_replay');b['q4']=[];self.assertIn('contradiction_hidden',self.review(b,self.records[12])['errors'])
 def test_unknown_and_unverifiable_do_not_inflate_accuracy(self):
  rows=[{'synthetic':True,'kind':'factual','verdict':v} for v in ['correct','incorrect','unverifiable']]+[{'synthetic':True,'kind':'hypothesis','verdict':'supported'},{'synthetic':True,'kind':'unknown'}]
  s=score_fixture_verdicts(rows,[],[]);self.assertEqual(s['documentary_accuracy'],.5);self.assertAlmostEqual(s['unverifiable_rate'],1/3)
 def test_authority_accuracy_separate_and_critical_error_blocks(self):
  rows=[{'synthetic':True,'kind':'factual','verdict':'correct','authority_current_verdict':'incorrect','error_type':'wrong_suite'},{'synthetic':True,'kind':'factual','verdict':'correct','authority_current_verdict':'unverifiable'}]
  s=score_fixture_verdicts(rows,[],[]);self.assertEqual(s['documentary_accuracy'],1);self.assertEqual(s['decision_authority_accuracy'],0);self.assertEqual(s['hard_integrity_gate'],'BLOCKED')
 def test_zero_missing_aborted_and_software_times_not_human_speed(self):
  t=[{'synthetic':True,'record_ref':'x','arm':a,'elapsed_seconds':n,'completion_status':'completed','timing_kind':'synthetic_scoring_test'} for a,n in [('manual',100),('assisted',75)]]
  t += [{'synthetic':True,'record_ref':'zero','arm':'manual','elapsed_seconds':0,'completion_status':'completed','timing_kind':'synthetic_scoring_test'},{'synthetic':True,'record_ref':'y','arm':'assisted','elapsed_seconds':.01,'completion_status':'completed','timing_kind':'software_replay'}]
  s=score_fixture_verdicts([],[],t);self.assertEqual(s['complete_timing_pairs'],1);self.assertEqual(s['median_paired_elapsed_reduction_percent'],25);self.assertEqual(s['excluded_timing_rows'],2)
 def test_absent_measurements_remain_unknown(self):
  s=score_fixture_verdicts([],[],[]);self.assertIsNone(s['documentary_accuracy']);self.assertIsNone(s['decision_authority_accuracy']);self.assertIsNone(s['source_usefulness_rate']);self.assertIsNone(s['median_paired_elapsed_reduction_percent']);self.assertFalse(s['real_execution_authorized'])
 def test_scorer_rejects_real_unmarked_input(self):
  with self.assertRaises(ValueError):score_fixture_verdicts([{'kind':'factual','verdict':'correct'}],[],[])
 def test_reported_confirmations_do_not_release_real_execution(self):
  m=json.loads((P/'authorization-manifest.json').read_text());self.assertEqual(m['reported_confirmation_count'],6);self.assertTrue(all(c['status']=='reported_confirmed_by_user' for c in m['reported_confirmations'].values()));self.assertFalse(m['can_process_real_records']);self.assertFalse(m['working_environment_verified']);self.assertEqual(m['permission_to_use_list_for_ai_research_and_benchmarking']['status'],'confirmed_by_user')
if __name__=='__main__':unittest.main(verbosity=2)
