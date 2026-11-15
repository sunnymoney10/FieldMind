---
name: "fieldmind-research"
description: "Research commercial businesses for FieldMind and produce the research file the FieldMind app imports. Use when asked to run FieldMind research, brief accounts, or research a prospect list."
---

# FieldMind research

FieldMind helps one commercial demand-response field rep (Duke EnergyWise Business, via Itron, Raleigh/Wake County area) walk into a business already understanding it. Your job is to research each account and return a file the FieldMind app imports. The rep should be able to read each brief in seconds.

The test for every line you write: **would this change what the rep does at this business today?** If not, leave it out.

## Run my FieldMind research (from the phone)

When the rep says "Run my FieldMind research" (or similar) without pasting a list, the stops are waiting in the FieldMind app itself. Results go straight back into the app; there is no file to send.

- App: the FieldMind artifact, slug `62969098-68d7-4ffe-b3d6-4ddfa167b0a8` (https://claude.ai/artifact/DB6cwMiRpU7MqXVZaMWUwy). Use the artifact database tools available in the session (the Artifact tool's read_db/write_db actions, or db_get / db_list / db_write with that slug).
- Read `research/queue`. Its `items` are `{ref, name, addr, city, zip}`, nothing else. If it is missing or empty, tell the rep nothing is queued and to tap the center button, then "Research the next stops".
- List the `research` collection. Skip any `ref` that already has a `research/result_<ref>` document: it is waiting for the rep to review.
- Research up to 10 queued stops per run, following everything below.
- For each stop, write one document with `db_write` op `set` at path `research/result_<ref>` (new document, no ifVersion), data `{"ref": "<ref>", "at": "<ISO timestamp>", "research": <a research file in the Output format below containing only that one account>}`. Copy the ref exactly. Write one at a time.
- Never write any other path. Never read or write anything under `data/users/`. Never change `research/queue`: the app clears it when the rep adds the results.
- Finish with one line: how many briefs are waiting, and that the rep should open FieldMind and tap "Review".

## Input

A list of accounts, usually pasted from the app's "Copy request" button, one per line:
`- Business name | address, city, zip | ref r1d77s0 | business type`
The `ref` is a code FieldMind makes so results match back to the right account. It carries no account information.
It may also be a CSV of an approved list. If there are more than about 15 accounts, do them in batches of 10–15 and deliver a file per batch, so the rep gets usable briefs early.

## What to find, per account

Work through the five dimensions. Budget about 4–8 searches or page reads per account. Stop early when sources run dry, and record what you checked.

1. **Business**: is it operating at this address now? Hours. Ownership changes, relocations, closures, expansions, new tenant (critical for MIMO). Chain, franchise, or independent?
2. **People**: who operates it and who can authorize enrollment. Owner-operator vs. manager vs. corporate vs. landlord. When the decision-maker is likely on site. Professional roles and documented decisions only.
3. **Infrastructure**: building size (Wake County parcel / real estate records), mechanical or HVAC permits (City of Raleigh / county permit portals), rooftop units, building automation, multi-tenant layout. Use these to estimate thermostat count.
4. **Participation**: what they have actually done, such as voluntary programs, efficiency upgrades, grants, chamber or community involvement, awards. Documented actions, not stated values.
5. **Energy experience**: is energy already on their radar? Reviews about heat or AC, owner replies, outages, energy-saving posts, equipment failures, backup power.

Free sources to prefer: the business's own site, Google Business Profile, booking platforms (Booksy, Fresha), carrier and franchise store locators, NC Secretary of State business registry, commercial real estate listings and leasing flyers (LoopNet, CommercialCafe, Cityfeet, landlord sites; these often name the tenant in each suite with its square footage), restaurant listings, local news.

Source limits learned so far:
- Raleigh's open permit data excludes mechanical and electrical trade permits, and the permit portal and Wake County real estate pages can't be queried directly from a research session. Mark `hvac` and `electrical` as `not_checked` with that reason unless a search result itself shows a dated permit.
- Suite numbers and street numbers often differ between Brian's list and public listings (e.g. 3907 vs 3901 in the same center). Flag the mismatch; don't silently pick one.
- An account in a landlord or property-management entity's name usually means a vacant or between-tenants suite. Look for a lease listing for that suite and say so.
- When two names share one premise on the list, check which one is operating now and record the other in `occupancy`.

## Privacy

Requests from the app no longer contain account numbers or premise IDs, only a `ref` code. If a pasted list or CSV does include premise IDs, Itron account numbers or other utility identifiers, never use them as search terms or send them to any outside service, and leave them out of the research file.

## Trap cases every run must pass

These come from real accounts on the first list. Before writing the file, check each brief against them. A model or tool that fails them isn't trusted for FieldMind research.

1. **Device is not the current business.** A MIMO row's device (e.g. IntelliTemp 801) belongs to the previous occupant. Fail: saying the current business has or had that device.
2. **Two names, one premise.** Rows sharing a premise ID under different names (e.g. Prism Fine Wine LLC / Uptown Biz Plaza LLC) need the relationship explained or flagged. Fail: merging them into one story or silently dropping one.
3. **Landlord-held account.** An account in a shopping center's or property-management entity's name (e.g. Stoneybrook Shopping Center, KRC Property Management) points to a vacant or between-tenants suite. Fail: treating the landlord as the business to pitch without saying so.
4. **Address drift.** Public listings and the list can disagree (3901 vs 3907 Capital Blvd for Tarrymore Square). Fail: picking one silently.
5. **Name change at a suite.** An older source naming one tenant and a newer one naming another (Pho Oxtail vs Nami at Ste 163) is an occupancy change. Fail: presenting the older tenant as current.
6. **Right building, wrong business.** A property fact (square footage, sale listing, permit) belongs to the premises, not automatically to the business on the account. Fail: attaching it to the business without saying so.
7. **Nothing found.** When searches turn up nothing, the summary says so. Fail: filling the brief with generic industry statements.

## Evidence rules (non-negotiable)

- Never invent. Every finding has a source and, where possible, a date and link.
- Separate **observed** (the source says it) from **inferred** (your reasoning). Put inferences in `detail` or `canInfer`, not in `claim`.
- Separate **current** from **historical**.
- Say **what level** the finding is about: the business, the premises, or the equipment. They are not interchangeable: a business can move, and a permit can cover a whole building.
- **Not found is not absent.** Record searches that found nothing in `coverage` as `not_found`. Never write "they have no X" because you didn't find X.
- **MIMO**: the previous occupant's enrollment and device describe the old account. Never present them as the current business's participation or as proof the device is still there and working.
- **People**: professional role, public business statements, and documented decisions only. Nothing about politics, religion, family, health, or private life. No personality profiles.
- No enrollment probabilities or lead scores.
- Don't state program rules (temperatures, event times, runtimes, incentive amounts) beyond these: thermostats need compatible central cooling or heat pump and secure 2.4 GHz Wi-Fi; participation choices are 50% and 75%; each thermostat credits 1.8 kW.
- If there is almost nothing to say, say so plainly in the summary. That is a valid brief.

## Writing the brief

- `story.summary`: 2–3 sentences connecting the findings into what is going on with this business. Specific to this business, never generic ("restaurants use a lot of energy").
- `story.canInfer` and `story.cannotConclude`: short bullets. `cannotConclude` keeps the rep honest, e.g. that equipment is compatible, or that the owner wants to join.
- `salience`: `high` (clear documented energy experience), `some`, or `none_found`.
- `decision.route`: one of `owner_operator`, `manager_needs_approval`, `corporate`, `landlord`, `unknown`, with `who`, `when`, and `basis` (the evidence).
- `thermostats`: `low`/`high` range plus `basis` (square footage, rooftop units, layout, business type, MIMO device). Omit it if there's no basis.
- `watchouts`: what could block enrollment or make the visit go wrong (BAS, corporate IT Wi-Fi, landlord HVAC, multi-tenant suite confusion, sensitive comfort concerns, closure signs).
- `askFirst`: the single most useful thing for the rep to find out at the door.
- `profile`: the business dossier. Fill every field: `hours`, `owner`, `structure` (independent, franchise, dealer, corporate), `property` (center, landlord, suite size), `occupancy` (who's there now, changes), `hvac` (last documented HVAC work), `electrical` (last documented electrical work). Each field is `{status, value, source, link, date}` where status is `found`, `not_found`, `not_checked`, or `conflict`. The last documented permit is not necessarily the last actual work; say "documented" and never invent a date.

## Output

For a pasted list: write one JSON file named `fieldmind-research-YYYY-MM-DD.json` (add `-b2`, `-b3` for later batches) and send it to the user with SendUserFile. Tell them to import it in FieldMind: center button, then "Import results". Validate that it parses before sending.

For "Run my FieldMind research": write each account's research file into the app as described above instead of sending a file.

```json
{
  "fieldmind_research": 1,
  "generated": "2026-11-14T12:00:00Z",
  "accounts": [
    {
      "match": {"ref": "r1d77s0", "name": "Business name", "addr": "412 Main St, Ste 3", "city": "Raleigh", "zip": "27606", "list": "mimo"},
      "researchedAt": "2026-11-14T12:00:00Z",
      "story": {
        "summary": "2–3 sentence connected story.",
        "canInfer": ["..."],
        "cannotConclude": ["..."]
      },
      "salience": "high | some | none_found",
      "decision": {"route": "owner_operator", "who": "Owner, per website", "when": "Mornings", "basis": "Why we think so"},
      "thermostats": {"low": 2, "high": 3, "basis": "Why"},
      "watchouts": ["..."],
      "askFirst": "One question.",
      "profile": {
        "hours": {"status": "found", "value": "Mon–Sat 9am–7pm", "source": "Google Business Profile", "link": "https://...", "date": "YYYY-MM-DD"},
        "owner": {"status": "not_found", "value": ""},
        "structure": {"status": "found", "value": "Independent", "source": "..."},
        "property": {"status": "found", "value": "Ste 163, 1,200 sq ft, Tarrymore Square", "source": "Leasing flyer", "link": "https://..."},
        "occupancy": {"status": "conflict", "value": "Flyer says X, newer listing says Y"},
        "hvac": {"status": "not_checked", "value": "Trade permits not in open data"},
        "electrical": {"status": "not_checked", "value": "Trade permits not in open data"}
      },
      "coverage": [
        {"dim": "infrastructure", "checked": "City of Raleigh permit search", "result": "found | not_found | not_checked"}
      ],
      "evidence": [
        {
          "dim": "business | people | infrastructure | behavior | energy",
          "claim": "What the source shows, stated plainly",
          "detail": "Context, caveats, or inference",
          "source": "Public permit | Business listing | Business website | Customer review | Job posting | News / local media | GIS / property record | Other",
          "date": "YYYY-MM-DD",
          "link": "https://...",
          "rel": "supports | contradicts | mixed | neutral | unknown",
          "level": "business | premises | equipment",
          "basis": "observed | inferred",
          "time": "current | historical"
        }
      ]
    }
  ]
}
```

Copy `ref`, name and address exactly from the input into `match` so the app links the brief to the right account. Without a `ref`, the app falls back to matching on name and address.

Finish with one or two lines: how many accounts were briefed, and any that stood out (likely multi-thermostat sites, a decision-maker with known hours, or signs of closure that could save a trip).