"""Conservative, deterministic public-page evidence leads. No authority verification."""
import hashlib,re
from bs4 import BeautifulSoup

def blocks(html):
 soup=BeautifulSoup(html,'html.parser')
 for tag in soup.select('script,style,noscript,nav,header,footer,aside,form,[role=navigation],[role=banner],[role=contentinfo]'):
  tag.decompose()
 root=soup.find('main') or soup.find('article') or soup.body or soup
 result=[]
 for tag in root.find_all(['p','address','h1','h2','h3','li']):
  if tag.name=='li' and tag.find(['p','address']):continue
  text=' '.join(tag.get_text(' ',strip=True).split())
  if not 18<=len(text)<=1800:continue
  linked=sum(len(a.get_text(' ',strip=True)) for a in tag.find_all('a'))
  if linked/max(len(text),1)>.55:continue
  if text not in result:result.append(text)
 return result

def evaluate(text, *, primary=False, street_number=''):
 """Return qualified leads, never a current verified fact or accepted identity."""
 kinds=[]
 if street_number and re.search(r'\b'+re.escape(street_number)+r'\b',text) and re.search(r'\b(street|st\.?|road|rd|ave|avenue|blvd|boulevard|drive|dr|lane|ln|way|court|ct)\b',text,re.I):kinds.append('location_lead')
 # Require people/context, not a menu label or a generic founding story.
 if re.search(r'\b(owner|co-owner|founder|co-founder)\b',text,re.I) and re.search(r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b',text):kinds.append('ownership_lead')
 if primary and re.search(r'\b(we|our)\b',text,re.I) and re.search(r'\b(roast|roaster|roasting|manufacture|manufacturing)\b',text,re.I):kinds.append('process_lead')
 if primary and re.search(r'\b(we|our|factory)\b',text,re.I) and re.search(r'\b(HVAC|thermostat|heat pump|air.conditioning)\b',text,re.I):kinds.append('equipment_lead')
 years=sorted(set(re.findall(r'\b(?:19|20)\d{2}\b',text)))
 return [{'kind':kind,'status':'historical_context' if years and kind=='ownership_lead' else 'source_supported_undated_lead','mentioned_years':years,'confidence':'qualified lead; not independently established','effective_at':None,'accepted_identity_relationship':False,'business_ownership':'unknown','business_operations_authority':'unknown','utility_account_authority':'unknown','property_authority':'unknown','hvac_facilities_authority':'unknown','current_equipment':'unknown','eligibility':'unknown','manager_authorization':'unchanged','suppression':'unchanged'} for kind in kinds]

def extract(html,source,primary=False,street_number=""):
 normalized='\n'.join(blocks(html));sha=hashlib.sha256(normalized.encode()).hexdigest();out=[]
 for n,text in enumerate(normalized.splitlines(),1):
  for lead in evaluate(text,primary=primary,street_number=street_number):
   out.append({**lead,'excerpt':text,'source_id':source['source_id'],'url':source['final_url'],'retrieved_at':source['retrieved_at'],'normalized_line':n,'normalized_sha256':sha})
 return normalized,out
