import json
recs = []
def add(**k): recs.append(k)
S = "search"
for i,q in enumerate(['"327 W Davie St" Raleigh NC','Videri Chocolate Factory 327 W Davie St Raleigh NC','Videri Chocolate Factory owner founder Raleigh',
  'Videri Chocolate Factory North Carolina Secretary of State business registration','327 W Davie St Raleigh property owner parcel Wake County',
  '327 W Davie St Raleigh permit HVAC mechanical','"327 W DAVIE" Raleigh owner LLC Depot deed'],1):
    add(id=f"S{i}", kind=S, query=q, outcome="ok", source_type="search_results", captured_text="(result list; items used are logged as V records)")
def V(id, url, title, stype, text, published=None, via="S2"):
    add(id=id, kind="search_result", via=via, url=url, title=title, outcome="ok", source_type=stype, captured_text=text, published=published)
V("V1","https://www.visitraleigh.com/listing/videri-chocolate-factory/65276/","Visit Raleigh listing","listing",
  "Videri Chocolate Factory\n- Address: 327 W. Davie St., Ste. 100, Raleigh, NC 27601\n- Area: Downtown Raleigh\n- Phone: 919.755.5053\nAbout\nVideri is a cozy, fully-operational chocolate factory and retail space located in the heart of downtown Raleigh's Warehouse District. It can comfortably accommodate 80 people, with seating available for 20.")
V("V2","https://abc11.com/amp/post/nc-made-raleighs-videri-chocolate-factory-serves-sweet-success-bean-bar-treats/16509066/","ABC11 (WTVD)","news",
  "RALEIGH, N.C. (WTVD) -- When it comes to talking chocolate, no one loves it more than Sam Ratto. He's the co-owner of Videri Chocolate Factory right here in downtown Raleigh.\n\nIn 2024, Videri was named the sixth-best independent coffee shop in the U.S. by USA Today and is in the running again for 2025.", "2025-05-23", "S3")
V("V3","https://www.wral.com/story/21291194/","WRAL","news",
  "Who owns Videri Chocolate Factory?\n\nSam Ratto is the owner of Videri Chocolate Factory in Raleigh, North Carolina. He moved to the Triangle in 2009 from California with plans of running golf courses for a living.\n\nVideri Chocolate Factory is located at 327 W. Davie St., in Raleigh, North Carolina.", None, "S3")
V("V4","https://www.wral.com/story/chocolate-factory-to-hold-grand-opening-in-raleigh/10572006/","WRAL (grand opening)","news",
  "Ratto said he, Sink and co-owner Chris Heavener wanted to focus on creating the best possible product before purchasing larger machines.\nVideri Chocolate Factory is open to the public Wednesday through Saturday 11 a.m.- 7 p.m. and by appointment.", "2011-12-01", "S3")
V("V5","https://indyweek.com/?p=117102","INDY Week","news",
  "Chris Heavener manages Videri and, with the Rattos, helped launch the factory.", None, "S3")
V("V6","https://waltermagazine.com/?p=2169","Walter Magazine","news",
  "“Chocolate, coffee, beer, and wine are cousins,” says Starr Sink Ratto, co-owner of Videri Chocolate Factory, on West Davie Street in the warehouse district.", None, "S3")
V("V7","https://feeds.buzzsprout.com/1786561/episodes/16587280-interview-with-sam-ratto-of-videri-chocolate-factory-and-golf-golf-golf-in-raleigh-nc","Podcast episode notes","news",
  "Its 4,000 square-foot facility in Raleigh’s Warehouse District is home to a small batch chocolate factory, coffee shop and chocolate shop. In 2023, Videri was named one of the 10 best chocolate shops in the country by USA Today.", None, "S3")
V("V8","https://ncfieldfamily.org/?p=23068","NC Field & Family","news",
  "Sam Ratto founded Videri Chocolate Factory in Raleigh in December 2011.\n\nVideri Chocolate Factory\n\n327 W. Davie St., “Sweet” 100 in Raleigh")
V("V9","https://atmosfy.io/location/raleigh/videri-chocolate-factory","Atmosfy (AI summary)","listing",
  "Videri Chocolate Factory, located at 327 W Davie St in Raleigh, is a bean-to-bar chocolate factory established in 2013.")
