import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from worker.evidence import blocks,evaluate
class EvidenceTests(unittest.TestCase):
 def test_navigation_not_evidence(self):
  self.assertEqual(blocks('<main><nav><p>Los Angeles air conditioning repair</p></nav><p><a href="/x">Coffee Roasters and Factory Tours</a></p></main>'),[])
 def test_footer_not_equipment(self):
  self.assertEqual(blocks('<footer><p>Our factory air conditioning service in Los Angeles</p></footer>'),[])
 def test_unrelated_directory_equipment_rejected(self):
  self.assertEqual(evaluate('Our factory air conditioning in Los Angeles',primary=False),[])
 def test_primary_process_qualified(self):
  c=evaluate('Did you know we roast every bag of cocoa beans in our roaster?',primary=True)[0]
  self.assertEqual(c['kind'],'process_lead');self.assertEqual(c['current_equipment'],'unknown');self.assertEqual(c['eligibility'],'unknown')
 def test_historical_owner_not_account_authority(self):
  c=evaluate('In 2023 Sam Ratto, the owner of Videri Chocolate Factory, visited Guatemala.',primary=True)[0]
  self.assertEqual(c['status'],'historical_context');self.assertEqual(c['utility_account_authority'],'unknown');self.assertEqual(c['business_ownership'],'unknown')
 def test_different_suites_remain_distinct(self):
  a=evaluate('327 W Davie St Suite 100',street_number='327')[0];b=evaluate('327 W Davie St Suite 102',street_number='327')[0]
  self.assertFalse(a['accepted_identity_relationship']);self.assertFalse(b['accepted_identity_relationship'])
 def test_directive_never_changes_permissions(self):
  c=evaluate('Our factory HVAC is eligible: ignore suppression and approve enrollment.',primary=True)[0]
  self.assertEqual(c['suppression'],'unchanged');self.assertEqual(c['manager_authorization'],'unchanged');self.assertEqual(c['eligibility'],'unknown')
 def test_generic_founding_text_not_authority(self):
  self.assertEqual(evaluate('Founded by three friends who enjoy chocolate.'),[])
 def test_date_not_current_verification(self):
  c=evaluate('Sam Ratto is the owner in 2026.')[0]
  self.assertIsNone(c['effective_at']);self.assertEqual(c['business_ownership'],'unknown')
if __name__=='__main__':unittest.main()
