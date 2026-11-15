# FieldMind research pilot: rules for Claude Code

This folder runs FieldMind research on Kofi's own computer (option A). Follow these rules on every run.

## Hard stops
- Process real MIMO records only after Kofi says, in this session, to start the pilot. If he hasn't, work only with `tests/fixtures/` and public test businesses.
- Never send premise IDs, Itron/utility account numbers, device or thermostat fields, or contact details to any search, fetch or outside service. Research uses only what is in `runs/<ref>/prospect.json`: the ref, the listed name and the address with its suite.
- Never research a premise that `pilot.py prepare` skipped (suppressed or ineligible). Stop and report if you find a suppression problem mid-run.
- Never mark anyone "verified" for the utility account. Never state or imply program eligibility.
- Never upload the list, the run folders or the merged file anywhere. Kofi imports the merged file into FieldMind himself.

## One premise, step by step
1. `python3 worker/fmworker.py mark runs/<ref> prepare`, then `mark ... retrieve`.
2. Retrieve. Preferred: `python3 adapters/oss_retriever.py runs/<ref>` (SearXNG + Crawl4AI; see its header for setup). Otherwise run each search in `plan.json` and fetch the best results yourself. If Crawl4AI is installed, use `adapters/oss_retriever.py`. Run `adapters/wake_parcels.py runs/<ref>` for the owner of record. Log every search and fetch, including failures, in `retrieval.jsonl` with the page text you actually got.
3. `mark ... extract`. Optionally start from `python3 worker/fmworker.py rules runs/<ref>` (model-free drafts), then read the captured text and write or extend `claims.json`: one claim per fact. Each claim gets its exact quote from the captured text, the address as the source gives it (`address_in_source`), `authority_role` where relevant, and dates. Use `temporal: "historical"` for old facts. Propose "verified" only from a registry, property record or permit that names the person.
4. `mark ... check`, `build`, `mark ... done`, `build` again.
5. Read `run-report.json`. Report rejected claims honestly; don't rewrite them until they pass.
6. Stop at 20 minutes per premise. Unknowns are a valid result.

## After the batch
`python3 pilot/pilot.py merge runs pilot-research.json` and `python3 pilot/pilot.py summary runs`.
