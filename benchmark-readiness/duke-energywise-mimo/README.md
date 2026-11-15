# FieldMind MIMO benchmark readiness

**Synthetic workflow: PASS. Real pilot: BLOCKED pending the handling setup and readiness-review handoff.** Permission to use Brian's MIMO list for FieldMind, AI-assisted research and benchmarking is confirmed by the user. We are not reopening that permission question.

Start with [READINESS.md](READINESS.md), [authorization manifest](authorization-manifest.json) and [locked protocol](protocol/PROTOCOL.md). The manifest records six reported confirmations and the user's follow-up permission confirmation. It does not invent the exact AI/storage workspace, allowed fields/sources, participant identities or retention configuration. Those operational details are still open.

## What was rehearsed

Twenty entirely synthetic primary cases, four strata of five, two counterbalanced protocol lanes, blinded brief IDs, separate deterministic fixture review, source attribution, historical/current distinctions, uncertainty, scoring and archive checks. Four extra gate controls remained blocked before packet reading. Forty completed software-replay briefs and 120 fixture quote/scope checks passed. Sixteen test cases exercise both valid paths and rejection of dangerous outputs.

Four primary cases include explicit **fictional** manager releases/scope clarifications; their negative variants retain restrictions. No actual Brian-list entry, customer record, program eligibility or real manager release is represented. Historical/raw fields are unchanged. Franchise/operations, multiple-account, suite and facilities distinctions remain explicit. All source URLs are fictional `.invalid` addresses; no public pages or AI research endpoints were accessed.

This is a deterministic **protocol replay**, not a completed human-manual/AI comparison. It cannot establish actual independent-review accuracy, decision-authority accuracy, rep usefulness, prioritization value or research speed. Actual pilot result fields remain null. Software timings are labeled separately and excluded from the research-time scorer.

## Artifacts

- [Protocol lock and hashes](protocol/lock.json), [counterbalanced assignments](protocol/assignment.synthetic.csv).
- [20 primary fixtures](fixtures/cohort.synthetic.json), [4 blocked controls](fixtures/gate-controls.synthetic.json), [fictional sources](fixtures/sources.synthetic.json), [reviewer-only key](fixtures/reviewer-key.synthetic.json).
- [Rehearsal summary](run/summary.json), [fixture reviews](run/fixture-reviews.json), [gate outcomes](run/gate-control-results.json), [software trace](run/software-trace.json), [executed assignment plan](run/assignment-execution.synthetic.json), [test output](run/test-output.txt).
- [Environment inspection](run/environment-inspection.json): measured local synthetic file controls only; actual approved cloud/AI environment and real authentication are not verified.
- [Results specification](RESULTS.md) and blank files under `templates/`: documentary accuracy, wrong-business/wrong-suite associations, current authority accuracy, verification usefulness, sources, priority changes and elapsed research time.
- Forty `run/BLIND-*.brief.json` files; the arm mapping is coordinator-only **by protocol**, not protected by production role enforcement in this archive.

## Reproduce safely

From this directory: `python tools/rehearse.py`. It accepts no external records or input path, reads the fixed synthetic fixtures, verifies the locked inputs, runs tests and writes the local `run/` artifacts. Only standard-library Python is required. Re-running changes genuine software timestamps/durations, not research results. `python tools/test_readiness.py` runs fault/scoring checks alone.

Do not place real records in this folder or GitHub. No live app, persistence layer, production infrastructure or main-branch merge is changed. The actual handling setup and explicit pilot execution handoff come after reviewing this package; no actual list has been opened or processed.
