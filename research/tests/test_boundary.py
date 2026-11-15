import sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]));sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'proof'))
from server import validate_target
from adapter import project
from network_guard import public_url
class BoundaryTests(unittest.TestCase):
 def test_allowlist(self):
  d={'name':'Synthetic Shop','addr':'100 Fictional Way','city':'Exampleton','ref':'syntheticref1'}
  self.assertEqual(validate_target(d),d)
  with self.assertRaises(ValueError):validate_target({**d,'acct':'synthetic-secret'})
 def test_input_bounds(self):
  for value in ['',{},'a'*161,'Bad\nName']:
   with self.assertRaises(ValueError):validate_target({'name':value,'addr':'100 Fake Way','city':'Exampleton','ref':'syntheticref'})
 def test_unsafe_destinations(self):
  for u in ['file:///etc/passwd','http://localhost/','http://user:pass@example.com','http://example.com:8765/']:self.assertFalse(public_url(u))
  with patch('socket.getaddrinfo',return_value=[(2,1,6,'',('10.0.0.1',443))]):self.assertFalse(public_url('https://synthetic.example/'))
 def test_projection_no_promotion(self):
  c={'id':'C1','kind':'ownership_lead','status':'historical_context','excerpt':'In 2023 Synthetic Owner owned a synthetic shop','source_tier':'synthetic','url':'https://example.com','retrieved_at':'2026-11-15T00:00:00Z','normalized_sha256':'synthetic','normalized_line':1}
  p=project({'claims':[c]}, {},'syntheticref')['premises'][0]
  self.assertEqual(p['occupant']['status'],'unknown');self.assertEqual(p['decision_route']['route'],'unknown');self.assertEqual(p['claims'][0]['status'],'historical');self.assertEqual(p['profile']['owner']['status'],'not_checked')
if __name__=='__main__':unittest.main()
