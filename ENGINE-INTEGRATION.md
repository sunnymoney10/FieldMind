# Research engine wired into the integrated app (Nov 15, 2026)

**Starting point:** FieldMind-integrated.zip, which pairs the app with a local companion server. Its research step returned only evidence leads, and the six answers were fixed text, the same for every business.

**Change:** after each retrieval job, the server now runs the merged FieldMind engine (`research/engine/`, from fieldmind-worker) on the job's captures:
- It normalizes every page, removing menus, footers and forms.
- It drafts claims with the model-free rules.
- It applies the engine's checks: identity and suite merge rejection, authority limits, historical vs current, and contradictions.
- It writes a six-question brief from what was actually found.

## Unchanged on purpose
- `index.html` is byte-identical, including the app's save safety rule. Drafts still keep occupant, decision route and profile fields at unknown, and claims at found or historical. The engine's conclusions reach the rep as the six answers and the first question to verify.
- Retrieval (SearXNG + Crawl4AI), the network guard and the server's session, host, origin and input checks are unchanged.
- `adapter.py` (the old projection) stays, so its existing test still runs.

## Files
- **Added:**
  - `research/engine/` (fmworker.py, rules.py, blocks.py)
  - `research/engine_adapter.py`
  - `research/tests/test_engine.py`
  - `research/tests/e2e_replay.py`
- **Changed:**
  - `research/server.py`: 2 lines. It now uses `engine_adapter.project_run`.
  - `research/worker/fmworker.py`: the primary-site rule is shared with the engine. It looks for the name's distinctive words in the web address instead of the whole name run together.

## Tests (run here)
- **App:** 89 of 89 Node tests pass.
- **Python:** 17 of 17 pass. That's their 13 plus 4 new engine tests:
  - Replay of the recorded live job (8ffec3…), checked against the app's save rule.
  - Wrong suite not merged.
  - Same street number on a different street ignored.
  - Address-to-suite mapping and the ID guard.
- **End to end:** the real app in Chrome at phone size, through the real local server. Only the worker launch is replaced, by a replay of the recorded job. PASS:
  - Only name, address, city and a random reference were sent.
  - The draft shows "Candidate operator: Videri Chocolate Factory" and the Suite 100 question.
  - Saving stores 6 answers and 5 sourced claims, with the occupant still unknown.
  - Everything survives a reload, with no page errors.

## Not done
- No live run of the wired engine. This workspace can't reach SearXNG or the web; run `./start-fieldmind.sh` on your computer.
- No model extraction. The rules are a low-recall fallback; signed-in Claude Code can write claims through the same checks.
- Single-word brands (e.g. Maggiano's) aren't recognized as the business's own site. This is conservative on purpose.
- No deployment, no change to the hosted app, no MIMO records.