V("V10","https://sosnc.gov/online_services/search/Business_Registration_profile/5040501","NC Secretary of State","registry",
  "Business Corporation\n\nLegal name:  Rocky Mountain Chocolate Factory, Inc.\n\nSecretary of State Identification Number (SOSID):  0392810\nStatus:  Current-Active\nCitizenship:  Foreign", None, "S4")
V("V11","https://sosnc.gov/online_services/search/Business_Registration_profile/9220643","NC Secretary of State","registry",
  "Limited Liability Company\n\nLegal name:  Davie Street, LLC\n\nSecretary of State Identification Number (SOSID):  1117265\nStatus:  Current-Active\nCitizenship:  Domestic", None, "S7")
V("V12","https://loopnet.com/property/328-w-davie-st-raleigh-nc-27601/37183-170333573589000","LoopNet property record","property_record",
  "Information for the property located at 328 W Davie St Raleigh, NC includes data gathered from Wake County tax records, public records data providers and LoopNet historical data records.\n328 W Davie St\nRestaurantbuilding\n7,656 SF", None, "S5")
def F(id, url, title, stype, text=None, published=None, error=None):
    add(id=id, kind="fetch", url=url, title=title, source_type=stype, outcome="ok" if text else "blocked", captured_text=text or "", published=published, error=error)
F("F1","https://www.viderichocolatefactory.com/","Videri website","business_site", error="URL_NOT_ON_ALLOWLIST: fetch tool only opens URLs that appeared as search-result links")
F("F2","https://abc11.com/post/nc-made-raleighs-videri-chocolate-factory-serves-sweet-success-bean-bar-treats/16509066/","ABC11 (WTVD)","news",
  "\"Friday, May 23, 2025\"\n\"He's the co-owner of Videri Chocolate Factory right here in downtown Raleigh.\"\n\"He opened Videri Chocolate in 2011.\"\n\"The beans are roasted and cracked using a machine with two metal wheels.\"\n\"A blower separates the lighter husks from the cocoa nibs, which fall into a bucket.\"\n\"The nibs are then ground in a spinning drum, where heat and pressure expel cocoa butter\"\n\"The chocolate factory also offers house-made ice cream, coffee, and popcorn.\"", "2025-05-23")
F("F3","https://www.sosnc.gov/online_services/search/by_title/_Business_Registration?SearchCriteria=Videri","NC SOS search","registry", error="URL_NOT_ON_ALLOWLIST: registry search is a form; constructed query URL refused")
F("F4","https://maps.wake.gov/arcgis/rest/services/Property/Parcels/MapServer/0/query?where=SITE_ADDRESS+LIKE+%27327+W+DAVIE%25%27&outFields=*&f=json","Wake County parcels API","property_record", error="URL_NOT_ON_ALLOWLIST: constructed API query refused")
F("F5","https://downtownraleigh.org/go/videri-chocolate-factory","Downtown Raleigh Alliance directory","listing",
  "327 W Davie St\n# 100\nRaleigh, NC 27601\n(919) 755-5053\nBean to bar chocolate factory and coffee shop serving Videri Chocolate and Black & White Coffee.")
F("F6","https://loopnet.ca/Listing/327-W-Davie-St-Raleigh-NC/21635564","LoopNet listing (The Depot)","listing",
  "\"The Depot\"\n\"327 W Davie St, Raleigh, NC 27601\"\n\"1920/2003\"\n\"17,721 SF\"\n\"Anchored by Videri Chocolate\"\n\"nationally known Videri Chocolate\"\n\"Date on Market: 2020-12-01\"", "2020-12-01")
F("F7","https://www.connectcre.com/?p=449369","Connect CRE","news",
  "\"The $75 million project, at 327 W. Davie St., is expected to be completed in 2028.\"\n\"Loden Development is helming The Depot, a mixed-use project that includes hotel, retail and office components\"\n\"The Triangle Business Journal reports the 2.37-acre property owned by the North Carolina Railroad Co.\"\n\"while preserving the former train depot building, which dates back to 1912.\"")
with open("runs/live-001/retrieval.jsonl","w") as f:
    for r in recs: r.setdefault("completed_at","2026-11-15T03:3x"); f.write(json.dumps(r)+"\n")
print(len(recs))
