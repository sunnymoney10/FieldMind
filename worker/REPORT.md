# FieldMind research engine: prototype results and open-source evaluation

Nov 14, 2026 · Isolated prototype, not wired into the live app · No MIMO records used

## 1. What was built

`worker/fmworker.py` is a standard-library Python worker:

| Step | What it does | Who does it |
|---|---|---|
| Intake guard | Accepts only a FieldMind ref, the listed name and the exact address with its suite. Refuses account, premise, Itron and device fields, and any long digit strings. | Code |
| Plan | Runs 6 fixed searches and 2 fetches per prospect: address, name + address, owner, NC Secretary of State, property, permits/HVAC. | Code |
| Retrieve | Writes `retrieval.jsonl`: one record per search or fetch, with outcome, error and captured text. | Adapter (agent tools in this run; SearXNG + Crawl4AI adapter written, not run) |
| Extract | Writes `claims.json`: each claim with the exact quote, the address as the source gives it, its authority role and dates. | Model (Claude) |
| Check | See the rules in the next table. | Code: no model decides acceptance |
| Assemble | Produces `brief.json` (the readiness package's six-question template), `research.v2.json` (FieldMind's import format) and `run-report.json`. | Code |

The check step applies these rules:

| Rule | Effect |
|---|---|
| The quote must appear in the captured text. | Otherwise the claim is rejected. |
| The source address must match the exact address and suite. | Otherwise it's an identity merge and the claim is rejected. |
| A claim with no address must be tied by name to a business already matched to this address. | Otherwise it's rejected. |
| Building and property facts must carry the exact address. | Otherwise they're rejected. |
| "Verified" requires an official record that names the person. | Otherwise the claim is downgraded to source-supported. |
| Utility-account authority is never accepted from public sources or by inference. | The claim is rejected. |
| Anything older than 24 months becomes historical. | The claim is relabelled. |
| Current claims that disagree are linked as disputed. | Both are marked disputed. |
| Inferences need accepted parent claims. | Otherwise they're rejected. |

**Tests:**
- 22 synthetic unit tests: `tests/test_worker.py`, 22/22 pass.
- An import test against an isolated copy of the app: `tests/test_app_import.py`, PASS.
  - The research file validates against the v2 schema with 0 errors.
  - It matched 1 of 1 premises and the brief shows the occupant.
  - It rendered 16 source links.
  - The label is "Local owner likely", with its basis shown.
  - The premise ID was not shown.

## 2. Live test: Videri Chocolate Factory, 327 W Davie St, Raleigh

This is a public business that isn't on Brian's list. All retrieval was live.

**Measured**

| | |
|---|---|
| Wall time, first step to frozen brief | **141 s** (2 min 21 s), against the 1,200 s cap |
| Phases | Retrieve 105 s · Extract 36 s · Check and assemble under 1 s |
| Searches | 7, all returned results |
| Page fetches | 7: 4 ok, **3 blocked** (business website, NC SOS search, Wake County parcel API) |
| Sources cited | 14 distinct URLs |
| Claims proposed / accepted / rejected | 22 / 18 / 6 (4 dropped and 2 downgraded) |
| Accepted claims by label | 0 verified · 9 source-supported · 5 historical · 2 inferred · 2 disputed |
| Marginal cost | **$0**: it ran on the existing Claude plan. No API, hosting or paid data. |

