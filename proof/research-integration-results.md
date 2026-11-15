# Research integration results

PASS for local deterministic public-source research integrated with the existing FieldMind intelligence view. This does not establish Claude Code/model reasoning or production readiness.

- 89 Node application/domain/security/integration tests: PASS.
- 13 Python source-filtering/service boundary tests: PASS.
- 7 live HTTP boundary checks: PASS (session, origin, host, input allowlist and file-access boundaries).
- Mobile browser live public proof: PASS. The complete UI → local API → fresh discovery/retrieval → draft review → explicit save → source evidence → reload path completed with no browser errors. Worker elapsed time: 69.142 seconds. Four searches; five pages requested; four usable; five qualified source leads.
- Only name, street address, city and opaque request reference left the app. Synthetic account/history fields remained unchanged and were not transmitted. No draft attached automatically.
- Independent automated review: raw/normalized hashes and exact excerpts passed; historical owner context stayed historical, current authority/identity stayed unknown. See research-integration-review.md.

Brave rate limits, DuckDuckGo CAPTCHA and one excluded HTTP302 source were recorded. No manual source fallback, paid research API or model call was used. Incremental external-service charges were $0; existing compute, assistant usage and labor are unmetered. A Crawl4AI subprocess cleanup warning remains in the worker log after successful output; the companion additionally terminates the job process group on completion/timeout. No multi-business accuracy claim is made.

The development snapshot lives on local branch codex/research-integration. Original /workspace/fieldmind/index.html is unchanged; this updated application's index.html is in /workspace/fieldmind-integrated. No GitHub branch update, deployment, main merge, storage replacement or real MIMO processing occurred. The exported HTML must run through the included local Python companion to perform web research; a file opened directly cannot execute Crawl4AI.
