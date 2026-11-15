# FieldMind research worker (isolated prototype)

    python3 worker/fmworker.py plan  runs/<dir>          # needs runs/<dir>/prospect.json
    python3 worker/fmworker.py mark  runs/<dir> <phase>  # prepare|retrieve|extract|check|assemble|done
    python3 worker/fmworker.py rules runs/<dir>          # model-free claim drafts from retrieval.jsonl
    python3 worker/fmworker.py build runs/<dir> [--as-of YYYY-MM-DD]
    python3 tests/test_worker.py                         # synthetic rule tests
    python3 tests/test_app_import.py                     # imports runs/live-001 into reference/app-copy.html

`runs/live-001` is the live Videri Chocolate Factory run (public business, not on any MIMO list).
`adapters/oss_retriever.py` is the SearXNG + Crawl4AI retrieval adapter (written, not yet run).
See REPORT.md for results. No real MIMO data is in this folder.

Merged with the automated-002 proof: see MERGE.md. `python3 -I tests/test_blocks_rules.py` runs its 9 ported tests;
`python3 -I tests/replay_automated_002.py <automated-002 folder>` replays its live captures.