The 141 s is how long the agent took. It does not include a person checking the brief, which the readiness protocol times separately. One multi-tenant claim (C16, The Venue at #102) was taken from a search result fetched within the timed window, but it was extracted during review, after the clock stopped.

**What the brief says**

1. **Operator:** Videri Chocolate Factory is a *candidate, source-supported*.
   - Supporting sources: the Downtown Raleigh Alliance directory and Visit Raleigh both list it at 327 W Davie St #100.
   - A May 2025 ABC11 piece shows it operating.
   - The building has several tenants. The Venue is at #102, and others share the address.
2. **Decision access:**
   - **Ownership:** Sam Ratto, co-owner (ABC11, May 2025), *source-supported*. It's not verified because no Secretary of State record was reachable.
   - **Earlier co-owners:** Chris Heavener and Starr Sink Ratto are *historical*.
   - **Property:** North Carolina Railroad Co. is reported by trade press, which cites the Triangle Business Journal. *Source-supported, secondhand.*
   - **Operations and HVAC authority:** unknown.
   - **Utility account:** unknown, as it always is from public sources.
3. **Energy context:**
   - On-site roasting and grinding machines are a process load, not HVAC.
   - No HVAC, mechanical or electrical permits were found.
   - Eligibility is not established.
4. **Uncertainty:**
   - The founding year is disputed (2011 in several sources, 2013 in an AI-written listing).
   - The 2020 lease listing, the launch-era owners and the 2011 hours are historical.
   - A $75M Depot redevelopment is expected to be finished in 2028. This is a real watch-out for tenancy.
5. **Verify first:** "The list has no suite. Sources put Videri Chocolate Factory in Suite 100 of a building with suites 100, 102. Is this premises that suite?"
6. **Priority:** left for the rep. The worker does not score.

**What the worker rejected on live data**

| Claim | Why |
|---|---|
| A neighbouring parcel's LoopNet record (328 W Davie St) | Different address |
| A Secretary of State hit for Rocky Mountain Chocolate Factory, Inc. | The name isn't tied to this address |
| "Davie Street, LLC controls the property" | No address in the source |
| "Sam Ratto holds the Duke account" | Utility authority is never inferred |
| WRAL owner claim and the trade-press property owner proposed as "verified" | Downgraded to source-supported, because news isn't an official record |

**My review of evidence quality**
- **Strong:** occupant and suite (two independent directories plus 2025 news), current owner, and the redevelopment.
- **Medium:** property owner (secondhand) and floor area (podcast notes, undated).
- **Missing:**
  - Official entity record
  - County property record
  - Hours from the business itself
  - Any HVAC evidence

All three blocked fetches would have filled these gaps. Nothing fabricated got through, and every accepted quote matches its captured text.

## 3. Open-source repositories

None of these could be run here. This workspace's code has no network access and can't install packages; `pip download crawl4ai` fails. The assessments below come from each project's page and documentation, not from measured runs.

| | Crawl4AI | SearXNG | browser-use | Docling | GraphRAG |
|---|---|---|---|---|---|
| Gets live public business info? | **Yes**: fetches and renders pages to markdown, including JavaScript sites | **Yes**: meta-search across Google, Bing, Brave, DuckDuckGo and others | Yes, by driving a browser through forms | Only converts documents and URLs it's given | No: indexes text you already have |
| Local, no paid key? | **Yes** (basic crawling needs no key; LLM extraction is optional) | **Yes** (self-hosted Docker) | **No**: needs a model on every step (cloud key, or Ollama on capable hardware) | Yes (downloads its own models) | No: LLM-heavy, and its docs warn indexing is expensive |
| License | Apache-2.0, but the README also says attribution is *required*. Add the badge or line to be safe. | **AGPL-3.0**: fine to run unmodified internally; modifying it and offering it as a service triggers source-sharing | MIT (cloud parts paid) | MIT; bundled models have their own licenses | MIT; maintenance mode, no new features |
| Main operational risk | Playwright/Chromium upkeep; some sites block crawlers | Upstream engines CAPTCHA-block it. SearXNG suspends Google for 7 days after a CAPTCHA by default. Scraping search engines may break their terms. | Slow, costs per step, brittle on form changes | Heavy install; only needed for PDFs | Cost and complexity with no fit at 36 premises |
| FieldMind fit | **Fixes the biggest gap here**: it can open the business website directly | Replaces the web search tool, but at this volume search already works and costs $0 on your plan | Only for form-based registries (NC SOS), and Claude in Chrome can do that without a new stack | Later: permit and rezoning PDFs | None now |

**Sources by question**

| Question | Best public source | Free access | Notes |
|---|---|---|---|
| Current occupancy and suite | Downtown and visitor directories; Google/Yelp listings via search; the business's own site | Search + fetch | Need two independent sources plus the suite. Directory dates are often missing. |
| Business ownership | NC Secretary of State (officers, registered agent) | Form-based; no API | The only route to "verified". Needs browser automation or a manual lookup. |
| Decision authority | Owner interviews in news; the business's About page | Search + fetch | Source-supported at best. Utility-account authority is never public. |
| Property / landlord | Wake County parcels service (open data, CC BY 4.0, updated daily) | **Free JSON API** | Blocked in this session. Runs directly from a local machine. |
| HVAC evidence | City of Raleigh permit portal | Portal only | Trade permits weren't in Raleigh's open data in our earlier check. Biggest gap. |
| Energy signals | News and features (process equipment, hours, size) | Search + fetch | Signals only, never eligibility. |

## 4. Recommended minimum stack

1. **Claude Code on your computer.** It runs the plan, reads the sources and writes `claims.json`, on the plan you already pay for.
2. **`fmworker.py`.** All acceptance rules, the brief and the FieldMind file. Already built and tested.
3. **Crawl4AI.** Page fetching with real timestamps and raw text, so the business website and other pages open directly instead of being blocked.
4. **Wake County parcels API.** Owner of record as an official property source.

**Skip for now:**
- **SearXNG:** search is not the bottleneck at 36 premises, and it adds a server, AGPL obligations and engine blocking.
- **browser-use:** use Claude in Chrome for the Secretary of State lookup instead.
- **Docling:** add it when permit PDFs matter.
- **GraphRAG:** no fit.

**Cost**
- **This stack:** $0 software and $0 hosting. Maintenance is about an hour a month for Crawl4AI and Playwright updates.
- **Unattended API version (later):** my estimate is $0.40–0.70 per prospect, or about $15–25 for 36 premises. This is not measured.

## 5. Limitations

- One live business, with one researcher (me) and no blind reviewer. This is a working demonstration, not an accuracy measurement.
- The captured text is the fetch tool's extract, copied into the log by the agent. That copy step is a trust point. The Crawl4AI adapter removes it, but it hasn't been run yet.
- Per-call timestamps were not captured in this run. Every retrieval carries the end time of the retrieval phase.
- The address matcher handles common US forms (St/Ste/#/Unit). Unusual formats need more test cases.
- Nothing has been integrated, deployed or merged. **The next step, real MIMO processing, is stopped and needs your go-ahead and the A/B environment choice.**
